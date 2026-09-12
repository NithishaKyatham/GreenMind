import React from "react";
import { useParams } from "react-router-dom";
import Result from "./Result";

// The individual history record view is identical to the prediction Result
// page (both show the same PredictionOut payload) — reused directly rather
// than duplicating markup.
const HistoryDetail: React.FC = () => {
  const { id } = useParams();
  return <Result key={id} />;
};

export default HistoryDetail;
