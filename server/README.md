# Redrob Candidate Ranking System

## Inputs

1. Job Description File (`pdf`, `docx`, `txt`)
2. `candidates.jsonl`
3. `top_k`

---

# Architecture

```text
JD File
↓
Document Service
↓
JD Text
↓
Retrieval Service

(Dense Retrieval + BM25)

↓
Top 500 Candidates
↓
Feature Engineering
↓
Scoring Service
↓
Ranking Service
↓
Reasoning Service
↓
Top K Candidates
↓
submission.csv
```

---

# Folder Structure

```text
server/

├── api/
│   ├── routes/
│   │   └── ranking.py
│   └── main.py
│
├── models/
│   ├── candidate.py
│   ├── ranking.py
│   └── response.py
│
├── services/
│   ├── document_service.py
│   ├── embedding_service.py
│   ├── vector_service.py
│   ├── bm25_service.py
│   ├── retrieval_service.py
│   ├── skill_service.py
│   ├── career_service.py
│   ├── activity_service.py
│   ├── consistency_service.py
│   ├── honeypot_service.py
│   ├── feature_engineering_service.py
│   ├── scoring_service.py
│   ├── reasoning_service.py
│   └── ranking_service.py
│
├── repositories/
│   ├── candidate_repository.py
│   ├── embedding_repository.py
│   └── feature_repository.py
│
├── artifacts/
│   ├── candidate_embeddings.npy
│   ├── faiss_index.bin
│   ├── bm25_corpus.pkl
│   ├── feature_table.parquet
│   └── lightgbm_ranker.pkl
│
├── output/
│   └── submission.csv
│
└── rank.py
```

---

# Core Services

### Document Service

* Parse PDF
* Parse DOCX
* Parse TXT
* Extract JD text

### Embedding Service

Models:

* BGE-small
* all-MiniLM-L6-v2
* E5-small

### Retrieval Service

Hybrid Retrieval:

```text
Dense Retrieval + BM25
```

Returns:

```text
Top 500 candidates
```

### Skill Service

* Skill overlap
* Skill duration
* Proficiency score
* Endorsement score

### Career Service

* Career progression
* Average tenure
* Stability score

### Activity Service

Uses:

* recruiter_response_rate
* interview_completion_rate
* profile_views_received_30d
* search_appearance_30d
* saved_by_recruiters_30d

### Consistency Service

Detects:

* Salary anomalies
* Timeline anomalies
* Education inconsistencies

Produces:

```text
Consistency Score
```

### Honeypot Service

Detects:

* Impossible timelines
* Contradictory experience
* Unrealistic skill claims

Produces:

```text
Honeypot Penalty
```

### Feature Engineering Service

Features:

* Semantic similarity
* Skill overlap
* Experience match
* Title similarity
* Career stability
* Activity score
* Consistency score
* Honeypot penalty

### Scoring Service

```python
score = (
    0.35 * semantic_similarity
    + 0.20 * skill_overlap
    + 0.15 * experience_match
    + 0.10 * activity_score
    + 0.10 * career_stability
    + 0.10 * consistency_score
)

score -= honeypot_penalty
```

### Ranking Service

Pipeline:

```text
Read JD
↓
Load candidates.jsonl
↓
Retrieve Top 500
↓
Build Features
↓
Compute Scores
↓
Sort
↓
Top K
↓
Generate Explanations
```

### Reasoning Service

Models:

* Ollama
* Qwen
* Llama

Produces:

```text
1-2 sentence explanations
```

---

# API

## POST /ranking

Inputs:

* JD file
* candidates.jsonl
* top_k

Returns:

```json
{
  "top_candidates": [...]
}
```

---

# Run API

```bash
python -m uvicorn api.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

# Batch Execution

```python
results = ranking_service.rank(
    jd_path,
    candidates_path,
    top_k
)
```

---

# Generate Submission

```bash
python rank.py
```

Output:

```text
output/submission.csv
```
