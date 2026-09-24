import React from "react";
import { NavLink } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";
import { PRIMARY_NAV_ITEMS } from "./navItems";

const MobileBottomNav: React.FC = () => {
  const { t } = useLanguage();

  return (
    <nav
      className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-earth-200 pb-[env(safe-area-inset-bottom)]"
      aria-label={t("nav_dashboard")}
    >
      <div className="grid grid-cols-4">
        {PRIMARY_NAV_ITEMS.map(({ to, labelKey, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-1 py-2.5 text-[11px] font-medium leading-none ${
                isActive ? "text-primary-700" : "text-earth-500"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`h-6 w-6 ${isActive ? "text-primary-700" : "text-earth-400"}`} />
                <span className="truncate max-w-[72px]">{t(labelKey)}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};

export default MobileBottomNav;
