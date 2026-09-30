import os
import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from crawler.ats_scraper import ATSScraper, ATS_BOARD_REGISTRY
from crawler.web_search_scraper import WebSearchScraper
from crawler.relevance_filter import score_job_suitability
from crawler.change_detector import ChangeDetector
from agent.firm_registry import FirmRegistry

logger = logging.getLogger("CrawlAgent")

class CrawlAgent:
    """
    Expert autonomous crawling agent that:
    1. Orchestrates tailored subagents for specific target firms.
    2. Executes multi-source scraping (ATS APIs + Custom Portals + Web Feeds).
    3. Evaluates role suitability against target MSFE 2027 profile.
    4. Detects state transitions (NEW vs ACTIVE vs CLOSED).
    5. Saves parsed results to data/live_openings.json and outputs summary reports.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.firms_csv = os.path.join(self.data_dir, "target_firms.csv")
        self.history_file = os.path.join(self.data_dir, "history_state.json")
        self.output_json = os.path.join(self.data_dir, "live_openings.json")
        self.output_summary = os.path.join(self.data_dir, "last_crawl_summary.json")

        self.ats_scraper = ATSScraper()
        self.web_scraper = WebSearchScraper()
        self.firm_registry = FirmRegistry()
        self.change_detector = ChangeDetector(self.history_file)
        self.firm_meta = self._load_firm_meta()

    def _load_firm_meta(self) -> Dict[str, Dict[str, Any]]:
        meta = {}
        if os.path.exists(self.firms_csv):
            try:
                with open(self.firms_csv, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        fn = row.get("firm_name", "").strip()
                        if fn:
                            meta[fn] = {
                                "industry_sector": row.get("industry_sector", ""),
                                "priority_tier": row.get("priority_tier", "Tier B: Main Focus"),
                                "priority_tag": row.get("priority_tag", "Main Focus"),
                                "estimated_comp": row.get("estimated_first_year_comp", "$220,000 - $380,000+"),
                                "comp_delta": row.get("comp_delta_vs_c1", "Superior"),
                                "strategic_advice": row.get("strategic_action_advice", "")
                            }
            except Exception as e:
                logger.error(f"Error loading target_firms.csv: {e}")
        return meta

    def crawl_single_firm(self, firm_name: str) -> Dict[str, Any]:
        """
        Runs a tailored crawler subagent for a single specific employer.
        """
        agent = self.firm_registry.get_agent_for_firm(firm_name)
        if not agent:
            # Fallback to ATS scraper if in registry
            logger.warning(f"No dedicated agent class for '{firm_name}', checking ATS registry...")
            if firm_name in ATS_BOARD_REGISTRY:
                reg = ATS_BOARD_REGISTRY[firm_name]
                raw_jobs = self.ats_scraper.scrape_firm(firm_name, reg)
            else:
                raw_jobs = self.web_scraper.search_live_postings(target_firms=[firm_name], query_keywords=["quantitative"])
        else:
            logger.info(f"Dispatching tailored subagent for '{firm_name}'...")
            raw_jobs = agent.crawl_jobs()

        firm_info = self.firm_meta.get(firm_name, {})
        tier_str = firm_info.get("priority_tier", "Tier B: Main Focus / High Conviction")

        scored_jobs = []
        for job in raw_jobs:
            score, analysis = score_job_suitability(job, firm_tier=tier_str)
            enriched_job = dict(job)
            enriched_job["suitability_score"] = score
            enriched_job["verdict"] = analysis["verdict"]
            enriched_job["recommendation"] = analysis["recommendation"]
            enriched_job["matched_signals"] = analysis["matched_positives"]
            enriched_job["penalties"] = analysis["penalties"]
            enriched_job["estimated_comp"] = firm_info.get("estimated_comp", "$220,000 - $380,000+")
            enriched_job["comp_delta_vs_c1"] = firm_info.get("comp_delta", "Substantially Superior (+20% to +107%)")
            enriched_job["priority_tier"] = tier_str
            enriched_job["priority_tag"] = firm_info.get("priority_tag", "Main Focus")
            scored_jobs.append(enriched_job)

        scored_jobs.sort(key=lambda x: x.get("suitability_score", 0), reverse=True)
        return {
            "firm_name": firm_name,
            "jobs_count": len(scored_jobs),
            "jobs": scored_jobs
        }

    def run_crawl(self, tier_filter: Optional[str] = None, max_boards: Optional[int] = None, specific_firm: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a crawl run across tailored subagents, target ATS boards, and custom portal feeds.
        """
        start_time = datetime.now()
        raw_candidates = []

        if specific_firm:
            firm_res = self.crawl_single_firm(specific_firm)
            raw_candidates.extend(firm_res["jobs"])
        else:
            # 1. First run tailored elite firm subagents (Jane Street, Citadel, Two Sigma, D.E. Shaw, Millennium, Point72, Goldman Sachs)
            for firm_name in ["Jane Street", "Citadel", "Two Sigma", "D.E. Shaw", "Millennium", "Point72", "Goldman Sachs"]:
                agent = self.firm_registry.get_agent_for_firm(firm_name)
                if agent:
                    logger.info(f"Running tailored crawler agent for {firm_name}...")
                    f_jobs = agent.crawl_jobs()
                    raw_candidates.extend(f_jobs)

            # 2. Run ATS scrapers for all configured firms
            crawled_count = 0
            for firm_name, registry_info in ATS_BOARD_REGISTRY.items():
                if tier_filter and tier_filter.lower() not in registry_info.get("tier", "").lower():
                    continue
                
                # Avoid duplicate crawling if already covered by tailored agent
                if firm_name in ["Two Sigma", "Point72"]:
                    continue

                if registry_info.get("ats") in ["greenhouse", "lever", "ashby"]:
                    board_jobs = self.ats_scraper.scrape_firm(firm_name, registry_info)
                    for j in board_jobs:
                        j["tier"] = registry_info.get("tier", "Tier B: Main Focus / High Conviction")
                        raw_candidates.append(j)
                    crawled_count += 1
                    if max_boards and crawled_count >= max_boards:
                        break

        # 3. Filter & Score candidates against target MSFE 2027 profile
        scored_jobs = []
        for job in raw_candidates:
            firm_name = job.get("firm_name", "Unknown")
            firm_info = self.firm_meta.get(firm_name, {})
            tier_str = firm_info.get("priority_tier") or job.get("tier", "Tier B")
            
            # If already scored in crawl_single_firm, reuse
            if "suitability_score" in job:
                scored_jobs.append(job)
                continue

            score, analysis = score_job_suitability(job, firm_tier=tier_str)
            
            # Keep roles with positive suitability (score >= 45) or explicit quant title
            if score >= 45 or analysis.get("has_quant_title"):
                enriched_job = dict(job)
                enriched_job["suitability_score"] = score
                enriched_job["verdict"] = analysis["verdict"]
                enriched_job["recommendation"] = analysis["recommendation"]
                enriched_job["matched_signals"] = analysis["matched_positives"]
                enriched_job["penalties"] = analysis["penalties"]
                enriched_job["estimated_comp"] = firm_info.get("estimated_comp", "$220,000 - $380,000+")
                enriched_job["comp_delta_vs_c1"] = firm_info.get("comp_delta", "Substantially Superior (+20% to +107%)")
                enriched_job["priority_tier"] = tier_str
                enriched_job["priority_tag"] = firm_info.get("priority_tag", "Main Focus")
                scored_jobs.append(enriched_job)

        # 4. Sort by Suitability Score descending, then tier
        scored_jobs.sort(key=lambda x: (x.get("suitability_score", 0), x.get("priority_tier", "")), reverse=True)

        # 5. Diff against state history
        updated_jobs, diff_stats = self.change_detector.diff_and_update(scored_jobs)

        # 6. Save live openings feed
        output_payload = {
            "last_updated": datetime.now().isoformat(),
            "candidate": {
                "cohort": "MSFE Class of 2027",
                "target": "Full-Time QR / QT / Strats Quant Roles",
                "benchmark": "Tier B+ High Conviction Priority"
            },
            "stats": {
                "total_live_openings": len(scored_jobs),
                "new_openings_this_crawl": diff_stats["new_openings"],
                "active_openings": diff_stats["retained_active"],
                "closed_openings": diff_stats["newly_closed"],
                "total_firms_evaluated": len({j.get("firm_name") for j in scored_jobs})
            },
            "openings": updated_jobs
        }

        with open(self.output_json, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)

        # Also write web/data.js for standalone browser / file:// access
        web_data_js = os.path.join(self.base_dir, "web", "data.js")
        try:
            with open(web_data_js, "w", encoding="utf-8") as f:
                f.write(f"window.LIVE_OPENINGS_DATA = {json.dumps(output_payload, indent=2, ensure_ascii=False)};\n")
        except Exception as e:
            logger.warning(f"Could not write web/data.js: {e}")

        summary_payload = {
            "crawl_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "diff_stats": diff_stats,
            "top_matches": [
                {
                    "firm": j.get("firm_name"),
                    "title": j.get("title"),
                    "location": j.get("location"),
                    "score": j.get("suitability_score"),
                    "url": j.get("url")
                }
                for j in updated_jobs[:10]
            ]
        }

        with open(self.output_summary, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2, ensure_ascii=False)

        return output_payload
