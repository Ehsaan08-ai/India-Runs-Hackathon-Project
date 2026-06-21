from typing import Dict, Any, Tuple, List
from datetime import datetime

def calculate_honeypot(candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Returns honeypot_score (0.0 to 1.0) and list of reasons."""
    reasons = []
    score = 0.0
    
    try:
        yoe = candidate.get("profile", {}).get("years_of_experience", 0)
        career = candidate.get("career_history", [])
        if career and yoe > 0:
            earliest_start = min([datetime.strptime(c["start_date"], "%Y-%m-%d") for c in career])
            actual_years = (datetime.now() - earliest_start).days / 365.25
            if yoe > actual_years + 1: 
                score += 0.3
                reasons.append(f"Claimed {yoe} YOE but career history spans only {actual_years:.1f} years")
    except Exception:
        pass

    for skill in candidate.get("skills", []):
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 0) == 0:
            score += 0.4
            reasons.append(f"Expert skill '{skill.get('name')}' has 0 months usage")
            break
            
    try:
        edu = candidate.get("education", [])
        career = candidate.get("career_history", [])
        if edu and career:
            latest_edu_end = max([e.get("end_year", 2000) for e in edu])
            earliest_career_start = min([int(c["start_date"][:4]) for c in career])
            if earliest_career_start < latest_edu_end - 5: # Allow 5 years overlap for part-time
                score += 0.2
                reasons.append("Career started significantly before graduation")
    except Exception:
        pass

    return min(score, 1.0), reasons