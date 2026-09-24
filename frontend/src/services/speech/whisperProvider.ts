import { SpeechRecognitionService, SpeechErrorInfo } from "./types";

function readEnv(name: string): string | undefined {
  return (import.meta as any).env?.[name];
}

function browserRecordingSupported(): boolean {
  return (
    typeof MediaRecorder !== "undefined" &&
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function"
  );
}

/**
 * Speech-to-text via an OpenAI-Whisper-compatible transcription API
 * (works against OpenAI's own endpoint, or a self-hosted
 * Whisper-compatible server that accepts the same multipart request
 * shape). This is a real, working adapter — not a placeholder — but it
 * is INACTIVE by default: `isSupported()` returns false unless the app
 * is explicitly configured with an API key or a self-hosted endpoint,
 * so building/running GreenMind never requires a Whisper account.
 *
 * To activate: set VITE_WHISPER_API_KEY (uses OpenAI's endpoint), or
 * VITE_WHISPER_ENDPOINT to point at a self-hosted server, then select
 * this provider via VITE_STT_PROVIDER=whisper (see services/speech/index.ts).
 */
export class WhisperSpeechRecognitionService implements SpeechRecognitionService {
  readonly providerName = "whisper";

  private endpoint: string;
  private apiKey?: string;
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;

  constructor(config?: { endpoint?: string; apiKey?: string }) {
    this.endpoint =
      config?.endpoint ||
      readEnv("VITE_WHISPER_ENDPOINT") ||
      "https://api.openai.com/v1/audio/transcriptions";
    this.apiKey = config?.apiKey || readEnv("VITE_WHISPER_API_KEY");
  }

  isSupported(): boolean {
    const configured = !!this.apiKey || !!readEnv("VITE_WHISPER_ENDPOINT");
    return configured && browserRecordingSupported();
  }

  startListening(
    locale: string,
    onResult: (result: { transcript: string }) => void,
    onError: (error: SpeechErrorInfo) => void
  ): void {
    if (!this.isSupported()) {
      onError({
        code: "not-configured",
        message:
          "Whisper speech recognition isn't configured. Set VITE_WHISPER_API_KEY (or a self-hosted VITE_WHISPER_ENDPOINT) to enable it.",
      });
      return;
    }

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        this.stream = stream;
        const recorder = new MediaRecorder(stream);
        this.chunks = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) this.chunks.push(e.data);
        };

        recorder.onstop = () => {
          this.stream?.getTracks().forEach((track) => track.stop());
          this.transcribe(locale, recorder.mimeType || "audio/webm", onResult, onError);
        };

        this.mediaRecorder = recorder;
        recorder.start();
      })
      .catch((err: any) => {
        if (err?.name === "NotAllowedError" || err?.name === "PermissionDeniedError") {
          onError({
            code: "permission-denied",
            message: "Microphone access was denied. Enable it in your browser settings to use voice input.",
          });
        } else {
          onError({ code: "unknown", message: "Could not start voice input." });
        }
      });
  }

  stopListening(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
  }

  private async transcribe(
    locale: string,
    mimeType: string,
    onResult: (result: { transcript: string }) => void,
    onError: (error: SpeechErrorInfo) => void
  ) {
    try {
      const audioBlob = new Blob(this.chunks, { type: mimeType });
      const form = new FormData();
      form.append("file", audioBlob, "speech.webm");
      form.append("model", "whisper-1");
      // GreenMind's locale codes (en, te, hi, ta, kn, mr, ml, bn, gu, pa)
      // are already ISO-639-1 codes, which is exactly what Whisper's
      // `language` parameter expects — no separate mapping table needed.
      form.append("language", locale);

      const headers: Record<string, string> = {};
      if (this.apiKey) headers.Authorization = `Bearer ${this.apiKey}`;

      const res = await fetch(this.endpoint, { method: "POST", headers, body: form });
      if (!res.ok) throw new Error(`Whisper request failed (${res.status})`);

      const data = await res.json();
      const transcript = data.text ?? data.transcript ?? "";
      onResult({ transcript });
    } catch {
      onError({
        code: "network",
        message: "Voice transcription failed. Please try again or type your message.",
      });
    }
  }
}
