import { ArrowLeft, Copy, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { AgentTimeline } from "../components/AgentTimeline";
import { EvidenceList } from "../components/EvidenceList";
import { money, riskText, time } from "../components/format";
import { ReportViewer } from "../components/ReportViewer";
import { ReviewPanel } from "../components/ReviewPanel";
import { RiskProfile } from "../components/RiskProfile";
import { TaskProgressPanel } from "../components/TaskProgressPanel";
import type { AgentEvent, EvidenceItem, ReportResponse, TaskDetail, WebSearchResultPreview } from "../types/diligence";

const ACTIVE_STATUSES = new Set(["pending", "running"]);

const profileLabels: Record<string, string> = {
  company_full_name: "企业名称",
  website: "官网",
  industry: "行业",
  region: "地区",
  unified_social_credit_code: "统一社会信用代码",
  registered_capital: "注册资本",
  established_date: "成立时间",
  legal_representative: "法定代表人",
  registered_address: "注册地址",
  business_scope: "经营范围",
  business_status: "经营状态",
};

function CompanyProfileCard({ profile }: { profile?: TaskDetail["company_profile"] }) {
  if (!profile?.length) return <section className="panel"><h2>企业基础信息补全</h2><div className="empty-state">该任务没有企业画像快照。</div></section>;
  return (
    <section className="panel company-profile-panel">
      <h2>企业基础信息补全</h2>
      <div className="profile-grid">
        {profile.map((item) => (
          <div className="profile-field" key={`${item.field_name}-${item.source_url ?? item.field_value}`}>
            <span>{profileLabels[item.field_name] ?? item.field_name}</span>
            <strong>{item.field_value || "未抽取"}</strong>
            <small>置信度 {typeof item.confidence === "number" ? item.confidence.toFixed(2) : "未记录"}</small>
            {item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer">查看来源</a> : <small>{item.reason || "来源 URL 未提供"}</small>}
          </div>
        ))}
      </div>
      <p className="profile-note">企业画像来自联网搜索标题、摘要和 URL 的结构化推断，不等同官方工商核验，需人工复核。</p>
    </section>
  );
}

function ReconciliationCards({ detail }: { detail: TaskDetail }) {
  const diagnostics = detail.diagnostics;
  const items = [
    ["搜索 query 数", detail.search_query_count ?? diagnostics?.search_query_count ?? 0],
    ["web_search_results", detail.web_search_result_count ?? diagnostics?.web_search_result_count ?? 0],
    ["真实 URL 数", detail.real_url_count ?? diagnostics?.real_url_count ?? 0],
    ["画像字段数", detail.profile_snapshot_count ?? diagnostics?.profile_snapshot_count ?? 0],
    ["画像非空字段", detail.profile_non_empty_count ?? diagnostics?.profile_non_empty_count ?? 0],
    ["可评分证据", detail.scoring_evidence_count ?? diagnostics?.scoring_evidence_count ?? 0],
    ["报告状态", (detail.report_available ?? diagnostics?.report_available) ? "可导出" : "暂无报告"],
  ];
  return (
    <section className="panel">
      <div className="section-title"><h2>数据对账</h2><p>以下统计均来自当前 route task_id。</p></div>
      <div className="diagnostic-grid">
        {items.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </div>
    </section>
  );
}

function WebSearchPreview({ rows }: { rows?: WebSearchResultPreview[] }) {
  if (!rows?.length) return <section className="panel"><h2>联网搜索结果预览</h2><div className="empty-state">该任务无联网搜索结果。</div></section>;
  return (
    <section className="panel">
      <div className="section-title"><h2>联网搜索结果预览</h2><p>展示当前任务前 5 条搜索结果。</p></div>
      <div className="web-preview-list">
        {rows.slice(0, 5).map((row, index) => (
          <article key={`${row.url ?? row.title}-${index}`}>
            <div className="web-preview-head"><strong>{row.title || "未命名搜索结果"}</strong><span>rank {row.rank ?? "--"}</span></div>
            <a href={row.url || undefined} target="_blank" rel="noreferrer">{row.url || "URL 未提供"}</a>
            <p>{row.snippet || "无摘要"}</p>
            <dl className="compact-meta">
              <div><dt>query</dt><dd>{row.query || "未记录"}</dd></div>
              <div><dt>是否参与评分</dt><dd>{row.decision === "score_evidence" ? "是" : "否"}</dd></div>
              <div><dt>不参与评分原因</dt><dd>{row.decision_reason || "未记录"}</dd></div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

export function TaskDetailPage({ taskId, onBack }: { taskId: string; onBack: () => void }) {
  const [detail, setDetail] = useState<TaskDetail | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    setRefreshing(true);
    setError("");
    try {
      const [nextDetail, nextEvents] = await Promise.all([
        api.getDiligenceTask(taskId),
        api.getDiligenceTaskEvents(taskId),
      ]);
      setDetail(nextDetail);
      setEvents(nextEvents);
      if (nextDetail.task.status === "completed" || nextDetail.task.status === "reviewed") {
        const [nextEvidence, nextReport] = await Promise.all([
          api.getTaskEvidence(taskId),
          api.getDiligenceTaskReport(taskId),
        ]);
        setEvidence(nextEvidence);
        setReport(nextReport);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [taskId]);

  useEffect(() => { void load(true); }, [load]);

  useEffect(() => {
    if (!detail || !ACTIVE_STATUSES.has(detail.task.status)) return;
    const timer = window.setInterval(() => { void load(false); }, 2000);
    return () => window.clearInterval(timer);
  }, [detail?.task.status, load]);

  async function copyTaskId() {
    await navigator.clipboard.writeText(taskId);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  if (loading) return <main className="page-shell"><div className="loading-card">加载任务详情中...</div></main>;
  if (error || !detail) return <main className="page-shell"><button className="ghost-button" onClick={onBack}><ArrowLeft size={16} />返回任务列表</button><div className="error-banner">{error || "任务不存在"}</div></main>;

  const risk = detail.risk_assessment;
  const isCompleted = detail.task.status === "completed" || detail.task.status === "reviewed";
  return (
    <main className="page-shell">
      <header className="detail-header task-id-header">
        <button className="ghost-button" onClick={onBack}><ArrowLeft size={16} />返回任务列表</button>
        <div className="task-id-chip"><span>当前路由 Task ID</span><code>{taskId}</code><button className="secondary-button" onClick={copyTaskId}><Copy size={16} />{copied ? "已复制" : "复制"}</button></div>
        <button className="secondary-button" onClick={() => void load(false)} disabled={refreshing}><RefreshCw size={16} />{refreshing ? "刷新中" : "刷新"}</button>
      </header>
      <TaskProgressPanel detail={detail} events={events} />
      <section className="overview-strip">
        <div><span>供应商</span><strong>{detail.supplier.name}</strong></div>
        <div><span>任务状态</span><strong>{detail.task.status}</strong></div>
        <div className={`risk-cell ${risk.risk_level ?? ""}`}><span>风险等级</span><strong>{risk.risk_level ? riskText[risk.risk_level] : "--"}</strong></div>
        <div><span>总分 / 原始分</span><strong>{risk.total_score ?? "--"} / {risk.raw_score ?? "--"}</strong></div>
      </section>
      <section className="panel supplier-summary">
        <h2>任务概览</h2>
        <dl className="compact-meta wide-meta">
          <div><dt>行业</dt><dd>{detail.supplier.industry || "未提供"}</dd></div>
          <div><dt>地区</dt><dd>{detail.supplier.region || "未提供"}</dd></div>
          <div><dt>采购金额</dt><dd>{money(detail.supplier.procurement_amount ?? detail.supplier.annual_spend)}</dd></div>
          <div><dt>合作类型</dt><dd>{detail.supplier.cooperation_type || "未提供"}</dd></div>
          <div><dt>创建时间</dt><dd>{time(detail.task.created_at)}</dd></div>
          <div><dt>更新时间</dt><dd>{time(detail.task.updated_at)}</dd></div>
        </dl>
      </section>
      <ReconciliationCards detail={detail} />
      {isCompleted ? <WebSearchPreview rows={detail.web_search_results ?? detail.diagnostics?.web_search_results_preview} /> : null}
      {isCompleted ? <CompanyProfileCard profile={detail.company_profile ?? detail.diagnostics?.company_profile_preview} /> : null}
      {isCompleted ? <RiskProfile risk={risk} /> : <section className="panel"><h2>风险画像</h2><div className="empty-state">任务执行中，完成后展示风险画像。</div></section>}
      <section className="panel"><h2>Agent 执行时间线</h2><AgentTimeline events={events} /></section>
      <section className="panel"><h2>关键证据链</h2><EvidenceList evidence={evidence} /></section>
      <section className="panel"><h2>Markdown 尽调报告</h2><ReportViewer taskId={taskId} markdown={report?.markdown_content} /></section>
      {isCompleted ? <section className="panel"><h2>人工复核</h2><ReviewPanel taskId={taskId} onSubmitted={() => load(false)} /></section> : null}
    </main>
  );
}
