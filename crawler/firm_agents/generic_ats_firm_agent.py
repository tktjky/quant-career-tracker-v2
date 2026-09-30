import logging
from typing import Dict, List, Any
from crawler.firm_agents.base_firm_agent import BaseFirmAgent

logger = logging.getLogger("GenericATSAgent")

class GenericATSAgent(BaseFirmAgent):
    """
    Worker tailored for any employer operating on standard ATS platforms
    (Greenhouse, Lever, Ashby) with specific board token parameters.
    """

    def __init__(self, firm_name: str, ats_type: str, board_token: str, priority_tier: str = "Tier B: Main Focus / High Conviction"):
        super().__init__(firm_name=firm_name, priority_tier=priority_tier)
        self.ats_type = ats_type.lower()
        self.board_token = board_token

    def crawl_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        if self.ats_type == "greenhouse":
            url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs?content=true"
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for rj in data.get("jobs", []):
                        jid = str(rj.get("id", ""))
                        title = rj.get("title", "")
                        loc = rj.get("location", {}).get("name", "Unknown") if isinstance(rj.get("location"), dict) else str(rj.get("location") or "")
                        link = rj.get("absolute_url", "")
                        desc = rj.get("content", "") or ""
                        depts = [d.get("name") for d in rj.get("departments", []) if isinstance(d, dict) and d.get("name")]
                        dept_str = ", ".join(depts) if depts else ""
                        jobs.append(self.normalize_job(
                            job_id=jid,
                            title=title,
                            url=link,
                            location=loc,
                            department=dept_str,
                            description=desc,
                            source_ats=f"Greenhouse ({self.board_token})"
                        ))
            except Exception as e:
                logger.warning(f"Error scraping Greenhouse board {self.board_token}: {e}")

        elif self.ats_type == "lever":
            url = f"https://api.lever.co/v0/postings/{self.board_token}?mode=json"
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for rj in data:
                        jid = str(rj.get("id", ""))
                        title = rj.get("text", "")
                        link = rj.get("hostedUrl", "")
                        categories = rj.get("categories", {})
                        loc = categories.get("location", "Unknown") if isinstance(categories, dict) else "Unknown"
                        team = categories.get("team", "") if isinstance(categories, dict) else ""
                        desc = rj.get("descriptionPlain", "") or ""
                        jobs.append(self.normalize_job(
                            job_id=jid,
                            title=title,
                            url=link,
                            location=loc,
                            department=team,
                            description=desc,
                            source_ats=f"Lever ({self.board_token})"
                        ))
            except Exception as e:
                logger.warning(f"Error scraping Lever board {self.board_token}: {e}")

        return jobs
