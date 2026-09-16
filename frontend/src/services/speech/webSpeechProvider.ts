import { SpeechRecognitionService, SpeechErrorInfo, TextToSpeechService } from "./types";
import { toBcp47 } from "./localeMap";

// Minimal ambient typings for the Web Speech API, which isn't in the
// default TS DOM lib. Kept local to this provider rather than a global.d.ts
// so it's obvious exactly what's being relied on.
interface SpeechRecognitionResultLike {
  transcript: string;
}
interface SpeechRecognitionEventLike extends Event {
  results: { [index: number]: { [index: number]: SpeechRecognitionResultLike }; length: number };
}
interface SpeechRecognitionLike extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
}

function getSpeechRecognitionCtor(): (new () => SpeechRecognitionLike) | undefined {
  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
}

function mapRecognitionError(event: any): SpeechErrorInfo {
  if (event.error === "not-allowed" || event.error === "permission-denied") {
    return {
      code: "permission-denied",
      message: "Microphone access was denied. Enable it in your browser settings to use voice input.",
    };
  }
  if (event.error === "network") {
    return { code: "network", message: "Voice recognition needs a network connection." };
  }
  if (event.error === "language-not-supported") {
    return {
      code: "language-not-supported",
      message: "Voice input isn't available for the selected language yet.",
    };
  }
  return { code: "unknown", message: "Voice input failed. Please try again or type your message." };
}

/**
 * Speech-to-text via the browser's native Web Speech API. No external
 * service, no API key, no network dependency beyond what the browser
 * itself needs. This is GreenMind's default/active provider — it's what
 * runs when no VITE_STT_PROVIDER env var is set. Support is inconsistent
 * across browsers (notably absent in most non-Chromium browsers), which
 * `isSupported()` reflects so callers can hide voice controls gracefully.
 */
export class WebSpeechRecognitionService implements SpeechRecognitionService {
  readonly providerName = "browser";
  private recognition: SpeechRecognitionLike | null = null;

  isSupported(): boolean {
    return !!getSpeechRecognitionCtor();
  }

  startListening(
    locale: string,
    onResult: (result: { transcript: string }) => void,
    onError: (error: SpeechErrorInfo) => void
  ): void {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) {
      onError({
        code: "not-supported",
        message: "Voice input isn't supported in this browser. Try Chrome or Edge.",
      });
      return;
    }

    const recognition: SpeechRecognitionLike = new Ctor();
    recognition.lang = toBcp47(locale);
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      onResult({ transcript: event.results[0][0].transcript });
    };
    recognition.onerror = (event: any) => onError(mapRecognitionError(event));

    this.recognition = recognition;
    try {
      recognition.start();
    } catch {
      onError({ code: "unknown", message: "Could not start voice input." });
    }
  }

  stopListening(): void {
    this.recognition?.stop();
  }
}

/**
 * Text-to-speech via the browser's native SpeechSynthesis API. Same
 * no-key, no-network-dependency profile as the recognition provider
 * above, and GreenMind's default active TTS provider.
 */
export class WebSpeechTextToSpeechService implements TextToSpeechService {
  readonly providerName = "browser";

  isSupported(): boolean {
    return !!window.speechSynthesis;
  }

  speak(text: string, locale: string): void {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // stop any prior utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = toBcp47(locale);
    window.speechSynthesis.speak(utterance);
  }

  cancel(): void {
    window.speechSynthesis?.cancel();
  }
}
