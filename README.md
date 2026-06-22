# 🏏 India Runs Hackathon — Candidate Ranking System

> **Fully deterministic, CPU-only candidate ranking pipeline** built for the India Runs Hackathon by **Ehsaan Shaikh**.

---

## 🚀 Live Demo

| Layer | Platform | URL |
|-------|----------|-----|
| **Frontend** | Streamlit Cloud | 🌐 [candidate-ranking-system.streamlit.app](https://candidate-ranking-system.streamlit.app) |
| **Backend API** | Hugging Face Spaces | 🤗 [huggingface.co/spaces/Ehsaan08-ai/redrob-ranker](https://huggingface.co/spaces/Ehsaan08-ai/redrob-ranker) |

> ⚠️ **Performance Note:** The app accepts JSONL files up to **1 GB** in size. Small files load and rank quickly. Large files (hundreds of MBs) may take <= 5 minutes to upload and process — please be patient while the ranking pipeline runs.

---

## 📖 Overview

This project implements a **high-performance candidate ranking engine** that scores and ranks job candidates from a JSONL dataset against a target Job Description (JD). The system is built around a six-component weighted scoring model, with honeypot fraud detection and O(n log 100) top-K selection.

The application is split into two independently deployed services:

- **Frontend** — A Streamlit web app (deployed on **Streamlit Cloud**) that provides an intuitive UI for uploading candidate files and viewing ranked results.
- **Backend** — A FastAPI server (deployed on **Hugging Face Spaces**) that hosts the ranking pipeline and exposes a REST API consumed by the frontend.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   USER'S BROWSER                         │
└───────────────────────┬──────────────────────────────────┘
                        │  HTTPS
                        ▼
┌──────────────────────────────────────────────────────────┐
│            FRONTEND — Streamlit Cloud                    │
│         frontend/app.py  (Streamlit UI)                  │
│  • Upload JSONL candidate file (≤ 1 GB)                  │
│  • Display ranked results & reasoning strings            │
└───────────────────────┬──────────────────────────────────┘
                        │  REST API (JSON)
                        ▼
┌──────────────────────────────────────────────────────────┐
│          BACKEND — Hugging Face Spaces                   │
│         backend/main.py  (FastAPI server)                │
│  • Schema validation (fastjsonschema)                    │
│  • Six-component weighted scoring                        │
│  • Honeypot fraud detection                              │
│  • Top-100 selection via min-heap (O(n log 100))         │
└──────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **Zero LLM calls at inference time** — fully deterministic and offline-capable
- **Schema validation** — every candidate is pre-validated before scoring
- **Six-component weighted scoring model:**

  | Component | Weight |
  |-----------|--------|
  | Technical depth + JD word-overlap | 35% |
  | Retrieval systems expertise (Pinecone, FAISS, Weaviate, Qdrant, Elasticsearch) | 20% |
  | Ranking / evaluation knowledge (NDCG, MRR, LTR) | 15% |
  | Production & startup DNA signals | 10% |
  | Redrob platform engagement (open-to-work, response rate, saves) | 5% |
  | Location / relocation availability | 5% |
  | *Honeypot penalty* | up to −10% |

- **Honeypot fraud detection** — penalises inflated YOE, impossible timelines, and expert skills with zero usage months
- **Hard penalty** — 50% score multiplier for consulting-only or pure-research backgrounds excluded by the JD
- **Efficient top-100 selection** — `heapq` min-heap gives O(n log 100) time and O(100) space
- **Grounded reasoning strings** — every ranked candidate receives a fact-derived explanation

---

## 📂 Project Structure

```
India-Runs-Hackathon-Project/
├── frontend/
│   └── app.py                  # Streamlit UI (deployed on Streamlit Cloud)
├── backend/
│   ├── main.py                 # FastAPI application (deployed on Hugging Face Spaces)
│   └── services/               # Scoring, validation, and ranking modules
├── data/                       # Sample / reference data provided by the hackathon website.
├── rank.py                     # CLI entry point for local ranking
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── Dockerfile                  # Container definition (for Hugging Face Spaces)
├── submission_metadata.yaml    # Hackathon submission manifest
└── team_ehsaan.csv             # Team submission CSV
```

---

## ⚡ Quick Start (Local)

### Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### 1. Clone the repository

```bash
git clone https://github.com/Ehsaan08-ai/India-Runs-Hackathon-Project.git
cd India-Runs-Hackathon-Project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the CLI ranker

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### 4. Run the backend locally

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Run the frontend locally

```bash
cd frontend
streamlit run app.py
```

---

## 📤 File Upload Guidelines

| File Size | Expected Behaviour |
|-----------|-------------------|
| < 10 MB | Near-instant upload and ranking |
| 10 MB – 100 MB | Fast — typically a few seconds |
| 100 MB – 500 MB | Moderate — may take up to a minute |
| 500 MB – 1 GB | Slow — please allow several minutes; do not close the tab |
| > 1 GB | ❌ Not supported |

> **Tip:** For the fastest experience during testing, use a representative sample of your dataset (e.g., 5,000–10,000 candidates). The full pipeline processes ~50,000 candidates in approximately 10 seconds on a single CPU core in a local environment. Cloud latency may add overhead for very large uploads.

---

## 🧪 Reproduce Results

Run the ranking pipeline end-to-end with:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

The output CSV will contain the ranked candidates with scores and reasoning strings, ready for hackathon submission.

---

## 🤖 AI Tools Declaration

| Tool | Purpose |
|------|---------|
| Claude | Architectural discussions |
| ChatGPT | Architectural discussions |
| GLM-5.2 | Code generation, debugging, and error handling |

> **Note:** No candidate data was fed to any LLM. The ranking pipeline is 100% deterministic and CPU-only.

---

## 👤 Team

| Name | Role | Contact |
|------|------|---------|
| **Ehsaan Shaikh** | AI Engineer & Team Lead | ehsaanshaikh08@gmail.com |

---

## 📜 Declarations

- ✅ Submission specification read and understood
- ✅ Code is original work
- ✅ No collusion with other teams
- ✅ Honeypot check completed
- ✅ Reproduction tested locally

---

## 📄 License

This project was created solely for the **India Runs Hackathon** competition. All rights reserved © 2026 Ehsaan Shaikh.
