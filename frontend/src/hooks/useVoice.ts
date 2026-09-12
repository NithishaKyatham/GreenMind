import { useEffect, useRef, useState } from "react";

// Minimal ambient typings for the Web Speech API, which isn't in the
// default TS DOM lib. Kept local to this hook rather than a global.d.ts
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

const LOCALE_TO_BCP47: Record<string, string> = {
  en: "en-IN", te: "te-IN", hi: "hi-IN", ta: "ta-IN", kn: "kn-IN", mr: "mr-IN",
};

/**
 * Voice input (speech-to-text) and output (text-to-speech) via the
 * browser's native Web Speech API. No external service, no API key.
 * Fails gracefully: `supported` is false on browsers without the API
 * (notably most non-Chromium browsers), and the caller should hide the
 * mic/speaker controls in that case rather than let the app break.
 */
export function useVoice(locale: string) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    const SpeechRecognitionCtor =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    setSupported(!!SpeechRecognitionCtor && !!window.speechSynthesis);
  }, []);

  const startListening = (onResult: (text: string) => void) => {
    const SpeechRecognitionCtor =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setError("Voice input isn't supported in this browser. Try Chrome or Edge.");
      return;
    }
    setError(null);
    const recognition: SpeechRecognitionLike = new SpeechRecognitionCtor();
    recognition.lang = LOCALE_TO_BCP47[locale] || "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };
    recognition.onerror = (event: any) => {
      if (event.error === "not-allowed" || event.error === "permission-denied") {
        setError("Microphone access was denied. Enable it in your browser settings to use voice input.");
      } else if (event.error === "network") {
        setError("Voice recognition needs a network connection.");
      } else if (event.error === "language-not-supported") {
        setError("Voice input isn't available for the selected language yet.");
      } else {
        setError("Voice input failed. Please try again or type your message.");
      }
      setListening(false);
    };
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    setListening(true);
    try {
      recognition.start();
    } catch {
      setError("Could not start voice input.");
      setListening(false);
    }
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setListening(false);
  };

  const speak = (text: string) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // stop any prior utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = LOCALE_TO_BCP47[locale] || "en-IN";
    window.speechSynthesis.speak(utterance);
  };

  return { supported, listening, error, startListening, stopListening, speak };
}
