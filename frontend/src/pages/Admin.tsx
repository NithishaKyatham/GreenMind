import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getAdminStats, getAdminUsers } from "../api/disease";

interface Stats {
  total_users: number;
  total_predictions: number;
  most_detected_diseases: { disease: string; count: number }[];
  most_analyzed_crops: { crop: string; count: number }[];
}

interface AdminUser {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
  prediction_count: number;
}

// Admin is an internal tool for agricultural staff, not the farmer-facing
// app — kept on the shared visual design tokens for consistency, but not
// run through the farmer-facing i18n system (the brief's translation
// requirements are scoped to farmer-facing UI).
const Admin: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);

  useEffect(() => {
    getAdminStats().then((res) => setStats(res.data));
    getAdminUsers().then((res) => setUsers(res.data));
  }, []);

  if (!stats) return <div className="p-8 text-center text-earth-500">Loading admin dashboard...</div>;

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6">
      <h1 className="text-2xl font-semibold text-earth-900 mb-6">Admin Dashboard</h1>

      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-soft border border-earth-200 p-5">
          <p className="text-sm text-earth-500">Total Users</p>
          <p className="text-3xl font-semibold text-primary-700">{stats.total_users}</p>
        </div>
        <div className="bg-white rounded-lg shadow-soft border border-earth-200 p-5">
          <p className="text-sm text-earth-500">Total Predictions</p>
          <p className="text-3xl font-semibold text-primary-700">{stats.total_predictions}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-soft border border-earth-200 p-5">
          <h2 className="font-semibold text-earth-900 mb-3">Most Detected Diseases</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.most_detected_diseases}>
              <XAxis dataKey="disease" tick={{ fontSize: 9 }} interval={0} angle={-30} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#4C8F39" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-lg shadow-soft border border-earth-200 p-5">
          <h2 className="font-semibold text-earth-900 mb-3">Most Analyzed Crops</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.most_analyzed_crops}>
              <XAxis dataKey="crop" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#C9862A" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h2 className="font-semibold text-earth-900 mb-3">Users</h2>
      <div className="bg-white rounded-lg shadow-soft border border-earth-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-earth-50 text-left">
            <tr>
              <th className="p-3 text-earth-700">Name</th>
              <th className="p-3 text-earth-700">Email</th>
              <th className="p-3 text-earth-700">Predictions</th>
              <th className="p-3 text-earth-700">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-earth-100">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="p-3 text-earth-900">{u.name}</td>
                <td className="p-3 text-earth-700">{u.email}</td>
                <td className="p-3 text-earth-700">{u.prediction_count}</td>
                <td className="p-3">
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium ${
                      u.is_active ? "bg-primary-50 text-primary-700" : "bg-earth-100 text-earth-500"
                    }`}
                  >
                    {u.is_active ? "Active" : "Disabled"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Admin;
