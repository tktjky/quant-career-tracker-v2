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
        from crawler.ats_scraper import ATSScraper
        scraper = ATSScraper(timeout=self.timeout)
        raw = scraper.scrape_firm(self.firm_name, {"ats": self.ats_type, "token": self.board_token})
        jobs = []
        for rj in raw:
            norm = self.normalize_job(
                job_id=str(rj.get("job_id", "")),
                title=rj.get("title", ""),
                url=rj.get("url", ""),
                location=rj.get("location", ""),
                department=rj.get("department", ""),
                description=rj.get("description", ""),
                source_ats=rj.get("source_ats", f"{self.ats_type} ({self.board_token})")
            )
            norm["posted_pay_range"] = rj.get("posted_pay_range", "")
            jobs.append(norm)
        return jobs
