import argparse
import csv
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ranking_engine import stream_and_rank_jsonl

DEFAULT_JD = """
Senior AI Engineer — Founding Team
Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid)
Experience Required: 5–9 years

We need someone comfortable with deep technical depth in modern ML systems (embeddings, retrieval, ranking, LLMs) AND a scrappy product-engineering attitude. 
Must have production experience with vector databases (Pinecone, Weaviate, Qdrant, FAISS) and evaluation frameworks (NDCG, MRR, MAP). 
No pure researchers. No framework enthusiasts. No consulting-only backgrounds.
"""

def main():
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranker CLI")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl file")
    parser.add_argument("--jd", default=None, help="Path to JD .txt file (optional, defaults to Redrob JD)")
    parser.add_argument("--out", required=True, help="Path to output submission.csv")
    
    args = parser.parse_args()
    
    jd_text = DEFAULT_JD
    if args.jd and os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_text = f.read()
            
    print(f"📊 Loading candidates from {args.candidates}...")
    
    with open(args.candidates, "rb") as f:
        file_bytes = f.read()
        
    print("⚙️ Running deterministic scoring pipeline (CPU-only)...")
    result = stream_and_rank_jsonl(file_bytes, jd_text=jd_text, top_k=100)
    
    print(f"✅ Evaluated {result['total_evaluated']} valid candidates.")
    print(f"⚠️ Skipped {result['invalid_candidates']} invalid candidates.")
    
    with open(args.out, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for cand in result["ranked_candidates"]:
            writer.writerow([
                cand["candidate_id"],
                cand["rank"],
                cand["score"],
                cand["reasoning"]
            ])
            
    print(f"🏆 Submission CSV saved to {args.out}")

if __name__ == "__main__":
    main()