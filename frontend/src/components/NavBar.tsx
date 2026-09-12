import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage, LOCALE_LABELS, Locale } from "../context/LanguageContext";

const NavBar: React.FC = () => {
  const { user, logout } = useAuth();
  const { t, locale, setLocale } = useLanguage();
  const navigate = useNavigate();

  return (
    <nav className="bg-primary-700 text-white px-6 py-3 flex items-center justify-between shadow">
      <Link to="/" className="text-xl font-bold tracking-tight">
        🌱 {t("app_name")}
      </Link>
      <div className="flex items-center gap-5 text-sm">
        {user ? (
          <>
            <Link to="/dashboard" className="hover:underline">{t("nav_dashboard")}</Link>
            <Link to="/detect" className="hover:underline">{t("nav_detect")}</Link>
            <Link to="/history" className="hover:underline">{t("nav_history")}</Link>
            <Link to="/weather" className="hover:underline">{t("nav_weather")}</Link>
            <Link to="/chat" className="hover:underline">{t("nav_chat")}</Link>
            {user.is_admin && <Link to="/admin" className="hover:underline">Admin</Link>}
            <Link to="/profile" className="hover:underline">{t("nav_profile")}</Link>
            <button
              onClick={() => {
                logout();
                navigate("/");
              }}
              className="bg-primary-600 px-3 py-1 rounded hover:bg-primary-500"
            >
              {t("nav_logout")}
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="hover:underline">{t("nav_login")}</Link>
            <Link to="/register" className="bg-white text-primary-700 px-3 py-1 rounded font-medium">
              {t("nav_register")}
            </Link>
          </>
        )}
        <select
          value={locale}
          onChange={(e) => setLocale(e.target.value as Locale)}
          className="bg-primary-600 text-white text-xs rounded px-2 py-1 border-none"
        >
          {Object.entries(LOCALE_LABELS).map(([code, label]) => (
            <option key={code} value={code}>{label}</option>
          ))}
        </select>
      </div>
    </nav>
  );
};

export default NavBar;
