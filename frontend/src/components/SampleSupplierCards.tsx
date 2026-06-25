import { ShieldCheck, Sparkles } from "lucide-react";
import type { Supplier } from "../types/diligence";
import { money, riskText } from "./format";

export function SampleSupplierCards({ samples, loading, hasMaterial, onCreate }: { samples: Supplier[]; loading: boolean; hasMaterial?: boolean; onCreate: (id: string) => void }) {
  if (!samples.length) return <div className="empty-state">暂无样例供应商，请确认后端已启动。</div>;
  return (
    <div className="sample-grid">
      {samples.map((supplier) => (
        <article className={`sample-card ${supplier.expected_risk_level ?? ""}`} key={supplier.id}>
          <div className="card-title-row">
            <ShieldCheck size={20} />
            <span className={`risk-badge ${supplier.expected_risk_level ?? ""}`}>{supplier.expected_risk_level ? riskText[supplier.expected_risk_level] : "待评估"}</span>
          </div>
          <h3>{supplier.name}</h3>
          <dl className="compact-meta">
            <div><dt>行业</dt><dd>{supplier.industry}</dd></div>
            <div><dt>地区</dt><dd>{supplier.region}</dd></div>
            <div><dt>采购金额</dt><dd>{money(supplier.procurement_amount ?? supplier.annual_spend)}</dd></div>
            <div><dt>合作类型</dt><dd>{supplier.cooperation_type}</dd></div>
          </dl>
          <p className="summary-text">{supplier.summary}</p>
          <div className="tag-row">{supplier.tags?.map((tag) => <span key={tag}>{tag}</span>)}</div>
          <button className="primary-button" disabled={loading || !supplier.id} onClick={() => supplier.id && onCreate(supplier.id)}>
            <Sparkles size={16} />{hasMaterial ? "创建该样例任务并分析补充材料" : "创建该样例任务"}
          </button>
        </article>
      ))}
    </div>
  );
}
