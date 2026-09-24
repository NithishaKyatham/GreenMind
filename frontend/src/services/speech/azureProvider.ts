import { SpeechRecognitionService, SpeechErrorInfo, TextToSpeechService } from "./types";
import { toBcp47 } from "./localeMap";

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

interface AzureConfig {
  key?: string;
  region?: string;
}

function readAzureConfig(config?: AzureConfig): Required<AzureConfig> | null {
  const key = config?.key || readEnv("VITE_AZURE_SPEECH_KEY");
  const region = config?.region || readEnv("VITE_AZURE_SPEECH_REGION");
  if (!key || !region) return null;
  return { key, region };
}

/** Azure issues short-lived (10 min) auth tokens from the subscription key. */
async function fetchAzureToken(key: string, region: string): Promise<string> {
  const res = await fetch(`https://${region}.api.cognitive.microsoft.com/sts/v1.0/issuetoken`, {
    method: "POST",
    headers: { "Ocp-Apim-Subscription-Key": key },
  });
  if (!res.ok) throw new Error(`Azure token request failed (${res.status})`);
  return res.text();
}

/**
 * Speech-to-text via Azure Cognitive Services Speech (REST, short-audio
 * endpoint). A real, working adapter — not a placeholder — but INACTIVE
 * by default: `isSupported()` returns false unless both
 * VITE_AZURE_SPEECH_KEY and VITE_AZURE_SPEECH_REGION are set, so building
 * or running GreenMind never requires an Azure account.
 *
 * To activate: set both env vars, then select this provider via
 * VITE_STT_PROVIDER=azure (see services/speech/index.ts).
 */
export class AzureSpeechRecognitionService implements SpeechRecognitionService {
  readonly providerName = "azure";
  private config?: AzureConfig;
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;

  constructor(config?: AzureConfig) {
    this.config = config;
  }

  isSupported(): boolean {
    return !!readAzureConfig(this.config) && browserRecordingSupported();
  }

  startListening(
    locale: string,
    onResult: (result: { transcript: string }) => void,
    onError: (error: SpeechErrorInfo) => void
  ): void {
    const azure = readAzureConfig(this.config);
    if (!azure) {
      onError({
        code: "not-configured",
        message:
          "Azure speech recognition isn't configured. Set VITE_AZURE_SPEECH_KEY and VITE_AZURE_SPEECH_REGION to enable it.",
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
          this.recognize(azure, locale, recorder.mimeType || "audio/webm", onResult, onError);
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

  private async recognize(
    azure: Required<AzureConfig>,
    locale: string,
    mimeType: string,
    onResult: (result: { transcript: string }) => void,
    onError: (error: SpeechErrorInfo) => void
  ) {
    try {
      const token = await fetchAzureToken(azure.key, azure.region);
      const audioBlob = new Blob(this.chunks, { type: mimeType });
      const url = `https://${azure.region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=${toBcp47(locale)}&format=simple`;

      const res = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": `${mimeType}; codecs=opus`,
        },
        body: audioBlob,
      });
      if (!res.ok) throw new Error(`Azure STT request failed (${res.status})`);

      const data = await res.json();
      if (data.RecognitionStatus && data.RecognitionStatus !== "Success") {
        onError({
          code: "unknown",
          message: "Voice input failed. Please try again or type your message.",
        });
        return;
      }
      onResult({ transcript: data.DisplayText ?? "" });
    } catch {
      onError({
        code: "network",
        message: "Voice transcription failed. Please try again or type your message.",
      });
    }
  }
}

/**
 * Text-to-speech via Azure Cognitive Services Speech (REST). Same
 * inactive-by-default profile as the recognition adapter above.
 *
 * To activate: set VITE_AZURE_SPEECH_KEY and VITE_AZURE_SPEECH_REGION,
 * then select this provider via VITE_TTS_PROVIDER=azure.
 */
export class AzureTextToSpeechService implements TextToSpeechService {
  readonly providerName = "azure";
  private config?: AzureConfig;
  private currentAudio: HTMLAudioElement | null = null;

  constructor(config?: AzureConfig) {
    this.config = config;
  }

  isSupported(): boolean {
    return !!readAzureConfig(this.config);
  }

  speak(text: string, locale: string, onEnd?: () => void): void {
    const azure = readAzureConfig(this.config);
    if (!azure) return; // caller should have checked isSupported() first

    this.cancel();

    const bcp47 = toBcp47(locale);
    const ssml = `<speak version='1.0' xml:lang='${bcp47}'><voice xml:lang='${bcp47}' xml:gender='Female' name='${bcp47}-Standard-A'>${escapeXml(
      text
    )}</voice></speak>`;

    fetchAzureToken(azure.key, azure.region)
      .then((token) =>
        fetch(`https://${azure.region}.tts.speech.microsoft.com/cognitiveservices/v1`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
          },
          body: ssml,
        })
      )
      .then((res) => {
        if (!res.ok) throw new Error(`Azure TTS request failed (${res.status})`);
        return res.blob();
      })
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        this.currentAudio = audio;
        audio.onended = () => {
          URL.revokeObjectURL(url);
          onEnd?.();
        };
        audio.play().catch(() => {
          /* Autoplay can be blocked by the browser; this is a best-effort
             feature, so failing silently here is acceptable rather than
             surfacing a disruptive error for a non-critical TTS playback. */
        });
      })
      .catch(() => {
        onEnd?.();
        /* Same rationale as above — TTS failures degrade to silence, not
           an error banner, since the text is already shown on screen. */
      });
  }

  cancel(): void {
    this.currentAudio?.pause();
    this.currentAudio = null;
  }
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}
