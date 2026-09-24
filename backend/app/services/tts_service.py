"""Server-side text-to-speech integration for localized recommendations."""
import html
from typing import Optional

import httpx

from app.core.config import settings
from app.services.recommendation_service import normalize_locale

AZURE_VOICE_BY_LOCALE = {
    "en": "en-IN-NeerjaNeural",
    "te": "te-IN-ShrutiNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-PallaviNeural",
    "kn": "kn-IN-SapnaNeural",
    "mr": "mr-IN-AarohiNeural",
    "ml": "ml-IN-SobhanaNeural",
    "bn": "bn-IN-TanishaaNeural",
    "gu": "gu-IN-DhwaniNeural",
    "pa": "pa-IN-OjasNeural",
}


class TTSUnavailableError(Exception):
    pass


def voice_for_locale(locale: Optional[str]) -> tuple[str, str]:
    normalized = normalize_locale(locale)
    return normalized, AZURE_VOICE_BY_LOCALE[normalized]


async def synthesize_speech(text: str, locale: Optional[str]) -> bytes:
    if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
        raise TTSUnavailableError("Cloud speech is not configured.")

    if not text.strip():
        raise TTSUnavailableError("Speech text cannot be empty.")

    if len(text) > settings.TTS_MAX_TEXT_LENGTH:
        raise TTSUnavailableError("Speech text is too long.")

    normalized, voice = voice_for_locale(locale)
    endpoint = (
        f"https://{settings.AZURE_SPEECH_REGION}.tts.speech.microsoft.com/"
        "cognitiveservices/v1"
    )
    ssml = (
        f"<speak version='1.0' xml:lang='{normalized}-IN'>"
        f"<voice name='{voice}'>{html.escape(text)}</voice>"
        "</speak>"
    )

    try:
        async with httpx.AsyncClient(timeout=settings.TTS_TIMEOUT_SECONDS) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
                },
                content=ssml.encode("utf-8"),
            )
            response.raise_for_status()
            return response.content
    except (httpx.HTTPError, OSError) as exc:
        raise TTSUnavailableError("Cloud speech is temporarily unavailable.") from exc
