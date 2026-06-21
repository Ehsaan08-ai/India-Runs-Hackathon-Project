import os
import json
import csv
import io
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import Body
from backend.services.jd_parser import parse_docx
from backend.services.ranking_engine import stream_and_rank_candidates


app = FastAPI(title="Redrob AI Candidate Ranker", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "Redrob AI Candidate Ranker v2"}

@app.post("/api/jd/upload-docx")
async def upload_jd_docx(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are accepted")
    content = await file.read()
    try:
        text = parse_docx(content)
        return {"jd_text": text, "filename": file.filename}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/rank")
async def rank(file: UploadFile = File(...), jd_text: str = Form(...)):
    """Main ranking endpoint. Accepts .jsonl, .json, or .csv files."""
    content = await file.read()
    filename = file.filename.lower()
    lines = []
    
    try:
        if filename.endswith(".jsonl"):
            # Already line-by-line JSON objects
            lines = content.decode("utf-8").splitlines()
            
        elif filename.endswith(".json"):
            # Standard JSON array or single object
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                lines = [json.dumps(obj) for obj in data]
            elif isinstance(data, dict):
                lines = [json.dumps(data)]
            else:
                raise HTTPException(400, "JSON must be an array or object")
                
        elif filename.endswith(".csv"):
            # Convert CSV rows back to JSON strings for the pipeline
            # Note: Redrob schema requires nested objects, so CSV cells containing 
            # JSON (like '{"min": 10, "max": 20}') will be parsed safely.
            reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
            for row in reader:
                parsed_row = {}
                for k, v in row.items():
                    if v is None or v == "": continue
                    try:
                        # Attempt to parse nested JSON strings
                        parsed_row[k] = json.loads(v)
                    except json.JSONDecodeError:
                        parsed_row[k] = v
                lines.append(json.dumps(parsed_row))
        else:
            raise HTTPException(400, "Unsupported file format. Please use .jsonl, .json, or .csv")
            
        result = stream_and_rank_candidates(lines, jd_text=jd_text, top_k=100)
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(500, f"Ranking failed: {str(e)}")

@app.post("/api/export-csv")
async def export_csv(data: Dict[Any, Any] = Body(...)):
    """Generates strict CSV output."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    
    for cand in data.get("ranked_candidates", []):
        writer.writerow([
            cand["candidate_id"],
            cand["rank"],
            cand["score"],
            cand["reasoning"]
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=redrob_submission.csv"}
    )