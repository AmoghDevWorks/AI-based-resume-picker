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
    # Detection thresholds
    expert_skill_cap: int = 6           # >N expert skills → removed
    max_timeline_drift: float = 3.0     # years; max allowed gap between stated YOE and career sum
    overlap_tolerance_months: int = 2   # small overlaps (e.g. notice periods) are acceptable

    # Known founding years for high-frequency companies.
    # Catches "8 yrs at a 3-yr-old company" style honeypots.
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
    start = _parse_year(job.get("start_year") or job.get("start_date"))
    end_raw = job.get("end_year") or job.get("end_date") or "present"
    if str(end_raw).lower() in ("present", "current", "now", ""):
        end = _current_year_float()
    else:
        end = _parse_year(end_raw)
    if start is None or end is None:
        return None
    return max(0.0, float(end - start))


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
            self._impossible_tenure,
            self._timeline_mismatch,
            self._skill_inflation,
            self._zero_years_expert,
            self._overlapping_jobs,
            self._future_dates,
            self._suspiciously_perfect,
        ]
        for check in checks:
            flagged, reason = check(candidate)
            if flagged:
                reasons.append(reason)

        return bool(reasons), reasons

    # ── Signal 1 ─────────────────────────────────────────────────────
    def _impossible_tenure(self, candidate) -> Tuple[bool, str]:
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            company = str(job.get("company", "") or "").lower().strip()
            dur = _tenure_years(job)
            if dur is None:
                continue
            for known_co, founded in self.cfg.company_founding_years.items():
                if known_co in company:
                    company_age = _CURRENT_YEAR - founded
                    if dur > company_age + 0.5:
                        return True, (
                            f"Claims {dur:.1f}yr tenure at '{company}' "
                            f"(founded {founded}, only {company_age}yr old)"
                        )
        return False, ""

    # ── Signal 2 ─────────────────────────────────────────────────────
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
                total += dur
                counted += 1
        if counted == 0:
            return False, ""
        drift = abs(total - stated)
        if drift > self.cfg.max_timeline_drift:
            return True, (
                f"Stated YOE={stated:.1f} but career history sums to {total:.1f}yr "
                f"(drift={drift:.1f}yr > {self.cfg.max_timeline_drift}yr allowed)"
            )
        return False, ""

    # ── Signal 3 ─────────────────────────────────────────────────────
    def _skill_inflation(self, candidate) -> Tuple[bool, str]:
        expert_count = sum(
            1 for s in candidate.skills
            if isinstance(s, dict) and str(s.get("proficiency", "")).lower() == "expert"
        )
        if expert_count > self.cfg.expert_skill_cap:
            return True, (
                f"Claims expert proficiency in {expert_count} skills "
                f"(cap={self.cfg.expert_skill_cap})"
            )
        return False, ""

    # ── Signal 4 ─────────────────────────────────────────────────────
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
                                f"Expert in '{s.get('name', '?')}' but years_used=0"
                            )
                    except (ValueError, TypeError):
                        pass
        return False, ""

    # ── Signal 5 ─────────────────────────────────────────────────────
    def _overlapping_jobs(self, candidate) -> Tuple[bool, str]:
        intervals: List[Tuple[float, float, str]] = []
        for job in candidate.career_history:
            if not isinstance(job, dict):
                continue
            start = _parse_year(job.get("start_year") or job.get("start_date"))
            end_raw = job.get("end_year") or job.get("end_date") or "present"
            end = (
                _current_year_float()
                if str(end_raw).lower() in ("present", "current", "now", "")
                else _parse_year(end_raw)
            )
            if start is None or end is None:
                continue
            intervals.append((float(start), float(end), str(job.get("title", ""))))

        intervals.sort(key=lambda x: x[0])
        tol = self.cfg.overlap_tolerance_months / 12
        for i in range(len(intervals) - 1):
            a_start, a_end, a_title = intervals[i]
            b_start, _b_end, b_title = intervals[i + 1]
            overlap = a_end - b_start
            if overlap > tol:
                return True, (
                    f"Job overlap: '{a_title}' (ends {a_end:.1f}) and "
                    f"'{b_title}' (starts {b_start:.1f}) overlap {overlap:.1f}yr"
                )
        return False, ""

    # ── Signal 6 ─────────────────────────────────────────────────────
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
                return True, f"Future date in {label}: {yr}"
        return False, ""

    # ── Signal 7 ─────────────────────────────────────────────────────
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
                f"Profile completeness={completeness:.0f} but github_score=0 "
                f"and no skill assessments — inflated paper profile"
            )
        return False, ""


# ════════════════════════════════════════════════════════════
# PUBLIC FILTER
# ════════════════════════════════════════════════════════════
class HoneypotFilter:
    """
    ANY triggered signal → candidate is removed immediately.

    Usage
    -----
        cleaned_df, removed_ids = HoneypotFilter().apply(df, candidates_by_id)
    """

    def __init__(self, config: HoneypotConfig | None = None):
        self.cfg = config or HoneypotConfig()
        self._detector = _HoneypotDetector(self.cfg)

    def apply(
        self,
        df: pd.DataFrame,
        candidates_by_id: Dict,
    ) -> Tuple[pd.DataFrame, List[str]]:
        if df.empty:
            return df, []

        remove_ids: List[str] = []
        flag_map: Dict[str, List[str]] = {}

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
                + ("…" if len(remove_ids) > 10 else "")
            )
            for cid, reasons in list(flag_map.items())[:5]:
                print(f"  ↳ {cid}: {' | '.join(reasons)}")

        cleaned_df = df[~df["candidate_id"].isin(remove_set)].copy()
        cleaned_df = cleaned_df.sort_values("final_score", ascending=False).reset_index(drop=True)
        cleaned_df.index += 1
        cleaned_df.index.name = "rank"

        print(f"[HoneypotFilter] {len(cleaned_df)} clean candidate(s) remaining.")

        return cleaned_df, remove_ids