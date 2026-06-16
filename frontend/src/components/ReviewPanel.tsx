import { useState } from "react";
import { api } from "../api/client";
import type { ReviewPayload } from "../types/diligence";
import { decisionText } from "./format";

export function ReviewPanel({ taskId, onSubmitted }: { taskId: string; onSubmitted: () => void }) {
  const [payload, setPayload] = useState<ReviewPayload>({ reviewer: "demo_reviewer", decision: "approve_with_conditions", comment: "要求供应商补充合规证明和近三年交付记录后再准入。" });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function submit() {
    setLoading(true);
    setError("");
    try {
      await api.submitReview(taskId, payload);
      setMessage("人工复核已提交");
      onSubmitted();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="review-panel">
      <div className="form-grid compact">
        <label>复核人<input value={payload.reviewer} onChange={(e) => setPayload({ ...payload, reviewer: e.target.value })} /></label>
        <label>复核结论<select value={payload.decision} onChange={(e) => setPayload({ ...payload, decision: e.target.value as ReviewPayload["decision"] })}>{Object.entries(decisionText).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
      </div>
      <label>复核意见<textarea value={payload.comment ?? ""} onChange={(e) => setPayload({ ...payload, comment: e.target.value })} /></label>
      <button className="primary-button" onClick={submit} disabled={loading}>{loading ? "提交中..." : "提交人工复核"}</button>
      {message ? <p className="success-text">{message}</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
    </div>
  );
}
