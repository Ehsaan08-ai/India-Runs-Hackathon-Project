import json
import heapq
import re
from typing import List, Dict, Any
from .validator import validate_candidate
from .honeypot import calculate_honeypot

RETRIEVAL_KEYWORDS = ["retrieval", "embedding", "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch", "faiss", "vector", "opensearch"]
RANKING_KEYWORDS = ["ranking", "ndcg", "mrr", "map", "learning to rank", "ltr", "recommendation", "search"]
PROD_KEYWORDS = ["production", "deployed", "shipped", "end-to-end", "scale"]
STARTUP_KEYWORDS = ["founding", "founder", "early", "startup", "series a", "series b"]
NEGATIVE_KEYWORDS = ["researcher", "academic", "marketing", "consultant", "tcs", "infosys", "wipro", "accenture"]
TARGET_LOCATIONS = ["pune", "noida", "mumbai", "delhi", "hyderabad", "bangalore"]

def extract_text(candidate: Dict[str, Any]) -> str:
    parts = []
    profile = candidate.get("profile", {})
    parts.append(profile.get("headline", ""))
    parts.append(profile.get("summary", ""))
    parts.append(profile.get("current_title", ""))
    parts.append(profile.get("current_company", ""))
    for job in candidate.get("career_history", []):
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))
    for skill in candidate.get("skills", []):
        parts.append(skill.get("name", ""))
    return " ".join(parts).lower()

def calculate_scores(candidate: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    text = extract_text(candidate)
    jd_text_lower = jd_text.lower()
    signals = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})
    
    jd_words = set(re.findall(r'\b[A-Za-z0-9+#.]+\b', jd_text_lower))
    cand_words = set(re.findall(r'\b[A-Za-z0-9+#.]+\b', text))
    jd_overlap = len(jd_words.intersection(cand_words)) / max(len(jd_words), 1)
    
    yoe = profile.get("years_of_experience", 0)
    yoe_score = min(yoe / 9.0, 1.0)
    tech_score = (yoe_score * 0.20) + (jd_overlap * 0.15)
    
    ret_matches = sum(1 for kw in RETRIEVAL_KEYWORDS if kw in text or kw in jd_text_lower)
    retrieval_score = min(ret_matches / 3.0, 1.0) * 0.20
    
    rank_matches = sum(1 for kw in RANKING_KEYWORDS if kw in text or kw in jd_text_lower)
    ranking_score = min(rank_matches / 2.0, 1.0) * 0.15
    
    prod_matches = sum(1 for kw in PROD_KEYWORDS if kw in text)
    startup_matches = sum(1 for kw in STARTUP_KEYWORDS if kw in text)
    behavioral_score = (min(prod_matches/2.0, 1.0) * 0.05) + (min(startup_matches/1.0, 1.0) * 0.05)
    
    open_to_work = signals.get("open_to_work_flag", False)
    resp_rate = signals.get("recruiter_response_rate", 0)
    saved = signals.get("saved_by_recruiters_30d", 0)
    engagement_score = (0.4 if open_to_work else 0.0) + (resp_rate * 0.3) + (min(saved/10.0, 1.0) * 0.3)
    engagement_score *= 0.05
    
    loc = profile.get("location", "").lower()
    will_relocate = signals.get("willing_to_relocate", False)
    notice = signals.get("notice_period_days", 60)
    loc_score = 0.0
    if any(l in loc for l in TARGET_LOCATIONS): loc_score = 1.0
    elif will_relocate and notice <= 30: loc_score = 0.5
    loc_score *= 0.05
    
    hp_score, hp_reasons = calculate_honeypot(candidate)
    penalty = hp_score * 0.10
    
    raw_score = tech_score + retrieval_score + ranking_score + behavioral_score + engagement_score + loc_score - penalty
    final_score = max(0.0, min(1.0, raw_score))
    
    neg_matches = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    if neg_matches > 0:
        final_score *= 0.5
        
    return {
        "final_score": round(final_score, 4),
        "tech_score": round(tech_score, 4),
        "retrieval_score": round(retrieval_score, 4),
        "ranking_score": round(ranking_score, 4),
        "behavioral_score": round(behavioral_score, 4),
        "engagement_score": round(engagement_score, 4),
        "loc_score": round(loc_score, 4),
        "honeypot_penalty": round(penalty, 4),
        "honeypot_score": round(hp_score, 4),
        "honeypot_reasons": hp_reasons
    }

def generate_reasoning(candidate: Dict[str, Any], scores: Dict[str, Any]) -> str:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    text = extract_text(candidate)
    
    parts = []
    parts.append(f"{profile.get('years_of_experience', 0)} YOE as {profile.get('current_title', 'Engineer')}.")
    
    if scores["retrieval_score"] > 0.1:
        techs = [kw for kw in RETRIEVAL_KEYWORDS if kw in text][:2]
        parts.append(f"Strong retrieval background ({', '.join(techs)}).")
    else:
        parts.append("Limited explicit retrieval systems experience.")
        
    if scores["loc_score"] > 0:
        parts.append(f"Located in {profile.get('location', 'India')} with {signals.get('notice_period_days', 60)}d notice.")
        
    if scores["honeypot_score"] > 0.3:
        parts.append(f"WARNING: Honeypot risk detected ({'; '.join(scores['honeypot_reasons'][:1])}).")
        
    return " ".join(parts)

def stream_and_rank_jsonl(file_bytes: bytes, jd_text: str, top_k: int = 100) -> Dict[str, Any]:
    valid_count = 0
    invalid_count = 0
    heap = []
    
    lines = file_bytes.decode("utf-8").splitlines()
    for line in lines:
        if not line.strip(): continue
        try:
            cand = json.loads(line)
        except json.JSONDecodeError:
            invalid_count += 1
            continue
            
        if not validate_candidate(cand):
            invalid_count += 1
            continue
            
        valid_count += 1
        scores = calculate_scores(cand, jd_text)
        
        if scores["final_score"] < 0.05: continue
        
        reasoning = generate_reasoning(cand, scores)
        cand_id = cand.get("candidate_id", "UNKNOWN")
        
        heap_item = (
            scores["final_score"], scores["tech_score"], scores["retrieval_score"],
            scores["engagement_score"], -scores["honeypot_score"], cand_id,
            cand, scores, reasoning
        )
        
        if len(heap) < top_k:
            heapq.heappush(heap, heap_item)
        else:
            if heap_item > heap[0]:
                heapq.heappushpop(heap, heap_item)
                
    heap.sort(key=lambda x: (-round(x[0], 4), x[5]))
    
    ranked_candidates = []
    for rank, item in enumerate(heap, 1):
        score, tech, ret, eng, neg_hp, cand_id, cand, scores, reasoning = item
        ranked_candidates.append({
            "candidate_id": cand_id,
            "candidate_name": cand.get("profile", {}).get("anonymized_name", "Unknown"),
            "rank": rank,
            "score": round(score, 4),
            "reasoning": reasoning,
            "scores": scores,
            "raw_data": cand
        })

    return {
        "ranked_candidates": ranked_candidates,
        "total_evaluated": valid_count,
        "invalid_candidates": invalid_count
    }