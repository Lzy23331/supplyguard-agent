import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clipboard, Download, FileText, Play, ShieldAlert, Sparkles } from "lucide-react";
import { marked } from "marked";
import { AgentEvent, api, DiligenceTask, SupplierInput } from "./api/client";

const emptySupplier: SupplierInput = {
  name: "",
  website: "",
  industry: "Industrial components",
  region: "Singapore",
  annual_spend: 180000,
  cooperation_type: "standard parts supplier"
};

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
    link.download = `${task?.supplier.name ?? "supplier"}-diligence-report.md`;
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
            <p>Supplier onboarding due diligence and risk reasoning system</p>
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
              {item.sample_key}
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
            Supplier name
            <input value={supplier.name} onChange={(event) => updateField("name", event.target.value)} required />
          </label>
          <label>
            Website
            <input value={supplier.website ?? ""} onChange={(event) => updateField("website", event.target.value)} />
          </label>
          <label>
            Industry
            <input value={supplier.industry} onChange={(event) => updateField("industry", event.target.value)} required />
          </label>
          <label>
            Region
            <input value={supplier.region} onChange={(event) => updateField("region", event.target.value)} required />
          </label>
          <label>
            Annual spend
            <input
              type="number"
              min="0"
              value={supplier.annual_spend}
              onChange={(event) => updateField("annual_spend", Number(event.target.value))}
              required
            />
          </label>
          <label>
            Cooperation type
            <input
              value={supplier.cooperation_type}
              onChange={(event) => updateField("cooperation_type", event.target.value)}
              required
            />
          </label>
          <button className="primary" disabled={loading}>
            <Play size={17} />
            {loading ? "Running agents" : "Create diligence task"}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      </section>

      <section className="content">
        <div className="status-strip">
          <div>
            <span>Task</span>
            <strong>{task?.id.slice(0, 8) ?? "Not started"}</strong>
          </div>
          <div>
            <span>Status</span>
            <strong>{task?.status ?? "idle"}</strong>
          </div>
          <div className={`risk-pill ${riskClass}`}>
            <span>Risk</span>
            <strong>{task?.risk_level ?? "--"}</strong>
          </div>
          <div>
            <span>Score</span>
            <strong>{task?.total_score ?? "--"}</strong>
          </div>
        </div>

        <section className="panel">
          <h2>Agent Timeline</h2>
          <div className="timeline">
            {events.map((event) => (
              <article className="event" key={event.id}>
                <CheckCircle2 size={18} />
                <div>
                  <div className="event-head">
                    <strong>{event.agent_name}</strong>
                    <span>{event.status}</span>
                  </div>
                  <p>{event.summary}</p>
                  {event.tool_calls.length > 0 && <code>{JSON.stringify(event.tool_calls)}</code>}
                </div>
              </article>
            ))}
            {!events.length && <p className="muted">Create a task or choose a sample supplier.</p>}
          </div>
        </section>

        <section className="panel">
          <h2>Risk Portrait</h2>
          <div className="risk-grid">
            {task?.dimensions.map((dimension) => (
              <article key={dimension.dimension} className="metric">
                <div>
                  <strong>{dimension.dimension}</strong>
                  <span>{dimension.level}</span>
                </div>
                <meter min="0" max="100" value={dimension.score} />
                <p>{dimension.rationale}</p>
              </article>
            ))}
          </div>
          <div className="evidence-list">
            {task?.evidence.map((item) => (
              <article key={`${item.source}-${item.title}`}>
                <span>{item.severity}</span>
                <strong>{item.title}</strong>
                <p>{item.content}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel report-panel">
          <div className="panel-actions">
            <h2>Report</h2>
            <div>
              <button onClick={() => void navigator.clipboard.writeText(report)} disabled={!report}>
                <Clipboard size={16} />
              </button>
              <button onClick={downloadReport} disabled={!report}>
                <Download size={16} />
              </button>
            </div>
          </div>
          {report ? <div className="markdown" dangerouslySetInnerHTML={reportHtml} /> : <div className="empty"><FileText />No report yet</div>}
        </section>
      </section>
    </main>
  );
}

export default App;

