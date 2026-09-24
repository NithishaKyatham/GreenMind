import { apiClient } from "./client";

export interface PredictionContextInput {
  season?: string;
  region?: string;
  crop_stage?: string;
  soil_info?: string;
}

export const predictDisease = (
  crop: string,
  image: File,
  locale = "en",
  context: PredictionContextInput = {},
) => {
  const formData = new FormData();
  formData.append("crop", crop);
  formData.append("locale", locale);
  Object.entries(context).forEach(([key, value]) => {
    if (value?.trim()) formData.append(key, value.trim());
  });
  formData.append("image", image);
  return apiClient.post("/disease/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getPrediction = (id: string, locale = "en") =>
  apiClient.get(`/disease/${id}`, { params: { locale } });

export const getPredictionImageBlob = (id: string) =>
  apiClient.get(`/disease/${id}/image`, { responseType: "blob" });

export const getCrops = () => apiClient.get("/crops");

export const getHistory = (params?: Record<string, string>) =>
  apiClient.get("/history", { params });

export const getWeather = (location: string) =>
  apiClient.get("/weather", { params: { location } });

export const sendChatMessage = (message: string, conversationId?: string, locale?: string) =>
  apiClient.post("/chatbot/message", { message, conversation_id: conversationId, locale });

export const generateReport = (predictionId: string) =>
  apiClient.post(`/reports/generate/${predictionId}`);

export const getAdminStats = () => apiClient.get("/admin/stats");
export const getAdminUsers = () => apiClient.get("/admin/users");
