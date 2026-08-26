# Shot Continuity M0 Dual Validation Policy Record

Date: 2026-08-26

## Purpose

本文记录 M0 从单一隐式 quality route 收敛为两个显式、不可互换的用户选择：
`fast-v1` 与 `quality-v1`。本记录描述 current local implementation 与验证边界，不构成
新的 live Provider、媒体生成、P6、Final Acceptance、push 或 release authorization。

## Current Contract

- P0 preparation、endpoint repair、M0 materialization 与 M0 caller 都必须显式选择
  `fast-v1` 或 `quality-v1`；没有 default，也没有 fast failure 后的自动 fallback。
- selection content-addressed 绑定 exact policy、profile document、execution stack、frozen
  rubric 与 capability。fast 的 PASS 不得资格化 quality capability，反之亦然。
- 两条 policy 共用同一 frozen M0 rubric，但 policy layer 不创建 verdict 或第二套 evidence
  lifecycle。Exact requirement-level evidence 仍须交给 existing P6/human owner，才能形成
  scoped `PASS`、`FAIL` 或 `NOT_EVALUATED`。
- P0 candidate labels 仍保持 `(m0, m1)`；显式 policy 只选择 M0 的 exact stack，不增加第三个
  candidate，也不改变 `ProductionStateCommitter`、Manifest、P6 或 Final Acceptance ownership。

## Fast And Quality Profiles

`quality-v1` 保持既有 Stock20/no-LoRA、20-step compiler 与 workflow bytes。其 compiler
SHA-256 继续为：

```text
e2ba38bb110e26a5221a5582ea19f777752a1946ffacbe31b1445073d1530d19
```

`fast-v1` 使用独立 offline qualification candidate：

- literal `Hybrid` task；
- exact first frame、last frame、identity image 与 motion-tail video 四锚点；
- sealed `minimax_h3_turbo_4step_ema_comfyui.safetensors` Turbo LoRA；
- `4` steps、`dual_clock_euler`、`native_flow`；
- exact conditioning、sampler、guider、advanced sampler、decoder 与 output dataflow；
- loopback/local-only，remote provider 与 cloud fallback 均关闭。

Fast profile 仍是 `offline_qualification_candidate`。它不是 live-ready profile，当前也没有
fast exact MP4、media analysis、P6 review 或 human acceptance evidence。

## Fail-Closed Behavior

- Missing/unknown policy、policy/stack/profile/rubric/capability mismatch、calibration drift、
  internal workflow dataflow drift、selected materialization mismatch 与 durable request drift
  都在 intent、permit、upload 或 submit effect 前停止。
- endpoint repair 不再隐式选 `quality-v1`；CLI 必须提供 `--m0-policy`，并将 selection 传入
  canonical P0 preparation seam。
- 既有程序化 P0 callers 已显式声明 `quality-v1`，因此 compatibility 是 explicit，而不是
  通过新 default 恢复。
- Fast source、compiler、guard、live-schema dispatch 与 caller 使用独立 dispatch；不会在
  fast failure 时进入 quality source 或 quality capability。
- Fast 的 script-level materialization 会合法 reseal current P0 receipt；preflight 固定并重验
  seed roots、Project/Registry 与 fresh complete snapshot，不会把 initial receipt hash 错当成
  post-materialization 的永久 identity。Prepared bundle → materialize → reopen → exact replay
  已由集成测试覆盖。

## Verification Evidence

本轮没有调用 Provider、ComfyUI、network、credential、media generation、analyzer、P6、
activation 或 recovery side effect。

已执行的 focused verification：

```text
python -m pytest -p no:cacheprovider \
  tests/test_prepare_shot_continuity_endpoint_repair.py \
  tests/test_prepare_shot_continuity_p0.py \
  tests/test_production_p0_qualification.py \
  tests/test_production_video_transition.py \
  tests/test_shot_continuity_source_runtime.py \
  tests/test_shot_continuity_source_qualification.py \
  tests/test_shot_continuity_source_operator.py \
  tests/test_shot_continuity_source_transport.py \
  tests/test_shot_continuity_m0_materialization.py \
  tests/test_shot_continuity_m0_validation.py \
  tests/test_shot_continuity_m0_caller.py \
  tests/test_shot_continuity_m0_policy.py \
  tests/test_shot_continuity_m0_fast_validation.py \
  tests/test_shot_continuity_m0_policy_preparation.py \
  tests/test_video_candidate.py \
  tests/test_video_generation.py \
  tests/test_production_local_video_state.py -q
```

Result: initial snapshot `273 passed in 94.50s`；review blocker修复后的exact-index selection为
`276 passed in 91.31s`。新增回归分别绑定unmodified shipped fast profile与exact fast prepared receipt，并证明
`fast-v1`、`quality-v1`在permit前validation后都不再重新读取compiler/profile/workflow sources。

另在isolated `/tmp` root中使用v7 source、用户批准的exact A3 bytes/timestamps执行no-Provider
`fast-v1` prepare，再以unmodified shipped fast profile完成canonical materialize/reopen。Initial fast receipt为
`9d2a9fa92b727af4be7cfc1fbc3a8624cf3766a8b741f715cd2fd3c9845cc30d`，initial M0 stack为
`d486728c5f8c561bfe1ca2c681fe41736ababfc7223856e7e0f18964abeb40f6`；materialization报告
`provider_effects=0`、`video_generated=false`、`winner_selected=false`。

`git diff --check` 与 relevant `py_compile` 均通过。Historical v3 Harness虽然各checks单独通过，但overall
`status=failed`、`workspace_stable=false`，原因是verification期间HEAD从`2a157ec`移动到`592a685`；因此
`.agent/harness/runs/m0-dual-validation-policy-20260826-v3/receipt.json`不是completion proof，也不得描述为fresh。
随后v4 staged Harness在tests启动前fail closed，因为4个M0 staged paths同时含有本task之外的unstaged
ecommerce edits；该run没有吸收或覆盖这些changes，也不是completion proof。为保持index与unrelated work隔离，
本task使用普通`git commit`只提交exact staged snapshot；current completion candidate path固定为
`.agent/harness/runs/m0-dual-validation-policy-20260826-v5/receipt.json`，并必须针对该exact commit range验证
status、integrity、scope、artifact hashes与freshness。本文不预宣PASS。

## Remaining Boundary

本轮只完成显式双 policy、independent fast stack 与 fail-closed offline execution contract。
Fast 尚未完成真实 M0 media experiment，也没有 policy-bound P6/human verdict。若后续用户授权
live validation，必须使用 exact selected fast bundle、单次 bounded local submit、逐 Shot
`video-analysis` Gate 与 existing P6/human lifecycle；不得把本轮 tests 或 Harness PASS 当成
媒体质量结论。
