import { apiClient } from "./client";

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  preferred_language?: string;
  location?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const registerUser = (payload: RegisterPayload) =>
  apiClient.post("/auth/register", payload);

export const loginUser = (payload: LoginPayload) =>
  apiClient.post("/auth/login", payload);

export const getCurrentUser = () => apiClient.get("/auth/me");
