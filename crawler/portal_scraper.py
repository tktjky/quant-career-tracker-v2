"""
iCIMS / Jibe Career Portal Scraper.

Scrapes iCIMS-powered career portals via their public search endpoints:
- iCIMS iframe search: GET https://{portal}.icims.com/jobs/search?in_iframe=1&searchKeyword={term}
- Jibe API: GET https://careers.{domain}/api/jobs
"""

import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

from crawler.salary_extractor import extract_posted_pay_range

logger = logging.getLogger("PortalScraper")

ICIMS_REGISTRY = {
    "MSCI": {
        "portal": "uscareers-msci",
        "base_url": "https://uscareers-msci.icims.com",
    },
}

JIBE_REGISTRY = {
    "SIG": {
        "api_url": "https://careers.sig.com/api/jobs",
        "careers_url": "https://careers.sig.com",
    },
}


class PortalScraper:
    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.timeout = timeout

    def scrape_icims_portal(self, firm_name: str, base_url: str,
                            search_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if search_keywords is None:
            search_keywords = ["quantitative", "quant", "trading", "data science"]

        seen_ids = set()
        jobs = []

        for keyword in search_keywords:
            url = f"{base_url}/jobs/search?in_iframe=1&searchKeyword={keyword}"
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/jobs/" not in href or "login" in href or "search" in href:
                        continue

                    m = re.search(r"/jobs/(\d+)/", href)
                    if not m:
                        continue
                    job_id = m.group(1)
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title_raw = a.get_text(strip=True)
                    title = re.sub(r"^Title", "", title_raw).strip()

                    full_url = href if href.startswith("http") else f"{base_url}{href}"
                    full_url = re.sub(r"[?&]in_iframe=1", "", full_url)

                    job_entry = {
                        "job_id": f"icims_{firm_name.lower().replace(' ', '_')}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": "Unknown",
                        "department": "",
                        "url": full_url,
                        "source_ats": "iCIMS",
                        "description": title,
                        "updated_at": None,
                    }
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)

            except Exception as e:
                logger.error(f"Error scraping iCIMS portal {firm_name} ({base_url}): {e}")

        logger.info(f"iCIMS [{firm_name}]: {len(jobs)} postings found")
        return jobs

    def scrape_jibe_api(self, firm_name: str, api_url: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            resp = self.session.get(api_url, timeout=self.timeout,
                                    headers={"Accept": "application/json"})
            if resp.status_code != 200:
                logger.warning(f"Jibe API {firm_name} returned HTTP {resp.status_code}")
                return jobs

            data = resp.json()
            raw_jobs = data.get("jobs", [])
            total = data.get("totalCount", len(raw_jobs))
            logger.info(f"Jibe API [{firm_name}]: {total} total positions reported")

            for rj in raw_jobs:
                jdata = rj.get("data", rj)
                job_id = str(jdata.get("req_id", jdata.get("id", "")))
                title = jdata.get("title", "")
                city = jdata.get("city", "")
                state = jdata.get("state", "")
                loc = ", ".join(filter(None, [city, state])) or "Unknown"
                dept = jdata.get("department", "")
                slug = jdata.get("slug", "")
                job_url = jdata.get("apply_url", "")
                if not job_url and slug:
                    base = api_url.rsplit("/api", 1)[0]
                    job_url = f"{base}/job/{slug}"

                job_entry = {
                    "job_id": f"jibe_{firm_name.lower().replace(' ', '_')}_{job_id}",
                    "firm_name": firm_name,
                    "title": title,
                    "location": loc,
                    "department": dept,
                    "url": job_url,
                    "source_ats": "Jibe/iCIMS",
                    "description": title,
                    "updated_at": None,
                }
                job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                jobs.append(job_entry)

        except Exception as e:
            logger.error(f"Error scraping Jibe API {firm_name}: {e}")

        return jobs
