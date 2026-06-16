# Business Background

SupplyGuard Agent 面向企业采购中的供应商准入尽调场景。采购团队希望快速引入供应商以保证价格、产能和交付弹性，合规团队则需要确认供应商是否真实、合法、稳定且可追责。

## 1. 业务问题

供应商准入不是简单登记表单，而是一组风险取舍：信息不对称、逆向选择、转换成本、合规外部性和证据分散。制裁名单、黑名单、商业贿赂、欺诈、重大失信和行政处罚不仅影响一次采购，还可能带来监管、付款、声誉和内部问责风险。

## 2. 为什么适合做 Agent 项目

1. IntakeAgent 读取供应商输入，决定尽调检查范围。
2. EvidenceCollectorAgent 收集模拟公开证据和内部参考证据。
3. ComplianceRiskAgent 检索政策知识库，执行合规评分。
4. BusinessRiskAgent 评估经营、交付、资料完整性和舆情风险。
5. ReportAgent 生成结构化 Markdown 尽调报告。

每个 Agent 的输入、输出和工具调用都可以被记录，因此适合展示工程化 Agent 的可观测性。

## 3. 第一版业务边界

1. 使用本地 mock 样例，不接真实工商、司法、制裁或新闻接口。
2. 使用本地 Markdown 政策知识库，不引入复杂向量数据库。
3. 风险等级由规则引擎计算，不由 LLM 决定。
4. 内部风险等级统一为 `low`、`medium`、`high`；展示层映射为低风险、中风险、高风险。
5. 所有结论仅用于学习和演示，不构成真实合规、法律或商业决策建议。

## 4. 三类演示供应商

low：Aster Precision Components Co., Ltd. 主体信息完整、经营稳定、采购金额适中、无重大负面，适合演示标准准入。

medium：Nova Packaging Materials Ltd. 经营正常但存在交付延期、轻微合同争议、资料完整性中等和补充履约材料不足，采购金额较高，适合演示补充材料和人工复核。

high：Northbridge Electronics Trading LLC 为境外紧急高额采购供应商，官网缺失、信息不透明，并存在疑似制裁名单/黑名单接近性、多条付款和交付争议，适合演示拒绝或升级审批。

## 5. 项目价值

SupplyGuard Agent 的核心价值不是替代合规人员，而是把供应商准入变成可重复、可追溯、可解释的工作流。规则引擎输出 `raw_score`、`total_score` 和 `hit_rules`，让后续 Agent、API 和前端都能解释风险结论。
