from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.user import User
from app.services.tts_service import TTSUnavailableError, synthesize_speech

router = APIRouter(prefix="/tts", tags=["Text to Speech"])


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    locale: str = "en"


@router.post("/synthesize", response_class=Response)
async def synthesize(
    payload: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    del current_user
    try:
        audio = await synthesize_speech(payload.text, payload.locale)
    except TTSUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return Response(content=audio, media_type="audio/mpeg")
