import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import React from "react";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { name: "Asha", id: "u1" }, loading: false }),
}));

vi.mock("../api/disease", () => ({
  getPredictionImageBlob: vi.fn().mockRejectedValue(new Error("Image unavailable in this component test")),
  getHistory: vi.fn().mockResolvedValue({
    data: [
      {
        id: "p1",
        crop: "Tomato",
        disease: "Unable to confidently identify",
        confidence: 0.4,
        severity: "Low",
        created_at: new Date().toISOString(),
      },
      {
        id: "p2",
        crop: "Potato",
        disease: "Late Blight",
        confidence: 0.91,
        severity: "High",
        created_at: new Date().toISOString(),
      },
    ],
  }),
}));

import { LanguageProvider, useLanguage } from "../context/LanguageContext";
import Dashboard from "../pages/Dashboard";

// Forces the dashboard to render in Bengali, to prove the low-confidence
// detection logic works off the raw API value rather than the (translated)
// display string — see the bug this guards against in Dashboard.tsx.
const BengaliDashboard: React.FC = () => {
  const { setLocale } = useLanguage();
  React.useEffect(() => {
    setLocale("bn");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <Dashboard />;
};

describe("Dashboard localization", () => {
  it("renders fully in the selected language, not just labels", async () => {
    render(
      <MemoryRouter>
        <LanguageProvider>
          <BengaliDashboard />
        </LanguageProvider>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText(/আসা|Asha/)).toBeInTheDocument());

    // Section headings and static copy must be Bengali, not hardcoded English.
    expect(screen.getByText("গ্রিনমাইন্ড সহকারীকে জিজ্ঞাসা করুন")).toBeInTheDocument();
    expect(screen.getByText("সাম্প্রতিক শনাক্তকরণ")).toBeInTheDocument();

    // The low-confidence prediction must show the translated status, and
    // the high-confidence one must show its translated severity — proving
    // the badge logic still works correctly once display text is localized.
    await waitFor(() => {
      expect(screen.getByText((_, element) => element?.tagName.toLowerCase() === "p" && !!element.textContent?.includes("নিশ্চিতভাবে শনাক্ত করা যায়নি"))).toBeInTheDocument();
      expect(screen.getByText("বেশি")).toBeInTheDocument(); // "High" severity, translated
    });
  });
});
