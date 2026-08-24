# Shot Continuity E0-C Prompt-Schedule Relay Development Experiment

## Status

- `experiment_id`: `shot_continuity_e0c_prompt_schedule_relay_v1`
- `classification`: `development_experiment`
- `execution_status`: `INCOMPLETE_INFRASTRUCTURE_INTERRUPTION`
- `empirical_status`: early route-kill gate passed; full 770-frame schedule not evaluated
- `production_status`: no Production qualification、activation、Manifest / Registry mutation、P6 verdict、release 或 canonical-reference promotion

本次只验证 E0-B STOP 后冻结的单变量：把每个 continuation 重复使用的 stop-oriented global prompt 改为 `segment_prompts_json` 驱动的 per-segment motion-state schedule。其余 generation surfaces 保持冻结。E0-C 没有启用 Prompt Relay Advanced attention patch；只使用现有 long-video orchestrator 的逐段 prompt override。

## Author Evidence Boundary

上游作者已经完成过约 32 秒的 `ScenePlusIdentity + interval 1 + 22-frame AV latent context` 长链实验。该实验改善了 identity，但 predeclared motion floor 失败，路径继续保持 `EXP` / default-off。作者也验证了 prompt relay 的机械执行路径，但没有提供“steady segments -> decelerate segment -> stop segment”能够恢复 motion preservation 的质量证据。

因此 E0-C 超出的是作者**已证明有效的 empirical evidence**，不是超出作者代码支持范围。E0-C 不重做作者已经回答的 reference/context baseline；它隔离验证尚未回答的 temporal prompt allocation hypothesis。

## Frozen Contract

唯一变量：

```text
prompt_temporal_allocation:
  repeated_stop_oriented_global_prompt
  -> per_segment_motion_state_schedule via segment_prompts_json
```

冻结不变：

- Local ComfyUI / MiniMax H3 T8 only；remote submit、paid Provider、fallback 均为 0。
- fixed seed `320001`；未运行 `320002`、`320003`、`320004`。
- `1344x768`、24 fps、目标 770 frames / 32.083333 s。
- Stock20、20 steps、`dual_clock_euler/native_flow`、shift `12/3`。
- Turbo LoRA off。
- `ScenePlusIdentity`、interval `1`。
- 22-frame AV latent context。
- `max_retries=0`、parallel `0`、native audio、CRF `17`、`unload_all_models`。
- segments `0..5`: steady motion；segment `6`: decelerate；segment `7`: stop。

Prompt SHA-256（exact UTF-8 bytes，末尾一个 LF）：

- steady: `51715a9b7a0a25017c5958147984e1000b527468390ac6973acb47e7652911c1`
- decelerate: `f6c151b3a0f38582dbd3b8c1177da943aced49db8d28f823d470bd012ce91e38`
- stop: `1cbdef638176de83372f053a64631923cffe8a09ba77a42a89a00a9aeae7be2f`
- E0-B frozen global prompt: `d65e4f9337c8f5b26854b3f413e61a6485ae1d2ab288bce3a87739fbcae1f22b`

Compact POST request SHA-256：`271642ad69f6a48eaa00984a73da6ac785fb168abd2ff8977e44d5af60789f7b`。初始 prompt id：`fcf5fbaf-d551-4d9e-bfb6-7fcbbae872fb`。只提交一次，没有 retry、fallback 或第二 seed。

## Runtime Receipt

- ComfyUI commit: `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`
- MiniMax H3 T8 plugin commit: `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`
- full-scene reference SHA-256: `a0eea9c27536c914c988e793682c21a2f31174df4ce39fb95861711180955336`
- identity crop SHA-256: `7e71030f3cad5e3049143be2169b5933711a80dbd277ea76025490b253dcafac`
- accepted chain Manifest SHA-256: `f08847e22d79e5b0711d2b73d71c10e07b227d6c37d490bca664d90f67e0f9e5`

成功接受 6 个 segments：`124 + 102 + 102 + 102 + 102 + 102 = 634` frames。segment 6 在 `1/20` sampling steps 时，承载 ComfyUI 的进程收到 `SIGTERM`，runner 返回 exit `143`。没有 segment 6 candidate 被接受；Manifest revision `6` 的最后 durable segment 为 index `5`。终止来源没有被当前证据识别为 user cancel、quality route-kill 或 model error，因此只分类为 infrastructure interruption，不猜测根因。

进程终止后：

- ComfyUI 不再监听 `127.0.0.1:8188`。
- `background_job.json` 遗留 `state=running`、`accepted_count=6`、`current_segment_index=6`、`retry_count=0`；这是失去 owner process 后的 stale state，不是 durable completion 或 cancellation truth。
- 因 frozen contract 为 retry 0，没有 restart、resume、补交或 fallback。

## Motion Measurements

沿用 E0-B 的 exact measurement：逐帧 resize 到 `336x192`、grayscale；相邻帧计算 mean absolute difference 与 Farneback optical flow，记录每对帧 magnitude median 的 segment mean。retention 始终使用本次新 segment 0 的 `1.2522561546` 作为 denominator。

| Segment | Frames | MAD mean | Median-flow mean | P90 | Retention vs segment 0 | Motion state |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 124 | 8.7722 | 1.2523 | 1.5623 | 1.0000 | steady |
| 1 | 102 | 13.2205 | 1.5312 | 2.1291 | 1.2228 | steady |
| 2 | 102 | 13.0761 | 1.3217 | 1.8740 | 1.0554 | steady |
| 3 | 102 | 10.0921 | 0.9854 | 1.3383 | 0.7869 | steady |
| 4 | 102 | 10.1038 | 0.8787 | 1.1840 | 0.7017 | steady |
| 5 | 102 | 10.5393 | 0.8172 | 1.1040 | 0.6526 | steady |

Frozen route-kill 要求 segment 1 和 segment 2 相对 segment 0 的 retention 均至少 `0.50`，同时存在可见 forward displacement。两段分别为 `1.2228` 和 `1.0554`，且采样帧显示人物从立柱区持续推进到扶梯和开放站厅，所以 early route-kill gate 通过。作为对照，E0-B segment 1 / 2 的 median-flow mean 只有 `0.1852` / `0.0348`。

后续 steady segments 出现 `0.7869 -> 0.7017 -> 0.6526` 的缓慢衰减，但没有重现 E0-B 在约 10--14 秒接近原地步态的 collapse。由于 segment 6 / 7 未接受，decelerate 与 stop schedule 没有 empirical result。

## Incremental Shot Analysis

生成后续 segments 的同时，对 durable accepted media 做了增量只读分析，而不是等到链尾：

- project-local `video-analysis` 对 634-frame exact partial 报告 `1344x768 @ 24fps`、H.264 High、AAC 32 kHz stereo、单一 scene、`859/859` sampled frames unique、`issues: []`。这些是 technical raw measurements，不拥有 semantic 或 Production verdict。
- 2 秒 contact sheet 显示同一 East Asian woman、short black bob、beige trench coat、red satchel、screen-right direction 与 railway-station architecture 持续稳定；背景从 concrete columns 推进到 departure display、escalator 和更开阔的 concourse，存在持续 forward displacement。
- 前五个 continuation seams 的逐帧 contact sheet 没有显示 hard cut、teleport、pose reset、方向反转或 fatal identity / wardrobe / satchel / scene regression。
- 单帧采样和自动指标不能证明完整 watchability、gait physics、prompt adherence、P6 或 Final Acceptance。

Exact incomplete preview：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0c_prompt_schedule_relay_v1_seed320001_20260824_INCOMPLETE_partial_634f_exact.mp4
```

- SHA-256: `1e7463ae607ecb53962cc810ddcb506ab6844b0e2a3623e45a60ecc569d24aac`
- video frames: `634`
- exact video span: `26.416667 s`
- container duration: `26.449 s`

该文件不是 32 秒成片，不得描述为完整 770-frame output。

## Root-Cause Hierarchy

1. **Strongest supported cause: repeated stop-oriented temporal semantics accelerated early settle.** 在 seed、reference、identity strategy、interval、context、steps、sampler、resolution 全部冻结时，只改变 per-segment temporal prompt allocation，segment 1 / 2 retention 从 E0-B 的约 `18.9%` / `3.6%` 提升到 `122.3%` / `105.5%`，并恢复可见空间推进。单 seed development evidence 支持“主要驱动”而不是普遍因果定律。
2. **Plausible secondary damping: persistent static-reference conditioning and/or latent-context gait loss.** steady segment retention 仍从 `1.2228` 缓慢下降到 `0.6526`。本实验没有分别改变 `ScenePlusIdentity + interval 1` 或 22-frame context，所以不能在二者之间归因。
3. **Not evaluated: near-end deceleration and stop controllability.** infrastructure interruption 发生在 segment 6 sampling early stage，未产生接受媒体；不能声称 schedule 已完成或结尾自然。

## Why E0-B STOP Is Unchanged

E0-B 的 exact bytes、328-frame partial、motion-collapse measurements 与 STOP verdict 都没有改变。E0-C 是新的单变量 development experiment：它提供了反事实 evidence，说明 E0-B 的 global prompt temporal allocation 是重要 root-cause surface，但没有让 E0-B output 变成合格成片，也没有重新分类作者的上游 EXP/default-off 路线。E0-C 自身也因 infrastructure interruption 没有完整 770-frame verdict。

## Effects

Repository effects：只新增本 record；没有 Production code、qualification contract、Manifest / Registry、canonical reference 或 Harness policy change。

Provider / media effects：一次 Local ComfyUI T8 submit；6 个 accepted segments、634-frame incomplete preview 和只读 analysis artifacts。remote submit `0`、paid effect `0`、fallback `0`、retry `0`。ComfyUI 已停止；server 不可达，不能声称 queue-empty receipt。

## Next One Thing

先做一次 bounded、read-only infrastructure interruption reassessment，确认 ComfyUI host process 为什么收到 `SIGTERM`，以及在不重解释 retry-0 contract 的前提下应如何处理 stale background state。只有形成新的明确授权/contract 后，才可决定是否从 accepted segment 5 继续相同 segment 6/7 schedule；不得 blind restart、把 resume 记作原实验无中断完成，或用另一 seed / 参数补考。

## Follow-up Engineering Closure: Cancelled Accepted-Prefix Composition

该 experiment 之后完成了一个 bounded local regression fix，目标不是重新生成或手工修复单个 E0-C artifact，而是关闭 cancelled/incomplete accepted prefix 绕过 canonical composer 的长期 routing 缺口。

人工预览此前直接拼接各 accepted segment 的 MP4/AAC，因此保留每段 AAC codec padding，并在 E0-C 的五个 segment seams 处报告可听断点。`long_video_delivery.py::compose_accepted_long_video()` 已经具备正确能力：按 Manifest absolute frame/sample boundaries 解码每段 exact PCM、丢弃 codec padding，并可用 `audio_seam_policy="cosine_bridge"` 与 `bridge_ms=5.0` 处理边界。缺失的是 cancelled background control path；它只 durable 写入 `cancelled` 后返回，没有把 non-final accepted Manifest prefix 送入该 composer。

MiniMax H3 T8 plugin local commit：

```text
5ad62dcefdb238cf4fb58711ea8107552392a71d Fix cancelled prefix composition routing
```

该 commit 的 exact implementation boundary：

- `long_video_routes.py` 在 `BACKGROUND_JOBS.cancel()` 返回后才读取 canonical accepted Manifest，保证 cancel transition 先 durable 完成。
- 仅 non-empty、non-final accepted prefix 自动调用 `compose_accepted_long_video()`；zero accepted 与 final chain 均不走 partial composition。
- 调用固定为 `require_final_segment=False`、`audio_seam_policy="cosine_bridge"`、`bridge_ms=5.0`，filename prefix 明确使用 `H3_Long_Video_Accepted_Prefix_Partial`。
- 成功 response 返回 `partial_preview_kind="accepted_prefix"`、`partial_video_path` 与 parsed `partial_compose_report`；失败返回 `partial_compose_error`，保持 durable `cancelled`，不 rollback cancel、不 retry/fallback generation。
- `long_video_delivery.py::compose_accepted_long_video()` 新增 backward-compatible、keyword-only `expected_manifest_revision`。Route 将第一次 non-final Manifest read 的 revision 传入 composer；composer 在自己的 authoritative Manifest load 后、创建 `assembled/` 或临时输出前 fail closed。这样关闭了两次 Manifest read 之间接受 final segment、再把完整链误命名为 partial 的 TOCTOU。
- 未传 `expected_manifest_revision` 的既有 callers 保持原行为；completed-chain `compose_when_complete` path、codec trimming、cosine bridge 算法、frame/sample accounting 与 BackgroundJobManager architecture 均未重写。

### Verification And Review

对 plugin commit 对应 tree 实际运行：

```text
PYTHONPATH=/home/reggie/ComfyUI PYTHONDONTWRITEBYTECODE=1 \
pytest -q -p no:cacheprovider \
  tests/test_long_video_routes.py \
  tests/test_long_video_background.py \
  tests/test_long_video_delivery.py \
  tests/test_preflight_and_registration.py
```

结果为 `79 passed`，另有 2 个既有 SWIG deprecation warnings。Focused coverage 包括：

- cancel 先于 compose；
- non-final accepted prefix 使用 exact partial composer options；
- zero accepted 与 final chain 不 compose；
- Manifest loader failure 与 composer failure 均保留 cancelled response，不 retry/fallback；
- Manifest revision mismatch 在任何 assembled output 写入前失败；
- existing exact frame/sample accounting 与 completed-chain composition tests 继续通过。

`ruff check`、focused `compileall` 与 `git diff --check` 均通过。Independent native review 首轮发现 Manifest TOCTOU 并给出 `reject`；加入 revision precondition 与 loader-failure coverage 后，同 tier scoped re-review 为 `accept`，无 blocking 或 non-blocking concern。

### Evidence And Publication Boundary

该 engineering closure 只存在于 MiniMax H3 T8 plugin local `main` commit `5ad62dc`；记录时相对 plugin `origin/main` 为 `ahead 1`，没有 push 或 release。Plugin checkout 在该 commit 之后已有其他 uncommitted work；这些后续 bytes 不属于 `5ad62dc`，本记录不认领也不用于上述 verification claim。

AI-VIDEO Production code、Manifest / Registry、qualification、Provider contract、seed、prompt schedule、identity strategy、resolution、steps 与 model 均未改变。没有重跑 seed `320001` 或其他 seed，没有启动模型 generation、remote/paid Provider、fallback 或 retry，也没有覆盖既有 v1/v2 media。

该 closure 是 engineering/runtime routing PASS，不是 empirical audio-quality PASS。现有 634-frame E0-C partial 没有因该 commit 自动重新合成；没有新的 full-speed listening evidence，不能声称五个 audible seams 已在该历史 artifact 上关闭，也不能把它升级为 770-frame / 32-second completion、P6 或 Final Acceptance。

### Updated Next One Thing

在下一次明确授权的 long-video execution 前，先让 ComfyUI 加载包含 `5ad62dc` 的 plugin build；首次发生 targeted cancel 时核对 response 中的 `partial_video_path`、`partial_compose_report`、Manifest revision 与 exact frame/sample totals，并对该新 partial 做人工听感检查。不得为验证本 routing fix 重跑 E0-C seed `320001`、补交 segments 6/7 或把历史 v2 rescue artifact 当作自动 route evidence。

## Follow-up Engineering Closure: Durable Supervision And Explicit Recovery

E0-C 的 `SIGTERM` 来源仍然未知；本次 closure 不把未知 termination 重新分类为已定位 root cause。它关闭的是两个可复用的 infrastructure hazards：Agent command lifecycle 持有 ComfyUI 长进程，以及 stale / unreadable `background_job.json` 可以在 read 或直接 requeue 时隐式改变 recovery truth。

AI-VIDEO local commit：

```text
f9b580d fix: supervise local ComfyUI lifecycle
```

该 commit 新增 `scripts/comfyui_supervisor.py` 并替换 `h3-video` skill 中的手工 `nohup` launcher：

- 每次 explicit `start` 创建不可复用的 `ai-video-comfyui-<32-lowercase-hex>.service` user-systemd transient unit，固定 `127.0.0.1`、`Restart=no` 与 journal output。
- User runtime advisory mutex 覆盖完整 preflight、`systemd-run`、health 与 final ownership confirmation；它只提供互斥，不保存 owner pointer 或第二套 job state。
- unit discovery 只接受 exact lowercase-hex namespace；多个 owner、已有 owner 或端口占用均 fail closed，`stop` 不使用 broad pattern。
- HTTP `/system_stats` 成功后仍必须确认同一 `InvocationID`、active state、positive `MainPID`，并从 `/proc/net/tcp` 与该 PID 的 fd table 证明 exact loopback listener ownership。
- post-creation failure 只清理本次 unique unit；若 `systemctl stop` 失败，则报告 cleanup unconfirmed 与 bounded detail，不把未知结果冒充 unit 已消失。
- `status` 与 `logs` 是只读 control；没有 auto-start、auto-restart、workflow submit、generation retry 或 stale-job recovery。

MiniMax H3 T8 plugin local commit：

```text
28cb160 fix: require explicit long-video recovery
```

该 commit 将 restart recovery 改为 explicit、fail-closed state transition：

- GET status 对 stale active 或 unreadable auxiliary state 只返回 ephemeral `detached` view 与 `recovery_persisted=false`，保持 `background_job.json` byte-exact。
- POST `recover` 在读取、quarantine 与写入期间持有 chain 的 OS advisory lease；另一 ComfyUI process 持有 lease 时，readable 与 unreadable 两种状态都拒绝 recovery 且不改 bytes。
- Recover 只持久化 `detached` classification；不 queue、release、compose、增加 retry 或改变 accepted Manifest truth。
- readable stale-active 与 unreadable state 都不能通过直接 requeue / `attach_prompt()` 绕过 Recover。Recover 成功后，用户才可 queue workflow once 重新附着 incomplete accepted Manifest，或对 complete Manifest 运行 Compose Accepted。
- 前端增加显式 Recover control，route 使用 `asyncio.to_thread()`，不会在 recover path 隐式调用 composer。

### Verification And Evidence

Plugin focused suite：

```text
PYTHONPATH=/home/reggie/ComfyUI python -m pytest -p no:cacheprovider \
  tests/test_long_video_background.py tests/test_long_video_routes.py \
  tests/test_preflight_and_registration.py -q
57 passed
```

AI-VIDEO parent focused verification 最终为 `193 passed`，覆盖 supervisor、Harness routing、Documentation Contract Gate 与 session-record hook；`python -m scripts.docs_contract_gate check`、read-only `python scripts/comfyui_supervisor.py status` 与 `git diff --check` 均通过。真实 status 为 inactive / not-found；本次没有启动或停止 ComfyUI。

Exact staged Harness receipt：

```text
.agent/harness/runs/20260824T114936417333Z/receipt.json
```

Receipt verification 报告 `passed=true`、`fresh=true`、`snapshot_matches=true`、`scope_paths_match=true`、`policy_matches=true`、`artifact_integrity=true`、`workspace_cleanup_confirmed=true`。同一 detached snapshot 中 `local_comfyui_supervisor_tests` 为 `16 passed`，`harness_tests` 为 `177 passed`；policy audit 无 unmapped、unverified、missing 或 unreferenced paths。

Independent `reviewer_xhigh` 多轮 review 先后拒绝了：unmapped Harness routing、跨进程 recovery lease 缺失、requeue bypass、可复用 systemd unit 的 stop race、宽松 unit namespace、并发 start、post-create cleanup leak 与共享-port health 误归属。Parent 随后补上 per-fd volatile `/proc` handling、direct inode/port fixture 与 typed mutex failure coverage，并重新运行上述 focused checks；reviewer 对 exact commit `f9b580d` 的最终 delta-only verdict 为 `accept`，无 blocking issue。

### MiniMax Diagnostic Capture

本轮 external MiniMax delegation 已由 automatic sanitized capture 保存：

```text
/home/reggie/.codex/session-diagnostics/minimax/01a03356-47e3-7780-ace7-b56ea5769dd2-35e25a9c7d181d56.md
```

Capture metadata：session `01a03356-47e3-7780-ace7-b56ea5769dd2`、fingerprint `35e25a9c7d181d56`、report schema `7`、malformed JSONL lines `0`。Terminal truth 将原始 subagent outcome 分开记录：

- read-only explorer 首次 invocation 为 transport `1`、CLI `0`、`dialogue_protocol_error` / `PROTOCOL_ERROR`，没有 evidence 或 blocker claim。
- 修正 dialogue 后的两次 read-only explorer invocation 均为 transport `0`、CLI `0`、`DONE_WITH_CONCERNS`；concerns 分别覆盖 architecture uncertainty、evidence gap 与 test gap，没有 blocker。它们只提供 code mapping / hypothesis evidence，不拥有最终实现决定。
- safe-edit writer invocation 为 transport `1`、CLI `-9`、`tool_error_loop` / `BLOCKED`，blocker 为 `permission_denial_loop`；没有 evidence，也没有修改文件。
- bounded fresh retry 在 backend 前被 `runner_validation` 拒绝，未获得新的 agent outcome，也没有修改文件。最终 implementation、verification、commits 与 reviewer acceptance 均由 parent / native reviewer 完成。

该 capture 省略 raw prompts、exact commands、Provider result prose、environment values 与 credentials。它证明 delegation transport/status 与 failure classification，不证明 code correctness、Harness PASS、ComfyUI runtime readiness、媒体质量或 E0-C completion；这些 truth 仍分别由 exact commits、tests、Harness receipts、read-only runtime status 与既有 empirical evidence 所有。

### Publication And Acceptance Boundary

两个 commit 都只存在于本机 `main`；没有 push、release 或 remote deployment。`index.json` 与 AI-VIDEO checkout 中其他 unrelated dirty changes均未 stage、commit、reset 或覆盖。

本 closure 是 engineering lifecycle / recovery PASS，不是 E0-C empirical completion。没有补交 segment 6/7、没有 generation、retry、fallback、remote/paid Provider 或新媒体，也没有改变 634-frame partial、Manifest revision 6、P6 或 Final Acceptance truth。下一次继续 E0-C 仍需要新的明确 execution authorization，并必须把 historical infrastructure interruption 与新的 resumed attempt 分开记录。
