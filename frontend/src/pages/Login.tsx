import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 bg-white p-8 rounded-lg shadow border border-gray-100">
      <h1 className="text-2xl font-bold text-primary-700 mb-6">Login to GreenMind</h1>
      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded mb-4">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className="w-full border rounded px-3 py-2" />
        </div>
        <button type="submit" disabled={loading}
          className="w-full bg-primary-600 text-white py-2 rounded font-medium hover:bg-primary-700 disabled:opacity-50">
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
      <p className="text-sm text-gray-600 mt-4 text-center">
        No account? <Link to="/register" className="text-primary-700 font-medium">Register</Link>
      </p>
    </div>
  );
};

export default Login;
