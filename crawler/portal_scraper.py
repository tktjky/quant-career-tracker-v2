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
    "GTS": {
        "portal": "careers-gtsx",
        "base_url": "https://careers-gtsx.icims.com",
    },
    "Charles Schwab": {
        "portal": "career-schwab",
        "base_url": "https://career-schwab.icims.com",
    },
    "Allspring Global Investments": {
        "portal": "careers-allspringglobal",
        "base_url": "https://careers-allspringglobal.icims.com",
    },
}

JIBE_REGISTRY = {
    "SIG": {
        "api_url": "https://careers.sig.com/api/jobs",
        "careers_url": "https://careers.sig.com",
    },
    "SIG (Susquehanna International Group)": {
        "api_url": "https://careers.sig.com/api/jobs",
        "careers_url": "https://careers.sig.com",
    },
}

JOBVITE_REGISTRY = {
    "Alger": {
        "base_url": "https://jobs.jobvite.com/alger",
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
                    title = re.sub(r"^(?:Job\s*Posting\s*Title|Job\s*Title|Title)\s*:?\s*", "", title_raw, flags=re.IGNORECASE).strip()

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
        page = 1
        limit = 100
        seen_ids = set()

        while True:
            try:
                sep = "&" if "?" in api_url else "?"
                page_url = f"{api_url}{sep}limit={limit}&page={page}"
                resp = self.session.get(page_url, timeout=self.timeout,
                                        headers={"Accept": "application/json"})
                if resp.status_code != 200:
                    logger.warning(f"Jibe API {firm_name} (page {page}) returned HTTP {resp.status_code}")
                    break

                data = resp.json()
                raw_jobs = data.get("jobs", [])
                total = data.get("totalCount", len(raw_jobs))
                if page == 1:
                    logger.info(f"Jibe API [{firm_name}]: {total} total positions reported")

                if not raw_jobs:
                    break

                for rj in raw_jobs:
                    jdata = rj.get("data", rj)
                    job_id = str(jdata.get("req_id", jdata.get("id", "")))
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = jdata.get("title", "")
                    city = jdata.get("city", "")
                    state = jdata.get("state", "")
                    loc = ", ".join(filter(None, [city, state])) or "Unknown"
                    dept = jdata.get("department", "")
                    slug = str(jdata.get("slug", job_id))

                    base = api_url.rsplit("/api", 1)[0]
                    job_url = f"{base}/jobs/{slug}"

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

                if len(jobs) >= total or len(raw_jobs) < limit or page >= 5:
                    break
                page += 1

            except Exception as e:
                logger.error(f"Error scraping Jibe API {firm_name} (page {page}): {e}")
                break

        logger.info(f"Jibe API [{firm_name}]: retrieved {len(jobs)} jobs across {page} pages")
        return jobs

    def scrape_jobvite_portal(self, firm_name: str, base_url: str) -> List[Dict[str, Any]]:
        """Scrapes Jobvite career portal (e.g., https://jobs.jobvite.com/{company})."""
        jobs = []
        try:
            resp = self.session.get(base_url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(f"Jobvite portal {firm_name} ({base_url}) returned {resp.status_code}")
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            seen_ids = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/job/" in href:
                    job_id = href.rstrip("/").split("/")[-1]
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    title = a.get_text(strip=True)
                    if not title or title.lower() in ["apply", "view"]:
                        continue
                    full_url = href if href.startswith("http") else f"https://jobs.jobvite.com{href}"
                    job_entry = {
                        "job_id": f"jobvite_{firm_name.lower().replace(' ', '_')}_{job_id}",
                        "firm_name": firm_name,
                        "title": title,
                        "location": "Unknown",
                        "department": "",
                        "url": full_url,
                        "source_ats": "Jobvite",
                        "description": title,
                        "updated_at": None,
                    }
                    job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                    jobs.append(job_entry)
        except Exception as e:
            logger.error(f"Error scraping Jobvite portal {firm_name} ({base_url}): {e}")

        logger.info(f"Jobvite [{firm_name}]: retrieved {len(jobs)} jobs")
        return jobs

