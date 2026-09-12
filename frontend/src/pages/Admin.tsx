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

const Admin: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);

  useEffect(() => {
    getAdminStats().then((res) => setStats(res.data));
    getAdminUsers().then((res) => setUsers(res.data));
  }, []);

  if (!stats) return <div className="p-8 text-center text-gray-500">Loading admin dashboard...</div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-primary-700 mb-6">Admin Dashboard</h1>

      <div className="grid md:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <p className="text-sm text-gray-500">Total Users</p>
          <p className="text-3xl font-bold text-primary-700">{stats.total_users}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <p className="text-sm text-gray-500">Total Predictions</p>
          <p className="text-3xl font-bold text-primary-700">{stats.total_predictions}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="font-semibold mb-3">Most Detected Diseases</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.most_detected_diseases}>
              <XAxis dataKey="disease" tick={{ fontSize: 9 }} interval={0} angle={-30} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#2e7d32" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="font-semibold mb-3">Most Analyzed Crops</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.most_analyzed_crops}>
              <XAxis dataKey="crop" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#8d6e46" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h2 className="font-semibold mb-3">Users</h2>
      <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="p-3">Name</th>
              <th className="p-3">Email</th>
              <th className="p-3">Predictions</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="p-3">{u.name}</td>
                <td className="p-3">{u.email}</td>
                <td className="p-3">{u.prediction_count}</td>
                <td className="p-3">{u.is_active ? "Active" : "Disabled"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Admin;
