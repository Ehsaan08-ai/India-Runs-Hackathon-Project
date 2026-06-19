import os
import json
from groq import Groq
from typing import Dict, Any, List, Tuple

_client = None

def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable not set")
        _client = Groq(api_key=api_key)
    return _client

def _llm(messages, temperature=0.2, max_tokens=1500):
    client = get_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content

def summarize_jd(jd_text: str) -> Tuple[str, List[str]]:
    """Use LLM to deeply understand the role (not just keyword extraction)."""
    prompt = f"""
You are an expert technical recruiter. Read the following job description and:
1. Produce a 2-3 sentence summary of what the role ACTUALLY needs (responsibilities, seniority, scope).
2. List 5-10 key requirements/skills/behaviors that matter most — including implicit signals (e.g., leadership, ownership, scale of impact).

Return JSON: {{"summary": str, "key_requirements": [str]}}

JOB DESCRIPTION:
{jd_text}
"""
    out = _llm([{"role": "user", "content": prompt}])
    parsed = json.loads(out)
    return parsed.get("summary", ""), parsed.get("key_requirements", [])

def score_candidate(jd_summary: str, key_requirements: List[str], candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ask the LLM to evaluate one candidate against the role — the way a great
    recruiter would: career history, skills, behavioral signals, platform activity.
    """
    cand_json = json.dumps(candidate, indent=2, default=str)[:6000]
    reqs = "\n".join(f"- {r}" for r in key_requirements)

    prompt = f"""
You are a senior technical recruiter evaluating a candidate for an open role.
Think holistically — career trajectory, demonstrated skills, behavioral signals,
impact/scope, and platform activity. Do NOT just match keywords.

ROLE SUMMARY:
{jd_summary}

KEY REQUIREMENTS:
{reqs}

CANDIDATE DATA (JSON):
{cand_json}

Evaluate this candidate against the role. Return strict JSON with:
{{
  "llm_score": <0-100 float>,
  "recommendation": "<Strong Match | Good Match | Borderline | Weak Match>",
  "strengths": [<3-5 short bullets>],
  "concerns": [<2-4 short bullets, or empty list>],
  "reasoning": "<2-4 sentence explanation of WHY they fit or don't — focus on substance not keywords>"
}}
"""
    try:
        out = _llm([{"role": "user", "content": prompt}], temperature=0.2)
        return json.loads(out)
    except Exception as e:
        return {
            "llm_score": 0.0,
            "recommendation": "Evaluation Failed",
            "strengths": [],
            "concerns": [f"LLM error: {e}"],
            "reasoning": "Could not evaluate candidate."
        }