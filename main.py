import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import argparse
import logging
from agent.crawl_agent import CrawlAgent
from agent.scheduler import CrawlScheduler
from agent.firm_scout_subagent import FirmScoutSubagent
from agent.firm_registry import FirmRegistry
from server import run_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(
        description="Quant Career Intelligence v2: Autonomous Tailored Crawl Subagents & Live Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py crawl                        Run crawl across all target quant ATS boards & tailored subagents
  python main.py crawl --firm "Jane Street"   Run tailored crawler subagent for Jane Street only
  python main.py crawl --firm "Citadel"       Run tailored crawler subagent for Citadel only
  python main.py scout --firm "Optiver"       Dispatch scout subagent to detect ATS endpoints for a firm
  python main.py web                          Launch live interactive dashboard on http://localhost:8081
  python main.py daemon --interval 6          Run recurring background crawler daemon (every 6 hours)
  python main.py openings                     Print top active openings in terminal
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: crawl
    crawl_parser = subparsers.add_parser("crawl", help="Run crawl agent to scrape and score target openings")
    crawl_parser.add_argument("--firm", type=str, default=None, help="Target specific firm with tailored subagent")
    crawl_parser.add_argument("--tier", choices=["tier-a", "tier-b", "tier-c1", "tier-c2", "tier-d", "all"], default="all", help="Target priority tier")
    crawl_parser.add_argument("--max-boards", type=int, default=None, help="Cap number of ATS boards to scrape")

    # Command: scout
    scout_parser = subparsers.add_parser("scout", help="Dispatch scout subagent to probe and tailor crawler for an employer")
    scout_parser.add_argument("--firm", type=str, required=True, help="Name of employer to scout")

    # Command: web
    web_parser = subparsers.add_parser("web", help="Launch live web dashboard server")
    web_parser.add_argument("--port", type=int, default=8081, help="Port to run web server on (default 8081)")

    # Command: daemon
    daemon_parser = subparsers.add_parser("daemon", help="Run recurring scheduler daemon")
    daemon_parser.add_argument("--interval", type=float, default=6.0, help="Interval in hours between crawl runs (default: 6)")

    # Command: openings
    openings_parser = subparsers.add_parser("openings", help="Display top live openings in terminal")
    openings_parser.add_argument("--firm", type=str, default=None, help="Filter by firm name")
    openings_parser.add_argument("--min-score", type=int, default=60, help="Minimum suitability score threshold")
    openings_parser.add_argument("--limit", type=int, default=20, help="Max listings to show")

    args = parser.parse_args()

    if args.command == "scout":
        scout = FirmScoutSubagent()
        res = scout.scout_firm(args.firm)
        print("\n" + "=" * 70)
        print(f"  SCOUT SUBAGENT INVESTIGATION: {args.firm}")
        print("=" * 70)
        print(f"  Detected ATS:         {res.get('detected_ats').upper()}")
        print(f"  Board Token:          {res.get('board_token')}")
        print(f"  Recommended Strategy: {res.get('recommended_strategy')}")
        if res.get("openings_sample"):
            print("  Discovered Sample Postings:")
            for s in res.get("openings_sample"):
                print(f"    - {s}")
        print("=" * 70 + "\n")

    elif args.command == "crawl":
        agent = CrawlAgent()
        if args.firm:
            print(f"Dispatching tailored subagent for '{args.firm}'...")
            res = agent.crawl_single_firm(args.firm)
            jobs = res.get("jobs", [])
            print("\n" + "-" * 70)
            print(f"  TAILORED CRAWL RESULT: {args.firm} ({len(jobs)} positions found)")
            print("-" * 70)
            for i, j in enumerate(jobs[:10], 1):
                print(f"{i}. {j.get('title')} ({j.get('suitability_score')}% Fit) - {j.get('location')}")
                print(f"   URL: {j.get('url')}")
            print("-" * 70 + "\n")
        else:
            print(f"Initiating autonomous crawl agent across all tailored subagents and boards...")
            tier_str = None if args.tier == "all" else args.tier.replace("-", " ")
            res = agent.run_crawl(tier_filter=tier_str, max_boards=args.max_boards)
            stats = res.get("stats", {})
            print("\n" + "-" * 60)
            print("  CRAWL COMPLETE")
            print(f"  Total Scored Live Openings: {stats.get('total_live_openings')}")
            print(f"  New Openings This Run:      {stats.get('new_openings_this_crawl')}")
            print(f"  Active Retained:            {stats.get('active_openings')}")
            print(f"  Newly Closed:               {stats.get('closed_openings')}")
            print(f"  Output saved to:            {agent.output_json}")
            print("-" * 60 + "\n")

    elif not args.command or args.command == "openings":
        agent = CrawlAgent()
        import json
        if not os.path.exists(agent.output_json):
            print("No cached live openings found. Running initial crawl...")
            agent.run_crawl()
        
        with open(agent.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        openings = data.get("openings", [])
        min_score = getattr(args, "min_score", 60)
        limit = getattr(args, "limit", 20)
        target_firm = getattr(args, "firm", None)

        filtered = [
            j for j in openings 
            if (j.get("suitability_score") or 0) >= min_score
            and (not target_firm or target_firm.lower() in j.get("firm_name", "").lower())
        ][:limit]

        print("\n" + "=" * 90)
        print(f"  QUANT CAREER INTELLIGENCE v2: TOP TARGET OPENINGS (Score >= {min_score})")
        print(f"  Profile: Quantitative Finance Class of 2027 | QR / QT / Front-Office Strats Focus")
        print("=" * 90)
        for i, j in enumerate(filtered, 1):
            score = j.get("suitability_score", 0)
            status_tag = f"[{j.get('status', 'ACTIVE')}]"
            print(f"\n{i}. {j.get('firm_name')} - {j.get('title')}")
            print(f"   Score: {score}% Fit | Status: {status_tag} | Tier: {j.get('priority_tier')}")
            print(f"   Location: {j.get('location')} | Source: {j.get('source_ats')}")
            print(f"   Comp: {j.get('estimated_comp')} ({j.get('comp_benchmark_delta')})")
            print(f"   URL: {j.get('url')}")
            if j.get("matched_signals"):
                print(f"   Signals: {', '.join(j.get('matched_signals')[:2])}")
        print("\n" + "=" * 90)
        print(f"  Total filtered openings: {len(filtered)} / {len(openings)}")
        print("  Launch interactive UI: python main.py web")
        print("=" * 90 + "\n")

    elif args.command == "web":
        run_server(port=args.port)

    elif args.command == "daemon":
        print(f"Starting recurring crawler daemon every {args.interval} hours...")
        scheduler = CrawlScheduler(interval_hours=args.interval)
        scheduler.run_blocking()

if __name__ == "__main__":
    main()
