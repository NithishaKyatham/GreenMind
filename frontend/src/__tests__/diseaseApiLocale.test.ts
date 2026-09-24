import { describe, expect, it, vi } from "vitest";

const { post, get } = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
}));

vi.mock("../api/client", () => ({
  apiClient: { post, get },
}));

import { getPrediction, predictDisease } from "../api/disease";

describe("disease API locale propagation", () => {
  it("sends the selected locale with the crop prediction request", async () => {
    post.mockResolvedValue({ data: { id: "p1" } });
    const image = new File(["image"], "leaf.png", { type: "image/png" });

    await predictDisease("Tomato", image, "te");

    const formData = post.mock.calls[0][1] as FormData;
    expect(formData.get("crop")).toBe("Tomato");
    expect(formData.get("locale")).toBe("te");
  });

  it("sends the selected locale when retrieving a stored prediction", async () => {
    get.mockResolvedValue({ data: { id: "p1" } });

    await getPrediction("p1", "hi");

    expect(get).toHaveBeenCalledWith("/disease/p1", { params: { locale: "hi" } });
  });
});
