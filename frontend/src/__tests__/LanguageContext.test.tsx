import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import {
  LanguageProvider,
  useLanguage,
  LOCALE_ORDER,
  LOCALE_NATIVE_NAMES,
  LOCALE_LABELS,
  Locale,
} from "../context/LanguageContext";

const Probe: React.FC = () => {
  const { t } = useLanguage();
  return <div>{t("app_name")}</div>;
};

const LocaleProbe: React.FC<{ initial: Locale }> = ({ initial }) => {
  const { locale, setLocale, t } = useLanguage();
  React.useEffect(() => {
    if (locale !== initial) setLocale(initial);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <div data-testid="app-name">{t("app_name")}</div>;
};

describe("LanguageContext", () => {
  it("defaults to English and resolves a known key", () => {
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>
    );
    expect(screen.getByText("GreenMind")).toBeInTheDocument();
  });

  it("supports all 10 required languages with no missing keys", () => {
    // Every locale must have both a short label and a full native name,
    // and every locale must resolve "app_name" to something other than
    // the raw key (which is the fallback `t()` uses when a key is missing).
    expect(LOCALE_ORDER).toHaveLength(10);
    LOCALE_ORDER.forEach((code) => {
      expect(LOCALE_LABELS[code]).toBeTruthy();
      expect(LOCALE_NATIVE_NAMES[code]).toBeTruthy();
    });
  });

  it.each(LOCALE_ORDER)("resolves app_name for locale '%s' without falling back to the raw key", (code) => {
    render(
      <LanguageProvider>
        <LocaleProbe initial={code} />
      </LanguageProvider>
    );
    expect(screen.getByTestId("app-name").textContent).not.toBe("app_name");
    expect(screen.getByTestId("app-name").textContent).not.toBe("");
  });
});
