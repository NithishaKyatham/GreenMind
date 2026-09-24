import { describe, expect, it, vi } from "vitest";
import {
  findVoiceForLocale,
  getAvailableVoiceLanguages,
  getVoiceAvailability,
} from "../services/speech/voiceSelection";
import { WebSpeechTextToSpeechService } from "../services/speech/webSpeechProvider";

const voice = (lang: string) => ({ lang }) as SpeechSynthesisVoice;

describe("dynamic browser voice detection", () => {
  it("detects readable English and Hindi languages", () => {
    const languages = getAvailableVoiceLanguages([voice("en-US"), voice("hi-IN")]);
    expect(languages.map(({ name }) => name)).toEqual(["English", "Hindi"]);
  });

  it("deduplicates multiple locales for one language", () => {
    const languages = getAvailableVoiceLanguages([
      voice("en-US"),
      voice("en-GB"),
      voice("en-IN"),
    ]);
    expect(languages).toHaveLength(1);
    expect(languages[0].name).toBe("English");
  });

  it("detects Telugu only when the device exposes te-IN", () => {
    expect(getAvailableVoiceLanguages([voice("en-US")]).map(({ name }) => name)).not.toContain("Telugu");
    expect(getAvailableVoiceLanguages([voice("en-US"), voice("te-IN")]).map(({ name }) => name)).toContain("Telugu");
  });

  it("supports dynamically detected French and Japanese names", () => {
    expect(getAvailableVoiceLanguages([voice("fr-FR"), voice("ja-JP")]).map(({ name }) => name)).toEqual([
      "French",
      "Japanese",
    ]);
  });

  it("matches exact locale before language prefix", () => {
    const exact = voice("en-IN");
    const otherEnglish = voice("en-US");
    expect(findVoiceForLocale([otherEnglish, exact], "en-IN")).toBe(exact);
    expect(findVoiceForLocale([otherEnglish], "en-IN")).toBe(otherEnglish);
  });

  it("does not report an unrelated voice as available", () => {
    const availability = getVoiceAvailability([voice("en-US")], "te-IN");
    expect(availability.available).toBe(false);
    expect(availability.voice).toBeNull();
  });

  it("updates detected languages after voiceschanged", () => {
    const listeners: (() => void)[] = [];
    let voices: SpeechSynthesisVoice[] = [voice("en-US")];
    const synthesis = {
      getVoices: () => voices,
      onvoiceschanged: null,
      cancel: vi.fn(),
      speak: vi.fn(),
    };
    (window as any).speechSynthesis = synthesis;
    const service = new WebSpeechTextToSpeechService();
    service.subscribeVoiceAvailability(() => listeners.forEach((listener) => listener()));
    const updates: string[][] = [];
    service.subscribeVoiceAvailability(() => {
      updates.push(service.getAvailableVoiceLanguages().map(({ name }) => name));
    });

    voices = [voice("en-US"), voice("te-IN")];
    (synthesis as any).onvoiceschanged?.();

    expect(updates).toEqual([["English", "Telugu"]]);
  });

  it("reports loading for empty initial voices and empty after discovery", () => {
    let voices: SpeechSynthesisVoice[] = [];
    const synthesis = {
      getVoices: () => voices,
      onvoiceschanged: null,
      cancel: vi.fn(),
      speak: vi.fn(),
    };
    (window as any).speechSynthesis = synthesis;
    const service = new WebSpeechTextToSpeechService();
    expect(service.getVoiceAvailability("en").loading).toBe(true);

    service.subscribeVoiceAvailability(() => undefined);
    (synthesis as any).onvoiceschanged?.();
    expect(service.getVoiceAvailability("en").loading).toBe(false);
    expect(service.getAvailableVoiceLanguages()).toEqual([]);
    voices = [voice("de-DE")];
    expect(service.getAvailableVoiceLanguages()[0].name).toBe("German");
  });
});
