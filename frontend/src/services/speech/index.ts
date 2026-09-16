import { SpeechRecognitionService, TextToSpeechService, SttProviderName, TtsProviderName } from "./types";
import { WebSpeechRecognitionService, WebSpeechTextToSpeechService } from "./webSpeechProvider";
import { WhisperSpeechRecognitionService } from "./whisperProvider";
import { AzureSpeechRecognitionService, AzureTextToSpeechService } from "./azureProvider";

/**
 * Single place that decides which speech provider is active. Nothing
 * outside this file should import a concrete provider class directly —
 * components and hooks only ever see the SpeechRecognitionService /
 * TextToSpeechService interfaces from ./types.
 *
 * Selection order:
 *   1. An explicit override passed by the caller (mainly for tests).
 *   2. VITE_STT_PROVIDER / VITE_TTS_PROVIDER env vars, if set.
 *   3. Default: "browser" (Web Speech API — no key, no network dependency).
 *
 * If the selected provider reports itself unsupported (e.g. "azure" was
 * requested but VITE_AZURE_SPEECH_KEY isn't set, or the browser lacks
 * MediaRecorder), this factory automatically falls back to the browser
 * provider rather than leaving the caller with a dead provider — this is
 * the "graceful fallback" behavior called for in the spec, one level
 * below the UI's own "voice not supported, type instead" messaging.
 */

function readEnv(name: string): string | undefined {
  return (import.meta as any).env?.[name];
}

export function createSpeechRecognitionService(
  providerOverride?: SttProviderName
): SpeechRecognitionService {
  const requested = providerOverride || (readEnv("VITE_STT_PROVIDER") as SttProviderName | undefined) || "browser";

  let service: SpeechRecognitionService;
  switch (requested) {
    case "whisper":
      service = new WhisperSpeechRecognitionService();
      break;
    case "azure":
      service = new AzureSpeechRecognitionService();
      break;
    case "browser":
    default:
      service = new WebSpeechRecognitionService();
      break;
  }

  if (!service.isSupported() && requested !== "browser") {
    const fallback = new WebSpeechRecognitionService();
    if (fallback.isSupported()) return fallback;
  }
  return service;
}

export function createTextToSpeechService(
  providerOverride?: TtsProviderName
): TextToSpeechService {
  const requested = providerOverride || (readEnv("VITE_TTS_PROVIDER") as TtsProviderName | undefined) || "browser";

  let service: TextToSpeechService;
  switch (requested) {
    case "azure":
      service = new AzureTextToSpeechService();
      break;
    case "browser":
    default:
      service = new WebSpeechTextToSpeechService();
      break;
  }

  if (!service.isSupported() && requested !== "browser") {
    const fallback = new WebSpeechTextToSpeechService();
    if (fallback.isSupported()) return fallback;
  }
  return service;
}

export type { SpeechRecognitionService, TextToSpeechService, SttProviderName, TtsProviderName } from "./types";
export type { SpeechRecognitionResult, SpeechErrorInfo, SpeechErrorCode } from "./types";
