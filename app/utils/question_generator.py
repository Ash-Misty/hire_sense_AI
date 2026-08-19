"""
Module 10 — Deterministic interview question generator.

This module provides a pure, offline question-generation engine that produces
personalized interview questions from:

  * candidate skills
  * parsed resume data (summary, experience, education, projects)
  * job description match results (matched/missing skills)

No external APIs or LLMs are used. The output is fully deterministic for the
same input, making it easy to test and reason about.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from app.utils.skill_dictionary import SKILL_CATEGORIES, normalize_skill

# ---------------------------------------------------------------------------
# Centralized question categories
# ---------------------------------------------------------------------------

QUESTION_CATEGORIES = [
    "technical",
    "behavioral",
    "hr",
    "skill_based",
    "project_based",
    "experience_based",
    "job_specific",
]

# ---------------------------------------------------------------------------
# Difficulty levels
# ---------------------------------------------------------------------------

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# ---------------------------------------------------------------------------
# Question templates
# ---------------------------------------------------------------------------
# Each template is a tuple of (category, difficulty, template_string).
# Placeholders:
#   {skill}            — replaced with the skill display name
#   {project_skill}    — replaced with a project-related skill mention
#   {experience_area}  — replaced with experience/domain text
# ---------------------------------------------------------------------------

_TEMPLATES: list[tuple[str, str, str]] = [
    # Technical
    ("technical", "easy", "What is your experience with {skill}?"),
    ("technical", "easy", "Can you define what {skill} is used for?"),
    ("technical", "easy", "Have you used {skill} in any of your projects?"),
    ("technical", "medium", "Explain how you have used {skill} in a project."),
    ("technical", "medium", "What are the main advantages of using {skill}?"),
    ("technical", "medium", "What limitations have you encountered with {skill}?"),
    ("technical", "hard", "How would you architect a system using {skill}?"),
    ("technical", "hard", "What trade-offs did you consider when choosing {skill}?"),
    ("technical", "hard", "Describe a complex bug you debugged involving {skill}."),

    # Behavioral
    ("behavioral", "easy", "Tell me about a difficult technical problem you solved."),
    ("behavioral", "easy", "Describe a time you had to learn a new technology quickly."),
    ("behavioral", "medium", "Tell me about a time you disagreed with a team member. How did you handle it?"),
    ("behavioral", "medium", "Describe a project where you had to meet a tight deadline."),
    ("behavioral", "hard", "Tell me about a time you failed. What did you learn?"),
    ("behavioral", "hard", "Describe a situation where you had to influence a technical decision without authority."),

    # HR
    ("hr", "easy", "Tell me about yourself."),
    ("hr", "easy", "What are your career goals?"),
    ("hr", "medium", "Why are you interested in this position?"),
    ("hr", "medium", "What motivates you to stay in this field?"),
    ("hr", "hard", "Describe your ideal work environment and team culture."),
    ("hr", "hard", "Where do you see yourself in five years?"),

    # Skill-based
    ("skill_based", "easy", "Rate your proficiency with {skill}."),
    ("skill_based", "medium", "Walk me through a real-world scenario where you applied {skill}."),
    ("skill_based", "hard", "How do you stay up-to-date with changes in {skill}?"),
    ("skill_based", "hard", "What advanced features of {skill} have you used?"),

    # Project-based
    ("project_based", "easy", "Explain your project involving {project_skill}."),
    ("project_based", "medium", "What challenges did you face while developing this project?"),
    ("project_based", "medium", "How did you test and validate your project?"),
    ("project_based", "hard", "If you were to rebuild this project, what would you do differently?"),
    ("project_based", "hard", "How did you handle performance bottlenecks in your project?"),

    # Experience-based
    ("experience_based", "easy", "What was your role in your most recent project?"),
    ("experience_based", "medium", "Describe your experience working in an Agile team."),
    ("experience_based", "hard", "How have you mentored junior developers or contributed to code reviews?"),
    ("experience_based", "hard", "Tell me about a time you had to balance technical debt with feature delivery."),

    # Job-specific
    ("job_specific", "easy", "Why do you think you are a good fit for this role?"),
    ("job_specific", "medium", "Which of the required skills for this role do you feel strongest about?"),
    ("job_specific", "hard", "How would you approach learning a skill required for this role that you have not used before?"),
]

# Seed for deterministic selection
_RNG = random.Random(42)


@dataclass
class Question:
    """Single generated interview question."""

    question: str
    category: str
    skill: str | None
    difficulty: str


def _normalize_skill(skill: str) -> str:
    return " ".join(skill.strip().lower().split())


def _get_display_skill(skill: str) -> str:
    """Return the canonical display name for a skill if known, else title-case it."""
    normalized = _normalize_skill(skill)
    for category_skills in SKILL_CATEGORIES.values():
        for s in category_skills:
            if _normalize_skill(s) == normalized:
                return s
    return " ".join(w.capitalize() for w in normalized.split())


def _generate_technical_questions(
    skills: Sequence[str],
    count: int = 3,
) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    skill_pool = list(dict.fromkeys(skills))

    for skill in skill_pool:
        display = _get_display_skill(skill)
        for category, difficulty, template in _TEMPLATES:
            if category != "technical":
                continue
            text = template.replace("{skill}", display)
            if text not in seen:
                seen.add(text)
                questions.append(
                    Question(
                        question=text,
                        category=category,
                        skill=display,
                        difficulty=difficulty,
                    )
                )
            if len(questions) >= count:
                break
        if len(questions) >= count:
            break

    return questions[:count]


def _generate_behavioral_questions(count: int = 2) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    for category, difficulty, template in _TEMPLATES:
        if category != "behavioral":
            continue
        if template not in seen:
            seen.add(template)
            questions.append(
                Question(
                    question=template,
                    category=category,
                    skill=None,
                    difficulty=difficulty,
                )
            )
        if len(questions) >= count:
            break
    return questions[:count]


def _generate_hr_questions(count: int = 2) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    for category, difficulty, template in _TEMPLATES:
        if category != "hr":
            continue
        if template not in seen:
            seen.add(template)
            questions.append(
                Question(
                    question=template,
                    category=category,
                    skill=None,
                    difficulty=difficulty,
                )
            )
        if len(questions) >= count:
            break
    return questions[:count]


def _generate_skill_based_questions(
    skills: Sequence[str],
    count: int = 3,
) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    skill_pool = list(dict.fromkeys(skills))

    for skill in skill_pool:
        display = _get_display_skill(skill)
        for category, difficulty, template in _TEMPLATES:
            if category != "skill_based":
                continue
            text = template.replace("{skill}", display)
            if text not in seen:
                seen.add(text)
                questions.append(
                    Question(
                        question=text,
                        category=category,
                        skill=display,
                        difficulty=difficulty,
                    )
                )
            if len(questions) >= count:
                break
        if len(questions) >= count:
            break

    return questions[:count]


def _generate_project_based_questions(
    skills: Sequence[str],
    count: int = 2,
) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    skill_pool = list(dict.fromkeys(skills))

    for skill in skill_pool:
        display = _get_display_skill(skill)
        for category, difficulty, template in _TEMPLATES:
            if category != "project_based":
                continue
            text = template.replace("{project_skill}", display)
            if text not in seen:
                seen.add(text)
                questions.append(
                    Question(
                        question=text,
                        category=category,
                        skill=display,
                        difficulty=difficulty,
                    )
                )
            if len(questions) >= count:
                break
        if len(questions) >= count:
            break

    return questions[:count]


def _generate_experience_based_questions(count: int = 2) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    for category, difficulty, template in _TEMPLATES:
        if category != "experience_based":
            continue
        if template not in seen:
            seen.add(template)
            questions.append(
                Question(
                    question=template,
                    category=category,
                    skill=None,
                    difficulty=difficulty,
                )
            )
        if len(questions) >= count:
            break
    return questions[:count]


def _generate_job_specific_questions(
    job_skills: Sequence[str],
    count: int = 3,
) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    skill_pool = list(dict.fromkeys(job_skills))

    if not skill_pool:
        return questions

    for skill in skill_pool:
        display = _get_display_skill(skill)
        for category, difficulty, template in _TEMPLATES:
            if category != "job_specific":
                continue
            text = template.replace("{skill}", display)
            if text not in seen:
                seen.add(text)
                questions.append(
                    Question(
                        question=text,
                        category=category,
                        skill=display,
                        difficulty=difficulty,
                    )
                )
            if len(questions) >= count:
                break
        if len(questions) >= count:
            break

    return questions[:count]


def generate_questions(
    candidate_skills: Sequence[str],
    parsed_resume: dict | None = None,
    job_description: str | None = None,
    job_match: dict | None = None,
    max_questions: int = 15,
) -> list[dict]:
    """
    Generate a deterministic list of interview questions.

    Parameters
    ----------
    candidate_skills:
        List of skills extracted from the candidate's resume.
    parsed_resume:
        Optional dict with keys like ``summary``, ``experience``, ``projects``,
        ``education``.
    job_description:
        Optional raw job description text.
    job_match:
        Optional dict from the matching engine containing ``matched_skills``,
        ``missing_skills``, ``extra_skills``.
    max_questions:
        Maximum number of questions to return.

    Returns
    -------
    list[dict]
        Each dict contains ``question``, ``category``, ``skill``, ``difficulty``.
    """
    if max_questions <= 0:
        return []

    skills = [str(s) for s in candidate_skills if s]
    job_skills: list[str] = []
    if job_match:
        matched = job_match.get("matched_skills", [])
        missing = job_match.get("missing_skills", [])
        job_skills = [str(s) for s in matched + missing if s]

    # Fallback: derive job skills from raw JD text if no job_match provided
    if not job_skills and job_description:
        from app.utils.job_skill_extractor import extract_job_skills
        job_skills = extract_job_skills(job_description)

    questions: list[Question] = []

    # Distribute counts across categories deterministically.
    # Base allocations.
    alloc_technical = max(1, min(3, len(skills), max_questions // 5))
    alloc_behavioral = 2
    alloc_hr = 2
    alloc_skill = max(1, min(3, len(skills), max_questions // 5))
    alloc_project = max(1, min(2, len(skills), max_questions // 6))
    alloc_experience = 2
    alloc_job = max(1, min(3, len(job_skills), max_questions // 5))

    total_alloc = (
        alloc_technical
        + alloc_behavioral
        + alloc_hr
        + alloc_skill
        + alloc_project
        + alloc_experience
        + alloc_job
    )

    if total_alloc > max_questions:
        overflow = total_alloc - max_questions
        weights = [
            ("alloc_job", alloc_job),
            ("alloc_project", alloc_project),
            ("alloc_experience", alloc_experience),
            ("alloc_hr", alloc_hr),
            ("alloc_behavioral", alloc_behavioral),
            ("alloc_skill", alloc_skill),
            ("alloc_technical", alloc_technical),
        ]
        total_weight = sum(w for _, w in weights)
        if total_weight > 0:
            reductions: dict[str, int] = {}
            remaining = overflow
            for name, weight in weights:
                if remaining <= 0:
                    break
                reduction = max(0, round(overflow * weight / total_weight))
                reductions[name] = reduction
                remaining -= reduction
            # Adjust for rounding errors.
            diff = overflow - sum(reductions.values())
            for name, _ in weights:
                if diff <= 0:
                    break
                reductions[name] = min(reductions.get(name, 0) + 1, weight)
                diff -= 1
            alloc_job = max(0, alloc_job - reductions.get("alloc_job", 0))
            alloc_project = max(0, alloc_project - reductions.get("alloc_project", 0))
            alloc_experience = max(0, alloc_experience - reductions.get("alloc_experience", 0))
            alloc_hr = max(0, alloc_hr - reductions.get("alloc_hr", 0))
            alloc_behavioral = max(0, alloc_behavioral - reductions.get("alloc_behavioral", 0))
            alloc_skill = max(0, alloc_skill - reductions.get("alloc_skill", 0))
            alloc_technical = max(0, alloc_technical - reductions.get("alloc_technical", 0))

    questions.extend(_generate_technical_questions(skills, alloc_technical))
    questions.extend(_generate_behavioral_questions(alloc_behavioral))
    questions.extend(_generate_hr_questions(alloc_hr))
    questions.extend(_generate_skill_based_questions(skills, alloc_skill))
    questions.extend(_generate_project_based_questions(skills, alloc_project))
    questions.extend(_generate_experience_based_questions(alloc_experience))
    questions.extend(_generate_job_specific_questions(job_skills, alloc_job))

    # Deduplicate by question text while preserving order.
    seen_texts: set[str] = set()
    unique: list[Question] = []
    for q in questions:
        if q.question not in seen_texts:
            seen_texts.add(q.question)
            unique.append(q)

    return [
        {
            "question": q.question,
            "category": q.category,
            "skill": q.skill,
            "difficulty": q.difficulty,
        }
        for q in unique[:max_questions]
    ]
