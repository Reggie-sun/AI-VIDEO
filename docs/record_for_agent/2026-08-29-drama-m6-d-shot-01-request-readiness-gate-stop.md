---
record_kind: architecture_implementation
topic_id: drama-m6-d-shot-01-request-readiness
learning_eligibility: ineligible
---

# Drama M6-D Shot 01 Request Readiness Gate Stop Record

Date: 2026-08-29

## Supersession Notice — 2026-08-29

本文原始`CANONICAL_SHOT_01_EXECUTION_INTENT_INCOMPLETE` stop及13-path diagnostics保留为commit
`71fc4e7ddc3174150283088030b3039fe32d963c`时的historical executable truth。新的versioned execution-intent overlay
已在不修改accepted semantic bytes或旧request/requirement evidence的前提下accepted/sealed，并经current canonical
Planner/requirement seam生成完整typed requirement与exact three-line H3 prompt。

Current state仍是`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`；被替换的只是pre-media authoring blocker。新的remaining
blocker为`PROVIDER_PROFILE_RUNTIME_IDENTITY_AND_EXACT_REQUEST_NOT_SELECTED`，本记录不授权submit或进入per-Shot media Gate。

## Purpose

本文固定 canonical M6-D Shot 01 从 accepted Drama package 到 H3 native prompt 之间的 executable boundary。原始checkpoint因`GenerationIntent`不完整而`STOP_BEFORE_SUBMIT`；本轮只解除该authoring blocker，并把current stop推进到Provider/profile/runtime identity与exact request selection之前。

本文不修改 accepted fixture、baseline、Project、Registry、Manifest、historical request 或媒体 evidence，也不授权手写 prompt、默认值补全、Provider submit、retry、`video-analysis`、candidate activation、P6 或 Final Acceptance。

## Exact Canonical Identity

- canonical run root：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/`。
- materialization evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-canonical-materialization.json`，SHA-256 `75be2e494e44b5b253d730f9c9daca366806e09209c7e5e5e231c014a1b09f71`。
- planning request hash：`92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f`。
- target Shot：`drama.shot.waiting-room.001@1`，content hash `4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b`。
- requirement hash：`d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81`。
- active pre-generation graph：`761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1`。

Independent xhigh re-review 对 accepted fixture Shot 01 的 14 个核心 source fields 逐项比较为 exact match，包括 visible key presentation、exact dialogue、blocking、performance、emotion、prop close 与 camera intent。Canonical Shot identity 与 authoring lineage 没有 drift。

## Historical Executable Stop

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

## Historical Remaining Repair Boundary (Resolved)

以下内容解释为什么`71fc4e7` checkpoint必须停止，以及本轮overlay必须显式拥有哪些facts；它不再是current blocker。

继续 M6-D 前需要 separately sealed authoring-to-request repair。它可以保持 fixture/baseline bytes 不变，但必须由 canonical owner明确新增当前缺失的 execution-intent facts，并生成新的 projection/request/requirement hashes。

已 sealed facts能够支持部分机械 projection，例如 Shot 内钥匙展示与 close prop state、left/right axis、no-crossing、locked framing、steady rain、no music、5.0s target与 exact dialogue。Current accepted truth不能完整决定 visual treatment、lighting、supported dialogue language、dialogue timing/lip-sync policy、motion amplitude及cadence/tempo；Project、Story与Characters language仍为 `und`，不得根据中文字形猜 `zh-CN`，baseline也不是 prompt fact owner。

在新的 exact requirement 通过完整 typed validation、native compile、three-field visible/audible audit、profile/runtime identity preflight 与 canonical lifecycle readiness前：

- `M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`；
- `next_shot_submit_allowed=false`；
- 不得手写 prompt、使用默认值、fallback、修补历史 requirement或复用 preview request；
- 不得调用 Provider、ComfyUI或`video-analysis`。

## Accepted Authoring-To-Request Repair

Accepted overlay：

- payload：`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v1.proposed.json`；
- payload commit：`68863c9a34c0b7d20063d80dce07bc311aba3846`；
- payload SHA-256：`4d8fa775ba9cf51d0b0d82637cc13c0f689657559b0f08447c2f6e9a868ac0db`；
- acceptance envelope：`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v1.accepted.json`；
- acceptance envelope SHA-256：`8b50b61b152b59542fc4521c870cc060b9b6469fc18db5e3a14248cf05de7efd`。

Overlay显式而非推断地拥有action endpoint/prop close、space/axis/no-crossing/locked framing、visible
performance/gaze/body/hand、visual treatment、lighting、steady-rain/no-music、exact dialogue、`zh-Hans`、
`1.700s–3.900s` timing、on-screen lip sync、camera endpoint、motion direction/amplitude、cadence/tempo与`5.0s` target。
`zh-Hans`由overlay直接author，不是从中文字形猜测locale；accepted fixture、baseline、Story、Scene、Character与Shot
semantic bytes均未改变。

Canonical accepted evidence：

- path：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-authoring-to-request-accepted-v1.json`；
- SHA-256：`1e38b731b31b4866720d5b80bfb2dd40da04ebe56dea8656f3d7219d15298cb6`；
- new request hash：`01c329aa22b898521d0611bd4fbcfcbba912babb81b4ce85a88582985704fe7c`；
- generation-intent projection hash：`9c1b1c633bef7cf9d2c26343e3f5dc84b0399269ecc4770cc879b6806fead419`；
- plan hash：`50af2a2b5df126ded8958f7d09d587a90c108a34567c15d093a9f649e88e8e24`；
- verified projection hash：`f2292b67f3616a5b4757c6c3e45301b971230bb59a3b683207d8a6d6cb412b1d`；
- new requirement hash：`d234cd95b712ca8d966132d28c6ee15a49831b412305b795c8c8eb9a2491b34d`；
- prompt SHA-256：`3676c9998a63e7ddc024faff7d18f07f5e48722046ee7193201f490ee57c750d`。

Strict request、requirement与verified projection reopen全部PASS。`compile_h3_prompt()`生成exactly three lines；exact
dialogue只出现一次，`<d>[Chinese]`与`non_diegetic_music: none`均为executable assertions。Audit确认无raw JSON、
Story/Scene/future bookkeeping、opaque canonical identity ID、abstract objective或`unspecified`。

Historical candidate evidence SHA-256 `747ec812a35eff69dc2cc20580c562cfe87165094d43127aa21712facb6d3977`与
accepted candidate-v2 SHA-256 `8d3256ab3d081820e67f727e8842fffe474a1f606ef074fa5ea09759118d13f2`在accepted rerun前后不变；
accepted-v1使用独立immutable path。Project tree before/after均为15 files，写入计数、Provider submit、媒体生成、
`video-analysis`、Manifest/Registry mutation与candidate activation全部为0。

## Current Verification And Stop

- focused Planner/requirement/H3 suite：`230 passed`；
- native `reviewer_xhigh` scoped re-review：`accept`，无blocking或non-blocking concern；
- detached exact-range Harness：`.agent/harness/runs/drama-m6-d-shot01-execution-intent-driver-v2-detached-20260829/receipt.json`；
- receipt SHA-256：`b9fff5a11907769bbc3c36fe16cf9136f65593675df60ec0f395e77cd01e2379`；
- Architecture Gate：PASS；full suite：`4206 passed, 4 skipped`；receipt status：`passed`。

该receipt在detached checkpoint上fresh且workspace stable；主checkout随后推进，因此current generic freshness不被写成true，
但immutable receipt与artifact integrity已重验。Current boundary为：

- `M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`；
- `next_shot_submit_allowed=false`；
- remaining blocker：`PROVIDER_PROFILE_RUNTIME_IDENTITY_AND_EXACT_REQUEST_NOT_SELECTED`；
- 未选择Provider/profile/workflow/runtime identity，未persist或submit request，未进入per-Shot media Gate；
- 未产生M6-D PASS、P6、Final Acceptance或Commercial verdict inheritance。
