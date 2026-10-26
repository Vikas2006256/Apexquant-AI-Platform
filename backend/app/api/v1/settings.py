from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings

router = APIRouter()

class SettingsUpdateSchema(BaseModel):
    openai_api_key: Optional[str] = ""
    gemini_api_key: Optional[str] = ""

@router.get("/")
def get_settings():
    return {
        "openai_api_key": settings.OPENAI_API_KEY,
        "gemini_api_key": settings.GEMINI_API_KEY,
    }

@router.put("/")
def update_settings(payload: SettingsUpdateSchema):
    settings.save_persisted_settings(
        openai_key=payload.openai_api_key or "",
        gemini_key=payload.gemini_api_key or ""
    )
    return {
        "status": "success",
        "message": "Settings updated successfully"
    }
