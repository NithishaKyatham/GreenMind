import React from "react";
import { useAuth } from "../context/AuthContext";

const Profile: React.FC = () => {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold text-primary-700 mb-6">Profile</h1>
      <div className="bg-white rounded-lg shadow border divide-y">
        {[
          ["Name", user.name],
          ["Email", user.email],
          ["Location", user.location || "Not set"],
          ["Preferred Language", user.preferred_language.toUpperCase()],
          ["Role", user.is_admin ? "Admin" : "Farmer"],
        ].map(([label, value]) => (
          <div key={label} className="flex justify-between p-4">
            <span className="text-gray-500 text-sm">{label}</span>
            <span className="font-medium text-sm">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Profile;
