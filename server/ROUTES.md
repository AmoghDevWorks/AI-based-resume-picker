# API Routes

Base URL

```text
http://localhost:8000
```

---

# Health Check

## GET /

Check whether the API is running.

### Response

```json
{
    "message": "Redrob Candidate Ranking System API"
}
```

---

# Ranking

Base:

```text
/ranking
```

---

## POST /ranking

Run complete ranking pipeline.

### Inputs

* jd_file
* candidates_file
* top_k

### Output

```json
{
    "top_k": 100,
    "num_results": 100,
    "results": [...]
}
```

---

## POST /ranking/reasoning

Generate explanations for already ranked candidates.

### Input

```json
{
    "candidate_ids": [...]
}
```

### Output

```json
{
    "results": [...]
}
```

---

## GET /ranking/top

Get the top ranked candidates from the latest run.

### Query Parameters

```text
top_k=100
```

---

## GET /ranking/candidate/{candidate_id}

Get ranking information for a specific candidate.

### Output

```json
{
    "candidate_id": "...",
    "score": 0.91,
    "reasoning": "..."
}
```

---

## GET /ranking/features/{candidate_id}

Get feature breakdown.

### Output

```json
{
    "semantic_similarity": ...,
    "skill_overlap": ...,
    "career_stability": ...,
    "activity_score": ...,
    "consistency_score": ...,
    "honeypot_penalty": ...
}
```

---

## GET /ranking/score/{candidate_id}

Get final score for a candidate.

### Output

```json
{
    "candidate_id": "...",
    "score": 0.91
}
```

---

## POST /ranking/export

Generate submission CSV.

### Output

```json
{
    "path": "output/submission.csv"
}
```

---

# Documentation

Swagger

```text
http://localhost:8000/docs
```

ReDoc

```text
http://localhost:8000/redoc
```
