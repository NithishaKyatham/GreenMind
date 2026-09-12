import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Register: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", location: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({ ...form, preferred_language: "en" });
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 bg-white p-8 rounded-lg shadow border border-gray-100">
      <h1 className="text-2xl font-bold text-primary-700 mb-6">Create your GreenMind account</h1>
      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded mb-4">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Full Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Password (min 8 characters)</label>
          <input type="password" required minLength={8} value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Location (village, district, state)</label>
          <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })}
            className="w-full border rounded px-3 py-2" placeholder="e.g. Warangal, Telangana, India" />
        </div>
        <button type="submit" disabled={loading}
          className="w-full bg-primary-600 text-white py-2 rounded font-medium hover:bg-primary-700 disabled:opacity-50">
          {loading ? "Creating account..." : "Register"}
        </button>
      </form>
      <p className="text-sm text-gray-600 mt-4 text-center">
        Already have an account? <Link to="/login" className="text-primary-700 font-medium">Login</Link>
      </p>
    </div>
  );
};

export default Register;
