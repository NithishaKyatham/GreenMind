import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCrops, predictDisease } from "../api/disease";
import { useLanguage } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";

interface Crop {
  id: string;
  name: string;
  display_name_en: string;
}

type Step = "capture" | "preview" | "analyzing";

const Detect: React.FC = () => {
  const navigate = useNavigate();
  const { t, locale } = useLanguage();
  const { user } = useAuth();
  const [crops, setCrops] = useState<Crop[]>([]);
  const [selectedCrop, setSelectedCrop] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<Step>("capture");
  const [stageIndex, setStageIndex] = useState(0);
  const [season, setSeason] = useState("");
  const [region, setRegion] = useState("");
  const [cropStage, setCropStage] = useState("");
  const [soilInfo, setSoilInfo] = useState("");

  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getCrops().then((res) => {
      setCrops(res.data);
      if (res.data.length > 0) setSelectedCrop(res.data[0].name);
    });
  }, []);

  useEffect(() => {
    if (user?.location && !region) setRegion(user.location);
  }, [user?.location, region]);

  const stages = [
    t("detect_stage_1"),
    t("detect_stage_2"),
    t("detect_stage_3"),
    t("detect_stage_4"),
  ];

  // Cycles through qualitative stage labels while the real request is in
  // flight — never a fabricated percentage, just an honest "something is
  // happening" indicator.
  useEffect(() => {
    if (step !== "analyzing") return;
    setStageIndex(0);
    const interval = setInterval(() => {
      setStageIndex((i) => (i + 1 < stages.length ? i + 1 : i));
    }, 1100);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const handleFile = (f: File) => {
    if (!["image/jpeg", "image/jpg", "image/png"].includes(f.type)) {
      setError(t("detect_error_filetype"));
      return;
    }
    if (f.size > 8 * 1024 * 1024) {
      setError(t("detect_error_filesize"));
      return;
    }
    setError(null);
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStep("preview");
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setStep("capture");
  };

  const handleSubmit = async () => {
    if (!file || !selectedCrop) {
      setError(t("detect_error_missing"));
      return;
    }
    setError(null);
    setStep("analyzing");
    try {
      const res = await predictDisease(selectedCrop, file, locale, {
        season,
        region,
        crop_stage: cropStage,
        soil_info: soilInfo,
      });
      navigate(`/result/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || t("detect_error_failed"));
      setStep("preview");
    }
  };

  return (
    <div className="max-w-xl mx-auto p-4 md:p-8">
      <h1 className="text-2xl font-semibold text-earth-900 mb-6">{t("upload_title")}</h1>

      {step === "analyzing" ? (
        <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-8 text-center">
          {preview && (
            <img src={preview} alt="" className="mx-auto max-h-40 rounded-md mb-6 opacity-90" />
          )}
          <div className="mx-auto mb-5 h-10 w-10 rounded-full border-2 border-primary-200 border-t-primary-600 animate-spin" />
          <p className="font-semibold text-earth-900 mb-1">{t("detect_analyzing_title")}</p>
          <p className="text-sm text-earth-500 transition-opacity">{stages[stageIndex]}</p>
        </div>
      ) : step === "preview" ? (
        <div>
          <div className="bg-white rounded-lg border border-earth-200 shadow-soft p-4 mb-4">
            <img src={preview!} alt="preview" className="mx-auto max-h-72 rounded-md" />
            <div className="flex flex-wrap justify-center gap-3 mt-4">
              <button
                onClick={reset}
                className="text-sm font-medium text-earth-700 border border-earth-200 rounded-md px-4 py-2 hover:bg-earth-50"
              >
                {t("detect_retake")}
              </button>
              <button
                onClick={reset}
                className="text-sm font-medium text-danger-500 border border-earth-200 rounded-md px-4 py-2 hover:bg-danger-50"
              >
                {t("detect_remove")}
              </button>
            </div>
          </div>

          <label className="block text-sm font-medium text-earth-700 mb-1">{t("upload_select_crop")}</label>
          <select
            value={selectedCrop}
            onChange={(e) => setSelectedCrop(e.target.value)}
            className="w-full border border-earth-200 rounded-md px-3 py-2 mb-4 bg-white"
          >
            {crops.map((c) => (
              <option key={c.id} value={c.name}>
                {c.display_name_en}
              </option>
            ))}
          </select>

          <details className="mb-5 border border-earth-200 rounded-md p-3 bg-earth-50">
            <summary className="text-sm font-medium text-earth-800 cursor-pointer">{t("detect_context_title")}</summary>
            <p className="text-xs text-earth-500 mt-2 mb-3">{t("detect_context_help")}</p>
            <div className="grid gap-3">
              <label className="text-sm text-earth-700">
                {t("detect_season")}
                <input value={season} onChange={(e) => setSeason(e.target.value)} placeholder={t("detect_season_placeholder")} className="w-full border border-earth-200 rounded-md px-3 py-2 mt-1 bg-white" />
              </label>
              <label className="text-sm text-earth-700">
                {t("detect_region")}
                <input value={region} onChange={(e) => setRegion(e.target.value)} placeholder={t("detect_region_placeholder")} className="w-full border border-earth-200 rounded-md px-3 py-2 mt-1 bg-white" />
              </label>
              <label className="text-sm text-earth-700">
                {t("detect_crop_stage")}
                <input value={cropStage} onChange={(e) => setCropStage(e.target.value)} placeholder={t("detect_crop_stage_placeholder")} className="w-full border border-earth-200 rounded-md px-3 py-2 mt-1 bg-white" />
              </label>
              <label className="text-sm text-earth-700">
                {t("detect_soil_info")}
                <input value={soilInfo} onChange={(e) => setSoilInfo(e.target.value)} placeholder={t("detect_soil_info_placeholder")} className="w-full border border-earth-200 rounded-md px-3 py-2 mt-1 bg-white" />
              </label>
            </div>
          </details>

          <ul className="text-sm text-earth-600 space-y-1.5 mb-5">
            <li className="flex items-start gap-2">
              <span className="text-primary-600" aria-hidden="true">✓</span> {t("detect_tip_single_leaf")}
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600" aria-hidden="true">✓</span> {t("detect_tip_lighting")}
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600" aria-hidden="true">✓</span> {t("detect_tip_blur")}
            </li>
          </ul>

          {error && <div className="bg-danger-50 text-danger-700 text-sm p-3 rounded-md mb-4">{error}</div>}

          <button
            onClick={handleSubmit}
            disabled={!file}
            className="w-full bg-primary-600 text-white py-3 rounded-md font-semibold hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {t("upload_button")}
          </button>
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <button
              onClick={() => cameraInputRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 bg-primary-600 text-white rounded-lg py-8 font-semibold hover:bg-primary-700 transition-colors"
            >
              <span className="text-2xl" aria-hidden="true">📷</span>
              {t("detect_step_take_photo")}
            </button>
            <button
              onClick={() => galleryInputRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 bg-white border border-earth-200 text-earth-800 rounded-lg py-8 font-semibold hover:bg-earth-50 transition-colors"
            >
              <span className="text-2xl" aria-hidden="true">🖼️</span>
              {t("detect_step_upload_gallery")}
            </button>
          </div>

          {/* Desktop drag-and-drop */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
            }}
            className={`hidden md:flex items-center justify-center border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver ? "border-primary-500 bg-primary-50" : "border-earth-200"
            }`}
          >
            <p className="text-earth-500 text-sm">{t("upload_drag_drop")}</p>
          </div>

          <input
            ref={cameraInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png"
            capture="environment"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <input
            ref={galleryInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />

          {error && <div className="bg-danger-50 text-danger-700 text-sm p-3 rounded-md mt-4">{error}</div>}
        </div>
      )}
    </div>
  );
};

export default Detect;
