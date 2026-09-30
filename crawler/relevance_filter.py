import re
from typing import Dict, Any, Tuple

CANDIDATE_PROFILE = {
    "role_level": "Quantitative Finance Graduate (Class of 2027)",
    "target_degree": "Quantitative Finance / Financial Engineering",
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

# Positive keywords strictly for quantitative finance and trading roles
KEYWORD_WEIGHTS = {
    # Core target titles (highest priority)
    r"\bquant(?:itative)?\s+research(?:er|)?\b": 45,
    r"\bquant(?:itative)?\s+trad(?:er|ing)\b": 45,
    r"\bquant(?:itative)?\s+strat(?:egist|s)?\b": 42,
    r"\balgo(?:rithmic)?\s+trad(?:er|ing)\b": 40,
    r"\balpha\s+research(?:er|)?\b": 40,
    r"\bfront\s+office\s+strat(?:s|egist)?\b": 40,
    r"\bmachine\s+learning\s+(?:quant|researcher|scientist|engineer)\b": 35,
    r"\bquant(?:itative)?\s+developer\b": 35,
    r"\bquant(?:itative)?\s+analyst\b": 32,
    r"\bportfolio\s+manager\s+associate\b": 25,
    r"\bdata\s+scientist\b": 20,
    r"\bfinancial\s+engineering\b": 18,
    r"\bmathematical\s+finance\b": 18,
    r"\bmachine\s+learning\b": 12,
    r"\bderivatives?\b": 12,
    r"\bvolatility\b": 12,
    r"\bstochastic\b": 10,
    r"\btime\s+series\b": 8,
}

# Non-quant corporate operational, back-office, legal, audit, marketing, sales, and fraud patterns
NON_QUANT_OPERATIONAL_PATTERN = (
    r"\b("
    r"fraud|"
    r"customer\s*(?:support|service|success|experience)|"
    r"client\s*(?:support|service|operations|solutions|success)|"
    r"operations\s*associate|"
    r"operations\s*specialist|"
    r"operations\s*analyst|"
    r"operations\s*manager|"
    r"payment\s*(?:partner\s*)?operations|"
    r"finance\s*associate|"
    r"corporate\s*finance|"
    r"fp&a|"
    r"billing|"
    r"payroll|"
    r"accounting|"
    r"bookkeeper|"
    r"accounts\s*payable|"
    r"accounts\s*receivable|"
    r"audit|internal\s*audit|"
    r"tax\s*(?:associate|analyst|specialist)|"
    r"sales|"
    r"marketing|"
    r"business\s*development|"
    r"bdr|sdr|"
    r"account\s*executive|"
    r"communications|public\s*relations|\bpr\b|"
    r"talent|recruiter|recruiting|human\s*resources|\bhr\b|"
    r"workplace|facilities|receptionist|office\s*manager|"
    r"legal|general\s*counsel|paralegal|compliance|"
    r"trade\s+surveillance\s+associate"
    r")\b"
)

# Negative disqualifiers (experience mismatches or excessive seniority)
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
    Evaluates a candidate job opening against target quantitative finance candidate profile.
    Returns:
        score: int (0 to 100)
        reasons: dict with matched signals, penalties, and fit tier verdict
    """
    title = job_dict.get("title", "").strip()
    location = job_dict.get("location", "").strip()
    department = job_dict.get("department", "").strip()
    description = job_dict.get("description", "") or ""
    
    title_lower = title.lower()

    # Hard rejection 1: Skip any role that has 'intern' or 'summer' in title or early description
    if re.search(r"\b(?:intern|internship|internships|summer)\b", title_lower) or \
       re.search(r"\b(?:summer\s+(?:analyst|associate|intern|program|internship))\b", description[:400].lower()):
        return 0, {
            "score": 0,
            "verdict": "DISQUALIFIED (Internship / Summer)",
            "recommendation": "Skip (Internship or summer program - seeking full-time new grad / junior)",
            "has_quant_title": False,
            "matched_positives": [],
            "penalties": ["Hard Disqualification: Contains 'intern' or 'summer' (-100)"]
        }

    # Hard rejection 2: Skip any role targeting senior, experienced, staff, principal, or executive hires
    if re.search(r"\b(?:senior|sr\.?|staff|principal|lead|head\s+of|director|managing\s+director|executive|vp|vice\s+president)\b|\bexperienced\b", title_lower):
        if not re.search(r"\b(?:junior/senior|senior/junior)\b", title_lower):
            return 0, {
                "score": 0,
                "verdict": "DISQUALIFIED (Senior / Experienced)",
                "recommendation": "Skip (Senior/Experienced role - seeking new grad / entry level / junior)",
                "has_quant_title": False,
                "matched_positives": [],
                "penalties": ["Hard Disqualification: Senior or Experienced title (-100)"]
            }

    # Hard rejection 3: Disqualify corporate operational, back-office, legal, audit, marketing, fraud, and sales roles
    # (Allow legitimate trading operations / quant operations execution desk roles)
    if re.search(NON_QUANT_OPERATIONAL_PATTERN, title_lower):
        is_trading_ops = re.search(r"\b(?:trading\s+operations|quant(?:itative)?\s+operations)\b", title_lower)
        if not is_trading_ops:
            return 0, {
                "score": 0,
                "verdict": "DISQUALIFIED (Non-Quant Operational / Back Office)",
                "recommendation": "Skip (Operational/Back-Office/Non-Quant role)",
                "has_quant_title": False,
                "matched_positives": [],
                "penalties": ["Hard Disqualification: Non-quant operational/back-office title (-100)"]
            }

    full_text = f"{title} | {department} | {location} | {description[:1000]}".lower()

    score = 0
    matched_positives = []
    penalties = []

    # 1. Base tier boost from firm classification (only applied if role has quant relevance)
    tier_boost = {
        "Tier A": 20,
        "Tier B": 15,
        "Tier C1": 8,
        "Tier C2": 4,
        "Tier D": -20,
        "Tier E": -20
    }
    boost_val = 0
    for t_key, boost in tier_boost.items():
        if t_key in firm_tier:
            boost_val = boost
            break

    # 2. Check title specifically for quant roles
    has_quant_title = False
    for pattern, weight in KEYWORD_WEIGHTS.items():
        if re.search(pattern, title_lower):
            score += weight
            matched_positives.append(f"Title match '{pattern}': +{weight}")
            has_quant_title = True

    # 3. Check full text for secondary quant / math signals
    for pattern, weight in KEYWORD_WEIGHTS.items():
        if pattern not in title_lower and re.search(pattern, full_text):
            adj_weight = max(2, weight // 2)
            score += adj_weight
            matched_positives.append(f"Keyword match '{pattern}': +{adj_weight}")

    # If the role has zero quantitative title relevance and zero quant modeling signals, disqualify
    if not has_quant_title and score < 15:
        return 0, {
            "score": 0,
            "verdict": "DISQUALIFIED (Non-Quant Role)",
            "recommendation": "Skip (Title and description lack quantitative finance focus)",
            "has_quant_title": False,
            "matched_positives": [],
            "penalties": ["No quantitative or trading signals matched (-100)"]
        }

    # Apply firm tier boost now that quant relevance is verified
    if boost_val > 0:
        score += boost_val
        matched_positives.append(f"Firm Quality Boost: +{boost_val}")
    elif boost_val < 0:
        score += boost_val
        penalties.append(f"Tier Penalty: {boost_val}")

    # 4. Calibrated Junior / Campus bonus (strictly awarded only if role is confirmed quant)
    if has_quant_title:
        if re.search(r"\b(?:2027|2026|campus|graduate|new\s+grad(?:uate)?|early\s+career|entry\s+level|junior)\b", title_lower) or \
           re.search(r"\b(?:2027|campus|new\s+grad(?:uate)?|graduate\s+program)\b", full_text):
            score += 8
            matched_positives.append("Junior / Campus Quant Target: +8")

    # NOTE: Location provides 0 bonus points (no location boost per user instruction)

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
        apply_recommendation = "Immediate Apply (Tailor quantitative resume)"
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
