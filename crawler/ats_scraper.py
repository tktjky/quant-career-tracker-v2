import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("ATSScraper")

# Curated registry of target employers and their primary public ATS board tokens
# Supports Greenhouse, Lever, and Ashby
ATS_BOARD_REGISTRY = {
    # Tier A & B Proprietary Trading & Market Making
    "Jump Trading": {"ats": "greenhouse", "token": "jumptrading", "tier": "Tier A: Too Hard"},
    "Jane Street": {"ats": "custom", "token": "janestreet", "tier": "Tier A: Too Hard"},
    "Hudson River Trading": {"ats": "greenhouse", "token": "hudsonrivertrading", "tier": "Tier A: Too Hard"},
    "Citadel": {"ats": "custom", "token": "citadel", "tier": "Tier A: Too Hard"},
    "Citadel Securities": {"ats": "custom", "token": "citadel-securities", "tier": "Tier A: Too Hard"},
    "Optiver": {"ats": "greenhouse", "token": "optiver", "tier": "Tier A: Too Hard"},
    "DRW": {"ats": "greenhouse", "token": "drw", "tier": "Tier B: Main Focus"},
    "Akuna Capital": {"ats": "greenhouse", "token": "akunacapital", "tier": "Tier B: Main Focus"},
    "IMC Trading": {"ats": "greenhouse", "token": "imctrading", "tier": "Tier B: Main Focus"},
    "Flow Traders": {"ats": "greenhouse", "token": "flowtraders", "tier": "Tier B: Main Focus"},
    "SIG": {"ats": "custom", "token": "sig", "tier": "Tier B: Main Focus"},
    "Virtu Financial": {"ats": "greenhouse", "token": "virtufinancial", "tier": "Tier B: Main Focus"},
    "Old Mission Capital": {"ats": "greenhouse", "token": "oldmissioncapital", "tier": "Tier B: Main Focus"},
    "Five Rings": {"ats": "greenhouse", "token": "fiverings", "tier": "Tier A: Too Hard"},
    "Tower Research Capital": {"ats": "greenhouse", "token": "towerresearchcapital", "tier": "Tier B: Main Focus"},
    "Valkyrie Trading": {"ats": "greenhouse", "token": "valkyrietrading", "tier": "Tier B: Main Focus"},
    "Volant Trading": {"ats": "greenhouse", "token": "volanttrading", "tier": "Tier B: Main Focus"},
    "TransMarket Group": {"ats": "greenhouse", "token": "transmarketgroup", "tier": "Tier B: Main Focus"},
    "Belvedere Trading": {"ats": "greenhouse", "token": "belvederetrading", "tier": "Tier B: Main Focus"},
    "Geneva Trading": {"ats": "greenhouse", "token": "genevatrading", "tier": "Tier B: Main Focus"},
    "Peak6 Investments": {"ats": "greenhouse", "token": "peak6", "tier": "Tier B: Main Focus"},

    # Quantitative Hedge Funds & Multi-Managers
    "Two Sigma": {"ats": "greenhouse", "token": "twosigma", "tier": "Tier A: Too Hard"},
    "Millennium Management": {"ats": "custom", "token": "millennium", "tier": "Tier A: Too Hard"},
    "Point72": {"ats": "greenhouse", "token": "point72", "tier": "Tier A: Too Hard"},
    "Balyasny Asset Management": {"ats": "greenhouse", "token": "balyasnyassetmanagement", "tier": "Tier A: Too Hard"},
    "ExodusPoint Capital": {"ats": "greenhouse", "token": "exoduspoint", "tier": "Tier B: Main Focus"},
    "Schonfeld Strategic Advisors": {"ats": "greenhouse", "token": "schonfeld", "tier": "Tier B: Main Focus"},
    "AQR Capital Management": {"ats": "custom", "token": "aqr", "tier": "Tier B: Main Focus"},
    "D.E. Shaw": {"ats": "custom", "token": "deshaw", "tier": "Tier A: Too Hard"},
    "Bridgewater Associates": {"ats": "greenhouse", "token": "bridgewater", "tier": "Tier B: Main Focus"},
    "Man Group": {"ats": "custom", "token": "mangroup", "tier": "Tier B: Main Focus"},
    "WorldQuant": {"ats": "greenhouse", "token": "worldquant", "tier": "Tier B: Main Focus"},
    "Verition Fund Management": {"ats": "greenhouse", "token": "veritionfundmanagement", "tier": "Tier B: Main Focus"},
    "Qube Research & Technologies": {"ats": "greenhouse", "token": "qrt", "tier": "Tier B: Main Focus"},
    "Cubist Systematic Strategies": {"ats": "greenhouse", "token": "point72", "tier": "Tier A: Too Hard"},
    "Squarepoint Capital": {"ats": "custom", "token": "squarepoint", "tier": "Tier B: Main Focus"},

    # Frontier AI, Tech & FinTech Giants
    "Stripe": {"ats": "greenhouse", "token": "stripe", "tier": "Tier B: Main Focus"},
    "Databricks": {"ats": "greenhouse", "token": "databricks", "tier": "Tier B: Main Focus"},
    "Anthropic": {"ats": "greenhouse", "token": "anthropic", "tier": "Tier A: Too Hard"},
    "OpenAI": {"ats": "greenhouse", "token": "openai", "tier": "Tier A: Too Hard"},
    "Palantir": {"ats": "greenhouse", "token": "palantirtechnologies", "tier": "Tier B: Main Focus"},
    "Robinhood": {"ats": "greenhouse", "token": "robinhood", "tier": "Tier B: Main Focus"},
    "Coinbase": {"ats": "greenhouse", "token": "coinbase", "tier": "Tier B: Main Focus"},
    "Plaid": {"ats": "greenhouse", "token": "plaid", "tier": "Tier B: Main Focus"},
    "Ramp": {"ats": "ashby", "token": "ramp", "tier": "Tier B: Main Focus"},
    "Brex": {"ats": "greenhouse", "token": "brex", "tier": "Tier B: Main Focus"},
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

class ATSScraper:
    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.timeout = timeout

    def scrape_greenhouse_board(self, board_token: str, firm_name: str) -> List[Dict[str, Any]]:
        """
        Fetches live postings via Greenhouse API:
        GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
        """
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        jobs = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                raw_jobs = data.get("jobs", [])
                for rj in raw_jobs:
                    job_id = str(rj.get("id", ""))
                    title = rj.get("title", "")
                    absolute_url = rj.get("absolute_url", "")
                    loc = rj.get("location", {}).get("name", "Unknown") if isinstance(rj.get("location"), dict) else str(rj.get("location") or "")
                    
                    # Departments / offices
                    depts = [d.get("name") for d in rj.get("departments", []) if isinstance(d, dict) and d.get("name")]
                    dept_str = ", ".join(depts) if depts else ""
                    
                    # Content snippet
                    content = rj.get("content", "") or ""

                    jobs.append({
                        "job_id": f"gh_{board_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": dept_str,
                        "url": absolute_url,
                        "source_ats": "Greenhouse",
                        "description": content,
                        "updated_at": rj.get("updated_at")
                    })
            else:
                logger.warning(f"Greenhouse board {board_token} returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Greenhouse board {board_token}: {e}")
        return jobs

    def scrape_lever_board(self, site_token: str, firm_name: str) -> List[Dict[str, Any]]:
        """
        Fetches live postings via Lever API:
        GET https://api.lever.co/v0/postings/{site_token}?mode=json
        """
        url = f"https://api.lever.co/v0/postings/{site_token}?mode=json"
        jobs = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                raw_jobs = resp.json()
                for rj in raw_jobs:
                    job_id = str(rj.get("id", ""))
                    title = rj.get("text", "")
                    hosted_url = rj.get("hostedUrl", "")
                    categories = rj.get("categories", {})
                    loc = categories.get("location", "Unknown") if isinstance(categories, dict) else "Unknown"
                    team = categories.get("team", "") if isinstance(categories, dict) else ""
                    description = rj.get("descriptionPlain", "") or ""

                    jobs.append({
                        "job_id": f"lever_{site_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": team,
                        "url": hosted_url,
                        "source_ats": "Lever",
                        "description": description,
                        "updated_at": rj.get("createdAt")
                    })
            else:
                logger.warning(f"Lever board {site_token} returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Lever board {site_token}: {e}")
        return jobs

    def scrape_firm(self, firm_name: str, ats_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        ats_type = ats_meta.get("ats")
        token = ats_meta.get("token")
        if ats_type == "greenhouse":
            return self.scrape_greenhouse_board(token, firm_name)
        elif ats_type == "lever":
            return self.scrape_lever_board(token, firm_name)
        else:
            return []
