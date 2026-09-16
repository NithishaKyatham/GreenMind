import { describe, it, expect, afterEach, vi } from "vitest";
import { WebSpeechRecognitionService, WebSpeechTextToSpeechService } from "../services/speech/webSpeechProvider";

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
    (window as any).speechSynthesis = { cancel, speak };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      (this as any).text = text;
      (this as any).lang = "";
    };

    const service = new WebSpeechTextToSpeechService();
    service.speak("hello", "hi");

    expect(cancel).toHaveBeenCalled();
    expect(speak).toHaveBeenCalled();
  });
});
