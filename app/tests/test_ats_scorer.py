"""
Module 8 — ATS scoring engine tests.

These tests exercise the deterministic, stateless scoring engine in
``app/utils/ats_scorer.py``. They do not require a database.
"""
from app.utils.ats_scorer import (
    ATS_KEYWORDS,
    CONTENT_MAX,
    CONTACT_MAX,
    LENGTH_MAX,
    SIGNALS_MAX,
    SKILLS_MAX,
    compute_ats_score,
)


def _extracted_skills(names, category="Programming Languages", confidence=0.8):
    return [
        {
            "skill": n,
            "normalized_skill": n.lower(),
            "category": category,
            "count": 1,
            "confidence": confidence,
        }
        for n in names
    ]


def _varied_category_skills():
    """Return skills spread across multiple categories."""
    return [
        {"skill": "Python", "normalized_skill": "python", "category": "Programming Languages", "count": 1, "confidence": 0.8},
        {"skill": "FastAPI", "normalized_skill": "fastapi", "category": "Frameworks & Libraries", "count": 1, "confidence": 0.8},
        {"skill": "Docker", "normalized_skill": "docker", "category": "Cloud & DevOps", "count": 1, "confidence": 0.8},
        {"skill": "PostgreSQL", "normalized_skill": "postgresql", "category": "Databases", "count": 1, "confidence": 0.8},
        {"skill": "Communication", "normalized_skill": "communication", "category": "Soft Skills", "count": 1, "confidence": 0.8},
    ]


COMPLETE = dict(
    name="John Doe",
    email="john@example.com",
    phone="+1-555-0000",
    summary="Experienced developer with leadership and project management skills.",
    skills=["Python", "FastAPI", "Docker", "PostgreSQL", "Git"],
    education=[{"degree": "BSc"}],
    experience=[{"role": "Engineer"}],
    projects=[{"name": "Project X"}],
    certifications=["AWS Certified"],
    raw_text=(" ".join(["led developed implemented team project improved "
                        "delivered results strategy roadmap"] * 40)),
    extracted_skills=_extracted_skills(
        ["Python", "FastAPI", "Docker", "PostgreSQL", "Git",
         "React", "AWS", "Kubernetes", "Communication", "SQL"]
    ),
)


def test_complete_resume_scores_high():
    report = compute_ats_score(**COMPLETE)
    assert report.overall_score >= 70


def test_empty_resume_scores_zero():
    report = compute_ats_score()
    assert report.overall_score == 0.0


def test_minimal_resume_scores_low():
    report = compute_ats_score(name="Jane", raw_text="Jane's resume.")
    assert report.overall_score < 50


def test_missing_name():
    r = dict(COMPLETE)
    r["name"] = None
    report = compute_ats_score(**r)
    contact = next(c for c in report.category_scores if c.name == "contact_info")
    assert contact.score == CONTACT_MAX - 5.0


def test_missing_email():
    r = dict(COMPLETE)
    r["email"] = None
    report = compute_ats_score(**r)
    contact = next(c for c in report.category_scores if c.name == "contact_info")
    assert contact.score == CONTACT_MAX - 5.0


def test_missing_phone():
    r = dict(COMPLETE)
    r["phone"] = None
    report = compute_ats_score(**r)
    contact = next(c for c in report.category_scores if c.name == "contact_info")
    assert contact.score == CONTACT_MAX - 5.0


def test_missing_summary():
    r = dict(COMPLETE)
    r["summary"] = None
    report = compute_ats_score(**r)
    content = next(c for c in report.category_scores if c.name == "content_completeness")
    assert content.score < CONTENT_MAX


def test_missing_experience():
    r = dict(COMPLETE)
    r["experience"] = []
    report = compute_ats_score(**r)
    content = next(c for c in report.category_scores if c.name == "content_completeness")
    assert content.score < CONTENT_MAX


def test_missing_education():
    r = dict(COMPLETE)
    r["education"] = []
    report = compute_ats_score(**r)
    content = next(c for c in report.category_scores if c.name == "content_completeness")
    assert content.score < CONTENT_MAX


def test_missing_skills():
    r = dict(COMPLETE)
    r["skills"] = []
    r["extracted_skills"] = []
    report = compute_ats_score(**r)
    content = next(c for c in report.category_scores if c.name == "content_completeness")
    assert content.score < CONTENT_MAX
    skills = next(c for c in report.category_scores if c.name == "skills_quality")
    assert skills.score == 0.0


def test_different_skill_counts():
    low = compute_ats_score(**dict(COMPLETE, extracted_skills=_extracted_skills(["Python"])))
    high = compute_ats_score(**dict(COMPLETE, extracted_skills=_extracted_skills(
        ["Python", "Java", "Go", "Rust", "C++", "SQL", "Docker", "AWS"])))
    low_skill = next(c for c in low.category_scores if c.name == "skills_quality")
    high_skill = next(c for c in high.category_scores if c.name == "skills_quality")
    assert high_skill.score > low_skill.score


def test_skill_category_diversity():
    single_cat = _extracted_skills(["Python", "Java", "Go"], category="Programming Languages")
    multi_cat = _varied_category_skills()
    a = compute_ats_score(**dict(COMPLETE, extracted_skills=single_cat))
    b = compute_ats_score(**dict(COMPLETE, extracted_skills=multi_cat))
    sa = next(c for c in a.category_scores if c.name == "skills_quality")
    sb = next(c for c in b.category_scores if c.name == "skills_quality")
    assert sb.score > sa.score


def test_skill_confidence():
    low_conf = compute_ats_score(**dict(COMPLETE, extracted_skills=_extracted_skills(
        ["Python", "Java", "Go"], confidence=0.3)))
    high_conf = compute_ats_score(**dict(COMPLETE, extracted_skills=_extracted_skills(
        ["Python", "Java", "Go"], confidence=0.9)))
    sl = next(c for c in low_conf.category_scores if c.name == "skills_quality")
    sh = next(c for c in high_conf.category_scores if c.name == "skills_quality")
    assert sh.score > sl.score


def test_duplicate_skills_do_not_inflate_score():
    dups = _extracted_skills(["Python", "Java", "Go"])
    many_dups = dups + _extracted_skills(["Python", "Java", "Go"]) * 5
    a = compute_ats_score(**dict(COMPLETE, extracted_skills=dups))
    b = compute_ats_score(**dict(COMPLETE, extracted_skills=many_dups))
    sa = next(c for c in a.category_scores if c.name == "skills_quality")
    sb = next(c for c in b.category_scores if c.name == "skills_quality")
    assert sb.score == sa.score


def test_short_resume():
    r = dict(COMPLETE)
    r["raw_text"] = "Short resume text."
    report = compute_ats_score(**r)
    length = next(c for c in report.category_scores if c.name == "resume_length")
    assert length.score < LENGTH_MAX


def test_normal_length_resume():
    r = dict(COMPLETE)
    r["raw_text"] = "word " * 500
    report = compute_ats_score(**r)
    length = next(c for c in report.category_scores if c.name == "resume_length")
    assert length.score == LENGTH_MAX


def test_very_long_resume():
    r = dict(COMPLETE)
    r["raw_text"] = "word " * 2000
    report = compute_ats_score(**r)
    length = next(c for c in report.category_scores if c.name == "resume_length")
    assert length.score < LENGTH_MAX


def test_projects_present_absent():
    r = dict(COMPLETE)
    r["projects"] = []
    report = compute_ats_score(**r)
    signals = next(c for c in report.category_scores if c.name == "other_signals")
    assert signals.score < SIGNALS_MAX


def test_certifications_present_absent():
    r = dict(COMPLETE)
    r["certifications"] = []
    report = compute_ats_score(**r)
    signals = next(c for c in report.category_scores if c.name == "other_signals")
    assert signals.score < SIGNALS_MAX


def test_keyword_density():
    rich = compute_ats_score(**dict(COMPLETE, raw_text=" led developed implemented improved results"))
    poor = compute_ats_score(**dict(COMPLETE, raw_text="the and or but of at for"))
    sr = next(c for c in rich.category_scores if c.name == "other_signals")
    sp = next(c for c in poor.category_scores if c.name == "other_signals")
    assert sr.score > sp.score


def test_score_always_between_0_and_100():
    cases = [
        COMPLETE,
        dict(COMPLETE, name=None, email=None, phone=None, raw_text=""),
        dict(COMPLETE, raw_text="word " * 3000),
        {},
    ]
    for case in cases:
        report = compute_ats_score(**case)
        assert 0.0 <= report.overall_score <= 100.0


def test_deterministic_same_input_same_score():
    a = compute_ats_score(**COMPLETE)
    b = compute_ats_score(**COMPLETE)
    assert a.overall_score == b.overall_score
    assert a.to_dict() == b.to_dict()


def test_feedback_is_returned():
    report = compute_ats_score()
    assert isinstance(report.feedback, list)
    assert len(report.feedback) > 0


def test_breakdown_contains_categories():
    report = compute_ats_score(**COMPLETE)
    assert set(report.score_breakdown.keys()) == {
        "contact_info",
        "content_completeness",
        "skills_quality",
        "resume_length",
        "other_signals",
    }
