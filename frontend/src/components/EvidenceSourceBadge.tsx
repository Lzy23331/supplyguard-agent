const sourceText: Record<string, string> = {
  mock_sample: "模拟公开信息",
  user_input: "用户输入材料",
  uploaded_file: "上传文件",
  external_api: "外部数据源",
  real_external: "真实外部数据",
  web_search: "联网搜索",
  web_search_profile: "联网搜索画像推断",
  mock_external: "模拟外部数据",
  internal_record: "内部记录",
};

export function EvidenceSourceBadge({ sourceType }: { sourceType?: string }) {
  const type = sourceType || "mock_sample";
  return <span className={`source-badge ${type}`}>{sourceText[type] ?? type}</span>;
}
