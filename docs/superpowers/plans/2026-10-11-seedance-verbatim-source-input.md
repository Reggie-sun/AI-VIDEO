# Seedance Verbatim Source Input Plan

## Goal

完成用户当前“再复刻用fast 2.0”：原画布原文、单张原参考图、15秒、480p，最多一次新物理提交。
修复已经复现的原文入口阻断，不以新增 Director 决策补齐输入。

## Scope And Contracts

`SeedanceNativePromptBinding` 独占原文输入声明；`SeedanceVideoProvider.compile_request` 仍为唯一 Seedance compiler owner。
新增显式 `source_preservation` 声明，仅接受与 canonical approved Shot.intent 完全相同的 prompt；
原文 SHA 必须同时匹配 prompt 与 source evidence。不可把附加说明、删改原文或旧扩写 prompt 当作原文。
沿现有非 v4 ProviderNeutralVideoRequirement 可表达的来源信息与 recipe 编译（Planner 仍为 `/3`）；
不伪造 camera-complete requirement `/4` 所需的运镜、灯光、表演字段。
完整 v4、新创作与既有 custom authored prompt 路径保持原有规则。
原文入口仍执行同一个 `compile_provider_video_request`、recipe lexical coverage、target/profile/reference/output checks、
GenerationDecisionExecutionBinding、Budget Guard、egress、durable intent、一次 permit、unknown fail-closed 和媒体 Gate。
输出时长 controls 只在 intent 与已绑定 output 一致时声明；可见状态变更须有原文内的目标文字。
不接受 typed-hash continuity、独立 VO 或用原文声明覆盖不能忠实表达的 controls。

## Files And Ownership

- `src/ai_video/production/seedance_native_prompt.py`：显式原文声明及 canonical Shot/text/hash/control 核验。
- `src/ai_video/production/seedance.py`：选择原文编译或现有丰富意图语法，不增加 transport/lifecycle。
- `tests/test_seedance_source_prompt.py`：同一 compiler 的正向与错文本/身份/省略已批准动作/新创作回归验证。
- `.agent/harness/policy.yaml`：把新测试纳入既有 Seedance check，不削减任何检查。
- `docs/agent-primary-contract-matrix.md`：同步原文入口 owner 与证明边界。
- 新 session record：实际调用计数、结果、媒体评估及未验证边界。

## Out Of Scope

不改旧 run、旧扩写、失败记录、已暂停的 paid-retarget dirty files、Provider/model/凭据来源，
不重置历史三次物理提交，不自动重试，不承诺 Jimeng UI 与 Ark API 的像素级一致。

## Acceptance And Verification

1. 原文入口通过真实 Seedance compiler 和 canonical execution binding，实际 request.prompt_text 与原画布 UTF-8 bytes 相同。
2. 未声明原文保留时，不完整意图继续拒绝；删改、增补、错 Shot/hash、隐藏未表达意图或 continuity 不得通过。
3. 现有完整意图与 native prompt binding tests 保持 PASS，exact staged Harness 验证，Parent Risk Gate 裁决。
4. 原 PNG Registry identity/bytes 与 reference role 保持；Fast2.0、480p、15s、原生音频 exact preview 后仅一次 POST。
5. 新 MP4 落盘后显式 project-local video-analysis，逐项 PASS/FAIL/NOT_EVALUATED；正常速度视听验收独立保留。

## Self-Review

已有离线复现：来源不扩写即可导入，但丰富语法强制缺失的表演/灯光/运镜等字段，`execution_binding_available=false`。
本修复为这次原文复刻的必要入口，保留原文、canonical approval 与全部生成门禁；它不降低 v4 完整意图契约，
不产生新的 source、QA 或 lifecycle owner。模型效果只由实际新片裁决。
