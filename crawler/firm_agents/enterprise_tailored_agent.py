import logging
import requests
from typing import Dict, List, Any
from crawler.firm_agents.base_firm_agent import BaseFirmAgent
from crawler.salary_extractor import extract_posted_pay_range

logger = logging.getLogger("EnterpriseTailoredAgent")

class EnterpriseTailoredAgent(BaseFirmAgent):
    """
    Tailored crawler agent for elite enterprise employers with proprietary APIs,
    structured search backends, or verified campus program feeds.
    """

    def __init__(self, firm_name: str, priority_tier: str, portal_url: str, verified_roles: List[Dict[str, Any]]):
        super().__init__(firm_name=firm_name, priority_tier=priority_tier)
        self.portal_url = portal_url
        self.verified_roles = verified_roles

    def crawl_jobs(self) -> List[Dict[str, Any]]:
        jobs = []

        # 1. First attempt dynamic API / structured search if supported
        if self.firm_name == "Amazon":
            try:
                url = "https://www.amazon.jobs/en/search.json?base_query=economist&result_type=jobs&sort=recent"
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for rj in data.get("jobs", [])[:10]:
                        title = rj.get("title", "")
                        job_path = rj.get("job_path", "")
                        full_url = f"https://www.amazon.jobs{job_path}" if job_path else self.portal_url
                        loc = rj.get("location_normalized") or rj.get("location") or "Seattle, WA / New York, NY"
                        desc = rj.get("description_short", "") or title
                        jid = str(rj.get("id", rj.get("job_path", "").split("/")[-1]))

                        job_entry = self.normalize_job(
                            job_id=jid,
                            title=title,
                            url=full_url,
                            location=loc,
                            department="Amazon Economics & Machine Learning",
                            description=desc,
                            source_ats="Amazon Jobs API"
                        )
                        job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                        jobs.append(job_entry)
            except Exception as e:
                logger.warning(f"Error querying Amazon API: {e}")

        elif self.firm_name == "Citigroup":
            try:
                url = "https://jobs.citi.com/search-jobs/quantitative/287/1"
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "html.parser")
                    anchors = soup.select("section#search-results-list ul li a, ul#search-results-list li a, .search-results-list li a")
                    for a in anchors[:8]:
                        title = a.get_text(strip=True)
                        href = a.get("href", "")
                        full_url = f"https://jobs.citi.com{href}" if href.startswith("/") else href
                        jid = href.rstrip("/").split("/")[-1] if href else title.replace(" ", "_")
                        job_entry = self.normalize_job(
                            job_id=jid,
                            title=title,
                            url=full_url,
                            location="New York, NY",
                            department="Markets Quantitative Analysis",
                            description=title,
                            source_ats="Citi Career Portal"
                        )
                        job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
                        jobs.append(job_entry)
            except Exception as e:
                logger.warning(f"Error querying Citi Portal: {e}")

        # 2. If dynamic parsing returned jobs, return them
        if jobs:
            return jobs

        # 3. Fallback to audited, verified front-office campus/experienced roles
        for r in self.verified_roles:
            job_entry = self.normalize_job(
                job_id=r["id"],
                title=r["title"],
                url=r.get("url", self.portal_url),
                location=r.get("location", "New York, NY"),
                department=r.get("department", "Quantitative Analytics"),
                description=r.get("desc", r["title"]),
                source_ats=f"{self.firm_name} Tailored Agent"
            )
            job_entry["posted_pay_range"] = extract_posted_pay_range(job_entry)
            jobs.append(job_entry)

        return jobs
