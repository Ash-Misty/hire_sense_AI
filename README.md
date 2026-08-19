# HireSense AI

> **AI-powered resume analysis and job matching backend**

HireSense AI is a production-style FastAPI backend that provides resume parsing, deterministic skill extraction, ATS scoring, and job description matching. It is built with a clean layered architecture, uses PostgreSQL for persistence, and requires no external AI APIs for its core features.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Database Migrations](#database-migrations)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Architecture](#architecture)
- [License](#license)

---

## Features

| Module | Capability |
|--------|-----------|
| **Authentication** | Register, login, JWT access tokens, refresh tokens, logout, password change |
| **User Management** | View profile, update profile, delete account |
| **Resume Upload** | Upload PDF/DOCX resumes with secure file handling |
| **Resume Parsing** | Rule-based extraction of name, email, phone, skills, education, experience, projects, and certifications |
| **Skill Extraction** | Deterministic, offline skill extraction with 10 categories, alias normalization, frequency counting, and confidence scoring |
| **ATS Scoring** | Deterministic 0-100 score with category breakdown and actionable feedback |
| **Job Matching** | Compare resume skills against job descriptions; compute match percentage, matched/missing/extra skills, and category scores |
| **Security** | JWT-protected routes, bcrypt password hashing, user ownership enforcement on all resources |

All matching and scoring logic is **fully deterministic and offline** — no OpenAI APIs, embeddings, or external services are used.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | FastAPI 0.141.1 |
| **ORM** | SQLAlchemy 2.0.51 |
| **Database** | PostgreSQL (via psycopg 3.3.4) |
| **Migrations** | Alembic 1.18.5 |
| **Config** | pydantic-settings 2.14.2 |
| **Auth** | python-jose 3.5.0 (JWT), bcrypt 4.0.1 |
| **Parsing** | pypdf 6.15.0, python-docx 1.2.0 |
| **Uploads** | python-multipart 0.0.32 |
| **Testing** | pytest 9.1.1, httpx 0.28.1 |
| **Server** | uvicorn 0.52.0 |

---

## Project Structure

```
hire-sense-ai/
├── alembic/
│   └── versions/              # Database migration scripts
├── app/
│   ├── api/
│   │   └── v1/                # API routers
│   │       ├── auth.py        # Register, login, refresh, logout
│   │       ├── user.py        # Profile, update, delete, change password
│   │       ├── resume.py      # Upload, parse, skills, ATS score
│   │       └── job_matching.py # Job descriptions and matching
│   ├── core/
│   │   └── config.py          # Application settings
│   ├── database/
│   │   ├── base.py            # SQLAlchemy declarative base
│   │   └── session.py         # Engine and session factory
│   ├── dependencies/
│   │   ├── auth.py            # get_current_user JWT dependency
│   │   └── database.py        # get_db session dependency
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   ├── resume.py
│   │   ├── parsed_resume.py
│   │   ├── extracted_skill.py
│   │   ├── ats_score.py
│   │   ├── job_description.py
│   │   └── job_match.py
│   ├── repositories/          # Data access layer
│   │   ├── user_repository.py
│   │   ├── resume_repository.py
│   │   ├── parsed_resume_repository.py
│   │   ├── extracted_skill_repository.py
│   │   ├── ats_score_repository.py
│   │   ├── job_description_repository.py
│   │   └── job_match_repository.py
│   ├── schemas/               # Pydantic DTOs
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── resume.py
│   │   ├── parsed_resume.py
│   │   ├── extracted_skill.py
│   │   ├── ats_score.py
│   │   ├── job_description.py
│   │   └── job_match.py
│   ├── services/              # Business logic layer
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── resume_service.py
│   │   ├── resume_parser_service.py
│   │   ├── skill_extraction_service.py
│   │   ├── ats_score_service.py
│   │   └── job_matching_service.py
│   ├── utils/                 # Pure functions and parsers
│   │   ├── file_handler.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── resume_section_parser.py
│   │   ├── skill_dictionary.py
│   │   ├── skill_extractor.py
│   │   ├── ats_scorer.py
│   │   ├── job_skill_extractor.py
│   │   └── matching_engine.py
│   └── tests/                 # pytest test suite
│       ├── test_ats_scorer.py
│       ├── test_ats_score_service.py
│       ├── test_ats_score_repository.py
│       ├── test_ats_score_api.py
│       ├── test_skill_extraction.py
│       └── test_job_matching.py
├── uploads/                   # Uploaded resume storage
├── .env                       # Environment variables
├── alembic.ini                # Alembic configuration
├── requirements.txt           # Python dependencies
├── TODO.md                    # Development roadmap
├── MODULE9.md                 # Module 9 documentation
└── README.md                  # This file
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/hire-sense-ai.git
cd hire-sense-ai

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
.\venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and update the values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `HireSense AI` |
| `APP_VERSION` | Application version | `1.0.0` |
| `DEBUG` | Debug mode | `True` |
| `HOST` | Bind host | `127.0.0.1` |
| `PORT` | Bind port | `8000` |
| `API_PREFIX` | API route prefix | `/api/v1` |
| `SECRET_KEY` | JWT signing secret | *(generate a secure random string)* |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://user:pass@localhost:5432/hiresense_db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry | `30` |
| `ALGORITHM` | JWT algorithm | `HS256` |

---

## Database Migrations

Initialize and apply database schema:

```bash
# Generate a new migration (when models change)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

The project includes migrations for the following tables:
- `users`
- `refresh_tokens`
- `resumes`
- `parsed_resumes`
- `extracted_skills`
- `ats_scores`
- `job_descriptions`
- `job_matches`

---

## API Reference

The API is available under the `/api/v1` prefix. Once the server is running, interactive documentation is available at `/docs`.

### Base URL

```
http://127.0.0.1:8000/api/v1
```

### Authentication

All endpoints except registration and login require a Bearer JWT token.

```http
Authorization: Bearer <access_token>
```

### Endpoints

#### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `POST` | `/auth/logout` | Revoke refresh token |

#### Users

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/me` | Get current user profile |
| `PUT` | `/users/me` | Update profile |
| `DELETE` | `/users/me` | Delete account |
| `PUT` | `/users/change-password` | Change password |

#### Resumes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/resume/upload` | Upload PDF/DOCX resume |
| `GET` | `/resume` | List user's resumes |
| `POST` | `/resume/parse/{resume_id}` | Parse resume into structured data |
| `GET` | `/resume/parse/{resume_id}` | Retrieve parsed resume |
| `POST` | `/resume/{resume_id}/skills/extract` | Extract skills from resume |
| `GET` | `/resume/{resume_id}/skills` | List extracted skills |
| `GET` | `/resume/{resume_id}/skills/summary` | Skills grouped by category |
| `POST` | `/resume/{resume_id}/ats-score` | Compute ATS score |
| `GET` | `/resume/{resume_id}/ats-score` | Retrieve ATS score |
| `DELETE` | `/resume/{resume_id}` | Delete resume |

#### Job Matching

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/job/descriptions` | Create job description |
| `GET` | `/job/descriptions` | List user's job descriptions |
| `GET` | `/job/descriptions/{job_id}` | Get job description |
| `DELETE` | `/job/descriptions/{job_id}` | Delete job description |
| `POST` | `/job/resumes/{resume_id}/match/{job_id}` | Match resume against job |
| `GET` | `/job/matches` | Get match history |

---

## Testing

Run the full test suite:

```bash
pytest app/tests/ -v
```

Run a specific test file:

```bash
pytest app/tests/test_job_matching.py -v
```

The test suite covers:
- ATS scoring engine (unit tests)
- Skill extraction (unit + integration tests)
- Job matching (perfect match, partial match, zero match, extra skills, duplicates, user isolation)
- API endpoints (authentication, authorization, CRUD operations)

---

## Architecture

HireSense AI follows a clean layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  API Layer (app/api/v1/)                                    │
│  - Route definitions                                        │
│  - Request/response serialization                           │
├─────────────────────────────────────────────────────────────┤
│  Service Layer (app/services/)                              │
│  - Business logic orchestration                             │
│  - Ownership validation                                     │
│  - Cross-cutting concerns                                  │
├─────────────────────────────────────────────────────────────┤
│  Repository Layer (app/repositories/)                       │
│  - SQLAlchemy CRUD operations                               │
│  - Query scoping by user                                    │
├─────────────────────────────────────────────────────────────┤
│  Model Layer (app/models/)                                  │
│  - SQLAlchemy ORM definitions                               │
│  - PostgreSQL tables                                        │
├─────────────────────────────────────────────────────────────┤
│  Utility Layer (app/utils/)                                 │
│  - Pure, stateless functions                                │
│  - Parsing, extraction, scoring engines                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Deterministic matching**: No LLM or external API calls. Matching is based on rule-based skill extraction and set operations against a curated skill dictionary.
- **User isolation**: Every protected resource is scoped to the authenticated user. Cross-user access is blocked at the service layer.
- **Idempotent operations**: Re-running parsing, skill extraction, or scoring replaces previous results instead of creating duplicates.
- **JSONB storage**: Structured data (skills, scores, categories) is stored in PostgreSQL JSONB columns for efficient querying.

---

## Roadmap

- [x] Module 1 — Environment Setup
- [x] Module 2 — PostgreSQL + SQLAlchemy + Alembic
- [x] Module 3 — Authentication
- [x] Module 4 — User Management
- [x] Module 5 — Resume Upload
- [x] Module 6 — Resume Parser
- [x] Module 7 — Skill Extraction
- [x] Module 8 — ATS Score Engine
- [x] Module 9 — Job Description Matching
- [ ] Module 10 — Interview Question Generator
- [ ] Module 11 — Recruiter Dashboard
- [ ] Module 12 — Candidate Dashboard
- [ ] Module 13 — Email Services
- [ ] Module 14 — Docker
- [ ] Module 15 — Testing
- [ ] Module 16 — Deployment

---
