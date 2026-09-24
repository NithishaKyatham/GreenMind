export interface VoiceAvailability {
  available: boolean;
  loading: boolean;
  voice: SpeechSynthesisVoice | null;
}

export interface AvailableVoiceLanguage {
  code: string;
  name: string;
  flag: string;
}

function languageName(code: string): string {
  try {
    return new Intl.DisplayNames(["en"], { type: "language" }).of(code) || code;
  } catch {
    return code;
  }
}

function flagForRegion(region: string | undefined): string {
  if (!region || !/^[A-Za-z]{2}$/.test(region)) return "";
  return region
    .toUpperCase()
    .split("")
    .map((letter) => String.fromCodePoint(letter.charCodeAt(0) + 127397))
    .join("");
}

/** Reads and deduplicates the languages currently exposed by the browser. */
export function getAvailableVoiceLanguages(
  voices: readonly SpeechSynthesisVoice[]
): AvailableVoiceLanguage[] {
  const detected = new Map<string, AvailableVoiceLanguage>();

  for (const voice of voices) {
    const parts = voice.lang.split("-");
    const code = parts[0].toLowerCase();
    if (!code || detected.has(code)) continue;
    detected.set(code, {
      code,
      name: languageName(code),
      flag: flagForRegion(parts.find((part) => /^[A-Za-z]{2}$/.test(part))),
    });
  }

  return [...detected.values()];
}

/** Selects only an exact locale or the same language prefix. */
export function findVoiceForLocale(
  voices: readonly SpeechSynthesisVoice[],
  locale: string
): SpeechSynthesisVoice | null {
  const requested = locale.toLowerCase();
  const language = requested.split("-")[0];

  return (
    voices.find((voice) => voice.lang.toLowerCase() === requested) ||
    voices.find((voice) => voice.lang.toLowerCase().split("-")[0] === language) ||
    null
  );
}

export function getVoiceAvailability(
  voices: readonly SpeechSynthesisVoice[],
  locale: string,
  loading = voices.length === 0
): VoiceAvailability {
  const voice = findVoiceForLocale(voices, locale);
  return { available: !!voice, loading, voice };
}
