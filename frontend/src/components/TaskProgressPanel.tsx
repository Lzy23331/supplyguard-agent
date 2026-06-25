import { CheckCircle2, Clock3, Loader2, XCircle } from "lucide-react";
import type { AgentEvent, TaskDetail } from "../types/diligence";

const statusText: Record<string, string> = {
  pending: "等待执行",
  running: "任务执行中",
  completed: "执行完成",
  failed: "执行失败",
  reviewed: "已人工复核",
};

function completedAgentCount(events: AgentEvent[]) {
  return new Set(events.filter((event) => event.event_type === "agent_completed").map((event) => event.agent_name)).size;
}

export function TaskProgressPanel({ detail, events }: { detail: TaskDetail; events: AgentEvent[] }) {
  const status = detail.task.status;
  const latest = events.length ? events[events.length - 1] : undefined;
  const failedMessage = detail.task.error_message || detail.error_message;
  const Icon = status === "completed" ? CheckCircle2 : status === "failed" ? XCircle : status === "pending" ? Clock3 : Loader2;

  return (
    <section className={`panel progress-panel ${status}`}>
      <div className="progress-head">
        <Icon size={20} />
        <div>
          <h2>{statusText[status] ?? status}</h2>
          <p>{latest ? `${latest.agent_name}: ${latest.summary}` : "等待 Agent 事件写入。"}</p>
        </div>
      </div>
      <div className="progress-metrics">
        <div><span>当前状态</span><strong>{statusText[status] ?? status}</strong></div>
        <div><span>Agent events</span><strong>{events.length}</strong></div>
        <div><span>已完成 Agent</span><strong>{completedAgentCount(events)}</strong></div>
      </div>
      {status === "failed" ? <div className="error-banner">{failedMessage || "后台任务执行失败，暂无详细原因。"}</div> : null}
      {status === "completed" ? <div className="success-text">尽调任务已完成，风险画像、证据链和报告已刷新。</div> : null}
    </section>
  );
}
