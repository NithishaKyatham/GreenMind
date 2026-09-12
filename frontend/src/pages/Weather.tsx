import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getWeather } from "../api/disease";

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
  const [location, setLocation] = useState(user?.location || "");
  const [data, setData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchWeather = async () => {
    if (!location) return;
    setLoading(true);
    try {
      const res = await getWeather(location);
      setData(res.data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-primary-700 mb-4">Weather</h1>
      <div className="flex gap-3 mb-6">
        <input value={location} onChange={(e) => setLocation(e.target.value)}
          placeholder="City or Village, State, Country"
          className="flex-1 border rounded px-3 py-2" />
        <button onClick={fetchWeather} disabled={loading}
          className="bg-primary-600 text-white px-4 py-2 rounded font-medium disabled:opacity-50">
          {loading ? "Loading..." : "Get Weather"}
        </button>
      </div>

      {data && data.source === "unavailable" && (
        <div className="bg-yellow-50 text-yellow-800 p-4 rounded border border-yellow-200">
          Weather data unavailable: {data.message}
        </div>
      )}

      {data && data.source === "live" && (
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-2">{data.location}</h2>
          <div className="grid grid-cols-2 gap-3 text-sm mb-4">
            <p>Temperature: <strong>{data.temperature}°C</strong></p>
            <p>Humidity: <strong>{data.humidity}%</strong></p>
            <p>Rainfall (1h): <strong>{data.rainfall} mm</strong></p>
            <p>Wind: <strong>{data.wind_speed} m/s</strong></p>
          </div>
          <p className="text-gray-600 capitalize mb-4">{data.condition}</p>

          {data.forecast.length > 0 && (
            <>
              <h3 className="font-semibold text-sm mb-2">5-Day Outlook</h3>
              <div className="grid grid-cols-5 gap-2 text-xs text-center">
                {data.forecast.map((d) => (
                  <div key={d.date} className="border rounded p-2">
                    <p className="font-medium">{d.date.slice(5)}</p>
                    <p>{Math.round(d.temp_min)}–{Math.round(d.temp_max)}°</p>
                    <p className="text-gray-500 truncate">{d.condition}</p>
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
