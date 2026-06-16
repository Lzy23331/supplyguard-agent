import { useEffect, useState } from "react";
import { api } from "../api/client";
import { SampleSupplierCards } from "../components/SampleSupplierCards";
import { defaultSupplier, SupplierForm } from "../components/SupplierForm";
import type { Supplier } from "../types/diligence";

export function TaskCreatePage({ onTaskCreated }: { onTaskCreated: (taskId: string) => void }) {
  const [samples, setSamples] = useState<Supplier[]>([]);
  const [supplier, setSupplier] = useState<Supplier>(defaultSupplier);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSampleSuppliers().then(setSamples).catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  async function createFromSample(id: string) {
    setLoading(true);
    setError("");
    try {
      const task = await api.createTaskFromSample(id);
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
      const task = await api.createCustomTask(supplier);
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
          <p>基于多 Agent 工作流、政策检索、规则评分和证据链追踪的供应商准入演示系统。</p>
        </div>
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      <section className="section-block">
        <div className="section-title"><h2>样例供应商</h2><p>选择低/中/高风险样例，快速生成完整尽调任务。</p></div>
        <SampleSupplierCards samples={samples} loading={loading} onCreate={createFromSample} />
      </section>
      <section className="section-block">
        <div className="section-title"><h2>自定义供应商</h2><p>录入供应商基础资料，系统会同步执行 Agent 工作流。</p></div>
        <SupplierForm value={supplier} loading={loading} onChange={setSupplier} onSubmit={createCustom} />
      </section>
    </main>
  );
}
