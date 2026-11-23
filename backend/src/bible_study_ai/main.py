from fastapi import FastAPI

from bible_study_ai.api.router import api_router
from bible_study_ai.config import settings

app = FastAPI(
    title=settings.app_name,
    description="An offline-first AI-powered Bible study companion",
    version="0.1.0",
)

app.include_router(api_router)