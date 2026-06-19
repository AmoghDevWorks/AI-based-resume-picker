# Redrob AI Candidate Ranking System

An AI-powered candidate ranking and filtering system built for Redrob Hackathon v4. This platform analyzes a Job Description (JD) and a pool of candidates to intelligently rank, filter, and surface the most qualified individuals while detecting honeypots and inflated profiles.

## ✨ Features

- **Multi-Modal Intake**: Upload Job Descriptions as PDF or DOCX, and Candidate Data as JSONL.
- **AI-Powered Scoring Engine**: Uses TF-IDF and specialized heuristics to calculate a holistic match score based on skills, experience, and platform signals.
- **Honeypot Detection**: Automatically flags and penalizes "honeypot" candidates (e.g., impossible timelines, skill inflation).
- **Semantic Search**: Generates deep embeddings using `sentence-transformers` and stores them in a FAISS Vector Database for rapid similarity search.
- **Explainable AI**: Provides transparent reasoning for why a candidate received their specific score.
- **Sleek UI**: A highly responsive, dark-mode React frontend with drag-and-drop zones and interactive candidate modals.

## 🏗️ Architecture

- **Frontend**: React (Vite) + Vanilla CSS (Custom dark theme)
- **Backend**: Python (FastAPI)
- **Machine Learning**: `scikit-learn` (TF-IDF), `sentence-transformers` (Embeddings), `FAISS` (Vector DB)
- **Data Parsing**: `pypdf`, `python-docx`

## 🚀 Getting Started

### 1. Backend Setup (FastAPI)

The backend handles all heavy lifting, including document extraction, NLP scoring, and vector database management.

```bash
cd server

# Create and activate a virtual environment
python -m venv venv
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```
*The server will start at `http://127.0.0.1:8000`*

### 2. Frontend Setup (React)

The frontend provides the graphical interface to upload files and explore the ranked candidates.

```bash
cd client

# Install dependencies
npm install

# Set environment variables
echo "VITE_BACKEND_URL=http://127.0.0.1:8000" > .env

# Start the dev server
npm run dev
```
*The frontend will be available at `http://localhost:5173`*

## 📁 Project Structure

```text
📦 RedRobProj
 ┣ 📂 client/               # React Frontend (Vite)
 ┃ ┣ 📂 src/
 ┃ ┃ ┣ 📂 components/     # DropZone, CandidateModal, icons
 ┃ ┃ ┣ 📂 context/        # AppContext for state management
 ┃ ┃ ┗ 📜 App.jsx         # Main UI layout and table
 ┃ ┗ 📜 .env              # VITE_BACKEND_URL configuration
 ┣ 📂 server/               # Python Backend (FastAPI)
 ┃ ┣ 📂 controller/       # API Logic
 ┃ ┃ ┣ 📂 utils/          # Embedding, Scoring, Honeypot, VectorDB, Extractors
 ┃ ┃ ┗ 📜 rank.py         # Main pipeline (Extract -> Score -> Clean -> Embed)
 ┃ ┣ 📜 main.py           # FastAPI server entry point
 ┃ ┗ 📜 requirements.txt  # Python ML dependencies
 ┗ 📂 Validation/           # Output validation and hackathon submission scripts
```

## 🧠 How the Pipeline Works

1. **Extraction**: `pdfWordFileExtractor.py` parses the JD (PDF/DOCX) and the candidate dataset (JSONL).
2. **Scoring**: `scoring.py` evaluates every candidate using TF-IDF text matching, direct skill matching, and experience thresholds to generate a final score.
3. **Cleaning**: `honeypotPenalty.py` reviews the top-scoring candidates to apply penalties to suspicious profiles and filters them out.
4. **Embedding**: The cleaned Top-100 candidates and the JD are embedded using `sentence-transformers` (`embedding.py`).
5. **Persistence**: Embeddings and metadata are saved to a local FAISS VectorDB (`vectorDB.py`).
6. **Delivery**: The JSON payload with scores, rankings, and reasoning is returned to the React frontend for display.
