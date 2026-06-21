# rank.py
import argparse
import csv
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from services.ranking_engine import stream_and_rank_candidates

DEFAULT_JD = "Senior AI Engineer..."

def main():
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranker CLI")
    parser.add_argument("--candidates", required=True, help="Path to candidates file (.jsonl, .json, .csv)")
    parser.add_argument("--jd", default=None, help="Path to JD .txt file (optional)")
    parser.add_argument("--out", required=True, help="Path to output submission.csv")
    
    args = parser.parse_args()
    
    jd_text = DEFAULT_JD
    if args.jd and os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_text = f.read()
            
    print(f"📊 Loading candidates from {args.candidates}...")
    
    lines = []
    with open(args.candidates, "r", encoding="utf-8") as f:
        if args.candidates.endswith(".jsonl"):
            lines = f.read().splitlines()
        elif args.candidates.endswith(".json"):
            data = json.load(f)
            if isinstance(data, list):
                lines = [json.dumps(obj) for obj in data]
            else:
                lines = [json.dumps(data)]
        elif args.candidates.endswith(".csv"):
            reader = csv.DictReader(f)
            for row in reader:
                parsed_row = {}
                for k, v in row.items():
                    if v is None or v == "": continue
                    try:
                        parsed_row[k] = json.loads(v)
                    except:
                        parsed_row[k] = v
                lines.append(json.dumps(parsed_row))
        
    print("⚙️ Running deterministic scoring pipeline (CPU-only)...")
    result = stream_and_rank_candidates(lines, jd_text=jd_text, top_k=100)
    
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