import React, { useEffect, useState } from "react";
import { getPredictionImageBlob } from "../api/disease";

interface Props {
  predictionId: string;
  alt: string;
  className?: string;
}

/**
 * The image endpoint (GET /disease/{id}/image) requires a Bearer token,
 * so it can't be used directly as an <img src="..."> — that would either
 * fail with 401 or (if we put the token in the URL instead) leak the
 * token into browser history/server logs, which the project's own
 * security rules rule out. Instead we fetch the image as a blob through
 * the authenticated API client and hand the browser a local object URL.
 */
const PredictionThumbnail: React.FC<Props> = ({ predictionId, alt, className }) => {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    getPredictionImageBlob(predictionId)
      .then((res) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(res.data);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [predictionId]);

  if (failed) {
    return (
      <div className={`flex items-center justify-center bg-earth-100 text-earth-400 ${className || ""}`}>
        <span aria-hidden="true">🌿</span>
      </div>
    );
  }

  if (!src) {
    return <div className={`animate-pulse bg-earth-100 ${className || ""}`} />;
  }

  return <img src={src} alt={alt} className={className} />;
};

export default PredictionThumbnail;
