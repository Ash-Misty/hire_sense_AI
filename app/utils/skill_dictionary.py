"""
Configurable technical-skill dictionary used by the rule-based resume parser
and the Module 7 skill extractor.

Skills are organized into categories so that the extractor can produce
structured, categorized output that later feeds the ATS score engine and
job-description matching modules.

This module exports:
  - ``TECHNICAL_SKILLS``   : flat list of skills (backward compatible).
  - ``SKILL_LOOKUP``       : list of ``(normalized, display)`` pairs (backward
                             compatible).
  - ``SKILL_CATEGORIES``   : ``{category: [skill, ...]}``.
  - ``CATEGORY_LOOKUP``    : ``{(normalized_skill, canonical): category}``.
  - ``SKILL_ALIASES``      : ``{canonical_skill: set_of_aliases}``.
  - ``SINGLE_CHAR_SKILLS`` : set of single-character skills that only count as
                             standalone tokens.
"""

# --------------------------------------------------------------------------
# Skill categories
# --------------------------------------------------------------------------
SKILL_CATEGORIES: dict[str, list[str]] = {
    "Programming Languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#",
        "Go", "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R",
        "Perl", "Haskell", "Dart", "Objective-C", "Visual Basic",
        "Assembly", "Elixir", "Erlang", "Bash", "Shell",
    ],
    "Web Technologies": [
        "HTML", "HTML5", "CSS", "CSS3", "Sass", "SCSS", "Less",
        "Bootstrap", "Tailwind", "Tailwind CSS", "jQuery", "AJAX",
        "DOM", "WebSockets", "REST", "RESTful APIs", "GraphQL",
        "gRPC", "JSON", "XML", "YAML", "HTTP", "HTTPS",
    ],
    "Frameworks & Libraries": [
        "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "React",
        "React Native", "Vue", "Vue.js", "Angular", "AngularJS",
        "Next.js", "Nuxt.js", "Node", "Node.js", "Express", "Express.js",
        "Ruby on Rails", "Laravel", "ASP.NET", ".NET", ".NET Core",
        "Pandas", "NumPy", "PyTorch", "TensorFlow", "Keras", "scikit-learn",
        "OpenCV", "NLTK", "spaCy", "Hibernate", "Maven", "Gradle",
        "jQuery",
    ],
    "Databases": [
        "SQL", "MySQL", "PostgreSQL", "Postgres", "MongoDB", "Redis",
        "SQLite", "Oracle", "Cassandra", "Elasticsearch", "Firebase",
        "DynamoDB", "MariaDB", "MS SQL Server", "SQL Server",
        "Neo4j", "InfluxDB", "CouchDB", "Memcached", "BigQuery",
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes",
        "K8s", "Terraform", "Ansible", "Jenkins", "CI/CD", "Git",
        "GitHub", "GitLab", "Bitbucket", "Nginx", "Linux", "Unix",
        "Prometheus", "Grafana", "ArgoCD", "CloudFormation", "Helm",
        "Vagrant", "CircleCI", "GitHub Actions",
    ],
    "AI & Machine Learning": [
        "Machine Learning", "Deep Learning", "Neural Networks", "NLP",
        "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
        "Transformers", "GPT", "LLM", "Large Language Models",
        "TensorFlow", "PyTorch", "Keras", "scikit-learn", "XGBoost",
        "LightGBM", "OpenAI", "Hugging Face", "Ollama", "RAG",
    ],
    "Data Science": [
        "Data Science", "Data Analysis", "Data Engineering", "Data Modeling",
        "Statistics", "Data Visualization", "Pandas", "NumPy", "SQL",
        "Spark", "Hadoop", "Airflow", "Big Data", "ETL", "A/B Testing",
        "Tableau", "Power BI", "Matplotlib", "Seaborn", "Kafka",
        "Snowflake", "Databricks",
    ],
    "Testing & Tools": [
        "Pytest", "JUnit", "Selenium", "Cypress", "Playwright",
        "Jest", "Mocha", "Chai", "Postman", "Insomnia", "Jira",
        "Confluence", "Sourcetree", "Git", "npm", "Yarn", "pip",
        "Webpack", "Vite", "Babel", "ESLint", "Prettier", "Docker",
    ],
    "Soft Skills": [
        "Communication", "Leadership", "Teamwork", "Collaboration",
        "Problem Solving", "Critical Thinking", "Time Management",
        "Agile", "Scrum", "Project Management", "Mentoring", "Adaptability",
        "Creativity", "Attention to Detail", "Stakeholder Management",
        "Negotiation", "Presentation", "Public Speaking",
    ],
    "Other": [
        "Microservices", "System Design", "OOP", "Design Patterns",
        "REST", "GraphQL", "Agile", "Scrum", "Kafka", "RabbitMQ",
        "SOLID", "TDD", "BDD", "CI/CD", "Linux", "Git",
    ],
}

# --------------------------------------------------------------------------
# Aliases: canonical skill -> set of accepted aliases (all lowercased)
# --------------------------------------------------------------------------
SKILL_ALIASES: dict[str, set[str]] = {
    "React": {"react", "reactjs", "react.js", "react js"},
    "Node.js": {"node", "nodejs", "node.js", "node js"},
    "Express": {"express", "expressjs", "express.js", "express js"},
    "PostgreSQL": {"postgresql", "postgres"},
    "Vue.js": {"vue", "vuejs", "vue.js", "vue js"},
    "Angular": {"angular", "angular2", "angularjs", "angular 2"},
    "Kubernetes": {"kubernetes", "k8s"},
    "Machine Learning": {"machine learning", "ml"},
    "Deep Learning": {"deep learning", "dl"},
    "Natural Language Processing": {
        "natural language processing", "nlp",
    },
    "JavaScript": {"javascript", "js"},
    "TypeScript": {"typescript", "ts"},
    "scikit-learn": {"scikit-learn", "scikit learn", "sklearn"},
    "C++": {"c++", "cpp"},
    "C#": {"c#", "csharp"},
    "SQL Server": {"ms sql server", "sql server", "mssql"},
    "Git": {"git", "github"},
}

# --------------------------------------------------------------------------
# Derived structures
# --------------------------------------------------------------------------

def normalize_skill(skill: str) -> str:
    """Normalize a skill for consistent matching (lowercase, trimmed)."""
    return " ".join(skill.strip().lower().split())


# Backward-compatible flat list.
TECHNICAL_SKILLS: list[str] = [
    skill
    for skills in SKILL_CATEGORIES.values()
    for skill in skills
]

# Backward-compatible (normalized, display) pairs.
SKILL_LOOKUP = [
    (normalize_skill(skill), skill)
    for skill in TECHNICAL_SKILLS
]

# (normalized_skill, display_name) -> category
CATEGORY_LOOKUP = {
    (normalize_skill(skill), skill): category
    for category, skills in SKILL_CATEGORIES.items()
    for skill in skills
}

# Single-character skills only count when they appear as standalone tokens.
SINGLE_CHAR_SKILLS: set[str] = {
    normalize_skill(s)
    for s in TECHNICAL_SKILLS
    if len(normalize_skill(s)) == 1
}

