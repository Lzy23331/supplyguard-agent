import { ArrowLeft, Download, ExternalLink, RefreshCw, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { money, riskText, time } from "../components/format";
import type { DiligenceTaskSummary } from "../types/diligence";

function shortId(taskId: string) {
  return taskId.slice(0, 8);
}

function downloadMarkdown(taskId: string, markdown: string, filename?: string) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || `supplyguard-report-${taskId}.md`;
  link.click();
  URL.revokeObjectURL(url);
}

export function TaskListPage({ onBackHome, onOpenTask, onCreateNew }: { onBackHome: () => void; onOpenTask: (taskId: string) => void; onCreateNew: () => void }) {
  const [tasks, setTasks] = useState<DiligenceTaskSummary[]>([]);
  const [taskIdInput, setTaskIdInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setTasks(await api.getTasks());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function exportTask(taskId: string) {
    setError("");
    try {
      const report = await api.getTaskReport(taskId);
      downloadMarkdown(taskId, report.markdown_content, report.filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function openManual() {
    const next = taskIdInput.trim();
    if (next) onOpenTask(next);
  }

  return (
    <main className="page-shell task-list-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">SupplyGuard Agent</p>
          <h1>历史尽调任务</h1>
          <p>按 task_id 打开详情、核对联网搜索数据，并导出当前任务报告。</p>
        </div>
        <div className="action-row compact-actions">
          <button className="ghost-button" onClick={onBackHome}><ArrowLeft size={16} />返回首页</button>
          <button className="secondary-button" onClick={() => void load()} disabled={loading}><RefreshCw size={16} />刷新</button>
          <button className="primary-button" onClick={onCreateNew}>新建任务</button>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="panel open-task-panel">
        <label>
          按 Task ID 打开
          <div className="task-id-open-row">
            <input value={taskIdInput} onChange={(event) => setTaskIdInput(event.target.value)} placeholder="输入完整 task_id，例如 55aa5baa-e241-4df4-9972-ca07ab86bc96" />
            <button className="secondary-button" onClick={openManual}><Search size={16} />打开</button>
          </div>
        </label>
      </section>

      <section className="panel task-table-panel">
        <div className="section-title"><h2>任务列表</h2><p>按创建时间倒序展示，导出按钮严格使用该行 task_id。</p></div>
        {loading ? <div className="loading-card">加载任务列表中...</div> : null}
        {!loading && !tasks.length ? <div className="empty-state">暂无历史任务。</div> : null}
        {tasks.length ? (
          <div className="task-table-wrap">
            <table className="task-table">
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>企业名称</th>
                  <th>创建时间</th>
                  <th>状态</th>
                  <th>风险</th>
                  <th>分数</th>
                  <th>搜索/URL</th>
                  <th>画像</th>
                  <th>采购金额</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.task_id}>
                    <td><button className="link-button" onClick={() => onOpenTask(task.task_id)}>{shortId(task.task_id)}</button></td>
                    <td>{task.supplier_name || "未命名企业"}</td>
                    <td>{time(task.created_at)}</td>
                    <td>{task.status}</td>
                    <td>{task.risk_level ? riskText[task.risk_level] : "--"}</td>
                    <td>{task.total_score ?? "--"}</td>
                    <td>{task.web_search_result_count ?? 0} / {task.real_url_count ?? 0}</td>
                    <td>{task.profile_snapshot_count ?? 0}（非空 {task.profile_non_empty_count ?? 0}）</td>
                    <td>{money(task.procurement_amount ?? undefined)}</td>
                    <td>
                      <div className="table-actions">
                        <button className="secondary-button icon-button" title="打开详情" onClick={() => onOpenTask(task.task_id)}><ExternalLink size={16} /></button>
                        <button className="secondary-button icon-button" title={`导出当前任务 ${task.task_id}`} disabled={!task.report_available} onClick={() => void exportTask(task.task_id)}><Download size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </main>
  );
}

