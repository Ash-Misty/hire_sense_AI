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

## Future Rounds (not yet started)
- [ ] Module 5: Resume Upload
- [ ] Module 6: Resume Parser (AI)
- [ ] Module 7: Skill Extraction
- [ ] Module 8: ATS Score Engine
- [ ] Module 9: Job Description Matching
- [ ] Module 10: Interview Question Generator
- [ ] Module 11: Recruiter Dashboard
- [ ] Module 12: Candidate Dashboard
- [ ] Module 13: Email Services
- [ ] Module 14: Docker
- [ ] Module 15: Testing
- [ ] Module 16: Deployment
