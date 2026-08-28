# H3 Causal Readiness Phase A Record

Date: 2026-08-28

## Supersession Notice — 2026-08-28

M6 已在新的 task-scoped authorization 下进入真实 local H3 micro-sequence，并由
`docs/record_for_agent/2026-08-28-h3-m6-causal-micro-sequence-gate-stop.md` 记录当前 evidence：
Shot A technical Gate 六类均 PASS；Shot B 的 causal handoff/release/exit PASS，但 conditioning 与 camera
requirement 为 FAIL，因此 stop rule 在 Shot C submit 前生效。下方 M1–M5 offline implementation 与 verification
仍有效；“下一关键步骤是首次执行 M6”的状态和 authorization blocker 已被该新记录取代。

## Purpose

本文记录 `docs/superpowers/plans/2026-08-27-ai-video-shot-to-h3-continuity-enforcement.md`
Milestones 1–5 的 offline implementation checkpoint。目标是把 v12/v13 已观察到的跨 Shot 因果跳变、
incompatible FL2VA last anchor 与 H3 prompt 多次 prose 翻译问题，收敛为一个可执行但尚未完成真实媒体验证的
pre-generation contract。

本记录不是 M6 media authorization，不是 HUMAN PASS、Production qualification、P6、Final Acceptance 或
publication evidence。

## Implemented Runtime Boundary

当前 local implementation 新增 additive `provider-neutral-video-requirement/4` branch：

- `GenerationIntent` 显式拥有 performance、visual treatment、lighting、ambience、dialogue、music、单一
  `primary_camera_motion` 与稳定 `camera_subject_relation`；locked camera 使用 canonical locked-off 表达，
  relation 不得夹带第二 creative camera motion。
- `ConditioningCompatibilityEvidence` 区分 I2VA / FL2VA，并在 requirement validation 中绑定 exact first/last
  asset identity、semantic role、geometry、capability needs、output duration 与 intent pacing。FL2VA 的 scale、
  composition、screen order/axis、camera path、character/prop state 与 action endpoint 必须全部显式 compatible。
- `ContinuityTransitionPolicy/2` 绑定 source/target exact Shot identity 与 generation-intent hashes，并使用 typed
  causal dimensions覆盖 character presence、prop identity/holder/hand/functional state、action phase、gaze、
  dialogue turn、screen motion/axis 与 audio bridge。Coarse boundary/obligation 与 causal semantics 不能形成双真相。
- `ShotReadinessRequest/2` 与 canonical `require_current_video_plan()` /
  `prepare_shot_for_existing_production()` handoff 显式消费 transition policy；缺失、维度不完整、identity/hash
  不匹配或 stale seal 时 fail closed，不能暴露 verified generation projection。
- `src/ai_video/production/_h3_prompt.py` 成为唯一 H3 three-field grammar owner。它只机械编译 sealed intent，
  生成唯一 `[Shot 1]`、`integrated_multimodal_description`、`overall_soundscape` 与
  `non_diegetic_music`，并拒绝 multi-Shot、transition instruction、line-boundary injection 与 secondary
  camera motion。Dialogue Unicode/quotes bytes 与 explicit music intent 原样保留。
- 只有 `LocalVideoQualityExecutionProfile` 的 `minimax_h3_fl2va_quality_local` Stock20 FL2VA lane 可使用
  compiler version `2`；generic compiler 缺少 explicit native prompt 与所有 non-pilot `/4` 路径均 fail closed。
  Historical requirement `/1`–`/3` 与 compiler version `1` 不被重解释。

Requirement、Provider-bound request 与 transition policy 都在 effect 前重新验证 exact seal；`model_copy()`
保留 stale hash 的对象不能借旧 lineage 编译新 prompt 或通过 readiness。

## Verification And Review

Current working-tree checkpoint 的 focused Phase A suite：

```text
266 passed in 3.87s
```

覆盖 requirement/planner/conditioning/transition/readiness/H3 compiler/Stock20 provider adapter、legacy hashes 与
reopen behavior。`git diff --check` 与相关 production/planning/quality-gate module `compileall` 通过。

第一次 `reviewer_xhigh` 独立审查为 `reject`，确认 pairwise gate 未接线、conditioning evidence 未绑定、pilot
profile 未隔离以及 prompt injection 四个 blocker。修复后同 tier scoped re-review 继续发现并验证 canonical
handoff、Unicode line boundary、exact dialogue bytes、secondary camera prose、coarse/fine transition semantics 与
stale-seal gaps；最终 verdict 为 `accept`，没有剩余 offline blocking issue。

所有验证均为 local offline code/test evidence。Provider submit、ComfyUI runtime、媒体生成、重编码、activation、
P6 或 human playback 均未发生。

## Evidence Relationship

- 四臂 conditioning attribution 支持 incompatible last anchor 是 forced transition、terminal snap 与 tail
  collapse 的 primary cause；它不支持普遍 FL2VA lane mismatch、Stock20 recipe/pin 或 H3 model limitation。
- v13 单 Shot 证明 compatible anchors + explicit visible handoff 可取得 technical Shot Gate PASS，但其 prompt 为
  manual authoring，且 30s recut 仍因 character entrance/exit/re-entry 失败。
- 本 Phase A 只证明上述 evidence 已被翻译成可执行的 typed gate 与 deterministic pilot compiler；它没有证明
  模型生成质量改善，也没有改变 v12/v13 的 media/human verdict。

## Remaining Risk And Stop Rule

下一关键步骤仍是 plan 的 M6 causal micro-sequence：使用单独 task-scoped authorization，生成符合当前 H3
最低 `124 frames @ 24 fps` 的 `2–3` Shots，验证 visible entrance/presence、recommend/show、handoff/receive、
explicit exit/release、open/use 与 effect。每个 exact Shot 仍须在下一次 submit 前通过 project-local
per-Shot post-media Gate，最终由 human 以 `1.0x` 判断 causal reachability、camera、performance、dialogue/lip-sync
与 readability。

在该 micro-sequence HUMAN evidence 之前，M7–M9、remaining adapters、qualification、composition enforcement
与 aggregate Gate expansion 保持 deferred。Phase A PASS 不授权任何新的 Provider、ComfyUI 或媒体动作。

## Agent Guardrails

- `Shot order PASS` 不等于 `previous.close_state -> next.open_state` causal reachability。
- compatible conditioning technical PASS 不等于 HUMAN camera/performance PASS。
- deterministic prompt compilation 不等于模型遵循 prompt。
- commercial cut、causal ellipsis 与 scene reset 必须由 typed policy 明确声明，不能从 abrupt output prose 推断。
- post processing 可以服务已声明的艺术/节奏目的，但不能创造或伪造 continuity PASS。
- M6 FAIL 必须回到最小责任 owner；不得因此继续扩 M7–M9 infrastructure。
