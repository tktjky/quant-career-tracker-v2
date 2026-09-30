"""
Workday CXS JSON API Scraper.

Scrapes Workday-powered career portals via their public CXS REST endpoint:
    POST https://{host}/wday/cxs/{tenant}/{site}/jobs
    Payload: {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "quantitative"}

Only works for tenants where the CXS endpoint is publicly accessible
without session authentication.
"""

import logging
import requests
from typing import Dict, List, Any, Optional

from crawler.salary_extractor import extract_posted_pay_range

logger = logging.getLogger("WorkdayScraper")

# Verified Workday CXS endpoints that return 200 with public JSON
WORKDAY_REGISTRY = {
    "BlackRock": {
        "host": "blackrock.wd1.myworkdayjobs.com",
        "tenant": "blackrock",
        "site": "BlackRock_Professional",
    },
    "State Street": {
        "host": "statestreet.wd1.myworkdayjobs.com",
        "tenant": "statestreet",
        "site": "Global",
    },
    "Morningstar": {
        "host": "morningstar.wd5.myworkdayjobs.com",
        "tenant": "morningstar",
        "site": "Morningstar",
    },
    "CME Group": {
        "host": "cmegroup.wd1.myworkdayjobs.com",
        "tenant": "cmegroup",
        "site": "CME_Careers",
    },
    "Arrowstreet Capital": {
        "host": "arrowstreetcapital.wd5.myworkdayjobs.com",
        "tenant": "arrowstreetcapital",
        "site": "Arrowstreet",
    },
    "Options Clearing Corporation (OCC)": {
        "host": "theocc.wd5.myworkdayjobs.com",
        "tenant": "theocc",
        "site": "careers",
    },
    "PEAK6": {
        "host": "peak6group.wd1.myworkdayjobs.com",
        "tenant": "peak6group",
        "site": "PEAK6",
    },
}

WORKDAY_SEARCH_TERMS = ["quantitative", "quant", "trading", "data scientist"]


class WorkdayScraper:
    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.timeout = timeout

    def scrape_workday_site(self, firm_name: str, host: str, tenant: str, site: str,
                            search_terms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scrape a single Workday CXS endpoint, deduplicating across multiple search terms."""
        if search_terms is None:
            search_terms = WORKDAY_SEARCH_TERMS

        url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        seen_ids = set()
        jobs = []

        for term in search_terms:
            offset = 0
            while True:
                payload = {
                    "appliedFacets": {},
                    "limit": 20,
                    "offset": offset,
                    "searchText": term,
                }
                try:
                    resp = self.session.post(url, json=payload, timeout=self.timeout)
                    if resp.status_code != 200:
                        logger.warning(f"Workday {firm_name} ({host}) returned HTTP {resp.status_code} for term '{term}'")
                        break

                    data = resp.json()
                    postings = data.get("jobPostings", [])
                    total = data.get("total", 0)

                    if not postings:
                        break

                    for p in postings:
                        ext_path = p.get("externalPath", "")
                        title = p.get("title", "")
                        loc = p.get("locationsText", "Unknown")
                        posted = p.get("postedOn", "")

                        if ext_path in seen_ids:
                            continue
                        seen_ids.add(ext_path)

                        job_url = f"https://{host}/{site}{ext_path}" if ext_path else ""

                        job_entry = {
                            "job_id": f"wd_{tenant}_{ext_path.split('_')[-1] if '_' in ext_path else ext_path}",
                            "firm_name": firm_name,
                            "title": title,
                            "location": loc,
                            "department": "",
                            "url": job_url,
                            "source_ats": "Workday CXS",
                            "description": title,
                            "updated_at": posted,
                        }
                        job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                        jobs.append(job_entry)

                    offset += len(postings)
                    if offset >= total:
                        break

                except Exception as e:
                    logger.error(f"Error scraping Workday {firm_name} ({host}): {e}")
                    break

        logger.info(f"Workday CXS [{firm_name}]: {len(jobs)} total postings scraped across {len(search_terms)} search terms")
        return jobs

    def scrape_all_registered(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape all firms in the WORKDAY_REGISTRY."""
        all_results = {}
        for firm_name, config in WORKDAY_REGISTRY.items():
            jobs = self.scrape_workday_site(
                firm_name=firm_name,
                host=config["host"],
                tenant=config["tenant"],
                site=config["site"],
            )
            all_results[firm_name] = jobs
        return all_results
