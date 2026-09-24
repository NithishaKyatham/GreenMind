import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";

const Login: React.FC = () => {
  const { login } = useAuth();
  const { t } = useLanguage();
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
      setError(err.response?.data?.detail || t("auth_error_login_failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 bg-white p-8 rounded-lg shadow-soft border border-earth-200">
      <h1 className="text-2xl font-semibold text-earth-900 mb-6">{t("auth_login_title")}</h1>
      {error && <div className="bg-danger-50 text-danger-700 text-sm p-3 rounded-md mb-4">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-earth-700 mb-1">{t("auth_email")}</label>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-earth-200 rounded-md px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium text-earth-700 mb-1">{t("auth_password")}</label>
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-earth-200 rounded-md px-3 py-2" />
        </div>
        <button type="submit" disabled={loading}
          className="w-full bg-primary-600 text-white py-2 rounded-md font-semibold hover:bg-primary-700 disabled:opacity-50 transition-colors">
          {loading ? t("auth_login_loading") : t("auth_login_button")}
        </button>
      </form>
      <p className="text-sm text-earth-600 mt-4 text-center">
        {t("auth_no_account")} <Link to="/register" className="text-primary-700 font-medium hover:text-primary-800">{t("auth_register_link")}</Link>
      </p>
    </div>
  );
};

export default Login;
