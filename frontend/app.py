import os
import json
import streamlit as st
import requests
from pathlib import Path

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ----------------------------- Page config -----------------------------
st.set_page_config(
    page_title="AI Recruiter — Candidate Ranking",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
css_path = Path(__file__).parent / "static" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ----------------------------- Session state ---------------------------
for k, v in {
    "jd_text": "",
    "candidates": [],
    "ranking_result": None,
    "error": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------- Hero ------------------------------------
st.markdown("""
<div class="hero">
  <h1>🎯 AI Recruiter — Rank Candidates Like a Great Recruiter</h1>
  <p>Paste or upload a Job Description, add candidates (JSON), and let the AI
  understand role fit beyond keywords — using semantic search + LLM reasoning
  powered by Groq.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Sidebar ---------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    top_k = st.slider("Top candidates to show", 5, 50, 10)
    st.markdown("---")
    st.markdown("### 🚀 How it works")
    st.markdown(
        "1. **Understand JD** — LLM extracts role context, not just keywords.\n\n"
        "2. **Embed candidates** — semantic search via sentence-transformers.\n\n"
        "3. **LLM evaluation** — Groq scores each candidate holistically.\n\n"
        "4. **Hybrid score** — weighted blend of semantic + LLM scores."
    )
    st.markdown("---")
    st.caption(f"Backend: `{BACKEND_URL}`")

# ----------------------------- JD input --------------------------------
st.markdown("## 📄 Step 1 — Job Description")
jd_tab1, jd_tab2 = st.tabs(["📝 Paste JD", "📎 Upload .docx"])

with jd_tab1:
    jd_text_input = st.text_area(
        "Paste job description text", height=240,
        placeholder="Paste the full job description here...",
        key="jd_paste"
    )
    if jd_text_input.strip():
        st.session_state.jd_text = jd_text_input.strip()

with jd_tab2:
    jd_file = st.file_uploader("Upload JD as .docx", type=["docx"], key="jd_file")
    if jd_file is not None:
        if st.button("Parse uploaded JD", key="parse_jd"):
            try:
                files = {"file": (jd_file.name, jd_file.getvalue())}
                r = requests.post(f"{BACKEND_URL}/api/jd/upload-docx", files=files, timeout=30)
                if r.ok:
                    st.session_state.jd_text = r.json()["jd_text"]
                    st.success(f"✅ Parsed JD from {jd_file.name}")
                else:
                    st.error(f"Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

if st.session_state.jd_text:
    st.markdown('<div class="section-label">Current JD (preview)</div>', unsafe_allow_html=True)
    st.text_area("JD Preview", st.session_state.jd_text[:1500], height=160, disabled=True, key="jd_preview")

# ----------------------------- Candidates input ------------------------
st.markdown("## 👥 Step 2 — Candidates")

cand_tab1, cand_tab2, cand_tab3 = st.tabs(
    ["📝 Paste JSON", "📎 Upload JSON", "📂 Upload Multiple Files"]
)

with cand_tab1:
    cand_paste = st.text_area(
        "Paste candidate JSON (array of objects)",
        height=240,
        placeholder='[{"name": "Alice", "skills": ["Python", "AWS"], "experience": [...]}]',
        key="cand_paste"
    )
    if st.button("Load pasted JSON", key="load_paste"):
        try:
            data = json.loads(cand_paste)
            if isinstance(data, list):
                st.session_state.candidates = data
                st.success(f"✅ Loaded {len(data)} candidates")
            elif isinstance(data, dict):
                st.session_state.candidates = [data]
                st.success("✅ Loaded 1 candidate")
            else:
                st.error("Expected a JSON array or object.")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

with cand_tab2:
    cand_file = st.file_uploader("Upload a single .json file", type=["json"], key="cand_single")
    if cand_file is not None and st.button("Load JSON file", key="load_single"):
        try:
            data = json.loads(cand_file.getvalue().decode("utf-8"))
            if isinstance(data, list):
                st.session_state.candidates = data
            elif isinstance(data, dict):
                st.session_state.candidates = [data]
            st.success(f"✅ Loaded {len(st.session_state.candidates)} candidates")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

with cand_tab3:
    cand_files = st.file_uploader(
        "Upload multiple .json files", type=["json"],
        accept_multiple_files=True, key="cand_multi"
    )
    if cand_files and st.button("Load all files", key="load_multi"):
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/candidates/upload-json",
                files=[("files", (f.name, f.getvalue())) for f in cand_files],
                timeout=60
            )
            if r.ok:
                st.session_state.candidates = r.json()["candidates"]
                st.success(f"✅ Loaded {r.json()['count']} candidates")
            else:
                st.error(f"Failed: {r.text}")
        except Exception as e:
            st.error(f"Error: {e}")

# Show candidate count
if st.session_state.candidates:
    st.info(f"📊 {len(st.session_state.candidates)} candidates loaded")
    with st.expander("Preview first candidate"):
        st.json(st.session_state.candidates[0])
else:
    st.warning("No candidates loaded yet.")

# ----------------------------- Rank button -----------------------------
st.markdown("## 🚀 Step 3 — Run AI Ranking")
col1, col2 = st.columns([1, 3])
with col1:
    run = st.button("🎯 Rank Candidates", type="primary", use_container_width=True)

if run:
    if not st.session_state.jd_text.strip():
        st.error("Please provide a Job Description first.")
    elif not st.session_state.candidates:
        st.error("Please load candidate data first.")
    else:
        with st.spinner("🧠 AI is understanding the role and evaluating candidates..."):
            try:
                payload = {
                    "jd_text": st.session_state.jd_text,
                    "candidates": st.session_state.candidates,
                    "top_k": top_k,
                }
                r = requests.post(f"{BACKEND_URL}/api/rank", json=payload, timeout=600)
                if r.ok:
                    st.session_state.ranking_result = r.json()
                else:
                    st.error(f"Ranking failed: {r.status_code} — {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# ----------------------------- Results ---------------------------------
result = st.session_state.ranking_result
if result:
    st.markdown("---")
    st.markdown("## 🏆 Ranked Shortlist")

    # Job understanding summary
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🧠 How the AI understood the role")
        st.write(result["job_summary"])
        st.markdown("**Key requirements identified:**")
        req_html = "".join(f'<span class="tag">{r}</span>' for r in result["key_requirements"])
        st.markdown(req_html, unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;margin-top:12px;'>"
                    f"Evaluated <b>{result['total_evaluated']}</b> candidates, showing top "
                    f"{len(result['ranked_candidates'])}.</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Candidate cards
    for cand in result["ranked_candidates"]:
        rec = cand["recommendation"].lower()
        if "strong" in rec: tag_class = "tag-good"
        elif "good" in rec: tag_class = "tag-good"
        elif "borderline" in rec: tag_class = "tag-warn"
        else: tag_class = "tag-bad"

        score = cand["final_score"]
        score_pct = max(0, min(100, score))

        st.markdown(f"""
        <div class="candidate-card">
          <div style="display:flex;align-items:center;gap:14px;">
            <div class="rank-badge">#{cand['rank']}</div>
            <div style="flex:1;">
              <div style="font-size:1.2rem;font-weight:600;">{cand['candidate_name']}</div>
              <div style="color:#94a3b8;font-size:0.85rem;">ID: {cand['candidate_id']}</div>
            </div>
            <span class="tag {tag_class}">{cand['recommendation']}</span>
            <div style="text-align:right;">
              <div style="font-size:1.6rem;font-weight:700;color:#22d3ee;">{score:.1f}</div>
              <div style="font-size:0.7rem;color:#94a3b8;">FINAL SCORE</div>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px;">
            <div>
              <div class="section-label">Semantic match</div>
              <div style="display:flex;justify-content:space-between;font-size:0.85rem;">
                <span>{cand['semantic_score']:.1f}</span>
              </div>
              <div class="score-bar"><div class="score-fill" style="width:{cand['semantic_score']:.1f}%"></div></div>
            </div>
            <div>
              <div class="section-label">LLM evaluation</div>
              <div style="display:flex;justify-content:space-between;font-size:0.85rem;">
                <span>{cand['llm_score']:.1f}</span>
              </div>
              <div class="score-bar"><div class="score-fill" style="width:{cand['llm_score']:.1f}%"></div></div>
            </div>
          </div>

          <div style="margin-top:14px;">
            <div class="section-label">Why this ranking</div>
            <p style="margin:4px 0 0 0;line-height:1.55;">{cand['reasoning']}</p>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px;">
            <div>
              <div class="section-label">💪 Strengths</div>
              {''.join(f'<div style="color:#10b981;font-size:0.85rem;margin:2px 0;">• {s}</div>' for s in cand['strengths']) or '<div style="color:#94a3b8;font-size:0.85rem;">None listed</div>'}
            </div>
            <div>
              <div class="section-label">⚠️ Concerns</div>
              {''.join(f'<div style="color:#f59e0b;font-size:0.85rem;margin:2px 0;">• {c}</div>' for c in cand['concerns']) or '<div style="color:#94a3b8;font-size:0.85rem;">None listed</div>'}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"View raw candidate data — {cand['candidate_name']}"):
            st.json(cand["raw_data"])

    # Export
    st.markdown("### 📥 Export results")
    export_json = json.dumps(result, indent=2)
    st.download_button(
        "Download ranked shortlist (JSON)",
        export_json,
        file_name="ranked_candidates.json",
        mime="application/json"
    )