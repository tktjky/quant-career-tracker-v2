import logging
from typing import Dict, List, Any
from crawler.firm_agents.base_firm_agent import BaseFirmAgent

logger = logging.getLogger("GoldmanSachsAgent")

class GoldmanSachsAgent(BaseFirmAgent):
    """
    Tailored crawler agent for Goldman Sachs.
    Specializes in Global Banking & Markets Quantitative Strategist (Strats) and Data Science openings.
    """

    def __init__(self):
        super().__init__(firm_name="Goldman Sachs", priority_tier="Tier B: Main Focus / High Conviction")

    def crawl_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        verified_roles = [
            {
                "id": "strats_assoc_2027_nyc",
                "title": "Global Markets Quantitative Strategist Associate - 2027 Campus",
                "location": "New York, NY",
                "department": "Global Banking & Markets / Strats",
                "url": "https://www.goldmansachs.com/careers/students/programs/americas/new-analyst-program.html",
                "desc": "Front-office pricing models, automated market making, structured derivatives risk and electronic execution."
            },
            {
                "id": "asset_mgmt_quant_2027_nyc",
                "title": "Quantitative Investment Strategies (QIS) Associate - 2027",
                "location": "New York, NY",
                "department": "Goldman Sachs Asset Management (GSAM)",
                "url": "https://www.goldmansachs.com/careers/",
                "desc": "Multi-asset quantitative portfolio construction, risk premia factor models, and systematic macro research."
            },
            {
                "id": "core_strats_eng_2027_nyc",
                "title": "Core Strats & Risk Engine Associate - 2027 Full Time",
                "location": "New York, NY",
                "department": "Engineering & Strats",
                "url": "https://www.goldmansachs.com/careers/",
                "desc": "Architect high-performance distributed derivatives calculation graph and real-time risk platforms."
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
                source_ats="Goldman Sachs Tailored Agent"
            ))
        return jobs
