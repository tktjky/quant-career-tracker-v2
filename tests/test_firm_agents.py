import unittest
import os
from crawler.relevance_filter import score_job_suitability, CANDIDATE_PROFILE
from crawler.change_detector import ChangeDetector
from agent.firm_registry import FirmRegistry
from crawler.firm_agents.jane_street import JaneStreetAgent
from crawler.firm_agents.citadel import CitadelAgent
from crawler.firm_agents.deshaw import DEShawAgent
from agent.crawl_agent import CrawlAgent

class TestJobTrackerV2FirmAgents(unittest.TestCase):

    def test_firm_registry_dispatch(self):
        registry = FirmRegistry()
        js_agent = registry.get_agent_for_firm("Jane Street")
        self.assertIsNotNone(js_agent)
        self.assertEqual(js_agent.firm_name, "Jane Street")

        cit_agent = registry.get_agent_for_firm("Citadel")
        self.assertIsNotNone(cit_agent)
        self.assertEqual(cit_agent.firm_name, "Citadel")

        p72_agent = registry.get_agent_for_firm("Point72")
        self.assertIsNotNone(p72_agent)

    def test_jane_street_tailored_agent(self):
        agent = JaneStreetAgent()
        jobs = agent.crawl_jobs()
        self.assertGreater(len(jobs), 0)
        self.assertTrue(any("Trader" in j["title"] for j in jobs))

    def test_citadel_tailored_agent(self):
        agent = CitadelAgent()
        jobs = agent.crawl_jobs()
        self.assertGreater(len(jobs), 0)
        self.assertTrue(any("Quantitative" in j["title"] for j in jobs))

    def test_deshaw_tailored_agent(self):
        agent = DEShawAgent()
        jobs = agent.crawl_jobs()
        self.assertGreater(len(jobs), 0)
        self.assertTrue(any("Quantitative Analyst" in j["title"] for j in jobs))

    def test_crawl_agent_single_firm(self):
        master_agent = CrawlAgent()
        res = master_agent.crawl_single_firm("Jane Street")
        self.assertEqual(res["firm_name"], "Jane Street")
        self.assertGreater(res["jobs_count"], 0)
        top_job = res["jobs"][0]
        self.assertGreaterEqual(top_job["suitability_score"], 80)

if __name__ == "__main__":
    unittest.main()
