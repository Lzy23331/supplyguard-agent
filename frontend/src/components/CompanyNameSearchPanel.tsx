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
  onChange,
  onSubmit,
}: {
  value: CompanyNameSearchValue;
  loading: boolean;
  hasMaterial: boolean;
  onChange: (value: CompanyNameSearchValue) => void;
  onSubmit: () => void;
}) {
  return (
    <div className="company-search-panel">
      <div className="form-grid compact">
        <label>
          企业名称
          <input
            value={value.company_name}
            onChange={(event) => onChange({ ...value, company_name: event.target.value })}
            placeholder="Northbridge Electronics Trading LLC."
          />
        </label>
        <label>
          采购金额
          <input
            type="number"
            min={0}
            value={value.procurement_amount ?? ""}
            onChange={(event) => onChange({ ...value, procurement_amount: Number(event.target.value || 0) })}
            placeholder="5000000"
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
        {hasMaterial ? "按企业名称创建任务并分析补充材料" : "按企业名称创建任务"}
      </button>
    </div>
  );
}
