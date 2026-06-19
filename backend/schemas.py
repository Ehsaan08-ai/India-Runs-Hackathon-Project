from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class JDTextRequest(BaseModel):
    jd_text: str

class CandidateJSONRequest(BaseModel):
    candidates: List[Dict[str, Any]]

class RankRequest(BaseModel):
    jd_text: str
    candidates: List[Dict[str, Any]]
    top_k: int = 10

class CandidateResult(BaseModel):
    candidate_id: str
    candidate_name: str
    semantic_score: float
    llm_score: float
    final_score: float
    rank: int
    reasoning: str
    strengths: List[str]
    concerns: List[str]
    recommendation: str
    raw_data: Dict[str, Any]

class RankResponse(BaseModel):
    job_summary: str
    key_requirements: List[str]
    ranked_candidates: List[CandidateResult]
    total_evaluated: int