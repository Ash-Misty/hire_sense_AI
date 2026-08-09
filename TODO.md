# HireSense AI — Backend Roadmap Progress

## Round 1: Finish Module 3 (Auth) + Module 4 (User Management)

- [x] 1. Add `REFRESH_TOKEN_EXPIRE_DAYS` to `app/core/config.py`
- [x] 2. Add `create_refresh_token()` to `app/core/security.py`
- [x] 3. Create `app/models/refresh_token.py` (RefreshToken model)
- [x] 4. Register model in `app/models/__init__.py`
- [x] 5. Create `app/repositories/refresh_token_repository.py`
- [x] 6. Add `ChangePasswordRequest` to `app/schemas/auth.py`
- [x] 7. Add `refresh_token` to `TokenResponse` in `app/schemas/login.py`
- [x] 8. Add `UserUpdateRequest` to `app/schemas/user.py`
- [x] 9. Update `app/services/auth_service.py` (login issues refresh, change_password, refresh_token, logout)
- [x] 10. Create `app/services/user_service.py` (update_profile, delete_account)
- [x] 11. Update `app/api/v1/auth.py` (POST /refresh, POST /logout)
- [x] 12. Update `app/api/v1/user.py` (PUT /users/me, DELETE /users/me, PUT /users/change-password)
- [x] 13. Create Alembic migration for `refresh_tokens` table
- [x] 14. Apply migration to database (`alembic upgrade head`)
- [x] 15. Verify routers in `app/main.py`

## Round 2: Module 5 (Resume Upload)

- [x] 1. Add upload settings to `app/core/config.py` (`MAX_UPLOAD_SIZE_MB`, `UPLOAD_DIR`)
- [x] 2. Create `app/models/resume.py` (Resume model)
- [x] 3. Register model in `app/models/__init__.py`
- [x] 4. Create `app/schemas/resume.py` (ResumeResponse, ResumeUploadResponse, ResumeListResponse)
- [x] 5. Register schemas in `app/schemas/__init__.py`
- [x] 6. Create `app/utils/file_handler.py` (secure file save + validation)
- [x] 7. Create `app/repositories/resume_repository.py`
- [x] 8. Create `app/services/resume_service.py`
- [x] 9. Create `app/api/v1/resume.py` (POST /resume/upload, GET /resume, DELETE /resume/{id})
- [x] 10. Register router in `app/api/v1/__init__.py`
- [x] 11. Register router in `app/main.py`
- [x] 12. Create Alembic migration for `resumes` table
- [x] 13. Apply migration to database (`alembic upgrade head`)
- [x] 14. Install `python-multipart` and add to `requirements.txt`
- [x] 15. Verify app startup

## Round 3: Module 6 (Resume Parser - AI)

- [x] 1. Add `pypdf` and `python-docx` to `requirements.txt`
- [x] 2. Create `app/utils/pdf_parser.py` (PDF text extraction)
- [x] 3. Create `app/utils/docx_parser.py` (DOCX text extraction)
- [x] 4. Create `app/utils/resume_section_parser.py` (section detection + regex extraction)
- [x] 5. Create `app/utils/skill_dictionary.py` (configurable skill dictionary)
- [x] 6. Create `app/models/parsed_resume.py` (ParsedResume model)
- [x] 7. Register model in `app/models/__init__.py`
- [x] 8. Create `app/schemas/parsed_resume.py` (Pydantic schemas)
- [x] 9. Register schemas in `app/schemas/__init__.py`
- [x] 10. Create `app/repositories/parsed_resume_repository.py`
- [x] 11. Create `app/services/resume_parser_service.py` (orchestrator)
- [x] 12. Update `app/api/v1/resume.py` (POST /resume/parse/{resume_id}, GET /resume/parse/{resume_id})
- [x] 13. Create Alembic migration for `parsed_resumes` table
- [x] 14. Apply migration to database (`alembic upgrade head`)
- [x] 15. Install dependencies (`pip install pypdf python-docx`)
- [x] 16. Verify app startup
- [x] 17. Update `TODO.md` (mark Module 6 complete)
- [x] 18. Create `MODULE6.md` task tracker

## Round 4: Module 7 (Skill Extraction)

- [x] 1. Enhance `app/utils/skill_dictionary.py` (categorized skills, aliases, normalized names)
- [x] 2. Create `app/utils/skill_extractor.py` (extraction engine with count + deterministic confidence)
- [x] 3. Create `app/models/extracted_skill.py` (ExtractedSkill model)
- [x] 4. Register model in `app/models/__init__.py`
- [x] 5. Create `app/schemas/extracted_skill.py` (Pydantic schemas)
- [x] 6. Register schemas in `app/schemas/__init__.py`
- [x] 7. Create `app/repositories/extracted_skill_repository.py`
- [x] 8. Create `app/services/skill_extraction_service.py` (orchestrator)
- [x] 9. Update `app/api/v1/resume.py` (POST /skills/extract, GET /skills, GET /skills/summary)
- [x] 10. Create Alembic migration for `extracted_skills` table
- [x] 11. Apply migration to database (`alembic upgrade head`)
- [x] 12. Add tests for skill extraction
- [x] 13. Create `MODULE7.md` task tracker
- [x] 14. Update `TODO.md` (mark Module 7 complete)

## Future Rounds (not yet started)
- [ ] Module 8: ATS Score Engine
- [ ] Module 9: Job Description Matching
- [ ] Module 10: Interview Question Generator
- [ ] Module 11: Recruiter Dashboard
- [ ] Module 12: Candidate Dashboard
- [ ] Module 13: Email Services
- [ ] Module 14: Docker
- [ ] Module 15: Testing
- [ ] Module 16: Deployment
