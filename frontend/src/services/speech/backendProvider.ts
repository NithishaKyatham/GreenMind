import { TextToSpeechService } from "./types";
import { toBcp47 } from "./localeMap";
import { WebSpeechTextToSpeechService } from "./webSpeechProvider";

function readEnv(name: string): string | undefined {
  return (import.meta as any).env?.[name];
}

/** Server-backed TTS with browser speech as a graceful fallback. */
export class BackendTextToSpeechService implements TextToSpeechService {
  readonly providerName = "backend";
  private readonly browserFallback = new WebSpeechTextToSpeechService();
  private controller: AbortController | null = null;
  private currentAudio: HTMLAudioElement | null = null;
  private currentUrl: string | null = null;
  private requestId = 0;

  isSupported(): boolean {
    return typeof fetch === "function" && typeof Audio !== "undefined";
  }

  speak(text: string, locale: string, onEnd?: () => void): void {
    if (!this.isSupported()) {
      this.browserFallback.speak(text, locale, onEnd);
      return;
    }

    this.cancel();
    const requestId = ++this.requestId;
    const controller = new AbortController();
    this.controller = controller;
    const baseUrl = readEnv("VITE_API_BASE_URL") || "http://localhost:8000/api";
    const token = localStorage.getItem("greenmind_access_token");

    fetch(`${baseUrl}/tts/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ text, locale: toBcp47(locale).split("-")[0] }),
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error(`TTS request failed: ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        if (requestId !== this.requestId) return;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        this.currentUrl = url;
        this.currentAudio = audio;
        let finished = false;
        const cleanup = () => {
          if (finished) return;
          finished = true;
          URL.revokeObjectURL(url);
          if (this.currentAudio === audio) {
            this.currentAudio = null;
            this.currentUrl = null;
          }
        };
        const finish = () => {
          cleanup();
          onEnd?.();
        };
        audio.onended = finish;
        audio.onerror = () => {
          cleanup();
          this.browserFallback.speak(text, locale, onEnd);
        };
        audio.play().catch(() => {
          cleanup();
          this.browserFallback.speak(text, locale, onEnd);
        });
      })
      .catch(() => {
        if (requestId !== this.requestId || controller.signal.aborted) return;
        this.browserFallback.speak(text, locale, onEnd);
      });
  }

  cancel(): void {
    this.requestId += 1;
    this.controller?.abort();
    this.controller = null;
    this.currentAudio?.pause();
    this.currentAudio = null;
    if (this.currentUrl) {
      URL.revokeObjectURL(this.currentUrl);
      this.currentUrl = null;
    }
    this.browserFallback.cancel();
  }
}
