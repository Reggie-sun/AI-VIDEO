# AI-VIDEO Session Handoff

Date: 2026-08-20

## Stop Reason

用户明确要求“先别做了”，本 session 已停止继续生产、修图、生成、渲染、Provider 调用和质量验收。本文件只记录当前 verified truth，不能作为继续执行、重新提交或付费调用的授权。

当前 5 分钟 rough cut 必须按 **REJECTED / INCOMPLETE** 处理。虽然存在可播放的 300 秒候选文件，但它在角色 identity、镜头变化和整体观看体验上不合格；没有 `final.mp4`、没有 `FinalAcceptanceReceipt`、没有 reality-validation report，也没有任何 final-delivery 或 quality-acceptance truth。

## Repository And Git State

- Repository: `/home/reggie/vscode_folder/AI-VIDEO`
- Branch: `main`
- Pause 前 HEAD: `54f93e9 feat: add canonical production bootstrap`
- Local branch 在写 handoff 前为 `main...origin/main [ahead 15]`；没有 push 或 release。
- 已提交 checkpoint `54f93e9` 增加 canonical `ProductionStateCommitter.bootstrap_initial_state()`。
- Bootstrap checkpoint receipt: `.agent/harness/runs/bootstrap-20260820-r2/receipt.json`；该 checkpoint 的完整 suite 为 `2208 passed`。它只证明对应代码/state contract，不证明视频主观质量。
- 当前另有 7 个 tracked source/test files 的未提交变更和 untracked `index.json`。handoff 写入后的复核中，`.codex/config.toml` 还新出现为 modified；它不是本 session 的 change，ownership 未知，未检查、修改或 stage。上述文件均未因 handoff 被 reset、覆盖、stage 或清理。
- `index.json` 不属于本 task，后续不得顺手 stage 或 commit。

## Plan And Run

- Execution plan: `docs/superpowers/plans/2026-08-20-ai-video-5-minute-rough-cut-reality-validation.md`
- Run root: `runs/5min-rough-cut-20260820T100302Z-v1`
- Story: `Relay Seven`，36 Shots / 300 seconds。主角 Elias 在暴风雨中修复 emergency relay，Mira 只通过 radio 出现。
- 实际 visual strategy distribution: `33 static_image / 3 generated_video`。
- Plan 的 planning target 是约 `20 static_image / 16 generated_video`。本 session 没有真实 Provider failure 或 accepted editorial decision 支持偏离到 `33/3`，这是本次观看失败的核心原因之一。
- Voice 使用 local `espeak-ng` 生成并以 mono PCM s16 48 kHz import；HyperFrames 最终混成 AAC 48 kHz stereo。项目包含 36 条 captions。

## Creative Skill Usage And Failure Boundary

本 session 实际调用并使用了用户指定的三个 advisory Skills：

1. `hell-grind-aigc-skill`：建立 relay oxidation -> open -> clean/reseat -> frequency restore 的 Shot state progression，并定义 outfit、toolbox、axis、light、environment 等 continuity locks。
2. `higgsfield`：把已经建立的 semantic intent 适配为 Local MiniMax H3 I2V prompt/mode guidance。
3. `video-shotcraft`：提供 pacing、camera/motion、transition、SFX 和 static/action beat 的建议。

Skills 的使用不能代替 reference quality、candidate inspection、batch QA 或 Production acceptance。真正失败在执行层：本 session 把 advisory prompt/continuity work 当成足够保障，却没有先完成 native high-resolution Character/Scene Reference Pack，也没有在 representative variation 通过后再按 4～6 Shots 批量推进。

与已有 durable records 的冲突必须保留为后续 guardrail：

- `docs/record_for_agent/2026-08-20-minimax-h3-quality-profile-and-alice-ab.md` 要求 quality profile 与 native high-resolution provenance reference 配套，并先做 representative variation。
- `docs/record_for_agent/2026-08-20-h3-shot-continuity-and-vscode-playback.md` 明确 technical continuity/playability 不等于 subjective acceptance。
- `docs/record_for_agent/2026-08-20-seedance-synthetic-continuity-and-skill-preflight.md` 明确 Skill 只负责 authoring guidance，quality gates 必须独立执行。

这些记录当时可用，但本 session 没有把它们落实为 rough-cut 批量生产前的 hard editorial gate。后续不得仅以“已经使用 Skill”作为可看性证据。

## Media Produced And Current Assessment

### Local H3 three-Shot chain

Local H3 成功调用恰好 3 次，每个 Shot 一次；exact replay 新增调用为 0，remote/paid Provider 调用为 0。

- Shot 013 MP4 SHA-256: `c180352359caf55b68283bce6ffd10acef956ee5209bf6a6cbbb03addfcff54f`
- Shot 014 MP4 SHA-256: `c8bebaa87d2209de5dafdd7649857b487f2a82be1201bc29bb384abd50bda615`
- Shot 015 MP4 SHA-256: `6d7596e7ceb34523d2bd8214f4d732069ab2c0e0f3afc7cd456d86218a36e2d5`
- Chain evidence: `runs/5min-rough-cut-20260820T100302Z-v1/evidence/h3-three-shot-chain.json`
- Contact sheet: `runs/5min-rough-cut-20260820T100302Z-v1/evidence/h3-chain-contact-sheet.jpg`

这三镜内部的桌面、人物、道具和动作连续性基本成立，但它们使用的蓝衬衫/金属头盔人物与全片主要 black-haired/charcoal-coat Elias reference 不一致。因此 chain 的 technical continuity 不能证明全片 character identity continuity。

### First cut and caption repair

- First complete rough cut SHA-256: `46ffac5ab4d7b4dde9ae22c31c5b928d02a3c0b184b33549be9dc650bfaa7d62`
- First-cut copy: `runs/5min-rough-cut-20260820T100302Z-v1/deliverables/first-complete-rough-cut.mp4`
- Caption-repaired copy: `runs/5min-rough-cut-20260820T100302Z-v1/deliverables/caption-repaired-rough-cut-v2.mp4`
- Caption-repaired SHA-256: `05fac28f9b59178106def9e27e092bd8d3473285e09e738a7f8f7e3393836b3c`

一次真实 P6 layout repair 关闭了 `caption-debug-banner-occlusion`，layout review 变为 PASS。该修复只解决字幕布局，不解决画面 identity、repetition 或 editorial quality。

### Rejected current candidate

为减少 helmet persona 与 black-haired Elias 的交替，本 session 通过 canonical Project revision + P5 graph，把 18 个 Qwen/helmet Shots 绑定替换为已有 flux/black-haired assets，并重新渲染。这个 repair 没有 Provider 调用，但只是把 identity jump 替换成更严重的重复画面，仍不可接受。

- Current candidate: `runs/5min-rough-cut-20260820T100302Z-v1/deliverables/final-candidate.mp4`
- SHA-256: `7ecd93eda1b281c36b7ae131eb7ab91f2cd5e21e6577057c4004bbe6fc0ca90b`
- Measured media: H.264, `1344x672`, 24 fps, 7200 frames, 300.022 seconds; AAC, 48 kHz, stereo; 21,267,656 bytes.
- Active render output: `runs/5min-rough-cut-20260820T100302Z-v1/state/render/outputs/7ecd93eda1b281c36b7ae131eb7ab91f2cd5e21e6577057c4004bbe6fc0ca90b.mp4`
- Active render state: `state/render/states/2697b6cef1fd5dc3fd16f0f58680142387bfc520f4c1797ed6ece388370aae40.json`
- Contact sheet: `runs/5min-rough-cut-20260820T100302Z-v1/evidence/final-contact-sheet.jpg`
- Project-local analysis: `runs/5min-rough-cut-20260820T100302Z-v1/evidence/video-analysis-final.json`

`video-analysis` 报告 `scene_count=1` / `static_visuals`，contact sheet 直接显示大面积重复和 character identity 切换。这个 candidate 只能作为 rejected diagnostic artifact，不能改名或复制为 `final.mp4`。

## Current Canonical Run State

停止时 Manifest truth：

- Manifest revision: `68`
- Active Project: revision `5`, content hash `d24e646cefeff06cbbdc6a3b0ef83682b170156c0ebcdf889a991109a3677c18`
- Active Registry content hash: `dfd839ff0de3e5a68c751791e7325561012ae77aa11d1336adab59220bed6bf5`
- Active Dependency Graph content hash: `87bed7865922b7ce0ad872f8512cb8860ecff44c77597093581df2aa3cea31d8`
- Active Render State content hash: `2697b6cef1fd5dc3fd16f0f58680142387bfc520f4c1797ed6ece388370aae40`
- `final_acceptance_state`: `null`
- `deliverables/final.mp4`: absent
- `evidence/reality-validation-report.md`: absent
- `evidence/reality-validation-report.json`: absent

## Interrupted Qwen Attempt

为纠正 reference/identity 问题，本 session 创建了 run-local `generate_representative_keyframes.py`，计划先为 Shots 001/007/019/031 生成 4 张 native `1344x672` representative Qwen keyframes。用户要求停止时，第一个 Shot 已经提交到 loopback ComfyUI，client 正在 poll。

本 session 中断 client 后显式调用 `ProductionStateCommitter.recover()`；Manifest 从 revision 67 前进到 68，并将 attempt fail closed 为：

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

ComfyUI server log 后续显示该 queued prompt 在外部执行端以 `149.92 seconds` 完成，但 AI-VIDEO client 已中断，没有 durable Provider result、registered image asset 或 activation。该结果只能视为未对账的 external/orphan outcome。不得搜索到一张输出图片后手工冒充 P7 success，也不得 blind retry 同一 attempt。

ComfyUI 已收到 Ctrl-C 并输出 `Stopped server`；PID `1860305` 已退出。停止时没有 `generate_representative_keyframes.py` 或该 loopback ComfyUI server 的残留进程。

## Tracked Code Changes Not Yet Checkpointed

以下 7 个 files 当前合计约 `445 insertions / 10 deletions`，均未 commit，且没有为这组 exact changes 生成 final Harness receipt：

- `src/ai_video/production/project.py`: 允许多个 caption bindings 共享完全相同的 style path；其他 duplicate/conflicting render sources 仍 fail closed。
- `tests/test_production_project.py`: shared-caption regression 与 graph-only transition historical-origin regression。
- `src/ai_video/production/hyperframes.py`: 从 registered caption style 消费 font/text/outline/background/top 等 style，而不是 hardcoded cyan；保留 legacy audit compatibility。
- `tests/test_production_hyperframes.py`: current style 与两个 legacy audit cases。
- `src/ai_video/production/_state_commit_bootstrap.py`: 新增 monotonic `upgrade_manifest_schema(target_schema_version, expected_manifest_revision)`，覆盖 2.0–2.8、exact replay、strict reopen 和 downgrade/unsupported rejection。
- `tests/test_production_state_commit.py`: schema-upgrade regression。
- `src/ai_video/production/_project_dependency_evidence.py`: `historical_origin_graph_pointer` 只接受与 evidence pointer/base project 对齐且 candidate project revision 真正前进的 succeeded attempt，避免 graph/render-only transition 产生 ambiguous historical origin。

已执行但不足以替代 final Harness 的 focused verification：

- Caption style focused tests: `3 passed`。
- Manifest schema upgrade regression: `1 passed`。
- Historical-origin regression + existing P8 E2E: `2 passed`。
- 当前未提交 change 没有 independent final review，也没有 exact staged-snapshot Harness receipt。

后续继续代码 lane 前必须先 inspect current diff 和 ownership，不能假定这些 changes 已完成或可以直接提交。

## Harness Assessment

Harness 仍然必要，它验证 exact snapshot、policy routing、tests、Architecture Gate、artifact integrity 和 workspace cleanliness；本次 committed bootstrap checkpoint 的 receipt 是有效工程证据。

Harness 不是 editorial or subjective media-quality gate。它不会判断角色是否换脸、镜头是否过度重复、故事节奏是否可看，或一个 5 分钟成片是否应该被 human accept。本 session 的错误不是 Harness 太重，而是把工程正确性证据错误外推成了观看质量信心。后续必须保持两条独立 gate：

1. Code/state correctness -> tests + exact Harness receipt。
2. Media/editorial acceptance -> representative frames, bounded batches, contact sheets, full-watch reviews, semantic review and explicit Final Acceptance。

## Resume Instructions

若用户以后明确恢复此任务，先做以下事情，不要从当前 `outcome_unknown` attempt 自动继续：

1. 把当前 run 保留为 rejected evidence，不得 promote 当前 `final-candidate.mp4`。
2. 先重新读取 execution plan 与上面三份 `docs/record_for_agent` 记录。
3. 对 `relay-seven-representative-keyframe-shot-001` 做 explicit outcome reconciliation。若不能用 canonical evidence 确认 exact external result，保持 `outcome_unknown`；不得 blind retry、伪造 result 或手工 activation。
4. 重新建立真实 native Character/Scene Reference Pack，先人工检查 Shots 001/007/019/031 四张 representative keyframes。四张不通过时不得 bulk generation。
5. 重新实现约 `20 static / 16 generated` 的 visual plan；generated lane 先做 representative three-Shot sequence，通过后每批只推进 4～6 Shots，并逐批检查 identity、continuity、variation、pacing 和 source quality。
6. 不要用重复已有 black-haired frames 来“修复”helmet identity；必须从 reference/source 层纠正。
7. 只有全片 full-watch、story/continuity/system reviews、P6 repair closure 和 explicit final acceptance 都通过后，才能创建 `deliverables/final.mp4` 与 reality-validation report。
8. 若继续当前 tracked code lane，先 review exact diff，补 final independent review，按 `.agent/harness/policy.yaml` 对 exact staged snapshot 运行 required checks，再 checkpoint commit。只 stage task-owned exact paths；不要 stage `index.json`。

## Files To Read First

1. `AGENTS.md`
2. `docs/superpowers/plans/2026-08-20-ai-video-5-minute-rough-cut-reality-validation.md`
3. `docs/record_for_agent/2026-08-20-minimax-h3-quality-profile-and-alice-ab.md`
4. `docs/record_for_agent/2026-08-20-h3-shot-continuity-and-vscode-playback.md`
5. `docs/record_for_agent/2026-08-20-seedance-synthetic-continuity-and-skill-preflight.md`
6. `runs/5min-rough-cut-20260820T100302Z-v1/state/manifest.json`
7. `runs/5min-rough-cut-20260820T100302Z-v1/evidence/final-contact-sheet.jpg`
8. `runs/5min-rough-cut-20260820T100302Z-v1/evidence/h3-chain-contact-sheet.jpg`

## Publication And Cost Truth

- Remote/paid Provider calls in this rough-cut run: `0`。
- Successful local H3 generations: `3`。
- Interrupted local Qwen attempt: `1 outcome_unknown`；没有 registered/activated image。
- No push, no release, no `final.mp4`, no Final Acceptance。
