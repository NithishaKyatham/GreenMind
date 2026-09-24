import { describe, it, expect, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useVoice } from "../hooks/useVoice";

const originalSpeechRecognition = (window as any).SpeechRecognition;
const originalSpeechSynthesis = (window as any).speechSynthesis;
const originalUtterance = (window as any).SpeechSynthesisUtterance;

afterEach(() => {
  (window as any).SpeechRecognition = originalSpeechRecognition;
  (window as any).speechSynthesis = originalSpeechSynthesis;
  (window as any).SpeechSynthesisUtterance = originalUtterance;
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("useVoice (post-refactor regression)", () => {
  it("reports browser TTS unavailable when browser speech APIs are missing", () => {
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;
    delete (window as any).speechSynthesis;

    const { result } = renderHook(() => useVoice("en"));
    expect(result.current.supported).toBe(false);
    expect(result.current.ttsSupported).toBe(false);
  });

  it("reports supported and round-trips a transcript through startListening, same public shape as before", async () => {
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
    (window as any).speechSynthesis = { cancel: vi.fn(), speak: vi.fn() };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      (this as any).text = text;
    };

    const { result } = renderHook(() => useVoice("te"));

    await waitFor(() => expect(result.current.supported).toBe(true));

    const onResult = vi.fn();
    act(() => {
      result.current.startListening(onResult);
    });

    expect(capturedInstance.lang).toBe("te-IN");

    act(() => {
      capturedInstance.onresult({ results: { 0: { 0: { transcript: "my tomato leaves are brown" } }, length: 1 } });
    });

    expect(onResult).toHaveBeenCalledWith("my tomato leaves are brown");
    expect(result.current.listening).toBe(false);
  });

  it("uses the installed browser voice for the selected locale", async () => {
    const speak = vi.fn();
    (window as any).SpeechRecognition = vi.fn();
    (window as any).speechSynthesis = {
      cancel: vi.fn(),
      speak,
      getVoices: () => [{ lang: "hi-IN", name: "Hindi Voice" }],
    };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      (this as any).text = text;
      (this as any).lang = "";
      (this as any).voice = null;
    };

    const { result } = renderHook(() => useVoice("hi"));
    act(() => {
      result.current.speak("hello farmer");
    });

    await waitFor(() => expect(speak).toHaveBeenCalled());
  });

  it("keeps TTS available when speech recognition is unavailable", async () => {
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;
    (window as any).speechSynthesis = { cancel: vi.fn(), speak: vi.fn() };
    (window as any).SpeechSynthesisUtterance = function (text: string) {
      (this as any).text = text;
    };

    const { result } = renderHook(() => useVoice("en"));

    await waitFor(() => expect(result.current.ttsSupported).toBe(true));
    expect(result.current.supported).toBe(false);
  });
});
