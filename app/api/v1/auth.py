from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterResponse
from app.schemas.auth import UserRegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
)
def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db),
):

    repository = UserRepository(db)

    service = AuthService(repository)

    user = service.register_user(user_data)

    return user