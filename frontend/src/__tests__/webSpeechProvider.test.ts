import { describe, it, expect, afterEach, vi } from "vitest";
import { WebSpeechRecognitionService, WebSpeechTextToSpeechService } from "../services/speech/webSpeechProvider";
import { LOCALE_TO_BCP47 } from "../services/speech/localeMap";

const originalSpeechRecognition = (window as any).SpeechRecognition;
const originalSpeechSynthesis = (window as any).speechSynthesis;

afterEach(() => {
  (window as any).SpeechRecognition = originalSpeechRecognition;
  (window as any).speechSynthesis = originalSpeechSynthesis;
});

describe("WebSpeechRecognitionService", () => {
  it("reports unsupported when the browser has no SpeechRecognition constructor", () => {
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;
    const service = new WebSpeechRecognitionService();
    expect(service.isSupported()).toBe(false);
  });

  it("reports supported and starts recognition with the correct BCP-47 locale", () => {
    const startSpy = vi.fn();
    const instances: any[] = [];

    class FakeRecognition {
      lang = "";
      continuous = false;
      interimResults = false;
      onresult: any = null;
      onerror: any = null;
      onend: any = null;
      start = startSpy;
      stop = vi.fn();
      constructor() {
        instances.push(this);
      }
    }
    (window as any).SpeechRecognition = FakeRecognition;

    const service = new WebSpeechRecognitionService();
    expect(service.isSupported()).toBe(true);

    const onResult = vi.fn();
    const onError = vi.fn();
    service.startListening("te", onResult, onError);

    expect(startSpy).toHaveBeenCalled();
    expect(instances[0].lang).toBe("te-IN"); // proves the locale map covers Telugu correctly

    instances[0].onresult({ results: { 0: { 0: { transcript: "hello" } }, length: 1 } });
    expect(onResult).toHaveBeenCalledWith({ transcript: "hello" });
  });

  it("maps a permission-denied recognition error to a clear message", () => {
    let capturedInstance: any;
    class FakeRecognition {
      lang = "";
      continuous = false;
      interimResults = false;
      onresult: any = null;
      onerror: any = null;
      onend: any = null;
      start = vi.fn();
      stop = vi.fn();
      constructor() {
        capturedInstance = this;
      }
    }
    (window as any).SpeechRecognition = FakeRecognition;

    const service = new WebSpeechRecognitionService();
    const onError = vi.fn();
    service.startListening("en", vi.fn(), onError);

    capturedInstance.onerror({ error: "not-allowed" });
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ code: "permission-denied" })
    );
  });
});

describe("WebSpeechTextToSpeechService", () => {
  it("reports unsupported when speechSynthesis is unavailable", () => {
    delete (window as any).speechSynthesis;
    const service = new WebSpeechTextToSpeechService();
    expect(service.isSupported()).toBe(false);
  });

  it("cancels any prior utterance before speaking a new one", () => {
    const cancel = vi.fn();
    const speak = vi.fn();
    (window as any).speechSynthesis = {
      cancel,
      speak,
      getVoices: () => [{ lang: "hi-IN", name: "Hindi Voice" }],
    };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      (this as any).text = text;
      (this as any).lang = "";
    };

    const service = new WebSpeechTextToSpeechService();
    service.speak("hello", "hi");

    expect(cancel).toHaveBeenCalled();
    expect(speak).toHaveBeenCalled();
  });

  it("uses the selected locale for recommendation playback", () => {
    const speak = vi.fn();
    const cancel = vi.fn();
    let utterance: any;
    const selectedVoice = { lang: "te-IN", name: "Telugu Voice" };
    (window as any).speechSynthesis = { cancel, speak, getVoices: () => [selectedVoice] };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      utterance = this;
      this.text = text;
      this.lang = "";
      this.voice = null;
    };

    const service = new WebSpeechTextToSpeechService();
    service.speak("Treatment: Apply fungicide.", "te");

    expect(utterance.text).toBe("Treatment: Apply fungicide.");
    expect(utterance.lang).toBe("te-IN");
    expect(utterance.voice).toBe(selectedVoice);
    expect(speak).toHaveBeenCalledWith(utterance);
  });

  it("speaks with the available Hindi voice", () => {
    const speak = vi.fn();
    const voice = { lang: "hi-IN", name: "Hindi Voice" };
    let utterance: any;
    (window as any).speechSynthesis = {
      cancel: vi.fn(),
      speak,
      getVoices: () => [voice],
    };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      utterance = this;
      this.text = text;
      this.lang = "";
      this.voice = null;
    };

    new WebSpeechTextToSpeechService().speak("स्थानीय सुझाव", "hi");

    expect(utterance.lang).toBe("hi-IN");
    expect(utterance.voice).toBe(voice);
    expect(speak).toHaveBeenCalledWith(utterance);
  });

  it("falls back to a same-language voice prefix", () => {
    const speak = vi.fn();
    const voice = { lang: "hi", name: "Hindi Voice" };
    let utterance: any;
    (window as any).speechSynthesis = {
      cancel: vi.fn(),
      speak,
      getVoices: () => [voice],
    };
    (window as any).SpeechSynthesisUtterance = function () {
      utterance = this;
      this.lang = "";
      this.voice = null;
    };

    new WebSpeechTextToSpeechService().speak("Localized recommendation", "hi");

    expect(utterance.lang).toBe("hi-IN");
    expect(utterance.voice).toBe(voice);
    expect(speak).toHaveBeenCalledWith(utterance);
  });

  it.each(Object.entries(LOCALE_TO_BCP47))("selects a voice for the %s locale", (locale, language) => {
    const speak = vi.fn();
    const voice = { lang: language, name: `${locale} voice` };
    let utterance: any;
    (window as any).speechSynthesis = { cancel: vi.fn(), speak, getVoices: () => [voice] };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      utterance = this;
      this.text = text;
      this.lang = "";
      this.voice = null;
    };

    new WebSpeechTextToSpeechService().speak("Localized recommendation", locale);

    expect(utterance.lang).toBe(language);
    expect(utterance.voice).toBe(voice);
  });

  it("reports an unavailable Telugu voice without speaking English", () => {
    const speak = vi.fn();
    const onError = vi.fn();
    const cancel = vi.fn();
    let utterance: any;
    (window as any).speechSynthesis = {
      cancel,
      speak,
      getVoices: () => [{ lang: "en-US", name: "English Voice" }],
    };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      utterance = this;
      this.text = text;
      this.lang = "";
      this.voice = null;
    };

    new WebSpeechTextToSpeechService().speak("Localized recommendation", "te", undefined, onError);

    expect(utterance.lang).toBe("te-IN");
    expect(utterance.voice).toBeNull();
    expect(speak).not.toHaveBeenCalled();
    expect(cancel).toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith({
      code: "language-not-supported",
      message: "A voice for Telugu is not available on this device.",
    });
  });

  it("waits for asynchronously loaded voices before speaking", () => {
    const speak = vi.fn();
    const voices: any[] = [];
    let utterance: any;
    (window as any).speechSynthesis = {
      cancel: vi.fn(),
      speak,
      getVoices: () => voices,
      onvoiceschanged: null,
    };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      utterance = this;
      this.text = text;
      this.lang = "";
      this.voice = null;
    };

    new WebSpeechTextToSpeechService().speak("Localized recommendation", "hi");
    expect(speak).not.toHaveBeenCalled();

    const voicesChanged = (window as any).speechSynthesis.onvoiceschanged;
    const voice = { lang: "hi-IN", name: "Hindi Voice" };
    voices.push(voice);
    voicesChanged();

    expect(utterance.lang).toBe("hi-IN");
    expect(utterance.voice).toBe(voice);
    expect(speak).toHaveBeenCalledWith(utterance);
  });

  it("reports an unavailable language after voices finish loading", () => {
    const speak = vi.fn();
    const onError = vi.fn();
    const voices: any[] = [];
    (window as any).speechSynthesis = {
      cancel: vi.fn(),
      speak,
      getVoices: () => voices,
      onvoiceschanged: null,
    };
    (window as any).SpeechSynthesisUtterance = function () {
      this.lang = "";
      this.voice = null;
    };

    new WebSpeechTextToSpeechService().speak("Localized recommendation", "te", undefined, onError);
    const voicesChanged = (window as any).speechSynthesis.onvoiceschanged;
    voices.push({ lang: "en-US", name: "English Voice" });
    voicesChanged();

    expect(speak).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith({
      code: "language-not-supported",
      message: "A voice for Telugu is not available on this device.",
    });
  });

  it("stops active and pending speech", () => {
    const cancel = vi.fn();
    const speak = vi.fn();
    const voices: any[] = [];
    (window as any).speechSynthesis = {
      cancel,
      speak,
      getVoices: () => voices,
      onvoiceschanged: null,
    };
    (window as any).SpeechSynthesisUtterance = function () {
      this.lang = "";
      this.voice = null;
    };

    const service = new WebSpeechTextToSpeechService();
    service.speak("Localized recommendation", "pa");
    const voicesChanged = (window as any).speechSynthesis.onvoiceschanged;
    service.cancel();
    voices.push({ lang: "pa-IN", name: "Punjabi Voice" });
    voicesChanged();

    expect(cancel).toHaveBeenCalled();
    expect(speak).not.toHaveBeenCalled();
  });
});
