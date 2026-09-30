import unittest
import os
import json
from crawler.relevance_filter import score_job_suitability, CANDIDATE_PROFILE
from crawler.change_detector import ChangeDetector
from crawler.web_search_scraper import WebSearchScraper
from agent.crawl_agent import CrawlAgent

class TestJobTrackerV2(unittest.TestCase):

    def test_candidate_profile(self):
        self.assertEqual(CANDIDATE_PROFILE["graduation_year"], 2027)
        self.assertEqual(CANDIDATE_PROFILE["target_degree"], "MSFE / Quantitative Finance")

    def test_relevance_scoring_high_match(self):
        job = {
            "title": "Quantitative Trader - Full Time 2027 Campus",
            "location": "New York, NY",
            "department": "Trading",
            "description": "Graduating Master's student in financial engineering or quantitative finance."
        }
        score, analysis = score_job_suitability(job, firm_tier="Tier B: Main Focus")
        self.assertGreaterEqual(score, 75)
        self.assertTrue(analysis["has_quant_title"])
        self.assertIn("HIGH PRIORITY", analysis["verdict"])

    def test_relevance_scoring_penalties(self):
        job = {
            "title": "Managing Director - Human Resources",
            "location": "New York, NY",
            "department": "HR",
            "description": "15+ years experience leading human resources."
        }
        score, analysis = score_job_suitability(job, firm_tier="Tier B: Main Focus")
        self.assertLess(score, 30)
        self.assertGreater(len(analysis["penalties"]), 0)

    def test_change_detector_flow(self):
        test_history_path = "/tmp/test_tracker_history.json"
        if os.path.exists(test_history_path):
            os.remove(test_history_path)

        detector = ChangeDetector(test_history_path)
        
        batch1 = [
            {"job_id": "job_1", "firm_name": "Jump Trading", "title": "Quantitative Researcher", "location": "Chicago"},
            {"job_id": "job_2", "firm_name": "Jane Street", "title": "Quantitative Trader", "location": "New York"}
        ]
        res1, stats1 = detector.diff_and_update(batch1)
        self.assertEqual(stats1["new_openings"], 2)
        self.assertEqual(stats1["retained_active"], 0)

        # Batch 2: job_1 stays, job_2 missing (closed for Jane Street), job_3 new
        batch2 = [
            {"job_id": "job_1", "firm_name": "Jump Trading", "title": "Quantitative Researcher", "location": "Chicago"},
            {"job_id": "job_3", "firm_name": "Citadel", "title": "Quantitative Researcher", "location": "New York"}
        ]
        res2, stats2 = detector.diff_and_update(batch2)
        self.assertEqual(stats2["new_openings"], 1)
        self.assertEqual(stats2["retained_active"], 1)

        if os.path.exists(test_history_path):
            os.remove(test_history_path)

    def test_web_search_scraper_portal_feed(self):
        scraper = WebSearchScraper()
        jobs = scraper.search_live_postings(target_firms=[], query_keywords=["quantitative"])
        self.assertGreater(len(jobs), 5)
        jane_street_jobs = [j for j in jobs if j["firm_name"] == "Jane Street"]
        self.assertGreater(len(jane_street_jobs), 0)

    def test_crawl_agent_instantiation(self):
        agent = CrawlAgent()
        self.assertTrue(os.path.exists(agent.firms_csv))
        self.assertGreater(len(agent.firm_meta), 50)

if __name__ == "__main__":
    unittest.main()
