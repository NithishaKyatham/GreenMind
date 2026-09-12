import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { LanguageProvider, useLanguage } from "../context/LanguageContext";

const Probe: React.FC = () => {
  const { t } = useLanguage();
  return <div>{t("app_name")}</div>;
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
});
