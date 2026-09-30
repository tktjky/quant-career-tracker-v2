import re
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("URLVerifier")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DEAD_BODY_PATTERNS = [
    "this job is no longer available",
    "the page you're looking for cannot be found",
    "job posting has expired",
    "position has been filled",
    "this position is closed",
    "this posting has been closed",
    "no longer accepting applications",
    "job not found",
    "this listing is expired",
]

def check_url_availability(url: str, timeout: float = 4.0) -> Tuple[bool, int, str]:
    """
    Checks if a job posting URL is still active and valid.
    Handles Greenhouse API direct verification, redirect inspection, and HTTP status codes.
    Returns (is_available: bool, status_code: int, reason: str).
    """
    if not url or not url.startswith("http"):
        return False, 0, "Invalid or missing URL"

    # 1. Specialized Greenhouse Check if URL matches greenhouse board
    gh_match = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", url)
    if gh_match:
        board_token, job_id = gh_match.group(1), gh_match.group(2)
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"
        try:
            gh_resp = requests.get(api_url, headers=DEFAULT_HEADERS, timeout=timeout)
            if gh_resp.status_code == 200:
                return True, 200, "Active (Greenhouse API Verified)"
            elif gh_resp.status_code in (404, 410):
                return False, gh_resp.status_code, "Job unlisted / removed (Greenhouse API 404)"
        except Exception:
            pass  # Fall back to standard web check

    # 2. General HTTP check
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True, stream=True)
        status_code = resp.status_code

        # Explicit dead status codes
        if status_code in (404, 410):
            return False, status_code, f"HTTP {status_code} - Page Not Found or Gone"

        # Check for redirect away from specific job to homepage / main career listing
        orig_job_match = re.search(r"/jobs?/([^/?#]+)", url)
        if orig_job_match:
            job_slug = orig_job_match.group(1)
            # If redirected to a generic root or careers page where original slug is gone
            if resp.history and (job_slug not in resp.url and not re.search(r"/jobs?/", resp.url)):
                return False, status_code, f"Redirected to homepage/portal ({resp.url})"

        if status_code >= 400:
            # Cloudflare bot challenge (403) on some employer domains - do not falsely mark inactive if URL structure is valid
            if status_code == 403:
                return True, 403, "Protected by Cloudflare / Access check"
            return False, status_code, f"HTTP {status_code} Error"

        if 200 <= status_code < 400:
            # Quick check of body content for explicit closed markers
            try:
                content_chunk = resp.raw.read(3072) if hasattr(resp, "raw") else resp.content[:3072]
                text = content_chunk.decode("utf-8", errors="ignore").lower()
                for pattern in DEAD_BODY_PATTERNS:
                    if pattern in text:
                        return False, status_code, f"Listing closed: '{pattern}'"
            except Exception:
                pass
            return True, status_code, "OK"

        return False, status_code, f"HTTP {status_code}"

    except requests.exceptions.Timeout:
        # Timeouts on slow networks shouldn't immediately kill active listings, mark uncertain but retain
        return True, 408, "Request timed out"
    except requests.exceptions.SSLError as e:
        return False, 495, f"SSL Error: {e}"
    except requests.exceptions.ConnectionError:
        return False, 503, "Connection failed or DNS lookup failed"
    except Exception as e:
        return False, 500, f"Error: {e}"

def verify_jobs_availability(
    jobs: List[Dict[str, Any]], 
    max_workers: int = 20, 
    timeout: float = 4.0
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Concurrently checks availability for a list of job dicts.
    If a job's URL is dead or closed, marks job['status'] = 'INACTIVE'
    and attaches 'inactive_reason' and 'url_status'.
    Returns (updated_jobs, stats).
    """
    total = len(jobs)
    if total == 0:
        return jobs, {"total_checked": 0, "active": 0, "inactive": 0}

    logger.info(f"Verifying live URL availability for {total} job postings with {max_workers} threads...")

    active_count = 0
    inactive_count = 0

    url_results: Dict[str, Tuple[bool, int, str]] = {}
    unique_urls = list({j.get("url") for j in jobs if j.get("url")})

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(check_url_availability, u, timeout): u 
            for u in unique_urls
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                is_avail, code, reason = future.result()
                url_results[url] = (is_avail, code, reason)
            except Exception as e:
                url_results[url] = (False, 500, str(e))

    for job in jobs:
        url = job.get("url")
        if not url:
            job["status"] = "INACTIVE"
            job["inactive_reason"] = "No URL provided"
            job["url_status"] = 0
            inactive_count += 1
            continue

        is_avail, code, reason = url_results.get(url, (False, 0, "Unchecked"))
        job["url_status"] = code

        if not is_avail:
            job["status"] = "INACTIVE"
            job["inactive_reason"] = reason
            inactive_count += 1
        else:
            if job.get("status") == "INACTIVE":
                job["status"] = "ACTIVE"
                job.pop("inactive_reason", None)
            active_count += 1

    logger.info(f"URL Verification complete: {active_count} active, {inactive_count} inactive out of {total}.")
    return jobs, {
        "total_checked": total,
        "active": active_count,
        "inactive": inactive_count
    }
