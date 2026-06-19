import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas import JDTextRequest, CandidateJSONRequest, RankRequest, RankResponse
from backend.services.jd_parser import parse_docx
from backend.services.ranking_engine import rank_candidates

load_dotenv()

app = FastAPI(title="AI Candidate Ranker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "AI Candidate Ranker"}

@app.post("/api/jd/upload-docx")
async def upload_jd_docx(file: UploadFile = File(...)):
    """Upload a JD as a .docx file, returns extracted text."""
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are accepted")
    content = await file.read()
    try:
        text = parse_docx(content)
        return {"jd_text": text, "filename": file.filename}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/candidates/upload-json")
async def upload_candidates_json(files: List[UploadFile] = File(...)):
    """Accept one or more JSON files. Each can be either an array of candidates
    or a single candidate object. Returns merged list."""
    all_candidates: List[Dict[str, Any]] = []
    for f in files:
        if not f.filename.lower().endswith(".json"):
            raise HTTPException(400, f"{f.filename} is not a .json file")
        raw = await f.read()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise HTTPException(400, f"Invalid JSON in {f.filename}: {e}")
        if isinstance(data, list):
            all_candidates.extend(data)
        elif isinstance(data, dict):
            all_candidates.append(data)
        else:
            raise HTTPException(400, f"Unexpected JSON structure in {f.filename}")
    return {"candidates": all_candidates, "count": len(all_candidates)}

@app.post("/api/rank", response_model=RankResponse)
def rank(req: RankRequest):
    """Main ranking endpoint. Accepts JD text + candidates list."""
    if not req.jd_text.strip():
        raise HTTPException(400, "Job description is empty")
    if not req.candidates:
        raise HTTPException(400, "No candidates provided")
    try:
        result = rank_candidates(req.jd_text, req.candidates, top_k=req.top_k)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, f"Ranking failed: {e}")