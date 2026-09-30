import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("ChangeDetector")

class ChangeDetector:
    """
    Tracks state of job listings across crawls.
    Detects:
      - NEW openings (first observed in current crawl)
      - ACTIVE openings (still present)
      - CLOSED/EXPIRED openings (previously seen, now missing)
    """

    def __init__(self, history_file: str):
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load history from {self.history_file}: {e}")
        return {"tracked_jobs": {}, "last_crawl_timestamp": None}

    def save_history(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.history_file)), exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def diff_and_update(self, current_jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Takes a list of currently scraped jobs and diffs against history.
        Tags each job with:
          'status': 'NEW' | 'ACTIVE' | 'CLOSED'
          'first_seen': ISO timestamp
          'last_seen': ISO timestamp
        Returns:
          updated_jobs_list, stats_summary
        """
        now_iso = datetime.now().isoformat()
        current_job_keys = set()
        result_jobs = []

        new_count = 0
        active_count = 0

        tracked = self.history.get("tracked_jobs", {})

        for job in current_jobs:
            # Deterministic unique key: firm + job_id (or firm + title + location)
            job_id = job.get("job_id") or ""
            firm = job.get("firm_name", "Unknown")
            title = job.get("title", "")
            location = job.get("location", "")
            
            key = f"{firm}::{job_id}" if job_id else f"{firm}::{title}::{location}"
            current_job_keys.add(key)

            if key not in tracked:
                # Brand new opening
                new_count += 1
                job_record = dict(job)
                job_record["key"] = key
                job_record["status"] = "NEW"
                job_record["first_seen"] = now_iso
                job_record["last_seen"] = now_iso
                job_record["consecutive_misses"] = 0
                tracked[key] = job_record
                result_jobs.append(job_record)
            else:
                # Previously seen job
                active_count += 1
                prev_record = tracked[key]
                # If it was marked closed previously, it's re-opened
                status = "REOPENED" if prev_record.get("status") == "CLOSED" else "ACTIVE"
                
                # Update latest fields
                prev_record.update(job)
                prev_record["status"] = status
                prev_record["last_seen"] = now_iso
                prev_record["consecutive_misses"] = 0
                result_jobs.append(prev_record)

        # Detect closed jobs for firms that were crawled
        crawled_firms = {j.get("firm_name") for j in current_jobs if j.get("firm_name")}
        closed_count = 0
        for key, prev_record in tracked.items():
            if prev_record.get("firm_name") in crawled_firms and key not in current_job_keys:
                if prev_record.get("status") != "CLOSED":
                    misses = prev_record.get("consecutive_misses", 0) + 1
                    prev_record["consecutive_misses"] = misses
                    # Only mark closed if missing
                    if misses >= 1:
                        prev_record["status"] = "CLOSED"
                        prev_record["closed_at"] = now_iso
                        closed_count += 1

        self.history["last_crawl_timestamp"] = now_iso
        self.save_history()

        stats = {
            "total_active_scraped": len(current_jobs),
            "new_openings": new_count,
            "retained_active": active_count,
            "newly_closed": closed_count,
            "total_tracked_all_time": len(tracked)
        }
        return result_jobs, stats
