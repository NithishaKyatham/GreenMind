import React from "react";
import { NavLink } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { PRIMARY_NAV_ITEMS, DESKTOP_ONLY_NAV_ITEMS } from "./navItems";

const linkBase =
  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors";
const linkActive = "bg-primary-100 text-primary-800";
const linkInactive = "text-earth-700 hover:bg-earth-100 hover:text-earth-900";

const DesktopSidebar: React.FC = () => {
  const { t } = useLanguage();
  const items = [...PRIMARY_NAV_ITEMS, ...DESKTOP_ONLY_NAV_ITEMS];

  return (
    <aside className="hidden md:flex md:w-56 md:flex-col md:shrink-0 border-r border-earth-200 bg-white px-3 py-6">
      <nav className="flex flex-col gap-1">
        {items.map(({ to, labelKey, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`}
          >
            <Icon className="h-5 w-5 shrink-0" />
            <span>{t(labelKey)}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default DesktopSidebar;
