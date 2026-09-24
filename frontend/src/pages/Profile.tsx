import React from "react";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import LanguageSelector from "../components/LanguageSelector";

const Profile: React.FC = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  if (!user) return null;

  const rows: [string, string][] = [
    [t("profile_name"), user.name],
    [t("profile_email"), user.email],
    [t("profile_location"), user.location || t("profile_location_not_set")],
    [t("profile_preferred_language"), user.preferred_language.toUpperCase()],
    [t("profile_role"), user.is_admin ? t("profile_role_admin") : t("profile_role_farmer")],
  ];

  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      <h1 className="text-2xl font-semibold text-earth-900 mb-6">{t("profile_title")}</h1>
      <div className="bg-white rounded-lg shadow-soft border border-earth-200 divide-y divide-earth-100">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 p-4">
            <span className="text-earth-500 text-sm">{label}</span>
            <span className="font-medium text-sm text-earth-900 text-right">{value}</span>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow-soft border border-earth-200 p-4 mt-6">
        {/* Changes the app's display language immediately. Note: this updates
            the local UI locale only — it does not yet call a backend endpoint
            to persist preferred_language on the User record, since no such
            update endpoint exists in the current auth API. That wiring is
            tracked as a follow-up, not silently implied here. */}
        <LanguageSelector />
      </div>
    </div>
  );
};

export default Profile;
