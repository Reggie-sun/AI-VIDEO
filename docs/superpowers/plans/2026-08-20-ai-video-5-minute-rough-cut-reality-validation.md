# AI-VIDEO 5-Minute Rough Cut Reality Validation Execution Plan

**Goal:** 使用当前已实现的 AI-VIDEO Production contracts，先完成并实际观看一段 30～60 秒、连续 4～8 Shots 的真实 Pilot，只有 Pilot GO 后才扩到 270～330 秒、30～45 个 Shots 的 short-drama rough cut，并以真实 selective repair 证明从 defect diagnosis 到 rerender 的闭环。

**Scope:** 1 个完整故事、1 个主要角色、最多 1 个主要配角、1～2 个主要场景；planning target 为 36 个 Shots / 300 秒，其中约 20 个 `static_image`、约 16 个 `generated_video`，最终数量允许在 spec 范围内因故事节奏调整。

**Contract Surfaces:** `ProductionProject`、Asset Registry、Production Manifest、`ProductionStateCommitter`、Dependency Graph / resolver、`ResolvedTimeline`、HyperFrames、P7 image lifecycle、P8 generated-video lifecycle、P4 voice/captions、P6 review/repair/final acceptance，以及 task-owned run evidence。

**Invariants:** `ProductionStateCommitter` 保持唯一 durable writer / activation / recovery owner；`ResolvedTimeline` 保持唯一 order/frame/sample/timing owner；P5 保持唯一 invalidation / rebuild frontier owner；HyperFrames 保持默认 renderer；Provider 必须显式选择且不得 automatic fallback；remote/paid call 必须经过 exact preview、finite budget、egress、secret reference、durable intent 与 one-use permit。

**Current / Target Behavior:** 当前仓库已经分别证明 P2-P8、Base AI Comic E2E、Local H3 technical continuity、generated MP4 composition 与 P6 repair contracts，但没有一份 5 分钟真实作品把这些能力作为同一个 Production Project 连续使用。目标不是新增 production orchestrator，而是用现有 public Python APIs 和 canonical owners 完成一次真实生产并保留可审计 evidence。

**Compatibility:** 不改变 Legacy `0.1.x` CLI、Manifest v1、Production schema、Registry layout、artifact layout、public API、renderer selection、Provider routing 或 sealed H3 profiles；不增加 runtime dependency。若真实生产暴露阻断性 bug，先单独复现、修复、验证和 commit，再从 explicit recovery seam 恢复本 run。

**Out of Scope:** P9、Studio UI、自动 Provider ranking/fallback、全模型 benchmark、Seedance/Hailuo 必选、Remotion 或第二 renderer、第二 timeline、第二 Manifest/Registry writer、schema redesign、LoRA training、无人值守生产和商业级 final polish。

**Acceptance Criteria:** 批量生产前先有实际观看并得到 GO 的 30～60 秒 Pilot MP4，包含连续 4～8 Shots、同一主要角色、static/image-motion、H3 generated-video、真实 voice/captions 与 HyperFrames composition；Pilot NO-GO 时 STOP。Pilot GO 后的真实 `final.mp4` 时长 270～330 秒、画面/语音/字幕完整；同时使用 static/image lane、generated-video lane、voice/caption、composition/render、QA/review；包含一组三 Shot continuity sequence；完成一次真实 defect 的 selective repair，且不从零重做全片；最终报告覆盖 spec Section 23.F 的全部指标。

**Verification:** strict reopen、exact replay、P5 closure comparison、`ffprobe`、project-local `video-analysis`、三次人工 full-watch、final acceptance receipt，以及任何 code/tooling delta 对应的 fresh Harness receipt。未执行的 remote Provider、主观质量或商业级 acceptance 不得由其他 evidence 外推。

**Spec:** `docs/superpowers/specs/5min_test.md`

## Status and Authorization Boundary

本文是 execution plan，不是 runtime completion evidence。当前“根据 spec 写 plan”的请求只授权本文件，不授权 local GPU production、live Provider、remote/paid submit、媒体生成或质量验收。

后续若用户明确要求执行本 plan，该请求可作为 accepted scope 内完成 rough cut 所需本地执行的授权；任何 remote/paid lane 仍必须在 submit 前形成 exact request、单 Shot 理由、费用上限和全部 Paid Provider Gate evidence。历史 credential、余额、receipt 或 live artifact 不授权新的调用。

## Problem Boundary

- **Single owner:** Production truth 归 `ProductionProject` / Asset Registry / Manifest 及其既有 owners；本 run 的 report 只汇总 evidence，不成为第二套 lifecycle。
- **Old path to avoid:** 不得使用 Legacy `ai-video run` 拼接 Production artifacts，不得用 ad-hoc ffmpeg stitching 代替 activated HyperFrames render，不得把 fetched Provider MP4 当成 activated asset，也不得按 Shot 顺序 blanket rebuild。
- **Supported first-run strategies:** 当前 P3 composition 只接受 `static_image`、`generated_video` 和 `existing_video`。虽然 domain validation 能表达 `image_motion`、`motion_graphics`、`hybrid`，当前 renderer contract 会明确拒绝；本轮不得为追求比例临时扩展它们。
- **Continuity mapping:** `exact_terminal` 只用于同一动作/机位的连续段；`reference` 通过 canonical Character/Scene references 和必要的独立 keyframe 重新构图；`semantic` 只继承故事/角色状态；不允许统一复制上一 Shot terminal frame。
- **Unchanged contracts:** P3/P4 audio/caption/mux、P5 typed graph、P6 approval/final acceptance、P7 image provenance、P8 Provider request/activation/recovery、Shot Router 的 Provider-selection boundary均保持不变。
- **Focused runtime seam:** `ShotVisualResolver` / `VideoGenerationResolver` 只作 pure routing；image 使用 `ProductionStateCommitter.generate_image_asset()`；video 使用 `VideoGenerationService` 与 committer-owned activation；composition 使用 `resolve_composition()` 和 `render_with_hyperframes()`；review/repair/final acceptance只通过 P6 committer methods。
- **Reference / final boundary:** Character / Scene reference 只提供 identity、state、space 或 style guidance；Final Shot Visual 必须绑定具体 Shot intent。无导演理由不得把 reference、crop/resize 或简单派生自动当作 final visual。

## File and Artifact Map

### Tracked planning artifact

- Create: `docs/superpowers/plans/2026-08-20-ai-video-5-minute-rough-cut-reality-validation.md` — 本 execution contract。

### Task-owned runtime artifacts created only during authorized execution

执行开始时只设置一次 `RUN_ID=5min-rough-cut-YYYYMMDDTHHMMSSZ-v1`；其中 timestamp 是实际 UTC 启动时间，后续不得复用或重命名该 ID。

- Create: `runs/$RUN_ID/project.yaml` — stable Production Project entrypoint；active truth 仍由其 Manifest pointers指向 exact snapshots。
- Create: `runs/$RUN_ID/state/**` — 仅由既有 `ProductionStateCommitter` 和 approved loaders/lifecycles创建的 canonical Project、Registry、graph、render、review、repair、image、video、voice evidence。
- Create: `runs/$RUN_ID/evidence/production-record.jsonl` — append-only per-Shot operator observations；不保存或改写 lifecycle state。
- Create: `runs/$RUN_ID/deliverables/pilot.mp4` — 30～60 秒 Reality Gate 成片；必须先 human GO，才能进入 5-minute bulk production。
- Create: `runs/$RUN_ID/evidence/pilot-review.{json,md}` — exact Pilot bytes 的 Visual / Continuity / Pacing / Production review、repair 与 GO/NO-GO。
- Create: `runs/$RUN_ID/evidence/first-cut-review-{story,continuity,system}.md` — 三次 full-watch 的独立记录。
- Create: `runs/$RUN_ID/evidence/{ffprobe,video-analysis}-final.json` — exact final bytes 的 machine-readable technical evidence。
- Create: `runs/$RUN_ID/evidence/reality-validation-report.{json,md}` — spec Section 23.F 指标、failure classification、repair closure、cost/resource summary 与 remaining risks。
- Create: `runs/$RUN_ID/deliverables/first-complete-rough-cut.mp4` — 第一版完整 cut 的 immutable delivery copy；SHA-256 必须绑定对应 activated render output。
- Create: `runs/$RUN_ID/deliverables/final.mp4` — 最终 rough-cut delivery copy；SHA-256 必须等于 final-accepted active render output。

### Tracked truth updates created only after runtime acceptance

- Create: `docs/record_for_agent/YYYY-MM-DD-5-minute-rough-cut-reality-validation.md` — durable run path、hash、receipt、结论与 blocker；文件名前缀必须替换为实际完成日。
- Modify: `docs/v0.2-runtime-baseline.md` — 只记录本轮实际已验证行为、artifact identity 和未验证边界。
- Modify: `docs/v0.2-agentic-production-roadmap.md` — 只记录本 slice 的真实 gate 状态与下一决策。

### Explicitly unchanged unless a blocker is proven or this task explicitly owns the document

- `src/ai_video/production/**`
- `tests/**`
- `workflows/**`
- `.agent/harness/policy.yaml`
- `README.md`
- Legacy `src/ai_video/{cli,pipeline,manifest}.py`

## Major Milestones

### Milestone 0: Freeze the Execution Base and Prove Readiness

**Files:**

- Read: `AGENTS.md`
- Read: `docs/agent-primary-contract-matrix.md`
- Read: `.agent/harness/policy.yaml`
- Read: `docs/v0.2-runtime-baseline.md`
- Read: `docs/v0.2-agentic-production-roadmap.md`
- Read: this plan and its spec
- Search/read: `docs/record_for_agent/` records directly relevant to real media production、quality regression、Provider quality、continuity 与 rough cut
- Modify: no runtime file

**Owner / Dependencies:** Parent/operator owns the full production lifecycle. Execution must be single-writer in the current working tree unless the user separately requests a worktree; no overlapping writer may own Production state, docs truth, or blocker-fix files.

**Contract:** 确认 current `HEAD`、working-tree ownership、supported visual strategies、exact local H3/image profiles、HyperFrames/ffmpeg availability和 no-network regression baseline。Preflight 不创建 run、不提交 Provider、不读取或输出 secret。

`docs/record_for_agent/` 只提供可复用经验，必须重新核对 current code/run truth；普通代码修改不得因此读取整个目录。

**Implementation Notes:**

1. 检查 `git status --short --branch`、当前 live agents、`git log -12` 和 local/origin divergence；若出现 unrelated dirty changes，停止写入并报告，不自动创建 worktree。
2. 运行既有 focused offline suites，至少覆盖 reader/state、composition/audio、dependency、review、image、video Provider 和 Shot Router。使用 `.agent/harness/policy.yaml` 中当前 command，不复制旧 pass count 作为 current truth。
3. 对 intended runtime paths 做 Harness advisory inspection；`runs/**` 是 ignored production output，不得作为 Harness receipt 替代品。
4. 通过 adapter 自身的 sealed preflight确认 Local Qwen image lane、Local H3 `fl2va` profile、ComfyUI loopback endpoint和 HyperFrames tool root。Preflight mismatch 在任何 durable intent 或 GPU submit 前 fail closed。

**Acceptance:** clean/owned execution base；offline focused suites fresh GREEN；所有本地工具和 sealed profile可解析；没有 network、secret或媒体 side effect。

**Verification:** 使用 policy 中的 `production_reader_tests`、`production_state_tests`、`production_composition_audio_tests`、`production_dependency_tests`、`production_review_tests`、`production_image_tests`、`production_video_provider_tests`、`production_shot_router_tests` 对应命令，并保存 exact command/result 到 execution log。

### Milestone 1: Lock Story, References, Shot State, and Production Budget

**Files:**

- Create through canonical Production models: Brief、Story、Character、Scene、Storyboard、Shots和 initial composition intent
- Create: run-local `evidence/production-record.jsonl`

**Owner / Dependencies:** Milestone 0；AI-VIDEO artifacts是 creative truth。`hell-grind-aigc-skill` 只用于 open/close state 与 continuity advice，`video-shotcraft` 只用于 pacing/transition/SFX advice；Provider-specific prompt adaptation 只有在 semantic contract locked 后才可使用 `higgsfield`。

**Contract:** 冻结一条 5 分钟内完整、低角色数、低场景数且包含关键动作的故事；planning target 为 36 Shots / 300 秒。每个 Shot 必须有明确 `visual_strategy`、`continuity_mode`、duration budget、asset roles、dialogue/narration和 `open_state -> changes_here -> close_state`。

`Reference Asset` 只负责说明角色/场景应该是什么；`Final Shot Visual` 是观众最终看到的 asset。Character / Scene reference 默认不得自动成为 final visual，crop/resize/轻微派生也不能自动升级为 Shot-specific visual。每个 Shot 必须记录画面目的、final asset、适配理由、continuity fit 与 reuse rationale；没有导演理由的非连续重复绑定不得进入 composition。

**Implementation Notes:**

- 默认分配 20 个 `static_image` 与 16 个 `generated_video`；只有已存在且注册的真实 source 才使用 `existing_video`。若故事调整，最终仍需 30～45 Shots、270～330 秒，并在 report 解释比例变化。不得为凑时长 blanket downgrade；每个降级必须有 Shot-specific replacement、导演理由和 human review。
- 在生成前锁定 Character Reference Pack、Scene Reference Pack、主要服装状态和关键道具。角色/场景 reference 不合格时先修 reference，不进入 bulk video generation。
- 至少设计一个连续三 Shot sequence：包含可审计的 N→N+1→N+2 state progression；continuity mode 可以组合 `exact_terminal`、`reference`、`semantic`，但每条 edge 必须有叙事理由。
- 为 ordinary generated Shot 设定最多 2 次本地 candidate generation；Hero Shot 最多 3 次。超出上限先诊断 Asset / Shot state / Prompt / Provider 层，不通过重复生成掩盖问题。
- Remote Provider 初始预算为 0 次调用。只有具体 Shot 在 local/static lane 无法满足“阻碍观看”标准时，才形成单独 rescue proposal。

**Acceptance:** Story/Character/Scene/Storyboard/Shot artifacts strict validate；36-Shot target 的 duration sum 位于 270～330 秒；每个 Shot 都能追溯 visual/continuity/voice/caption intent；references已锁定。

**Verification:** `load_production_project()` strict reopen、`validate_project_references()` 和 Shot strategy validation通过；report 中保存 Shot count、duration sum、strategy distribution和 continuity sequence IDs。

### Milestone 2: Bootstrap Canonical Project State and Register Locked Inputs

**Files:**

- Create: run root `project.yaml`
- Create through committer: exact Project/Registry/Dependency Graph snapshots and Manifest pointers under `state/**`
- Create: exact registered Character/Scene/prop/style reference assets

**Owner / Dependencies:** Milestone 1；`ProductionStateCommitter` 是唯一 writer，Asset Registry 是唯一 asset identity/provenance owner，P5 builder/resolver是唯一 dependency owner。

**Contract:** 所有后续 image/video/voice/render request 必须绑定同一 active Project/Registry/Graph tuple和 exact registered bytes。Operator report只能引用 IDs、hashes和 observations，不得声明 active state。

**Implementation Notes:**

- 通过 standard Production loading/sealing/commit seam 创建初始 snapshot，不直接写 Manifest JSON/YAML，也不复用 test factories。
- Human-created/imported reference 使用 truthful source/actor receipt；local generated reference 使用 P7 request/result/provenance；不得把 web/manual image描述成 Provider API result。
- 每次 activation 后 strict reopen 并记录 Manifest revision、active pointers、artifact SHA-256。Unknown outcome 立即停止该 lane并执行 explicit recovery，不 blind retry。

**Acceptance:** clean run root可由 `load_production_project()` strict reopen；所有 active reference bytes存在、path-contained、hash-matched；graph没有 dangling nodes或第二 lifecycle。

**Verification:** reader/state/dependency focused checks保持 GREEN；run-local reopen记录列出 exact project/registry/graph identities。

### Milestone 3: Complete Static Visuals, Voice, and Captions Before Bulk Video

**Files:**

- Create through P7 lifecycle: static visual assets for all planned static Shots and keyframes required by generated Shots
- Create through P4 lifecycle: dialogue/narration audio、alignment evidence、`CaptionTrack`、optional ambience/SFX/BGM
- Update through canonical owners: active Project/Registry/Graph only

**Owner / Dependencies:** Milestone 2。P7 owns image request/provenance/activation；P4 owns audio/caption contracts；timing仍由未来 `ResolvedTimeline` 统一解析。

**Contract:** 在 bulk H3 generation 前，所有 static Shots 有可用画面，所有台词/旁白有真实可听 audio 和 structured caption source。Voice duration可以推动 Shot timing，但不得另建 audio timeline。

**Implementation Notes:**

- Static lane 默认使用 sealed local Qwen image adapter；必要的 human image import必须使用 existing import contract。不得使用 unattended browser automation或假称 OpenAI Image API provenance。每个 static/image-motion Shot 必须使用 Shot-specific image 或有明确导演理由的 approved reusable plate；不得拿 Character / Scene reference 或其简单 crop 顶替。
- Voice 默认选择当前已支持且可诚实记录 provenance 的路径：本地/人工音频走 `AudioImportRequest`；若选择现有 remote speech adapter，则在 request 固定后执行 voice preview/authorization/durable intent/one-use permit，费用计入本 run。不得在这两条路径之间 silent fallback。
- 先根据实际音频 duration生成/调整 `CaptionTrack`，再冻结 Shot duration budget。字幕 source text、speaker/voice identity、alignment和 audio bytes必须能互相核对。
- 每激活一个 asset，append一条 per-Shot record：generation count、elapsed time、candidate identity、failure reason、manual intervention、accepted flag。

**Acceptance:** 所有 Pilot static Shots 已有 Shot-specific accepted source；任何非连续 final-asset reuse 都有导演理由和人工 review；全部 dialogue/narration可听且字幕文本/时间可追溯；Pilot duration为 30～60 秒；未发生未授权 remote submit。

**Verification:** P7/P4 strict reopen；抽查至少主角、配角、两个场景和关键道具的 reference binding；probe全部 audio；验证 CaptionTrack 对应 script和 source samples。

### Milestone 3A: Pass The 30–60 Second Pilot Reality Gate

**Files:**

- Create through existing owners: 4～8 个连续 Pilot Shot visuals、必要 H3 generated-video assets、Pilot `ResolvedTimeline` / HyperFrames state
- Create: `deliverables/pilot.mp4`
- Create: Pilot `ffprobe`、current-byte contact sheet / `video-analysis` raw evidence、human review 与 repair notes

**Owner / Dependencies:** Milestone 3。AI-VIDEO Shot / Asset / P4 / P8 / P3 / P6 owners保持不变；Skills只提供 authoring guidance。

**Contract:** 从当前故事选择连续 4～8 Shots（约 30～60 秒），包含同一个主要角色、至少一个真实 transition、至少一个 static/image-motion Shot、至少一个 Local H3 generated-video Shot、真实 voice、真实 captions 与最终 HyperFrames composition。Pilot 必须实际观看；hash、Manifest、tests、`ffprobe`、contact sheet 与 `video-analysis` 不能单独给 GO。

**Implementation Notes:**

1. 每个 Shot 先回答 visual intent、final asset、适配理由、continuity fit 与 reuse rationale；reference 默认不得成为 final visual。
2. 使用现有 asset IDs / hashes 做低成本 repetition audit：同一 final image 跨非连续 Shots 复用且无导演理由时 fail；连续长静止或 captions-only progression进入人工 review。
3. 使用现有 `Character.reference_asset_ids`、`Shot.character_ids`、continuity 与 Review contracts完成 important-character identity review；不新增 Character schema、LoRA、Manifest或 identity database。
4. 人工检查 Visual / Continuity / Pacing / Production 四组问题，并给出明确 `GO` 或 `NO-GO`。
5. `NO-GO` 时只修 Pilot 内最小责任层，证明单 Shot selective rebuild，重新 render并重新观看；不得批量扩到 5 分钟。

**Acceptance:** `deliverables/pilot.mp4` 完整可播放且经 human review 达到基本能看、角色基本稳定、画面与剧情对应、无大量重复 reference、声音字幕正常、无重大 continuity jump；verdict 为 `GO`。

**Verification:** strict reopen、exact replay、P5 closure、`ffprobe`、project-local `video-analysis`、current-byte contact sheet、完整人工观看与明确 verdict。缺任一项即 `NO-GO`。

### Milestone 4: Produce Generated-Video Shots in Bounded Batches

**Files:**

- Create through P8 lifecycle: Local H3 requests、durable local submit intents/results、fetched/measured MP4、terminal evidence、activated Project/Registry/Graph snapshots
- Append: per-Shot production records and failure classifications

**Owner / Dependencies:** Milestone 3A 已 GO；Shot Router仅提出 explicit feasible route，operator批准具体 visual/provider/profile，`VideoGenerationService` 执行已有 lifecycle。

**Contract:** H3 是 primary generated-video lane。每个 request 绑定 exact Shot、mode、prompt、reference/terminal evidence、output requirement、profile和 active base tuple；Provider失败不得触发自动切换。

**Implementation Notes:**

1. Pilot 中先执行代表性的三 Shot continuity sequence，不立即批量生成全片。`exact_terminal` 证明 source terminal bytes等于 downstream `first_frame`；`reference` 若需要新构图，先用 P7 canonical references生成独立 Shot-specific keyframe，再交给 H3 I2V；`semantic` 不伪造像素连续。
2. 代表 sequence通过 technical reopen与人工 continuity inspection后，以 4～6 Shots 为一批推进。每批完成后更新真实 generation count、success rate、local elapsed time、identity/continuity defects，避免最后集中补账。
3. 非关键 Shot 达到可观看标准即停止迭代；quality一般但不阻碍观看时保留并进入 first cut。超过 Milestone 1 candidate上限或连续三次同类失败时，先定位 Asset / Shot state / Prompt / Provider/model责任层。
4. Hailuo只允许作为明确列名的 rescue/Hero Shot。每个 cloud Shot必须单独保存 exact preview、cost ceiling、egress、authorization、one-use permit和 outcome；Seedance不是本轮 completion dependency。
5. Provider outcome unknown 时停止该 Shot，执行 explicit recovery并保留完整 orphan evidence；不得 remint permit或复制 external task identity。

**Acceptance:** Pilot GO 后的所有 planned generated Shots都有 activated H.264 MP4，或以逐 Shot导演理由、Shot-specific replacement 与 human review显式降级；不得为凑时长 blanket downgrade。三 Shot continuity chain可重开且人工检查；H3 generation和任何 remote call/cost均逐 Shot计数。

**Verification:** `VideoGenerationService.fetch_and_activate()` 后 strict reopen；exact replay新增 submit/fetch/activation均为零；MP4 measured metadata满足 composition contract；P5只 stale真实 downstream closure。

### Milestone 5: Render the First Complete Rough Cut Early

**Files:**

- Create through P3/P4 render lifecycle: sealed `ResolvedTimeline`、HyperFrames source/receipt/output/state
- Create: `deliverables/first-complete-rough-cut.mp4`
- Create: first-cut `ffprobe` and hash evidence

**Owner / Dependencies:** Milestone 3A GO + Milestone 4。`resolve_composition()` 独占 timeline resolution，`render_with_hyperframes()` 是唯一 render path，committer独占 render state activation。

**Contract:** 第一版必须从 0 秒播放到最后、故事完整、无缺失 source、声音基本可听、字幕基本可读、每个 Shot有明确 asset来源。允许少量非关键 static replacement和未精修素材，但不允许 broken timeline或 silent source fallback。

**Implementation Notes:**

- 只使用当前 P3支持的 `static_image`、`generated_video`、`existing_video` spans；不得把 CSS motion、crossfade、ad-hoc ffmpeg或未支持 strategy塞进 renderer。
- 根据真实 voice/caption duration最后解析一次 canonical timeline。若总时长越界，先调整 Shot editorial duration和无价值 Shot，不以视频变速或截断台词掩盖问题。
- Activated render output以 byte-for-byte copy形成 delivery file，并记录 source pointer、SHA-256和 copy hash；delivery copy不是新的 active truth。

**Acceptance:** first complete cut时长 270～330 秒、画面/音频 stream存在、无 missing Shot、字幕可读、active render strict reopen；此 gate完成后才进入系统性 review。

**Verification:** `ffprobe` 保存 container、codec、dimensions、fps、duration、audio streams；从头到尾人工播放一次确认无播放中断；reopen active render并核对 delivery SHA-256。

### Milestone 6: Perform Three Independent Full-Watch Review Passes

**Files:**

- Create: `evidence/first-cut-review-story.md`
- Create: `evidence/first-cut-review-continuity.md`
- Create: `evidence/first-cut-review-system.md`
- Create through P6: review request/evidence/receipt and layer states

**Owner / Dependencies:** Milestone 5。project-local `video-analysis` 只产生 raw technical evidence；human/operator和 P6 policy/committer决定 durable verdict。

**Contract:** 三次 review必须各自完整观看同一 first-cut bytes，不得用抽帧替代 full-watch。每个 defect记录 exact time/Shot、observed symptom、responsibility layer、severity、evidence和 recommended smallest repair。

**Implementation Notes:**

- **Pass A — Story:** 理解度、节奏、Shot长短、无价值镜头。
- **Pass B — Visual / Continuity:** identity、body/outfit、scene/prop、screen direction、action phase、lighting和 Shot transition。
- **Pass C — Production System:** defect应该在哪层修、P5 closure是否精确、是否发生不必要 regeneration、是否有 untracked asset、manual bypass或 silent fallback。
- 同时运行 project-local `video-analysis`，但 heuristic没有报错不能替代 semantic PASS；人工 review与 machine evidence必须绑定 exact render SHA。

**Acceptance:** 三份独立 full-watch记录完成；所有 blocker和严重 defect已分类；选出至少一个真实、可 bounded repair 的 failure；P6 durable review状态与 exact first-cut render一致。

**Verification:** review request、technical context、tool identity、render hash、timeline fingerprint和 graph hash strict reopen；每个 reported defect可映射回 Shot/asset/timestamp。

### Milestone 7: Execute One Genuine Selective Repair Closure

**Files:**

- Create through P6: approved repair receipt、repair outcome receipt
- Modify through existing canonical owner: one smallest responsible artifact or contract input
- Create through P5/P3/P6: selective transition、rerender、fresh review evidence

**Owner / Dependencies:** Milestone 6。Repair target由 defect responsibility layer决定；P6 authorizer批准 exact target，P5 resolver计算真实 transitive closure，各 domain owner只修改自己的 input/state。

**Contract:** 只修阻碍观看、明显身份错误、严重 continuity、严重声音/字幕或系统级错误。必须在 mutation前保存 expected P5 closure，并证明 unrelated Shots、voice/captions和 assets没有 regeneration或 identity变化。

**Implementation Notes:**

- Asset defect修 Asset/reference；Shot-state defect修 canonical Shot input；prompt defect创建新的 exact generation request；Provider defect只重做该 candidate；caption/timing defect修 P4 input；layout defect修 composition input。不得把所有问题归为模型失败。
- 若发现现有 runtime blocker，暂停媒体生产，先用最小 executable RED reproduction证明“没有该修复 rough cut无法继续或 production truth错误”。只修改 blocker-owned code/tests，运行 policy-routed tests和 fresh Harness，commit后再通过 explicit recovery恢复 run。
- 若 repair需要 schema/layout/new writer/new renderer/new Provider-selection path，停止并请求独立 scope-expansion approval；本 plan不授权该架构变化。

**Acceptance:** 至少一次 `defect -> diagnosis -> approved exact change -> P5 selective rebuild -> rerender -> fresh review` 完成；没有整片从零重做；unaffected identities保持不变并有 before/after evidence。

**Verification:** 保存 before/after graph state和 changed closure；核对 Provider/image/voice/render call counts；exact replay不重复 side effect；repair outcome只绑定 fresh repaired render/review。

### Milestone 8: Produce and Accept the Final Rough Cut

**Files:**

- Create: `deliverables/final.mp4`
- Create: `evidence/ffprobe-final.json`
- Create: `evidence/video-analysis-final.json`
- Create through P6: final acceptance receipt/state

**Owner / Dependencies:** Milestone 7；final acceptance仍由 Manifest/committer lifecycle拥有，delivery file和 report只引用它。

**Contract:** final bytes必须来自 repaired active HyperFrames render，满足 deliverable、production、continuity、repair和 evidence gates。`final.mp4` 名称不自动代表 accepted；必须先有 current fresh review和 final acceptance receipt。

**Implementation Notes:**

- 对 final bytes重跑 `ffprobe` 和 project-local `video-analysis`，完整观看最终版，重点复查 repair window、三 Shot continuity sequence、字幕边界、音频可听性和尾帧完整性。
- 执行 strict reopen、explicit recovery no-op检查和 exact replay；任何 tamper、mixed state或 unknown outcome均 fail closed。
- 将 activated output byte-for-byte复制为 `deliverables/final.mp4`，记录 active output pointer、SHA-256、size、duration和 delivery hash。
- Acceptance只声明“5-minute rough-cut reality validation accepted”。不得外推为商业级成片、H3通用质量、cloud Provider acceptance或 P9完成。

**Acceptance:** 270～330 秒 final MP4可完整播放，有画面、真实可听语音和可读字幕；三 Shot continuity人工通过；repair defect已关闭；final acceptance state strict reopen。

**Verification:** `ffprobe` technical gate、`video-analysis` raw evidence、final full-watch checklist、active output/delivery SHA equality、final acceptance receipt freshness和 zero-effect replay。

### Milestone 9: Publish Reality-Validation Evidence and Next Decision

**Files:**

- Create: `evidence/reality-validation-report.json`
- Create: `evidence/reality-validation-report.md`
- Create on actual completion date: `docs/record_for_agent/YYYY-MM-DD-5-minute-rough-cut-reality-validation.md`
- Modify after proof: `docs/v0.2-runtime-baseline.md`
- Modify after proof: `docs/v0.2-agentic-production-roadmap.md`

**Owner / Dependencies:** Milestone 8。Run report汇总 production observations；canonical docs只记录 verified current truth，不复制完整 runtime ledger。

**Contract:** Report必须回答总 Shot 数、strategy distribution、generated-video数、H3使用次数、remote次数/费用、总生成次数、accepted candidate比例、最常见三类失败、人工介入次数、selective repair位置和主要瓶颈。

**Implementation Notes:**

- 同时报告总 wall time、local GPU execution time、人工 review/selection time、remote spend和失败/返工时间；local resource不伪装成 paid receipt。
- 对每项 conclusion附 exact run-relative artifact path、SHA-256或 receipt identity。若 evidence只支持 technical而非 subjective结论，明确标注边界。
- 根据真实数据提出下一步最多三个 prioritized options；不得在本 task中顺手启动 H3 quality、ref2va、更多 cloud Provider、Router扩展、Studio UI或 P9。
- Runtime artifacts保持在 ignored `runs/**`；tracked durable note记录它们的 exact location/hash。只 stage本 task的 tracked docs和任何已独立验证的 blocker fix files。

**Acceptance:** JSON/Markdown数字一致；spec Section 23.F无缺项；baseline/roadmap没有把失败、blocked或未验证项写成 complete；publication state明确区分 local commit、origin和 release。

**Verification:** 对 tracked exact staged snapshot运行 Harness inspection/verification和 receipt self-verification；docs-only delta至少通过 `scope_diff_check`。若包含 blocker code/tooling，必须同时通过其 policy-routed focused/full checks和 fresh passing Harness receipt。

## Stop Gates

立即停止当前 lane并报告，而不是自行扩大 scope：

1. `ProductionProject`、Manifest、Registry、Dependency Graph或 active render无法 strict reopen/recover。
2. 完整 timeline或 `final.mp4` 无法生成，或真实 Shot无法进入 current composition contract。
3. 重要 reference被静默丢弃、Provider silent fallback、asset provenance缺失或 fetched candidate被误当 activation。
4. 单 Shot change触发错误 blanket rebuild，或 repair无法绑定 exact P5 closure。
5. Provider outcome unknown、费用超过 exact ceiling、需要新增 remote call、Provider/model/egress发生变化。
6. 需要 schema/layout/public API/new writer/new renderer/new timeline/new Provider-selection path 才能继续。
7. Pilot 没有实际观看、verdict 为 `NO-GO`，或 Pilot repair 后仍未达到 basic watchability。
8. Character / Scene reference 或其简单派生被无导演理由当作 Final Shot Visual。
9. 同一 final asset 被多个非连续 Shots 复用且没有 director rationale / human review。
10. 重要角色 final asset 未完成 identity / wardrobe / state review。

以下情况在 Pilot 已 GO、Shot-specific visual成立且有人工 review 后可记录为 observation：非关键 Shot质量一般、Hailuo不支持特定 reference capability、基础 BGM/SFX不完美、少量 candidate需要人工选择。不得再把“部分 Shot降级为 static”作为 blanket exemption。

## Spec Coverage Matrix

| Spec concern | Plan owner |
| --- | --- |
| Objective、Scope、Story、Production profile | Milestones 1 and 9 |
| 30～60 秒 Pilot Reality Gate 与 GO/NO-GO | Milestone 3A |
| Reference Asset / Final Shot Visual 与 Shot-specific visual | Problem Boundary、Milestones 1、3 and 3A |
| Visual repetition / identity / human viewing | Milestone 3A and Milestone 6 |
| Shot strategy and current renderer compatibility | Problem Boundary、Milestones 1 and 5 |
| Provider policy and paid authorization | Status Boundary、Milestone 4、Stop Gates |
| Exact/reference/semantic continuity and Shot state | Milestones 1 and 4 |
| Character/Scene reference lock | Milestones 1–3 |
| Voice、CaptionTrack and timing | Milestones 3 and 5 |
| First complete cut early | Milestone 5 |
| Three-pass reality review | Milestone 6 |
| Per-Shot record and failure classification | Milestones 1、3、4、6、9 |
| Selective repair | Milestone 7 |
| Architecture freeze and non-goals | Problem Boundary、Stop Gates |
| Final deliverable、continuity、repair、evidence acceptance | Milestones 8 and 9 |
| Evidence-driven next decision | Milestone 9 |

## Completion Handoff

完成本 plan 文档后停止；不要在同一 plan-only task中创建 run、生成媒体、调用 Provider或修改 runtime。后续执行必须从 Milestone 0重新核对 current code、Git、runtime evidence和 authorization，不能把本 plan 的 proposed commands、数量或 artifact paths当作已经发生的事实。
