---
record_kind: session_summary
topic_id: jieshi-s01-repair-profile-expired
learning_eligibility: ineligible
---

# S01 Repair Preflight Block

## Result

用户“实践”授权新的有界 S01 实验。已核对原始首帧、先前 I2V Gate 和现有执行脚本，新增 `runs/jieshi-e01-i2v-20260906-attempt02/request-draft.json`；最多一次提交，本轮实际零提交。草案不是 compiled request、Registry receipt、intent 或 permit。

## Evidence

先前真实首帧输入已成功，但 0.898 秒出现对应手影，见 [原逐镜记录](2026-09-06-jieshi-s01-vidu-i2v-live-gate.md)。不能把本次实验描述为首次补入 reference。当前查看 PNG 中七人和空座可见，完整工牌身份仍未闭合。

现有 profile 位于 `runs/jieshi-e01-i2v-20260906-attempt01/preparation-v7/provider-profile.json`，有效期截至 `2026-09-05T19:39:26.420637Z`。本轮在真实 `ViduVideoProvider.preview` 上离线重现 `paid_provider_budget_rejected: Vidu pricing ceiling is not current.`，transport=None，credential supplier 禁止读取。没有调用 Provider、改写时间或查询价格。

## Next Action

由 operator 提供有效且 sealed 的兼容 profile 后，将新草案通过既有 Planner/readiness、Router、compiler 和 Provider 流程重新封装，再创建本次独立 intent/permit。旧授权与 permit 不复用。先前失败媒体不作为已接受连续性状态，S02 继续阻断。

## Verification And Learning

已验证离线 preview 的真实错误、草案 JSON 与 exact-path whitespace；未执行新媒体 Gate，因为没有新 MP4。记录/自动学习评估 `no_candidate`：没有新增媒体实验，不构成独立支持。保留其他 staged runs 和 H3 dirty changes，无 push；没有另行刷新 RAG index。
