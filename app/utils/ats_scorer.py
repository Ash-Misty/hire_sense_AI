"""
Module 8 — Deterministic, offline ATS (Applicant Tracking System) score engine.

This engine produces a single 0-100 ATS score and a structured, per-category
breakdown for a resume. It is intentionally:

  * Deterministic   -> the same input always yields the same output.
  * Offline         -> no external APIs or LLM calls.
  * Stateless       -> it does NOT touch the database or the API layer.

The engine accepts a plain, JSON-serializable "resume snapshot" and returns a
structured ``AtsReport``. All scoring weights are explicit constants so the
methodology is transparent and easy to tune.

The score is composed of five weighted categories:

  * contact_info        (15 pts) : name, email, phone presence.
  * content_completeness(30 pts) : summary, experience, education, skills.
  * skills_quality      (30 pts) : skill count, category diversity, confidence.
  * resume_length       (10 pts) : word count of the raw resume text.
  * other_signals       (15 pts) : projects, certifications, ATS keyword density.

The final score is clamped to [0, 100]. Duplicate skills are de-duplicated
before scoring so they cannot inflate the score.

NOTE: This is the ATS score, which measures general resume quality. Job-description
matching / semantic similarity is a separate concern handled by the future Job
Match module.
"""
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field

# --------------------------------------------------------------------------
# Scoring weights (max points per category). Sum = 100.
# --------------------------------------------------------------------------
CONTACT_MAX = 15.0
CONTENT_MAX = 30.0
SKILLS_MAX = 30.0
LENGTH_MAX = 10.0
SIGNALS_MAX = 15.0

# Sub-component maxima for the contact category.
CONTACT_NAME_MAX = 5.0
CONTACT_EMAIL_MAX = 5.0
CONTACT_PHONE_MAX = 5.0

# Content completeness components.
CONTENT_SUMMARY_MAX = 8.0
CONTENT_EXPERIENCE_MAX = 8.0
CONTENT_EDUCATION_MAX = 7.0
CONTENT_SKILLS_MAX = 7.0

# Skills quality behaviour.
SKILLS_TARGET_COUNT = 15          # points plateau once this many unique skills.
SKILLS_DIVERSITY_TARGET = 5       # fully rewarded at this many categories.
SKILLS_CONFIDENCE_TARGET = 0.8    # average confidence that scores full points.

# Resume length behaviour (word counts of raw text).
LENGTH_IDEAL_MIN = 400
LENGTH_IDEAL_MAX = 800
LENGTH_MIN_THRESHOLD = 100
LENGTH_MAX_THRESHOLD = 1500

# Keyword density behaviour. Keywords are general professional/ATS terms.
MIN_KEYWORD_DENSITY = 0.02        # 2% of words are keywords at full points.
MAX_KEYWORD_DENSITY = 0.05        # density above this is treated as full.

# A broad set of general professional/ATS-relevant keywords. This is NOT job
# specific; job-description matching is handled separately (Job Match module).
ATS_KEYWORDS = {
    "experience", "achieved", "managed", "developed", "designed", "implemented",
    "led", "created", "improved", "delivered", "team", "project", "responsible",
    "launched", "built", "coordinated", "collaborated", "mentored", "trained",
    "analyzed", "optimized", "scheduled", "budget", "customer", "client",
    "deadline", "quality", "results", "strategy", "launch", "cross-functional",
    "stakeholder", "initiative", "deliverable", "metrics", "deployed",
    "documentation", "requirements", "stakeholders", "roadmap", "scalable",
}


@dataclass
class CategoryScore:
    """Score for a single scoring category."""
    name: str
    score: float
    max_score: float
    weight: float                # max_score / 100
    feedback: list[str] = field(default_factory=list)


@dataclass
class AtsReport:
    """The full deterministic scoring report for one resume."""
    overall_score: float
    category_scores: list[CategoryScore]
    score_breakdown: dict
    feedback: list[str]

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the report."""
        return {
            "overall_score": self.overall_score,
            "category_scores": [
                asdict(c) for c in self.category_scores
            ],
            "score_breakdown": self.score_breakdown,
            "feedback": self.feedback,
        }


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp a value between low and high."""
    return round(max(low, min(value, high)), 2)


def _has(text: str | None) -> bool:
    """Return True if a value is non-empty text."""
    return bool(text and str(text).strip())


def _word_count(text: str | None) -> int:
    """Count the number of whitespace-separated words."""
    if not text:
        return 0
    return len(str(text).split())


def _compute_keyword_density(text: str | None) -> float:
    """
    Compute the ratio of ATS keywords to total words in the raw text.

    Returns a value in [0, 1]. A text with no words yields 0.0.
    """
    words = (text or "").lower().split()
    if not words:
        return 0.0
    hits = sum(1 for w in words if w.strip(".,;:!?()") in ATS_KEYWORDS)
    return hits / len(words)


# --------------------------------------------------------------------------
# Category scorers
# --------------------------------------------------------------------------
def _score_contact(name: str | None, email: str | None, phone: str | None) -> CategoryScore:
    feedback: list[str] = []
    score = 0.0

    if _has(name):
        score += CONTACT_NAME_MAX
    else:
        feedback.append("Add your full name to the resume.")

    if _has(email):
        score += CONTACT_EMAIL_MAX
    else:
        feedback.append("Add an email address for contact.")

    if _has(phone):
        score += CONTACT_PHONE_MAX
    else:
        feedback.append("Provide a phone number.")

    return CategoryScore(
        name="contact_info",
        score=round(score, 2),
        max_score=CONTACT_MAX,
        weight=CONTACT_MAX / 100,
        feedback=feedback,
    )


def _score_content(
    summary: str | None,
    experience: list | None,
    education: list | None,
    skills: list | None,
) -> CategoryScore:
    feedback: list[str] = []
    score = 0.0

    if _has(summary):
        score += CONTENT_SUMMARY_MAX
    else:
        feedback.append("Add a professional summary at the top.")

    if experience:
        score += CONTENT_EXPERIENCE_MAX
    else:
        feedback.append("Include a work experience section with roles and achievements.")

    if education:
        score += CONTENT_EDUCATION_MAX
    else:
        feedback.append("Add an education section.")

    if skills:
        score += CONTENT_SKILLS_MAX
    else:
        feedback.append("Add a skills section.")

    return CategoryScore(
        name="content_completeness",
        score=round(score, 2),
        max_score=CONTENT_MAX,
        weight=CONTENT_MAX / 100,
        feedback=feedback,
    )


def _score_skills(skills: list[dict]) -> CategoryScore:
    """
    Score the skills category.

    Skills are de-duplicated by their normalized_skill so duplicates cannot
    inflate the score. Points come from count, category diversity, and the
    average deterministic confidence.
    """
    feedback: list[str] = []

    # De-duplicate by normalized skill.
    unique: dict[str, dict] = {}
    for s in skills or []:
        key = s.get("normalized_skill") or s.get("skill") or ""
        unique[key] = s
    unique_list = list(unique.values())

    total = len(unique_list)

    # 1) Skill count (max 12 pts of the 30).
    count_pts = (total / SKILLS_TARGET_COUNT) * 12.0
    count_pts = min(count_pts, 12.0)

    # 2) Category diversity (max 10 pts of the 30).
    categories = {s.get("category", "Other") for s in unique_list}
    diversity_pts = (len(categories) / SKILLS_DIVERSITY_TARGET) * 10.0
    diversity_pts = min(diversity_pts, 10.0)

    # 3) Average confidence (max 8 pts of the 30).
    if unique_list:
        avg_conf = sum(float(s.get("confidence", 0.0)) for s in unique_list) / total
    else:
        avg_conf = 0.0
    conf_pts = (avg_conf / SKILLS_CONFIDENCE_TARGET) * 8.0
    conf_pts = min(conf_pts, 8.0)

    score = count_pts + diversity_pts + conf_pts

    if total == 0:
        feedback.append("Add technical and soft skills to boost your score.")
    else:
        if total < SKILLS_TARGET_COUNT:
            feedback.append(
                f"Add more skills to reach {SKILLS_TARGET_COUNT} unique skills "
                f"(currently {total})."
            )
        if len(categories) < SKILLS_DIVERSITY_TARGET:
            feedback.append(
                "Include skills from more categories (e.g. languages, frameworks, "
                "databases, cloud, soft skills)."
            )
        if avg_conf < SKILLS_CONFIDENCE_TARGET:
            feedback.append(
                "Make skill mentions concrete (e.g. in project descriptions) to "
                "increase their confidence."
            )

    return CategoryScore(
        name="skills_quality",
        score=round(score, 2),
        max_score=SKILLS_MAX,
        weight=SKILLS_MAX / 100,
        feedback=feedback,
    )


def _score_length(raw_text: str | None) -> CategoryScore:
    feedback: list[str] = []
    words = _word_count(raw_text)
    score = 0.0

    if words >= LENGTH_IDEAL_MIN and words <= LENGTH_IDEAL_MAX:
        score = LENGTH_MAX
    elif words < LENGTH_MIN_THRESHOLD:
        # Very short resumes get a proportional score.
        score = (words / LENGTH_MIN_THRESHOLD) * LENGTH_MAX * 0.6
        feedback.append(
            "Your resume is too short. Aim for 400–800 words of content."
        )
    elif words < LENGTH_IDEAL_MIN:
        # Ramp from threshold to ideal.
        score = LENGTH_MAX * (words / LENGTH_IDEAL_MIN)
        feedback.append(
            f"Add more detail to reach the ideal length of {LENGTH_IDEAL_MIN}+ words."
        )
    elif words > LENGTH_MAX_THRESHOLD:
        score = LENGTH_MAX * 0.7
        feedback.append(
            "Your resume is very long; consider trimming to 800 words or fewer."
        )
    else:
        # Between ideal max and the very-long threshold, taper slightly.
        score = LENGTH_MAX * (LENGTH_MAX_THRESHOLD - words) / (
            LENGTH_MAX_THRESHOLD - LENGTH_IDEAL_MAX
        )
        if words > LENGTH_IDEAL_MAX:
            feedback.append("Consider condensing to keep the resume concise.")

    return CategoryScore(
        name="resume_length",
        score=_clamp(score, 0, LENGTH_MAX),
        max_score=LENGTH_MAX,
        weight=LENGTH_MAX / 100,
        feedback=feedback,
    )


def _score_other_signals(
    projects: list | None,
    certifications: list | None,
    raw_text: str | None,
) -> CategoryScore:
    feedback: list[str] = []
    score = 0.0

    # Projects (max 6 pts).
    if projects:
        score += 6.0
    else:
        feedback.append("Add a projects section to showcase hands-on work.")

    # Certifications (max 4 pts).
    if certifications:
        score += 4.0
    else:
        feedback.append(
            "Include relevant certifications or professional training if applicable."
        )

    # Keyword density (max 5 pts).
    density = _compute_keyword_density(raw_text)
    if density >= MIN_KEYWORD_DENSITY:
        kw_pts = 5.0
    elif density > 0:
        kw_pts = 5.0 * (density / MIN_KEYWORD_DENSITY)
    else:
        kw_pts = 0.0
        feedback.append(
            "Use more action-oriented, achievement-based language "
            "(e.g. 'led', 'developed', 'improved')."
        )
    score += kw_pts

    return CategoryScore(
        name="other_signals",
        score=_clamp(score, 0, SIGNALS_MAX),
        max_score=SIGNALS_MAX,
        weight=SIGNALS_MAX / 100,
        feedback=feedback,
    )


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def compute_ats_score(
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    summary: str | None = None,
    skills: list[str] | None = None,
    education: list[dict] | None = None,
    experience: list[dict] | None = None,
    projects: list[dict] | None = None,
    certifications: list[str] | None = None,
    raw_text: str | None = None,
    extracted_skills: list[dict] | None = None,
) -> AtsReport:
    """
    Compute a deterministic ATS score for a resume snapshot.

    All inputs are plain JSON-serializable values. ``extracted_skills`` is a
    list of dicts with keys: skill, normalized_skill, category, count,
    confidence (from the Module 7 extractor). If ``extracted_skills`` is not
    provided, ``skills`` (a flat list of display names) is used instead.

    Returns an ``AtsReport`` with the overall score, per-category scores, a
    detailed score breakdown, and actionable feedback.
    """
    # Safely normalize lists.
    education = education or []
    experience = experience or []
    projects = projects or []
    certifications = certifications or []

    # Build extracted-skill dicts from the flat list when not provided.
    if extracted_skills is None:
        extracted_skills = [
            {
                "skill": s,
                "normalized_skill": " ".join(str(s).strip().lower().split()),
                "category": "Other",
                "count": 1,
                "confidence": 0.8,
            }
            for s in (skills or [])
        ]

    contact = _score_contact(name, email, phone)
    content = _score_content(summary, experience, education, skills)
    skills_cat = _score_skills(extracted_skills)
    length = _score_length(raw_text)
    signals = _score_other_signals(projects, certifications, raw_text)

    category_scores = [contact, content, skills_cat, length, signals]

    overall = sum(c.score for c in category_scores)
    overall = _clamp(overall)

    feedback: list[str] = []
    for c in category_scores:
        feedback.extend(c.feedback)

    score_breakdown = {
        "contact_info": {
            "score": contact.score,
            "max": CONTACT_MAX,
            "name": (name or "")[:255],
            "email": (email or "")[:255],
            "phone": (phone or "")[:64],
        },
        "content_completeness": {
            "score": content.score,
            "max": CONTENT_MAX,
            "has_summary": _has(summary),
            "experience_count": len(experience),
            "education_count": len(education),
            "skills_count": len(skills or []),
        },
        "skills_quality": {
            "score": skills_cat.score,
            "max": SKILLS_MAX,
            "unique_skill_count": len(
                {
                    s.get("normalized_skill") or s.get("skill") or ""
                    for s in extracted_skills
                }
            ),
            "category_count": len(
                {s.get("category", "Other") for s in extracted_skills}
            ),
        },
        "resume_length": {
            "score": length.score,
            "max": LENGTH_MAX,
            "word_count": _word_count(raw_text),
        },
        "other_signals": {
            "score": signals.score,
            "max": SIGNALS_MAX,
            "project_count": len(projects),
            "certification_count": len(certifications),
            "keyword_density": round(_compute_keyword_density(raw_text), 4),
        },
    }

    return AtsReport(
        overall_score=overall,
        category_scores=category_scores,
        score_breakdown=score_breakdown,
        feedback=feedback,
    )
