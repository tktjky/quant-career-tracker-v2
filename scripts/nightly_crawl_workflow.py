import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any

from crawler.ats_deep_inspector import ATSDeepInspector, KNOWN_FIRM_PROFILES
from crawler.ats_scraper import ATS_BOARD_REGISTRY
from agent.crawl_agent import CrawlAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NightlyCrawlWorkflow")

def run_workflow():
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("STARTING EXHAUSTIVE NIGHTLY CRAWL & FIRM CRAWLABILITY AUDIT WORKFLOW")
    logger.info("=" * 80)

    firms_csv = os.path.join(BASE_DIR, "data", "target_firms.csv")
    if not os.path.exists(firms_csv):
        logger.error(f"Target firms CSV not found at {firms_csv}")
        return

    firms = []
    with open(firms_csv, "r", encoding="utf-8-sig") as f:
        firms = list(csv.DictReader(f))
    logger.info(f"Loaded {len(firms)} target employers from {firms_csv}")

    # Phase 1: Deep ATS Inspection & Barrier Diagnosis
    logger.info("\n>>> PHASE 1: Deep Inspection of 296 Target Portals & ATS Detection...")
    inspector = ATSDeepInspector(timeout=6)
    audit_results = inspector.inspect_all_firms(firms, max_workers=25)
    audit_map = {r["firm_name"]: r for r in audit_results}

    # Save raw audit JSON
    audit_json_path = os.path.join(BASE_DIR, "data", "firm_crawlability_audit.json")
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_map, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved complete crawlability audit to {audit_json_path}")

    # Phase 2: Sync Discovered ATS Boards
    logger.info("\n>>> PHASE 2: Synchronizing Discovered Public ATS Boards...")
    discovered_boards_path = os.path.join(BASE_DIR, "data", "discovered_ats_boards.json")
    discovered_boards = {}
    if os.path.exists(discovered_boards_path):
        try:
            with open(discovered_boards_path, "r", encoding="utf-8") as f:
                discovered_boards = json.load(f)
        except Exception:
            discovered_boards = {}

    newly_added_boards = 0
    for res in audit_results:
        fn = res.get("firm_name")
        ats = res.get("ats")
        token = res.get("token")
        if res.get("status") == "AUTOMATED_FEED" and ats in ("greenhouse", "lever", "ashby", "smartrecruiters", "workable", "workday", "icims", "jibe") and token:
            if fn not in discovered_boards:
                discovered_boards[fn] = {
                    "ats": ats,
                    "token": token,
                    "tier": res.get("priority_tier", "Tier B: Main Focus"),
                    "sector": res.get("industry_sector", "Quantitative Hedge Funds"),
                    "active_job_count": res.get("job_count", 0)
                }
                newly_added_boards += 1
            # Also register in runtime ATS_BOARD_REGISTRY
            ATS_BOARD_REGISTRY[fn] = {
                "ats": ats,
                "token": token,
                "tier": res.get("priority_tier", "Tier B: Main Focus")
            }

    with open(discovered_boards_path, "w", encoding="utf-8") as f:
        json.dump(discovered_boards, f, indent=2, ensure_ascii=False)
    logger.info(f"Discovered ATS boards updated: {len(discovered_boards)} total active boards ({newly_added_boards} newly discovered)")

    # Phase 3: Run Full Crawl Agent across all discovered boards & tailored agents
    logger.info("\n>>> PHASE 3: Executing Multi-Tier Crawl Engine...")
    agent = CrawlAgent(base_dir=BASE_DIR)
    crawl_output = agent.run_crawl()

    # Phase 4: Enrich firms_directory with crawlability audit metadata
    logger.info("\n>>> PHASE 4: Injecting Crawlability Status & Reasons into Directory...")
    live_openings_path = os.path.join(BASE_DIR, "data", "live_openings.json")
    web_data_js_path = os.path.join(BASE_DIR, "web", "data.js")

    active_firm_counts = {}
    for j in crawl_output.get("openings", []):
        if j.get("status") != "INACTIVE":
            fn = j.get("firm_name")
            active_firm_counts[fn] = active_firm_counts.get(fn, 0) + 1

    enriched_directory = []
    crawlable_count = 0
    uncrawlable_count = 0

    for f_row in crawl_output.get("firms_directory", []):
        fn = f_row.get("firm_name")
        audit_info = audit_map.get(fn, {})
        
        has_active_roles = active_firm_counts.get(fn, 0) > 0
        status = audit_info.get("status", "UNCRAWLABLE_PORTAL_ONLY")
        method = audit_info.get("method", "Direct Portal Monitored")
        reason = audit_info.get("reason")

        # If a tailored agent or board found jobs, ensure status is AUTOMATED_FEED
        if has_active_roles or fn in ATS_BOARD_REGISTRY or fn in KNOWN_FIRM_PROFILES:
            if status != "AUTOMATED_FEED":
                status = "AUTOMATED_FEED"
                method = audit_info.get("method") or "Automated Feed"
                reason = None

        if status == "AUTOMATED_FEED":
            crawlable_count += 1
        else:
            uncrawlable_count += 1

        f_row["crawl_status"] = status
        f_row["crawl_method"] = method
        f_row["uncrawlable_reason"] = reason or ("Direct Career Portal Monitored" if status == "UNCRAWLABLE_PORTAL_ONLY" else None)
        enriched_directory.append(f_row)

    crawl_output["firms_directory"] = enriched_directory
    crawl_output["stats"]["crawlable_firms_count"] = crawlable_count
    crawl_output["stats"]["uncrawlable_firms_count"] = uncrawlable_count

    with open(live_openings_path, "w", encoding="utf-8") as f:
        json.dump(crawl_output, f, indent=2, ensure_ascii=False)

    with open(web_data_js_path, "w", encoding="utf-8") as f:
        f.write(f"window.LIVE_OPENINGS_DATA = {json.dumps(crawl_output, indent=2, ensure_ascii=False)};\n")

    # Phase 5: Generate Human-Readable Markdown Report
    logger.info("\n>>> PHASE 5: Generating Firm Crawlability Audit Report...")
    report_md_path = os.path.join(BASE_DIR, "data", "firm_crawlability_report.md")
    generate_audit_report(report_md_path, enriched_directory, crawl_output["stats"], start_time)

    duration = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 80)
    logger.info(f"NIGHTLY CRAWL WORKFLOW COMPLETE IN {duration:.1f}s")
    logger.info(f"Total Monitored Employers:  {len(enriched_directory)}")
    logger.info(f"Automated Feed / Scraped:   {crawlable_count}")
    logger.info(f"Direct Portal Monitored:    {uncrawlable_count}")
    logger.info(f"Active Live Roles Tracked:  {crawl_output['stats']['active_openings']}")
    logger.info("=" * 80)

def generate_audit_report(output_file: str, firms_directory: List[Dict[str, Any]], stats: Dict[str, Any], start_time: datetime):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    crawlable = [f for f in firms_directory if f.get("crawl_status") == "AUTOMATED_FEED"]
    uncrawlable = [f for f in firms_directory if f.get("crawl_status") != "AUTOMATED_FEED"]

    lines = [
        "# Comprehensive Target Employer Crawlability Audit Report",
        f"\n**Audit Timestamp:** {now_str} | **Total Employers Audited:** {len(firms_directory)}\n",
        "## Executive Summary",
        f"- **Total Target Employers Monitored:** {len(firms_directory)}",
        f"- **Automated Live Feeds & Tailored Crawlers:** {len(crawlable)} firms",
        f"- **Direct Official Portals Monitored (Custom / Protected):** {len(uncrawlable)} firms",
        f"- **Total Active Quant Positions Tracked:** {stats.get('active_openings', 0)}",
        f"- **Employers Currently Hiring Quant Roles:** {stats.get('firms_with_active_openings', 0)}",
        "\n---\n",
        "## 1. Automated Live Feeds & Tailored Subagent Employers",
        "These firms possess automated, public, or tailored API endpoints (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, custom scrapers). The system polls these endpoints on an automated schedule.\n",
        "| Firm Name | Priority Tier | Industry Sector | Feed / Scraper Method | Live Roles | Official Careers Portal |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for f in sorted(crawlable, key=lambda x: x["firm_name"]):
        roles_str = f"**{f['active_roles_count']} roles**" if f['active_roles_count'] > 0 else "0 (Off-Cycle)"
        lines.append(f"| **{f['firm_name']}** | {f['priority_tier']} | {f['industry_sector']} | `{f.get('crawl_method', 'Automated Feed')}` | {roles_str} | [Visit Portal]({f['official_careers_url']}) |")

    lines.extend([
        "\n---\n",
        "## 2. Employers Monitored via Direct Career Portals (Uncrawlable / Protected)",
        "These firms do not expose open public ATS APIs or are protected by enterprise security barriers. The tracker monitors their official portals and provides one-click direct access to their careers pages.\n",
        "| Firm Name | Priority Tier | Industry Sector | Technical Crawl Barrier | Official Careers Portal |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ])

    for f in sorted(uncrawlable, key=lambda x: x["firm_name"]):
        reason = f.get("uncrawlable_reason", "Direct Portal Monitored")
        lines.append(f"| **{f['firm_name']}** | {f['priority_tier']} | {f['industry_sector']} | *{reason}* | [Open Official Portal]({f['official_careers_url']}) |")

    lines.append("\n---\n*Report generated by Quant Career Tracker v2 Autonomous Nightly Workflow*\n")

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))

if __name__ == "__main__":
    run_workflow()
