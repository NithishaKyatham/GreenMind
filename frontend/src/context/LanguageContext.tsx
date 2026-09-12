import React, { createContext, useContext, useState } from "react";
import en from "../locales/en.json";
import te from "../locales/te.json";
import hi from "../locales/hi.json";
import ta from "../locales/ta.json";
import kn from "../locales/kn.json";
import mr from "../locales/mr.json";

export type Locale = "en" | "te" | "hi" | "ta" | "kn" | "mr";
const dictionaries: Record<Locale, Record<string, string>> = { en, te, hi, ta, kn, mr };

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN", te: "తె", hi: "हि", ta: "த", kn: "ಕ", mr: "म",
};

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
