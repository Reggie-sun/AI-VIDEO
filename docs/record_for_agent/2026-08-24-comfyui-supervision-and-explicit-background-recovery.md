# ComfyUI Supervision And Explicit Background Recovery Record

Date: 2026-08-24

## Purpose

本文记录 AI-VIDEO 本地 ComfyUI 长进程 supervision 与 long-video background state 显式恢复的当前 implemented truth，供后续 Agent 处理 ComfyUI 启停、process interruption、stale / unreadable `background_job.json`、reattach 与 accepted Manifest continuity 时复用。

本记录描述 engineering/runtime closure，不把 ComfyUI service health、offline tests 或 recovery routing PASS 描述成媒体质量、Shot Continuity、P6 或 Final Acceptance。代码、tests、Harness receipts 与当前 runtime status 仍是 source of truth。

## Incident And Scope Boundary

Shot Continuity E0-C 在已接受 6 个 segments、634 frames 后，于 segment 6 sampling `1/20` 时观察到承载 ComfyUI 的进程收到 `SIGTERM`，runner exit `143`。终止来源没有被证据识别；不得把本次 hardening 描述为已经定位或消除了该 `SIGTERM` root cause。

进程终止后遗留的 `background_job.json` 为 `state=running`、`accepted_count=6`、`current_segment_index=6`、`retry_count=0`。它是失去 owner process 后的 stale auxiliary state，不是 completion、cancel、retry authorization 或 accepted-position truth；accepted Manifest 继续拥有 durable segment position。

本次 authorized scope 只关闭两个可复用 hazard：

1. Agent command / unified exec lifecycle 不应持有本地 ComfyUI 长进程。
2. GET status、direct requeue 或 unreadable-state handling 不应隐式推进 recovery truth。

没有恢复 E0-C generation、补交 segment 6/7、retry、fallback、remote/paid Provider、媒体生成或 quality acceptance。

## Local ComfyUI Service Ownership

AI-VIDEO local commit：

```text
f9b580d fix: supervise local ComfyUI lifecycle
```

Canonical development owner 为 `scripts/comfyui_supervisor.py`，`h3-video` skill 已从手工 `nohup` launcher 切换到该 explicit CLI。当前 contract：

- `start`、`status`、`logs`、`stop` 是唯一公开 lifecycle controls；没有 auto-start、auto-restart、timer、workflow submit 或 generation recovery。
- 每次 explicit `start` 创建不可复用的 `ai-video-comfyui-<32-lowercase-hex>.service` user-systemd transient unit，固定 `127.0.0.1`、`Restart=no`、`KillMode=mixed` 与 journal output。
- Systemd strict-namespace enumeration 是唯一 owner discovery；supervisor 不保存第二套 pointer、PID file 或 job state。
- User runtime advisory mutex 覆盖完整 preflight、unit creation、health poll 与 final ownership confirmation，使 concurrent supervisor callers 必须重新检查 existing unit 与 port ownership。
- existing strict unit、多个 strict units 或 occupied loopback port 均 fail closed；`stop` 不使用 wildcard 或 broad prefix targeting。
- HTTP `/system_stats` 成功仍不足以宣称 owner ready。Supervisor 继续验证同一 `InvocationID`、active state、positive `MainPID`，并从 `/proc/net/tcp` 与该 PID 的 fd table 证明 exact `127.0.0.1:<port>` listener ownership。
- post-creation failure 只清理本次 unique unit。若 `systemctl stop` 失败，结果明确为 cleanup unconfirmed，并保留 bounded diagnostic detail；不得猜测 unit 已消失。
- `status` 与 `logs` 只读。Service active 只证明 local process ownership / technical readiness，不证明 queue empty、Provider capability、媒体输出或 quality acceptance。

Canonical human-readable surface contract 位于 `docs/agent-primary-contract-matrix.md` 的 `Local ComfyUI Supervisor` row；Harness routing 位于 `.agent/harness/policy.yaml` 的 `local_comfyui_supervisor` category。

## Explicit Background Recovery

ComfyUI custom-node plugin local commit：

```text
28cb160 fix: require explicit long-video recovery
```

Plugin checkout：`/home/reggie/ComfyUI/custom_nodes/minimax-h3-audio-T8`。当前 recovery contract：

- GET background status 对 stale active 或 unreadable auxiliary state 只返回 ephemeral `detached` recovery view，并设置 `recovery_persisted=false`；它保持 `background_job.json` byte-exact，不 quarantine、不 queue、不 compose。
- POST action `recover` 是显式 durable transition。它在读取、quarantine 与写入期间持有 chain 的 OS advisory lease。
- 另一 ComfyUI process 持有 lease 时，readable 与 unreadable 两种 state 都拒绝 recovery，且 background state bytes 不变。
- Recover 只持久化 `detached` classification；不 queue prompt、不 release models、不 compose、不增加 retry，也不重写 accepted Manifest position。
- readable stale-active 与 unreadable state 都不能通过直接 queue / `attach_prompt()` 绕过 Recover。
- Recover 成功后，incomplete accepted Manifest 只能由用户 queue workflow once 重新附着；complete accepted Manifest 只引导 `Compose Accepted`，不得再生成一个 segment。
- Frontend 暴露独立 Recover control；route 使用 `asyncio.to_thread()`，recover path 不隐式调用 composer。

Mutable background execution state 仍由 plugin background manager 拥有；accepted media position/finality 仍由 canonical long-video Manifest 拥有。Supervisor 不读取或修改 long-video job state，background recovery 也不拥有 systemd lifecycle。

## Verification And Evidence

AI-VIDEO parent focused verification：

```text
193 passed
Documentation contract gate passed.
```

覆盖 supervisor CLI、strict unit namespace、cross-caller mutex、post-create cleanup、foreign health rejection、exact `/proc` listener inode/port ownership、Harness routing、Documentation Contract Gate 与 session record hook。

Exact staged AI-VIDEO Harness receipt：

```text
.agent/harness/runs/20260824T114936417333Z/receipt.json
```

Receipt verification 为 `passed=true`、`fresh=true`、`snapshot_matches=true`、`scope_paths_match=true`、`policy_matches=true`、`artifact_integrity=true`、`workspace_cleanup_confirmed=true`。Detached snapshot 中 `local_comfyui_supervisor_tests` 为 `16 passed`，`harness_tests` 为 `177 passed`；policy audit 无 unmapped、unverified、missing 或 unreferenced paths。

Plugin focused verification：

```text
PYTHONPATH=/home/reggie/ComfyUI python -m pytest -p no:cacheprovider \
  tests/test_long_video_background.py tests/test_long_video_routes.py \
  tests/test_preflight_and_registration.py -q
57 passed
```

Focused coverage 包括 read-only byte preservation、explicit recovery、readable/unreadable cross-process lease rejection、no queue/release/retry/compose effects、reattach prerequisite、route 与 frontend control。

Independent `reviewer_xhigh` 多轮 review 先后拒绝并推动关闭 Harness mapping、cross-process lease、direct requeue bypass、reusable unit stop race、loose unit namespace、concurrent start、cleanup leak、shared-port health misattribution 与 volatile fd handling。对 exact commit `f9b580d` 的最终 verdict 为 `accept`，无 blocking issue。

Read-only real supervisor status 在记录时为 inactive / not-found。本次没有执行真实 `start` 或 `stop`；因此 tests 与 status 不能替代下一次 authorized launch 的 journal、PID/listener 与 application-level observation。

## Publication And Acceptance Boundary

AI-VIDEO commits `f9b580d` 与 ComfyUI plugin commit `28cb160` 只存在于本机 `main`。记录时 AI-VIDEO 相对 `origin/main` 为 ahead，plugin 相对 `origin/main` 为 ahead `2`；没有 push、release 或 remote deployment。

本次没有 stage、commit、reset 或覆盖 AI-VIDEO checkout 中的 `index.json` 或其他 unrelated dirty changes。Plugin checkout 在 `28cb160` 后 clean。

该 closure 是 engineering lifecycle / recovery PASS，不是 E0-C empirical completion。634-frame partial、Manifest revision 6、未知 `SIGTERM` root cause、segment 6/7 absence、P6 与 Final Acceptance truth 均未改变。

## Remaining Risks And Next Work

- 未知 `SIGTERM` 来源仍需独立、bounded、read-only reassessment；supervisor hardening 不能倒推出 termination cause。
- 下一次真实 ComfyUI `start` 必须来自明确 lifecycle authorization，并核对 returned unique unit、journal、`InvocationID`、MainPID 与 exact loopback listener。
- 若下一次需要恢复 E0-C，必须把新的 resumed attempt 与 historical interrupted attempt 分开记录；不得 blind retry 或把 resumed output 冒充 uninterrupted original execution。
- Recover 前必须确认没有 live process lease；Recover 后只能按 response 的 `queue_workflow_once` 或 `compose_accepted` action 执行。

## Agent Guardrails

- `systemd active` 不等于 ComfyUI generation succeeded。
- `/system_stats` healthy 不等于 exact unit owner；必须保留 PID/listener binding proof。
- GET detached view 不等于 recovery 已持久化；必须检查 `recovery_persisted`。
- Recover PASS 不等于 queue、resume、retry 或 composition 已执行。
- accepted Manifest truth 不得被 stale `background_job.json` 覆盖。
- infrastructure hardening PASS 不等于 E0-C complete、watchable、P6 PASS 或 Final Acceptance。
- 历史 credential、ComfyUI availability 或 local media 不授权新的 Provider、generation、resume、push 或 release。
