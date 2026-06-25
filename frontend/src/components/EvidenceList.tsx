import type { EvidenceItem } from "../types/diligence";
import { EvidenceSourceBadge } from "./EvidenceSourceBadge";

const severityText: Record<string, string> = { info: "信息", warning: "预警", critical: "严重" };

function evidenceKindLabel(item: EvidenceItem) {
  const shouldScore = item.should_use_for_scoring === true || item.should_use_for_scoring === 1;
  if (shouldScore) return "实际风险证据";
  if (item.source_type === "web_search" || item.source_type === "web_search_profile") return "观察记录";
  if (item.source_type === "user_input" || item.source_type === "uploaded_file") return "材料证据";
  return "不参与评分";
}

export function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  if (!evidence.length) return <div className="empty-state">暂无证据链。</div>;
  return (
    <div className="evidence-grid">
      {evidence.map((item) => (
        <article className={`evidence-card ${item.severity}`} key={item.id ?? item.title}>
          <div className="evidence-head"><EvidenceSourceBadge sourceType={item.source_type} /><b>{severityText[item.severity] ?? item.severity}</b><b>{evidenceKindLabel(item)}</b></div>
          <h3>{item.title}</h3>
          <p>{item.content}</p>
          {item.risk_keywords?.length ? <div className="tag-row">{item.risk_keywords.map((signal) => <span key={signal}>{signal}</span>)}</div> : null}
          {!item.risk_keywords?.length && item.rule_signals?.length ? <div className="tag-row">{item.rule_signals.map((signal) => <span key={signal}>{signal}</span>)}</div> : null}
          {typeof item.confidence === "number" ? <small>置信度：{item.confidence.toFixed(2)}</small> : null}
          {item.raw_text ? <p className="rationale">原文摘录：{item.raw_text}</p> : null}
          {item.economic_rationale ? <p className="rationale">业务含义：{item.economic_rationale}</p> : null}
          {item.url || item.source_url ? <a className="source-link" href={item.url || item.source_url} target="_blank" rel="noreferrer">{item.url || item.source_url}</a> : null}
        </article>
      ))}
    </div>
  );
}

