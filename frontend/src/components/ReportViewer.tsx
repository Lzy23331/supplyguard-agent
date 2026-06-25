import { Clipboard, Download } from "lucide-react";
import { marked } from "marked";
import { api } from "../api/client";
import { useMemo, useState } from "react";

export function ReportViewer({ taskId, markdown }: { taskId: string; markdown?: string }) {
  const [copied, setCopied] = useState(false);
  const html = useMemo(() => ({ __html: marked.parse(markdown ?? "") as string }), [markdown]);
  if (!markdown) return <div className="empty-state">暂无报告。</div>;
  async function copy() {
    await navigator.clipboard.writeText(markdown ?? "");
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }
  async function downloadPdf() {
    const blob = await api.getTaskReportPdf(taskId);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `supplyguard-report-${taskId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }
  function download() {
    const blob = new Blob([markdown ?? ""], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `supplyguard-report-${taskId}.md`;
    link.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div>
      <div className="export-binding-note">将导出当前任务：<code>{taskId}</code></div>
      <div className="action-row">
        <button className="secondary-button" onClick={copy}><Clipboard size={16} />{copied ? "已复制" : "复制报告"}</button>
        <button className="secondary-button" onClick={download}><Download size={16} />下载 Markdown</button>
        <button className="secondary-button" onClick={() => void downloadPdf()}><Download size={16} />下载 PDF</button>
      </div>
      <div className="markdown-card" dangerouslySetInnerHTML={html} />
    </div>
  );
}


