# Shot Continuity Source Production Blocker Record

Date: 2026-08-24

> **Superseded current-facing status (2026-08-25):** 本记录中的 `ZERO submit`
> 与 historical v6 bundle 事实仍有效，但当时的graph、Shot identity/role、candidate
> closure、Provider lifecycle、fresh bundle与non-test operator blockers均已关闭。唯一Local
> A2→A3 attempt随后成功fetch exact MP4，但因frames 107→108明显跳变未通过frozen
> boundary/motion gate；没有P6、activation或M0 effect。见
> `2026-08-25-shot-continuity-source-live-attempt.md`。

## Purpose

本文记录 rainy-station A2→A3 upstream source attempt 在进入任何 Local ComfyUI effect 前发现的 Production contract blocker。该 checkpoint 的结论是 `ZERO submit`，不是 source qualification implementation、Production candidate、P6 或 M0 已完成。

## Current Runtime Truth

当前 canonical P0 bundle 为：

`runs/shot-continuity-rainy-station-p0-20260824-v6/production`

其 `state/manifest.json` 为 Manifest `2.11`、revision `5`，但 `active_dependency_graph` 为 `null`。`ProductionStateCommitter.begin_video_generation()` 明确要求 active dependency graph，因此 existing generated-video lifecycle 会在 durable video request write、local submit intent、permit 与 ComfyUI prompt effect之前 fail closed。

当前 Shot 3 bytes还显示另一组 independent mismatch：

- canonical `Shot.shot_id` 是 `rainy-station-3`；`artifact_id` 是 `shot-rainy-station-3`。
- Shot 3 的唯一 `required_asset_roles` role 是 `approved_endpoint`，当前绑定 A3 image。
- 未提交的 source-qualification profile/implementation使用 `target_shot_id=shot-rainy-station-3` 与 `target_asset_role=source_video`。

现有 `video_candidate.make_video_candidate_preparer()` 按真实 `Shot.shot_id` 查找 target，并要求 target role已经在 base Shot中唯一存在。因此即使只补一张 dependency graph，当前未提交 request/profile仍不能形成可由 canonical candidate/P6/activation path接受的 Production candidate。

## Session Work And Decision

本轮只读追踪了 source qualification caller、`VideoGenerationService`、`ProductionStateCommitter` video lifecycle、`ComfyUIVideoProvider` status/fetch、candidate preparer、P0 runtime bundle与 exact Shot 3 bytes。

两个 external MiniMax explorer均为 read-only：

- source-effect gate mapping：runner model `MiniMax-M3`、Claude-compatible transport，`status=success`、`agent_status=DONE_WITH_CONCERNS`；结论为 direct M0仍禁止，第一候选 effect只能是 upstream source attempt。
- concrete operator mapping：同一 runner/transport/status；结论为仓库没有 non-test source-qualification operator，缺少真实 request/project/transport wiring。

parent verification进一步推翻了“当前 seam已可安全 submit”的假设：fixture构造了非空 dependency graph，并用 `SimpleNamespace` 模拟 Shot identity/role，因此没有覆盖 canonical P0 bundle中的上述 mismatch。

最终决定是保持 effect count为零，不通过临时 Python、test helper、空 graph或 submit-only shortcut制造无法进入 canonical evidence pipeline 的孤儿 ComfyUI job。继续修复需要新的明确 scope，至少关闭 active dependency graph、真实 Shot identity/role与 candidate-preparer contract。

## Verification And Evidence

本轮运行的 focused offline tests：

```text
python -m pytest -p no:cacheprovider \
  tests/test_shot_continuity_source_qualification.py \
  tests/test_shot_continuity_m0_caller.py \
  tests/test_video_generation.py \
  tests/test_production_local_video_state.py -q

91 passed in 4.48s
```

该 PASS只证明未提交 fixture所描述的 local request/permit/unknown-outcome行为，不证明 current P0 runtime bundle可执行。直接读取 current bundle确认：

- `active_dependency_graph: null`
- Shot 3 `shot_id: rainy-station-3`
- Shot 3 role: `approved_endpoint`

本轮没有启动 ComfyUI generation，没有提交 prompt，没有调用 remote/paid Provider，也没有产生新媒体。

## Remaining Work

继续 A 路线前必须先获得明确 scope，并以离线 contract/test为先：

1. 定义 P0 bundle何时、由哪个 canonical owner获得 exact active dependency graph；不得注入与项目语义无关的空 graph。
2. 决定 upstream source candidate应替换 `approved_endpoint`，还是通过受控 Project/Shot revision新增正式 role；同步 profile中的真实 `Shot.shot_id`。
3. 证明 deterministic candidate preparer能从 fetched A2→A3 bytes建立 inactive candidate、P6/human evidence与后续 activation closure。
4. 只有上述 changes在 exact committed snapshot上通过 focused tests、Harness与 independent review后，才重新授权一次 local submit；unknown outcome仍不得 retry或 fallback。

Direct M0 generation继续禁止，直到 accepted upstream source bytes、terminal与motion-tail全部由 canonical evidence chain产生。

## Agent Guardrails

- offline fixture PASS不等于 canonical runtime executable。
- `artifact_id`不等于 `Shot.shot_id`。
- 临时补 graph不等于 dependency semantics已建立。
- ComfyUI submit/fetch success不等于 candidate、P6、activation或M0许可。
- 对相同 desired attempt不得通过新脚本、MCP或direct HTTP绕过 existing durable request、permit、replay与recovery owner。
