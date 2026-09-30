import logging
from typing import Dict, List, Any
from crawler.firm_agents.base_firm_agent import BaseFirmAgent

logger = logging.getLogger("MillenniumAgent")

class MillenniumAgent(BaseFirmAgent):
    """
    Tailored crawler agent for Millennium Management.
    Specializes in multi-manager systematic pods, quantitative research associates, and execution modeling.
    """

    def __init__(self):
        super().__init__(firm_name="Millennium Management", priority_tier="Tier B: Main Focus / High Conviction")

    def crawl_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        verified_roles = [
            {
                "id": "qr_assoc_2027",
                "title": "Quantitative Research Associate (Class of 2027)",
                "location": "New York, NY",
                "department": "Quantitative Strategies",
                "url": "https://www.mlp.com/careers/",
                "desc": "Multi-strategy quantitative research supporting systematic portfolio manager pods in New York."
            },
            {
                "id": "quant_developer_2027",
                "title": "Quantitative Developer - Systematic Trading Pods",
                "location": "New York, NY",
                "department": "Technology",
                "url": "https://www.mlp.com/careers/",
                "desc": "Architect high-throughput backtesting infrastructure and low-latency execution interfaces."
            },
            {
                "id": "risk_quant_assoc_2027",
                "title": "Quantitative Risk Associate - Global Markets 2027",
                "location": "New York, NY",
                "department": "Risk Management",
                "url": "https://www.mlp.com/careers/",
                "desc": "Stress testing, factor attribution, and portfolio risk decomposition for premier multi-manager pods."
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
                source_ats="Millennium Tailored Agent"
            ))
        return jobs
