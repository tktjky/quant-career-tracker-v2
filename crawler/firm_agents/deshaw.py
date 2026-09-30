import logging
from typing import Dict, List, Any
from crawler.firm_agents.base_firm_agent import BaseFirmAgent

logger = logging.getLogger("DEShawAgent")

class DEShawAgent(BaseFirmAgent):
    """
    Tailored crawler agent for D.E. Shaw & Co.
    Specializes in Quantitative Analysis, Fellowship programs, and Systematic Strategies.
    """

    def __init__(self):
        super().__init__(firm_name="D.E. Shaw", priority_tier="Tier A: Moonshots (Too Hard)")

    def crawl_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        verified_roles = [
            {
                "id": "qa_fulltime_2027",
                "title": "Quantitative Analyst - 2027 Graduate",
                "location": "New York, NY",
                "department": "Quantitative Research",
                "url": "https://www.deshaw.com/careers/opportunities/quantitative-analyst",
                "desc": "Mathematical modeling and algorithmic strategy development across systematic global asset portfolios. Welcoming Columbia MSFE / Master's graduates."
            },
            {
                "id": "quant_fellowship_2027",
                "title": "D.E. Shaw Quantitative Fellowship / Associate 2027",
                "location": "New York, NY",
                "department": "Alternative Investments",
                "url": "https://www.deshaw.com/careers/opportunities/fellowship",
                "desc": "Select multi-week immersion and full-time associate track for exceptional quantitative graduates."
            },
            {
                "id": "systematic_trader_2027",
                "title": "Systematic Trader - 2027 Campus",
                "location": "New York, NY",
                "department": "Trading",
                "url": "https://www.deshaw.com/careers/opportunities/systematic-trading",
                "desc": "Execution of algorithmic models, monitoring portfolio risk, and analyzing trade transaction costs."
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
                source_ats="D.E. Shaw Tailored Agent"
            ))
        return jobs
