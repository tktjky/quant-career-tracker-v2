# Quant Career Intelligence v2: Autonomous Web Crawling Agent & Live Job Tracker

## Overview
**Version 2 (`AI_workspace/job_tracker_v2/`)** introduces an autonomous crawling expert agent that actively discovers, filters, scores, and tracks live job openings tailored specifically for **Kangqi (Kevin) Yu**:
- **Candidate Profile**: Columbia Business School Master of Science in Financial Economics (CBS MSFE Class of 2027)
- **Anchor Offer in Hand**: Capital One Senior Associate — Data Science ($183,500 Year 1 Total Comp with full visa sponsorship)
- **Target Roles**: Quantitative Research (QR), Quantitative Trading (QT), Front-Office Strats, Financial ML Engineer
- **Isolation Guarantee**: The original `AI_workspace/job_tracker/` (v1) remains completely untouched and functional.

---

## Key Features in v2

1. **Modular Tailored Firm Subagents (`crawler/firm_agents/`)**:
   - Each target employer or group has a dedicated subagent crawler tailored to that firm's distinct API structure, URL patterns, and candidate level.
   - Dedicated crawlers implemented for **Jane Street**, **Citadel & Citadel Securities**, **Two Sigma**, **D.E. Shaw**, **Millennium Management**, **Point72 & Cubist Systematic Strategies**, and **Goldman Sachs (Global Markets Strats)**.
   - Generic ATS subagent worker for Greenhouse, Lever, and Ashby boards.

2. **Automated Firm Scout Subagent (`agent/firm_scout_subagent.py`)**:
   - Dispatches a subagent to scout unfamiliar or new employer domains, detect their underlying ATS provider (Greenhouse, Lever, Workday, etc.), extract sample postings, and recommend crawl configurations.

3. **High-Speed Direct ATS Scraper (`crawler/ats_scraper.py`)**:
   - Direct HTTP scraping of board APIs without browser overhead.

4. **CBS MSFE Suitability Engine (`crawler/relevance_filter.py`)**:
   - Calculates a 0–100% suitability match score based on title regex, 2026/2027 cohort signals, campus/graduate tags, NYC/Chicago/Greenwich location preferences, and negative filters (penalizes executive MD/Director roles, 7+ years requirement, and non-quant corporate roles).

5. **Stateful Change Detector (`crawler/change_detector.py`)**:
   - Compares successive crawl runs against `data/history_state.json`.
   - Tags every opening as `NEW` (discovered in current run), `ACTIVE` (retained from previous runs), or `CLOSED` (no longer active).

6. **Live Web Dashboard & REST API (`web/` & `server.py`)**:
   - Runs locally on **`http://localhost:8081`**.
   - Features real-time search, multi-tier filtering, suitability score thresholds, 1-click apply links, and in-browser **"Crawl Firm"** / **"Run All Crawlers"** buttons.

7. **Periodic Scheduler Daemon (`agent/scheduler.py`)**:
   - Enables background automatic crawls on a set interval (e.g. every 6 or 24 hours).

---

## Quickstart Guide

### 1. Launch Interactive Web Dashboard
Run the following from your terminal:
```bash
source /Users/kevinyu/miniconda3/bin/activate py310
cd AI_workspace/job_tracker_v2
python main.py web
```
Then open your browser to **http://localhost:8081**.

### 2. Run a Live Crawl on Demand
To scan all target ATS boards and update the live openings database:
```bash
python main.py crawl
```
You can also filter by priority tier or limit board count:
```bash
python main.py crawl --tier tier-b
python main.py crawl --tier tier-a --max-boards 10
```

### 3. Run a Tailored Crawl for a Specific Firm
To run a specialized subagent for an individual target employer:
```bash
python main.py crawl --firm "Jane Street"
python main.py crawl --firm "Citadel"
python main.py crawl --firm "Two Sigma"
```

### 4. Dispatch Scout Subagent to Investigate an Employer
To investigate an employer's career portal and probe their underlying ATS:
```bash
python main.py scout --firm "Optiver"
```

### 5. View Top Openings in Terminal
To inspect top target matches directly from your terminal:
```bash
python main.py openings --min-score 70 --limit 15
python main.py openings --firm "Jane Street"
```

### 6. Run Background Recurring Daemon
To keep listings updated continuously (e.g. every 6 hours):
```bash
python main.py daemon --interval 6
```

### 7. Run Unit Test Suite
To verify the firm subagents, scoring heuristics, and change detector:
```bash
PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py"
```

---

## Directory Layout
```
AI_workspace/job_tracker_v2/
├── agent/
│   ├── crawl_agent.py          # Master crawl orchestrator
│   └── scheduler.py            # Recurring crawl daemon
├── crawler/
│   ├── ats_scraper.py          # Greenhouse/Lever/Ashby API scrapers
│   ├── web_search_scraper.py   # Custom institutional portals & feeds
│   ├── relevance_filter.py     # Heuristic CBS MSFE scoring engine
│   └── change_detector.py      # Stateful diff tracking (NEW/ACTIVE/CLOSED)
├── data/
│   ├── target_firms.csv        # 293 employers across 6 priority tiers
│   ├── live_openings.json      # Current scored live openings feed
│   ├── history_state.json      # Historic snapshot tracking state transitions
│   └── last_crawl_summary.json # Summary and performance metrics
├── tests/
│   └── test_v2.py              # Unit tests (6/6 passing)
├── web/
│   ├── index.html              # Responsive dark-theme dashboard
│   ├── app.js                  # Frontend client logic & filters
│   └── data.js                 # Fallback static data object
├── server.py                   # Local web server on port 8081
├── main.py                     # Unified CLI entrypoint
└── README.md                   # System documentation
```
