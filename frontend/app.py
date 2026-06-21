import os
import json
import csv
import io
import streamlit as st
import requests
from pathlib import Path


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Redrob Ranker", page_icon="🎯", layout="wide")

css_path = Path(__file__).parent / "static" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

for k, v in {"jd_text": "", "ranking_result": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown("""
<div class="hero">
  <h1>🎯 Redrob Intelligent Candidate Ranker</h1>
  <p>Paste the Job Description and upload your candidate file (.jsonl, .json, or .csv). 
  CPU-only, deterministic scoring, < 5 min runtime.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("## 📄 Step 1 — Job Description")
st.session_state.jd_text = st.text_area(
    "Paste the full Job Description here", height=250, 
    placeholder="Paste the Redrob Senior AI Engineer JD here..."
)

st.markdown("## 📤 Step 2 — Upload Candidate Dataset")
cand_file = st.file_uploader(
    "Upload candidate file", 
    type=["jsonl", "json", "csv"], 
    key="cand_file"
)

if st.button("🚀 Run Deterministic Pipeline", type="primary"):
    if not st.session_state.jd_text.strip():
        st.error("Please paste the Job Description first.")
    elif cand_file is None:
        st.error("Please upload a candidate file.")
    else:
        with st.spinner("⚙️ Streaming, validating, and scoring candidates..."):
            try:
                files = {"file": (cand_file.name, cand_file.getvalue())}
                data = {"jd_text": st.session_state.jd_text}
                r = requests.post(f"{BACKEND_URL}/api/rank", files=files, data=data, timeout=600)
                if r.ok:
                    st.session_state.ranking_result = r.json()
                    st.success(f"✅ Evaluated {r.json()['total_evaluated']} valid candidates.")
                else:
                    st.error(f"Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

result = st.session_state.ranking_result
if result:
    st.markdown("---")
    st.markdown("## 🏆 Top 100 Shortlist")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Valid Candidates Processed", result["total_evaluated"])
    with col2:
        st.metric("Invalid/Skipped Records", result["invalid_candidates"])

    # Generate CSV directly in Streamlit for instant download
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    
    for cand in result.get("ranked_candidates", []):
        writer.writerow([
            cand["candidate_id"],
            cand["rank"],
            cand["score"],
            cand["reasoning"]
        ])
        
    st.download_button(
        label="📥 Download Submission CSV",
        data=csv_buffer.getvalue().encode('utf-8'),
        file_name="redrob_submission.csv",
        mime="text/csv"
    )

    for cand in result["ranked_candidates"]:
        scores = cand.get("scores", {})
        st.markdown(f"""
        <div class="candidate-card">
          <div style="display:flex;align-items:center;gap:14px;">
            <div class="rank-badge">#{cand['rank']}</div>
            <div style="flex:1;">
              <div style="font-size:1.1rem;font-weight:600;">{cand['candidate_id']}</div>
              <div style="color:#94a3b8;font-size:0.8rem;">{cand['candidate_name']}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:1.4rem;font-weight:700;color:#22d3ee;">{cand['score']}</div>
              <div style="font-size:0.7rem;color:#94a3b8;">SCORE (0-1)</div>
            </div>
          </div>
          <div style="margin-top:12px;">
            <div class="section-label">Reasoning</div>
            <p style="margin:4px 0 0 0;font-size:0.9rem;">{cand['reasoning']}</p>
          </div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px;font-size:0.75rem;color:#94a3b8;">
            <div>Tech: {scores.get('tech_score', 0)}</div>
            <div>Retrieval: {scores.get('retrieval_score', 0)}</div>
            <div>Ranking: {scores.get('ranking_score', 0)}</div>
            <div>Honeypot: {scores.get('honeypot_score', 0)}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)