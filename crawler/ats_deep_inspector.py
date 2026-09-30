import os
import re
import json
import csv
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

logger = logging.getLogger("ATSDeepInspector")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# Known manual overrides for premier quant / finance firms where standard scraping is tricky
KNOWN_FIRM_PROFILES = {
    # Tailored Crawlers
    "Jane Street": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},
    "Citadel": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},
    "Citadel Securities": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},
    "Two Sigma": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},
    "D.E. Shaw": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},
    "Millennium Management": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},
    "Point72": {"status": "AUTOMATED_FEED", "method": "Greenhouse API", "ats": "greenhouse", "token": "point72", "reason": None},
    "Cubist Systematic Strategies": {"status": "AUTOMATED_FEED", "method": "Greenhouse API", "ats": "greenhouse", "token": "point72", "reason": None},
    "Goldman Sachs": {"status": "AUTOMATED_FEED", "method": "Tailored Subagent", "ats": "custom", "reason": None},

    # Enterprise Workday & Cloudflare Protected Portals
    "BlackRock": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "workday", "reason": "Enterprise Workday (Session Auth Required)"},
    "Morgan Stanley": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "workday", "reason": "Enterprise Taleo/Workday Portal"},
    "J.P. Morgan Chase": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "oraclecloud", "reason": "Enterprise Oracle Cloud HCM Portal"},
    "Bank of America": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "workday", "reason": "Enterprise Workday Portal"},
    "PIMCO": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "workday", "reason": "Enterprise Workday Portal"},
    "Fidelity Investments": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "workday", "reason": "Enterprise Workday Portal"},
    "Hudson River Trading (HRT)": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Cloudflare Bot Management (Turnstile 403)"},
    "DRW": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Cloudflare Bot Protected Careers SPA"},
    "IMC Trading": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Enterprise Portal / Cloudflare Protected"},
    "Virtu Financial": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Cloudflare Protected Careers Portal"},
    "Balyasny Asset Management": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Private Internal ATS Feed"},
    "Verition Fund Management": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Direct Career Portal Monitored"},
    "Bridgewater Associates": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Cloudflare Protected Careers Portal"},
    "Qube Research & Technologies (QRT)": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Custom Enterprise Portal"},
    "Palantir Technologies": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Custom Careers React SPA"},
    "Bloomberg": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "custom", "reason": "Enterprise Portal (Session Protected)"},
    "CME Group": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "workday", "reason": "Enterprise Workday Portal"},
    "TGS Management": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "none", "reason": "Invite & Referral Only (No Public Board)"},
    "Radix Trading": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "none", "reason": "Direct Contact / Referral Portal"},
    "Headlands Technologies": {"status": "UNCRAWLABLE_PORTAL_ONLY", "method": "Direct Portal Monitored", "ats": "none", "reason": "Direct Email Application (careers@headlandstech.com)"},
}

class ATSDeepInspector:
    def __init__(self, timeout: int = 8):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.timeout = timeout

    def probe_ats_api(self, ats: str, token: str) -> Optional[int]:
        """Probes standard ATS JSON APIs to check if valid and count jobs."""
        try:
            if ats == "greenhouse":
                url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
                r = self.session.get(url, timeout=4)
                if r.status_code == 200:
                    d = r.json()
                    return len(d.get("jobs", []))
            elif ats == "lever":
                url = f"https://api.lever.co/v0/postings/{token}?mode=json"
                r = self.session.get(url, timeout=4)
                if r.status_code == 200:
                    d = r.json()
                    return len(d) if isinstance(d, list) else 0
            elif ats == "ashby":
                url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
                r = self.session.get(url, timeout=4)
                if r.status_code == 200:
                    d = r.json()
                    return len(d.get("jobs", []))
            elif ats == "smartrecruiters":
                url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
                r = self.session.get(url, timeout=4)
                if r.status_code == 200:
                    d = r.json()
                    return len(d.get("content", []))
            elif ats == "workable":
                url = f"https://apply.workable.com/api/v3/accounts/{token}/jobs"
                r = self.session.get(url, timeout=4)
                if r.status_code == 200:
                    d = r.json()
                    return len(d.get("results", []))
        except Exception:
            pass
        return None

    def inspect_firm(self, firm: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep-inspects a single firm to determine its ATS provider, crawlability status,
        and specific technical barrier if uncrawlable.
        """
        firm_name = firm.get("firm_name", "").strip()
        url = firm.get("official_careers_url", "").strip()
        tier = firm.get("priority_tier", "Tier B: Main Focus")
        sector = firm.get("industry_sector", "Quantitative Hedge Funds")

        # 1. Check known profiles first
        if firm_name in KNOWN_FIRM_PROFILES:
            prof = dict(KNOWN_FIRM_PROFILES[firm_name])
            prof.update({
                "firm_name": firm_name,
                "official_careers_url": url,
                "priority_tier": tier,
                "industry_sector": sector,
            })
            return prof

        if not url or not url.startswith("http"):
            return {
                "firm_name": firm_name,
                "official_careers_url": url,
                "priority_tier": tier,
                "industry_sector": sector,
                "status": "UNCRAWLABLE_PORTAL_ONLY",
                "method": "Direct Portal Monitored",
                "ats": "none",
                "reason": "Missing or Invalid Career URL"
            }

        # 2. Try fetching the careers page
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            final_url = resp.url.lower()
            status_code = resp.status_code
            html = resp.text

            # Check for Cloudflare / Akamai Bot Protection
            if status_code in (403, 503) or "cloudflare" in html.lower() and ("just a moment" in html.lower() or "challenge-platform" in html.lower()):
                return {
                    "firm_name": firm_name,
                    "official_careers_url": url,
                    "priority_tier": tier,
                    "industry_sector": sector,
                    "status": "UNCRAWLABLE_PORTAL_ONLY",
                    "method": "Direct Portal Monitored",
                    "ats": "custom",
                    "reason": "Cloudflare / Bot Protection (HTTP 403 Challenge)"
                }

            # Check Workday
            if "myworkdayjobs.com" in final_url or "myworkdayjobs.com" in html:
                return {
                    "firm_name": firm_name,
                    "official_careers_url": url,
                    "priority_tier": tier,
                    "industry_sector": sector,
                    "status": "UNCRAWLABLE_PORTAL_ONLY",
                    "method": "Direct Portal Monitored",
                    "ats": "workday",
                    "reason": "Enterprise Workday (Dynamic Session Required)"
                }

            # Check Taleo / Oracle Cloud
            if "taleo.net" in final_url or "oraclecloud.com" in final_url or "taleo" in html.lower():
                return {
                    "firm_name": firm_name,
                    "official_careers_url": url,
                    "priority_tier": tier,
                    "industry_sector": sector,
                    "status": "UNCRAWLABLE_PORTAL_ONLY",
                    "method": "Direct Portal Monitored",
                    "ats": "taleo",
                    "reason": "Enterprise Taleo / Oracle HCM Portal"
                }

            # Check iCIMS
            if "icims.com" in final_url or "icims.com" in html:
                return {
                    "firm_name": firm_name,
                    "official_careers_url": url,
                    "priority_tier": tier,
                    "industry_sector": sector,
                    "status": "UNCRAWLABLE_PORTAL_ONLY",
                    "method": "Direct Portal Monitored",
                    "ats": "icims",
                    "reason": "Enterprise iCIMS Portal (Dynamic iFrame)"
                }

            # Scan HTML for embedded Greenhouse board token
            gh_match = re.search(r"boards\.greenhouse\.io/(?:embed/job_board\?for=|v1/boards/)?([a-zA-Z0-9_\-]+)", html, re.I)
            if gh_match:
                token = gh_match.group(1).lower()
                job_count = self.probe_ats_api("greenhouse", token)
                if job_count is not None:
                    return {
                        "firm_name": firm_name,
                        "official_careers_url": url,
                        "priority_tier": tier,
                        "industry_sector": sector,
                        "status": "AUTOMATED_FEED",
                        "method": "Greenhouse API",
                        "ats": "greenhouse",
                        "token": token,
                        "job_count": job_count,
                        "reason": None
                    }

            # Scan HTML for embedded Lever board token
            lever_match = re.search(r"jobs\.lever\.co/([a-zA-Z0-9_\-]+)", html, re.I)
            if lever_match:
                token = lever_match.group(1).lower()
                job_count = self.probe_ats_api("lever", token)
                if job_count is not None:
                    return {
                        "firm_name": firm_name,
                        "official_careers_url": url,
                        "priority_tier": tier,
                        "industry_sector": sector,
                        "status": "AUTOMATED_FEED",
                        "method": "Lever API",
                        "ats": "lever",
                        "token": token,
                        "job_count": job_count,
                        "reason": None
                    }

            # Scan HTML for embedded Ashby board token
            ashby_match = re.search(r"jobs\.ashbyhq\.com/([a-zA-Z0-9_\-]+)", html, re.I)
            if ashby_match:
                token = ashby_match.group(1).lower()
                job_count = self.probe_ats_api("ashby", token)
                if job_count is not None:
                    return {
                        "firm_name": firm_name,
                        "official_careers_url": url,
                        "priority_tier": tier,
                        "industry_sector": sector,
                        "status": "AUTOMATED_FEED",
                        "method": "Ashby API",
                        "ats": "ashby",
                        "token": token,
                        "job_count": job_count,
                        "reason": None
                    }

            # Scan SmartRecruiters
            smart_match = re.search(r"smartrecruiters\.com/(?:[a-zA-Z0-9_\-]+/)?([a-zA-Z0-9_\-]+)", html, re.I)
            if smart_match:
                token = smart_match.group(1).lower()
                job_count = self.probe_ats_api("smartrecruiters", token)
                if job_count is not None and job_count > 0:
                    return {
                        "firm_name": firm_name,
                        "official_careers_url": url,
                        "priority_tier": tier,
                        "industry_sector": sector,
                        "status": "AUTOMATED_FEED",
                        "method": "SmartRecruiters API",
                        "ats": "smartrecruiters",
                        "token": token,
                        "job_count": job_count,
                        "reason": None
                    }

            # Check email-only apply pattern
            if re.search(r"\b(?:send\s+(?:your\s+)?(?:cv|resume)\s+to|email\s+(?:us\s+at\s+)?careers@)\b", html, re.I):
                return {
                    "firm_name": firm_name,
                    "official_careers_url": url,
                    "priority_tier": tier,
                    "industry_sector": sector,
                    "status": "UNCRAWLABLE_PORTAL_ONLY",
                    "method": "Direct Portal Monitored",
                    "ats": "email_direct",
                    "reason": "Direct Email Application (No Online ATS Board)"
                }

            # If page succeeded with HTTP 200 but no automated public ATS API was identified
            return {
                "firm_name": firm_name,
                "official_careers_url": url,
                "priority_tier": tier,
                "industry_sector": sector,
                "status": "UNCRAWLABLE_PORTAL_ONLY",
                "method": "Direct Portal Monitored",
                "ats": "custom",
                "reason": "Custom Portal / Off-Cycle (No Public ATS API Discovered)"
            }

        except requests.exceptions.Timeout:
            return {
                "firm_name": firm_name,
                "official_careers_url": url,
                "priority_tier": tier,
                "industry_sector": sector,
                "status": "UNCRAWLABLE_PORTAL_ONLY",
                "method": "Direct Portal Monitored",
                "ats": "custom",
                "reason": "Connection Timeout (Enterprise Firewall / VPN Protected)"
            }
        except Exception as e:
            return {
                "firm_name": firm_name,
                "official_careers_url": url,
                "priority_tier": tier,
                "industry_sector": sector,
                "status": "UNCRAWLABLE_PORTAL_ONLY",
                "method": "Direct Portal Monitored",
                "ats": "custom",
                "reason": f"Access Restricted ({type(e).__name__})"
            }

    def inspect_all_firms(self, firms: List[Dict[str, Any]], max_workers: int = 20) -> List[Dict[str, Any]]:
        """Executes deep inspection across all firms concurrently."""
        results = []
        logger.info(f"Starting deep inspection across {len(firms)} target firms with {max_workers} threads...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            fut_map = {executor.submit(self.inspect_firm, f): f["firm_name"] for f in firms}
            for fut in as_completed(fut_map):
                fn = fut_map[fut]
                try:
                    res = fut.result()
                    results.append(res)
                except Exception as e:
                    logger.error(f"Error inspecting {fn}: {e}")
                    results.append({
                        "firm_name": fn,
                        "status": "UNCRAWLABLE_PORTAL_ONLY",
                        "method": "Direct Portal Monitored",
                        "reason": f"Inspection Error: {e}"
                    })
        return sorted(results, key=lambda x: x["firm_name"])
