import os
import json
import requests
import logging
from typing import Dict, List, Any, Optional

from crawler.salary_extractor import extract_posted_pay_range

logger = logging.getLogger("ATSScraper")

# Curated registry of target employers and their primary public ATS board tokens
# Supports Greenhouse, Lever, and Ashby
ATS_BOARD_REGISTRY = {
    # Tier A & B Proprietary Trading & Market Making
    "Jump Trading": {"ats": "greenhouse", "token": "jumptrading", "tier": "Tier A: Too Hard"},
    "Jane Street": {"ats": "greenhouse", "token": "janestreet", "tier": "Tier A: Too Hard"},
    "Hudson River Trading (HRT)": {"ats": "greenhouse", "token": "wehrtyou", "tier": "Tier A: Too Hard"},
    "Citadel": {"ats": "custom", "token": "citadel", "tier": "Tier A: Too Hard"},
    "Citadel Securities": {"ats": "custom", "token": "citadel-securities", "tier": "Tier A: Too Hard"},
    "Optiver": {"ats": "greenhouse", "token": "optiverus", "tier": "Tier A: Too Hard"},
    "Radix Trading": {"ats": "greenhouse", "token": "radixuniversity", "tier": "Tier A: Too Hard"},
    "DRW": {"ats": "greenhouse", "token": "drweng", "tier": "Tier B: Main Focus"},
    "Akuna Capital": {"ats": "greenhouse", "token": "akunacapital", "tier": "Tier B: Main Focus"},
    "IMC Trading": {"ats": "greenhouse", "token": "imc", "tier": "Tier B: Main Focus"},
    "Flow Traders": {"ats": "greenhouse", "token": "flowtraders", "tier": "Tier B: Main Focus"},
    "SIG": {"ats": "jibe", "token": "sig", "tier": "Tier B: Main Focus"},
    "SIG (Susquehanna International Group)": {"ats": "jibe", "token": "sig", "tier": "Tier B: Main Focus"},
    "Virtu Financial": {"ats": "greenhouse", "token": "virtu", "tier": "Tier B: Main Focus"},
    "Old Mission Capital": {"ats": "greenhouse", "token": "oldmissioncapital", "tier": "Tier B: Main Focus"},
    "Five Rings": {"ats": "greenhouse", "token": "fiveringsllc", "tier": "Tier A: Too Hard"},
    "Five Rings LLC": {"ats": "greenhouse", "token": "fiveringsllc", "tier": "Tier A: Too Hard"},
    "Tower Research Capital": {"ats": "greenhouse", "token": "towerresearchcapital", "tier": "Tier B: Main Focus"},
    "Headlands Technologies": {"ats": "greenhouse", "token": "headlandstechnologiesllc", "tier": "Tier B: Main Focus"},
    "Valkyrie Trading": {"ats": "lever", "token": "valkyrietrading", "tier": "Tier B: Main Focus"},
    "TransMarket Group": {"ats": "greenhouse", "token": "transmarketgroup", "tier": "Tier B: Main Focus"},
    "Belvedere Trading": {"ats": "lever", "token": "belvederetrading", "tier": "Tier B: Main Focus"},
    "Geneva Trading": {"ats": "greenhouse", "token": "genevatrading", "tier": "Tier B: Main Focus"},
    "DV Trading": {"ats": "greenhouse", "token": "dvtrading", "tier": "Tier B: Main Focus"},
    "Maven Securities": {"ats": "greenhouse", "token": "mavensecuritiesholdingltd", "tier": "Tier B: Main Focus"},
    "Chicago Trading Company (CTC)": {"ats": "greenhouse", "token": "chicagotrading", "tier": "Tier B: Main Focus"},
    "Simplex Trading": {"ats": "greenhouse", "token": "simplextrading", "tier": "Tier B: Main Focus"},
    "Walleye Capital": {"ats": "greenhouse", "token": "walleyecapital-external-fulltime", "tier": "Tier B: Main Focus"},
    "PEAK6": {"ats": "workday", "token": "peak6", "tier": "Tier B: Main Focus"},

    # Quantitative Hedge Funds & Multi-Managers
    "Two Sigma": {"ats": "greenhouse", "token": "twosigma", "tier": "Tier A: Too Hard"},
    "Millennium Management": {"ats": "custom", "token": "millennium", "tier": "Tier A: Too Hard"},
    "Point72": {"ats": "greenhouse", "token": "point72", "tier": "Tier A: Too Hard"},
    "Balyasny Asset Management": {"ats": "greenhouse", "token": "balyasnyassetmanagement", "tier": "Tier A: Too Hard"},
    "ExodusPoint Capital Management": {"ats": "greenhouse", "token": "exoduspoint", "tier": "Tier B: Main Focus"},
    "Schonfeld Strategic Advisors": {"ats": "greenhouse", "token": "schonfeld", "tier": "Tier B: Main Focus"},
    "AQR Capital Management": {"ats": "greenhouse", "token": "aqr", "tier": "Tier B: Main Focus"},
    "D.E. Shaw": {"ats": "custom", "token": "deshaw", "tier": "Tier A: Too Hard"},
    "Bridgewater Associates": {"ats": "greenhouse", "token": "bridgewater89", "tier": "Tier B: Main Focus"},
    "Man Group (AHL / Numeric)": {"ats": "greenhouse", "token": "mangroup", "tier": "Tier B: Main Focus"},
    "WorldQuant": {"ats": "greenhouse", "token": "worldquant", "tier": "Tier B: Main Focus"},
    "Verition Fund Management": {"ats": "greenhouse", "token": "veritiongroupllc", "tier": "Tier B: Main Focus"},
    "Qube Research & Technologies (QRT)": {"ats": "greenhouse", "token": "quberesearchandtechnologies", "tier": "Tier B: Main Focus"},
    "Cubist Systematic Strategies": {"ats": "greenhouse", "token": "point72", "tier": "Tier A: Too Hard"},
    "Squarepoint Capital": {"ats": "greenhouse", "token": "squarepointcapital", "tier": "Tier B: Main Focus"},
    "Capstone Investment Advisors": {"ats": "greenhouse", "token": "capstoneinvestmentadvisors", "tier": "Tier B: Main Focus"},
    "Engineers Gate": {"ats": "greenhouse", "token": "engineersgate", "tier": "Tier B: Main Focus"},
    "Quantbot Technologies": {"ats": "greenhouse", "token": "quantbot-technologies", "tier": "Tier B: Main Focus"},
    "Viking Global Investors": {"ats": "greenhouse", "token": "vikingglobalinvestors", "tier": "Tier B: Main Focus"},
    "MIO Partners": {"ats": "greenhouse", "token": "miopartners", "tier": "Tier B: Main Focus"},
    "HBK Capital Management": {"ats": "greenhouse", "token": "hbkcapitalmanagement", "tier": "Tier B: Main Focus"},
    "AXQ Capital": {"ats": "greenhouse", "token": "axq", "tier": "Tier B: Main Focus"},
    "GMO": {"ats": "lever", "token": "gmo", "tier": "Tier B: Main Focus"},
    "Tudor Investment Corp": {"ats": "greenhouse", "token": "tudorgroup", "tier": "Tier B: Main Focus"},
    "Stone Ridge Asset Management": {"ats": "greenhouse", "token": "stone", "tier": "Tier B: Main Focus"},
    "Conversion Capital": {"ats": "ashby", "token": "conversion", "tier": "Tier B: Main Focus"},
    "Moon Capital Management": {"ats": "greenhouse", "token": "moon", "tier": "Tier B: Main Focus"},
    "GrayScale": {"ats": "greenhouse", "token": "grayscale", "tier": "Tier B: Main Focus"},
    "Iconiq Capital": {"ats": "greenhouse", "token": "iconiq", "tier": "Tier B: Main Focus"},

    # Frontier AI, Tech & FinTech Giants
    "Stripe": {"ats": "greenhouse", "token": "stripe", "tier": "Tier B: Main Focus"},
    "Databricks": {"ats": "greenhouse", "token": "databricks", "tier": "Tier B: Main Focus"},
    "Anthropic": {"ats": "greenhouse", "token": "anthropic", "tier": "Tier A: Too Hard"},
    "OpenAI": {"ats": "ashby", "token": "openai", "tier": "Tier A: Too Hard"},
    "Palantir Technologies": {"ats": "lever", "token": "palantir", "tier": "Tier B: Main Focus"},
    "Robinhood": {"ats": "greenhouse", "token": "robinhood", "tier": "Tier B: Main Focus"},
    "Coinbase": {"ats": "greenhouse", "token": "coinbase", "tier": "Tier B: Main Focus"},
    "Plaid": {"ats": "ashby", "token": "plaid", "tier": "Tier B: Main Focus"},
    "Ramp": {"ats": "ashby", "token": "ramp", "tier": "Tier B: Main Focus"},
    "Brex": {"ats": "greenhouse", "token": "brex", "tier": "Tier B: Main Focus"},
    "Scale AI": {"ats": "greenhouse", "token": "scaleai", "tier": "Tier B: Main Focus"},
    "Snowflake": {"ats": "ashby", "token": "snowflake", "tier": "Tier B: Main Focus"},
    "Perplexity AI": {"ats": "ashby", "token": "perplexity", "tier": "Tier B: Main Focus"},
    "Block (Cash App)": {"ats": "greenhouse", "token": "block", "tier": "Tier B: Main Focus"},
    "Chime": {"ats": "greenhouse", "token": "chime", "tier": "Tier B: Main Focus"},
    "SoFi": {"ats": "greenhouse", "token": "sofi", "tier": "Tier B: Main Focus"},
    "Upstart": {"ats": "greenhouse", "token": "upstart", "tier": "Tier B: Main Focus"},
    "Affirm": {"ats": "greenhouse", "token": "affirm", "tier": "Tier B: Main Focus"},
    "Waymo": {"ats": "greenhouse", "token": "waymo", "tier": "Tier B: Main Focus"},
    "Spotify": {"ats": "lever", "token": "spotify", "tier": "Tier B: Main Focus"},
    "Glenmede": {"ats": "lever", "token": "glenmede", "tier": "Tier C2: Same or Below Benchmark"},
    "MerQube": {"ats": "greenhouse", "token": "merqube", "tier": "Tier B: Main Focus"},
    "Numerix": {"ats": "greenhouse", "token": "numerix", "tier": "Tier B: Main Focus"},
    "TIFIN": {"ats": "greenhouse", "token": "tifin", "tier": "Tier C2: Same or Below Benchmark"},

    # Systematic Asset Management & Allocators
    "Dimensional Fund Advisors (DFA)": {"ats": "ashby", "token": "dimensional", "tier": "Tier C1: Same or Above Benchmark"},

    # Frontier AI, Tech & FinTech Giants
    "Fireworks AI": {"ats": "ashby", "token": "fireworks", "tier": "Tier B: Main Focus"},
    "Invisible Technologies": {"ats": "smartrecruiters", "token": "invisibletechnologies", "tier": "Tier B: Main Focus"},

    # Quantitative Hedge Funds & Proprietary Trading
    "Capital Four": {"ats": "lever", "token": "capital", "tier": "Tier B: Main Focus"},
    "The Voleon Group": {"ats": "ashby", "token": "voleon", "tier": "Tier B: Main Focus"},
    "Tanius Tech": {"ats": "greenhouse", "token": "tanius", "tier": "Tier B: Main Focus"},
    "Marshall Wace": {"ats": "greenhouse", "token": "mw-tech-grad", "tier": "Tier A: Too Hard"},
    "Rokos Capital Management": {"ats": "greenhouse", "token": "neptunenorth", "tier": "Tier B: Main Focus"},
    "Trexquant Investment": {"ats": "workable", "token": "trexquant", "tier": "Tier B: Main Focus"},

    # Practice Tier
    "Penn Medicine": {"ats": "smartrecruiters", "token": "pennmedicine", "tier": "Tier D: Pure Practice"},

    # Enterprise Portals with verified Workday CXS API
    "BlackRock": {"ats": "workday", "token": "blackrock", "tier": "Tier C1: Same or Above Benchmark"},
    "State Street": {"ats": "workday", "token": "statestreet", "tier": "Tier C1: Same or Above Benchmark"},
    "Morningstar": {"ats": "workday", "token": "morningstar", "tier": "Tier C2: Same or Below Benchmark"},
    "CME Group": {"ats": "workday", "token": "cmegroup", "tier": "Tier C1: Same or Above Benchmark"},
    "Arrowstreet Capital": {"ats": "workday", "token": "arrowstreetcapital", "tier": "Tier A: Too Hard"},
    "Options Clearing Corporation (OCC)": {"ats": "workday", "token": "theocc", "tier": "Tier B: Main Focus"},
    "Castleton Commodities International (CCI)": {"ats": "workday", "token": "cci", "tier": "Tier B: Main Focus"},
    "AllianceBernstein": {"ats": "workday", "token": "alliancebernstein", "tier": "Tier C1: Same or Above Benchmark"},
    "Invesco": {"ats": "workday", "token": "invesco", "tier": "Tier C1: Same or Above Benchmark"},
    "Brown Brothers Harriman": {"ats": "workday", "token": "bbh", "tier": "Tier C1: Same or Above Benchmark"},
    "CIBC Capital Markets": {"ats": "workday", "token": "cibc", "tier": "Tier C1: Same or Above Benchmark"},
    "American Century Investments": {"ats": "workday", "token": "americancentury", "tier": "Tier C2: Same or Below Benchmark"},
    "Columbia Threadneedle": {"ats": "workday", "token": "columbiathreadneedle", "tier": "Tier C2: Same or Below Benchmark"},
    "TD Securities": {"ats": "workday", "token": "td", "tier": "Tier C1: Same or Above Benchmark"},
    "NVIDIA": {"ats": "workday", "token": "nvidia", "tier": "Tier B: Main Focus"},
    "Blackstone": {"ats": "workday", "token": "blackstone", "tier": "Tier B: Main Focus"},

    # Workable Portals
    "Capula Investment Management": {"ats": "workable", "token": "capula-investment-management-ltd", "tier": "Tier B: Main Focus"},
    "Tibra Capital": {"ats": "workable", "token": "tibra-capital-1", "tier": "Tier B: Main Focus"},

    # Enterprise Portals with verified iCIMS/Jibe/Jobvite API
    "MSCI": {"ats": "icims", "token": "msci", "tier": "Tier C2: Same or Below Benchmark"},
    "GTS": {"ats": "icims", "token": "gts", "tier": "Tier A: Too Hard"},
    "Charles Schwab": {"ats": "icims", "token": "schwab", "tier": "Tier C2: Same or Below Benchmark"},
    "Allspring Global Investments": {"ats": "icims", "token": "allspring", "tier": "Tier C2: Same or Below Benchmark"},
    "Alger": {"ats": "jobvite", "token": "alger", "tier": "Tier C2: Same or Below Benchmark"},
    "Beacon Platform": {"ats": "greenhouse", "token": "beaconplatform", "tier": "Tier C2: Same or Below Benchmark"},
}

# Auto-merge any newly discovered boards from data/discovered_ats_boards.json
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_discovered_path = os.path.join(_base_dir, "data", "discovered_ats_boards.json")
if os.path.exists(_discovered_path):
    try:
        with open(_discovered_path, "r", encoding="utf-8") as _df:
            _disc = json.load(_df)
            for _fname, _info in _disc.items():
                if _fname not in ATS_BOARD_REGISTRY:
                    ATS_BOARD_REGISTRY[_fname] = {
                        "ats": _info["ats"],
                        "token": _info["token"],
                        "tier": _info.get("tier", "Tier B: Main Focus")
                    }
    except Exception as _e:
        logger.warning(f"Could not auto-load discovered ATS boards: {_e}")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

class ATSScraper:
    def __init__(self, timeout: int = 15):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
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
                    
                    content = rj.get("content", "") or ""

                    job_entry = {
                        "job_id": f"gh_{board_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": dept_str,
                        "url": absolute_url,
                        "source_ats": "Greenhouse",
                        "description": content,
                        "updated_at": rj.get("updated_at")
                    }
                    # Extract posted salary disclosure
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)
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

                    job_entry = {
                        "job_id": f"lever_{site_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": team,
                        "url": hosted_url,
                        "source_ats": "Lever",
                        "description": description,
                        "updated_at": rj.get("createdAt")
                    }
                    # Extract posted salary disclosure
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)
            else:
                logger.warning(f"Lever board {site_token} returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Lever board {site_token}: {e}")
        return jobs

    def scrape_ashby_board(self, site_token: str, firm_name: str) -> List[Dict[str, Any]]:
        """
        Fetches live postings via Ashby API:
        GET https://api.ashbyhq.com/posting-api/job-board/{site_token}
        """
        url = f"https://api.ashbyhq.com/posting-api/job-board/{site_token}"
        jobs = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                raw_jobs = data.get("jobs", [])
                for rj in raw_jobs:
                    job_id = str(rj.get("id", ""))
                    title = rj.get("title", "")
                    job_url = rj.get("jobUrl", "") or f"https://jobs.ashbyhq.com/{site_token}/{job_id}"
                    loc = rj.get("location", "Unknown")
                    dept = rj.get("department", "") or rj.get("team", "")
                    desc = rj.get("descriptionPlain", "") or rj.get("descriptionHtml", "") or ""
                    comp = rj.get("compensation")

                    job_entry = {
                        "job_id": f"ashby_{site_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": dept,
                        "url": job_url,
                        "source_ats": "Ashby",
                        "description": desc,
                        "raw_compensation": comp,
                        "updated_at": rj.get("publishedAt")
                    }
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)
            else:
                logger.warning(f"Ashby board {site_token} returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Ashby board {site_token}: {e}")
        return jobs

    def scrape_smartrecruiters_board(self, site_token: str, firm_name: str) -> List[Dict[str, Any]]:
        """
        Fetches live postings via SmartRecruiters API:
        GET https://api.smartrecruiters.com/v1/companies/{site_token}/postings?limit=100
        """
        url = f"https://api.smartrecruiters.com/v1/companies/{site_token}/postings?limit=100"
        jobs = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                raw_jobs = data.get("content", [])
                for rj in raw_jobs:
                    job_id = str(rj.get("id", ""))
                    title = rj.get("name", "")
                    job_url = f"https://jobs.smartrecruiters.com/{site_token}/{job_id}"
                    loc_info = rj.get("location", {})
                    city = loc_info.get("city", "")
                    region = loc_info.get("region", "")
                    country = loc_info.get("country", "")
                    loc = ", ".join(filter(None, [city, region or country])) or "Unknown"
                    dept_info = rj.get("department", {})
                    dept = dept_info.get("label", "") if isinstance(dept_info, dict) else ""

                    job_entry = {
                        "job_id": f"sr_{site_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": dept,
                        "url": job_url,
                        "source_ats": "SmartRecruiters",
                        "description": title,
                        "updated_at": rj.get("releasedDate")
                    }
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)
            else:
                logger.warning(f"SmartRecruiters board {site_token} returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error scraping SmartRecruiters board {site_token}: {e}")
        return jobs

    def scrape_workable_board(self, site_token: str, firm_name: str) -> List[Dict[str, Any]]:
        """
        Fetches live postings via Workable API:
        GET https://apply.workable.com/api/v1/widget/accounts/{site_token}
        """
        url = f"https://apply.workable.com/api/v1/widget/accounts/{site_token}"
        jobs = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                raw_jobs = data.get("jobs", [])
                for rj in raw_jobs:
                    job_id = str(rj.get("shortcode", rj.get("id", "")))
                    title = rj.get("title", "")
                    job_url = rj.get("url", f"https://apply.workable.com/{site_token}/j/{job_id}/")
                    loc = rj.get("city", "") or rj.get("country", "Unknown")
                    dept = rj.get("department", "")

                    job_entry = {
                        "job_id": f"workable_{site_token}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": loc,
                        "department": dept,
                        "url": job_url,
                        "source_ats": "Workable",
                        "description": rj.get("description", ""),
                        "updated_at": rj.get("created_at")
                    }
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)
        except Exception as e:
            logger.error(f"Error scraping Workable board {site_token}: {e}")
        return jobs

    def scrape_firm(self, firm_name: str, ats_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        ats_type = ats_meta.get("ats")
        token = ats_meta.get("token")
        if ats_type == "greenhouse":
            return self.scrape_greenhouse_board(token, firm_name)
        elif ats_type == "lever":
            return self.scrape_lever_board(token, firm_name)
        elif ats_type == "ashby":
            return self.scrape_ashby_board(token, firm_name)
        elif ats_type == "smartrecruiters":
            return self.scrape_smartrecruiters_board(token, firm_name)
        elif ats_type == "workable":
            return self.scrape_workable_board(token, firm_name)
        elif ats_type == "workday":
            return self._scrape_workday(firm_name, token)
        elif ats_type == "icims":
            return self._scrape_icims(firm_name, token)
        elif ats_type == "jibe":
            return self._scrape_jibe(firm_name, token)
        elif ats_type == "jobvite":
            return self._scrape_jobvite(firm_name, token)
        else:
            return []

    def _scrape_workday(self, firm_name: str, token: str) -> List[Dict[str, Any]]:
        from crawler.workday_scraper import WorkdayScraper, WORKDAY_REGISTRY
        config = WORKDAY_REGISTRY.get(firm_name)
        if not config:
            logger.warning(f"No Workday CXS config for {firm_name}")
            return []
        scraper = WorkdayScraper(timeout=self.timeout)
        return scraper.scrape_workday_site(
            firm_name=firm_name,
            host=config["host"],
            tenant=config["tenant"],
            site=config["site"],
        )

    def _scrape_icims(self, firm_name: str, token: str) -> List[Dict[str, Any]]:
        from crawler.portal_scraper import PortalScraper, ICIMS_REGISTRY
        config = ICIMS_REGISTRY.get(firm_name)
        if not config:
            logger.warning(f"No iCIMS config for {firm_name}")
            return []
        scraper = PortalScraper(timeout=self.timeout)
        return scraper.scrape_icims_portal(
            firm_name=firm_name,
            base_url=config["base_url"],
        )

    def _scrape_jibe(self, firm_name: str, token: str) -> List[Dict[str, Any]]:
        from crawler.portal_scraper import PortalScraper, JIBE_REGISTRY
        config = JIBE_REGISTRY.get(firm_name)
        if not config:
            logger.warning(f"No Jibe config for {firm_name}")
            return []
        scraper = PortalScraper(timeout=self.timeout)
        return scraper.scrape_jibe_api(
            firm_name=firm_name,
            api_url=config["api_url"],
        )

    def _scrape_jobvite(self, firm_name: str, token: str) -> List[Dict[str, Any]]:
        from crawler.portal_scraper import PortalScraper, JOBVITE_REGISTRY
        config = JOBVITE_REGISTRY.get(firm_name)
        if not config:
            logger.warning(f"No Jobvite config for {firm_name}")
            return []
        scraper = PortalScraper(timeout=self.timeout)
        return scraper.scrape_jobvite_portal(
            firm_name=firm_name,
            base_url=config["base_url"],
        )


