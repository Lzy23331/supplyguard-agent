import { Upload } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";
import type { UploadMaterial } from "../types/diligence";

export function FileUploadPanel({ uploads, onUploadsChange }: { uploads: UploadMaterial[]; onUploadsChange: (uploads: UploadMaterial[]) => void }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function upload(file: File) {
    setUploading(true);
    setError("");
    try {
      const result = await api.uploadMaterial(file);
      onUploadsChange([...uploads, result]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="file-upload-panel">
      <div className="section-title compact-title">
        <h3>可选：上传供应商材料</h3>
        <p>支持 .txt、.md、.csv、.pdf，解析文本会随任务提交并抽取风险证据。</p>
      </div>
      <label className="upload-button">
        <Upload size={16} />
        {uploading ? "上传解析中..." : "选择文件上传"}
        <input
          type="file"
          accept=".txt,.md,.csv,.pdf"
          disabled={uploading}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void upload(file);
            event.currentTarget.value = "";
          }}
        />
      </label>
      {error ? <div className="error-text">{error}</div> : null}
      {uploads.length ? (
        <div className="upload-list">
          {uploads.map((item) => (
            <article key={item.upload_id} className={item.status}>
              <strong>{item.filename}</strong>
              <span>{item.status === "parsed" ? `解析成功，文本 ${item.text_length ?? 0} 字符` : item.status === "failed" ? `解析失败：${item.error_message}` : "已上传"}</span>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
