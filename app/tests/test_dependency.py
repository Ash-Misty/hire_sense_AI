from app.dependencies.database import get_db

db = next(get_db())

print(type(db))

db.close()