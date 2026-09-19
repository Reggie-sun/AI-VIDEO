---
record_kind: session_summary
topic_id: jieshi-s03-first-frame-preparation
learning_eligibility: ineligible
---

# S03 First-Frame Preparation

Date: 2026-09-11

## Current State

用户在保留 S02 attempt04 后选择“继续 S03（推荐）”，随后以“确认”回答已提出的 S02 scoped human review 与 S03 首帧选择，再以“可以”批准最小 import 兼容修复。修复后已创建真实 S03 Production root、如实导入首帧，并完成一次 S03 视频生成与下载。用户随后对 exact S03 MP4 完成正常速度人审并回答“通过”；raw visual Gate 现为 PASS、holistic verdict 为 KEEP。S02 Manifest 保持 revision 46 和原 hash；S03 Manifest 仍未改写或激活，P4 最终音频仍为 NOT_EVALUATED。

工作目录：`runs/jieshi-e01-i2v-20260907-attempt10/preparation-s03-v1/`。

- 来源 S02 exact MP4：`ca76302f937a8a1c683f165e0cdb8561fddbfdbee1689bacb46f190e6e0e5eab`。仅提取 frame 96、t=4.0s 作为反打场景和道具参考。
- 实际调用 `image_gen` 一次；不是 automated-browser image tool，不声称具体 backend model。
- 候选 `s03-first-frame-candidate-v1.png`：SHA-256 `2bf11b952cbaca5047f8faff56ae480cdc74c5504f601e0166c425803b285b20`，2,012,175 bytes，941×1672。原始工具 PNG 保留；workspace 保存 exact copy。
- 陈立为灰色卫衣、短发、耳机、右手持深蓝手机、朝屏幕左的反打构图。手机背部摄像头细节与玻璃反射身份仍需核对，不声明 continuity PASS。
- `director-coverage.json` 已通过既有 validator。完整实际 image prompt 独立保存在 `image-generation-prompt.txt`；本记录不复制 prompt。

## Gate Applicability Correction

本轮初始调查把 typed human presentation 的限制误当成 S03 的普遍阻断条件，已在用户更新及 `first-frame-result.json` 中纠正。

`_state_commit_video.py::_require_production_predecessors()` 对 `production_lineage=None` 返回；当前 S02 是 standalone Shot。实际适用 `.agent/context/control-plane-playbook.md` 的 Agent-controlled Per-Shot Gate，并可复用既有 S01→S02 的 exact-bound gate + scoped human confirmation 方式。不得为了接续伪造 typed `/2` human proof，也不需要新增 host 协议或修改架构。

此前仅有用户“没问题”的 checkpoint 不冒充逐项 playback evidence。后续“确认”已保存为 `s02-s03-scoped-human-confirmation.json`，包含实际问题范围与 exact MP4/PNG hashes。新建 `s02-prospective-next-shot-gate.json`：9 项 raw-generation PASS，2 项 final-composition NOT_EVALUATED/deferred；原 NE gate、QA、verdict 和 Manifest history 不变。判断来自 scoped 用户正常速度审片报告与 project-local MCP 原始采样证据，不是 assistant 连续播放或 typed `/2` human proof。已声明的 P4 最终对白及环境声不属于 raw next-Shot barrier；最终音频仍需以后实际验证。

## Confirmed Import Blocker

本节为已解决的历史阻断；当前实现与验证见下一节。原复现文件保持原结果，不改写为 PASS。

`s03-import-admission-reproduction.json` 记录当前 Pydantic references union 的实际验证：正确来源 `HumanImageImportReceipt(source_surface=codex_imagegen_tool)` 拒绝实际 `VideoFrameImageImportReferenceBinding`；browser receipt 可接受 frame，但会错误声明工具来源。没有提交 Provider，也没有用空 references 绕过。

native `reviewer_xhigh` 对“空 references + source/license note”候选方案判 `reject`：普通 note 不建立 bootstrap/reader 的 typed source closure；不能省略已知实际输入。Parent 已独立复现 union rejection 并检查对应 closure。当时尚未获准修复；后续用户“可以”批准了现有 import 路径的最小扩展，不改变 QA、Provider、quota 或 Director 架构。

## Authorized Compatibility Fix

修改 `image_import.py` 的 Human/Codex reference union 与既有 commit 参数传递，并在 `_state_commit_bootstrap.py` 为 Codex receipt 补全首次写入前解码帧校验。只允许真实 `codex_imagegen_tool` 来源使用这条新增 Human video-frame 路径，旧 web/browser identities 和旧 hash 保留。公共用法见 [Codex Imagegen Video-Frame Import](../codex-imagegen-video-frame-import.md)。

新增 bootstrap 负例曾真实出现 `1 failed, 34 passed`：错误帧号被 Codex 首次 bootstrap 放过。补齐原 owner 的 receipt dispatch 后，focused suite 为 `35 passed`；没有靠空 references 或普通 note 绕过。

真实 S03 root 为 `production-s03-v1`，bootstrap/graph/QA exact reopen 成功。Import receipt 为 `2c8e83d15c8f98b4bac11fef59b734dd8e6d503cd93920af1d23bfa9c59046da`，QA 为 `b51aab39249d219a9686fb02c126944c2c4ff38f3d31705040934d65821312c9`；首帧 PNG hash 不变。原始 prompt fingerprint 去掉保存文件时额外添加的换行；approval timestamp 来自已保存的真实 scoped 确认。

真实 Planner/Router 判 `GENERATE_ONCE`，无 baseline/history 继承、无 intervention；Vidu Q3 Pro、4 秒、1080p、单一 approved first frame、native audio=false，task ceiling=1/used=0。Binding `4673e2d434079d34ed0c47b04a13a4a1129f393d016ab8da41f725bbb2dba7db`，resolved request `f47272f0674991df6e74e87db5318f71b25b44c8b32509d5d0a407d495592519`。此前临时 root 结果只作离线验证，不冒充真实提交。

正式 Harness 针对 HEAD + 三个 task-owned files 的独立 snapshot 实际运行，未触碰主 index；结果 `failed`，仅因原有 policy audit 未映射 `image_import_video_frame.py`、`paid_provider_no_effect_reconciliation.py` 和对应 test。证据在 `preparation-s03-v1/harness-snapshot-result/receipt.json`。不声称 fresh passing Harness。Task-delta Architecture Gate 实际 `PASS`，伴随已有 oversized image_import 模块增长 WARN；本次保持原 import owner，未新增架构。其余 mandatory image/state/skill suites 在同一独立 snapshot 合并去重后实际 `1317 passed`，日志为 `import-policy-tests.log`，源 hashes 和限制为 `s03-import-verification.json`。独立 `reviewer_xhigh` 对冻结修复及 actual binding/preview 判 `accept with concerns`，明确不豁免正式 Harness 限制或媒体验收。

## S03 Actual Video Result

唯一一次 POST 于 2026-09-11 12:51:50 UTC 被接受；后续仅 GET poll/fetch。无追加样本、无 S04 submit。旧过程使用过的 public DNS GET-only fetch seam 仅解析既有下载 hostname，保留 TLS 和 public-address validation，未改全局网络或生成请求。

- Exact MP4：`production-s03-v1/state/video-generation/fetch/files/d35624979e6dc6902c2e527bf5a99bcc47108de083f8e069de687e337c1a9268.mp4`。
- SHA-256：`d35624979e6dc6902c2e527bf5a99bcc47108de083f8e069de687e337c1a9268`；7,230,552 bytes；H.264、1080×1920、24fps、97 帧、4.042s、无 audio stream。
- MCP 已实际调用 `video_probe`、`video_review`、`video_extract_frames`。Parent 查看全部 9 个半秒样本及 1.75/2.25/2.75/3.75s 加密样本；不声称 continuous 1.0x playback。
- 采样可见陈立左手接触左耳、朝屏幕左回应/微笑并回看手机；2.25s 左耳处未见原先黑色耳机，末段缺乏已戴回的明确证据。该疑点当时留待人审，现已由下节的人审 checkpoint 解决；不以起手时间、精确笑容或零 camera motion preference 判 QUALITY_FAILURE。
- `s03-attempt01-post-media-gate.json` 逐项绑定 canonical QA 的 observable/tolerance/measurement/stage/proof；8 项 required 均保持 `NOT_EVALUATED`，holistic `UNDECIDED`，不继承 S02 human PASS。2 项 P4 final audio 仍待后期。
- `s03-attempt01-final-state-check.json`：S03 Manifest revision 11，SHA `c340d0a5ca174835a13f4dfc511f11fa725ee797a36ea11cc368e1203f274b27`；attempt 为 running/validate，paid accepted，final_visual 尚未激活，next_shot_allowed=false。S02 Manifest SHA 仍为 `11571f3994dfb7323bbe977f6ef52b1fd10db64de95e9a3cd3aa29686534d624`。

## Human Acceptance Supersession

用户在收到上述 exact MP4 及“请正常速度重点看左耳机是否明确戴回、整体动作是否自然”的明确审片问题后回答“通过”。`s03-attempt01-human-confirmation.json` 仅把这次人审绑定到 SHA-256 `d35624979e6dc6902c2e527bf5a99bcc47108de083f8e069de687e337c1a9268`，不声称 assistant 完成连续播放，也不冒充 typed `/2` human source、P6 或 Final Acceptance。

`s03-attempt01-human-next-shot-gate.json` 原样复用 canonical S03 QA 的 criterion：6 项 `raw_generation` hard requirements 为 PASS，2 项 `final_composition` P4 音频 requirements 继续为 NOT_EVALUATED 且不作为 raw next-Shot barrier。Holistic verdict 为 KEEP。此前 `s03-attempt01-post-media-gate.json` 的 NOT_EVALUATED / UNDECIDED 是人审前历史 checkpoint，exact bytes 与 SHA-256 `68928251e785e68bae5e9176920e6539e26892ab72918539bd15f6758166187d` 均未改写。

`s03-attempt01-human-checkpoint-state.json` 明确记录这次 supersession 只产生 technical next-Shot eligibility：没有改写 Manifest、没有激活 candidate、没有生成 S04，也不把本次“通过”解释成 S04 submit authorization。

## Verification

- 候选 PNG SHA 在 workspace 重新核对一致。
- Director coverage validator：PASS。
- `tests/test_generation_execution_guards.py`：14 passed；这是工程检查，不是媒体 acceptance。
- Assistant 仍未声称自己完成连续 1.0x playback；全片 raw visual PASS 来自用户对 exact MP4 的正常速度人审报告。
- 当前 checkpoint 仅新增 preparation artifacts 与本记录；未 stage、commit、push，其他 working-tree changes 保留。
- 后续确认轮追加 `orchestration/s03_common.py` 和 `s03-authoring-check.json`，仅为既有模型下的 S03 authoring 准备。Planner focused tests：135 passed；source strict reopen：PASS（revision 46），但 S03 integrated planning 明确 `NOT_RUN`，没有 QA activation 或 executable Provider request。Parent 检查并要求修正了 B02-SC01 重复 beat 的草稿问题，现在保留 S02 并向同一 beat 追加 S03。不能把这些准备检查称为完整 Production readiness。

## Next Boundary

S03 attempt01 的 raw visual 人审已通过，应保留 exact MP4，不需要为左耳机终态或整体动作继续重生。P4 最终对白与环境声仍需在最终合成阶段制作并验证。S03 Manifest 尚未激活；本 checkpoint 没有推进或生成 S04，也不授权 S04 submit。代码与记录保持 local uncommitted，未 stage、commit、push；主 index 与其他 dirty work 保留。

自动 learning evaluation：`no_candidate`。一次 S03 exact attempt 的人审通过没有两个独立 attempts 或受控多臂对照，不产生可推广的 Provider 或生成质量结论。
