import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPrediction, generateReport } from "../api/disease";
import { apiClient } from "../api/client";

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
}

const severityColor: Record<string, string> = {
  Low: "bg-green-100 text-green-700",
  Medium: "bg-yellow-100 text-yellow-700",
  High: "bg-red-100 text-red-700",
};

const Result: React.FC = () => {
  const { id } = useParams();

  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!id) {
      setError("Prediction ID is missing.");
      return;
    }

    setPrediction(null);
    setError(null);

    getPrediction(id)
      .then((res) => {
        setPrediction(res.data);
      })
      .catch((err) => {
        console.error("Failed to load prediction:", err);

        const message =
          err?.response?.data?.detail ||
          "Unable to load this prediction. Please try again.";

        setError(message);
      });
  }, [id]);

  const handleGenerateReport = async () => {
    if (!id) return;

    setGenerating(true);

    try {
      const res = await generateReport(id);

      const download = await apiClient.get(
        `/reports/download/${res.data.id}`,
        {
          responseType: "blob",
        }
      );

      const url = window.URL.createObjectURL(
        new Blob([download.data])
      );

      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `greenmind_report_${id}.pdf`
      );

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to generate report:", err);
      alert("Unable to generate the PDF report. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-5">
          <h2 className="font-semibold mb-2">
            Unable to load prediction
          </h2>

          <p className="text-sm mb-4">
            {error}
          </p>

          <Link
            to="/history"
            className="inline-block border px-4 py-2 rounded font-medium hover:bg-gray-50"
          >
            Back to History
          </Link>
        </div>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="p-8 text-center text-gray-500">
        Loading result...
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">

      {prediction.status === "fallback" && (
        <div className="bg-yellow-50 text-yellow-800 text-sm p-3 rounded mb-4 border border-yellow-200">
          Development/demo mode: no trained model is loaded, so this
          result is a placeholder, not a real AI diagnosis.
        </div>
      )}

      {prediction.status === "low_confidence" && (
        <div className="bg-blue-50 text-blue-800 text-sm p-3 rounded mb-4 border border-blue-200">
          The model couldn't confidently identify a disease from this
          image.

          {prediction.possible_disease && (
            <>
              {" "}
              Closest guess:{" "}
              <strong>{prediction.possible_disease}</strong>.
              This is shown as a hint only, not a diagnosis.
            </>
          )}
        </div>
      )}

      {prediction.crop_mismatch_note && (
        <div className="bg-orange-50 text-orange-800 text-sm p-3 rounded mb-4 border border-orange-200">
          {prediction.crop_mismatch_note}
        </div>
      )}

      <div className="bg-white rounded-lg shadow border p-6 mb-4">
        <div className="flex justify-between items-start mb-4">

          <div>
            <p className="text-sm text-gray-500">
              {prediction.crop}
            </p>

            <h1 className="text-2xl font-bold text-primary-700">
              {prediction.disease}
            </h1>
          </div>

          {prediction.status !== "low_confidence" && (
            <span
              className={`text-xs px-3 py-1 rounded-full font-semibold ${
                severityColor[prediction.severity] ||
                "bg-gray-100 text-gray-700"
              }`}
            >
              {prediction.severity} severity
            </span>
          )}
        </div>

        <p className="text-sm text-gray-600 mb-2">
          Confidence:{" "}
          <strong>
            {(prediction.confidence * 100).toFixed(1)}%
          </strong>
        </p>

        <p className="text-gray-700">
          {prediction.description}
        </p>
      </div>

      {prediction.recommendation && (
        <div className="bg-white rounded-lg shadow border p-6 space-y-4 mb-4">
          {[
            ["Treatment", prediction.recommendation.treatment],
            [
              "Fertilizer Guidance",
              prediction.recommendation.fertilizer,
            ],
            [
              "Pesticide Guidance",
              prediction.recommendation.pesticide_guidance,
            ],
            [
              "Prevention",
              prediction.recommendation.prevention,
            ],
            [
              "Crop Management",
              prediction.recommendation.crop_management,
            ],
            [
              "Monitoring Advice",
              prediction.recommendation.monitoring_advice,
            ],
          ]
            .filter(([, value]) => value)
            .map(([label, value]) => (
              <div key={label as string}>
                <h3 className="font-semibold text-primary-700 text-sm mb-1">
                  {label}
                </h3>

                <p className="text-sm text-gray-700">
                  {value}
                </p>
              </div>
            ))}
        </div>
      )}

      <p className="text-xs text-gray-500 italic mb-4">
        {prediction.disclaimer}
      </p>

      <div className="flex gap-3">
        <button
          onClick={handleGenerateReport}
          disabled={generating}
          className="bg-primary-600 text-white px-4 py-2 rounded font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {generating
            ? "Generating..."
            : "Generate PDF Report"}
        </button>

        <Link
          to="/history"
          className="border px-4 py-2 rounded font-medium hover:bg-gray-50"
        >
          View History
        </Link>
      </div>
    </div>
  );
};

export default Result;