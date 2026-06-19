from typing import List, Dict, Any, Tuple
import numpy as np
from .embeddings import embed_text, embed_texts, cosine_similarity, candidate_to_text
from .llm_ranker import summarize_jd, score_candidate

def rank_candidates(
    jd_text: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 10,
) -> Dict[str, Any]:
    if not candidates:
        raise ValueError("No candidates provided")

    # 1) Understand the JD
    jd_summary, key_requirements = summarize_jd(jd_text)

    # 2) Semantic embedding of the role
    jd_query = jd_summary + "\n" + "\n".join(key_requirements)
    jd_vec = embed_text(jd_query)

    # 3) Embed each candidate (semantic search step)
    cand_texts = [candidate_to_text(c) for c in candidates]
    cand_vecs = embed_texts(cand_texts)  # shape: (N, D)

    semantic_scores = []
    for i, vec in enumerate(cand_vecs):
        semantic_scores.append(cosine_similarity(jd_vec, vec))

    # 4) LLM evaluation per candidate
    llm_results = []
    for c in candidates:
        llm_results.append(score_candidate(jd_summary, key_requirements, c))

    # 5) Hybrid scoring
    # Normalize semantic scores to 0-100 (cosine in [-1,1] -> [0,100])
    sem_arr = np.array(semantic_scores)
    if sem_arr.max() > sem_arr.min():
        sem_norm = (sem_arr - sem_arr.min()) / (sem_arr.max() - sem_arr.min()) * 100
    else:
        sem_norm = np.full_like(sem_arr, 50.0)

    alpha = 0.35  # semantic weight
    beta = 0.65   # LLM weight

    results = []
    for i, cand in enumerate(candidates):
        llm_score = float(llm_results[i].get("llm_score", 0.0))
        final = alpha * float(sem_norm[i]) + beta * llm_score
        results.append({
            "candidate_id": str(cand.get("candidate_id") or cand.get("id") or f"cand_{i}"),
            "candidate_name": str(cand.get("name") or cand.get("full_name") or cand.get("candidate_name") or f"Candidate {i+1}"),
            "semantic_score": round(float(sem_norm[i]), 2),
            "llm_score": round(llm_score, 2),
            "final_score": round(final, 2),
            "reasoning": llm_results[i].get("reasoning", ""),
            "strengths": llm_results[i].get("strengths", []),
            "concerns": llm_results[i].get("concerns", []),
            "recommendation": llm_results[i].get("recommendation", ""),
            "raw_data": cand,
        })

    # 6) Sort and rank
    results.sort(key=lambda x: x["final_score"], reverse=True)
    for rank, r in enumerate(results, start=1):
        r["rank"] = rank

    # 7) Trim to top_k (but keep total_evaluated accurate)
    total_evaluated = len(results)
    ranked = results[:top_k]

    return {
        "job_summary": jd_summary,
        "key_requirements": key_requirements,
        "ranked_candidates": ranked,
        "total_evaluated": total_evaluated,
    }