import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendTextToSpeechService } from "../services/speech/backendProvider";

const locales = {
  en: "en-IN",
  te: "te-IN",
  hi: "hi-IN",
  ta: "ta-IN",
  kn: "kn-IN",
  mr: "mr-IN",
  ml: "ml-IN",
  bn: "bn-IN",
  gu: "gu-IN",
  pa: "pa-IN",
};

const originalAudio = (window as any).Audio;

afterEach(() => {
  (window as any).Audio = originalAudio;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("BackendTextToSpeechService", () => {
  it.each(Object.entries(locales))("sends the %s locale to backend TTS", async (locale, bcp47) => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, blob: async () => new Blob(["audio"]) });
    const play = vi.fn().mockResolvedValue(undefined);
    const FakeAudio = vi.fn().mockImplementation(function (this: any) {
      this.play = play;
      this.pause = vi.fn();
      this.onerror = null;
      this.onended = null;
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("Audio", FakeAudio);
    vi.stubGlobal("URL", { createObjectURL: vi.fn(() => "blob:test"), revokeObjectURL: vi.fn() });
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => "token") });

    new BackendTextToSpeechService().speak("Localized recommendation", locale);
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalled());

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      text: "Localized recommendation",
      locale: bcp47.split("-")[0],
    });
  });

  it("falls back to browser speech when backend TTS is unavailable", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 503 });
    const browserSpeak = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("Audio", vi.fn());
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => null) });
    vi.stubGlobal("speechSynthesis", {
      cancel: vi.fn(),
      speak: browserSpeak,
      getVoices: () => [{ lang: "te-IN", name: "Telugu Voice" }],
    });
    vi.stubGlobal("SpeechSynthesisUtterance", vi.fn());

    new BackendTextToSpeechService().speak("Use safe guidance", "te");
    await vi.waitFor(() => expect(browserSpeak).toHaveBeenCalled());
  });

  it("cancels the request and current audio immediately", () => {
    const abort = vi.fn();
    const pause = vi.fn();
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    vi.stubGlobal("Audio", vi.fn().mockImplementation(function (this: any) {
      this.pause = pause;
    }));
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => null) });

    const service = new BackendTextToSpeechService();
    (service as any).controller = { abort };
    (service as any).currentAudio = { pause };
    service.cancel();

    expect(abort).toHaveBeenCalled();
    expect(pause).toHaveBeenCalled();
  });
});
