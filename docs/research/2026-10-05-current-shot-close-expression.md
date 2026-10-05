# Current Shot Close Expression Research

## Baseline

执行 `git fetch origin main` 后 `HEAD == origin/main == d607726643a25bcbaadd3debaa0ec7ef36337201`。
existing staged Harness granularity paths 属于其他任务，保留且不纳入本任务提交。

## Ownership And Classification

**Case C**。`production/video_requirement.py::GenerationIntent.close_state` 是独立 typed seal；
`ProviderNeutralGenerationIntentProjection.create` 封存 author 提供的 intent，
`planning/_planner_models.py::VideoPlanningRequest.generation_intent` 消费该 projection，
`planning/video_planner.py::_build_generation_requirement` 透传至 requirement。Planner 不创作终态。
canonical creative owner 是 approved Shot/context 的 author，durable input owner 仍是 `GenerationIntent`。

`SubjectAction.endpoint`、`PerformanceIntent.terminal_performance_state`、`SpaceContinuity.exit_state`、
`MotionEnvelope.settle`、`CameraEndpoint` 都是局部事实，不能确定完整十维 causal column。
`production/video_transition.py::CausalStateChange` 只定义 `source_close`、`target_open`，
`ContinuityTransitionPolicy` v2 是 previous-close → current-open edge。
`production/_video_continuity.py::C4SemanticBoundaryState.close_state` 是旧 C4 字符串列表，
没有 `CausalDimension` 映射或当前 GenerationIntent close-column binding，不能冒充完整 current close。
director coverage / Shot narrative 不提供可用于确定性 projection 的十维 close truth。

## Opening Evidence

`_sequence_source.build_verified_causal_opening_expression` 重开 selected Production project、
accepted source、exact Planner projection、policy/route。`_causal_prompt_context.VerifiedCausalOpeningExpression`
是 ephemeral、owner-issued、requirement/provider-request/policy/route/source-close hash bound；
每次 `opening_facts` 重验完整 source-close / target-open columns。无 durable duplicate truth。
该证明不拥有 current close，即使 opening 和 closing digest 相等也无 closing authority。

## Compiler And Local Debt

`_remote_video_native_prompt.compile_remote_video_prompt` 支持 verified opening，但 close hash 一直 unsupported。
`_h3_prompt._state_text` 依次取 ref/text/hash，实际存在 hash-as-prose。
production consumers 为 `comfy_video.ComfyUIVideoProvider`、`comfy_t8_video` Quality、
`comfy_t8_turbo_video` Turbo、`comfy_t8_native_turbo_video` Native/Long。
需要同一 endpoint verification / renderer，保留 remote/local 独立 grammar。

## Fresh Source And QA

authoring 没有 current-close preimage，故 Planner 可以封存 arbitrary hash，但 remote compiler 无法诚实表达。
`generation_feedback._expressions` 从 selected QA 的 `intent_paths` 派生 recipe；
`_sequence_source.accepted_sequence_source` 要求 raw analyzer/human、exact tolerance、
`observable == generation_intent.close_state.state_hash` 的 acceptance criterion。
`generation_evaluation_criteria.evaluation_items` 原本只从 rubric 生成问题，不消费 requirement preimage；
`ai_video_mcp/generation_feedback` presentation 和 `generation_evaluation` reopen 必须同时接入同一 sealed intent。
技术 PASS、prompt coverage 或 scripted PASS 不能证明真实 raw terminal state。

## Tool Boundaries

Agent Memory all-scope 查询 exit 3（library-incompatible shards），按 Skill 不重试、不前台重建。
CodeGraph 已索引并核对 `compile_with_sequence_expression` 的 feedback/pre-submit callers。
AOCI 提供 stale/dirty advisory index，不作为 current implementation truth。
Kimi route 需要 live credential injection 与外部 request；本次禁止项优先，因此使用 native
read-only `code_mapper` 调查 QA。没有 credential lookup、Provider submit、paid permit consumption 或媒体生成。
