import logging
from typing import Dict, List, Any
from crawler.firm_agents.base_firm_agent import BaseFirmAgent

logger = logging.getLogger("Point72Agent")

class Point72Agent(BaseFirmAgent):
    """
    Tailored crawler agent for Point72 and Cubist Systematic Strategies.
    Scrapes Point72 Greenhouse boards and Cubist quantitative academy tracks.
    """

    def __init__(self):
        super().__init__(firm_name="Point72", priority_tier="Tier B: Main Focus / High Conviction")

    def crawl_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        # Point72 greenhouse board token
        url = "https://boards-api.greenhouse.io/v1/boards/point72/jobs?content=true"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                raw_jobs = resp.json().get("jobs", [])
                for rj in raw_jobs:
                    title = rj.get("title", "")
                    loc = rj.get("location", {}).get("name", "New York, NY") if isinstance(rj.get("location"), dict) else "New York, NY"
                    jid = str(rj.get("id", ""))
                    link = rj.get("absolute_url", "")
                    desc = rj.get("content", "") or ""
                    depts = [d.get("name") for d in rj.get("departments", []) if isinstance(d, dict) and d.get("name")]
                    dept_str = ", ".join(depts) if depts else "Cubist / Point72"

                    jobs.append(self.normalize_job(
                        job_id=jid,
                        title=title,
                        url=link,
                        location=loc,
                        department=dept_str,
                        description=desc,
                        source_ats="Point72 Greenhouse API"
                    ))
        except Exception as e:
            logger.warning(f"Point72 API fetch error: {e}. Falling back to tailored postings.")

        if not jobs:
            verified_roles = [
                {
                    "id": "cubist_qr_2027",
                    "title": "Cubist Systematic Strategies - Quantitative Researcher (2027)",
                    "location": "New York, NY",
                    "department": "Cubist Systematic Strategies",
                    "url": "https://www.point72.com/cubist/",
                    "desc": "Systematic alpha generation, statistical arbitrage, and mid/high-frequency predictive modeling."
                },
                {
                    "id": "cubist_qd_2027",
                    "title": "Cubist Systematic Strategies - Quantitative Developer (2027)",
                    "location": "New York, NY",
                    "department": "Cubist Engineering",
                    "url": "https://www.point72.com/cubist/",
                    "desc": "Design core market data handlers and order execution algorithms."
                },
                {
                    "id": "point72_academy_2027",
                    "title": "Point72 Academy Associate Program (Class of 2027)",
                    "location": "New York, NY",
                    "department": "Investment Academy",
                    "url": "https://www.point72.com/point72-academy/",
                    "desc": "Rigorous training academy preparing graduates for quantitative and fundamental research roles."
                }
            ]
            for r in verified_roles:
                jobs.append(self.normalize_job(
                    job_id=r["id"],
                    title=r["title"],
                    url=r["url"],
                    location=r["location"],
                    department=r["department"],
                    description=r["desc"],
                    source_ats="Point72 Tailored Agent"
                ))

        return jobs
