import re
import math

def normalize_skill(skill):
    if not skill:
        return ""
    # Remove punctuation, convert to lowercase, handle common aliases
    skill = skill.lower()
    skill = re.sub(r'[^a-z0-9]', '', skill)
    # Simple aliases
    aliases = {
        'reactjs': 'react',
        'nodejs': 'node',
        'vuejs': 'vue',
        'tensorflow': 'tf',
        'machinelearning': 'ml',
        'artificialintelligence': 'ai'
    }
    return aliases.get(skill, skill)

def calculate_skill_match(jd_skills, candidate_skills):
    if not jd_skills:
        return 1.0 # If no skills required, it's a match
        
    jd_norm = set(normalize_skill(s) for s in jd_skills)
    if not jd_norm:
        return 1.0
        
    cand_norm = set(normalize_skill(s.get('name', '')) for s in candidate_skills)
    
    # Intersection over union (Jaccard) or just recall
    # We care more about recall (how many of JD skills candidate has)
    intersection = jd_norm.intersection(cand_norm)
    score = len(intersection) / len(jd_norm)
    
    # Boost slightly if proficiency is advanced/expert
    prof_boost = 0.0
    for s in candidate_skills:
        n = normalize_skill(s.get('name', ''))
        if n in jd_norm:
            prof = s.get('proficiency', 'intermediate').lower()
            if prof == 'expert':
                prof_boost += 0.05
            elif prof == 'advanced':
                prof_boost += 0.02
                
    return min(1.0, score + (prof_boost / len(jd_norm)))

def calculate_experience_match(jd_years, candidate_years):
    if jd_years is None or jd_years <= 0:
        return 1.0
        
    # Gaussian decay
    # If candidate_years == jd_years, score = 1.0
    # If candidate_years < jd_years, steep drop
    # If candidate_years > jd_years, slow drop
    
    diff = candidate_years - jd_years
    
    if diff >= 0:
        # Over-qualified: sigma is larger so decay is slower
        sigma = jd_years * 2.0  # Just an arbitrary curve
        score = math.exp(-(diff ** 2) / (2 * sigma ** 2))
    else:
        # Under-qualified: steeper decay
        sigma = max(1.0, jd_years / 2.0)
        score = math.exp(-(diff ** 2) / (2 * sigma ** 2))
        
    return max(0.0, min(1.0, score))

def calculate_title_similarity(jd_title, candidate_title):
    if not jd_title or not candidate_title:
        return 0.5
        
    jd_norm = jd_title.lower().strip()
    cand_norm = candidate_title.lower().strip()
    
    if jd_norm == cand_norm:
        return 1.0
        
    jd_words = set(re.findall(r'\w+', jd_norm))
    cand_words = set(re.findall(r'\w+', cand_norm))
    
    if not jd_words or not cand_words:
        return 0.5
        
    intersection = jd_words.intersection(cand_words)
    return len(intersection) / max(len(jd_words), len(cand_words))

def calculate_activity_score(signals):
    if not signals:
        return 0.0
        
    # Example components:
    # 1. profile completeness
    comp = signals.get('profile_completeness_score', 50) / 100.0
    
    # 2. recruiter response rate
    resp = signals.get('recruiter_response_rate', 0.5)
    
    # 3. github activity
    gh = signals.get('github_activity_score', -1)
    gh_score = (gh / 100.0) if gh >= 0 else 0.5
    
    return (comp + resp + gh_score) / 3.0

def calculate_stability_score(career_history):
    if not career_history:
        return 0.5
        
    total_months = sum(job.get('duration_months', 0) for job in career_history)
    avg_tenure = total_months / len(career_history)
    
    # If avg tenure > 24 months, perfect stability
    # If < 6 months, poor stability
    
    if avg_tenure >= 24:
        return 1.0
    elif avg_tenure <= 6:
        return 0.0
    else:
        return (avg_tenure - 6) / 18.0

def calculate_honeypot_penalty(candidate):
    """
    Check for impossible or contradictory information.
    Returns 0.0 if honeypot, else 1.0.
    """
    profile = candidate.get('profile', {})
    yoe = profile.get('years_of_experience', 0)
    
    history = candidate.get('career_history', [])
    total_months = sum(job.get('duration_months', 0) for job in history)
    
    # Impossible timeline check
    if yoe > 0 and total_months > (yoe * 12) + 24: # 2 year grace period for overlapping roles
        return 0.0
        
    # Contradictory skills check
    skills = candidate.get('skills', [])
    expert_skills_0_duration = sum(1 for s in skills if s.get('proficiency', '').lower() == 'expert' and s.get('duration_months', 1) == 0)
    
    if expert_skills_0_duration > 5:
        return 0.0
        
    # Contradictory dates (e.g. start year > end year in education)
    edu = candidate.get('education', [])
    for e in edu:
        sy = e.get('start_year')
        ey = e.get('end_year')
        if sy and ey and sy > ey:
            return 0.0

    return 1.0
