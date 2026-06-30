import { ArrowLeft, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ProviderStatus } from "../types/diligence";

function StatusItem({ label, value }: { label: string; value: string | boolean | null | undefined }) {
  return <div><span>{label}</span><strong>{typeof value === "boolean" ? (value ? "是" : "否") : value || "未配置"}</strong></div>;
}

export function ProviderStatusPage({ onBack }: { onBack: () => void }) {
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      setStatus(await api.getProviderStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => { void load(); }, []);

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">System Status</p>
          <h1>Provider 与部署状态</h1>
          <p>仅展示服务配置状态，不展示任何密钥或密钥尾号。</p>
        </div>
        <div className="action-row compact-actions">
          <button className="ghost-button" onClick={onBack}><ArrowLeft size={16} />返回首页</button>
          <button className="secondary-button" onClick={() => void load()}><RefreshCw size={16} />刷新</button>
        </div>
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      <section className="panel">
        {!status ? <div className="loading-card">读取 Provider 状态中...</div> : (
          <div className="diagnostic-grid">
            <StatusItem label="部署模式" value={status.deployment_mode} />
            <StatusItem label="Demo Mode" value={status.demo_mode_available} />
            <StatusItem label="Real Query 已启用" value={status.real_query_enabled} />
            <StatusItem label="腾讯云搜索已配置" value={status.tencent_search_configured} />
            <StatusItem label="LLM 已配置" value={status.llm_configured} />
            <StatusItem label="PDF 导出" value={status.pdf_export_available} />
            <StatusItem label="腾讯云 Secret" value={status.tencent_search_configured ? "已配置" : "未配置"} />
            <StatusItem label="LLM Secret" value={status.llm_configured ? "已配置" : "未配置"} />
          </div>
        )}
      </section>
      <section className="panel">
        <h2>安全边界</h2>
        <p className="summary-text">密钥只应存在于后端 .env 或部署平台 Secret 中。前端页面、报告、PDF、公开 API 和 Git 仓库不得包含 API Key 或密钥尾号。</p>
      </section>
    </main>
  );
}
