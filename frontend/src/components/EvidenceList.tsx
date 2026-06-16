import type { EvidenceItem } from "../types/diligence";

const severityText: Record<string, string> = { info: "信息", warning: "预警", critical: "严重" };

export function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  if (!evidence.length) return <div className="empty-state">暂无证据链。</div>;
  return (
    <div className="evidence-grid">
      {evidence.map((item) => (
        <article className={`evidence-card ${item.severity}`} key={item.id ?? item.title}>
          <div className="evidence-head"><span>{item.category ?? item.source}</span><b>{severityText[item.severity] ?? item.severity}</b></div>
          <h3>{item.title}</h3>
          <p>{item.content}</p>
          {item.rule_signals?.length ? <div className="tag-row">{item.rule_signals.map((signal) => <span key={signal}>{signal}</span>)}</div> : null}
          {item.economic_rationale ? <p className="rationale">业务含义：{item.economic_rationale}</p> : null}
          {item.url ? <small>{item.url}</small> : null}
        </article>
      ))}
    </div>
  );
}
