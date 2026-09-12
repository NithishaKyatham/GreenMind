import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCrops, predictDisease } from "../api/disease";

interface Crop {
  id: string;
  name: string;
  display_name_en: string;
}

const Detect: React.FC = () => {
  const navigate = useNavigate();
  const [crops, setCrops] = useState<Crop[]>([]);
  const [selectedCrop, setSelectedCrop] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCrops().then((res) => {
      setCrops(res.data);
      if (res.data.length > 0) setSelectedCrop(res.data[0].name);
    });
  }, []);

  const handleFile = (f: File) => {
    if (!["image/jpeg", "image/jpg", "image/png"].includes(f.type)) {
      setError("Only JPG and PNG images are supported.");
      return;
    }
    if (f.size > 8 * 1024 * 1024) {
      setError("Image exceeds the 8MB size limit.");
      return;
    }
    setError(null);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleSubmit = async () => {
    if (!file || !selectedCrop) {
      setError("Please select a crop and an image.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await predictDisease(selectedCrop, file);
      navigate(`/result/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Prediction failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-primary-700 mb-6">Upload Leaf Image</h1>

      <label className="block text-sm font-medium mb-1">Select Crop</label>
      <select value={selectedCrop} onChange={(e) => setSelectedCrop(e.target.value)}
        className="w-full border rounded px-3 py-2 mb-4">
        {crops.map((c) => (
          <option key={c.id} value={c.name}>{c.display_name_en}</option>
        ))}
      </select>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        }}
        onClick={() => document.getElementById("file-input")?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          dragOver ? "border-primary-600 bg-primary-50" : "border-gray-300"
        }`}
      >
        {preview ? (
          <img src={preview} alt="preview" className="mx-auto max-h-64 rounded" />
        ) : (
          <p className="text-gray-500">Drag & drop an image here, or click to browse</p>
        )}
        <input
          id="file-input" type="file" accept="image/jpeg,image/jpg,image/png" className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded mt-4">{error}</div>}

      <button
        onClick={handleSubmit}
        disabled={loading || !file}
        className="w-full bg-primary-600 text-white py-3 rounded font-medium mt-6 hover:bg-primary-700 disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Analyze Image"}
      </button>
    </div>
  );
};

export default Detect;
