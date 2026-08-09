"""
Module 7 — Deterministic, offline skill-extraction engine.

This engine enhances the basic flat skill matching from Module 6 with:

  * Categorization      -> skills grouped into SKILL_CATEGORIES.
  * Normalization       -> aliases (e.g. "React.js" / "Reactjs") map to a
                           canonical skill name ("React").
  * Frequency counting  -> how many times each skill appears in the text.
  * Deterministic match -> a rule-based confidence score based on the quality
                           of the match. This is NOT an ML/AI confidence score;
                           it is a stable, explainable heuristic.

The engine is intentionally offline and deterministic. It reuses the skill
dictionary vocabulary and does not call any external API.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.utils.skill_dictionary import (
    CATEGORY_LOOKUP,
    SINGLE_CHAR_SKILLS,
    SKILL_ALIASES,
    SKILL_CATEGORIES,
    normalize_skill,
)


@dataclass
class ExtractedSkill:
    """A single extracted skill with its metadata."""
    skill: str
    normalized_skill: str
    category: str
    count: int
    confidence: float


@dataclass
class ExtractionResult:
    """The full result of running the extractor over text."""
    skills: list[ExtractedSkill] = field(default_factory=list)

    @property
    def total_skills(self) -> int:
        return len(self.skills)

    def category_summary(self) -> dict[str, int]:
        """Return {category: number of skills}."""
        summary: dict[str, int] = {}
        for skill in self.skills:
            summary[skill.category] = summary.get(skill.category, 0) + 1
        return summary


# --------------------------------------------------------------------------
# Regex helpers
# --------------------------------------------------------------------------
# Token pattern used to detect standalone single-character skills.
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9#+.\-]*")
# Word boundary pattern for multi-token phrase matching.
_PHRASE_RE = re.compile(r"[\w+#.\-]+")


def _build_phrase_pattern(normalized: str) -> re.Pattern:
    """
    Build a regex that matches a phrase on word boundaries while allowing
    multi-word phrases to match naturally.
    """
    # Escape but treat spaces as flexible whitespace.
    parts = [re.escape(p) for p in normalized.split()]
    pattern = r"\b" + r"[\s]+".join(parts) + r"\b"
    return re.compile(pattern, re.IGNORECASE)


def _count_phrase(text: str, normalized: str) -> int:
    """Count non-overlapping occurrences of a normalized phrase in text."""
    pattern = _build_phrase_pattern(normalized)
    return len(pattern.findall(text))


def _count_single_char(text_normalized: str, skill_normalized: str) -> int:
    """Count standalone single-character skill tokens (e.g. 'c', 'r')."""
    tokens = _TOKEN_RE.findall(text_normalized)
    return sum(1 for tok in tokens if tok == skill_normalized)


def _confidence(count: int, exact_section_hit: bool, is_alias: bool) -> float:
    """
    Deterministic confidence heuristic (0.0 - 1.0).

    * Base score depends on how often a skill appears.
    * A small bonus is added when the skill appears in the skills section.
    * A tiny penalty is applied for alias matches to reflect that aliases are
      slightly less explicit than the canonical name.

    This is fully deterministic — it is not an ML probability.
    """
    score = min(0.5 + 0.1 * count, 0.95)
    if exact_section_hit:
        score = min(score + 0.05, 1.0)
    if is_alias:
        score = max(score - 0.02, 0.0)
    return round(score, 2)


def _collect_canonical_variants() -> tuple[
    dict[str, dict],  # canonical -> {display, category, variants}
]:
    """
    Build a canonical-centric lookup.

    Each canonical skill maps to a metadata dict containing:
      * display  -> preferred display name.
      * category -> first category that includes it.
      * variants -> set of normalized strings (canonical + all aliases)
                    that should be matched to count this skill.

    This consolidates overlapping dictionary entries (e.g. "Node" and
    "Node.js", or "Postgres" and "PostgreSQL") under one canonical skill so
    that a single occurrence is not double-counted.
    """
    # Map any alias/normalized variant -> its canonical normalized form.
    alias_to_canonical: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        canonical_norm = normalize_skill(canonical)
        for alias in aliases:
            alias_to_canonical[normalize_skill(alias)] = canonical_norm

    canonical_info: dict[str, dict] = {}

    for category, skills in SKILL_CATEGORIES.items():
        for display in skills:
            normalized = normalize_skill(display)
            canonical_norm = alias_to_canonical.get(normalized, normalized)

            info = canonical_info.setdefault(
                canonical_norm,
                {
                    "display": display,
                    "category": category,
                    "variants": set(),
                    "is_single_char": normalized in SINGLE_CHAR_SKILLS,
                },
            )
            info["variants"].add(normalized)

            # Prefer the canonical form's own display name over an alias
            # display (e.g. "PostgreSQL" over "Postgres").
            if normalized == canonical_norm:
                info["display"] = display

    return canonical_info


def _count_canonical(
    text_lower: str,
    variants: set[str],
    is_single_char: bool,
) -> int:
    """
    Count non-overlapping occurrences of a canonical skill by matching its
    variants longest-first. Overlapping matches (e.g. "node" inside
    "node.js") are only counted once.
    """
    if is_single_char:
        tokens = _TOKEN_RE.findall(text_lower)
        return sum(
            1 for tok in tokens if tok in variants
        )

    ordered = sorted(variants, key=len, reverse=True)
    patterns = [
        (variant, _build_phrase_pattern(variant))
        for variant in ordered
    ]

    occupied: list[tuple[int, int]] = []
    count = 0

    for variant, pattern in patterns:
        for match in pattern.finditer(text_lower):
            start, end = match.span()

            # Skip if this span overlaps an already-counted (longer) match.
            overlaps = any(
                start < occ_end and end > occ_start
                for occ_start, occ_end in occupied
            )
            if overlaps:
                continue

            occupied.append((start, end))
            count += 1

    return count


def extract_skills(
    text: str,
    skills_section_text: str = "",
) -> ExtractionResult:
    """
    Extract and categorize skills from resume text.

    :param text:              Full raw resume text.
    :param skills_section_text: Optional text of the explicit "Skills" section,
                                used to boost confidence for explicit hits.
    :return: ExtractionResult with de-duplicated, normalized skills.
    """
    if not text:
        return ExtractionResult()

    text_lower = text.lower()
    skills_text_lower = (skills_section_text or "").lower()

    canonical_info = _collect_canonical_variants()

    results: list[ExtractedSkill] = []

    for canonical_norm, info in canonical_info.items():
        variants = info["variants"]
        is_single_char = info["is_single_char"]

        count = _count_canonical(text_lower, variants, is_single_char)

        if count == 0:
            continue

        # Determine whether the match came only via an alias (for the
        # confidence penalty). The canonical form itself is never an alias.
        canonical_is_alias = _is_alias_variant(canonical_norm, variants)

        # Detect an exact hit in the explicit skills section.
        exact_section_hit = False
        if skills_text_lower:
            exact_section_hit = _section_hit(
                skills_text_lower, variants, is_single_char
            )

        confidence = _confidence(count, exact_section_hit, canonical_is_alias)

        results.append(
            ExtractedSkill(
                skill=info["display"],
                normalized_skill=canonical_norm,
                category=info["category"],
                count=count,
                confidence=confidence,
            )
        )

    # Sort by count desc, then skill name asc for stable output.
    ordered = sorted(
        results,
        key=lambda s: (-s.count, s.normalized_skill),
    )

    return ExtractionResult(skills=ordered)


def _is_alias_variant(canonical_norm: str, variants: set[str]) -> bool:
    """
    Return True if the only way to match this canonical is via an alias
    (i.e. the canonical form itself is not a listed variant).
    """
    return canonical_norm not in variants


def _section_hit(
    text_lower: str,
    variants: set[str],
    is_single_char: bool,
) -> bool:
    """Check whether any variant of a canonical skill appears in a section."""
    if is_single_char:
        tokens = _TOKEN_RE.findall(text_lower)
        return any(tok in variants for tok in tokens)

    for variant in sorted(variants, key=len, reverse=True):
        if _build_phrase_pattern(variant).search(text_lower):
            return True

    return False


def _canonical_display(normalized: str) -> str:
    """
    Map a normalized canonical skill back to a display name.
    Prefers the canonical display casing from the dictionary.
    """
    for (norm, display), _category in CATEGORY_LOOKUP.items():
        if norm == normalized:
            return display

    # Fallback: title-case the normalized value.
    return " ".join(w.capitalize() for w in normalized.split())
