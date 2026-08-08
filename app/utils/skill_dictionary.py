"""
Configurable technical-skill dictionary used by the rule-based resume parser.

Add or remove skills here to expand the set of recognized technologies.
Each entry is matched case-insensitively against the raw resume text.
"""

TECHNICAL_SKILLS: list[str] = [
    # Programming languages
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#",
    "Go", "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R",
    # Web frameworks
    "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "React",
    "React Native", "Vue", "Vue.js", "Angular", "Node.js", "Express",
    "Next.js", "GraphQL", "REST", "RESTful APIs",
    # Databases / storage
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
    "Oracle", "Cassandra", "Elasticsearch", "Firebase",
    # Cloud / DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "Ansible", "Jenkins", "CI/CD", "Git", "GitHub", "GitLab",
    "Nginx", "Linux",
    # Data / AI
    "Pandas", "NumPy", "TensorFlow", "PyTorch", "scikit-learn",
    "Keras", "Spark", "Hadoop", "Airflow", "NLP", "Machine Learning",
    "Deep Learning", "Data Science", "Data Analysis",
    # Testing / tools
    "Pytest", "JUnit", "Selenium", "Cypress", "Jira",
    # Others
    "Microservices", "System Design", "OOP", "Agile", "Scrum",
    "Kafka", "RabbitMQ",
]


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill for consistent matching (lowercase, trimmed).
    """
    return " ".join(skill.strip().lower().split())


SKILL_LOOKUP = [
    (normalize_skill(skill), skill)
    for skill in TECHNICAL_SKILLS
]

