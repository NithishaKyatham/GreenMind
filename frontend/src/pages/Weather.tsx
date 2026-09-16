import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getWeather } from "../api/disease";
import { useLanguage } from "../context/LanguageContext";

interface ForecastDay {
  date: string;
  temp_min: number;
  temp_max: number;
  condition: string;
  rain_probability?: number;
}

interface WeatherData {
  location: string;
  temperature: number | null;
  humidity: number | null;
  rainfall: number | null;
  condition: string | null;
  wind_speed: number | null;
  forecast: ForecastDay[];
  source: "live" | "unavailable";
  message: string | null;
}

const Weather: React.FC = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [location, setLocation] = useState(user?.location || "");
  const [data, setData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchWeather = async (loc?: string) => {
    const target = loc ?? location;
    if (!target) return;
    setLoading(true);
    try {
      const res = await getWeather(target);
      setData(res.data);
    } finally {
      setLoading(false);
    }
  };

  // Weather is useful, not decorative — load it automatically when the
  // farmer has a saved location instead of requiring a manual search.
  useEffect(() => {
    if (user?.location) fetchWeather(user.location);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.location]);

  const rainSoon =
    data?.source === "live" &&
    data.forecast.slice(0, 2).some((d) => (d.rain_probability ?? 0) >= 50);

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-8">
      <h1 className="text-2xl font-semibold text-earth-900 mb-4">{t("nav_weather")}</h1>
      <div className="flex gap-3 mb-6">
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchWeather()}
          placeholder={t("weather_location_placeholder")}
          className="flex-1 border border-earth-200 rounded-md px-3 py-2 bg-white"
        />
        <button
          onClick={() => fetchWeather()}
          disabled={loading}
          className="bg-primary-600 text-white px-4 py-2 rounded-md font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? t("dashboard_loading") : t("weather_get_button")}
        </button>
      </div>

      {data && data.source === "unavailable" && (
        <div className="bg-accent-50 text-accent-700 p-4 rounded-md border border-accent-100">
          {/* data.message is a live status string from the backend and is
              not translated — the backend has no i18n support for these
              messages yet, so only the fixed prefix is localized here. */}
          {t("weather_unavailable_prefix")}: {data.message}
        </div>
      )}

      {data && data.source === "live" && (
        <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 md:p-6">
          <h2 className="text-lg font-semibold text-earth-900 mb-3">{data.location}</h2>

          <div className="flex flex-wrap items-baseline gap-3 mb-4">
            <p className="text-4xl font-semibold text-earth-900">
              {data.temperature != null ? `${Math.round(data.temperature)}°C` : "—"}
            </p>
            <p className="text-earth-600 capitalize break-words">{data.condition}</p>
          </div>

          <div className="grid grid-cols-3 gap-3 text-sm mb-4">
            <div>
              <p className="text-earth-500 text-xs">{t("weather_humidity")}</p>
              <p className="font-medium text-earth-900">{data.humidity}%</p>
            </div>
            <div>
              <p className="text-earth-500 text-xs">{t("weather_rainfall")}</p>
              <p className="font-medium text-earth-900">{data.rainfall} mm</p>
            </div>
            <div>
              <p className="text-earth-500 text-xs">{t("weather_wind")}</p>
              <p className="font-medium text-earth-900">{data.wind_speed} m/s</p>
            </div>
          </div>

          {rainSoon && (
            <div className="bg-info-50 text-info-700 text-sm p-3 rounded-md mb-4 border border-info-500/20">
              ☔ {t("result_weather_rain_caution")}
            </div>
          )}

          {data.forecast.length > 0 && (
            <>
              <h3 className="font-semibold text-sm text-earth-900 mb-2">{t("weather_forecast_title")}</h3>
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 text-xs text-center">
                {data.forecast.map((d) => (
                  <div key={d.date} className="border border-earth-200 rounded-md p-2">
                    <p className="font-medium text-earth-900">{d.date.slice(5)}</p>
                    <p className="text-earth-700">
                      {Math.round(d.temp_min)}–{Math.round(d.temp_max)}°
                    </p>
                    <p className="text-earth-500 truncate">{d.condition}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default Weather;
