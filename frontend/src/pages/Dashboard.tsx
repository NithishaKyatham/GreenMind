import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { getHistory, getWeather } from "../api/disease";
import PredictionThumbnail from "../components/PredictionThumbnail";

interface HistoryItem {
  id: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: string;
  created_at: string;
}

interface WeatherData {
  location: string;
  temperature: number | null;
  humidity: number | null;
  condition: string | null;
  source: string;
  message: string | null;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherQuery, setWeatherQuery] = useState("");

  useEffect(() => {
    getHistory()
      .then((res) => setHistory(res.data))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!user?.location) return;
    setWeatherLoading(true);
    getWeather(user.location)
      .then((res) => setWeather(res.data))
      .catch(() => setWeather(null))
      .finally(() => setWeatherLoading(false));
  }, [user?.location]);

  const searchWeather = (e: React.FormEvent) => {
    e.preventDefault();
    if (!weatherQuery.trim()) return;
    setWeatherLoading(true);
    getWeather(weatherQuery.trim())
      .then((res) => setWeather(res.data))
      .catch(() => setWeather(null))
      .finally(() => setWeatherLoading(false));
  };

  // "Unable to confidently identify" is a literal status string the backend
  // returns (not a disease name) — checked against the raw (untranslated)
  // API value, never the translated display string.
  const isLowConfidence = (item: HistoryItem) =>
    item.disease === "Unable to confidently identify" || item.confidence < 0.6;
  const isHealthy = (item: HistoryItem) => !isLowConfidence(item) && item.disease.toLowerCase() === "healthy";

  const getDisplayDisease = (item: HistoryItem) =>
    isLowConfidence(item) ? t("dashboard_unable_identify") : item.disease;

  const severityLabel = (severity: string) => {
    if (severity === "High") return t("severity_high");
    if (severity === "Medium") return t("severity_medium");
    if (severity === "Low") return t("severity_low");
    return severity;
  };

  const healthyCount = history.filter(isHealthy).length;
  const lowConfidenceCount = history.filter(isLowConfidence).length;
  const diseaseCount = history.length - healthyCount - lowConfidenceCount;

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-earth-900 mb-1">
            {t("dashboard_welcome")}, {user?.name} <span aria-hidden="true">👋</span>
          </h1>
          <p className="text-earth-600">{t("dashboard_overview")}</p>
        </div>
        <Link
          to="/detect"
          className="inline-flex items-center justify-center gap-2 bg-primary-600 text-white px-5 py-3 rounded-md font-semibold hover:bg-primary-700 transition-colors shrink-0"
        >
          <span aria-hidden="true">📷</span> {t("dashboard_new_diagnosis")}
        </Link>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Left / main column */}
        <div className="md:col-span-2 space-y-6">
          {/* Crop health summary — derived from the farmer's real history,
              never a fabricated aggregate. */}
          <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-5">
            <h2 className="font-semibold text-earth-900 mb-4">{t("dashboard_health_summary")}</h2>
            {loading ? (
              <p className="text-sm text-earth-500">{t("dashboard_loading")}</p>
            ) : history.length === 0 ? (
              <p className="text-sm text-earth-500">{t("dashboard_no_predictions")}</p>
            ) : (
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <p className="text-2xl font-semibold text-primary-700">{healthyCount}</p>
                  <p className="text-xs text-earth-500 mt-1">{t("status_healthy")}</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-danger-500">{diseaseCount}</p>
                  <p className="text-xs text-earth-500 mt-1">{t("dashboard_disease_detected")}</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-info-500">{lowConfidenceCount}</p>
                  <p className="text-xs text-earth-500 mt-1">{t("dashboard_low_confidence")}</p>
                </div>
              </div>
            )}
          </div>

          {/* Recent diagnoses */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-earth-900">{t("dashboard_recent_detections")}</h2>
              {history.length > 0 && (
                <Link to="/history" className="text-sm font-medium text-primary-700 hover:text-primary-800">
                  {t("nav_history")}
                </Link>
              )}
            </div>

            {loading ? (
              <p className="text-sm text-earth-500">{t("dashboard_loading")}</p>
            ) : history.length === 0 ? (
              <div className="bg-white rounded-lg border border-earth-200 p-6 text-center">
                <p className="text-earth-500 text-sm mb-3">{t("dashboard_no_predictions")}</p>
                <Link to="/detect" className="text-primary-700 font-medium text-sm hover:text-primary-800">
                  {t("dashboard_upload_leaf")}
                </Link>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-3">
                {history.slice(0, 4).map((item) => {
                  const lowConf = isLowConfidence(item);
                  return (
                    <Link
                      key={item.id}
                      to={`/result/${item.id}`}
                      className="flex gap-3 bg-white rounded-lg border border-earth-200 p-3 hover:border-primary-300 hover:shadow-soft transition-all"
                    >
                      <PredictionThumbnail
                        predictionId={item.id}
                        alt={item.crop}
                        className="h-14 w-14 rounded-md object-cover shrink-0"
                      />
                      <div className="min-w-0">
                        <p className="font-medium text-sm text-earth-900 truncate">
                          {item.crop} — {getDisplayDisease(item)}
                        </p>
                        <p className="text-xs text-earth-500 mb-1.5">
                          {new Date(item.created_at).toLocaleDateString()}
                        </p>
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                            lowConf
                              ? "bg-info-50 text-info-700"
                              : item.severity === "High"
                              ? "bg-danger-50 text-danger-700"
                              : item.severity === "Medium"
                              ? "bg-accent-50 text-accent-700"
                              : "bg-primary-50 text-primary-700"
                          }`}
                        >
                          {lowConf ? t("dashboard_low_confidence") : severityLabel(item.severity)}
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right column: weather + quick actions */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-5">
            <h2 className="font-semibold text-earth-900 mb-3 flex items-center gap-2">
              <span aria-hidden="true">☁️</span> {t("nav_weather")}
            </h2>

            {!user?.location && !weather && (
              <form onSubmit={searchWeather} className="flex gap-2 mb-2">
                <input
                  value={weatherQuery}
                  onChange={(e) => setWeatherQuery(e.target.value)}
                  placeholder="City, state"
                  className="flex-1 min-w-0 text-sm rounded-md border border-earth-200 px-2.5 py-1.5 focus-visible:outline-none"
                />
                <button
                  type="submit"
                  className="text-sm font-medium bg-primary-600 text-white px-3 rounded-md hover:bg-primary-700"
                >
                  →
                </button>
              </form>
            )}

            {weatherLoading ? (
              <p className="text-sm text-earth-500">{t("dashboard_loading")}</p>
            ) : weather?.source === "unavailable" ? (
              <p className="text-sm text-earth-500">{weather.message}</p>
            ) : weather ? (
              <div>
                <p className="text-sm text-earth-600 mb-1">{weather.location}</p>
                <p className="text-3xl font-semibold text-earth-900">
                  {weather.temperature != null ? `${Math.round(weather.temperature)}°C` : "—"}
                </p>
                <p className="text-sm text-earth-600 capitalize">{weather.condition}</p>
                <Link to="/weather" className="text-xs text-primary-700 font-medium hover:text-primary-800 mt-2 inline-block">
                  {t("nav_weather")} →
                </Link>
              </div>
            ) : (
              <p className="text-sm text-earth-500">—</p>
            )}
          </div>

          <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-5">
            <h2 className="font-semibold text-earth-900 mb-3">{t("dashboard_ask_assistant")}</h2>
            <p className="text-sm text-earth-600 mb-3">{t("dashboard_quick_guidance")}</p>
            <Link
              to="/chat"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-700 hover:text-primary-800"
            >
              <span aria-hidden="true">💬</span> {t("nav_chat")}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
