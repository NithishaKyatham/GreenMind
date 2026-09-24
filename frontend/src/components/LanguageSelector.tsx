import React from "react";
import { useLanguage, LOCALE_NATIVE_NAMES, LOCALE_ORDER, Locale } from "../context/LanguageContext";

interface LanguageSelectorProps {
  /** Optional heading shown above the language grid. Defaults to a bilingual prompt. */
  title?: string;
  /** Called after the user picks a language, in addition to updating the app locale. */
  onSelect?: (locale: Locale) => void;
  className?: string;
}

/**
 * Full "Choose your language" selector — a grid of large, tappable buttons
 * showing each language's native name, for onboarding, dashboard, and
 * settings contexts. For a compact inline switcher (e.g. the navbar), the
 * plain <select> driven by LOCALE_LABELS is used instead.
 */
const LanguageSelector: React.FC<LanguageSelectorProps> = ({ title, onSelect, className }) => {
  const { locale, setLocale } = useLanguage();

  return (
    <div className={className}>
      <h2 className="text-lg font-semibold text-gray-700 mb-3">
        {title ?? "Choose your language / భాష ఎంచుకోండి"}
      </h2>
      <div
        role="listbox"
        aria-label="Choose your language"
        className="grid grid-cols-2 sm:grid-cols-3 gap-3"
      >
        {LOCALE_ORDER.map((code) => {
          const selected = code === locale;
          return (
            <button
              key={code}
              type="button"
              role="option"
              aria-selected={selected}
              onClick={() => {
                setLocale(code);
                onSelect?.(code);
              }}
              className={`flex items-center justify-center gap-2 rounded-lg border-2 px-4 py-4 text-base font-medium transition-colors min-h-[56px] ${
                selected
                  ? "border-primary-600 bg-primary-50 text-primary-700"
                  : "border-gray-200 bg-white text-gray-800 hover:border-primary-300"
              }`}
            >
              <span aria-hidden="true">🇮🇳</span>
              <span>{LOCALE_NATIVE_NAMES[code]}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default LanguageSelector;
