import { SpeechRecognitionService, SpeechErrorInfo, TextToSpeechService } from "./types";
import { LOCALE_NAMES, toBcp47 } from "./localeMap";
import {
  AvailableVoiceLanguage,
  findVoiceForLocale,
  getAvailableVoiceLanguages,
  getVoiceAvailability,
  VoiceAvailability,
} from "./voiceSelection";

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
  private requestId = 0;
  private pendingTimer: number | null = null;
  private voicesChangedHandler: (() => void) | null = null;
  private voicesLoaded = false;

  isSupported(): boolean {
    return !!window.speechSynthesis;
  }

  getVoiceAvailability(locale: string): VoiceAvailability {
    const synthesis = window.speechSynthesis;
    if (!synthesis) return { available: false, loading: false, voice: null };
    const voices = synthesis.getVoices?.() || [];
    if (voices.length) this.voicesLoaded = true;
    return getVoiceAvailability(voices, toBcp47(locale), !this.voicesLoaded);
  }

  getAvailableVoiceLanguages(): AvailableVoiceLanguage[] {
    const synthesis = window.speechSynthesis;
    return synthesis ? getAvailableVoiceLanguages(synthesis.getVoices?.() || []) : [];
  }

  subscribeVoiceAvailability(listener: () => void): () => void {
    const synthesis = window.speechSynthesis;
    if (!synthesis) return () => undefined;
    const previousHandler = synthesis.onvoiceschanged;
    const handler = () => {
      previousHandler?.call(synthesis, new Event("voiceschanged"));
      this.voicesLoaded = true;
      listener();
    };
    synthesis.onvoiceschanged = handler;
    return () => {
      if (synthesis.onvoiceschanged === handler) synthesis.onvoiceschanged = previousHandler;
    };
  }

  speak(
    text: string,
    locale: string,
    onEnd?: () => void,
    onError?: (error: SpeechErrorInfo) => void
  ): void {
    const synthesis = window.speechSynthesis;
    if (!synthesis) return;
    this.cancel();
    const requestId = ++this.requestId;
    const utterance = new SpeechSynthesisUtterance(text);
    const language = toBcp47(locale);
    const languageName = LOCALE_NAMES[locale] || language;
    utterance.lang = language;
    utterance.onend = onEnd || null;
    utterance.onerror = onEnd || null;

    const speakWithAvailableVoice = (): boolean => {
      if (requestId !== this.requestId) return true;

      const voices = synthesis.getVoices?.() || [];
      if (!voices.length) return false;

      const matchingVoice = findVoiceForLocale(voices, language);

      if (!matchingVoice) {
        this.cancel();
        onError?.({
          code: "language-not-supported",
          message: `A voice for ${languageName} is not available on this device.`,
        });
        return true;
      }
      utterance.voice = matchingVoice;
      synthesis.speak(utterance);
      return true;
    };

    // Some browsers populate voices only after voiceschanged fires.
    const supportsVoiceEvents = "onvoiceschanged" in synthesis;
    const spokeWithMatchingVoice = speakWithAvailableVoice();
    if (spokeWithMatchingVoice || !supportsVoiceEvents || !synthesis.getVoices) {
      if (!spokeWithMatchingVoice) {
        this.cancel();
        onError?.({
          code: "language-not-supported",
          message: `A voice for ${languageName} is not available on this device.`,
        });
      }
      return;
    }

    const previousHandler = synthesis.onvoiceschanged;
    const handleVoicesChanged = () => {
      previousHandler?.call(synthesis, new Event("voiceschanged"));
      if (this.pendingTimer !== null) window.clearTimeout(this.pendingTimer);
      this.pendingTimer = null;
      synthesis.onvoiceschanged = previousHandler;
      if (!speakWithAvailableVoice()) {
        this.cancel();
        onError?.({
          code: "language-not-supported",
          message: `A voice for ${languageName} is not available on this device.`,
        });
      }
    };
    this.voicesChangedHandler = handleVoicesChanged;
    synthesis.onvoiceschanged = handleVoicesChanged;
    this.pendingTimer = window.setTimeout(() => {
      if (requestId !== this.requestId) return;
      synthesis.onvoiceschanged = previousHandler;
      this.voicesChangedHandler = null;
      this.pendingTimer = null;
      if (!speakWithAvailableVoice()) {
        this.cancel();
        onError?.({
          code: "language-not-supported",
          message: `A voice for ${languageName} is not available on this device.`,
        });
      }
    }, 250);
  }

  cancel(): void {
    this.requestId += 1;
    if (this.pendingTimer !== null) {
      window.clearTimeout(this.pendingTimer);
      this.pendingTimer = null;
    }
    if (window.speechSynthesis && this.voicesChangedHandler === window.speechSynthesis.onvoiceschanged) {
      window.speechSynthesis.onvoiceschanged = null;
    }
    this.voicesChangedHandler = null;
    window.speechSynthesis?.cancel();
  }
}
