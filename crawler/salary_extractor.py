import re
from typing import Optional, Dict, Any

# Regular expression patterns for extracting posted salary disclosures
# Handles US, UK, and European pay transparency standards
SALARY_PATTERNS = [
    # 1. Hourly range (check first to avoid mistaking $65.00 as 5-character annual number): e.g. "$65.00 - $95.00 / hour" or "$50 - $80 / hr"
    re.compile(
        r"([\$£€]\d{2,3}(?:\.\d{2})?\s*(?:[-–—to]+\s*|\s+to\s+)[\$£€]?\d{2,3}(?:\.\d{2})?\s*(?:\/hr|\/hour|per\s+hour))",
        re.IGNORECASE
    ),
    # 2. Stated label preceding the range: e.g. "Base Salary: $150,000 - $200,000" or "Salary Range: $180k - $240k"
    re.compile(
        r"(?:base\s+salary(?:\s+range)?|salary(?:\s+range)?|compensation(?:\s+range)?|pay\s+range)[\s\:\–\-]*"
        r"([\$£€][\d,]+(?:\.\d+)?\s*(?:k|K)?\s*(?:[-–—to]+|\s+to\s+)\s*[\$£€]?[\d,]+(?:\.\d+)?\s*(?:k|K)?"
        r"(?:\s*(?:per\s+year|annually|\/\s*yr|\/\s*year|base|USD|EUR|GBP|\/\s*hr|\/\s*hour|per\s+hour))?)",
        re.IGNORECASE
    ),
    # 3. Explicit annual dollar range (e.g. "$175,000 - $250,000" or "$150,000 to $225,000 / year")
    re.compile(
        r"([\$£€]\d{2,3},\d{3}(?:\.\d{2})?\s*(?:[-–—to]+\s*|\s+to\s+)[\$£€]?\d{2,3},\d{3}(?:\.\d{2})?"
        r"(?:\s*(?:USD|EUR|GBP|base|per\s+year|\/yr|\/year|annually))?)",
        re.IGNORECASE
    ),
    # 4. Explicit 'k' shorthand range: e.g. "$150k - $220k" or "$175K - $250K / yr"
    re.compile(
        r"([\$£€]\d{2,3}k\s*(?:[-–—to]+\s*|\s+to\s+)[\$£€]?\d{2,3}k"
        r"(?:\s*(?:USD|EUR|GBP|base|per\s+year|\/yr|\/year|annually))?)",
        re.IGNORECASE
    )
]

def clean_salary_text(raw_text: str) -> str:
    """Cleans and standardizes raw salary strings."""
    text = raw_text.strip().rstrip(",;.:")
    # Normalize multiple whitespace characters
    text = re.sub(r"\s+", " ", text)
    # Ensure a space around hyphens/dashes for consistency
    text = re.sub(r"([\$£€\d])\s*[-–—]\s*([\$£€\d])", r"\1 - \2", text)
    return text

def extract_posted_pay_range(job_dict: Dict[str, Any]) -> Optional[str]:
    """
    Extracts the official posted compensation/salary range from a job posting dictionary.
    Checks:
    1. Direct structured metadata fields (Ashby raw_compensation, Greenhouse metadata, Lever additional).
    2. HTML / plain text body description.
    
    Returns:
        Formatted salary range string (e.g. '$175,000 - $250,000 / yr') or None.
    """
    # 1. Check structured Ashby compensation if present
    raw_comp = job_dict.get("raw_compensation")
    if isinstance(raw_comp, dict):
        summary = raw_comp.get("compensationTierSummary") or raw_comp.get("summary")
        if summary and isinstance(summary, str) and "$" in summary:
            return clean_salary_text(summary)
        # Check min/max numbers
        min_val = raw_comp.get("min")
        max_val = raw_comp.get("max")
        curr = raw_comp.get("currency", "USD")
        if min_val and max_val:
            prefix = "$" if curr == "USD" else (curr + " ")
            return f"{prefix}{int(min_val):,} - {prefix}{int(max_val):,} / yr"

    # 2. Check description text (HTML or plain)
    desc = job_dict.get("description", "") or ""
    if not desc or len(desc) < 10:
        return None

    # Search against pre-compiled regex patterns
    for pattern in SALARY_PATTERNS:
        match = pattern.search(desc)
        if match:
            extracted = clean_salary_text(match.group(1))
            # Basic sanity check: make sure it contains digits
            if any(char.isdigit() for char in extracted):
                # If hourly is detected
                if re.search(r"(?:\/hr|\/hour|per\s+hour|hourly)", extracted, re.I):
                    if not re.search(r"(?:\/hr|\/hour|per\s+hour)", extracted, re.I):
                        extracted += " / hr"
                    return extracted
                # If annual unit is already present
                if re.search(r"(?:\/yr|\/year|annually|per\s+year)", extracted, re.I):
                    return extracted
                # If numbers indicate annual compensation (> $1,000 or has k suffix e.g. 150k)
                if re.search(r"\d{2,3},\d{3}|\d+k", extracted, re.I):
                    extracted += " / yr"
                return extracted

    return None
