import type { RiskLevel } from "../types/diligence";

export const riskText: Record<RiskLevel, string> = { low: "低风险", medium: "中风险", high: "高风险" };
export const eventText: Record<string, string> = { agent_started: "开始", tool_called: "工具调用", agent_completed: "完成", agent_failed: "失败" };
export const decisionText: Record<string, string> = { approve: "准入", approve_with_conditions: "有条件准入", reject: "拒绝", escalate: "升级审批" };
export const dimensionText: Record<string, string> = {
  compliance: "合规风险",
  business: "经营风险",
  delivery: "交付风险",
  completeness: "资料完整性",
  reputation: "舆情风险"
};

export function money(value?: number) {
  if (typeof value !== "number") return "--";
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 0 }).format(value);
}

export function time(value?: string) {
  if (!value) return "--";
  return new Date(value).toLocaleString("zh-CN");
}
