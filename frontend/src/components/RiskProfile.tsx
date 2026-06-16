import type { RiskAssessment } from "../types/diligence";
import { dimensionText, riskText } from "./format";

export function RiskProfile({ risk }: { risk?: RiskAssessment }) {
  if (!risk) return <div className="empty-state">暂无风险评估。</div>;
  const level = risk.risk_level;
  return (
    <section className="panel risk-overview">
      <div className="overview-main">
        <span className={`risk-badge ${level ?? ""}`}>{level ? riskText[level] : "待评估"}</span>
        <strong>{risk.total_score ?? "--"}</strong>
        <small>综合评分 / 100</small>
      </div>
      <div className="overview-detail">
        <div className="metric-line"><span>原始分</span><b>{risk.raw_score ?? "--"}</b></div>
        <p>{risk.recommendation}</p>
        <div className="dimension-grid">
          {Object.entries(risk.dimension_scores ?? {}).map(([key, value]) => (
            <div className="dimension-item" key={key}><span>{dimensionText[key] ?? key}</span><meter min="0" max="100" value={value} /><b>{value}</b></div>
          ))}
        </div>
        <div className="rules-list">
          <h3>命中规则</h3>
          {(risk.triggered_rules ?? []).map((rule, index) => (
            <article key={`${rule.rule_id}-${index}`}>
              <div><strong>{rule.rule_name ?? rule.rule_id}</strong><span>{dimensionText[rule.dimension ?? ""] ?? rule.dimension} +{rule.score}</span></div>
              <p>{rule.reason}</p>
              {rule.evidence_ids?.length ? <small>证据：{rule.evidence_ids.join("、")}</small> : null}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
