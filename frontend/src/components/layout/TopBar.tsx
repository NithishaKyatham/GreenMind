import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useLanguage, LOCALE_NATIVE_NAMES, LOCALE_ORDER, Locale } from "../../context/LanguageContext";
import { UserIcon, CloudIcon, LogoutIcon, ShieldIcon } from "./icons";

const TopBar: React.FC = () => {
  const { user, logout } = useAuth();
  const { t, locale, setLocale } = useLanguage();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-earth-200">
      <div className="mx-auto max-w-7xl px-4 md:px-6 h-16 flex items-center justify-between gap-4">
        <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2 shrink-0">
          <span className="text-xl" aria-hidden="true">🌱</span>
          <span className="text-lg font-semibold text-primary-800 tracking-tight">{t("app_name")}</span>
        </Link>

        <div className="flex items-center gap-2 md:gap-3">
          <label className="sr-only" htmlFor="topbar-locale">Language</label>
          <select
            id="topbar-locale"
            value={locale}
            onChange={(e) => setLocale(e.target.value as Locale)}
            className="text-sm rounded-md border border-earth-200 bg-earth-50 px-2 py-1.5 text-earth-700 focus-visible:outline-none"
          >
            {LOCALE_ORDER.map((code) => (
              <option key={code} value={code}>
                {LOCALE_NATIVE_NAMES[code]}
              </option>
            ))}
          </select>

          {user ? (
            <details className="relative group">
              <summary className="list-none flex items-center gap-2 rounded-full border border-earth-200 pl-1 pr-3 py-1 cursor-pointer select-none hover:bg-earth-50">
                <span className="h-7 w-7 rounded-full bg-primary-100 text-primary-800 flex items-center justify-center text-sm font-semibold">
                  {user.name?.[0]?.toUpperCase() || "?"}
                </span>
                <span className="hidden sm:inline text-sm font-medium text-earth-800 max-w-[120px] truncate">
                  {user.name}
                </span>
              </summary>
              <div className="absolute right-0 mt-2 w-52 rounded-md border border-earth-200 bg-white shadow-soft py-1 text-sm">
                <Link
                  to="/weather"
                  className="md:hidden flex items-center gap-2 px-3 py-2 text-earth-700 hover:bg-earth-50"
                >
                  <CloudIcon className="h-4 w-4" /> {t("nav_weather")}
                </Link>
                <Link to="/profile" className="flex items-center gap-2 px-3 py-2 text-earth-700 hover:bg-earth-50">
                  <UserIcon className="h-4 w-4" /> {t("nav_profile")}
                </Link>
                {user.is_admin && (
                  <Link to="/admin" className="flex items-center gap-2 px-3 py-2 text-earth-700 hover:bg-earth-50">
                    <ShieldIcon className="h-4 w-4" /> Admin
                  </Link>
                )}
                <button
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left text-danger-500 hover:bg-danger-50"
                >
                  <LogoutIcon className="h-4 w-4" /> {t("nav_logout")}
                </button>
              </div>
            </details>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login" className="text-sm font-medium text-earth-700 hover:text-earth-900 px-2 py-1.5">
                {t("nav_login")}
              </Link>
              <Link
                to="/register"
                className="text-sm font-semibold bg-primary-600 text-white px-3.5 py-1.5 rounded-md hover:bg-primary-700 transition-colors"
              >
                {t("nav_register")}
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default TopBar;
