import { Search } from "lucide-react";

export type CompanyNameSearchValue = {
  company_name: string;
  procurement_amount?: number;
  cooperation_type?: string;
};

export function CompanyNameSearchPanel({
  value,
  loading,
  hasMaterial,
  modeLabel = "Real Query Mode",
  modeDescription = "将调用后端配置的联网搜索 Provider，并把搜索结果、企业画像和报告写入当前任务。",
  onChange,
  onSubmit,
}: {
  value: CompanyNameSearchValue;
  loading: boolean;
  hasMaterial: boolean;
  modeLabel?: string;
  modeDescription?: string;
  onChange: (value: CompanyNameSearchValue) => void;
  onSubmit: () => void;
}) {
  return (
    <div className="company-search-panel">
      <div className="query-mode-banner">
        <strong>{modeLabel}</strong>
        <span>{modeDescription}</span>
      </div>
      <div className="form-grid compact">
        <label>
          企业名称
          <input
            value={value.company_name}
            onChange={(event) => onChange({ ...value, company_name: event.target.value })}
            placeholder="例如：大疆创新科技有限公司"
          />
        </label>
        <label>
          采购金额
          <input
            type="number"
            min={0}
            value={value.procurement_amount ?? ""}
            onChange={(event) => onChange({ ...value, procurement_amount: Number(event.target.value || 0) })}
            placeholder="500000"
          />
        </label>
        <label>
          合作类型
          <select value={value.cooperation_type ?? ""} onChange={(event) => onChange({ ...value, cooperation_type: event.target.value })}>
            <option value="">未选择</option>
            <option value="常规采购">常规采购</option>
            <option value="框架协议">框架协议</option>
            <option value="紧急采购">紧急采购</option>
            <option value="试单采购">试单采购</option>
          </select>
        </label>
      </div>
      <button className="primary-button wide" disabled={loading || !value.company_name.trim()} onClick={onSubmit}>
        <Search size={16} />
        {hasMaterial ? "创建真实查询任务并分析补充材料" : "创建真实查询任务"}
      </button>
    </div>
  );
}