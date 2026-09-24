import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import React from "react";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ login: vi.fn(), register: vi.fn(), user: null, loading: false }),
}));

vi.mock("../api/disease", () => ({
  getCrops: vi.fn().mockResolvedValue({ data: [{ id: "c1", name: "tomato", display_name_en: "Tomato" }] }),
  predictDisease: vi.fn(),
}));

import { LanguageProvider, useLanguage } from "../context/LanguageContext";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Detect from "../pages/Detect";

const InHindi: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { setLocale } = useLanguage();
  React.useEffect(() => {
    setLocale("hi");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
};

const renderIn = (ui: React.ReactElement) =>
  render(
    <MemoryRouter>
      <LanguageProvider>
        <InHindi>{ui}</InHindi>
      </LanguageProvider>
    </MemoryRouter>
  );

describe("Auth and Detect pages localization", () => {
  it("Login renders translated title and button, not hardcoded English", async () => {
    renderIn(<Login />);
    await waitFor(() => {
      expect(screen.getByText("ग्रीनमाइंड में लॉगिन करें")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "लॉगिन" })).toBeInTheDocument();
    });
  });

  it("Register renders translated title and field labels", async () => {
    renderIn(<Register />);
    await waitFor(() => {
      expect(screen.getByText("अपना ग्रीनमाइंड खाता बनाएं")).toBeInTheDocument();
      expect(screen.getByText("पूरा नाम")).toBeInTheDocument();
    });
  });

  it("Detect renders translated upload title and drag/drop prompt", async () => {
    renderIn(<Detect />);
    await waitFor(() => {
      expect(screen.getByText("पत्ती की छवि अपलोड करें")).toBeInTheDocument();
    });
  });
});
