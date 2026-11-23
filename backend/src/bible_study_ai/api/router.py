from fastapi import APIRouter

from bible_study_ai.api.health import router as health_router
from bible_study_ai.api.chat import router as chat_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(chat_router)