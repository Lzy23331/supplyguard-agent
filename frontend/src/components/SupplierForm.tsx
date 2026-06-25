import type { FormEvent } from "react";
import type { Supplier } from "../types/diligence";

export const defaultSupplier: Supplier = {
  name: "Demo Supplier Ltd.",
  website: "https://example.com/demo",
  industry: "电子元器件",
  region: "广东深圳",
  procurement_amount: 800000,
  annual_spend: 800000,
  cooperation_type: "标准采购",
  business_status: "正常",
  company_age_years: 5,
  profile_completeness: "中",
  ownership_transparency: "中",
  urgency: "常规"
};

export function SupplierForm({ value, loading, hasMaterial, onChange, onSubmit }: { value: Supplier; loading: boolean; hasMaterial?: boolean; onChange: (next: Supplier) => void; onSubmit: () => void }) {
  function set<K extends keyof Supplier>(key: K, next: Supplier[K]) {
    onChange({ ...value, [key]: next });
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
  }
  return (
    <form className="supplier-form" onSubmit={submit}>
      <div className="form-grid">
        <label>供应商名称<input value={value.name} onChange={(e) => set("name", e.target.value)} required /></label>
        <label>官网<input value={value.website ?? ""} onChange={(e) => set("website", e.target.value)} /></label>
        <label>行业<input value={value.industry ?? ""} onChange={(e) => set("industry", e.target.value)} /></label>
        <label>地区<input value={value.region ?? ""} onChange={(e) => set("region", e.target.value)} /></label>
        <label>采购金额<input type="number" min="0" value={value.procurement_amount ?? 0} onChange={(e) => set("procurement_amount", Number(e.target.value))} /></label>
        <label>年采购金额<input type="number" min="0" value={value.annual_spend ?? 0} onChange={(e) => set("annual_spend", Number(e.target.value))} /></label>
        <label>合作类型<select value={value.cooperation_type ?? ""} onChange={(e) => set("cooperation_type", e.target.value)}>
          <option value="">未提供</option><option>标准采购</option><option>年度框架采购</option><option>紧急采购</option>
        </select></label>
        <label>经营状态<select value={value.business_status ?? ""} onChange={(e) => set("business_status", e.target.value)}>
          <option value="">未提供</option><option>正常</option><option>经营异常</option><option>信息不透明</option>
        </select></label>
        <label>成立年限<input type="number" min="0" value={value.company_age_years ?? 5} onChange={(e) => set("company_age_years", Number(e.target.value))} /></label>
        <label>资料完整性<select value={value.profile_completeness ?? ""} onChange={(e) => set("profile_completeness", e.target.value)}>
          <option value="">未提供</option><option>高</option><option>中</option><option>低</option>
        </select></label>
        <label>股权透明度<select value={value.ownership_transparency ?? ""} onChange={(e) => set("ownership_transparency", e.target.value)}>
          <option value="">未提供</option><option>高</option><option>中</option><option>低</option>
        </select></label>
        <label>采购紧急度<select value={value.urgency ?? ""} onChange={(e) => set("urgency", e.target.value)}>
          <option value="">未提供</option><option>常规</option><option>紧急</option>
        </select></label>
      </div>
      <button className="primary-button wide" disabled={loading}>{loading ? "执行中..." : hasMaterial ? "创建自定义任务并分析补充材料" : "创建自定义尽调任务"}</button>
    </form>
  );
}
