"""
Module 9: Job Description Matcher.

Compares a job description against an applicant's skill profile
(derived from their resume) and produces:
  - a deterministic match score (0-100)
  - category scores (e.g., skills, education, experience)
  - a list of matched skills
  - a list of missing skills (skills required by the job but absent
    from the resume)
  - human-readable feedback lines

The matcher is intentionally pure (no I/O, no DB), unit-testable, and
works directly on plain Python data structures so it can be used both
by services and scripts.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

# Weights for the three matching categories. They must sum to 100.
SKILLS_WEIGHT = 50.0
EXPERIENCE_WEIGHT = 30.0
EDUCATION_WEIGHT = 20.0


@dataclass
class CategoryScore:
    name: str
    score: float
    max_score: float
    weight: float
    details: dict

    @property
    def weighted_score(self) -> float:
        return round(self.score * self.weight / 100.0, 2)


@dataclass
class JobMatchResult:
    overall_score: float
    category_scores: list[CategoryScore]
    matched_skills: list[str]
    missing_skills: list[str]
    feedback: list[str]
    is_qualified: bool


def _normalize_text(text: str | None) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    return " ".join(text.lower().split())


def _extract_keywords(job_description: str) -> set[str]:
    """Extract simple keyword tokens from a job description."""
    if not job_description:
        return set()
    normalized = _normalize_text(job_description)
    stop_words = {
        "the", "and", "for", "with", "our", "you", "your", "are",
        "will", "have", "has", "had", "was", "were", "be", "been",
        "this", "that", "these", "those", "from", "into", "onto",
        "a", "an", "of", "to", "in", "on", "at", "by", "as",
        "is", "it", "or", "if", "we", "us", "their", "they",
    }
    words = set(word for word in normalized.split() if word not in stop_words)
    return words
