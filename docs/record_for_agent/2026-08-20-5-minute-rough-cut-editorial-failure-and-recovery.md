# Five-Minute Rough-Cut Editorial Failure And Recovery Record

Date: 2026-08-20

## Purpose

本文记录 `Relay Seven` 五分钟 rough-cut reality-validation run 的实际失败、Creative Skill 使用边界、媒体与 Manifest truth、一次中断后的 explicit recovery，以及后续 Agent 必须执行的 editorial gates。

这是一份 failed-run / recovery record，不是完成证明，也不授权继续 local generation、remote/paid Provider、重新渲染、自动 recovery、质量验收、push 或 release。当前代码、Manifest、registered artifacts 与重新核对的媒体 bytes 仍是 source of truth；session handoff 只作为辅助上下文。

## Current Runtime Truth

Execution contract 与 run：

- Plan: `docs/superpowers/plans/2026-08-20-ai-video-5-minute-rough-cut-reality-validation.md`
- Run root: `runs/5min-rough-cut-20260820T100302Z-v1`
- Story: `Relay Seven`
- Active Shots: `36`
- Active strategy distribution: `33 static_image / 3 generated_video`
- Plan target: 约 `20 static_image / 16 generated_video`

Active Project 中的 36 个 exact Shot artifact paths 重新计数后确认上述 `33/3` 分布。当前没有 verified Provider failure、accepted story revision 或 documented editorial decision 可以解释这次大幅偏离；它不能被描述为 plan 允许的正常节奏调整。

停止时 Manifest revision 为 `68`：

- Active Project revision `5`: `d24e646cefeff06cbbdc6a3b0ef83682b170156c0ebcdf889a991109a3677c18`
- Active Registry: `dfd839ff0de3e5a68c751791e7325561012ae77aa11d1336adab59220bed6bf5`
- Active Dependency Graph: `87bed7865922b7ce0ad872f8512cb8860ecff44c77597093581df2aa3cea31d8`
- Active Render State: `2697b6cef1fd5dc3fd16f0f58680142387bfc520f4c1797ed6ece388370aae40`
- `final_acceptance_state`: `null`

不存在以下 final-delivery artifacts：

- `runs/5min-rough-cut-20260820T100302Z-v1/deliverables/final.mp4`
- `runs/5min-rough-cut-20260820T100302Z-v1/evidence/reality-validation-report.md`
- `runs/5min-rough-cut-20260820T100302Z-v1/evidence/reality-validation-report.json`

因此该 run 的唯一正确状态是 **REJECTED / INCOMPLETE**。

## Media Artifact Layers

### First complete rough cut

```text
runs/5min-rough-cut-20260820T100302Z-v1/deliverables/first-complete-rough-cut.mp4
SHA-256: 46ffac5ab4d7b4dde9ae22c31c5b928d02a3c0b184b33549be9dc650bfaa7d62
```

该版本实现了从 0 秒到约 300 秒的画面、P4 audio 与 captions technical composition，但不是 subjective quality acceptance。

### Caption repair derivative

```text
runs/5min-rough-cut-20260820T100302Z-v1/deliverables/caption-repaired-rough-cut-v2.mp4
SHA-256: 05fac28f9b59178106def9e27e092bd8d3473285e09e738a7f8f7e3393836b3c
```

一次真实 P6 repair 关闭了 `caption-debug-banner-occlusion`，layout review 变为 PASS。这个 repair 只证明 caption layout closure，不证明 character identity、shot variation、motion、pacing、story 或 full-watch acceptance。

### Current rejected candidate

```text
runs/5min-rough-cut-20260820T100302Z-v1/deliverables/final-candidate.mp4
SHA-256: 7ecd93eda1b281c36b7ae131eb7ab91f2cd5e21e6577057c4004bbe6fc0ca90b
```

本轮重新执行 `sha256sum` 与 `ffprobe` 得到：

- H.264, `1344x672`, 24 fps, 7200 frames
- duration: `300.022` seconds
- AAC, 48 kHz, stereo
- size: `21,267,656` bytes

它是 current render candidate，不是 `final.mp4`，也没有 Final Acceptance。

## Stale Analysis Evidence Boundary

现有文件：

```text
runs/5min-rough-cut-20260820T100302Z-v1/evidence/video-analysis-final.json
```

内部明确绑定：

```text
render_sha256: f37e6e153938b48c6e58be44e3daaf7fa1d63530a5155d7818f70003da5000dc
```

它对旧候选报告：

- `scene_count=1`
- `static_visuals`, severity `high`
- sampled frame unique ratio `0.481`

当前 candidate SHA 已变为 `7ecd93...`，所以该 analysis 不能作为 current candidate 的 fresh evidence。`evidence/final-contact-sheet.jpg` 与该 analysis 均创建于当前 candidate 之前，且没有 exact hash binding 证明它属于 `7ecd93...`；它只能说明早期候选曾出现大面积重复和 black-haired/helmet character identity jump。

本 record 没有为了补齐文档而重新运行 `video-analysis`、生成 contact sheet 或进行新的媒体派生。因此 current candidate 仍缺 fresh semantic/subjective evidence，这本身就是 rejection boundary，而不是可以忽略的文档缺口。

## Creative Skill Usage And Why It Was Insufficient

本次创作阶段实际使用了用户指定的三个 advisory Skills：

1. `hell-grind-aigc-skill`：建立 relay oxidation -> open -> clean/reseat -> frequency restore 的 semantic Shot progression，以及 outfit、toolbox、axis、light、environment continuity locks。
2. `higgsfield`：在 semantic intent 确立后适配 Local MiniMax H3 I2V prompt/mode guidance。
3. `video-shotcraft`：提供 pacing、camera/motion、transition、SFX 与 static/action beat guidance。

调用 Skill 本身不是失败点；失败发生在把 authoring guidance 外推成了 reference quality 和成片可看性保证。External Skills 没有、也不应拥有 Character/Scene/Shot truth、Asset Registry、Manifest、Provider lifecycle、`ResolvedTimeline`、HyperFrames 或 Final Acceptance。

本次没有把以下已有要求落成 bulk-generation 前的 hard gate：

- `docs/record_for_agent/2026-08-20-minimax-h3-quality-profile-and-alice-ab.md` 要求 quality profile 与 native high-resolution provenance reference 配套，并先验证 representative variation。
- `docs/record_for_agent/2026-08-20-h3-shot-continuity-and-vscode-playback.md` 明确 technical continuity/playability 不等于 subjective acceptance。
- `docs/record_for_agent/2026-08-20-seedance-synthetic-continuity-and-skill-preflight.md` 明确 Skill 只负责 authoring guidance，quality gate 必须独立存在。
- Execution plan Milestone 1 要求先锁定合格 Character/Scene Reference Pack；Milestone 4 要求 representative sequence 通过后再以 4～6 Shots 为一批推进。

这些 records 并非没有提供经验；实际问题是本次 execution 没有按它们设置 stop gate。后续不得用“已经调用 Skill”或“已有 continuity proof”代替 reference inspection、bounded-batch review 与 full-watch acceptance。

## Local H3 Evidence

本 run 中成功的 Local H3 generations 恰好为 3 次，分别属于 Shots 013–015；`evidence/h3-three-shot-chain.json` 记录 `remote_calls=0`：

```text
shot-013: c180352359caf55b68283bce6ffd10acef956ee5209bf6a6cbbb03addfcff54f
shot-014: c8bebaa87d2209de5dafdd7649857b487f2a82be1201bc29bb384abd50bda615
shot-015: 6d7596e7ceb34523d2bd8214f4d732069ab2c0e0f3afc7cd456d86218a36e2d5
```

这三镜证明 bounded local generation、registered video assets 与 three-Shot technical chain 可以进入 composition。它不证明全片 identity continuity，也不支持把其余 33 个 Shots 留在高度重复的 static lane。

## Interrupted Image Attempt And Recovery

在用户要求停止时，representative Qwen keyframe lane 的第一个 request 已进入 loopback ComfyUI poll。Client 被中断后，本 session 通过 `ProductionStateCommitter.recover()` 将 Manifest 从 revision 67 推进到 68，并保留以下 fail-closed truth：

```text
attempt_id: relay-seven-representative-keyframe-shot-001
operation: image_generation
status: outcome_unknown
image_phase: submit_intent
error_code: image_provider_outcome_unknown
finished_at: 2026-08-20T12:48:06.647451+00:00
provider_request_id: null
provider_task_id: null
```

ComfyUI server log 随后显示 queued prompt 在 external execution side 完成，但 AI-VIDEO 没有 durable result、registered image asset 或 activation。该结果只能视为 unresolved external/orphan outcome；不得通过寻找 ComfyUI 输出文件把它手工升级为 P7 success，也不得 blind retry。

ComfyUI 已停止，停止检查没有发现该 server 或 `generate_representative_keyframes.py` 的残留进程。本 record 没有重新启动它们。

## Harness And Editorial Gate Separation

Commit `54f93e9 feat: add canonical production bootstrap` 是独立的 engineering checkpoint。Receipt：

```text
.agent/harness/runs/bootstrap-20260820-r2/receipt.json
```

Receipt `status=passed`、`closure_eligible=true`，其中 `production_contract_tests` log 为 `2208 passed, 3 skipped, 166 deselected`。这证明 exact committed bootstrap/code snapshot 的 policy checks；不证明 rough cut 的角色一致性、镜头变化、节奏、故事可读性或 human acceptance。

后续必须保留两套不能互相替代的 gates：

1. Code/state correctness: focused tests + exact staged/commit-range Harness receipt。
2. Media/editorial acceptance: native references、representative keyframes、4～6 Shot batch review、current-byte contact sheet/analysis、三次 full-watch 与 explicit Final Acceptance。

Harness 对工程闭环仍然必要；本次错误是将其证据边界外推，而不是 Harness 本身证明了错误的媒体质量。

## Git And Publication State

写 record 前重新检查：

- Branch: `main`
- HEAD: `54f93e9`
- Local branch: `ahead 15` relative to `origin/main`
- Initial staged paths: none
- Dirty paths included `.agent/context/session-handoff.md`, `.codex/config.toml`, seven tracked source/test files, and untracked `index.json`
- 在 record checkpoint 前的第二次 gate 中，`.codex/config.toml` 已由另一个 actor 出现在 staged index；本 record 未读取、修改、unstage 或认领它，并要求使用 path-limited commit 保留其 index state。

本 record 不认领、不检查、不修改、不 stage 上述 unrelated paths。当前 source/test changes 没有被本 record 转换成 completed implementation truth，也没有新的 full test 或 Harness receipt。没有 push 或 release。

## Assessment

本次 run 证明 Production contracts 可以组合出 300 秒、带画面、P4 audio 与 captions 的 technical artifact，也证明 caption defect 可以经 P6 selective repair 闭环。但它没有完成计划要求的现实验证，因为：

1. `33 static / 3 generated` 破坏了预期 visual variation。
2. Character/Scene references 没有在 bulk composition 前达到 native, inspected, production-ready quality。
3. Three-Shot technical continuity 被错误外推为全片 identity/editorial confidence。
4. Representative sequence 与 4～6 Shot batch stop gates 没有执行。
5. 当前 rerender candidate 缺与 exact bytes 匹配的 fresh analysis/contact sheet/full-watch evidence。
6. User-visible quality failure出现后，candidate 没有被错误升级为 Final Acceptance；这一 fail-closed boundary必须保留。

## Remaining Risks Or Next Work

只有用户未来明确恢复本任务后，才可以继续。推荐顺序：

1. 保留当前 run 为 rejected diagnostic evidence；不要覆盖、删除或 promote `final-candidate.mp4`。
2. 对 `relay-seven-representative-keyframe-shot-001` 做 explicit outcome reconciliation；无法建立 canonical exact-result evidence时保持 `outcome_unknown`。
3. 重新建立 native Character/Scene Reference Pack，并先人工检查 Shots 001/007/019/031 的四张 representative keyframes。
4. 四张 keyframes 未通过 identity、scene、composition 与 variation gate时，不进入 video bulk generation。
5. 恢复约 `20 static / 16 generated` 的 shot plan；代表 sequence通过后每批仅推进 4～6 Shots。
6. 每个 batch 检查 identity、continuity、motion、variation、pacing、caption readability与 source quality，不等到 final render 后集中发现。
7. 对最终 exact candidate bytes重新生成 hash-bound `ffprobe`、project-local `video-analysis` 和 contact sheet，并完成 story/continuity/system 三次 full-watch。
8. 只有 P6 repair closure 和 explicit Final Acceptance 都通过，才创建 `deliverables/final.mp4` 与 reality-validation report。

## Agent Guardrails

- `Skill used` 不等于 `reference accepted`、`candidate reviewed` 或 `final quality accepted`。
- `technical continuity` 不等于 `character identity continuity` 或 `editorial continuity`。
- `300-second playable MP4` 不等于 `watchable rough cut`。
- `caption layout PASS` 不等于 visual/story PASS。
- Analysis/contact sheet 必须绑定 current exact render SHA；stale evidence不得沿文件名复用。
- `outcome_unknown` 必须 explicit reconcile，不能 blind retry、猜测 external result或手工 activation。
- Harness receipt 只证明对应 code snapshot；不得用它替代 human/media acceptance。
- 本 record 不授权新的 Provider submit、generation、render、benchmark、push 或 release。
