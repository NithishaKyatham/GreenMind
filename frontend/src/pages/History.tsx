import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory, generateReport } from "../api/disease";
import { apiClient } from "../api/client";
import { useLanguage } from "../context/LanguageContext";
import PredictionThumbnail from "../components/PredictionThumbnail";

interface HistoryItem {
  id: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: string;
  created_at: string;
}

type StatusFilter = "all" | "healthy" | "disease" | "low_confidence";

const History: React.FC = () => {
  const { t } = useLanguage();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [crop, setCrop] = useState("");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("latest");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const fetchHistory = () => {
    setLoading(true);
    const params: Record<string, string> = { sort };
    if (crop.trim()) params.crop = crop.trim();
    if (q.trim()) params.q = q.trim();
    getHistory(params)
      .then((res) => setItems(res.data))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort]);

  const isLowConfidence = (item: HistoryItem) =>
    item.disease === "Unable to confidently identify" || item.confidence < 0.6;
  const isHealthy = (item: HistoryItem) => !isLowConfidence(item) && item.disease.toLowerCase() === "healthy";

  const severityWord = (severity: string) => {
    if (severity === "High") return t("severity_high");
    if (severity === "Medium") return t("severity_medium");
    if (severity === "Low") return t("severity_low");
    return severity;
  };

  const filtered = useMemo(() => {
    if (statusFilter === "all") return items;
    return items.filter((item) => {
      if (statusFilter === "healthy") return isHealthy(item);
      if (statusFilter === "low_confidence") return isLowConfidence(item);
      return !isHealthy(item) && !isLowConfidence(item);
    });
  }, [items, statusFilter]);

  const handleGenerateReport = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setGeneratingId(id);
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
    } finally {
      setGeneratingId(null);
    }
  };

  const filterChips: { key: StatusFilter; label: string }[] = [
    { key: "all", label: t("history_filter_all") },
    { key: "healthy", label: t("status_healthy") },
    { key: "disease", label: t("dashboard_disease_detected") },
    { key: "low_confidence", label: t("dashboard_low_confidence") },
  ];

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8">
      <h1 className="text-2xl font-semibold text-earth-900 mb-4">{t("history_title")}</h1>

      <div className="flex gap-2 mb-4 flex-wrap">
        {filterChips.map((chip) => (
          <button
            key={chip.key}
            onClick={() => setStatusFilter(chip.key)}
            className={`text-sm font-medium px-3 py-1.5 rounded-full border transition-colors ${
              statusFilter === chip.key
                ? "bg-primary-600 text-white border-primary-600"
                : "bg-white text-earth-700 border-earth-200 hover:bg-earth-50"
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      <div className="flex gap-3 mb-6 flex-wrap">
        <input
          placeholder={t("history_search_placeholder")}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchHistory()}
          className="border border-earth-200 rounded-md px-3 py-2 text-sm flex-1 min-w-[160px] bg-white"
        />
        <input
          placeholder={t("history_crop_filter_placeholder")}
          value={crop}
          onChange={(e) => setCrop(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchHistory()}
          className="border border-earth-200 rounded-md px-3 py-2 text-sm bg-white"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="border border-earth-200 rounded-md px-3 py-2 text-sm bg-white"
        >
          <option value="latest">{t("history_sort_latest")}</option>
          <option value="oldest">{t("history_sort_oldest")}</option>
        </select>
        <button
          onClick={fetchHistory}
          className="bg-primary-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-primary-700"
        >
          {t("history_apply")}
        </button>
      </div>

      {loading ? (
        <p className="text-earth-500 text-sm">{t("dashboard_loading")}</p>
      ) : filtered.length === 0 ? (
        <p className="text-earth-500 text-sm">{t("history_no_matches")}</p>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item) => {
            const lowConf = isLowConfidence(item);
            return (
              <Link
                key={item.id}
                to={`/history/${item.id}`}
                className="bg-white rounded-lg border border-earth-200 shadow-soft overflow-hidden hover:border-primary-300 transition-colors flex flex-col"
              >
                <PredictionThumbnail predictionId={item.id} alt={item.crop} className="h-32 w-full object-cover" />
                <div className="p-3 flex-1 flex flex-col">
                  <p className="font-medium text-sm text-earth-900 truncate">
                    {item.crop} — {lowConf ? t("dashboard_unable_identify") : item.disease}
                  </p>
                  <p className="text-xs text-earth-500 mb-2">{new Date(item.created_at).toLocaleDateString()}</p>
                  <div className="flex items-center justify-between mt-auto">
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
                      {lowConf ? t("dashboard_low_confidence") : severityWord(item.severity)}
                    </span>
                    <button
                      onClick={(e) => handleGenerateReport(item.id, e)}
                      disabled={generatingId === item.id}
                      className="text-[11px] font-medium text-primary-700 hover:text-primary-800 disabled:opacity-50"
                    >
                      {generatingId === item.id ? t("result_generating") : t("generate_report")}
                    </button>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default History;
