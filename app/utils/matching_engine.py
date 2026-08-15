from __future__ import annotations

from collections import OrderedDict
from typing import Iterable

from app.utils.skill_dictionary import SKILL_ALIASES, SKILL_CATEGORIES, normalize_skill


_CANONICAL_TO_DISPLAY: dict[str, str] = {}
for _canonical, _aliases in SKILL_ALIASES.items():
    _CANONICAL_TO_DISPLAY[normalize_skill(_canonical)] = _canonical
for _category, _skills in SKILL_CATEGORIES.items():
    for _skill in _skills:
        _norm = normalize_skill(_skill)
        if _norm not in _CANONICAL_TO_DISPLAY:
            _CANONICAL_TO_DISPLAY[_norm] = _skill


def _canonicalize(skill_name: str) -> str:
    text = (skill_name or "").strip()
    if not text:
        return ""
    normalized = normalize_skill(text)
    for canonical, aliases in SKILL_ALIASES.items():
        if normalized == normalize_skill(canonical):
            return normalize_skill(canonical)
        if normalized in {normalize_skill(alias) for alias in aliases}:
            return normalize_skill(canonical)
    return normalized


def _to_display(canonical: str) -> str:
    return _CANONICAL_TO_DISPLAY.get(canonical, canonical.title())


def _skill_set(skills: Iterable[str]) -> set[str]:
    normalized: set[str] = set()
    for skill in skills:
        canonical = _canonicalize(skill)
        if canonical:
            normalized.add(canonical)
    return normalized


def _category_for_skill(skill: str) -> str:
    canonical = _canonicalize(skill)
    for category, items in SKILL_CATEGORIES.items():
        if canonical in {normalize_skill(item) for item in items}:
            return category
    return "Other"


def calculate_match(candidate_skills: Iterable[str], required_skills: Iterable[str]) -> dict:
    candidate = _skill_set(candidate_skills)
    required = _skill_set(required_skills)

    matched = sorted(candidate & required, key=lambda s: s.lower())
    missing = sorted(required - candidate, key=lambda s: s.lower())
    extra = sorted(candidate - required, key=lambda s: s.lower())

    total_required = len(required)
    match_percentage = 0.0 if total_required == 0 else round((len(matched) / total_required) * 100, 2)

    category_scores: OrderedDict[str, float] = OrderedDict()
    for category_name in SKILL_CATEGORIES.keys():
        category_skills = {normalize_skill(item) for item in SKILL_CATEGORIES[category_name]}
        relevant_required = sorted(required & category_skills, key=lambda s: s.lower())
        if not relevant_required:
            continue
        relevant_matched = [skill for skill in relevant_required if skill in candidate]
        score = 0.0 if not relevant_required else round((len(relevant_matched) / len(relevant_required)) * 100, 2)
        category_scores[category_name] = score

    return {
        "matched_skills": [_to_display(s) for s in matched],
        "missing_skills": [_to_display(s) for s in missing],
        "extra_skills": [_to_display(s) for s in extra],
        "match_percentage": match_percentage,
        "category_scores": category_scores,
    }
