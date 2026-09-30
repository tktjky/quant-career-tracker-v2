import re
from typing import Dict, Any, Tuple

CANDIDATE_PROFILE = {
    "role_level": "Master of Science in Financial Economics (Class of 2027)",
    "target_degree": "MSFE / Quantitative Finance",
    "graduation_year": 2027,
    "target_roles": [
        "Quantitative Researcher",
        "Quantitative Research",
        "Quantitative Trader",
        "Quantitative Trading",
        "QR",
        "QT",
        "Quantitative Strategist",
        "Front Office Strats",
        "Financial Machine Learning",
        "Quantitative Developer",
        "Data Scientist"
    ],
    "target_locations": [
        "New York", "NYC", "NY",
        "Jersey City", "Greenwich", "Stamford", "Connecticut",
        "Chicago", "IL",
        "San Francisco", "SF", "Bay Area", "Palo Alto",
        "Remote", "United States", "US"
    ]
}

# Positive keywords for quant finance roles
KEYWORD_WEIGHTS = {
    # Core target titles (highest priority)
    r"\bquant(?:itative)?\s+research(?:er|)?\b": 35,
    r"\bquant(?:itative)?\s+trad(?:er|ing)\b": 35,
    r"\bquant(?:itative)?\s+strat(?:egist|s)?\b": 30,
    r"\balgo(?:rithmic)?\s+trad(?:er|ing)\b": 30,
    r"\balpha\s+research(?:er|)?\b": 30,
    r"\bfront\s+office\s+strat(?:s|egist)?\b": 30,
    r"\bmachine\s+learning\s+(?:quant|researcher|scientist|engineer)\b": 25,
    r"\bportfolio\s+manager\s+associate\b": 25,
    r"\bquant(?:itative)?\s+analyst\b": 22,
    r"\bquant(?:itative)?\s+developer\b": 20,
    r"\bdata\s+scientist\b": 15,
    r"\bmachine\s+learning\b": 12,
    r"\bderivatives?\b": 10,
    r"\bvolatility\b": 10,
    r"\bstochastic\b": 10,
    r"\btime\s+series\b": 8,

    # Cohort / New Grad / Campus markers (Targeting Class of 2027)
    r"\b2027\b": 25,
    r"\b2026\b": 15,
    r"\b(campus|graduate|new\s+grad(?:uate)?|early\s+career|entry\s+level|university)\b": 20,
    r"\bmaster(?:'s)?\b": 15,
    r"\bphd\s+or\s+master\b": 15,
    r"\bassociate\b": 12,

    # NYC / Preferred Quant Hubs
    r"\b(?:new\s+york|nyc|ny)\b": 15,
    r"\b(?:chicago|greenwich|stamford)\b": 12,
    r"\b(?:jersey\s+city|hoboken)\b": 10,
}

# Negative disqualifiers (experience mismatches or non-quant operational roles)
DISQUALIFIER_PATTERNS = [
    (r"\b(?:managing\s+director|md|director|vice\s+president|vp|principal)\b", -40, "Senior executive level (MD/Director/VP)"),
    (r"\b(?:lead|head\s+of|chief|manager\s+of)\b", -30, "Leadership/Management requirement"),
    (r"\b(?:7\+|8\+|10\+|12\+|15\+)\s*(?:years|yrs)\b", -45, "Excessive experience requirement (7+ years)"),
    (r"\b(?:5\+|6\+)\s*(?:years|yrs)\s+(?:of\s+)?experience\b", -25, "5+ years experience required"),
    (r"\b(?:undergraduate\s+only|freshman|sophomore|junior\s+only)\b", -40, "Undergraduate-only program"),
    (r"\b(?:human\s+resources|recruiter|hr|talent\s+acquisition)\b", -80, "Non-quant: Human Resources"),
    (r"\b(?:paralegal|legal\s+counsel|compliance\s+officer)\b", -80, "Non-quant: Legal & Compliance"),
    (r"\b(?:accountant|payroll|tax\s+specialist|auditor)\b", -80, "Non-quant: Accounting & Tax"),
    (r"\b(?:executive\s+assistant|office\s+manager|receptionist)\b", -80, "Non-quant: Administrative"),
    (r"\bphd\s+only\b", -35, "PhD degree mandatory"),
]

def score_job_suitability(job_dict: Dict[str, Any], firm_tier: str = "Tier B") -> Tuple[int, Dict[str, Any]]:
    """
    Evaluates a candidate job opening against target MSFE quantitative profile.
    Returns:
        score: int (0 to 100)
        reasons: dict with matched signals, penalties, and fit tier verdict
    """
    title = job_dict.get("title", "").strip()
    location = job_dict.get("location", "").strip()
    department = job_dict.get("department", "").strip()
    description = job_dict.get("description", "") or ""
    
    full_text = f"{title} | {department} | {location} | {description[:1000]}".lower()
    title_lower = title.lower()

    score = 0
    matched_positives = []
    penalties = []

    # 1. Base tier boost from firm classification
    tier_boost = {
        "Tier A": 15,
        "Tier B": 12,
        "Tier C1": 8,
        "Tier D": 6,
        "Tier C2": 2,
        "Tier E": -20
    }
    for t_key, boost in tier_boost.items():
        if t_key in firm_tier:
            score += boost
            if boost > 0:
                matched_positives.append(f"Firm Quality Boost ({t_key}): +{boost}")
            break

    # 2. Check title specifically for quant roles
    has_quant_title = False
    for pattern, weight in KEYWORD_WEIGHTS.items():
        if re.search(pattern, title_lower):
            score += weight
            matched_positives.append(f"Title match '{pattern}': +{weight}")
            has_quant_title = True

    # 3. Check full text for campus/cohort signals
    for pattern, weight in KEYWORD_WEIGHTS.items():
        if pattern not in title_lower and re.search(pattern, full_text):
            # Half weight if only in description/department
            adj_weight = max(2, weight // 2)
            score += adj_weight
            matched_positives.append(f"Keyword match '{pattern}': +{adj_weight}")

    # 4. Location scoring
    loc_lower = location.lower()
    if any(loc in loc_lower for loc in ["new york", "nyc", "ny", "manhattan"]):
        score += 15
        matched_positives.append("Preferred Location (NYC Hub): +15")
    elif any(loc in loc_lower for loc in ["chicago", "greenwich", "stamford", "jersey city"]):
        score += 10
        matched_positives.append("Major Quant Hub Location: +10")
    elif any(loc in loc_lower for loc in ["remote", "san francisco", "sf", "bay area"]):
        score += 5
        matched_positives.append("Acceptable Location: +5")

    # 5. Apply Disqualifiers / Penalties
    for pattern, penalty, reason in DISQUALIFIER_PATTERNS:
        if re.search(pattern, full_text):
            score += penalty
            penalties.append(f"{reason} ({penalty})")

    # 6. Clamp score between 0 and 100
    final_score = max(0, min(100, score))

    # Suitability Verdict
    if final_score >= 80:
        verdict = "HIGH PRIORITY (Direct Target)"
        apply_recommendation = "Immediate Apply (Tailor CBS MSFE resume)"
    elif final_score >= 60:
        verdict = "STRONG FIT (Competitive)"
        apply_recommendation = "Apply (Standard quant package)"
    elif final_score >= 40:
        verdict = "POSSIBLE FIT (Calibration)"
        apply_recommendation = "Secondary / Calibration apply"
    else:
        verdict = "LOW RELEVANCE / SKIP"
        apply_recommendation = "Skip or review manually"

    return final_score, {
        "score": final_score,
        "verdict": verdict,
        "recommendation": apply_recommendation,
        "has_quant_title": has_quant_title,
        "matched_positives": matched_positives,
        "penalties": penalties
    }
