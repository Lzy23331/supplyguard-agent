import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clipboard, Download, FileText, Play, ShieldAlert, Sparkles } from "lucide-react";
import { marked } from "marked";
import { AgentEvent, api, DiligenceTask, SupplierInput } from "./api/client";

const emptySupplier: SupplierInput = {
  name: "",
  website: "",
  industry: "精密零部件",
  region: "江苏苏州",
  annual_spend: 500000,
  cooperation_type: "标准采购"
};

const riskLabels: Record<string, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险"
};

const statusLabels: Record<string, string> = {
  idle: "未开始",
  created: "已创建",
  pending: "待执行",
  running: "执行中",
  completed: "已完成",
  failed: "失败",
  reviewed: "已复核"
};

const dimensionLabels: Record<string, string> = {
  compliance: "合规风险",
  business: "经营风险",
  delivery: "交付风险",
  completeness: "资料完整性",
  reputation: "舆情风险"
};

const severityLabels: Record<string, string> = {
  info: "信息",
  warning: "预警",
  critical: "严重"
};

const agentLabels: Record<string, string> = {
  IntakeAgent: "准入受理 Agent",
  EvidenceCollectorAgent: "证据收集 Agent",
  ComplianceRiskAgent: "合规风险 Agent",
  BusinessRiskAgent: "经营交付 Agent",
  ReportAgent: "报告生成 Agent",
  Orchestrator: "编排器"
};

const toolLabels: Record<string, string> = {
  MockSearchTool: "模拟搜索工具",
  EvidenceStoreTool: "证据存储工具",
  RAGPolicyTool: "政策检索工具",
  RiskRuleTool: "风险规则工具",
  ReportExportTool: "报告生成工具"
};

function formatAmount(value?: number) {
  if (typeof value !== "number") return "--";
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 0 }).format(value);
}

function formatToolCall(call: Record<string, unknown>) {
  const tool = typeof call.tool === "string" ? toolLabels[call.tool] ?? call.tool : "工具调用";
  const details = Object.entries(call)
    .filter(([key]) => key !== "tool")
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join("，");
  return details ? `${tool}（${details}）` : tool;
}

function App() {
  const [samples, setSamples] = useState<SupplierInput[]>([]);
  const [supplier, setSupplier] = useState<SupplierInput>(emptySupplier);
  const [task, setTask] = useState<DiligenceTask | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [report, setReport] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.samples().then(setSamples).catch((err) => setError(String(err)));
  }, []);

  async function createTask(nextSupplier = supplier) {
    setLoading(true);
    setError("");
    try {
      const created = await api.createTask(nextSupplier);
      setTask(created);
      const [nextEvents, nextReport] = await Promise.all([api.getEvents(created.id), api.getReport(created.id)]);
      setEvents(nextEvents);
      setReport(nextReport.markdown);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const reportHtml = useMemo(() => ({ __html: marked.parse(report) as string }), [report]);
  const riskClass = (task?.risk_level ?? "none").toLowerCase();

  function updateField<K extends keyof SupplierInput>(key: K, value: SupplierInput[K]) {
    setSupplier((current) => ({ ...current, [key]: value }));
  }

  function downloadReport() {
    const blob = new Blob([report], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${task?.supplier.name ?? "供应商"}-尽调报告.md`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="workspace">
      <section className="sidebar">
        <div className="brand">
          <ShieldAlert size={30} />
          <div>
            <h1>SupplyGuard Agent</h1>
            <p>供应商准入尽调与风险研判系统</p>
          </div>
        </div>

        <div className="sample-row">
          {samples.map((item) => (
            <button
              key={item.sample_key}
              className="sample-button"
              onClick={() => {
                setSupplier(item);
                void createTask(item);
              }}
            >
              <Sparkles size={16} />
              {riskLabels[item.sample_key ?? ""] ?? item.sample_key ?? "样例"}
            </button>
          ))}
        </div>

        <form
          className="form"
          onSubmit={(event) => {
            event.preventDefault();
            void createTask();
          }}
        >
          <label>
            供应商名称
            <input value={supplier.name} onChange={(event) => updateField("name", event.target.value)} required />
          </label>
          <label>
            官网
            <input value={supplier.website ?? ""} onChange={(event) => updateField("website", event.target.value)} />
          </label>
          <label>
            所属行业
            <input value={supplier.industry} onChange={(event) => updateField("industry", event.target.value)} required />
          </label>
          <label>
            所在地区
            <input value={supplier.region} onChange={(event) => updateField("region", event.target.value)} required />
          </label>
          <label>
            年采购金额
            <input
              type="number"
              min="0"
              value={supplier.annual_spend}
              onChange={(event) => updateField("annual_spend", Number(event.target.value))}
              required
            />
          </label>
          <label>
            合作类型
            <input
              value={supplier.cooperation_type}
              onChange={(event) => updateField("cooperation_type", event.target.value)}
              required
            />
          </label>
          <button className="primary" disabled={loading}>
            <Play size={17} />
            {loading ? "Agent 执行中" : "创建尽调任务"}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      </section>

      <section className="content">
        <div className="status-strip">
          <div>
            <span>任务编号</span>
            <strong>{task?.id.slice(0, 8) ?? "未开始"}</strong>
          </div>
          <div>
            <span>任务状态</span>
            <strong>{statusLabels[task?.status ?? "idle"] ?? task?.status}</strong>
          </div>
          <div className={`risk-pill ${riskClass}`}>
            <span>风险等级</span>
            <strong>{riskLabels[task?.risk_level ?? ""] ?? "--"}</strong>
          </div>
          <div>
            <span>综合评分</span>
            <strong>{task?.total_score ?? "--"}</strong>
          </div>
        </div>

        <section className="panel">
          <h2>Agent 执行时间线</h2>
          <div className="timeline">
            {events.map((event) => (
              <article className="event" key={event.id}>
                <CheckCircle2 size={18} />
                <div>
                  <div className="event-head">
                    <strong>{agentLabels[event.agent_name] ?? event.agent_name}</strong>
                    <span>{statusLabels[event.status] ?? event.status}</span>
                  </div>
                  <p>{event.summary}</p>
                  {event.tool_calls.length > 0 && (
                    <ul className="tool-list">
                      {event.tool_calls.map((call, index) => (
                        <li key={index}>{formatToolCall(call)}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </article>
            ))}
            {!events.length && <p className="muted">请选择一个样例供应商，或填写表单后创建尽调任务。</p>}
          </div>
        </section>

        <section className="panel">
          <h2>风险画像</h2>
          <div className="risk-grid">
            {task?.dimensions.map((dimension) => (
              <article key={dimension.dimension} className="metric">
                <div>
                  <strong>{dimensionLabels[dimension.dimension] ?? dimension.dimension}</strong>
                  <span>{riskLabels[dimension.level] ?? dimension.level}</span>
                </div>
                <meter min="0" max="100" value={dimension.score} />
                <p>{dimension.rationale}</p>
              </article>
            ))}
          </div>
          <div className="evidence-list">
            {task?.evidence.map((item) => (
              <article key={`${item.source}-${item.title}`}>
                <span>{severityLabels[item.severity] ?? item.severity}</span>
                <strong>{item.title}</strong>
                <p>{item.content}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel report-panel">
          <div className="panel-actions">
            <h2>尽调报告</h2>
            <div>
              <button title="复制报告" onClick={() => void navigator.clipboard.writeText(report)} disabled={!report}>
                <Clipboard size={16} />
              </button>
              <button title="下载 Markdown 报告" onClick={downloadReport} disabled={!report}>
                <Download size={16} />
              </button>
            </div>
          </div>
          {report ? <div className="markdown" dangerouslySetInnerHTML={reportHtml} /> : <div className="empty"><FileText />暂无报告</div>}
        </section>
      </section>
    </main>
  );
}

export default App;
