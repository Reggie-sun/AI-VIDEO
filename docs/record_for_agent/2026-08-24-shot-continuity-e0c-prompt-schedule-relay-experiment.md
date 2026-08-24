# Shot Continuity E0-C Prompt-Schedule Relay Development Experiment

## Status

- `experiment_id`: `shot_continuity_e0c_prompt_schedule_relay_v1`
- `classification`: `development_experiment`
- `execution_status`: `COMPLETED_RESUMED_ATTEMPT_AFTER_EXPLICIT_RECOVERY`
- `empirical_status`: `HUMAN_REJECT_STOP`; full 770-frame schedule completed and motion preservation improved, but final stop adherence failed and seam pulses remain measurable
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

## Original Interrupted Attempt Runtime Receipt

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

## Original Interrupted Attempt Shot Analysis

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

## Original Interrupted Attempt Effects

Repository effects：只新增本 record；没有 Production code、qualification contract、Manifest / Registry、canonical reference 或 Harness policy change。

Provider / media effects：一次 Local ComfyUI T8 submit；6 个 accepted segments、634-frame incomplete preview 和只读 analysis artifacts。remote submit `0`、paid effect `0`、fallback `0`、retry `0`。ComfyUI 已停止；server 不可达，不能声称 queue-empty receipt。

## Historical Next One Thing (Completed)

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

通用 ComfyUI lifecycle、user-systemd supervision、stale / unreadable `background_job.json` 与 explicit Recover contract 已迁移到独立记录：[`2026-08-24-comfyui-supervision-and-explicit-background-recovery.md`](2026-08-24-comfyui-supervision-and-explicit-background-recovery.md)。

对 E0-C 而言，`SIGTERM` 来源仍然未知；该 engineering closure 记录时没有补交 segment 6/7、generation、retry、fallback、remote/paid Provider 或新媒体，也没有改变 634-frame partial、Manifest revision 6、P6 或 Final Acceptance truth。随后获得的新 execution authorization 与 resumed attempt 证据记录如下；它不回写或抹除 historical infrastructure interruption。

## Resumed Attempt Completion

2026-08-24 的新用户授权允许继续同一 Local T8 chain。执行前重新验证 exact request bytes、accepted Manifest revision `6`、segment `5` context、ComfyUI/plugin commits 与 empty queue。没有重新生成 segments `0..5`，也没有将 resume 伪装成原始 submit 从未中断。

恢复过程使用已实现的 explicit recovery contract：

- ComfyUI commit: `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`
- MiniMax H3 T8 plugin commit: `28cb160827c245b2d6a37539df30c1d7c5e7aecd`
- supervised unit: `ai-video-comfyui-782ca50952d940a59ff413af1d917414.service`
- supervisor invocation id: `b24a6450d8a8450fbafe0e9b22b71f3b`
- recovered background job id: `ef160057-95e4-41e1-b21d-02e7f1286575`
- resumed segment 6 prompt id: `47be3a14-45f2-4862-9f7d-64a90934319f`
- auto-queued segment 7 prompt id: `659a5000-414e-48a0-b8b5-f747ed69d734`

先将 stale state 显式转换为 durable `detached` recovery state，再对 exact frozen request 做唯一一次新 submit。segment 6 接受后只由 existing background orchestrator 自动排入 segment 7。最终 `background_job.json` 为 `state=completed`、`accepted_count=8`、`retry_count=0`、`last_error=""`；queue 在验证时为 running `0` / pending `0`。没有 second manual submit、retry、fallback、parallel execution、remote 或 paid effect。验证完成后通过 supervisor 显式停止 ComfyUI，unit 为 `inactive`，`127.0.0.1:8188` 不再监听。

## Completed Media Evidence

Canonical assembled development artifact：

```text
/home/reggie/ComfyUI/output/minimax_h3_t8_long_video/shot_continuity_e0c_prompt_schedule_relay_v1_seed320001_20260824/assembled/development_experiment_shot_continuity_e0c_prompt_schedule_relay_62f0f369564f_r0008_cosine_bridge.mp4
```

- final MP4 SHA-256: `907757a3b0b8f1da71d4a5d2237cd6dc8804f1445f06215014e1aa42a368a047`
- final Manifest SHA-256: `71ac60ad466ece4d94b591e98213c1c4588f4932039ea31301416d8e7889cf31`
- Manifest revision: `8`
- accepted frames: `124 + 102 + 102 + 102 + 102 + 102 + 102 + 34 = 770`
- video: H.264 High、`1344x768`、24 fps、exact `770` frames、`32.083333 s`
- audio: AAC、32 kHz、stereo；Manifest PCM boundary 为 exact `1,026,667` samples，container duration `32.084 s`
- file size: `18,675,848` bytes
- segment 6 video SHA-256: `7b6937d3207d8e46a40d6a33118344ca7e533f8ff0dcd0fbd88e705cc7c84f8a`
- segment 6 context SHA-256: `ff927420593a4593b126b444c50c0af89f7fa78d9c57791b23ca5990f8fa7ce1`
- segment 7 video SHA-256: `cc407f3acbddc07d7a1d25bba14ecc3bc54e3c0dd45699fd3aaeebc49675c63e`

所有 8 个 accepted MP4 与 7 个 non-final context artifacts 均按 Manifest SHA-256 重新校验通过。`ffmpeg` 对 final video/audio 的完整 decode 通过。Project-local `video-analysis` 确认 `770` frames、单一 scene、audio present；这些是 technical evidence，不是 P6 或 human acceptance。

## Full-Schedule Motion And Seam Assessment

沿用前述 exact Farneback measurement，新增 segments 6 / 7：

| Segment | Frames | MAD mean | Median-flow mean | P90 | Retention vs segment 0 | Scheduled state |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6 | 102 | 11.8131 | 0.7882 | 1.0887 | 0.6294 | decelerate |
| 7 | 34 | 11.5088 | 0.7330 | 0.9736 | 0.5853 | stop |

完整链的 segment retention 约为 `1.0000 -> 1.2228 -> 1.0554 -> 0.7869 -> 0.7017 -> 0.6526 -> 0.6294 -> 0.5853`。因此 per-segment prompt schedule relay 明显避免了 E0-B 在 segments 1 / 2 的急剧 motion collapse，并将可见 forward gait 保持到 32 秒附近。

但 near-end control 没有按 prompt 完成：segment 6 的最后三分之一 flow 没有下降，segment 7 的三个 thirds 为约 `0.703 -> 0.722 -> 0.775`；最后 10 个 frame-pair flow 仍呈步态式交替。0.5 秒采样 strip 显示人物在 final frame 仍向 screen-right 跨步，未形成 one natural stop。结论必须拆开：

- motion-preservation hypothesis: `PASS` for this single-seed development experiment；
- full temporal schedule / final-stop adherence: `FAIL`；
- Production qualification、P6、Final Acceptance: not evaluated and not authorized。

用户随后完成 human review，并明确判定“最后没有停下来”不可接受。因此该 exact 770-frame development candidate 的 human verdict 为 `REJECT / STOP`。这个 verdict 不撤销 motion-preservation 子假设的 evidence，但禁止把完整 Shot 描述为 creative PASS、可交付成片或 Final Acceptance output。

7 个 visual seam 的 boundary frame-pair 相对局部 median motion/MAD 仍高约 `1.28--1.45x` / `1.34--1.47x`。Project-local scene detection 没有把它们判为 hard cut，逐 seam frame pairs 也保持 identity、wardrobe、satchel、scene 与 screen direction；但 17.9167 s、22.1667 s、26.4167 s 与 30.6667 s 仍有可量化 motion pulse，不能声称 visual seams 已消失。

`cosine_bridge` 明显降低了音频边界的单样本 discontinuity：7 个 seam 的 decoded single-sample step 均不高于局部常态，后四个只处于局部 derivative 的约 `2--9` percentile。但 20 ms seam 前后 RMS 仍改变约 `1.2--1.56x`，说明 bridge 去除了 click，却没有统一各 segment 的 ambience texture / loudness；人工仍可能听出段落变化。

## Resumed Attempt Effects And Next One Thing

Repository effect：只更新本 experiment record；没有 Production code、qualification contract、Manifest / Registry、canonical reference、Harness policy、push 或 release change。E0-B 的 exact partial、measurements 与 `STOP` verdict 不变；E0-C resumed attempt 是独立的新 runtime evidence。

Provider / media effect：一次 explicit Local ComfyUI resumed submit，接受 segments 6 / 7 并生成一个完整 770-frame development artifact；remote submit `0`、paid effect `0`、fallback `0`、retry `0`。它不是 activated Production candidate 或 Final Acceptance output。

Next One Thing：若继续实验，只冻结一个仍属于 `prompt_temporal_allocation` 的后续合同——把 decelerate / stop conditioning 提前，使 stop state 不再只获得最后 34 frames，并让 final segment 表达 settled hold；seed、reference strategy、interval、context、steps、resolution、sampler 与其他 surfaces 全部保持不变。在获得新的 execution authorization 前不重跑，也不把 motion-preservation `PASS` 扩写成整条 Shot `PASS`。
