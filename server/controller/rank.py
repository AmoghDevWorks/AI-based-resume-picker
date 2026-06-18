import csv
import io
import os
import random
from fastapi import UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from concurrent.futures import ProcessPoolExecutor

from .utils.pdfWordFileExtractor import extract_text
from .utils.vectorDB import retrieve_top_k
from .services.matchers import (
    calculate_skill_match,
    calculate_experience_match,
    calculate_title_similarity,
    calculate_activity_score,
    calculate_stability_score,
    calculate_honeypot_penalty
)

def evaluate_candidate(args):
    feat, jd_skills, jd_years, jd_title = args
    
    # Run the heuristic feature services
    skill_score = calculate_skill_match(jd_skills, feat.get("skills", []))
    exp_score = calculate_experience_match(jd_years, feat.get("imputed_yoe", 0))
    title_score = calculate_title_similarity(jd_title, feat.get("profile", {}).get("current_title", ""))
    act_score = calculate_activity_score(feat.get("redrob_signals", {}))
    stab_score = calculate_stability_score(feat.get("career_history", []))
    
    # Retrieve RRF score from vectorDB
    rrf_score = feat.get("rrf_score", 0.0)
    
    # Ensemble weights
    # Normalize RRF locally if needed, but here we just multiply
    # We assume max RRF score is small, so we might need to scale it or just use it raw.
    # Actually, RRF is typically very small. Let's use dense_score (cosine) for the final score instead of raw RRF to keep it in [0, 1].
    cosine = feat.get("dense_score", 0.0)
    # Clamp cosine
    cosine = max(0.0, min(1.0, cosine))
    
    final_score = (0.40 * cosine) + (0.30 * skill_score) + (0.15 * exp_score) + (0.05 * title_score) + (0.05 * act_score) + (0.05 * stab_score)
    
    # Honeypot penalty
    penalty = calculate_honeypot_penalty(feat)
    final_score *= penalty
    
    feat['final_score'] = final_score
    feat['breakdown'] = {
        'cosine': cosine,
        'skill': skill_score,
        'exp': exp_score,
        'title': title_score,
        'act': act_score,
        'stab': stab_score
    }
    
    return feat

def generate_reasoning(feat, jd_skills):
    bd = feat.get('breakdown', {})
    yoe = round(feat.get('imputed_yoe', 0), 1)
    
    # Determine the strongest attribute
    highest = max(['cosine', 'skill', 'exp', 'title'], key=lambda k: bd[k])
    
    templates = []
    
    if highest == 'exp':
        templates.append(f"Highly qualified with {yoe} years of relevant experience, perfectly matching the role requirements.")
        templates.append(f"Candidate possesses a strong tenure of {yoe} years, showing excellent stability and domain expertise.")
    elif highest == 'skill':
        templates.append(f"Exceptional technical alignment. Demonstrated strong overlap with required skills and steady career growth.")
        templates.append(f"Strong match on core competencies. The candidate's skill profile closely mirrors the technical demands of the job.")
    elif highest == 'title':
        templates.append(f"Direct role match. The candidate currently holds a highly relevant title with {yoe} years of overall experience.")
        templates.append(f"Proven track record in a similar role. Strong alignment in both title and responsibilities.")
    else:
        templates.append(f"Excellent holistic match. Strong semantic alignment with the job description across experience and skills.")
        templates.append(f"Highly relevant background based on profile summary and headline, complemented by {yoe} years of experience.")
        
    return random.choice(templates)


async def rank_candidates(jd: UploadFile, candidates: UploadFile, top_k: int):
    # 1. Parse JD
    jd_text = await extract_text(jd)
    
    # Simple extraction for JD criteria (in a real system, use an NLP parser or regex, here we mock it based on text keywords)
    # We will just pass the raw JD text to the retrieval.
    # For skills, we would extract from JD text. We will just hardcode some for demonstration or use simple regex.
    # Let's extract words starting with capital letters as a rough heuristic for now, or just pass empty.
    import re
    jd_words = re.findall(r'\b[A-Z][a-z0-9]+\b', jd_text)
    jd_skills = list(set([w.lower() for w in jd_words if len(w) > 3]))[:10] # Rough heuristic
    
    # Extract years of experience (look for "X years")
    jd_years = 5 # default fallback
    yoe_match = re.search(r'(\d+)\+?\s*(?:-\s*\d+\s*)?years?', jd_text, re.IGNORECASE)
    if yoe_match:
        jd_years = int(yoe_match.group(1))
        
    jd_title = "Engineer" # fallback
    
    # 2. Stage 1: Retrieval (Hybrid Search)
    top_candidates = retrieve_top_k(jd_text, top_k=1000)
    
    # 3. Stage 2: Deep Scoring (Parallel execution)
    args_list = [(feat, jd_skills, jd_years, jd_title) for feat in top_candidates]
    
    scored_candidates = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        for result in executor.map(evaluate_candidate, args_list):
            scored_candidates.append(result)
            
    # 4. Tie-breaking and Sorting
    # Primary: round(final_score, 4) (DESC)
    # Secondary: candidate_id (ASC)
    scored_candidates.sort(key=lambda x: (-round(x['final_score'], 4), x['candidate_id']))
    
    # 5. Take top 100
    final_100 = scored_candidates[:100]
    
    # 6. Generate CSV and JSON payload
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    
    json_results = []
    
    for rank_idx, feat in enumerate(final_100, start=1):
        cid = feat['candidate_id']
        score = feat['final_score']
        reasoning = generate_reasoning(feat, jd_skills)
        
        writer.writerow([cid, rank_idx, round(score, 4), reasoning])
        
        json_results.append({
            "candidate_id": cid,
            "rank": rank_idx,
            "score": round(score, 4),
            "reasoning": reasoning,
            "profile": feat.get("profile", {})
        })
        
    csv_content = csv_buffer.getvalue()
    
    # In a real API we might return StreamingResponse or JSONResponse. 
    # Since we need to support the frontend beautifully, let's return JSON containing both the data and the CSV string.
    return {
        "message": "Ranking successful",
        "results": json_results,
        "csv_data": csv_content
    }