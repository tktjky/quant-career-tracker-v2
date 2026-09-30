import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("BaseFirmAgent")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

class BaseFirmAgent(ABC):
    """
    Abstract base class for a tailored firm crawler agent.
    Each firm agent specializes in:
      1. Knowing the exact careers API / portal structure of that specific firm.
      2. Constructing tailored requests (handling auth, pagination, session cookies, search parameters).
      3. Normalizing extracted jobs into a standardized schema for quantitative suitability scoring.
    """

    def __init__(self, firm_name: str, priority_tier: str = "Tier B: Main Focus / High Conviction", timeout: int = 12):
        self.firm_name = firm_name
        self.priority_tier = priority_tier
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    @abstractmethod
    def crawl_jobs(self) -> List[Dict[str, Any]]:
        """
        Executes the tailored crawl logic for this specific firm.
        Returns a list of standardized job dictionaries:
          {
            "job_id": str,
            "firm_name": str,
            "title": str,
            "location": str,
            "department": str,
            "url": str,
            "source_ats": str,
            "tier": str,
            "description": str,
            "updated_at": str
          }
        """
        pass

    def normalize_job(
        self,
        job_id: str,
        title: str,
        url: str,
        location: str = "New York, NY",
        department: str = "",
        description: str = "",
        source_ats: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "job_id": f"{self.firm_name.lower().replace(' ', '_')}_{job_id}",
            "firm_name": self.firm_name,
            "title": title.strip(),
            "location": location.strip() or "New York, NY",
            "department": department.strip(),
            "url": url.strip(),
            "source_ats": source_ats or f"{self.firm_name} Tailored Crawler",
            "tier": self.priority_tier,
            "description": description.strip(),
            "updated_at": datetime.now().isoformat()
        }
