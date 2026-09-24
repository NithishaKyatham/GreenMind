import { describe, it, expect, afterEach, vi } from "vitest";
import { createSpeechRecognitionService, createTextToSpeechService } from "../services/speech";

const originalSpeechRecognition = (window as any).SpeechRecognition;
const originalSpeechSynthesis = (window as any).speechSynthesis;

function mockBrowserSpeechSupport(supported: boolean) {
  if (supported) {
    (window as any).SpeechRecognition = vi.fn();
    (window as any).speechSynthesis = {};
  } else {
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;
    delete (window as any).speechSynthesis;
  }
}

describe("speech service factory", () => {
  afterEach(() => {
    (window as any).SpeechRecognition = originalSpeechRecognition;
    (window as any).speechSynthesis = originalSpeechSynthesis;
    vi.unstubAllEnvs();
  });

  it("defaults to the browser TTS provider without cloud dependencies", () => {
    mockBrowserSpeechSupport(true);
    const stt = createSpeechRecognitionService();
    const tts = createTextToSpeechService();
    expect(stt.providerName).toBe("browser");
    expect(tts.providerName).toBe("browser");
  });

  it("falls back to the browser provider when azure is requested but not configured", () => {
    mockBrowserSpeechSupport(true);
    // No VITE_AZURE_SPEECH_KEY/REGION set, so the azure adapter reports
    // itself unsupported and the factory should fall back automatically.
    const stt = createSpeechRecognitionService("azure");
    const tts = createTextToSpeechService("azure");
    expect(stt.providerName).toBe("browser");
    expect(tts.providerName).toBe("browser");
  });

  it("falls back to the browser provider when whisper is requested but not configured", () => {
    mockBrowserSpeechSupport(true);
    const stt = createSpeechRecognitionService("whisper");
    expect(stt.providerName).toBe("browser");
  });

  it("an explicit provider override takes precedence over env vars", () => {
    mockBrowserSpeechSupport(true);
    const stt = createSpeechRecognitionService("browser");
    expect(stt.providerName).toBe("browser");
  });
});
