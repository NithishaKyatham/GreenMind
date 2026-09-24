import React, { createContext, useContext, useEffect, useState } from "react";
import { loginUser, registerUser, getCurrentUser, RegisterPayload } from "../api/auth";

interface User {
  id: string;
  name: string;
  email: string;
  preferred_language: string;
  location?: string;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = async () => {
    const token = localStorage.getItem("greenmind_access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const response = await getCurrentUser();
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await loginUser({ email, password });
    localStorage.setItem("greenmind_access_token", response.data.access_token);
    localStorage.setItem("greenmind_refresh_token", response.data.refresh_token);
    await fetchCurrentUser();
  };

  const register = async (payload: RegisterPayload) => {
    await registerUser(payload);
    await login(payload.email, payload.password);
  };

  const logout = () => {
    localStorage.removeItem("greenmind_access_token");
    localStorage.removeItem("greenmind_refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
