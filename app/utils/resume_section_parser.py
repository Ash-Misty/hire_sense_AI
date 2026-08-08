"""
Rule-based (Version 1) resume section parser.

This is a deterministic, offline parser intended as a solid base that can
later be replaced/extended by spaCy or a Transformer/LLM-based component
without impacting the rest of the application.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from app.utils.skill_dictionary import SKILL_LOOKUP


class ExtractedData(NamedTuple):
    name: str
    email: str
    phone: str
    summary: str
    skills: list[str]
    education: list[dict]
    experience: list[dict]
    projects: list[dict]
    certifications: list[str]


# --------------------------------------------------------------------------
# Contact regexes
# --------------------------------------------------------------------------
EMAIL_RE = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+"
)

PHONE_RE = re.compile(
    r"(?<!\d)(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{3,4}(?!\d)"
)


# --------------------------------------------------------------------------
# Section headers
# --------------------------------------------------------------------------
SECTION_HEADERS = {
    "summary": [
        "summary", "professional summary", "profile", "objective",
        "career objective", "about me", "overview",
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "technologies",
        "tech stack", "areas of expertise",
    ],
    "education": [
        "education", "academic background", "academics", "educational",
        "qualifications",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "career history", "work history",
    ],
    "projects": [
        "projects", "personal projects", "academic projects", "project work",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "certification",
    ],
}


def _normalize_header(line: str) -> str:
    """Lowercase a line and strip common trailing punctuation."""
    text = line.strip().lower().rstrip(":.")
    return " ".join(text.split())


def _match_section(line: str) -> str | None:
    """
    Return the canonical section name for a header line, or None.
    """
    normalized = _normalize_header(line)

    # A header should be short (few words) to reduce false positives.
    if len(normalized.split()) > 6:
        return None

    for section, headers in SECTION_HEADERS.items():
        if normalized in headers:
            return section

    return None


def _split_sections(text: str) -> list[tuple[str, str]]:
    """
    Split normalized resume text into a list of (section_name, content).

    Content before the first detected header is treated as a "contact" zone.
    """
    lines = [ln.strip() for ln in text.splitlines()]

    sections: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_name is not None:
            content = "\n".join(ln for ln in current_lines if ln)
            sections.append((current_name, content))
        current_lines.clear()

    for line in lines:
        section = _match_section(line)

        if section is not None:
            flush()
            current_name = section
        else:
            current_lines.append(line)

    if current_name is None:
        # No sections found: treat whole text as contact/unknown.
        content = "\n".join(ln for ln in lines if ln)
        sections.append(("contact", content))
    else:
        flush()

    return sections


def _extract_email(contact_text: str) -> str:
    match = EMAIL_RE.search(contact_text)
    return match.group(0).strip() if match else ""


def _extract_phone(contact_text: str) -> str:
    match = PHONE_RE.search(contact_text)
    return match.group(0).strip() if match else ""


def _extract_name(contact_text: str, email: str) -> str:
    """
    Heuristic name extraction from the contact zone.
    """
    lines = [
        ln for ln in contact_text.splitlines()
        if ln and not EMAIL_RE.search(ln) and not PHONE_RE.search(ln)
    ]

    for ln in lines[:2]:
        candidate = ln.strip()
        # Simple heuristic: 1-3 title-case words.
        words = candidate.split()
        if 1 <= len(words) <= 3 and all(
            w.istitle() or w in ("de", "da", "van", "von")
            for w in words
        ):
            return candidate

    if email:
        return email.split("@")[0].replace(".", " ").replace("_", " ").title()

    return ""


def _extract_skills(text: str) -> list[str]:
    """
    Match known technical skills against the full resume text using word
    boundaries. Preserves the display casing from the dictionary.

    Ignores single-character skills (e.g. "C", "R") unless they appear as
    standalone tokens to reduce false positives.
    """
    # Pre-tokenize once for single-char skill checks.
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9#+.\-+]*", text.lower()))

    found: list[str] = []

    for lookup, display in SKILL_LOOKUP:
        if len(lookup) == 1:
            # Single-char skills only count if they're a standalone token.
            if lookup in tokens and display not in found:
                found.append(display)
        else:
            pattern = re.compile(rf"\b{re.escape(lookup)}\b")
            if pattern.search(text.lower()) and display not in found:
                found.append(display)

    return found


def _extract_summary(section_text: str) -> str:
    """Clean up the summary section text."""
    lines = [
        ln.strip() for ln in section_text.splitlines()
        if ln.strip() and len(ln.strip()) > 3
    ]
    return " ".join(lines) if lines else ""


def _extract_education(section_text: str) -> list[dict]:
    """
    Extract education entries from the education section.
    Returns a list of dicts with keys like institution, degree, dates.
    Clusters text into separated chunks (by year ranges).
    """
    entries: list[dict] = []
    year_range = re.compile(r"(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}|(19|20)\d{2}")

    current: dict = {"text": ""}
    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

    for line in lines:
        if year_range.search(line) and current["text"]:
            entries.append(current)
            current = {"text": line}
        else:
            current["text"] = (current["text"] + " " + line).strip()

    if current["text"]:
        entries.append(current)

    return entries


def _extract_experience(section_text: str) -> list[dict]:
    """
    Extract experience entries. Clusters into chunks separated by
    date/year ranges.
    """
    entries: list[dict] = []
    date_range = re.compile(
        r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*"
        r"(19|20)\d{2}|(19|20)\d{2})\s*[-–—to]+\s*"
        r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*"
        r"(19|20)\d{2}|present|current|(19|20)\d{2})",
        re.IGNORECASE,
    )

    current: dict = {"text": ""}
    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

    for line in lines:
        if date_range.search(line) and current["text"]:
            entries.append(current)
            current = {"text": line}
        else:
            current["text"] = (current["text"] + " " + line).strip()

    if current["text"]:
        entries.append(current)

    return entries


def _extract_projects(section_text: str) -> list[dict]:
    """
    Extract project entries. Splits by bullet-like markers when present,
    otherwise treats the whole section as a single entry.
    """
    entries: list[dict] = []
    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

    current: dict = {"text": ""}

    for line in lines:
        is_bullet = re.match(r"^[•\-\*–]|^\d+[\.\)]|^o[\s]", line)
        if is_bullet and current["text"]:
            entries.append(current)
            current = {"text": re.sub(r"^[•\-\*–]\s*|\d+[\.\)]\s*", "", line)}
        else:
            current["text"] = (current["text"] + " " + line).strip()

    if current["text"]:
        entries.append(current)

    return entries


def _extract_certifications(section_text: str) -> list[str]:
    """Extract certification names from the certifications section."""
    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]
    return [re.sub(r"^[•\-\*–]\s*", "", ln) for ln in lines]


def parse_resume_text(text: str) -> ExtractedData:
    """
    Parse raw resume text into structured ExtractedData.

    This is intentionally defensive: any missing section simply yields empty
    values rather than failing the whole parse.
    """
    sections = dict(_split_sections(text))
    contact_text = sections.get("contact", "")

    email = _extract_email(contact_text or text)
    phone = _extract_phone(contact_text or text)
    name = _extract_name(contact_text, email)

    summary = _extract_summary(sections.get("summary", ""))
    skills = _extract_skills(text)

    education = _extract_education(sections.get("education", ""))
    experience = _extract_experience(sections.get("experience", ""))
    projects = _extract_projects(sections.get("projects", ""))
    certifications = _extract_certifications(
        sections.get("certifications", "")
    )

    return ExtractedData(
        name=name,
        email=email,
        phone=phone,
        summary=summary,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        certifications=certifications,
    )

