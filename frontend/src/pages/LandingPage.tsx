import { ArrowRight, Database, FileText, PlusCircle, ShieldCheck, Workflow } from "lucide-react";

export function LandingPage({
  onCreateTask,
  onStartDemo,
  onOpenTasks,
  onOpenStatus,
}: {
  onCreateTask: () => void;
  onStartDemo: () => void;
  onOpenTasks: () => void;
  onOpenStatus: () => void;
}) {
  return (
    <main className="landing-page">
      <section className="landing-hero">
        <nav className="landing-nav">
          <strong>SupplyGuard Agent</strong>
          <div>
            <button onClick={onCreateTask}>新建任务</button>
            <button onClick={onStartDemo}>Demo</button>
            <button onClick={onOpenTasks}>任务列表</button>
            <button onClick={onOpenStatus}>Provider 状态</button>
          </div>
        </nav>
        <div className="hero-content">
          <p className="eyebrow">AI Agent · 公开信息尽调 · 证据链报告</p>
          <h1>供应商准入尽调与风险研判演示网站</h1>
          <p>从企业名称输入到搜索计划、联网证据可信度评估、企业画像、规则评分和 Markdown/PDF 报告下载，展示一个可部署的供应商风险 Agent 闭环。</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={onCreateTask}><PlusCircle size={16} />创建新任务</button>
            <button className="secondary-button" onClick={onOpenTasks}>查看历史任务</button>
            <button className="secondary-button" onClick={onStartDemo}>开始缓存演示 <ArrowRight size={16} /></button>
          </div>
        </div>
      </section>
      <section className="landing-feature-grid subtle-grid">
        <article><Workflow size={22} /><h2>Agent 工作流</h2><p>搜索计划、Provider 调用、证据评估、画像抽取、规则评分和报告生成分阶段展示。</p></article>
        <article><Database size={22} /><h2>Cached Demo Mode</h2><p>使用预置案例稳定展示完整流程，便于快速演示和对账。</p></article>
        <article><ShieldCheck size={22} /><h2>证据可信度</h2><p>区分目标签约主体、关联公司、品牌新闻和普通搜索记录，降低误伤。</p></article>
        <article><FileText size={22} /><h2>报告导出</h2><p>Markdown 与 PDF 文件名均绑定当前 task_id，便于和数据库结果对账。</p></article>
      </section>
      <section className="landing-disclaimer subtle-disclaimer">
        <h2>免责声明</h2>
        <p>本网站用于技术演示。缓存案例来自公开网页摘要和模拟数据，不构成投资、采购或法律意见；正式准入仍需人工复核和官方工商/司法/合规系统核验。</p>
      </section>
    </main>
  );
}