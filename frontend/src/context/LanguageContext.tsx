import React, { createContext, useContext, useState } from "react";
import en from "../locales/en.json";
import te from "../locales/te.json";
import hi from "../locales/hi.json";
import ta from "../locales/ta.json";
import kn from "../locales/kn.json";
import mr from "../locales/mr.json";
import ml from "../locales/ml.json";
import bn from "../locales/bn.json";
import gu from "../locales/gu.json";
import pa from "../locales/pa.json";

export type Locale = "en" | "te" | "hi" | "ta" | "kn" | "mr" | "ml" | "bn" | "gu" | "pa";
const dictionaries: Record<Locale, Record<string, string>> = {
  en, te, hi, ta, kn, mr, ml, bn, gu, pa,
};

// Short labels — used in compact UI (e.g. the navbar switcher).
export const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN", te: "తె", hi: "हि", ta: "த", kn: "ಕ", mr: "म", ml: "മ", bn: "বা", gu: "ગુ", pa: "ਪੰ",
};

// Full native names — used in the "Choose your language" selector (section 14 of spec).
export const LOCALE_NATIVE_NAMES: Record<Locale, string> = {
  en: "English",
  te: "తెలుగు",
  hi: "हिन्दी",
  ta: "தமிழ்",
  kn: "ಕನ್ನಡ",
  ml: "മലയാളം",
  mr: "मराठी",
  bn: "বাংলা",
  gu: "ગુજરાતી",
  pa: "ਪੰਜਾਬੀ",
};

// Stable display order for the selector (English first, then the rest
// alphabetically by native script grouping used in the spec).
export const LOCALE_ORDER: Locale[] = ["en", "te", "hi", "ta", "kn", "ml", "mr", "bn", "gu", "pa"];

interface LanguageContextType {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocale] = useState<Locale>(
    (localStorage.getItem("greenmind_locale") as Locale) || "en"
  );

  const changeLocale = (l: Locale) => {
    setLocale(l);
    localStorage.setItem("greenmind_locale", l);
  };

  const t = (key: string): string => dictionaries[locale][key] || dictionaries.en[key] || key;

  return (
    <LanguageContext.Provider value={{ locale, setLocale: changeLocale, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
};
