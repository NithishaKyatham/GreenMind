/**
 * Maps GreenMind's internal locale codes (matching Locale in
 * context/LanguageContext.tsx) to BCP-47 language tags used by speech
 * APIs (Web Speech, Azure Speech). Kept in one place so every provider
 * (and any new one added later) references the same 10 languages
 * instead of each hardcoding its own partial list.
 *
 * NOTE: the previous inline copy of this map inside useVoice.ts only had
 * 6 of the 10 supported UI languages (missing ml, bn, gu, pa) — a real
 * gap fixed here, not just refactored.
 */
export const LOCALE_TO_BCP47: Record<string, string> = {
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

export function toBcp47(locale: string): string {
  return LOCALE_TO_BCP47[locale] || "en-IN";
}
