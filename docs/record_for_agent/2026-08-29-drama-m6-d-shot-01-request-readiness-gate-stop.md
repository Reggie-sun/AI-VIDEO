---
record_kind: architecture_implementation
topic_id: drama-m6-d-shot-01-request-readiness
learning_eligibility: ineligible
---

# Drama M6-D Shot 01 Request Readiness Gate Stop Record

Date: 2026-08-29

## Purpose

本文固定 canonical M6-D Shot 01 从 accepted Drama package 到 H3 native prompt 之间的当前 executable boundary。结论是 `STOP_BEFORE_SUBMIT`：canonical source binding 正确，但 executable `GenerationIntent` 尚不完整，current H3 compiler 对 exact requirement 返回 typed `H3PromptUnsupported`。

本文不修改 accepted fixture、baseline、Project、Registry、Manifest、historical request 或媒体 evidence，也不授权手写 prompt、默认值补全、Provider submit、retry、`video-analysis`、candidate activation、P6 或 Final Acceptance。

## Exact Canonical Identity

- canonical run root：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/`。
- materialization evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-canonical-materialization.json`，SHA-256 `75be2e494e44b5b253d730f9c9daca366806e09209c7e5e5e231c014a1b09f71`。
- planning request hash：`92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f`。
- target Shot：`drama.shot.waiting-room.001@1`，content hash `4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b`。
- requirement hash：`d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81`。
- active pre-generation graph：`761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1`。

Independent xhigh re-review 对 accepted fixture Shot 01 的 14 个核心 source fields 逐项比较为 exact match，包括 visible key presentation、exact dialogue、blocking、performance、emotion、prop close 与 camera intent。Canonical Shot identity 与 authoring lineage 没有 drift。

## Current Executable Stop

Strict reopen exact canonical requirement 后，`compile_h3_prompt()` 返回：

- outcome：`unsupported`；
- `prompt_text=null`；
- no native prompt bytes or SHA；
- no persisted `VideoGenerationRequest`；
- no Provider selection、permit、submit、poll、fetch 或 media effect。

Exact unsupported paths：

1. `generation_intent.subject_action.endpoint`
2. `generation_intent.space_continuity.screen_direction`
3. `generation_intent.axis_continuity.camera_axis`
4. `generation_intent.axis_continuity.framing_continuity`
5. `generation_intent.performance_intent`
6. `generation_intent.visual_treatment`
7. `generation_intent.lighting_intent`
8. `generation_intent.ambience_intent`
9. `generation_intent.dialogue_intent`
10. `generation_intent.music_intent`
11. `generation_intent.camera_endpoint.start_framing`
12. `generation_intent.camera_endpoint.end_framing`
13. `generation_intent.pacing.shot_duration_seconds`

这些 diagnostics 不是可机械照填的完整 checklist。Current sparse intent 还保留 `unspecified` camera、motion、pacing、space/axis values；仅让上述 13 项消失仍可能产生不满足 visible/audible H3 grammar 的 prompt。

## Compiler Guardrail Repair

Legacy `/1` T2VA compiler 不再直接投影 `target_shot.intent`。Production Project 中的 `Shot.intent` 可以合法保存 canonical structured authoring JSON，但 Provider-native prompt 只能消费已验证的 typed current-Shot execution fields。此 guardrail 防止未来完整 intent 在 compile 时重新泄漏 `dramatic_function`、`next_shot_obligation` 或 raw JSON；它不补造 canonical M6-D 当前缺失的 execution facts，也不把 unsupported requirement升级为 ready。

Historical 6-Shot Development preview `runs/drama-h3-t8-30s-preview-20260829-v1/` 是不同 Shot identity、不同 requirement 与不同 empirical attempt。其 exact Shot 1 Gate `FAIL` 保持有效，但不得借给 canonical M6-D；同样不得把 preview request 借来绕过本 stop。

## Verification And Review

- strict reopen canonical materialization与 exact requirement：PASS。
- canonical compile outcome：稳定复现 exact 13-path `H3PromptUnsupported`。
- regression：structured `target_shot.intent` 不进入 legacy H3 prompt；三字段 grammar 与 raw-JSON exclusion保持。
- focused H3/requirement/provider adapter suite：`86 passed`。
- broader H3/T8/planner/video suite：`325 passed`。
- native `reviewer_xhigh` revised verdict：`reject` pre-submit readiness；canonical source binding正确，executable intent不完整。

## Remaining Repair Boundary

继续 M6-D 前需要 separately sealed authoring-to-request repair。它可以保持 fixture/baseline bytes 不变，但必须由 canonical owner明确新增当前缺失的 execution-intent facts，并生成新的 projection/request/requirement hashes。

已 sealed facts能够支持部分机械 projection，例如 Shot 内钥匙展示与 close prop state、left/right axis、no-crossing、locked framing、steady rain、no music、5.0s target与 exact dialogue。Current accepted truth不能完整决定 visual treatment、lighting、supported dialogue language、dialogue timing/lip-sync policy、motion amplitude及cadence/tempo；Project、Story与Characters language仍为 `und`，不得根据中文字形猜 `zh-CN`，baseline也不是 prompt fact owner。

在新的 exact requirement 通过完整 typed validation、native compile、three-field visible/audible audit、profile/runtime identity preflight 与 canonical lifecycle readiness前：

- `M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`；
- `next_shot_submit_allowed=false`；
- 不得手写 prompt、使用默认值、fallback、修补历史 requirement或复用 preview request；
- 不得调用 Provider、ComfyUI或`video-analysis`。
