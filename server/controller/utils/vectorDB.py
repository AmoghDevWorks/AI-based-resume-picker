import json
import os
import pickle
import math
from collections import defaultdict, Counter
import numpy as np
import multiprocessing as mp
import re

from .embedding import get_embedding, load_model

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dataset", "cache")
EMBEDDING_CACHE_FILE = os.path.join(CACHE_DIR, "candidate_embeddings.pkl")
FEATURES_CACHE_FILE = os.path.join(CACHE_DIR, "candidate_features.pkl")
BM25_CACHE_FILE = os.path.join(CACHE_DIR, "bm25_index.pkl")

# BM25 Parameters
K1 = 1.5
B = 0.75

def preprocess_text(text):
    if not text:
        return []
    # simple tokenization: lowercase, remove non-alphanumeric, split by space
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text.split()

class BM25Index:
    def __init__(self):
        self.doc_freqs = defaultdict(int)
        self.doc_lengths = []
        self.avgdl = 0
        self.N = 0
        self.inverted_index = defaultdict(list)
        
    def fit(self, corpus_tokens):
        self.N = len(corpus_tokens)
        total_length = 0
        
        for doc_id, tokens in enumerate(corpus_tokens):
            self.doc_lengths.append(len(tokens))
            total_length += len(tokens)
            
            term_counts = Counter(tokens)
            for term, count in term_counts.items():
                self.inverted_index[term].append((doc_id, count))
                self.doc_freqs[term] += 1
                
        self.avgdl = total_length / self.N if self.N > 0 else 1.0

    def get_scores(self, query_tokens):
        scores = np.zeros(self.N)
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            
            df = self.doc_freqs[term]
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            
            for doc_id, tf in self.inverted_index[term]:
                doc_len = self.doc_lengths[doc_id]
                numerator = tf * (K1 + 1)
                denominator = tf + K1 * (1 - B + B * doc_len / self.avgdl)
                scores[doc_id] += idf * (numerator / denominator)
                
        return scores

def extract_candidate_text(candidate):
    """Extract semantic text for dense embedding."""
    profile = candidate.get("profile", {})
    headline = profile.get("headline", "")
    summary = profile.get("summary", "")
    skills = " ".join([s.get("name", "") for s in candidate.get("skills", [])])
    return f"{headline}. {summary}. Skills: {skills}"

def extract_features(candidate):
    """Extract lightweight features for Stage 2 processing."""
    profile = candidate.get("profile", {})
    
    # Impute years of experience if missing
    yoe = profile.get("years_of_experience")
    if yoe is None:
        yoe = 0
        for job in candidate.get("career_history", []):
            yoe += job.get("duration_months", 0) / 12.0
            
    return {
        "candidate_id": candidate.get("candidate_id"),
        "profile": profile,
        "skills": candidate.get("skills", []),
        "career_history": candidate.get("career_history", []),
        "redrob_signals": candidate.get("redrob_signals", {}),
        "imputed_yoe": yoe
    }

def process_chunk(candidates_chunk):
    # Load model in the worker process
    load_model(offline_mode=True)
    embeddings = []
    features = []
    texts_for_bm25 = []
    
    for cand in candidates_chunk:
        text = extract_candidate_text(cand)
        emb = get_embedding(text)
        feat = extract_features(cand)
        
        embeddings.append(emb)
        features.append(feat)
        texts_for_bm25.append(preprocess_text(text))
        
    return embeddings, features, texts_for_bm25

def build_offline_cache(jsonl_path):
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    chunk_size = 5000
    candidates_chunk = []
    
    all_embeddings = []
    all_features = []
    all_texts_for_bm25 = []
    
    print("Starting offline processing...")
    
    # We can use ProcessPoolExecutor for parallel processing
    from concurrent.futures import ProcessPoolExecutor
    
    futures = []
    with ProcessPoolExecutor() as executor:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                candidates_chunk.append(json.loads(line))
                
                if len(candidates_chunk) == chunk_size:
                    futures.append(executor.submit(process_chunk, candidates_chunk))
                    candidates_chunk = []
            
            if candidates_chunk:
                futures.append(executor.submit(process_chunk, candidates_chunk))
                
        for future in futures:
            emb, feat, txts = future.result()
            all_embeddings.extend(emb)
            all_features.extend(feat)
            all_texts_for_bm25.extend(txts)

    print(f"Processed {len(all_features)} candidates.")

    # Save features and embeddings
    all_embeddings = np.array(all_embeddings, dtype=np.float32)
    with open(EMBEDDING_CACHE_FILE, 'wb') as f:
        pickle.dump(all_embeddings, f)
        
    with open(FEATURES_CACHE_FILE, 'wb') as f:
        pickle.dump(all_features, f)
        
    # Build and save BM25
    bm25 = BM25Index()
    bm25.fit(all_texts_for_bm25)
    with open(BM25_CACHE_FILE, 'wb') as f:
        pickle.dump(bm25, f)
        
    print("Offline caching complete.")

# ---------------------------------------------------------
# ONLINE STAGE
# ---------------------------------------------------------

_embeddings_cache = None
_features_cache = None
_bm25_cache = None

def load_caches():
    global _embeddings_cache, _features_cache, _bm25_cache
    if _embeddings_cache is None:
        if not os.path.exists(EMBEDDING_CACHE_FILE):
            raise FileNotFoundError("Offline caches not found. Run vectorDB.py offline first.")
            
        with open(EMBEDDING_CACHE_FILE, 'rb') as f:
            _embeddings_cache = pickle.load(f)
            
        with open(FEATURES_CACHE_FILE, 'rb') as f:
            _features_cache = pickle.load(f)
            
        class CustomUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                if name == 'BM25Index':
                    return BM25Index
                return super().find_class(module, name)
                
        with open(BM25_CACHE_FILE, 'rb') as f:
            _bm25_cache = CustomUnpickler(f).load()

def compute_rrf(dense_ranks, sparse_ranks, k=60):
    """Compute Reciprocal Rank Fusion."""
    scores = defaultdict(float)
    
    for rank, doc_id in enumerate(dense_ranks):
        scores[doc_id] += 1.0 / (k + rank + 1)
        
    for rank, doc_id in enumerate(sparse_ranks):
        scores[doc_id] += 1.0 / (k + rank + 1)
        
    return scores

def retrieve_top_k(jd_text, top_k=1000):
    load_caches()
    
    # 1. Dense Retrieval
    jd_embedding = np.array(get_embedding(jd_text), dtype=np.float32)
    # Cosine similarity
    similarities = np.dot(_embeddings_cache, jd_embedding)
    dense_ranked_indices = np.argsort(similarities)[::-1]
    
    # 2. Sparse Retrieval
    jd_tokens = preprocess_text(jd_text)
    bm25_scores = _bm25_cache.get_scores(jd_tokens)
    sparse_ranked_indices = np.argsort(bm25_scores)[::-1]
    
    # 3. RRF
    rrf_scores = compute_rrf(dense_ranked_indices, sparse_ranked_indices)
    
    # Sort by RRF score
    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    top_indices = sorted_doc_ids[:top_k]
    
    top_candidates = []
    for idx in top_indices:
        feat = _features_cache[idx]
        feat['dense_score'] = float(similarities[idx])
        feat['sparse_score'] = float(bm25_scores[idx])
        feat['rrf_score'] = float(rrf_scores[idx])
        top_candidates.append(feat)
        
    return top_candidates

if __name__ == "__main__":
    # If run as a script, build the offline cache
    import sys
    if len(sys.argv) > 1:
        jsonl_path = sys.argv[1]
    else:
        jsonl_path = os.path.join(CACHE_DIR, "..", "India_runs_data_and_ai_challenge", "candidates.jsonl")
    
    build_offline_cache(jsonl_path)
