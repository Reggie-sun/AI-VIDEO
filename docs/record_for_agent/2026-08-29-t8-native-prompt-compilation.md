---
record_kind: architecture_implementation
topic_id: t8-native-prompt-compilation
learning_eligibility: ineligible
---

# T8 Native Prompt Compilation Record

Date: 2026-08-29

## Purpose

本文记录 Local T8 Quality v1 与 hybrid Turbo v1 从 provider-neutral requirement 编译到 H3 native prompt 的已实现边界。目标是让新 request 向 ComfyUI workflow 交付三字段字符串，而不是 `generation_mode=...`、`scene_mood=...` 或嵌套 JSON。

本文不是媒体质量验收，也不授权新的 ComfyUI submit、retry、Provider call、candidate activation、P6 Review 或 Final Acceptance。

## Current Runtime Truth

- `src/ai_video/production/comfy_t8_video.py` 与 `comfy_t8_turbo_video.py` 的 T2VA compiler contract 现为 version `2`，共用 strict reopen、lineage/hash preflight 与 `compile_h3_prompt()`。
- `src/ai_video/production/_h3_prompt.py` 对 historical requirement `/1` 与 camera-complete `/4` 生成 exactly three lines：`integrated_multimodal_description`、`overall_soundscape`、`non_diegetic_music`。
- historical `/1` 只投影 current-Shot 的 typed action、performance、motion、pacing、visual treatment、lighting、space/axis、camera 与 audio。`target_shot.intent`、global identity/scene bookkeeping、future beats、opaque Scene/Character IDs、overloaded open/close prose、neutral key-value 与 raw JSON 不进入 Provider prompt。
- `DialogueIntent.language` 使用 sealed canonical BCP-47 core tag。缺失 language 的历史 JSON 仍按原 bytes/hash reopen，但 H3 `/1` dialogue compile 会 fail closed；当前仅支持 `zh-* -> Chinese` 与 `en-* -> English`，不再根据字符集猜 language。
- `locked` 与历史 sealed literal `locked-off` 均确定性输出一次 `locked-off camera`；其他 legacy camera movement 仍 typed unsupported。
- `/4` I2V prompt bytes/SHA 保持兼容；历史 request、resolved request 与媒体 evidence 没有被重写或升级。

Canonical runtime anchors：

- `docs/agent-primary-contract-matrix.md` 的 `Local T8 H3 Provider Family`。
- `docs/v0.2-runtime-baseline.md` 的 Local T8 compiler current truth。
- commits `9e5d64351945e0844fa01a699a71b4a6a26ad6b5` 与 `e66d8dc6f6bbc4a2de61179a2414cd16d08253c1`。

## Session Work And Decisions

1. 首先确认 frontend 只是展示 persisted `prompt_text`；raw neutral JSON 的根因位于 backend compiler chain，不是 React stringify。
2. 将 Quality/Turbo T2VA adapter 从 generic neutral compiler 切换到唯一 H3 native compiler，并把 compiler version 从 `1` 提升到 `2`。旧 version `1` 明确返回 typed unsupported，不隐式升级历史 request。
3. 保留 current-Shot 可执行信息，但移除 global Scene/identity/future-story bookkeeping，避免 Shot 1 prompt 混入 Shot 2/3 beat。
4. 将 legacy visual event owner 收敛为 typed `subject_action + performance/motion/...`；`target_shot.intent` 可保存 canonical structured authoring JSON，但不属于 Provider-native prompt projection。Exact speech只由`dialogue_intent`输出，避免 overloaded prose 重复发送。
5. 用户明确选择新增显式 dialogue language contract。历史无 language 的 serialization/hash 保持兼容，新 H3 dialogue execution 必须提供 supported sealed language。

## Verification And Evidence

Parent verification：

- focused/current behavior suite：`463 passed`。
- `python -m scripts.architecture_gate check`：PASS；只有既有/当前 scope 的 WARN/INFO，没有 error。
- exact historical requirement `runs/drama-h3-t8-30s-preview-20260829-v1/sidecars/requests/shot-01-requirement.json`：原 `requirement_hash` 可 reopen；离线 compile 为 3 行；无 `{}`；包含 current action/performance；不含 `Shot 3`、Scene ID token 或 scene mood。
- canonical M6-D requirement `d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81`：strict reopen 后返回 exact 13-path `H3PromptUnsupported`，没有 prompt bytes；详见 `docs/record_for_agent/2026-08-29-drama-m6-d-shot-01-request-readiness-gate-stop.md`。
- historical missing-language `GenerationIntent` canonical hash 固定为 `077e9b41fd5109d96e12bf014ba3c511b01be0ea3e9d20dde4bb0ababf614053`。
- earlier compiler implementation `reviewer_xhigh` verdict：`accept`，无 blocking issue 或 non-blocking concern；该verdict不评估canonical M6-D pre-submit readiness，后者由新的gate-stop record与scoped `reject`独立所有。

Exact-range Harness：

- range：`57aa62d40e5e7e5654e7cd597440b66ee3351a9a..e66d8dc`。
- receipt：`.agent/harness/runs/h3-native-t8-prompts-final-20260829/receipt.json`。
- status：`passed`。
- receipt verification：`fresh=true`、`scope_worktree_clean=true`、`integrity=true`、`complete_completion_proof=true`。
- mandatory test evidence：Harness `204 passed`、Production video provider `734 passed`、provider-neutral requirement `359 passed`、planner `119 passed`、Shot readiness `208 passed`。

本次没有启动 ComfyUI、没有 submit/poll/fetch、没有生成或修改媒体、没有写 Production Manifest、没有 activation/recovery，也没有产生新的主观质量 evidence。

## Assessment

完整且可安全表达的新 requirement 会向 T8 workflow 交付 H3 native三字段字符串；字段不完整的 canonical requirement继续 typed fail closed。前端若读取成功编译的新 request 的 exact `prompt_text`，应显示该字符串而不是原始 neutral JSON。

已有 `runs/` 中的 request 与视频属于 immutable historical evidence，所以旧页面仍可能展示当时 compiler version `1` 的 raw neutral prompt。修复不会伪造或回填历史 prompt；要看到新格式必须产生一个满足 compiler version `2`、完整 current-Shot intent、以及对白时显式 language 的新 attempt。

## Remaining Risks Or Next Work

- 本次只有 offline/compiler/runtime verification，没有新的真实媒体或 human visual verdict；不能据此宣称 motion、identity、continuity、speech 或画质 PASS。
- Canonical M6-D Shot 01 的 current executable intent不完整，仍为`STOP_BEFORE_SUBMIT`；historical preview compile success不得借给它。
- 当前 H3 dialogue native tag 仅支持 `zh-*` 与 `en-*`。其他 language 必须先建立明确 Provider support/mapping，再扩大 contract。
- 本记录不刷新单独的 RAG index；若 retrieval freshness 依赖外部 index，仍需其 canonical workflow 独立执行。

## Agent Guardrails

- 不得把历史 raw prompt 的存在解释为本修复未生效；先区分 immutable old attempt 与 future compiler version `2` attempt。
- 不得把 `prompt_text` 已变为三字段字符串解释为 Provider submit、媒体生成、candidate activation 或质量 acceptance。
- 不得重新引入 generic neutral serializer、字符集 language guessing、future Story/Scene beat、opaque identity ID 或第二 prompt owner。
- 修改 dialogue language、schema/hash compatibility、compiler version 或 H3 grammar 时，必须同步 tests、canonical docs 与 exact-range Harness。
