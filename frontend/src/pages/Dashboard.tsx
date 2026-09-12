import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getHistory } from "../api/disease";

interface HistoryItem {
  id: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: string;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then((res) => setHistory(res.data))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  const getDisplayDisease = (item: HistoryItem) => {
    if (
      item.disease === "Unable to confidently identify" ||
      item.confidence < 0.6
    ) {
      return "Unable to confidently identify";
    }

    return item.disease;
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-primary-700 mb-1">
        Welcome, {user?.name}
      </h1>

      <p className="text-gray-600 mb-6">
        Here's an overview of your crop health activity.
      </p>

      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <p className="text-sm text-gray-500">Total Predictions</p>

          <p className="text-3xl font-bold text-primary-700">
            {loading ? "—" : history.length}
          </p>
        </div>

        <Link
          to="/detect"
          className="bg-primary-600 text-white rounded-lg p-5 flex flex-col justify-center hover:bg-primary-700"
        >
          <p className="font-semibold">+ New Diagnosis</p>

          <p className="text-sm text-primary-100">
            Upload a leaf image now
          </p>
        </Link>

        <Link
          to="/chat"
          className="bg-white rounded-lg shadow-sm border p-5 hover:bg-primary-50"
        >
          <p className="font-semibold text-primary-700">
            Ask GreenMind Assistant
          </p>

          <p className="text-sm text-gray-500">
            Get quick agricultural guidance
          </p>
        </Link>
      </div>

      <h2 className="text-lg font-semibold text-primary-700 mb-3">
        Recent Detections
      </h2>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : history.length === 0 ? (
        <p className="text-gray-500">
          No predictions yet. Start by uploading a leaf image.
        </p>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border divide-y">
          {history.slice(0, 5).map((item) => {
            const displayDisease = getDisplayDisease(item);
            const isLowConfidence =
              displayDisease === "Unable to confidently identify";

            return (
              <Link
                key={item.id}
                to={`/result/${item.id}`}
                className="flex justify-between items-center p-4 hover:bg-primary-50"
              >
                <div>
                  <p className="font-medium">
                    {item.crop} — {displayDisease}
                  </p>

                  <p className="text-xs text-gray-500">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>

                <span
                  className={`text-xs px-2 py-1 rounded font-medium ${
                    isLowConfidence
                      ? "bg-blue-100 text-blue-700"
                      : item.severity === "High"
                      ? "bg-red-100 text-red-700"
                      : item.severity === "Medium"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-green-100 text-green-700"
                  }`}
                >
                  {isLowConfidence ? "Low confidence" : item.severity}
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Dashboard;