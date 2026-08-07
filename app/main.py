from fastapi import FastAPI
from app.api.v1.user import router as user_router
from app.api.v1 import auth_router
from app.api.v1 import resume_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)
@app.get("/")
def root():
    return {
        "message": "Welcome to HireSense AI"
    }


app.include_router(
    auth_router,
    prefix=settings.API_PREFIX,
)
app.include_router(
    user_router,
    prefix=settings.API_PREFIX,
)
app.include_router(
    resume_router,
    prefix=settings.API_PREFIX,
)
