"""
controller/utils/honeypotPenalty.py
====================================
Detects and removes honeypot / unrealistic candidate profiles BEFORE
the top-100 slice is taken.

Policy: ANY triggered signal = immediate removal. No soft penalties.

Detection signals
-----------------
 1. Impossible company tenure
    – career_history entry whose duration > company_age (for known young companies).

 2. Experience–timeline mismatch
    – sum of all career_history durations differs from profile.years_of_experience
      by more than MAX_TIMELINE_DRIFT years.

 3. Skill inflation
    – candidate claims "expert" proficiency in more than EXPERT_SKILL_CAP skills.

 4. Zero-years expert
    – Any skill listed as "expert" but years_used == 0.

 5. Overlapping job tenures
    – two career_history entries whose date ranges overlap by more than
      OVERLAP_TOLERANCE_MONTHS months.

 6. Future dates
    – any date field (start/end of job, education) is in the future.

 7. Suspiciously perfect paper profile
    – profile_completeness_score > 95 but github_activity_score == 0
      and no skill_assessment_scores.

 8. Excessive job hopping
    – more than JOB_HOP_COUNT jobs within JOB_HOP_YEARS years.

 9. Unrealistic promotion velocity
    – progression from a junior-tier role to a senior-tier role within
      PROMOTION_MIN_YEARS years.

10. Duplicate career entries
    – same (company, title, start_year) tuple appears more than once.

11. Impossible skill chronology
    – any skill's years_used exceeds the candidate's total years_of_experience.

12. Education–employment inconsistency
    – earliest job start predates graduation by more than
      GRAD_WORK_OVERLAP_YEARS while stated YOE is large.

13. Simultaneous full-time jobs
    – more than SIMULTANEOUS_JOB_LIMIT non-trivially overlapping jobs at the
      same time.

14. Keyword stuffing
    – total skill list length exceeds SKILL_LIST_CAP, or the same technology
      appears under more than one entry.

15. Activity contradiction
    – high completeness + high YOE but zero GitHub activity, zero
      certifications, and zero assessments combined.

Public API
----------
    from controller.utils.honeypotPenalty import HoneypotFilter
    cleaned_df, removed_ids = HoneypotFilter().apply(df, candidates_by_id)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd


# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class HoneypotConfig:
    # ── Original thresholds ───────────────────────────────────────────
    expert_skill_cap: int = 6            # >N expert skills → removed
    max_timeline_drift: float = 3.0      # years; max allowed gap between stated YOE and career sum
    overlap_tolerance_months: int = 2    # small overlaps (e.g. notice periods) are acceptable

    # Known founding years for high-frequency companies.
    company_founding_years: Dict[str, int] = field(default_factory=lambda: {
        "openai": 2015,
        "anthropic": 2021,
        "mistral": 2023,
        "perplexity": 2022,
        "cohere": 2019,
        "inflection": 2022,
        "character.ai": 2021,
        "stability ai": 2020,
        "midjourney": 2021,
        "hugging face": 2016,
    })

    # ── Signal 8 – Excessive job hopping ─────────────────────────────
    job_hop_count: int = 8               # more than N jobs …
    job_hop_years: float = 4.0           # … within this many years

    # ── Signal 9 – Unrealistic promotion velocity ─────────────────────
    promotion_min_years: float = 1.5     # junior → senior in less than N years

    # ── Signal 11 – Impossible skill chronology ───────────────────────
    # (no extra threshold; compared against years_of_experience directly)

    # ── Signal 12 – Education–employment inconsistency ────────────────
    # Earliest job may predate graduation by at most this many years
    # (internship / co-op tolerance).
    grad_work_overlap_years: float = 1.0
    # Only apply when stated YOE is above this — avoids penalising new grads.
    grad_check_min_yoe: float = 3.0

    # ── Signal 13 – Simultaneous full-time jobs ───────────────────────
    simultaneous_job_limit: int = 2      # more than N jobs overlapping at once

    # ── Signal 14 – Keyword stuffing ─────────────────────────────────
    skill_list_cap: int = 50             # total skills including all proficiency levels

    # ── Signal 15 – Activity contradiction ───────────────────────────
    activity_contradiction_completeness: float = 85.0   # completeness threshold
    activity_contradiction_min_yoe: float = 5.0         # experience threshold


# ════════════════════════════════════════════════════════════
# ROLE-TIER MAP  (used by Signal 9)
# ════════════════════════════════════════════════════════════
# Lower number = more junior.  Gaps of >=2 tiers in < promotion_min_years -> flag.
_ROLE_TIER: Dict[str, int] = {
    # Tier 0 - student / trainee
    "intern": 0, "trainee": 0, "apprentice": 0, "student": 0,
    # Tier 1 - entry level
    "junior": 1, "associate": 1, "entry": 1, "graduate": 1,
    # Tier 2 - mid level
    "engineer": 2, "developer": 2, "analyst": 2, "consultant": 2,
    "specialist": 2, "designer": 2,
    # Tier 3 - senior / lead
    "senior": 3, "lead": 3, "staff": 3, "principal": 3,
    # Tier 4 - management / architecture
    "manager": 4, "architect": 4, "director": 4,
    # Tier 5 - executive
    "vp": 5, "cto": 5, "ceo": 5, "head of": 5, "chief": 5,
}

_PROMOTION_SKIP_THRESHOLD = 2   # tier jump that is "unrealistic" in too short a span


def _title_tier(title: str) -> int | None:
    """Return the highest matching tier for a job title, or None."""
    t    = title.lower()
    best: int | None = None
    for keyword, tier in _ROLE_TIER.items():
        if keyword in t:
            if best is None or tier > best:
                best = tier
    return best


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════
_CURRENT_YEAR = datetime.now().year


def _parse_year(value) -> int | None:
    """Extract a 4-digit year from int, float, or string."""
    if value is None:
        return None
    try:
        s = str(int(float(str(value).strip())))
        if re.fullmatch(r"\d{4}", s):
            return int(s)
    except (ValueError, TypeError):
        pass
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").year
    except ValueError:
        pass
    return None


def _current_year_float() -> float:
    now = datetime.now()
    return now.year + (now.month - 1) / 12


def _tenure_years(job: dict) -> float | None:
    start   = _parse_year(job.get("start_year") or job.get("start_date"))
    end_raw = job.get("end_year") or job.get("end_date") or "present"
    if str(end_raw).lower() in ("present", "current", "now", ""):
        end = _current_year_float()
    else:
        end = _parse_year(end_raw)
    if start is None or end is None:
        return None
    return max(0.0, float(end - start))


def _job_interval(job: dict) -> Tuple[float, float] | None:
    """Return (start_float, end_float) for a career entry, or None."""
    start   = _parse_year(job.get("start_year") or job.get("start_date"))
    end_raw = job.get("end_year") or job.get("end_date") or "present"
    end = (
        _current_year_float()
        if str(end_raw).lower() in ("present", "current", "now", "")
        else _parse_year(end_raw)
    )
    if start is None or end is None:
        return None
    return float(start), float(end)


# ════════════════════════════════════════════════════════════
# DETECTOR
# ════════════════════════════════════════════════════════════
class _HoneypotDetector:
    def __init__(self, cfg: HoneypotConfig):
        self.cfg = cfg

    def is_honeypot(self, candidate) -> Tuple[bool, List[str]]:
        """
        Run all checks. Returns (flagged: bool, reasons: list[str]).
        A single triggered check is enough to flag the candidate.
        """
        reasons: List[str] = []

        checks = [
            # Original signals
            self._impossible_tenure,
            self._timeline_mismatch,
            self._skill_inflation,
            self._zero_years_expert,
            self._overlapping_jobs,
            self._future_dates,
            self._suspiciously_perfect,
            # New signals
            self._excessive_job_hopping,
            self._unrealistic_promotion_velocity,
            self._duplicate_career_entries,
            self._impossible_skill_chronology,
            self._education_employment_inconsistency,
            self._simultaneous_fulltime_jobs,
            self._keyword_stuffing,
            self._activity_contradiction,
        ]
        for check in checks:
            flagged, reason = check(candidate)
            if flagged:
                reasons.append(reason)

        return bool(reasons), reasons

    # ════════════════════════════════════════════════════════════
    # ORIGINAL SIGNALS
    # ════════════════════════════════════════════════════════════

    def _impossible_tenure(self, candidate) -> Tuple[bool, str]:
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            company = str(job.get("company", "") or "").lower().strip()
            dur     = _tenure_years(job)
            if dur is None:
                continue
            for known_co, founded in self.cfg.company_founding_years.items():
                if known_co in company:
                    company_age = _CURRENT_YEAR - founded
                    if dur > company_age + 0.5:
                        return True, (
                            f"IMPOSSIBLE_TENURE: Claims {dur:.1f}yr tenure at '{company}' "
                            f"(founded {founded}, only {company_age}yr old)"
                        )
        return False, ""

    def _timeline_mismatch(self, candidate) -> Tuple[bool, str]:
        stated = candidate.years_of_experience
        if stated == 0:
            return False, ""
        total, counted = 0.0, 0
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            dur = _tenure_years(job)
            if dur is not None:
                total   += dur
                counted += 1
        if counted == 0:
            return False, ""
        drift = abs(total - stated)
        if drift > self.cfg.max_timeline_drift:
            return True, (
                f"TIMELINE_MISMATCH: Stated YOE={stated:.1f} but career history sums to "
                f"{total:.1f}yr (drift={drift:.1f}yr > {self.cfg.max_timeline_drift}yr allowed)"
            )
        return False, ""

    def _skill_inflation(self, candidate) -> Tuple[bool, str]:
        expert_count = sum(
            1 for s in candidate.skills
            if isinstance(s, dict) and str(s.get("proficiency", "")).lower() == "expert"
        )
        if expert_count > self.cfg.expert_skill_cap:
            return True, (
                f"SKILL_INFLATION: Claims expert proficiency in {expert_count} skills "
                f"(cap={self.cfg.expert_skill_cap})"
            )
        return False, ""

    def _zero_years_expert(self, candidate) -> Tuple[bool, str]:
        for s in candidate.skills:
            if not isinstance(s, dict):
                continue
            if str(s.get("proficiency", "")).lower() == "expert":
                years_used = s.get("years_used")
                if years_used is not None:
                    try:
                        if float(years_used) == 0:
                            return True, (
                                f"ZERO_YEARS_EXPERT: Expert in '{s.get('name', '?')}' "
                                f"but years_used=0"
                            )
                    except (ValueError, TypeError):
                        pass
        return False, ""

    def _overlapping_jobs(self, candidate) -> Tuple[bool, str]:
        intervals: List[Tuple[float, float, str]] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            iv = _job_interval(job)
            if iv is not None:
                intervals.append((*iv, str(job.get("title", ""))))

        intervals.sort(key=lambda x: x[0])
        tol = self.cfg.overlap_tolerance_months / 12
        for i in range(len(intervals) - 1):
            a_start, a_end, a_title = intervals[i]
            b_start, _b_end, b_title = intervals[i + 1]
            overlap = a_end - b_start
            if overlap > tol:
                return True, (
                    f"OVERLAPPING_JOBS: '{a_title}' (ends {a_end:.1f}) and "
                    f"'{b_title}' (starts {b_start:.1f}) overlap {overlap:.1f}yr"
                )
        return False, ""

    def _future_dates(self, candidate) -> Tuple[bool, str]:
        fields: List[Tuple[any, str]] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            for key in ("start_year", "end_year", "start_date", "end_date"):
                val = job.get(key)
                if val and str(val).lower() not in ("present", "current", "now"):
                    fields.append((val, f"career '{job.get('title', '')}' {key}"))
        for edu in candidate.education:
            if not isinstance(edu, dict):
                continue
            for key in ("graduation_year", "end_year", "start_year"):
                val = edu.get(key)
                if val:
                    fields.append((val, f"education {key}"))
        for raw_val, label in fields:
            yr = _parse_year(raw_val)
            if yr is not None and yr > _CURRENT_YEAR + 1:
                return True, f"FUTURE_DATE: Future date in {label}: {yr}"
        return False, ""

    def _suspiciously_perfect(self, candidate) -> Tuple[bool, str]:
        rs = candidate.signals
        try:
            completeness = float(rs.get("profile_completeness_score", 0) or 0)
        except (ValueError, TypeError):
            completeness = 0.0
        try:
            raw_gh = rs.get("github_activity_score")
            github = float(raw_gh) if raw_gh is not None else -1.0
        except (ValueError, TypeError):
            github = -1.0
        assessments = rs.get("skill_assessment_scores", {})
        if completeness > 95 and github == 0 and not assessments:
            return True, (
                f"SUSPICIOUSLY_PERFECT: Profile completeness={completeness:.0f} but "
                f"github_score=0 and no skill assessments — inflated paper profile"
            )
        return False, ""

    # ════════════════════════════════════════════════════════════
    # NEW SIGNALS
    # ════════════════════════════════════════════════════════════

    def _excessive_job_hopping(self, candidate) -> Tuple[bool, str]:
        """
        Flag candidates with more than JOB_HOP_COUNT distinct jobs whose
        combined span fits inside JOB_HOP_YEARS years.
        """
        start_years: List[float] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            iv = _job_interval(job)
            if iv is not None:
                start_years.append(iv[0])

        if not start_years:
            return False, ""

        start_years.sort()
        window_end     = start_years[0] + self.cfg.job_hop_years
        jobs_in_window = sum(1 for s in start_years if s <= window_end)

        if jobs_in_window > self.cfg.job_hop_count:
            return True, (
                f"EXCESSIVE_JOB_HOPPING: {jobs_in_window} jobs started within "
                f"{self.cfg.job_hop_years:.0f}yr window "
                f"(threshold={self.cfg.job_hop_count})"
            )
        return False, ""

    def _unrealistic_promotion_velocity(self, candidate) -> Tuple[bool, str]:
        """
        Detect a tier jump of >= _PROMOTION_SKIP_THRESHOLD in less than
        promotion_min_years between consecutive roles.
        """
        timed_roles: List[Tuple[float, int, str]] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            title = str(job.get("title", "") or "")
            tier  = _title_tier(title)
            iv    = _job_interval(job)
            if tier is not None and iv is not None:
                timed_roles.append((iv[0], tier, title))

        if len(timed_roles) < 2:
            return False, ""

        timed_roles.sort(key=lambda x: x[0])

        for i in range(len(timed_roles) - 1):
            s1, t1, title1 = timed_roles[i]
            s2, t2, title2 = timed_roles[i + 1]
            elapsed   = s2 - s1
            tier_jump = t2 - t1
            if (
                tier_jump >= _PROMOTION_SKIP_THRESHOLD
                and 0 <= elapsed < self.cfg.promotion_min_years
            ):
                return True, (
                    f"UNREALISTIC_PROMOTION: '{title1}' (tier {t1}) -> "
                    f"'{title2}' (tier {t2}) in {elapsed:.1f}yr "
                    f"(min={self.cfg.promotion_min_years}yr for a "
                    f"{tier_jump}-tier jump)"
                )
        return False, ""

    def _duplicate_career_entries(self, candidate) -> Tuple[bool, str]:
        """
        Detect entries with the same (company, title, start_year) tuple.
        """
        seen: Dict[Tuple[str, str, str], int] = {}
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            company = str(job.get("company", "") or "").lower().strip()
            title   = str(job.get("title",   "") or "").lower().strip()
            start   = str(_parse_year(job.get("start_year") or job.get("start_date")) or "")
            key     = (company, title, start)
            if not any(key):
                continue
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > 1:
                return True, (
                    f"DUPLICATE_CAREER_ENTRY: '{title}' at '{company}' "
                    f"starting {start} appears more than once"
                )
        return False, ""

    def _impossible_skill_chronology(self, candidate) -> Tuple[bool, str]:
        """
        Any skill whose years_used exceeds total years_of_experience is impossible.
        """
        stated_yoe = float(candidate.years_of_experience or 0)
        if stated_yoe <= 0:
            return False, ""

        for s in candidate.skills:
            if not isinstance(s, dict):
                continue
            years_used = s.get("years_used")
            if years_used is None:
                continue
            try:
                yu = float(years_used)
            except (ValueError, TypeError):
                continue
            if yu > stated_yoe:
                return True, (
                    f"IMPOSSIBLE_SKILL_CHRONOLOGY: '{s.get('name', '?')}' "
                    f"years_used={yu:.1f} exceeds total YOE={stated_yoe:.1f}"
                )
        return False, ""

    def _education_employment_inconsistency(self, candidate) -> Tuple[bool, str]:
        """
        Earliest job start predates graduation by more than grad_work_overlap_years
        while stated YOE is significant.
        """
        stated_yoe = float(candidate.years_of_experience or 0)
        if stated_yoe < self.cfg.grad_check_min_yoe:
            return False, ""

        grad_years: List[int] = []
        for edu in candidate.education:
            if not isinstance(edu, dict):
                continue
            for key in ("graduation_year", "end_year"):
                yr = _parse_year(edu.get(key))
                if yr is not None:
                    grad_years.append(yr)

        if not grad_years:
            return False, ""

        latest_grad = max(grad_years)

        job_starts: List[float] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            iv = _job_interval(job)
            if iv is not None:
                job_starts.append(iv[0])

        if not job_starts:
            return False, ""

        earliest_start = min(job_starts)
        overlap = latest_grad - earliest_start
        if overlap > self.cfg.grad_work_overlap_years:
            return True, (
                f"EDUCATION_INCONSISTENCY: Earliest job starts {earliest_start:.0f} "
                f"but latest graduation is {latest_grad} — "
                f"{overlap:.1f}yr pre-grad employment "
                f"(tolerance={self.cfg.grad_work_overlap_years}yr) "
                f"with stated YOE={stated_yoe:.1f}"
            )
        return False, ""

    def _simultaneous_fulltime_jobs(self, candidate) -> Tuple[bool, str]:
        """
        Sweep-line check: more than simultaneous_job_limit jobs active at once.
        """
        tol       = self.cfg.overlap_tolerance_months / 12
        intervals: List[Tuple[float, float]] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            iv = _job_interval(job)
            if iv is not None:
                intervals.append(iv)

        if len(intervals) < self.cfg.simultaneous_job_limit + 1:
            return False, ""

        events: List[Tuple[float, int]] = []
        for start, end in intervals:
            events.append((start, +1))
            events.append((end - tol, -1))

        events.sort(key=lambda e: (e[0], e[1]))

        active = 0
        for _year, delta in events:
            active += delta
            if active > self.cfg.simultaneous_job_limit:
                return True, (
                    f"SIMULTANEOUS_JOBS: More than {self.cfg.simultaneous_job_limit} "
                    f"jobs active concurrently (beyond "
                    f"{self.cfg.overlap_tolerance_months}-month tolerance)"
                )
        return False, ""

    def _keyword_stuffing(self, candidate) -> Tuple[bool, str]:
        """
        (a) Too many total skills, or (b) same technology listed more than once.
        """
        skills = [s for s in candidate.skills if isinstance(s, dict)]

        if len(skills) > self.cfg.skill_list_cap:
            return True, (
                f"KEYWORD_STUFFING: {len(skills)} skills listed "
                f"(cap={self.cfg.skill_list_cap})"
            )

        seen_names: Dict[str, int] = {}
        for s in skills:
            raw        = str(s.get("name", "") or "")
            normalised = re.sub(r"[^a-z0-9]", "", raw.lower())
            if not normalised:
                continue
            seen_names[normalised] = seen_names.get(normalised, 0) + 1
            if seen_names[normalised] > 1:
                return True, (
                    f"KEYWORD_STUFFING: Technology '{raw}' appears more than "
                    f"once in the skill list"
                )
        return False, ""

    def _activity_contradiction(self, candidate) -> Tuple[bool, str]:
        """
        High completeness + significant YOE but zero GitHub, no assessments,
        and no certifications — inflated paper profile.
        """
        stated_yoe = float(candidate.years_of_experience or 0)
        if stated_yoe < self.cfg.activity_contradiction_min_yoe:
            return False, ""

        rs = candidate.signals
        try:
            completeness = float(rs.get("profile_completeness_score", 0) or 0)
        except (ValueError, TypeError):
            completeness = 0.0

        if completeness < self.cfg.activity_contradiction_completeness:
            return False, ""

        try:
            raw_gh = rs.get("github_activity_score")
            github = float(raw_gh) if raw_gh is not None else -1.0
        except (ValueError, TypeError):
            github = -1.0

        assessments    = rs.get("skill_assessment_scores", {})
        certifications = rs.get("certifications", [])

        if github == 0 and not assessments and not certifications:
            return True, (
                f"ACTIVITY_CONTRADICTION: completeness={completeness:.0f}, "
                f"YOE={stated_yoe:.1f} but github_score=0, "
                f"no assessments, no certifications"
            )
        return False, ""


# ════════════════════════════════════════════════════════════
# PUBLIC FILTER
# ════════════════════════════════════════════════════════════
class HoneypotFilter:
    """
    ANY triggered signal -> candidate is removed immediately.

    Called by CandidateRankingEngine.run() BEFORE TF-IDF scoring so that
    the cosine-similarity matrix is built only over clean candidates.

    Usage
    -----
        cleaned_df, removed_ids = HoneypotFilter().apply(df, candidates_by_id)
    """

    def __init__(self, config: HoneypotConfig | None = None):
        self.cfg       = config or HoneypotConfig()
        self._detector = _HoneypotDetector(self.cfg)

    def apply(
        self,
        df: pd.DataFrame,
        candidates_by_id: Dict,
    ) -> Tuple[pd.DataFrame, List[str]]:
        if df.empty:
            return df, []

        remove_ids: List[str]            = []
        flag_map:   Dict[str, List[str]] = {}

        for cid in df["candidate_id"]:
            candidate = candidates_by_id.get(cid)
            if candidate is None:
                continue
            flagged, reasons = self._detector.is_honeypot(candidate)
            if flagged:
                remove_ids.append(cid)
                flag_map[cid] = reasons

        remove_set = set(remove_ids)

        if remove_ids:
            print(
                f"[HoneypotFilter] Removed {len(remove_ids)} honeypot candidate(s): "
                + ", ".join(remove_ids[:10])
                + ("..." if len(remove_ids) > 10 else "")
            )
            for cid, reasons in list(flag_map.items())[:5]:
                print(f"  -> {cid}: {' | '.join(reasons)}")

        cleaned_df = df[~df["candidate_id"].isin(remove_set)].copy()
        cleaned_df = cleaned_df.sort_values("final_score", ascending=False).reset_index(drop=True)
        cleaned_df.index      += 1
        cleaned_df.index.name  = "rank"

        print(f"[HoneypotFilter] {len(cleaned_df)} clean candidate(s) remaining.")

        return cleaned_df, remove_ids