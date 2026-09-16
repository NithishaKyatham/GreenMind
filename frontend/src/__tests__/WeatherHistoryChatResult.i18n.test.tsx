import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import React from "react";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { name: "Asha", location: "" }, loading: false }),
}));

vi.mock("../hooks/useVoice", () => ({
  useVoice: () => ({ supported: false, listening: false, error: null, speak: vi.fn(), startListening: vi.fn(), stopListening: vi.fn() }),
}));

vi.mock("../api/disease", () => ({
  getPredictionImageBlob: vi.fn().mockRejectedValue(new Error("Image unavailable in this component test")),
  getHistory: vi.fn().mockResolvedValue({ data: [] }),
  getWeather: vi.fn(),
  sendChatMessage: vi.fn(),
  getPrediction: vi.fn().mockResolvedValue({
    data: {
      id: "p1",
      crop: "Tomato",
      disease: "Late Blight",
      confidence: 0.9,
      severity: "High",
      status: "confident",
      description: "A fungal disease.",
      is_fallback_prediction: false,
      disclaimer: "Informational only.",
      recommendation: { treatment: "Apply fungicide." },
    },
  }),
  generateReport: vi.fn(),
}));

import { LanguageProvider, useLanguage } from "../context/LanguageContext";
import Weather from "../pages/Weather";
import History from "../pages/History";
import Chat from "../pages/Chat";
import Result from "../pages/Result";

const InTelugu: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { setLocale } = useLanguage();
  React.useEffect(() => {
    setLocale("te");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
};

const renderIn = (ui: React.ReactElement, initialEntries = ["/"]) =>
  render(
    <MemoryRouter initialEntries={initialEntries}>
      <LanguageProvider>
        <InTelugu>
          <Routes>
            <Route path="*" element={ui} />
          </Routes>
        </InTelugu>
      </LanguageProvider>
    </MemoryRouter>
  );

describe("Weather/History/Chat/Result localization", () => {
  it("Weather renders the translated page title and button", async () => {
    renderIn(<Weather />);
    await waitFor(() => {
      expect(screen.getByText("వాతావరణం")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "వాతావరణం పొందండి" })).toBeInTheDocument();
    });
  });

  it("History renders the translated title and empty state", async () => {
    renderIn(<History />);
    await waitFor(() => {
      expect(screen.getByText("అంచనా చరిత్ర")).toBeInTheDocument();
      expect(screen.getByText("ఈ ఫిల్టర్‌లకు సరిపోలే అంచనాలు లేవు.")).toBeInTheDocument();
    });
  });

  it("Chat renders the translated title and input placeholder", async () => {
    renderIn(<Chat />);
    await waitFor(() => {
      expect(screen.getByText("గ్రీన్‌మైండ్ సహాయకుడు")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(
          "పంట వ్యాధులు, ఎరువులు, పురుగుల గురించి గ్రీన్‌మైండ్ సహాయకుడిని అడగండి..."
        )
      ).toBeInTheDocument();
    });
  });

  it("Result renders the translated confidence label and severity", async () => {
    render(
      <MemoryRouter initialEntries={["/result/p1"]}>
        <LanguageProvider>
          <InTelugu>
            <Routes>
              <Route path="/result/:id" element={<Result />} />
            </Routes>
          </InTelugu>
        </LanguageProvider>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(
        screen.getByText((_, element) => element?.tagName.toLowerCase() === "p" && !!element.textContent?.includes("నమ్మకం"))
      ).toBeInTheDocument();
      expect(screen.getByText("ఎక్కువ")).toBeInTheDocument(); // "High" severity
    });
  });
});
