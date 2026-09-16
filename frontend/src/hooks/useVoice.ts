import { useEffect, useRef, useState } from "react";
import { createSpeechRecognitionService, createTextToSpeechService } from "../services/speech";
import type { SpeechRecognitionService, TextToSpeechService } from "../services/speech";

/**
 * Voice input (speech-to-text) and output (text-to-speech) for GreenMind.
 *
 * This hook no longer talks to the browser's Web Speech API directly —
 * it goes through the provider-independent interfaces in services/speech/.
 * The active provider defaults to the browser (no external service, no
 * API key), but can be switched to Whisper or Azure via VITE_STT_PROVIDER
 * / VITE_TTS_PROVIDER env vars without changing this hook or any
 * component that uses it (see services/speech/index.ts for selection
 * logic and automatic fallback behavior).
 *
 * Public API: {supported, listening, error, startListening, stopListening,
 * speak, stopSpeaking}.
 */
export function useVoice(locale: string) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionServiceRef = useRef<SpeechRecognitionService | null>(null);
  const ttsServiceRef = useRef<TextToSpeechService | null>(null);

  useEffect(() => {
    recognitionServiceRef.current = createSpeechRecognitionService();
    ttsServiceRef.current = createTextToSpeechService();
    setSupported(
      recognitionServiceRef.current.isSupported() && ttsServiceRef.current.isSupported()
    );
  }, []);

  const startListening = (onResult: (text: string) => void) => {
    const service = recognitionServiceRef.current;
    if (!service) return;

    setError(null);
    setListening(true);

    service.startListening(
      locale,
      (result) => {
        setListening(false);
        onResult(result.transcript);
      },
      (err) => {
        setError(err.message);
        setListening(false);
      }
    );
  };

  const stopListening = () => {
    recognitionServiceRef.current?.stopListening();
    setListening(false);
  };

  const speak = (text: string) => {
    ttsServiceRef.current?.speak(text, locale);
  };

  const stopSpeaking = () => {
    ttsServiceRef.current?.cancel();
  };

  return { supported, listening, error, startListening, stopListening, speak, stopSpeaking };
}
