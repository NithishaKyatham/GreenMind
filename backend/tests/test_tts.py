import pytest

from app.core.config import settings
from app.services.tts_service import (
    AZURE_VOICE_BY_LOCALE,
    TTSUnavailableError,
    synthesize_speech,
    voice_for_locale,
)


@pytest.mark.parametrize("locale", ["en", "te", "hi", "ta", "kn", "mr", "ml", "bn", "gu", "pa"])
def test_all_supported_locales_have_azure_voices(locale):
    normalized, voice = voice_for_locale(locale)
    assert normalized == locale
    assert voice == AZURE_VOICE_BY_LOCALE[locale]


def test_unsupported_locale_falls_back_to_english_voice():
    assert voice_for_locale("xx") == ("en", AZURE_VOICE_BY_LOCALE["en"])


@pytest.mark.asyncio
async def test_missing_cloud_credentials_is_reported(monkeypatch):
    monkeypatch.setattr(settings, "AZURE_SPEECH_KEY", "")
    monkeypatch.setattr(settings, "AZURE_SPEECH_REGION", "")

    with pytest.raises(TTSUnavailableError):
        await synthesize_speech("Recommendation", "te")
