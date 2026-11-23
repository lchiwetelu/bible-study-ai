from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

