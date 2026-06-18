# 🏆 Redrob Candidate Ranking System v4

An ultra-fast, offline, CPU-only candidate ranking and retrieval system built for the Redrob **Intelligent Candidate Discovery & Ranking Challenge**. 

This repository implements a **Hybrid Search Pipeline** (Dense Vector + Sparse Lexical) coupled with a heavy mathematical heuristics engine to dynamically rank thousands of candidates against a Job Description in under 30 seconds.

---

## 🏗️ Architecture Design

To comply with the strict **5-minute CPU-only offline constraint**, the system is divided into two distinct phases:

### Phase 1: Offline Cache Generation (`vectorDB.py`)
Because generating 100,000+ dense embeddings via transformer models takes approximately 15 minutes on a standard CPU, this operation is pulled completely **offline**.
1. **SentenceTransformers**: Parses every candidate's raw profile into a 384-dimensional dense semantic vector.
2. **BM25 Lexical Index**: Generates a high-speed sparse dictionary for exact keyword matching.
3. **Serialization**: The computed matrices and feature sets are serialized and cached to disk as `.pkl` files.

### Phase 2: Online API (`rank.py`)
The actual API endpoint (`http://localhost:8000/rank`) achieves **O(1) retrieval speeds** by instantly hitting the offline cache instead of parsing the 500MB candidate file during the network request.
1. **Extraction**: Uses `PyPDF2` / `python-docx` to extract text and heuristic requirements from the uploaded Job Description.
2. **Hybrid Retrieval**: Queries the Dense and Sparse caches simultaneously and merges the Top 1,000 candidates using **Reciprocal Rank Fusion (RRF)**.
3. **Parallel Deep Scoring**: Splits the Top 1,000 candidates across the physical CPU cores using Python `ProcessPoolExecutor` to compute intense heuristic scoring (Gaussian Decay for experience, Jaccard Index for skills, and Honeypot penalty detection).
4. **Tie-Breaking**: Formats the final Top 100 mathematically according to the strict validation rules and streams a beautifully formatted CSV and JSON back to the client.

---

## 💻 Tech Stack

### Backend (Python/FastAPI)
- **FastAPI** + **Uvicorn**: Lightning-fast async web server.
- **Sentence-Transformers**: Local, open-source transformer models running entirely on CPU.
- **NumPy**: Matrix multiplication and high-speed Cosine Similarity.
- **Python multiprocessing**: Bypassing the Global Interpreter Lock (GIL) for parallel CPU-bound scoring.

### Frontend (React/Vite)
- **React + Context API**: State management across the application.
- **Tailwind CSS**: Glassmorphism, animations, and modern dark-mode aesthetics.
- **React-Dropzone**: Seamless file uploading interactions.

---

## 🚀 How to Run Locally

### 1. Build the Offline Cache
Before starting the server, you must run the offline ingestion pipeline to create the `.pkl` caches.
*(Note: To save time during testing, we run this on a `small_candidates.jsonl` slice of the dataset).*
```bash
cd server
python -m controller.utils.vectorDB ../dataset/India_runs_data_and_ai_challenge/small_candidates.jsonl
```

### 2. Start the Backend API
Start the FastAPI server. It will automatically load the `.pkl` caches into memory.
```bash
cd server
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

### 3. Start the Frontend Dashboard
Start the Vite development server to launch the React UI.
```bash
cd client
npm run dev
```
The Dashboard will be available at `http://localhost:5173`.

---

## ✅ Current Status
- [x] Implemented Offline Dense + Sparse Hybrid Caching.
- [x] Implemented API Pipeline with Parallel Processing.
- [x] Implemented Modern React Frontend with Glassmorphism UI.
- [x] Evaluated strict Tie-Breaking rules (Passes `validate_submission.py`).
- [ ] **NEXT UP**: Hyper-optimize `matchers.py` heuristic rules to align explicitly with the hidden hackathon "Honeypot" disqualifiers inside the provided Job Description.
