import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPrediction, generateReport, getWeather } from "../api/disease";
import { apiClient } from "../api/client";
import { useLanguage } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";
import { useVoice } from "../hooks/useVoice";
import { LOCALE_NAMES } from "../services/speech/localeMap";
import PredictionThumbnail from "../components/PredictionThumbnail";

interface Recommendation {
  treatment: string;
  fertilizer?: string;
  pesticide_guidance?: string;
  prevention?: string;
  crop_management?: string;
  monitoring_advice?: string;
}

interface Prediction {
  id: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: string;
  status: "confident" | "low_confidence" | "fallback";
  description: string;
  is_fallback_prediction: boolean;
  disclaimer: string;
  recommendation: Recommendation | null;
  possible_disease?: string | null;
  crop_mismatch_note?: string | null;
  context?: {
    season?: string | null;
    region?: string | null;
    crop_stage?: string | null;
    soil_info?: string | null;
    weather?: { source?: string; location?: string | null } | null;
  } | null;
}

const severityColor: Record<string, string> = {
  Low: "bg-primary-50 text-primary-700",
  Medium: "bg-accent-50 text-accent-700",
  High: "bg-danger-50 text-danger-700",
};

const severityWord = (t: (k: string) => string, severity: string) => {
  if (severity === "High") return t("severity_high");
  if (severity === "Medium") return t("severity_medium");
  if (severity === "Low") return t("severity_low");
  return severity;
};

const Result: React.FC = () => {
  const { id } = useParams();
  const { t, locale } = useLanguage();
  const { user } = useAuth();
  const voice = useVoice(locale);
  const availableVoiceLanguages = voice.availableVoiceLanguages || [];

  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [rainSoon, setRainSoon] = useState(false);

  useEffect(() => {
    if (!id) {
      setError(t("result_error_missing_id"));
      return;
    }
    setPrediction(null);
    setError(null);
    getPrediction(id, locale)
      .then((res) => setPrediction(res.data))
      .catch((err) => {
        console.error("Failed to load prediction:", err);
        setError(err?.response?.data?.detail || t("result_error_load_failed"));
      });
  }, [id, locale]);

  // Real, conditional weather tie-in — only shown when the farmer has a
  // saved location AND the actual forecast indicates meaningful rain
  // chance; never a generic/invented claim.
  useEffect(() => {
    if (!user?.location) return;
    getWeather(user.location)
      .then((res) => {
        const forecast = res.data?.forecast || [];
        const soon = forecast
          .slice(0, 2)
          .some((d: any) => (d.rain_probability ?? 0) >= 50);
        setRainSoon(soon);
      })
      .catch(() => setRainSoon(false));
  }, [user?.location]);

  const recommendationSpeechText = useMemo(() => {
    if (!prediction?.recommendation) return "";

    const fields: [string, string | undefined][] = [
      [t("result_treatment"), prediction.recommendation.treatment],
      [t("result_fertilizer"), prediction.recommendation.fertilizer],
      [t("result_pesticide"), prediction.recommendation.pesticide_guidance],
      [t("result_prevention"), prediction.recommendation.prevention],
      [t("result_crop_management"), prediction.recommendation.crop_management],
      [t("result_monitoring"), prediction.recommendation.monitoring_advice],
    ];

    return fields
      .filter(([, value]) => value)
      .map(([label, value]) => `${label}: ${value}`)
      .join(". ");
  }, [prediction, t, locale]);

  const handleGenerateReport = async () => {
    if (!id) return;
    setGenerating(true);
    try {
      const res = await generateReport(id);
      const download = await apiClient.get(`/reports/download/${res.data.id}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([download.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `greenmind_report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to generate report:", err);
      setError(t("result_generate_pdf_error"));
    } finally {
      setGenerating(false);
    }
  };

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-danger-50 text-danger-700 border border-danger-500/20 rounded-lg p-5">
          <h2 className="font-semibold mb-2">{t("result_unable_load_title")}</h2>
          <p className="text-sm mb-4">{error}</p>
          <Link to="/history" className="inline-block border border-earth-200 px-4 py-2 rounded-md font-medium hover:bg-earth-50">
            {t("result_back_to_history")}
          </Link>
        </div>
      </div>
    );
  }

  if (!prediction) {
    return <div className="p-8 text-center text-earth-500">{t("result_loading")}</div>;
  }

  const organicFields = [
    [t("result_treatment"), prediction.recommendation?.treatment],
    [t("result_fertilizer"), prediction.recommendation?.fertilizer],
    [t("result_crop_management"), prediction.recommendation?.crop_management],
    [t("result_monitoring"), prediction.recommendation?.monitoring_advice],
  ].filter(([, v]) => v) as [string, string][];

  const conventionalFields = [[t("result_pesticide"), prediction.recommendation?.pesticide_guidance]].filter(
    ([, v]) => v
  ) as [string, string][];

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6">
      {prediction.status === "fallback" && (
        <div className="bg-accent-50 text-accent-700 text-sm p-3 rounded-md mb-4 border border-accent-100">
          {t("result_fallback_notice")}
        </div>
      )}

      {prediction.status === "low_confidence" && (
        <div className="bg-info-50 text-info-700 text-sm p-3 rounded-md mb-4 border border-info-500/20">
          {t("result_low_confidence_notice")}
          {prediction.possible_disease && (
            <>
              {" "}
              {t("result_low_confidence_hint_prefix")} <strong>{prediction.possible_disease}</strong>.{" "}
              {t("result_low_confidence_hint_suffix")}
            </>
          )}
        </div>
      )}

      {prediction.crop_mismatch_note && (
        <div className="bg-accent-50 text-accent-700 text-sm p-3 rounded-md mb-4 border border-accent-100">
          <div className="flex flex-wrap gap-x-6 gap-y-1 mb-2 text-xs font-medium">
            <span>
              {t("result_you_selected")}: <span className="font-semibold">{prediction.crop}</span>
            </span>
            <span>
              {t("result_greenmind_detected")}:{" "}
              <span className="font-semibold">{prediction.possible_disease?.split(" - ")[0]}</span>
            </span>
          </div>
          {prediction.crop_mismatch_note}
        </div>
      )}

      <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 mb-4">
        <div className="flex gap-4 items-start">
          <PredictionThumbnail
            predictionId={prediction.id}
            alt={prediction.crop}
            className="h-20 w-20 rounded-md object-cover shrink-0 border border-earth-100"
          />
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start gap-2">
              <div>
                <p className="text-xs text-earth-500">{t("result_detected_crop")}</p>
                <p className="font-semibold text-earth-900">{prediction.crop}</p>
              </div>
              {prediction.status !== "low_confidence" && (
                <span className={`text-xs px-3 py-1 rounded-full font-semibold shrink-0 ${severityColor[prediction.severity] || "bg-earth-100 text-earth-700"}`}>
                  {severityWord(t, prediction.severity)}
                </span>
              )}
            </div>
            <h1 className="text-xl font-semibold text-earth-900 mt-2 mb-1">{prediction.disease}</h1>
            {prediction.status !== "low_confidence" && (
              <p className="text-sm text-earth-600">
                {t("result_confidence")}: <strong>{(prediction.confidence * 100).toFixed(0)}%</strong>
              </p>
            )}
          </div>
        </div>

      </div>

      {rainSoon && (
        <div className="bg-info-50 text-info-700 text-sm p-3 rounded-md mb-4 border border-info-500/20">
          ☔ {t("result_weather_rain_caution")}
        </div>
      )}

      {prediction.context && (
        <details className="bg-white rounded-lg border border-earth-200 shadow-soft p-4 mb-3">
          <summary className="font-semibold text-earth-900 cursor-pointer">{t("result_context_used")}</summary>
          <div className="mt-3 space-y-1 text-sm text-earth-700">
            {prediction.context.season && <p><strong>{t("result_context_season")}:</strong> {prediction.context.season} ({t("result_context_farmer_provided")})</p>}
            {prediction.context.region && <p><strong>{t("result_context_region")}:</strong> {prediction.context.region} ({t("result_context_farmer_provided")})</p>}
            {prediction.context.crop_stage && <p><strong>{t("result_context_crop_stage")}:</strong> {prediction.context.crop_stage} ({t("result_context_farmer_provided")})</p>}
            {prediction.context.soil_info && <p><strong>{t("result_context_soil")}:</strong> {prediction.context.soil_info} ({t("result_context_farmer_provided")})</p>}
            {prediction.context.weather?.source === "live" && (
              <p><strong>{t("result_context_weather")}:</strong> {prediction.context.weather.location || prediction.context.region || t("result_context_location_unknown")} ({t("result_context_live")})</p>
            )}
          </div>
        </details>
      )}

      {prediction.recommendation && recommendationSpeechText && (
        <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 mb-3">
          {voice.ttsSupported ? (
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => voice.speak(recommendationSpeechText)}
                disabled={voice.voiceLoading || voice.voiceAvailable === false}
                className="text-sm font-medium flex items-center gap-2 border border-earth-200 rounded-md px-3 py-2 hover:bg-earth-50"
              >
                🔊 {t("voice_listen_recommendation")}
              </button>
              {voice.speaking && (
                <button
                  onClick={voice.stopSpeaking}
                  className="text-sm font-medium flex items-center gap-2 border border-earth-200 rounded-md px-3 py-2 hover:bg-earth-50"
                >
                  ⏹ {t("voice_stop")}
                </button>
              )}
              {voice.speaking && <span className="text-xs text-primary-600">{t("voice_speaking")}</span>}
              {voice.error && <span className="text-xs text-danger-600">{voice.error}</span>}
              {!voice.error && voice.voiceAvailable === false && (
                <span className="text-xs text-danger-600">
                  A voice for {LOCALE_NAMES[locale] || locale} is not available on this device.
                </span>
              )}
            </div>
          ) : (
            <p className="text-sm text-earth-500">{t("voice_unavailable")}</p>
          )}
          <div className="mt-4 pt-3 border-t border-earth-100">
            <p className="text-xs font-medium text-earth-700">🔊 Voice languages available on this device</p>
            <p className="text-xs text-earth-500 mt-1">
              These are device voices, separate from GreenMind translation languages.
            </p>
            {voice.voiceLoading ? (
              <p className="text-xs text-earth-500 mt-2">Checking available voices...</p>
            ) : availableVoiceLanguages.length === 0 ? (
              <p className="text-xs text-earth-500 mt-2">No speech voices are available on this device.</p>
            ) : (
              <ul className="flex flex-wrap gap-x-3 gap-y-1 mt-2" aria-label="Available voice languages">
                {availableVoiceLanguages.map((language) => (
                  <li key={language.code} className="text-xs text-earth-700">
                    {language.flag && `${language.flag} `}{language.name}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      <details open className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 mb-3">
        <summary className="font-semibold text-earth-900 cursor-pointer">{t("result_what_it_means")}</summary>
        <p className="text-sm text-earth-700 mt-3 leading-relaxed">{prediction.description}</p>
      </details>

      {organicFields.length > 0 && (
        <details className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 mb-3">
          <summary className="font-semibold text-earth-900 cursor-pointer flex items-center gap-2">
            <span aria-hidden="true">🌱</span> {t("result_organic_options")}
          </summary>
          <div className="mt-3 space-y-3">
            {organicFields.map(([label, value]) => (
              <div key={label}>
                <h3 className="font-medium text-primary-700 text-sm mb-1">{label}</h3>
                <p className="text-sm text-earth-700">{value}</p>
              </div>
            ))}
          </div>
        </details>
      )}

      {conventionalFields.length > 0 && (
        <details className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 mb-3">
          <summary className="font-semibold text-earth-900 cursor-pointer flex items-center gap-2">
            <span aria-hidden="true">🧪</span> {t("result_conventional_options")}
          </summary>
          <div className="mt-3 space-y-3">
            {conventionalFields.map(([label, value]) => (
              <div key={label}>
                <h3 className="font-medium text-primary-700 text-sm mb-1">{label}</h3>
                <p className="text-sm text-earth-700">{value}</p>
              </div>
            ))}
          </div>
        </details>
      )}

      {prediction.recommendation?.prevention && (
        <details className="bg-white rounded-lg border border-earth-200 shadow-soft p-5 mb-4">
          <summary className="font-semibold text-earth-900 cursor-pointer flex items-center gap-2">
            <span aria-hidden="true">🛡️</span> {t("result_prevention")}
          </summary>
          <p className="text-sm text-earth-700 mt-3">{prediction.recommendation.prevention}</p>
        </details>
      )}

      <p className="text-xs text-earth-500 italic mb-4">{prediction.disclaimer}</p>

      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleGenerateReport}
          disabled={generating}
          className="bg-primary-600 text-white px-4 py-2 rounded-md font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {generating ? t("result_generating") : t("generate_report")}
        </button>
        <Link to="/history" className="border border-earth-200 px-4 py-2 rounded-md font-medium hover:bg-earth-50">
          {t("result_view_history")}
        </Link>
        <Link to="/chat" className="border border-earth-200 px-4 py-2 rounded-md font-medium hover:bg-earth-50">
          {t("result_ask_greenmind")}
        </Link>
      </div>
    </div>
  );
};

export default Result;
