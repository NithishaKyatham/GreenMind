/**
 * Provider-independent speech interfaces.
 *
 * Anything that talks to a farmer's microphone or speaker goes through
 * these two interfaces, never directly against a specific vendor's API.
 * This is what lets the active provider be swapped (browser Web Speech
 * today; Whisper, Azure, Google, Sarvam, etc. later) without touching
 * any component — only services/speech/index.ts's factory needs to
 * change, or a runtime env var.
 */

export interface SpeechRecognitionResult {
  transcript: string;
}

export type SpeechErrorCode =
  | "not-supported"       // this provider cannot run at all in this environment
  | "not-configured"      // provider needs an endpoint/API key that isn't set
  | "permission-denied"   // user denied microphone access
  | "network"             // network/connectivity failure
  | "language-not-supported"
  | "unknown";

export interface SpeechErrorInfo {
  code: SpeechErrorCode;
  /** Already end-user-facing (not a raw provider error string). */
  message: string;
}

export interface SpeechRecognitionService {
  /** Short identifier for logging/debugging, e.g. "browser", "whisper", "azure". */
  readonly providerName: string;

  /**
   * Whether this provider can plausibly work right now, in this browser,
   * with its current configuration. Does NOT guarantee success (e.g. the
   * user can still deny mic permission) — it's a pre-flight check so the
   * caller can decide whether to show voice controls at all.
   */
  isSupported(): boolean;

  /**
   * Starts listening for speech in the given locale (GreenMind locale
   * code, e.g. "te", "hi", not a raw BCP-47 tag — providers translate
   * internally). Exactly one of onResult/onError will fire per session,
   * followed by the recognition session ending.
   */
  startListening(
    locale: string,
    onResult: (result: SpeechRecognitionResult) => void,
    onError: (error: SpeechErrorInfo) => void
  ): void;

  /** Stops an in-progress listening session, if any. Safe to call when idle. */
  stopListening(): void;
}

export interface TextToSpeechService {
  readonly providerName: string;

  isSupported(): boolean;

  /** Speaks `text` in the given locale. Cancels any speech already in progress. */
  speak(
    text: string,
    locale: string,
    onEnd?: () => void,
    onError?: (error: SpeechErrorInfo) => void
  ): void;

  getVoiceAvailability?(locale: string): {
    available: boolean;
    loading: boolean;
    voice: SpeechSynthesisVoice | null;
  };

  getAvailableVoiceLanguages?(): import("./voiceSelection").AvailableVoiceLanguage[];

  subscribeVoiceAvailability?(listener: () => void): () => void;

  /** Stops any speech currently playing. Safe to call when idle. */
  cancel(): void;
}

export type SttProviderName = "browser" | "whisper" | "azure";
export type TtsProviderName = "browser" | "azure" | "backend";
