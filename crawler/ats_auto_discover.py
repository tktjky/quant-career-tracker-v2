import os
import json
import csv
import re
import logging
import requests
from typing import Dict, List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("ATSAutoDiscover")

# Common aliases / known tokens for top quant and finance firms
FIRM_TOKEN_OVERRIDES = {
    "AQR Capital Management": [("greenhouse", "aqr")],
    "Squarepoint Capital": [("greenhouse", "squarepointcapital")],
    "Five Rings": [("greenhouse", "fiveringsllc"), ("greenhouse", "fiverings")],
    "Belvedere Trading": [("lever", "belvederetrading")],
    "Plaid": [("ashby", "plaid")],
    "Ramp": [("ashby", "ramp")],
    "OpenAI": [("ashby", "openai")],
    "Maven Securities": [("ashby", "maven")],
    "Scale AI": [("greenhouse", "scaleai")],
    "Snowflake": [("ashby", "snowflake")],
    "DV Trading": [("greenhouse", "dvtrading")],
    "Capstone Investment Advisors": [("greenhouse", "capstoneinvestmentadvisors")],
    "Engineers Gate": [("greenhouse", "engineersgate")],
    "Quantbot Technologies": [("greenhouse", "quantbot-technologies")],
    "Viking Global Investors": [("greenhouse", "vikingglobalinvestors")],
    "MIO Partners": [("greenhouse", "miopartners")],
    "MerQube": [("greenhouse", "merqube")],
    "Numerix": [("greenhouse", "numerix")],
    "GMO": [("lever", "gmo")],
    "Valkyrie Trading": [("lever", "valkyrietrading")],
    "HBK Capital Management": [("greenhouse", "hbkcapitalmanagement")],
    "SESCO": [("greenhouse", "sesco")],
    "Iconiq Capital": [("greenhouse", "iconiq")],
    "TIFIN": [("greenhouse", "tifin")],
    "Upstart": [("greenhouse", "upstart")],
    "SoFi": [("greenhouse", "sofi")],
    "Chime": [("greenhouse", "chime")],
    "Block (Cash App)": [("greenhouse", "block")],
    "GrayScale": [("greenhouse", "grayscale")],
    "Conversion Capital": [("ashby", "conversion")],
    "Waymo": [("greenhouse", "waymo")],
}

def generate_candidate_slugs(firm_name: str) -> List[str]:
    """Generates candidate ATS slug names from a company name."""
    name = re.sub(r"\(.*?\)", "", firm_name).strip()
    name = re.sub(
        r"\b(LLC|Inc\.?|Corp\.?|Capital|Management|Group|Securities|Partners|Asset Management|Investments?|Holdings?)\b",
        "",
        name,
        flags=re.I
    ).strip()

    slugs = set()
    clean_alpha = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    if len(clean_alpha) >= 3:
        slugs.add(clean_alpha)

    full_alpha = re.sub(r"[^a-zA-Z0-9]", "", firm_name).lower()
    if len(full_alpha) >= 3:
        slugs.add(full_alpha)

    dash_slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    if len(dash_slug) >= 3:
        slugs.add(dash_slug)

    return list(slugs)

def probe_ats_endpoint(session: requests.Session, ats: str, token: str, timeout: int = 4) -> int:
    """Probes an ATS endpoint to see if it exists and has open jobs."""
    if ats == "greenhouse":
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    elif ats == "lever":
        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    elif ats == "ashby":
        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    else:
        return 0

    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            jobs = data.get("jobs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            return len(jobs)
    except Exception:
        pass
    return 0

def discover_all_firm_boards(firms_csv_path: str, output_json_path: str, max_workers: int = 25) -> Dict[str, Dict[str, Any]]:
    """
    Scans all target firms and discovers verified active public ATS job boards.
    Saves results to output_json_path.
    """
    if not os.path.exists(firms_csv_path):
        logger.error(f"Firms CSV not found at {firms_csv_path}")
        return {}

    firms = []
    firm_meta_map = {}
    with open(firms_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = row.get("firm_name", "").strip()
            if fn:
                firms.append(fn)
                firm_meta_map[fn] = {
                    "tier": row.get("priority_tier", "Tier B: Main Focus"),
                    "sector": row.get("industry_sector", "Quantitative Hedge Funds")
                }

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    })

    # Prepare probe tasks
    tasks = []
    seen = set()

    # 1. Add known overrides first
    for fn, overrides in FIRM_TOKEN_OVERRIDES.items():
        for ats, tok in overrides:
            if (ats, tok) not in seen:
                seen.add((ats, tok))
                tasks.append((fn, ats, tok))

    # 2. Add algorithmic candidates for all target firms
    for fn in firms:
        slugs = generate_candidate_slugs(fn)
        for slug in slugs:
            for ats in ["greenhouse", "lever", "ashby"]:
                if (ats, slug) not in seen:
                    seen.add((ats, slug))
                    tasks.append((fn, ats, slug))

    logger.info(f"Probing {len(tasks)} candidate endpoints across Greenhouse, Lever, and Ashby...")

    discovered_boards = {}

    def _worker(item):
        f_name, a_type, t_val = item
        count = probe_ats_endpoint(session, a_type, t_val)
        return (f_name, a_type, t_val, count)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_worker, t) for t in tasks]
        for fut in as_completed(futures):
            f_name, a_type, t_val, count = fut.result()
            if count > 0:
                meta = firm_meta_map.get(f_name, {})
                discovered_boards[f_name] = {
                    "ats": a_type,
                    "token": t_val,
                    "tier": meta.get("tier", "Tier B: Main Focus"),
                    "sector": meta.get("sector", "Quantitative Hedge Funds"),
                    "active_job_count": count
                }
                logger.info(f"Discovered: {f_name} -> {a_type}:{t_val} ({count} live jobs)")

    # Save to JSON
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(discovered_boards, f, indent=2, ensure_ascii=False)

    logger.info(f"Total verified active ATS boards discovered: {len(discovered_boards)}")
    return discovered_boards

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    firms_csv = os.path.join(base, "data", "target_firms.csv")
    output_json = os.path.join(base, "data", "discovered_ats_boards.json")
    boards = discover_all_firm_boards(firms_csv, output_json)
    print(f"Discovery complete. Found {len(boards)} boards.")
