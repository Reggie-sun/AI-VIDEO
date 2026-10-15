# METASO Preserved Source And Recovery

## Goal

按用户最新明确要求，用现有 METASO MiniMax-H3 API 执行原《界蚀》S01→S02，不再使用 Seedance 或搜索接口替代视频执行。修复仅覆盖必要共享缺口。

## Contracts

- 原文、对白、动作、身份、倒影、空间、摄影及既有 QA/final goal 不删改。exact first-frame PNG 不变。
- Source preservation 复用现有 sealed source parts、引用 identity、endpoint grounding、重编校验；METASO 使用自己的 compiler/grammar identity，不冒称 Seedance。
- 已知无副作用的失败仅在新显式、一次、exact target scope 的跨 Provider 授权下恢复；同 task/Shot、旧 receipt/消费/unknown 均保留。旧同 Provider 恢复语义及序列化兼容不变。
- H3 请求4秒、768P（该 Provider 无480p）、adaptive、24fps、native audio；canonical S01采用3秒，S02采用4秒。输出 timing 只允许已声明 Provider 技术差异，禁止降低叙事/声音质量。
- Canonical authoring/Planner 会随上述几何适配更新 Shot revision/hash/provenance、三个请求/intent identity hash，以及首帧的 Shot owner hash；只允许这些身份随对应旧/新 Shot 更新，所有原文、intent 语义、asset ID/SHA、role 和其他 owner 保持不变。两端 typed requirement 与 candidate scope 仍必须 exact 绑定。
- 现有 `source_fidelity` 输出规则含原生 `480p` 字样；显式选择 H3 后只允许将该原生分辨率 token 改为 `768P`，创建新 sealed QA/goal identity并保存逐字 diff。跨 Provider grant 必须绑定两端实际 output label，其他原文、规则 ID、proof/tolerance、时长、帧率、声音及全部剧情要求不变；不能用此许可任意改 rubric。
- 不新增故事执行脚本、状态库、timeline 或 renderer；使用 Canvas/GenerationFeedback/ProductionStateCommitter/VideoGenerationService。
- 新单元至多一次 S01 提交；后镜仅在前镜全部 required findings PASS 与实际状态绑定后执行。任何 UNKNOWN 停止，不重试。

## Verification

真实 source-preserved H3 编译及篡改拒绝；旧 Seedance source 回归；未显式跨 Provider grant 的拒绝；exact grant/closed no-effect/one-use 的正向与负向测试；完整适用 Harness、Risk Gate。工程通过后才做当前 runtime/credential/budget/egress/intent/permit 核验和真实逐镜 QA。

## Self Review

任务内必要适配已由用户授权；未扩大人物创作、外部订阅或自动重抽范围。工程证据与媒体/人工验收分开。
