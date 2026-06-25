import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CompanyNameSearchPanel, type CompanyNameSearchValue } from "../components/CompanyNameSearchPanel";
import { FileUploadPanel } from "../components/FileUploadPanel";
import { MaterialInputBox } from "../components/MaterialInputBox";
import { SampleSupplierCards } from "../components/SampleSupplierCards";
import { defaultSupplier, SupplierForm } from "../components/SupplierForm";
import type { Supplier, UploadMaterial } from "../types/diligence";

export function TaskCreatePage({ onTaskCreated, onOpenTasks }: { onTaskCreated: (taskId: string) => void; onOpenTasks?: () => void }) {
  const [samples, setSamples] = useState<Supplier[]>([]);
  const [supplier, setSupplier] = useState<Supplier>(defaultSupplier);
  const [companyQuery, setCompanyQuery] = useState<CompanyNameSearchValue>({
    company_name: "Northbridge Electronics Trading LLC.",
    procurement_amount: 5000000,
    cooperation_type: "紧急采购",
  });
  const [materialText, setMaterialText] = useState("");
  const [uploads, setUploads] = useState<UploadMaterial[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSampleSuppliers().then(setSamples).catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  async function createFromSample(id: string) {
    setLoading(true);
    setError("");
    try {
      const task = await api.createDiligenceTask({ supplier_id: id, execution_mode: "async", material_text: materialText || undefined, upload_ids: uploads.filter((item) => item.status === "parsed").map((item) => item.upload_id) });
      onTaskCreated(task.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function createCustom() {
    setLoading(true);
    setError("");
    try {
      const task = await api.createDiligenceTask({ supplier, execution_mode: "async", material_text: materialText || undefined, upload_ids: uploads.filter((item) => item.status === "parsed").map((item) => item.upload_id) });
      onTaskCreated(task.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function createFromCompanyName() {
    setLoading(true);
    setError("");
    try {
      const task = await api.createDiligenceTask({
        company_name: companyQuery.company_name,
        procurement_amount: companyQuery.procurement_amount,
        cooperation_type: companyQuery.cooperation_type,
        execution_mode: "async",
        material_text: materialText || undefined,
        upload_ids: uploads.filter((item) => item.status === "parsed").map((item) => item.upload_id),
      });
      onTaskCreated(task.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">SupplyGuard Agent</p>
          <h1>供应商准入尽调与风险研判系统</h1>
          <p>创建任务后进入详情页，后台 Agent 会持续写入执行进度。</p>
        </div>
        {onOpenTasks ? <button className="secondary-button" onClick={onOpenTasks}>查看历史任务</button> : null}
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      <section className="section-block">
        <div className="section-title"><h2>可选：供应商补充材料</h2><p>这段材料会随你下方选择的创建方式一起提交，系统会从中抽取风险证据并参与评分。</p></div>
        <MaterialInputBox value={materialText} onChange={setMaterialText} />
        <FileUploadPanel uploads={uploads} onUploadsChange={setUploads} />
      </section>
      <section className="section-block">
        <div className="section-title"><h2>企业名称查询尽调</h2><p>输入企业名称创建任务，系统会先解析企业画像，再调用模拟外部数据源和内部记录抽取证据。</p></div>
        <CompanyNameSearchPanel value={companyQuery} loading={loading} hasMaterial={Boolean(materialText.trim()) || uploads.some((item) => item.status === "parsed")} onChange={setCompanyQuery} onSubmit={createFromCompanyName} />
      </section>
      <section className="section-block">
        <div className="section-title"><h2>自定义供应商尽调</h2><p>录入供应商基础资料，可选补充材料，系统会异步执行同一套 Agent 工作流。</p></div>
        <SupplierForm value={supplier} loading={loading} hasMaterial={Boolean(materialText.trim()) || uploads.some((item) => item.status === "parsed")} onChange={setSupplier} onSubmit={createCustom} />
      </section>
      <section className="section-block">
        <div className="section-title"><h2>样例供应商快速演示</h2><p>保留低/中/高风险样例；如上方补充材料有内容，也会随样例一起提交分析。</p></div>
        <SampleSupplierCards samples={samples} loading={loading} hasMaterial={Boolean(materialText.trim()) || uploads.some((item) => item.status === "parsed")} onCreate={createFromSample} />
      </section>
    </main>
  );
}


