import { ArrowLeft, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { AgentTimeline } from "../components/AgentTimeline";
import { EvidenceList } from "../components/EvidenceList";
import { money, riskText, time } from "../components/format";
import { ReportViewer } from "../components/ReportViewer";
import { ReviewPanel } from "../components/ReviewPanel";
import { RiskProfile } from "../components/RiskProfile";
import type { AgentEvent, EvidenceItem, ReportResponse, TaskDetail } from "../types/diligence";

export function TaskDetailPage({ taskId, onBack }: { taskId: string; onBack: () => void }) {
  const [detail, setDetail] = useState<TaskDetail | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [nextDetail, nextEvents, nextEvidence, nextReport] = await Promise.all([
        api.getTask(taskId), api.getTaskEvents(taskId), api.getTaskEvidence(taskId), api.getTaskReport(taskId)
      ]);
      setDetail(nextDetail);
      setEvents(nextEvents);
      setEvidence(nextEvidence);
      setReport(nextReport);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <main className="page-shell"><div className="loading-card">加载任务详情中...</div></main>;
  if (error || !detail) return <main className="page-shell"><button className="ghost-button" onClick={onBack}><ArrowLeft size={16} />返回</button><div className="error-banner">{error || "任务不存在"}</div></main>;

  const risk = detail.risk_assessment;
  return (
    <main className="page-shell">
      <header className="detail-header">
        <button className="ghost-button" onClick={onBack}><ArrowLeft size={16} />返回任务创建</button>
        <button className="secondary-button" onClick={() => void load()}><RefreshCw size={16} />刷新</button>
      </header>
      <section className="overview-strip">
        <div><span>供应商</span><strong>{detail.supplier.name}</strong></div>
        <div><span>任务状态</span><strong>{detail.task.status}</strong></div>
        <div className={`risk-cell ${risk.risk_level ?? ""}`}><span>风险等级</span><strong>{risk.risk_level ? riskText[risk.risk_level] : "--"}</strong></div>
        <div><span>总分 / 原始分</span><strong>{risk.total_score ?? "--"} / {risk.raw_score ?? "--"}</strong></div>
      </section>
      <section className="panel supplier-summary">
        <h2>任务概览</h2>
        <dl className="compact-meta wide-meta">
          <div><dt>行业</dt><dd>{detail.supplier.industry}</dd></div>
          <div><dt>地区</dt><dd>{detail.supplier.region}</dd></div>
          <div><dt>采购金额</dt><dd>{money(detail.supplier.procurement_amount ?? detail.supplier.annual_spend)}</dd></div>
          <div><dt>合作类型</dt><dd>{detail.supplier.cooperation_type}</dd></div>
          <div><dt>创建时间</dt><dd>{time(detail.task.created_at)}</dd></div>
          <div><dt>更新时间</dt><dd>{time(detail.task.updated_at)}</dd></div>
        </dl>
      </section>
      <RiskProfile risk={risk} />
      <section className="panel"><h2>Agent 执行时间线</h2><AgentTimeline events={events} /></section>
      <section className="panel"><h2>关键证据链</h2><EvidenceList evidence={evidence} /></section>
      <section className="panel"><h2>Markdown 尽调报告</h2><ReportViewer taskId={taskId} markdown={report?.markdown_content} /></section>
      <section className="panel"><h2>人工复核</h2><ReviewPanel taskId={taskId} onSubmitted={load} /></section>
    </main>
  );
}
