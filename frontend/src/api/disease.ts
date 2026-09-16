import { apiClient } from "./client";

export const predictDisease = (crop: string, image: File) => {
  const formData = new FormData();
  formData.append("crop", crop);
  formData.append("image", image);
  return apiClient.post("/disease/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getPrediction = (id: string) => apiClient.get(`/disease/${id}`);

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
