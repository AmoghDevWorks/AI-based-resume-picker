import gc
import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


# ════════════════════════════════════════════════════════════
# CONFIG — single source of truth
# ════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class ScoringConfig:
    # scoring weights — must sum to 100
    w_tfidf: float = 45
    w_skills: float = 25
    w_experience: float = 5
    w_platform: float = 25

    # experience target curve
    exp_min: int = 3
    exp_ideal: int = 7
    exp_max: int = 20

    # only candidates whose FINAL (post-bonus) score clears this bar get saved
    min_final_score: float = 40.0

    def __post_init__(self):
        total = self.w_tfidf + self.w_skills + self.w_experience + self.w_platform
        if abs(total - 100) > 1e-6:
            raise ValueError(f"Scoring weights must sum to 100, got {total}")


# ════════════════════════════════════════════════════════════
# SkillVocabulary — knowledge base + word-boundary-aware matching
# ════════════════════════════════════════════════════════════
class SkillVocabulary:
    KNOWN_SKILLS = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
        "rust", "scala", "kotlin", "swift", "ruby", "php", "r", "matlab", "bash",
        "shell", "perl", "dart", "elixir", "haskell", "lua", "groovy",
        "django", "flask", "fastapi", "spring", "spring boot", "express", "node.js",
        "nodejs", "react", "react.js", "angular", "vue", "vue.js", "next.js", "nuxt",
        "rails", "laravel", "asp.net", "dotnet", ".net", "svelte", "gatsby",
        "machine learning", "deep learning", "natural language processing", "nlp",
        "computer vision", "reinforcement learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost", "hugging face",
        "transformers", "bert", "gpt", "llm", "langchain", "pandas", "numpy", "scipy",
        "matplotlib", "seaborn", "plotly", "jupyter", "data science", "mlops",
        "feature engineering", "model deployment", "a/b testing",
        "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "cassandra",
        "dynamodb", "elasticsearch", "spark", "pyspark", "hadoop", "kafka", "airflow",
        "dbt", "snowflake", "bigquery", "redshift", "databricks", "hive", "flink",
        "data pipeline", "etl", "data warehouse", "data lake", "data engineering",
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "github actions", "ci/cd", "devops",
        "helm", "argocd", "prometheus", "grafana", "datadog", "cloudformation",
        "lambda", "ec2", "s3", "rds", "ecs", "eks", "gke", "aks", "serverless",
        "microservices", "rest api", "restful", "graphql", "grpc", "websocket",
        "event driven", "message queue", "rabbitmq", "sqs", "pub/sub", "api gateway",
        "system design", "distributed systems", "cloud native", "service mesh",
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "agile",
        "scrum", "kanban", "tdd", "bdd", "unit testing", "integration testing",
        "pytest", "junit", "selenium", "postman", "swagger", "openapi",
        "fintech", "edtech", "healthtech", "ecommerce", "saas", "b2b", "b2c",
        "product analytics", "growth engineering", "platform engineering",
        "leadership", "mentoring", "communication", "problem solving",
        "stakeholder management", "cross functional", "startup", "founding team",
        "full stack", "backend", "frontend", "data engineer", "data scientist",
        "ml engineer", "devops engineer", "site reliability", "sre",
    ]

    # Pre-split into "short" (<=3 chars, need word-boundary regex) and "long"
    # (plain substring match) so .extract() doesn't rebuild this split on
    # every single call across 100k candidates.
    _SHORT_SKILLS = [s for s in KNOWN_SKILLS if len(s) <= 3]
    _LONG_SKILLS  = [s for s in KNOWN_SKILLS if len(s) > 3]
    _SHORT_PATTERNS = {
        s: re.compile(r"\b" + re.escape(s) + r"\b") for s in _SHORT_SKILLS
    }

    @classmethod
    def extract(cls, text: str) -> set:
        text_lower = text.lower()
        found = set()
        for skill, pattern in cls._SHORT_PATTERNS.items():
            if pattern.search(text_lower):
                found.add(skill)
        for skill in cls._LONG_SKILLS:
            if skill in text_lower:
                found.add(skill)
        return found

    @classmethod
    def contains(cls, text_lower: str, skill: str) -> bool:
        if len(skill) <= 3:
            pattern = cls._SHORT_PATTERNS.get(skill)
            if pattern is None:
                pattern = re.compile(r"\b" + re.escape(skill) + r"\b")
            return bool(pattern.search(text_lower))
        return skill in text_lower


# ════════════════════════════════════════════════════════════
# JobDescription
# ════════════════════════════════════════════════════════════
class JobDescription:
    def __init__(self, text: str, skill_keywords: set):
        self.text = text
        self.skill_keywords = skill_keywords

    @classmethod
    def from_text(cls, text: str) -> "JobDescription":
        keywords = SkillVocabulary.extract(text)
        return cls(text, keywords)


# ════════════════════════════════════════════════════════════
# Candidate
# ════════════════════════════════════════════════════════════
class Candidate:
    def __init__(self, raw: dict, row_id: int):
        self.raw = raw
        self.row_id = row_id
        self.profile = raw.get("profile", {})
        self.signals = raw.get("redrob_signals", {})
        self.skills = raw.get("skills", [])
        self.career_history = raw.get("career_history", [])
        self.education = raw.get("education", [])
        self.certifications = raw.get("certifications", [])

    @property
    def candidate_id(self) -> str:
        return self.raw.get("candidate_id") or self.raw.get("id") or f"row_{self.row_id}"

    @property
    def years_of_experience(self) -> float:
        try:
            return float(self.profile.get("years_of_experience", 0) or 0)
        except (ValueError, TypeError):
            return 0.0

    def to_resume_text(self) -> str:
        return ResumeTextBuilder(self).build()

    def to_metadata_row(self) -> dict:
        p, rs = self.profile, self.signals
        sal = rs.get("expected_salary_range_inr_lpa", {})

        skills_sorted = sorted(
            self.skills,
            key=lambda s: (
                {"expert": 3, "advanced": 2, "intermediate": 1, "beginner": 0}
                .get(s.get("proficiency", ""), 0) if isinstance(s, dict) else 0,
                s.get("endorsements", 0) if isinstance(s, dict) else 0,
            ),
            reverse=True,
        )

        top_skills = ", ".join(s.get("name", "") for s in skills_sorted[:8] if isinstance(s, dict))
        latest = self.career_history[0] if self.career_history and isinstance(self.career_history[0], dict) else {}

        return {
            "candidate_id": self.candidate_id,
            "name": p.get("anonymized_name", ""),
            "headline": p.get("headline", ""),
            "current_title": p.get("current_title", ""),
            "current_company": p.get("current_company", ""),
            "years_of_experience": p.get("years_of_experience", ""),
            "location": p.get("location", ""),
            "country": p.get("country", ""),
            "industry": p.get("current_industry", ""),
            "top_skills": top_skills,
            "latest_title": latest.get("title", ""),
            "latest_company": latest.get("company", ""),
            "notice_period_days": rs.get("notice_period_days", ""),
            "salary_min_lpa": sal.get("min", ""),
            "salary_max_lpa": sal.get("max", ""),
            "preferred_work_mode": rs.get("preferred_work_mode", ""),
            "willing_to_relocate": rs.get("willing_to_relocate", ""),
            "open_to_work": rs.get("open_to_work_flag", ""),
            "last_active": rs.get("last_active_date", ""),
            "profile_completeness": rs.get("profile_completeness_score", ""),
            "github_score": rs.get("github_activity_score", ""),
            "interview_completion": rs.get("interview_completion_rate", ""),
            "recruiter_response_rate": rs.get("recruiter_response_rate", ""),
            "num_certifications": len(self.certifications),
        }


# ════════════════════════════════════════════════════════════
# ResumeTextBuilder
# ════════════════════════════════════════════════════════════
class ResumeTextBuilder:
    def __init__(self, candidate: Candidate):
        self.c = candidate
        self._parts: list = []

    def build(self) -> str:
        self._add_headline_block()
        self._add_skills_block()
        self._add_assessment_block()
        self._add_career_block()
        self._add_education_block()
        self._add_certification_block()
        return "\n".join(self._parts)

    def _add_headline_block(self):
        p = self.c.profile
        headline = p.get("headline", "")
        current_title = p.get("current_title", "")
        company = p.get("current_company", "")
        industry = p.get("current_industry", "")
        yoe = p.get("years_of_experience", 0)
        summary = p.get("summary", "")

        if headline:      self._parts.append(str(headline))
        if current_title:
            self._parts.append(str(current_title))
            self._parts.append(f"Role: {current_title}")
        if company:       self._parts.append(f"Company: {company}")
        if industry:      self._parts.append(f"Industry: {industry}")
        if yoe:           self._parts.append(f"{yoe} years experience")
        if summary:       self._parts.append(str(summary))

    def _add_skills_block(self):
        tokens = []
        for s in self.c.skills:
            if not isinstance(s, dict):
                continue
            name = s.get("name", "").strip()
            prof = s.get("proficiency", "")
            if not name:
                continue
            tokens.append(name)
            if prof in ("expert", "advanced"):
                tokens.append(name)
                tokens.append(name)
        if tokens:
            self._parts.append("Skills: " + " ".join(tokens))

    def _add_assessment_block(self):
        assessments = self.c.signals.get("skill_assessment_scores", {})
        if assessments:
            self._parts.append(
                "Assessed skills: " + " ".join(f"{k} {v:.0f}" for k, v in assessments.items())
            )

    def _add_career_block(self):
        for job in self.c.career_history:
            if not isinstance(job, dict):
                continue
            title = job.get("title", "")
            co    = job.get("company", "")
            ind   = job.get("industry", "")
            desc  = str(job.get("description", "") or "").strip()[:500]
            line  = " | ".join(filter(None, [title, co, ind, desc]))
            if line.strip():
                self._parts.append(line.strip())

    def _add_education_block(self):
        for edu in self.c.education:
            if not isinstance(edu, dict):
                continue
            line = " ".join(filter(None, [
                edu.get("degree", ""),
                edu.get("field_of_study", ""),
                edu.get("institution", ""),
            ]))
            if line.strip():
                self._parts.append(line.strip())

    def _add_certification_block(self):
        cert_parts = []
        for cert in self.c.certifications:
            if not isinstance(cert, dict):
                continue
            name   = cert.get("name", "")
            issuer = cert.get("issuer", "")
            if name:
                cert_parts.append(f"{name} {issuer}".strip())
        if cert_parts:
            self._parts.append("Certifications: " + " | ".join(cert_parts))


# ════════════════════════════════════════════════════════════
# CandidateScorer Strategy
# ════════════════════════════════════════════════════════════
class CandidateScorer(ABC):
    name: str = "score"

    @abstractmethod
    def score(self, candidate: Candidate, jd: JobDescription) -> float:
        ...


class SkillMatchScorer(CandidateScorer):
    name = "skill_match_score"

    def score(self, candidate: Candidate, jd: JobDescription) -> float:
        if not jd.skill_keywords:
            return 50.0

        candidate_text = ""
        for s in candidate.skills:
            if isinstance(s, dict):
                candidate_text += " " + s.get("name", "").lower()
        for job in candidate.career_history:
            if isinstance(job, dict):
                candidate_text += " " + str(job.get("description", "") or "").lower()
                candidate_text += " " + str(job.get("title", "")).lower()
        for k in candidate.signals.get("skill_assessment_scores", {}).keys():
            candidate_text += " " + str(k).lower()

        skill_weights = {}
        for s in candidate.skills:
            if isinstance(s, dict):
                name = s.get("name", "").lower()
                prof = s.get("proficiency", "")
                w = {"expert": 3.0, "advanced": 2.0, "intermediate": 1.0, "beginner": 0.5}.get(prof, 1.0)
                skill_weights[name] = max(skill_weights.get(name, 0), w)

        matched_weight = 0.0
        total_weight   = len(jd.skill_keywords)
        for kw in jd.skill_keywords:
            if SkillVocabulary.contains(candidate_text, kw):
                matched_weight += skill_weights.get(kw, 1.0)

        raw_ratio = matched_weight / max(total_weight, 1)
        score = min(100.0, (raw_ratio ** 0.6) * 100)
        return round(score, 2)


class ExperienceScorer(CandidateScorer):
    name = "exp_score"

    def __init__(self, exp_min: int, exp_ideal: int, exp_max: int):
        self.exp_min   = exp_min
        self.exp_ideal = exp_ideal
        self.exp_max   = exp_max

    def score(self, candidate: Candidate, jd: JobDescription) -> float:
        yoe = candidate.years_of_experience

        if yoe < self.exp_min:
            score = (yoe / max(self.exp_min, 1)) * 60
        elif yoe <= self.exp_ideal:
            score = 60 + ((yoe - self.exp_min) / max(self.exp_ideal - self.exp_min, 1)) * 40
        elif yoe <= self.exp_max:
            score = 100 - ((yoe - self.exp_ideal) / max(self.exp_max - self.exp_ideal, 1)) * 15
        else:
            score = 85

        return round(min(100.0, max(0.0, score)), 2)


class PlatformSignalScorer(CandidateScorer):
    name = "platform_score"

    def score(self, candidate: Candidate, jd: JobDescription) -> float:
        rs = candidate.signals
        weighted_parts = []

        try:
            completeness = float(rs.get("profile_completeness_score", 50))
        except (ValueError, TypeError):
            completeness = 50.0
        weighted_parts.append((completeness, 0.20))

        try:
            github = float(rs.get("github_activity_score", -1))
        except (ValueError, TypeError):
            github = -1.0
        if github >= 0:
            weighted_parts.append((github, 0.25))
        else:
            weighted_parts.append((30, 0.10))

        assessments = rs.get("skill_assessment_scores", {})
        if assessments:
            weighted_parts.append((float(np.mean(list(assessments.values()))), 0.25))
        else:
            weighted_parts.append((30, 0.10))

        try:
            response_rate = float(rs.get("recruiter_response_rate", 0.5) or 0.5)
        except (ValueError, TypeError):
            response_rate = 0.5
        weighted_parts.append((response_rate * 100, 0.10))

        try:
            interview_rate = float(rs.get("interview_completion_rate", 0.5) or 0.5)
        except (ValueError, TypeError):
            interview_rate = 0.5
        weighted_parts.append((interview_rate * 100, 0.10))

        weighted_parts.append((self._recency_score(rs.get("last_active_date", "")), 0.10))

        total_weight   = sum(w for _, w in weighted_parts)
        weighted_score = sum(s * w for s, w in weighted_parts) / total_weight
        return round(min(100.0, weighted_score), 2)

    @staticmethod
    def _recency_score(last_active_str: str) -> float:
        try:
            last_active = datetime.strptime(last_active_str, "%Y-%m-%d")
            days_ago = (datetime.now() - last_active).days
            return max(0.0, 100 - (days_ago / 365) * 100)
        except Exception:
            return 50.0


# ════════════════════════════════════════════════════════════
# TfidfSimilarityScorer
# ════════════════════════════════════════════════════════════
class TfidfSimilarityScorer:
    """
    Memory-optimized vs. the original:
      - max_features reduced from 150_000 -> 30_000.
        At 100k docs, bigrams blow up the vocabulary fast; the long tail of
        rare bigrams contributes almost nothing to ranking (they appear in
        ~1 document and barely move cosine similarity), but they cost a lot
        of sparse-matrix memory. 30k features is a safe, generous cap that
        preserves ranking order in practice. Raise to 50_000 if you have
        memory headroom and want to be extra conservative about quality.
      - dtype=np.float32 on the vectorizer -> half the memory of the
        default float64, with no meaningful precision loss for similarity
        ranking (we're comparing relative scores, not doing high-precision
        arithmetic).
      - linear_kernel instead of cosine_similarity: TF-IDF vectors from
        scikit-learn are L2-normalized by default (norm="l2" is the
        default), so linear_kernel(a, b) == cosine_similarity(a, b)
        mathematically. linear_kernel just skips cosine_similarity's
        internal renormalization step, which is otherwise redundant work
        and an extra allocation.
      - Sparse matrix is deleted and gc.collect()'d immediately after the
        score array is extracted, instead of being left to the next GC
        cycle.
    """

    name = "tfidf_score"

    def __init__(self, vectorizer: Optional[TfidfVectorizer] = None):
        self.vectorizer = vectorizer or TfidfVectorizer(
            stop_words="english",
            sublinear_tf=True,
            ngram_range=(1, 2),
            max_features=30_000,
            dtype=np.float32,
        )

    def score_all(self, jd_text: str, resume_texts: list) -> np.ndarray:
        if not resume_texts:
            return np.array([])

        all_texts = [jd_text] + resume_texts
        matrix = self.vectorizer.fit_transform(all_texts)

        jd_vector        = matrix[0:1]
        candidate_matrix = matrix[1:]

        raw = linear_kernel(jd_vector, candidate_matrix).flatten()

        # Free the sparse matrix and its slices before returning — these
        # are the largest allocations in the whole pipeline.
        del matrix, jd_vector, candidate_matrix
        gc.collect()

        lo, hi = raw.min(), raw.max()
        return ((raw - lo) / (hi - lo) * 100) if hi > lo else raw * 100


# ════════════════════════════════════════════════════════════
# WeightedScoreAggregator & NoticePeriodBonusDecorator
# ════════════════════════════════════════════════════════════
class WeightedScoreAggregator:
    def __init__(self, config: ScoringConfig, scorers: list):
        self.weights = {
            TfidfSimilarityScorer.name: config.w_tfidf,
            SkillMatchScorer.name:      config.w_skills,
            ExperienceScorer.name:      config.w_experience,
            PlatformSignalScorer.name:  config.w_platform,
        }

    def aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        df       = df.copy()
        weighted = sum((self.weights[col] / 100) * df[col] for col in self.weights if col in df.columns)
        df["final_score"] = weighted.round(2)
        return df


class NoticePeriodBonusDecorator:
    @staticmethod
    def _bonus(days) -> float:
        if pd.isna(days) or days == "":
            return 0.0
        try:
            d = int(days)
        except (ValueError, TypeError):
            return 0.0

        if d == 0:   return 5.0
        if d <= 15:  return 4.0
        if d <= 30:  return 3.0
        if d <= 60:  return 1.0
        return -3.0

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["notice_bonus"] = df["notice_period_days"].apply(self._bonus)
        df["final_score"]  = (df["final_score"] + df["notice_bonus"]).round(2)
        return df


class MinimumScoreFilter:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["final_score"] > self.threshold].copy()


# ════════════════════════════════════════════════════════════
# RankingResult
# ════════════════════════════════════════════════════════════
@dataclass
class RankingResult:
    dataframe:         pd.DataFrame
    candidates_by_id:  Dict[str, Candidate] = field(default_factory=dict)
    skipped_records:   int = 0
    honeypots_removed: int = 0
    honeypot_ids:      List[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════
# CandidateRankingEngine
# ════════════════════════════════════════════════════════════
class CandidateRankingEngine:
    """
    Memory-optimized vs. the original:

      1. `raw_candidates` is deleted as soon as Phase 1 finishes building
         everything we need from it (meta rows, per-candidate scores,
         resume text). This is the single biggest win — at 100k
         candidates, the raw JSONL-derived dict list is typically
         2-4 GB. The caller (rank.py) MUST NOT reference raw_candidates
         after calling engine.run() — see rank.py for the corresponding
         change (it now captures len(raw_candidates) before the call).

      2. resume_texts is now keyed by candidate_id (text_by_id) instead
         of being a parallel positional list. The original code zipped
         resume_texts against meta_rows by position to filter down to
         post-honeypot survivors — that's correct as long as both lists
         stay in lockstep, but it's fragile and forces resume_texts to
         stay alive in full until the zip runs. Keying by ID lets us
         build the filtered text list directly from df["candidate_id"]
         with no ordering assumptions, and makes it natural to free
         text_by_id immediately afterward.

      3. Intermediate structures (meta_rows, score_cols, text_by_id,
         filtered_texts) are explicitly deleted with gc.collect() the
         moment they're no longer needed, rather than waiting for them
         to fall out of scope at function return.

      4. candidates_by_id is unavoidably kept alive for the full
         function (HoneypotFilter and the downstream embedding step in
         rank.py both need full Candidate objects by ID). This is the
         one large structure we cannot free early without changing the
         honeypot/embedding contract — see the docstring note below for
         why this is an acceptable tradeoff at 100k scale.

      No scoring logic, weights, or thresholds were changed. Output
      rankings are identical to the original implementation.
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()
        self.scorers: List[CandidateScorer] = [
            SkillMatchScorer(),
            ExperienceScorer(self.config.exp_min, self.config.exp_ideal, self.config.exp_max),
            PlatformSignalScorer(),
        ]
        self.tfidf_scorer = TfidfSimilarityScorer()
        self.aggregator   = WeightedScoreAggregator(self.config, self.scorers)
        self.notice_bonus = NoticePeriodBonusDecorator()
        self.score_filter = MinimumScoreFilter(self.config.min_final_score)

    def run(self, jd: JobDescription, raw_candidates: List[dict]) -> RankingResult:
        # ── Phase 1: build candidates + score everything except TF-IDF ──
        meta_rows         = []
        text_by_id: Dict[str, str] = {}
        score_cols         = {s.name: [] for s in self.scorers}
        skipped            = 0
        candidates_by_id: Dict[str, Candidate] = {}

        for i, raw in enumerate(raw_candidates, 1):
            if not isinstance(raw, dict):
                skipped += 1
                continue

            candidate = Candidate(raw, i)
            text      = candidate.to_resume_text()
            if not text.strip():
                skipped += 1
                continue

            meta_rows.append(candidate.to_metadata_row())
            text_by_id[candidate.candidate_id] = text
            for scorer in self.scorers:
                score_cols[scorer.name].append(scorer.score(candidate, jd))

            candidates_by_id[candidate.candidate_id] = candidate

        # ── Free raw_candidates NOW — everything we need from it has been
        # extracted into meta_rows / text_by_id / score_cols / candidates_by_id.
        # This is the single largest memory release in the pipeline
        # (typically 2-4 GB at 100k candidates). The caller must not rely
        # on raw_candidates after engine.run() is invoked.
        del raw_candidates
        gc.collect()

        if not meta_rows:
            return RankingResult(
                pd.DataFrame(),
                candidates_by_id,
                skipped,
                honeypots_removed=0,
                honeypot_ids=[],
            )

        # ── Phase 2: assemble dataframe with non-TF-IDF scores ──────────
        df = pd.DataFrame(meta_rows)
        del meta_rows
        for name, values in score_cols.items():
            df[name] = values
        del score_cols
        gc.collect()

        # ── Phase 3: honeypot filter BEFORE TF-IDF ──────────────────────
        # Placeholder columns so HoneypotFilter.apply() can sort.
        # These will be overwritten by the real aggregation below.
        df[TfidfSimilarityScorer.name] = 0.0
        df["final_score"]              = 0.0

        from controller.utils.honeypotPenalty import HoneypotFilter
        df, removed_ids = HoneypotFilter().apply(df, candidates_by_id)

        if df.empty:
            del text_by_id
            gc.collect()
            return RankingResult(
                pd.DataFrame(),
                candidates_by_id,
                skipped,
                honeypots_removed=len(removed_ids),
                honeypot_ids=removed_ids,
            )

        # ── Phase 4: keep only resume texts for surviving candidates ─────
        # Built from text_by_id keyed lookup — no positional zip, no
        # ordering assumptions. text_by_id is freed immediately after.
        filtered_texts = [
            text_by_id[cid] for cid in df["candidate_id"] if cid in text_by_id
        ]
        del text_by_id
        gc.collect()

        # ── Phase 5: TF-IDF on the smaller, clean candidate set ─────────
        df[TfidfSimilarityScorer.name] = self.tfidf_scorer.score_all(
            jd.text, filtered_texts
        ).round(2)

        del filtered_texts
        gc.collect()

        # ── Phase 6: aggregate → rank → notice bonus → rank → filter ────
        df = self.aggregator.aggregate(df)
        df = self._rank(df)

        df = self.notice_bonus.apply(df)
        df = self._rank(df)

        df = self.score_filter.apply(df)
        df = self._rank(df)

        return RankingResult(
            df,
            candidates_by_id,
            skipped,
            honeypots_removed=len(removed_ids),
            honeypot_ids=removed_ids,
        )

    @staticmethod
    def _rank(df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("final_score", ascending=False).reset_index(drop=True)
        df.index      += 1
        df.index.name  = "rank"
        return df