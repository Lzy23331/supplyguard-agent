import { CheckCircle2, CircleDot, Wrench, XCircle } from "lucide-react";
import type { AgentEvent } from "../types/diligence";
import { eventText, time } from "./format";

const iconMap: Record<string, typeof CircleDot> = { agent_started: CircleDot, tool_called: Wrench, agent_completed: CheckCircle2, agent_failed: XCircle };

export function AgentTimeline({ events }: { events: AgentEvent[] }) {
  if (!events.length) return <div className="empty-state">暂无 Agent 执行事件。</div>;
  return (
    <div className="timeline-list">
      {events.map((event) => {
        const Icon = iconMap[event.event_type ?? ""] ?? CircleDot;
        return (
          <article className={`timeline-event ${event.event_type ?? ""}`} key={event.id}>
            <Icon size={18} />
            <div>
              <div className="event-header"><strong>{event.agent_name}</strong><span>{eventText[event.event_type ?? ""] ?? event.event_type}</span><time>{time(event.created_at)}</time></div>
              <p>{event.summary}</p>
              {event.tool_name ? <div className="tool-box"><b>{event.tool_name}</b><span>{event.tool_output_summary}</span><code>{JSON.stringify(event.tool_input, null, 2)}</code></div> : null}
            </div>
          </article>
        );
      })}
    </div>
  );
}
