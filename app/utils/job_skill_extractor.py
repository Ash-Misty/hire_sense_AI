import re
from collections.abc import Iterable

from app.utils.skill_dictionary import SKILL_ALIASES, SKILL_CATEGORIES, normalize_skill


def _normalize_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9+#.\s-]", " ", (value or "").lower()).split())


def _contains_variant(text: str, variant: str) -> bool:
    if not variant:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def extract_job_skills(job_description: str) -> list[str]:
    if not job_description or not job_description.strip():
        return []

    normalized_text = _normalize_text(job_description)
    seen: dict[str, str] = {}

    for category_skills in SKILL_CATEGORIES.values():
        for skill_name in category_skills:
            canonical_key = normalize_skill(skill_name)
            if canonical_key in seen:
                continue

            aliases = {normalize_skill(alias) for alias in SKILL_ALIASES.get(skill_name, set())}
            variants = {canonical_key, *aliases}

            if any(_contains_variant(normalized_text, variant) for variant in variants):
                seen[canonical_key] = skill_name

    return list(seen.values())


def extract_skill_names(job_description: str) -> list[str]:
    return extract_job_skills(job_description)
