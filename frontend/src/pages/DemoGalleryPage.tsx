import { ArrowLeft, PlayCircle, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { riskText } from "../components/format";
import type { DemoCaseSummary, ProviderStatus } from "../types/diligence";

export function DemoGalleryPage({ onBack, onOpenTask }: { onBack: () => void; onOpenTask: (taskId: string) => void }) {
  const [cases, setCases] = useState<DemoCaseSummary[]>([]);
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [runningCase, setRunningCase] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [nextCases, nextStatus] = await Promise.all([api.getDemoCases(), api.getProviderStatus()]);
      setCases(nextCases);
      setStatus(nextStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => { void load(); }, []);

  async function runCase(caseId: string) {
    setRunningCase(caseId);
    setError("");
    try {
      const detail = await api.runDemoCase(caseId);
      onOpenTask(detail.task_id || detail.id || detail.task.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunningCase(null);
    }
  }

  return (
    <main className="page-shell demo-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Cached Demo Mode</p>
          <h1>演示案例库</h1>
          <p>点击示例会创建缓存演示任务，不调用实时腾讯云或 LLM API。</p>
        </div>
        <div className="action-row compact-actions">
          <button className="ghost-button" onClick={onBack}><ArrowLeft size={16} />返回首页</button>
          <button className="secondary-button" onClick={() => void load()}><RefreshCw size={16} />刷新</button>
        </div>
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      <section className="panel mode-banner">
        <strong>当前模式：{status?.deployment_mode || "demo"}</strong>
        <span>实时查询：{status?.real_query_enabled ? "已开启，会消耗 API" : "默认关闭，缓存演示不消耗 API"}</span>
        <span>PDF 导出：{status?.pdf_export_available ? "可用" : "不可用"}</span>
      </section>
      <section className="demo-grid">
        {cases.map((item) => (
          <article className="demo-card" key={item.case_id}>
            <div className="demo-card-head">
              <span className={`risk-badge ${item.risk_level || "low"}`}>{item.risk_level ? riskText[item.risk_level] : "演示"}</span>
              <small>{item.cached_demo ? "Cached" : "Real"}</small>
            </div>
            <h2>{item.company_name}</h2>
            <p>{item.description}</p>
            <dl className="compact-meta">
              <div><dt>评分</dt><dd>{item.score ?? "--"}</dd></div>
              <div><dt>搜索结果 / URL</dt><dd>{item.web_search_results_count} / {item.real_url_count}</dd></div>
              <div><dt>画像字段</dt><dd>{item.profile_field_count}</dd></div>
            </dl>
            <button className="primary-button wide" onClick={() => void runCase(item.case_id)} disabled={runningCase === item.case_id}>
              <PlayCircle size={16} />{runningCase === item.case_id ? "创建中" : "运行缓存演示"}
            </button>
          </article>
        ))}
      </section>
      <section className="panel real-query-note">
        <h2>Real Query Mode</h2>
        <p>{status?.real_query_enabled ? "后端已开启实时查询，可在创建页输入真实企业名称；该模式会消耗 API 次数。" : "当前实时查询入口关闭。设置 ENABLE_REAL_QUERY=true 且后端密钥配置完整后，可用于本地管理员演示。"}</p>
      </section>
    </main>
  );
}
