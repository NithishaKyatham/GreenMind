import { useEffect, useRef, useState } from "react";
import { createSpeechRecognitionService, createTextToSpeechService } from "../services/speech";
import type { SpeechRecognitionService, TextToSpeechService } from "../services/speech";
import type { AvailableVoiceLanguage } from "../services/speech/voiceSelection";

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
  const [ttsSupported, setTtsSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceAvailable, setVoiceAvailable] = useState<boolean | null>(null);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [availableVoiceLanguages, setAvailableVoiceLanguages] = useState<AvailableVoiceLanguage[]>([]);

  const recognitionServiceRef = useRef<SpeechRecognitionService | null>(null);
  const ttsServiceRef = useRef<TextToSpeechService | null>(null);

  useEffect(() => {
    recognitionServiceRef.current = createSpeechRecognitionService();
    // Recommendation playback is intentionally local and free; it must not
    // route through the optional cloud TTS providers.
    ttsServiceRef.current = createTextToSpeechService("browser");
    const recognitionSupported = recognitionServiceRef.current.isSupported();
    const textToSpeechSupported = ttsServiceRef.current.isSupported();
    setSupported(recognitionSupported && textToSpeechSupported);
    setTtsSupported(textToSpeechSupported);
    const updateVoiceAvailability = () => {
      const availability = ttsServiceRef.current?.getVoiceAvailability?.(locale);
      if (!availability) return;
      setVoiceAvailable(availability.available);
      setVoiceLoading(availability.loading);
      setAvailableVoiceLanguages(
        ttsServiceRef.current?.getAvailableVoiceLanguages?.() || []
      );
    };
    updateVoiceAvailability();
    const unsubscribe = ttsServiceRef.current?.subscribeVoiceAvailability?.(
      updateVoiceAvailability
    );
    return unsubscribe;
  }, [locale]);

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
    const service = ttsServiceRef.current;
    if (!service || !service.isSupported()) return;

    setError(null);
    setSpeaking(true);
    service.speak(
      text,
      locale,
      () => setSpeaking(false),
      (voiceError) => {
        setSpeaking(false);
        setError(voiceError.message);
      }
    );
  };

  const stopSpeaking = () => {
    ttsServiceRef.current?.cancel();
    setSpeaking(false);
  };

  return {
    supported,
    ttsSupported,
    voiceAvailable,
    voiceLoading,
    availableVoiceLanguages,
    speaking,
    listening,
    error,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}
