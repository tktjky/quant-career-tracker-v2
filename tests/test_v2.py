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
        self.assertEqual(CANDIDATE_PROFILE["target_degree"], "Quantitative Finance / Financial Engineering")

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

    def test_firm_tier_and_industry_metadata(self):
        agent = CrawlAgent()
        coinbase = agent.firm_meta.get("Coinbase")
        self.assertIsNotNone(coinbase)
        self.assertEqual(coinbase["priority_tier"], "Tier B: Main Focus")
        self.assertEqual(coinbase["industry_sector"], "FinTech & Elite Tech")

        robinhood = agent.firm_meta.get("Robinhood")
        self.assertIsNotNone(robinhood)
        self.assertEqual(robinhood["priority_tier"], "Tier B: Main Focus")
        self.assertEqual(robinhood["industry_sector"], "FinTech & Elite Tech")

        goldman = agent.firm_meta.get("Goldman Sachs")
        self.assertIsNotNone(goldman)
        self.assertEqual(goldman["priority_tier"], "Tier C1: Same or Above Benchmark")
        self.assertEqual(goldman["industry_sector"], "Bulge Bracket & Global Investment Banks")

        openai = agent.firm_meta.get("OpenAI")
        self.assertIsNotNone(openai)
        self.assertEqual(openai["priority_tier"], "Tier A: Too Hard")
        self.assertEqual(openai["industry_sector"], "FinTech & Elite Tech")

    def test_intern_summer_hard_disqualification(self):
        intern_jobs = [
            {"title": "Quantitative Research Intern - Summer 2027", "location": "New York, NY", "department": "Trading"},
            {"title": "Summer Analyst - Global Markets Quantitative Strats", "location": "New York, NY", "department": "Strats"},
            {"title": "Quantitative Trading Internship 2026", "location": "Chicago, IL", "department": "Trading"},
        ]
        for job in intern_jobs:
            score, analysis = score_job_suitability(job, firm_tier="Tier B: Main Focus")
            self.assertEqual(score, 0)
            self.assertIn("DISQUALIFIED", analysis["verdict"])
            self.assertIn("intern", analysis["recommendation"].lower())

    def test_url_verifier_unit(self):
        from crawler.url_verifier import check_url_availability, verify_jobs_availability
        is_avail, code, msg = check_url_availability("")
        self.assertFalse(is_avail)
        self.assertEqual(code, 0)

        # Batch test
        sample_jobs = [
            {"title": "Job 1", "url": "", "status": "ACTIVE"},
            {"title": "Job 2", "url": "https://boards-api.greenhouse.io/v1/boards/nonexistenttoken123/jobs/99999", "status": "ACTIVE"}
        ]
        updated, stats = verify_jobs_availability(sample_jobs, max_workers=2)
        self.assertEqual(len(updated), 2)
        self.assertEqual(updated[0]["status"], "INACTIVE")
        self.assertEqual(updated[1]["status"], "INACTIVE")

    def test_senior_experienced_hard_disqualification(self):
        senior_jobs = [
            {"title": "Senior Options Quantitative Researcher", "location": "New York, NY", "department": "Trading"},
            {"title": "Staff Machine Learning Engineer", "location": "San Francisco, CA", "department": "Engineering"},
            {"title": "Experienced Quantitative Trader", "location": "Chicago, IL", "department": "Trading"},
            {"title": "Managing Director - Quantitative Strategies", "location": "New York, NY", "department": "Strats"},
        ]
        for job in senior_jobs:
            score, analysis = score_job_suitability(job, firm_tier="Tier B: Main Focus")
            self.assertEqual(score, 0)
            self.assertIn("DISQUALIFIED", analysis["verdict"])
            self.assertIn("senior", analysis["recommendation"].lower())

    def test_live_openings_contains_no_senior_or_experienced_roles(self):
        import re
        agent = CrawlAgent()
        if os.path.exists(agent.output_json):
            with open(agent.output_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            openings = data.get("openings", [])
            pattern = r'\b(?:senior|sr\.?|staff|principal|lead|head\s+of|director|managing\s+director|executive|vp|vice\s+president)\b|\bexperienced\b'
            for j in openings:
                title = j.get("title", "")
                if "junior/senior" in title.lower():
                    continue
                self.assertFalse(
                    re.search(pattern, title, re.IGNORECASE),
                    f"Found senior/experienced posting in live dataset: {title}"
                )

    def test_operational_and_back_office_disqualification(self):
        operational_jobs = [
            {"title": "Finance Associate", "location": "New York, NY", "department": "Finance"},
            {"title": "Fraud Operations Associate", "location": "New York, NY", "department": "Risk"},
            {"title": "Payment Partner Operations, Associate", "location": "San Francisco, CA", "department": "Ops"},
            {"title": "Associate General Counsel, Privacy", "location": "San Francisco, CA", "department": "Legal"},
            {"title": "Compliance Associate", "location": "New York, NY", "department": "Compliance"},
            {"title": "Digital Communications Associate", "location": "New York, NY", "department": "Comms"},
        ]
        for job in operational_jobs:
            score, analysis = score_job_suitability(job, firm_tier="Tier B: Main Focus")
            self.assertEqual(score, 0, f"Expected 0 score for operational role: {job['title']}")
            self.assertIn("DISQUALIFIED", analysis["verdict"])
            self.assertIn("Non-Quant Operational", analysis["verdict"])

    def test_location_invariance(self):
        job_base = {
            "title": "Junior Quantitative Researcher",
            "department": "Quantitative Alpha Research",
            "description": "Cross-sectional alpha modeling, statistical arbitrage, and stochastic simulation."
        }
        job_nyc = dict(job_base, location="New York, NY")
        job_dallas = dict(job_base, location="Dallas, TX")
        job_unknown = dict(job_base, location="Unknown / Remote")

        score_nyc, _ = score_job_suitability(job_nyc, firm_tier="Tier B: Main Focus")
        score_dallas, _ = score_job_suitability(job_dallas, firm_tier="Tier B: Main Focus")
        score_unknown, _ = score_job_suitability(job_unknown, firm_tier="Tier B: Main Focus")

        self.assertEqual(score_nyc, score_dallas, "NYC should not receive bonus points over Dallas")
        self.assertEqual(score_nyc, score_unknown, "Location must be purely descriptive with 0 score boost")

    def test_posted_pay_range_extraction(self):
        from crawler.salary_extractor import extract_posted_pay_range
        test_samples = [
            ({"description": "The base salary range for this role is $175,000 - $250,000 plus bonus."}, "$175,000 - $250,000 / yr"),
            ({"description": "Base Salary: $150k - $220k. Eligible for equity."}, "$150k - $220k / yr"),
            ({"description": "Pay range: $65.00 - $95.00 / hour depending on experience."}, "$65.00 - $95.00 / hour"),
            ({"raw_compensation": {"compensationTierSummary": "$160,000 - $210,000 / year"}}, "$160,000 - $210,000 / year"),
            ({"description": "No salary disclosure mentioned."}, None)
        ]
        for job_dict, expected in test_samples:
            extracted = extract_posted_pay_range(job_dict)
            self.assertEqual(extracted, expected)

    def test_target_firms_have_official_careers_urls(self):
        import csv
        firms_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "target_firms.csv")
        self.assertTrue(os.path.exists(firms_csv))
        with open(firms_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self.assertIn("official_careers_url", reader.fieldnames)
            rows = list(reader)
            self.assertGreaterEqual(len(rows), 260)
            for r in rows:
                fn = r.get("firm_name", "")
                url = r.get("official_careers_url", "")
                self.assertTrue(bool(url), f"Firm '{fn}' has missing official_careers_url")
                self.assertTrue(url.startswith("http"), f"Firm '{fn}' has invalid url: {url}")

if __name__ == "__main__":
    unittest.main()



