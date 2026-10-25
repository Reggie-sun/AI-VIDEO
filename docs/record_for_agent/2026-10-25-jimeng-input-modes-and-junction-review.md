---
record_kind: architecture_implementation
topic_id: jimeng-input-modes-and-junction-review
learning_eligibility: ineligible
---

# Jimeng Input Modes And Junction Review

Date: 2026-10-25 (Asia/Hong_Kong)

## Purpose

用户要求先修首尾帧逻辑，再让即梦支持各类 Shot / image、video 及白模参考，并防止首尾帧生成后直接拼接造成动作、对白或笑声重叠。本轮修复共享输入编译和开发审片入口；作品剪辑证据归[颜生源记录](2026-10-25-yanshengyuan-seedance20-two-shot.md)。

## Current Runtime Truth

四个 Jimeng exact model 的 `text_to_video` / `first_frame` / `first_last_frame` / `multimodal` 分别编译为 native mode 1/2/3/4；端点角色与普通 image/audio/video reference 显式分离。旧默认 multimodal 字节身份保留，无隐式换模型或模式。真实平台只读 config/validator 覆盖四模型×四模式，16项有效，零上传和生成；sanitized fixtures 位于 `tests/fixtures/generated_video/jimeng-native-*-20261025.json`。四模型仍为 `UNQUALIFIED`，不是质量或 Production qualification 结论。

`jimeng_prompt.compile_jimeng_native_prompt` 是初次编译与 causal-state 重编译共用的 native 文法 owner；修复 marker 文本与纯 prose 被误比较的冲突。使用 exact model UTF-16 上限，包括 marker；不再受其他 remote Provider 的5000字符默认值误限。初次编译复用 adapter `resolve` 校验完整素材数量、时长和几何约束，避免 Router 编译成功而执行必拒绝。已封存 ReferenceDuty 的身份/布局/动作/摄影职责按实际 asset/index 写入 native 文本，不把上传文件等同于表达职责。

共享 `_causal_state_expression.native_recipe_expression_view` 只在临时 prose 视图排除已由 native grammar 表达、且与当前 endpoint 完全相同的 state seal；原 recipe/hash 不变，普通泄露 hash guard 保留。C4 强多锚点、硬端点与动作视频同时约束、独立 edit/extend、typed voice routing、preserved-source 文法仍为明确 unsupported；不以删 guard 声称所有控制可组合。

`scripts.visual_quality_report prepare` 的新完整 `/4` packet 必须绑定 canonical `ResolvedTimeline`、本次 HyperFrames render report 和 exact MP4，自动封存所有实际切镜，包括无显式 transition 的 cut；没有另建 timeline。逐刀记录实际入出点、保留理由或待 trim、视觉和声音的独立 verdict。`trim` 表示仍需剪辑，不能取得 PASS。缺记录、hash 漂移、未实际听声音或不合格全片1倍速证据均阻断 PASS；ExplicitEvaluator 不能假装 HUMAN。明确 audio FAIL 不因听音资格不足被降为 NOT_EVALUATED。旧 `/1` 兼容原范围，旧完整 `/2`、`/3` 不证明新接缝检查完成，最高保留 NOT_EVALUATED。

约束已纳入现有 `open-video` creative-completion reference、canonical visual-quality 文档和 Harness 模块/测试映射；不是仅增加一条提醒。该开发工具不拦截任意 shell 或聊天交付，不代签 Production/P6/Final Acceptance，也不强迫所有首尾帧镜头必须裁掉内容。

## Verification And Evidence

证据前缀：`runs/yanshengyuan-blockbuster-seedance20-20261025-001/continuation/edit-repair-003/engineering-proof/`。`evidence-index.json` 保存原日志/快照 hash。

- 修复前真实 requirement→Router→compiler→resolve 的失败已复现，修复后所有新模式与 causal 专项59项通过（1.32s），包括四模型纯文字完整链、实际标准 state-seal recipe、ReferenceDuty、限额与端点基数边界。
- 第二轮相关回归286项通过（232.97s），含 typed/current closing expression、generation decision/input control、visual quality、review report 和 junction Gate。前一轮458项及 legacy service96项通过的日志单独保留，计数有交集，不相加冒充独立覆盖。
- policy/skill相关43项通过；`test_open_video_skill.py` 48项通过；policy-audit diagnostics为空，新增模块路径不再 fallback/unfocused；docs gate 与 owned `git diff --check` 通过。
- `/root/jimeng_junction_review` / `reviewer_xhigh` 两轮工程审查。YM-ENG-001（state seal 被重新追加到正文）、YM-ENG-002（audio FAIL 被降级）均由 Parent CONFIRMED、补回归修复，再作 targeted re-review。最终20文件快照 SHA `44eff1718311240701b2e68c304ed028849ac8d277db25a0bd01cfe6b40059ec` 前后 hash 一致，工程 finding set为空；见 `reviewer-round2-parent-adjudication.json`。这不是媒体实际审听结论。
- 38秒作品已实际用 `/4` packet 生成四刀清单7.5/14/22/32秒，HTML经真实浏览器查看。实际听音与 HUMAN整体审片不足，结果明确 NOT_EVALUATED；不会用 ASR、PCM相关性或播放器 ended 冒充听过。

## Publication And Ownership

此记录落笔时本轮实现尚未提交，完整 frozen Harness 尚未运行；上述是 working-tree focused/related 证据，不是完整 Harness PASS。另一窗口已将 Harness分级本地提交为 `5daa3d6`、`136038a`，并交回空 index；其完整回归11项失败均在旧 `2d17c49` 重现，完整发布仍 BLOCKED，见[该窗口记录](2026-10-25-harness-three-level-verification.md)。不借局部通过 push main，也不修复或掩盖其非本轮失败。

用户已授权保留并补修 `video_compiler.py`、保留并补 `policy.yaml` 映射。其他窗口 NativeTextExpressionReport overlay、Seedance映射及全部无关 dirty 内容保留，不属于本轮提交范围。全局 architecture gate 的其他窗口 StateCommit owner 超限错误未解决；本轮 compiler 未新增独立职责 owner。

## Assessment

稳定工程 checkpoint 已达成；新三支40–60秒广告获明确生成授权，后续按逐镜 Gate继续，不能把这份工程记录当媒体 GO。此次未新增即梦视频生成或重试旧 audio UNKNOWN；只读16项能力校验、已有片本地重剪与工程测试各有独立证明边界。

`record-ai-video-session` 后自动评估 `distill-ai-video-learning`：`no_candidate`。本轮是确定性缺陷复现/修复及同一素材链的多种证明，没有可归因的独立媒体质量对照；不创建学习占位项，不修改全局 memory，不作通用模型质量归纳。
