from app.database.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password

db = SessionLocal()

repo = UserRepository(db)

user = User(
    full_name="Ashini",
    email="ashini@gmail.com",
    hashed_password=hash_password("Ashini@123"),
)

saved_user = repo.create(user)

print(saved_user.id)
print(saved_user.email)

db.close()