import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { LanguageProvider, useLanguage } from "../context/LanguageContext";
import LanguageSelector from "../components/LanguageSelector";

const LocaleReadout: React.FC = () => {
  const { locale } = useLanguage();
  return <div data-testid="current-locale">{locale}</div>;
};

describe("LanguageSelector", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders one option per supported language, including the 4 newly added ones", () => {
    render(
      <LanguageProvider>
        <LanguageSelector />
      </LanguageProvider>
    );
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(10);
    // Newly added languages for this phase.
    expect(screen.getByText("മലയാളം")).toBeInTheDocument();
    expect(screen.getByText("বাংলা")).toBeInTheDocument();
    expect(screen.getByText("ગુજરાતી")).toBeInTheDocument();
    expect(screen.getByText("ਪੰਜਾਬੀ")).toBeInTheDocument();
  });

  it("updates the shared locale (and persists it) when a language is picked", () => {
    render(
      <LanguageProvider>
        <LanguageSelector />
        <LocaleReadout />
      </LanguageProvider>
    );
    fireEvent.click(screen.getByText("বাংলা"));
    expect(screen.getByTestId("current-locale").textContent).toBe("bn");
    expect(localStorage.getItem("greenmind_locale")).toBe("bn");
  });
});
