# Shot Continuity Source Local Lifecycle Record

Date: 2026-08-25

## Purpose

本文记录 rainy-station A2→A3 upstream source qualification 的同一 Provider local
lifecycle checkpoint。它证明 offline implementation、durable failure semantics、review 与
exact current-HEAD Harness 已关闭；不授权或证明 ComfyUI live generation、source MP4、P6、
M0、Join Gate J1、winner selection、activation 或 Final Acceptance。

## Current Runtime Truth

commit `50de0c07cc5a5fe0603c99542af9468f671176cb` 补齐
`ShotContinuitySourceQualificationProvider` 的 `get_local_status()` 与 `fetch_local()`，并继续
通过 `VideoGenerationService` 与 `ProductionStateCommitter` 保持唯一 durable lifecycle owner。
没有新增 second Provider、direct HTTP operator、automatic retry、fallback、activation 或 recovery
owner。

当前行为边界为：

- `SourceQualificationTransport` 明确声明 sealed submit 后所需的 `poll_job()` 与
  `fetch_artifact_bytes()` contract；concrete loopback transport仍是唯一 effect adapter。
- poll 前绑定 reopened request 与 durable submission；fetch、locator parse 与 sink write 前绑定
  request、submission 及 observation fingerprints。mismatch 以 typed
  `VIDEO_REQUEST_INVALID` fail closed，effect count保持为零。
- terminal `FAILED` 形成 canonical failed observation；timeout/非 terminal outcome 形成
  non-retryable `VIDEO_PROVIDER_OUTCOME_UNKNOWN`，要求 explicit recovery。
- ComfyUI 报告 `COMPLETED` 但没有 exact sealed output node 的唯一 MP4 时，归一化为
  non-retryable `VIDEO_PROVIDER_FAILED`。`VideoGenerationService` 将其持久化为 Manifest
  `FAILED`，`resume_next_action()=="stop"`，同 attempt不得再次 poll。
- fetched payload 在写 sink 前执行 minimal MP4 signature validation；成功 receipt继续绑定 exact
  submission、observation、artifact bytes、size与 SHA-256。

historical `runs/shot-continuity-rainy-station-p0-20260824-v6/production` 不因本次 code
checkpoint 自动升级。它仍不是 fresh executable source attempt，也没有 accepted upstream MP4。

## Verification And Review

parent 在最终 code state运行：

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_shot_continuity_source_qualification.py \
  tests/test_shot_continuity_source_runtime.py \
  tests/test_shot_continuity_source_transport.py \
  tests/test_shot_continuity_m0_caller.py \
  tests/test_shot_continuity_m0_validation.py \
  tests/test_video_generation.py \
  tests/test_production_local_video_state.py -q

143 passed in 47.11s
```

native `reviewer_xhigh` 初审发现并拒绝两个 lifecycle defect：effect 前 identity未绑定，以及
completed-invalid output不会形成 durable terminal failure。两项均加入 RED regressions并修复；同
tier scoped re-review最终 `Verdict: accept`，无 blocking或non-blocking concern，其 focused suite为
`51 passed in 28.52s`。

exact range `8ebe3313bfb067b6f328d154f43a427d28322aa1..50de0c07cc5a5fe0603c99542af9468f671176cb`
的 Harness receipt为：

`.agent/harness/runs/shot-continuity-source-lifecycle-50de0c0/receipt.json`

Harness在 detached snapshot记录：

- Shot Continuity P0：`233 passed`；
- Production video Provider：`651 passed`；
- provider-neutral video requirement：`292 passed`；
- docs contract、policy audit与Architecture Gate均通过；Architecture Gate只有
  `ARCH005 module-fan-out-review-signal` INFO；
- receipt的 integrity、freshness、policy/snapshot match、scope cleanliness、workspace stability、
  cleanup、closure与completion proof全部为 `true`。

尝试复验 historical `254c3851..34f38ed` range时，Harness按 contract拒绝非 current-HEAD
closure：`completion scope is not closure eligible`。没有通过 checkout、reset或临时 branch绕过
shared dirty tree。因此旧 receipt不能被描述成 fresh completion proof；当前 checkpoint只依赖上述
`50de0c0` current-HEAD receipt。

## Remaining Gates

下一步仍不得直接执行 M0：

1. 从 canonical preparation/materialization seam创建 fresh Production root，重新核对 selected
   project/registry/dependency graph、source/M0 stack、schema seals、A2/A3 bytes与空 attempt state。
2. 提供 non-test resolved source request/operator wiring；不得复用 test helper、direct ComfyUI HTTP、
   submit-only脚本或 historical v6 bundle制造孤儿 job。
3. 由于 active plan明确不自行授权 live generation，执行唯一一次 A2→A3 local submit前仍需当前
   task的 explicit local-live scope；remote/paid execution不在 scope。
4. fetched source MP4仍须经过 decoded boundary、P6/human acceptance，并从同一 accepted bytes派生
   terminal与motion-tail；随后才可评估一次 M0 edge 3→4。
5. `docs/agent-primary-contract-matrix.md` 与 `docs/v0.2-runtime-baseline.md` 当前含本 task
   之外的 commercial uncommitted changes。本 session未争抢 same-file ownership，因此 canonical
   documentation sync仍是明确 blocker，不能把本 record当作第二 runtime owner。

## Agent Guardrails

- offline Provider lifecycle PASS不等于 live-ready、source generated或quality accepted。
- fetch receipt不等于 inactive candidate、P6、activation、M0或Final Acceptance。
- one permit / one submit / no retry / no fallback / explicit recovery保持不变。
- historical bundle、old MP4、experiment media或test fixture不得冒充 exact accepted source。
- 本轮没有 ComfyUI upload/submit/poll/fetch、媒体生成、remote/paid call、push或release。
