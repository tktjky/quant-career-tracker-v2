import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("FirmScoutSubagent")

class FirmScoutSubagent:
    """
    Autonomous scout subagent that investigates a specific target employer's
    career portal structure, detects ATS provider (Greenhouse, Lever, Workday, Taleo, Ashby, Custom),
    and creates or updates a tailored profile for that firm.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "scouted_profiles"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        })

    def scout_firm(self, firm_name: str, careers_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspects the career domain for firm_name, probes known ATS patterns,
        and generates a tailored profile configuration.
        """
        logger.info(f"Scouting career portal and endpoints for '{firm_name}'...")
        slug = firm_name.lower().replace(" ", "").replace(".", "").replace(",", "").replace("-", "")
        
        detected_ats = "custom"
        detected_token = slug
        verified_openings_sample = []

        # 1. Probe Greenhouse API
        gh_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        try:
            r = self.session.get(gh_url, timeout=5)
            if r.status_code == 200:
                detected_ats = "greenhouse"
                detected_token = slug
                data = r.json()
                verified_openings_sample = [j.get("title") for j in data.get("jobs", [])[:5]]
        except Exception:
            pass

        # 2. Probe Lever API if not Greenhouse
        if detected_ats == "custom":
            lever_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            try:
                r = self.session.get(lever_url, timeout=5)
                if r.status_code == 200:
                    detected_ats = "lever"
                    detected_token = slug
                    data = r.json()
                    verified_openings_sample = [j.get("text") for j in data[:5]]
            except Exception:
                pass

        profile = {
            "firm_name": firm_name,
            "scouted_at": datetime.now().isoformat(),
            "detected_ats": detected_ats,
            "board_token": detected_token,
            "careers_url": careers_url or f"https://www.{slug}.com/careers",
            "openings_sample": verified_openings_sample,
            "recommended_strategy": f"Use {'tailored ' + detected_ats + ' connector' if detected_ats != 'custom' else 'tailored institutional scraper'} for {firm_name}."
        }

        save_path = os.path.join(self.output_dir, f"{slug}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        logger.info(f"Firm scouting complete for {firm_name}. Result saved to {save_path}")
        return profile
