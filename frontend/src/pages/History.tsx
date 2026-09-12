import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../api/disease";

interface HistoryItem {
  id: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: string;
  created_at: string;
}

const History: React.FC = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [crop, setCrop] = useState("");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("latest");
  const [loading, setLoading] = useState(true);

  const fetchHistory = () => {
    setLoading(true);

    const params: Record<string, string> = { sort };

    if (crop.trim()) {
      params.crop = crop.trim();
    }

    if (q.trim()) {
      params.q = q.trim();
    }

    getHistory(params)
      .then((res) => setItems(res.data))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, [sort]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-primary-700 mb-4">
        Prediction History
      </h1>

      <div className="flex gap-3 mb-4 flex-wrap">
        <input
          placeholder="Search disease..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              fetchHistory();
            }
          }}
          className="border rounded px-3 py-2 text-sm flex-1 min-w-[180px]"
        />

        <input
          placeholder="Filter by crop..."
          value={crop}
          onChange={(e) => setCrop(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              fetchHistory();
            }
          }}
          className="border rounded px-3 py-2 text-sm"
        />

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="latest">Latest first</option>
          <option value="oldest">Oldest first</option>
        </select>

        <button
          onClick={fetchHistory}
          className="bg-primary-600 text-white px-4 py-2 rounded text-sm hover:bg-primary-700"
        >
          Apply
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : items.length === 0 ? (
        <p className="text-gray-500">
          No predictions match these filters.
        </p>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border divide-y">
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/history/${item.id}`}
              className="flex justify-between items-center p-4 hover:bg-primary-50"
            >
              <div>
                <p className="font-medium">
                  {item.crop} — {item.disease}
                </p>

                <p className="text-xs text-gray-500">
                  {new Date(item.created_at).toLocaleString()}
                </p>
              </div>

              <div className="text-right">
                <p className="text-sm">
                  {(item.confidence * 100).toFixed(0)}%
                </p>

                <p className="text-xs text-gray-500">
                  {item.severity}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default History;