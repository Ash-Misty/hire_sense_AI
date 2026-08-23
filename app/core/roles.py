USER_ROLE_CANDIDATE = "candidate"
USER_ROLE_RECRUITER = "recruiter"
USER_ROLE_ADMIN = "admin"

VALID_ROLES = {USER_ROLE_CANDIDATE, USER_ROLE_RECRUITER, USER_ROLE_ADMIN}


def is_recruiter(user) -> bool:
    return getattr(user, "role", None) == USER_ROLE_RECRUITER


def is_admin(user) -> bool:
    return getattr(user, "role", None) == USER_ROLE_ADMIN


def has_recruiter_access(user) -> bool:
    return is_recruiter(user) or is_admin(user)
