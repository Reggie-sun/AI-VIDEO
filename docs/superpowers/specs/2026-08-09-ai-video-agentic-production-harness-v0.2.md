# AI-VIDEO v0.2 Agentic Production Harness Specification

Status: Approved product direction and planning contract on 2026-08-09; every runtime slice requires separate implementation authorization.
Target Repository: `Reggie-sun/AI-VIDEO`
Target Version: `0.2.x`
Product Name: `Agent-first AI Video / AI Comic Production Harness`
Current Runtime Evidence: `docs/v0.2-runtime-baseline.md`
Dependency Map: `docs/v0.2-agentic-production-roadmap.md`
Supersedes: `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`

---

# 1. Problem

当前 `0.1.x` runtime 把 Shot 主要建模为一次 ComfyUI video workflow request。这个模型能够生成、串联、恢复和拼接视频 clip，但无法稳定表达一部 AI 漫剧或解说视频的完整生产状态：Story、Character Bible、Scene Bible、Storyboard、静态图、配音、字幕、音乐、时间线、review 和局部 repair 都没有 first-class owner。

如果继续以 Provider abstraction 和“所有 Shot 都生成视频”为主线，会产生三个错误结果：

1. 把昂贵且不稳定的 video generation 当成基础能力，而不是 optional visual asset capability。
2. 让 Codex 只做一串没有 durable state 的 plugin/API 调用，无法解释、恢复或局部重建。
3. 同时引入多个 timeline/render owner，导致 HyperFrames、Remotion 和 ffmpeg 对同一时间线重复控制。

v0.2 需要解决的核心问题不是“如何再接一个视频模型”，而是“Codex 如何在一个可验证、可恢复、可选择性重建的 production contract 上完成整部作品”。

# 2. Product Decision

v0.2 的产品定位正式调整为：

`Agent-first AI Video / AI Comic Production Harness`

Codex 是顶层 Production Agent。AI-VIDEO 不实现第二套通用 Agent runtime，而是提供：

- durable project contract；
- creative state 与 production state；
- typed asset registry；
- provenance、hash 和 cost receipts；
- artifact dependency graph；
- deterministic invalidation 和 selective rebuild；
- resolved timeline/composition；
- renderer adapter；
- QA、review 和 repair receipts。

基础 Production Path 必须在没有 Video Provider 的情况下完成：

```text
Story / Script
    -> Character Bible
    -> Scene Bible
    -> Storyboard
    -> Shot Plan
    -> Image Assets
    -> Voice Assets
    -> Caption Timing
    -> Resolved Timeline
    -> HyperFrames Render
    -> video-analysis QA
    -> Selective Repair
    -> final.mp4
```

Wan、Seedance、Vidu、Kling 或其它视频模型只负责生成某些 Shot 的 `generated_video` asset，不拥有 Production Runtime。

# 3. Current-State Audit

## 3.1 Implemented Today

当前 local `main` 已验证实现：

- `validate`、`run`、`resume` 三个 CLI command；
- default-local、显式 opt-in non-local 的 ComfyUI transport；
- Wan workflow examples；
- API/UI workflow loader；
- template + binding rendering；
- sequential Shot execution；
- bounded typed-error retry；
- optional last-frame chaining；
- `CharacterProfile` 和第一张 reference image 的 upload/hash；
- Manifest v1、atomic replace、clip/frame/normalized hashes；
- terminal failed Attempt persistence；
- direct last-frame dependency invalidation；
- attempt-qualified artifact staging、promotion 和 rollback；
- Legacy generation/delivery FPS compatibility semantics；
- ffmpeg probe、validate、extract、normalize、stitch；
- project-local `video-analysis` MCP 的 probe、frames、transcribe、scene detection、heuristic review 和 optimization helpers。

完整证据和剩余缺陷见 `docs/v0.2-runtime-baseline.md`。

## 3.2 Planned but Not Implemented

以下均不得写成当前行为：

- `ProductionProject`、Story、Scene、Storyboard、asset registry；
- Shot `visual_strategy`；
- image、voice、music、SFX、caption production domains；
- Resolved Timeline / Composition；
- HyperFrames、Remotion、ElevenLabs 或 Captions integration；
- general dependency graph 和 cross-domain selective rebuild；
- review/repair receipts、cost ledger、final acceptance；
- Provider abstraction、Take、Reference v2、Manifest v2；
- Human Review、Semantic Evaluation、Budget Guard、Cloud Egress；
- Seedance、Vidu、Kling 或其它 cloud video Provider。

## 3.3 Remaining Technical Debt

以下 debt 继续有效，但不再自动拥有新 v0.2 的第一主线：

- succeeded resume fast path 不验证 normalized clips 和 final output；
- config/template/binding、prompt、explicit init image 和 character reference hashes 尚未进入完整 validity；
- in-flight job handle 没有 crash-safe persistence；
- final output 没有 hash，多 artifact transaction 没有 journal/fsync 级恢复；
- word-level transcription output contract 不完整；
- current QA 把低帧差统一当作缺陷，不理解合法的 `static_image` / `image_motion` strategy；
- Legacy `defaults.fps` 同时承担 generation fallback 和 delivery FPS，新 domain 需要分离而不能破坏旧配置。

# 4. Goals

v0.2 必须实现：

1. Codex 可从小说、剧本、主题或 production brief 创建并维护完整 production project。
2. Story、Characters、Scenes、Storyboard 和 Shots 拥有 durable、可校验的 state。
3. Shot 不默认等于 video-generation prompt，而是选择明确的 visual strategy。
4. Images、video、voice、music、SFX 和 captions 都是 typed assets，带 provenance、hash、usage 和 dependency。
5. Audio 成为 first-class production domain。
6. AI-VIDEO 拥有 canonical resolved timeline；同一 project/run 只有一个 active renderer owner。
7. 修改一个 input 只 invalidates 真正依赖它的 artifacts。
8. Codex 能读取 status、执行生成/渲染、调用 QA、诊断问题并只修复受影响部分。
9. 基础 AI 漫剧不依赖 Video Provider。
10. Legacy Wan path、CLI、Manifest v1 和 flat run layout 在迁移期继续可用。
11. 所有 remote/paid capability 保持 explicit opt-in、可预估、可审计、可停止。

# 5. Non-Goals

v0.2 不负责：

- 研发新的 image、voice 或 video foundation model；
- 要求每个 Shot 都有连续角色动作；
- 自动把所有静态视觉升级为生成视频；
- 在仓库内实现通用 planner、memory 或 multi-agent framework；
- 同时维护两套 canonical timeline；
- 把 HyperFrames 和 Remotion 串联成两次完整 render；
- 把 Captions.ai 的 burned-in video 当成基础 caption data；
- 在 P0/P2 中引入 cloud API、secret、付费 submit 或新 runtime dependency；
- 在没有 strategy-aware evidence 时宣称 identity、continuity 或 semantic quality 已通过；
- 静默改变 Legacy CLI、Manifest v1 或 `runs/<run_id>/` layout。

# 6. Design Principles

## 6.1 Agent-First

Codex 负责理解目标、拆解故事、选择 strategy、调用 skills/tools、author composition、解释 QA 和提出 repair。Python runtime 只执行可验证 contract，不推测 creative intent。

## 6.2 Tool-and-Skill-First

外部能力优先通过 Codex skill/plugin/CLI adapter 调用。只有当 durable recovery、batch execution、typed error、cost/security 或 deterministic test 明确要求时，才在单独 slice 中提出 Python runtime dependency。

## 6.3 Durable-State-First

任何 material production action 前后都必须有 durable input、status 和 receipt。Plugin output 只有在 materialize、hash、register 后才成为 production asset。

## 6.4 Deterministic-Core, Generative-Edges

Story decomposition、prompting、asset generation 和 semantic diagnosis 可以是 generative。Schema validation、fingerprint、dependency resolution、timeline resolution、render invocation、artifact verification 和 invalidation 必须 deterministic。

## 6.5 One Owner per Contract

一个 state surface 只能有一个 canonical owner。Adapter 可以转换或执行，但不得创建第二份可独立变化的 timeline、asset registry 或 final status。

# 7. Architecture

```text
User Goal / Source Material
            |
            v
   Codex Production Agent
            |
            | reads/writes validated project artifacts
            v
  AI-VIDEO Production Harness
  +-------------------------------+
  | Brief / Story / Bibles        |
  | Storyboard / Shot Plan        |
  | Asset Registry / Provenance   |
  | Dependency Graph / Status     |
  | Resolved Timeline             |
  | Review / Repair Receipts      |
  +-------------------------------+
       |          |          |
       v          v          v
 Image tools   Audio tools   Optional video tools
       |          |          |
       +----------+----------+
                  |
                  v
       HyperFrames renderer adapter
       (Remotion optional, exclusive)
                  |
                  v
              final.mp4
                  |
                  v
          video-analysis QA
                  |
                  v
       Codex diagnosis and repair
```

## 7.1 Canonical Owners

| Contract | Canonical Owner | Non-Owners |
| --- | --- | --- |
| Creative intent and production decisions | Codex + approved production artifacts | Python heuristics、renderer |
| Project schema and validation | AI-VIDEO Python harness | plugins、providers |
| Asset identity and immutable provenance | Asset Registry | filesystem discovery、renderer output names |
| Mutable lifecycle, desired/applied fingerprints and active revision | Production Manifest | Asset Registry、Dependency Graph、Agent memory |
| Dependency and invalidation | Dependency Graph resolver | Shot ordering、directory order、provider adapter |
| Temporal order, duration and layer assignment | `ResolvedTimeline` | HyperFrames HTML order、Remotion component order、ffmpeg concat list |
| Default render execution | HyperFrames adapter | Python pipeline、Remotion、Captions.ai |
| Caption text and timing | Caption Track | renderer CSS/template、burned-in video |
| Caption layout and drawing | selected renderer | transcription provider、Caption Track |
| Audio source identity and timing | Audio assets + resolved audio tracks | TTS provider、renderer filesystem scan |
| QA evidence | Review Receipt | mutable console output、unrecorded agent judgment |
| Repair decision | Codex + Repair Receipt | auto-edit heuristic alone |

# 8. Tool and Renderer Decisions

## 8.1 Environment Audit

截至 2026-08-09，使用 `codex-cli 0.144.1` 审计的当前 Codex environment：

| Capability | Current Status | Evidence and Consequence |
| --- | --- | --- |
| HyperFrames | Marketplace `0.1.2` available，但 `installed=false`、`enabled=false`；本机只有 cached bundle，没有 active tool 或 PATH binary | 可读取的 skill/CLI contract 显示 `npx hyperframes` 提供 HTML/CSS/GSAP composition、lint、inspect、preview、render、transcribe 和 TTS。P3 前仍需单独安装、spike 和版本锁定授权。 |
| Remotion | Marketplace plugin `1.0.3` available，但 `installed=false`、`enabled=false`；remote cache manifest 为 `1.0.7`，存在版本漂移；仓库没有 Remotion project 或 CLI | 官方能力覆盖 React composition、audio、captions、Node/Lambda rendering；适合作为 optional React/data-driven adapter。Plugin skill bundle 的 license 不能外推到 Remotion engine，实施前必须检查 Remotion License。 |
| ElevenLabs | 当前 marketplace、environment 和 repo 未发现 plugin、skill、CLI 或 SDK | 官方 REST/SDK 支持 TTS、dialogue、character timestamps、Forced Alignment、STT word timestamps、SFX 和 music。P4 优先作为 opt-in Voice/Timing Provider，通过 Codex tool/skill 或 thin adapter 评估。 |
| Captions.ai / Mirage | 当前 marketplace、environment 和 repo 未发现 plugin、skill 或 SDK | 当前公开 video-caption flow 会 upload 9:16 video、transcribe、按 template 直接烧录并输出新 video；公开 flow 未提供 raw word timing。它不适合作为 canonical Caption Track 或默认 renderer。 |
| video-analysis | project-local MCP 已实现 | 可复用 probe、frames、Whisper、scene detection 和 technical heuristics；必须先 strategy-aware 才能成为 v0.2 QA gate。 |

本机 `pip` 中的 `hyperframe` Python package 与 HyperFrames video renderer 不同，不得当成安装证据。

## 8.2 HyperFrames Decision

选择 HyperFrames 作为 v0.2 default renderer target，原因：

- agent-native plain HTML/CSS/GSAP authoring；
- seekable、frame-addressable composition；
- image、video、audio、captions、motion graphics 和 transitions 进入同一 render；
- `lint`、`inspect` 和 machine-readable output 适合 Codex repair loop；
- local CLI 和 Apache-2.0 license 与 reuse policy 相容；
- 不要求 AI-VIDEO 把 React project 作为第一条 production dependency。

这是 architecture decision，不是当前安装或 production-readiness claim。HyperFrames 当前仍是 `0.1.x`，P3 必须以 pinned version 做 preview/render parity、timing、audio/caption、failure/recovery 和 deterministic fixture spike；spike 不通过时停止实施并回到 renderer decision gate。

Production-level canonical composition state 是 AI-VIDEO 的 `ResolvedTimeline`；selected renderer 的 canonical renderable composition source 则归对应 adapter。默认 path 中，HyperFrames HTML/CSS/GSAP source 拥有 motion、caption layout 和 visual implementation，并且必须从 `ResolvedTimeline` materialize、hash 和验证。HyperFrames adapter 不得回写 Story、Shot intent 或 Asset Registry identity。

## 8.3 Remotion Boundary

Remotion 保留为 optional renderer adapter，适合已有 React scene library、复杂 data-driven component 或 batch/template 产品化场景。Remotion engine 使用 special Remotion License；任何 commercial/company use 必须在 P3/P9 相关 plan 中重新核对适用条件，不能把 Codex plugin manifest 的 license 当作 engine license。

规则：

1. `renderer.kind` 在 project/run materialization 前显式选择并持久化。
2. 一个 render attempt 只能选择 `hyperframes` 或 `remotion` 之一。
3. 禁止 `HyperFrames -> Remotion -> final` 或反向 double render。
4. 切换 renderer 会 invalidates renderer source、render 和 downstream review，不会 invalidates image、voice 或 caption timing assets。
5. Remotion adapter 只有在独立 plan 证明真实需求、license 适用性和 parity test 后才实现。

## 8.4 Captions.ai Boundary

Captions.ai / Mirage 只可能作为 future optional post-process/export Provider。只要它不能返回 AI-VIDEO Caption Track 所需的 raw text/timing contract，就不得进入基础 pipeline，也不得接管 final renderer。

# 9. Production Domain Model

```text
ProductionProject
├── ProductionBrief
├── Story
├── Characters[]
├── Scenes[]
├── Storyboard
├── Shots[]
├── AssetRegistry
│   ├── image
│   ├── video
│   ├── voice
│   ├── music
│   ├── sfx
│   └── caption
├── DependencyGraph
├── CompositionSpec
├── ResolvedTimeline
├── Reviews[]
├── Repairs[]
└── Renders[]
```

## 9.1 Production Project

`ProductionProject` 提供 project ID、schema version、title、delivery profile、default language、renderer policy/default preference 和 artifact roots。它引用其它 artifacts，不把所有内容塞进一个超大 JSON。当前 active revision、resolved renderer selection 和 applied state 只能从 Production Manifest 读取；project config 的 default preference 不是第二个 lifecycle owner。

Proposed v2 layout 只能由显式 v2 project 创建：

```text
projects/<project_id>/
├── project.yaml
├── creative/
│   ├── brief.yaml
│   ├── story.yaml
│   ├── characters/
│   ├── scenes/
│   ├── storyboard.yaml
│   └── shots/
├── assets/
│   ├── registry.<revision>.json
│   └── files/
├── state/
│   ├── manifest.json
│   └── dependency_graph.<revision>.json
├── composition/
│   ├── spec.json
│   ├── resolved_timeline.json
│   └── renderer/
├── reviews/
├── repairs/
└── renders/
```

该 layout 是 proposed contract；P2/P5/P3 必须分别实现并迁移，当前 `runs/` 不变。

## 9.2 Story, Characters and Scenes

- `Story`：logline、synopsis、acts/beats、source references、language 和 revision。
- `Character`：identity、appearance bible、wardrobe、voice profile、reference assets、allowed variations 和 revision。
- `Scene`：location、time、mood、participants、continuity constraints 和 visual references。
- `Storyboard`：有序 beats 与 Shot references；它表达 narrative intent，不表达 renderer layer implementation。

所有 creative artifact 都必须有 stable ID、schema version、content hash、creation receipt 和 source provenance。内容变化创建新 revision；immutable artifact 本身不维护 mutable `updated_at` 或 lifecycle status。

## 9.3 Shot

Shot 是 narrative/composition unit，不是 Provider request。它至少表达：

- stable `shot_id`；
- scene/storyboard reference；
- intent、dialogue/narration 和 duration policy；
- character/scene continuity constraints；
- `visual_strategy`；
- required input asset roles；
- composition directives；
- review policy；
- current desired fingerprint。

Provider-specific prompt、model、seed 或 workflow binding 属于 Asset Generation Request，不属于 Shot identity。

# 10. Asset Model

每个 `AssetRecord` 必须包含：

- stable `asset_id` 和 `asset_type`；
- immutable artifact path/URI snapshot；
- content hash、size、MIME、duration/dimensions 等 measured metadata；
- source kind：`imported | generated | derived`；
- generator/tool/provider name 和 version；
- input artifact IDs 和 input fingerprint；
- creation receipt ID；失败的 generation/import attempt 记录在 Manifest lifecycle/attempt records，不伪造 AssetRecord；
- usage/license/egress metadata；
- cost receipt ID；
- 所属 immutable registry snapshot 的 revision ID；record 不重复保存会导致自引用 hash 的 revision 字段。

允许 asset types：

```text
image
video
voice
music
sfx
caption
composition_source
render
review_evidence
```

Asset Registry 是 append-only immutable identity/provenance catalog，不拥有 `fresh | stale | failed | blocked | superseded` 等 mutable lifecycle。Asset file 存在不等于 registered；只有 validation、hash 和 registry revision commit 完成，并且 Production Manifest atomic switch 到该 registry revision 后，才可被下游 active state 引用。

# 11. Shot Visual Strategy

`visual_strategy` 必须是以下显式值之一：

| Strategy | Required Inputs | Expected Render Behavior | Video Provider Required |
| --- | --- | --- | --- |
| `static_image` | one or more image assets | 稳定构图，可有切换但无连续 camera transform | No |
| `image_motion` | image asset + deterministic motion directive | pan、zoom、parallax、reveal 或 layered motion | No |
| `motion_graphics` | text/data/vector/image assets + animation directive | typography、cards、diagram、particles、transitions | No |
| `generated_video` | generation request + resulting video asset | normalize/trim/place generated clip | Yes, only for this asset |
| `existing_video` | imported/stock video asset | trim/place/overlay | No generation Provider |
| `hybrid` | explicit combination of assets and layers | renderer combines video/image/graphics deterministically | Optional |

Validation rules：

- `static_image` 不得因为低 frame difference 自动失败。
- `image_motion` 必须有 deterministic motion parameters，而不是只写“更有动感”。
- `generated_video` 必须解释为什么 image/motion-graphics path 不足。
- `hybrid` 必须列出每个 source asset 和 layer role，不能成为 arbitrary escape hatch。
- Shot strategy change invalidates composition and strategy-specific assets only when their required inputs change。

# 12. Audio Model

Audio 是 first-class domain，不是 video Provider 的附带字段。

## 12.1 Track Types

```text
dialogue
narration
ambience
sfx
bgm
```

每个 Audio asset/track 必须记录 source、speaker/voice、language、script hash、duration、sample rate、channels、loudness metadata、timing、gain、fade、ducking group 和 provenance。

## 12.2 Voice Provider

ElevenLabs 是首选 opt-in `VoiceAssetProvider` candidate，但不是 Python core dependency。优先路径：

1. Codex 读取 ElevenLabs skill/tool contract。
2. Harness 生成 immutable Voice Generation Request 和 budget/egress preview。
3. 获得 explicit authorization 后调用 provider。
4. Audio 与 alignment result materialize 到本地。
5. Harness probe、hash、register 并写 cost/provenance receipt。

若当前 Codex environment 没有可调用的 ElevenLabs skill/plugin，可用独立 P4 plan 比较 official SDK、REST thin adapter 或 local fallback；不得在本 spec 中假设已安装。

## 12.3 Audio Resolution

Voice 文案变化会 invalidates voice asset、alignment/caption timing、resolved audio timeline、render 和 review。它不会 invalidates unrelated images。

BGM、ambience 或 SFX 变化只 invalidates resolved audio timeline、render 和 audio-related review，除非 Shot duration policy 明确依赖该 asset。

# 13. Caption Model

Canonical `CaptionTrack` 是结构化数据，不是 burned-in pixels。它包含：

- source transcript/script ID 和 hash；
- language；
- segments；
- optional words；
- each item 的 start/end time；
- speaker reference；
- segmentation policy/version；
- confidence/source provider；
- style reference；
- timing fingerprint。

Caption timing source 优先顺序：

1. TTS provider alignment，例如 ElevenLabs timing response；
2. forced alignment against final voice asset；
3. local/remote transcription with word timestamps；
4. human-authored cue timing。

Caption style 不得改变 transcript 或 voice asset。Style change 只 invalidates composition source、render 和 visual review。

最终字幕 layout/drawing 归 selected renderer。HyperFrames 可用 HTML/CSS/GSAP 实现 frame-addressed captions；Remotion adapter 若启用则消费同一 `CaptionTrack`。Captions.ai burned-in output 不进入默认 path。

# 14. Timeline and Composition

## 14.1 Composition Spec

`CompositionSpec` 描述 semantic layers 和 edit intent：Shot order、asset references、transitions、caption style、audio policy、delivery profile。它不包含未解析的 filesystem scan，也不允许 renderer 自行决定 Shot order。

## 14.2 Resolved Timeline

`ResolvedTimeline` 是 canonical composition owner。它必须完全解析：

- delivery width、height、FPS、codec profile；
- visual tracks with integer `start_frame` / `duration_frames`；
- audio tracks with integer `start_sample` / `duration_samples`；
- caption cues snapped to display frames；
- asset IDs、hashes、trim、transform、opacity、z-order 和 transition；
- total duration；
- renderer kind/version；
- deterministic composition fingerprint。

禁止 renderer 根据目录名、mtime 或 lexicographic filename 推断 order。相同 `ResolvedTimeline`、renderer source、asset hashes 和 pinned renderer/tool versions 应产生 frame-equivalent output；byte-identical 只在 container/encoder contract 明确支持时要求。

## 14.3 Renderer Source

Codex 可以 author HyperFrames HTML/CSS/GSAP source，但该 source 必须：

- 引用 registered asset IDs/materialized paths；
- 由 `ResolvedTimeline` 驱动 timing；
- 通过 lint/inspect；
- 有 content hash 和 generation/edit receipt；
- 不包含 wall-clock randomness、隐式 network fetch 或 untracked asset。

# 15. Manifest and Provenance

v2 production state 继续保留 Manifest 的优点，但 Manifest 不再只是一组 ordered Shot records。Production Manifest 是唯一 mutable lifecycle、desired/applied fingerprint、active selection 和 current revision owner。

Manifest 必须回答：

- 当前 project revision、active Asset Registry revision 和 active Dependency Graph revision 是什么；
- 每个 creative artifact、asset、timeline、renderer source、render 和 review 的 desired/applied fingerprint；
- 谁或哪个 tool 在何时以哪些 inputs 创建 artifact；
- 哪个 artifact fresh、stale、failed、blocked 或 superseded；
- 每个 external action 的 provider、model/tool version、request receipt、cost 和 egress；
- final output 由哪些 exact asset hashes 和 timeline revision 构成；
- 哪个 QA/review receipt 支持 final acceptance。

原则：

- content artifacts immutable；新生成不能覆盖旧 provenance；
- desired state 与 applied state 分离；
- Manifest/state atomic write；
- secrets、Authorization headers、signed URLs 和 raw sensitive provider responses 禁止落盘；
- final render 必须有 hash；
- in-flight external job handle 在 submit 后立即 crash-safe 持久化；
- multi-artifact commit 的 power-loss strategy 必须由独立 plan 明确，不能只依赖进程内 rollback。

Asset Registry 和 Dependency Graph 都是 immutable、content-addressed/versioned snapshots：Registry 只保存 identity/provenance，Graph 只保存 typed edges 和 fingerprint contribution，不保存 mutable freshness/status。更新顺序是：写 temporary snapshot -> flush/fsync -> atomic rename -> 验证 snapshot hash -> 最后通过 atomic Production Manifest write 切换 active revision pointer 和 lifecycle state。Manifest atomic replace 是 transaction commit point；crash 后未被 Manifest 引用的完整 snapshot 是 orphan，可由显式 GC 回收，partial temporary file 永远不参与 resume。P2 只实现 read-only snapshot/pointer verification，不宣称 append-only activation 或跨文件 crash safety；首个写入或激活 v2 registry/graph snapshot 的后续 slice 必须实现上述 commit protocol 和 crash-injection tests。

# 16. Dependency and Invalidation

Dependency Graph 的 node 是 versioned creative artifact、Asset、Resolved Timeline、renderer source、Render 或 Review。Edge 必须记录 dependency reason 和 fingerprint contribution。Graph 是 immutable resolver input，不拥有 fresh/stale status；resolver 计算的 desired fingerprint 和 lifecycle transition 只提交到 Production Manifest。

示例：

```text
Character reference -> image generation request -> image asset -> Shot layer
Voice script -> voice asset -> alignment -> CaptionTrack -> Shot duration
Image asset -> ResolvedTimeline -> renderer source -> final render
Caption style -> renderer source -> final render
BGM -> resolved audio track -> final render
Hero video asset -> Shot layer -> final render
final render -> review evidence -> review receipt
```

## 16.1 Invalidation Matrix

| Change | Must Rebuild | Must Not Rebuild by Default |
| --- | --- | --- |
| Caption style | renderer source、render、visual review | voice、alignment、images、video assets |
| Caption text with unchanged voice | CaptionTrack、timeline、render、review | unrelated image/video generation |
| Voice script | voice、alignment、CaptionTrack、duration-dependent timeline、render、review | unrelated images |
| Voice settings/model | voice and downstream timing/render | Story、unrelated visuals |
| Character reference | dependent image/video assets、their Shot layers、render | unrelated scenes/assets |
| One image prompt | that image asset and consumers | other Shot assets、voice |
| One Hero video | that video asset and consumers | unrelated images/voice/captions |
| BGM | audio timeline、render、audio review | visual generation |
| Delivery FPS/resolution | resolved timeline、renderer source、render、review | source assets unless provider request explicitly depends on delivery |
| Renderer kind/version | renderer source、render、review | creative state and source assets |
| QA policy/version | affected review receipts | assets/render unless repair is approved |

Invalidation 必须 edge-by-edge 传播，并在 input fingerprint 相同处停止。不得使用“从 Shot N 开始全部 stale”的 blanket rule。

# 17. Codex Agent Operating Contract

Codex 必须按以下 loop 操作：

```text
inspect project status
-> propose/record production decision
-> validate desired state
-> preview capability, cost and egress
-> invoke one bounded skill/tool
-> materialize and register outputs
-> resolve dependency changes
-> compose/render only when inputs are fresh
-> run QA and persist review receipt
-> diagnose with evidence
-> propose repair set
-> execute only approved/allowed repair
-> rerender affected graph
-> record final acceptance
```

## 17.1 Required Agent Inputs

- `ProductionBrief`；
- current project/status summary；
- capability availability；
- stale/blocked reasons；
- cost/egress preview；
- unresolved human decisions。

## 17.2 Required Receipts

- production decision receipt；
- asset generation/import receipt；
- renderer selection receipt；
- render receipt；
- review receipt；
- repair receipt；
- cost receipt；
- final acceptance receipt。

## 17.3 Forbidden Agent Behavior

- 未写 durable request 就调用 material production tool；
- 未 register/hash output 就继续下游；
- 静默切换 provider、renderer 或 visual strategy；
- 因某个 asset 失败而 blanket rebuild 全 project；
- 把 console text 当作唯一状态；
- 在没有 evidence 时把 heuristic review 写成 semantic pass；
- 通过 Agent memory 替代 project state。

# 18. QA and Repair

QA 分层：

1. `technical`：artifact 存在、hash、codec、duration、resolution、audio stream、black/silent/clipping 等。
2. `layout`：caption overflow、safe area、text clipping、layer collision、transition boundary。
3. `strategy`：结果是否符合 Shot `visual_strategy`；`static_image` 不要求 video-like frame diversity。
4. `semantic`：story/character/continuity/prompt adherence；只有明确 evaluator 或 human evidence 时可声明。
5. `final_acceptance`：所有 required receipts fresh，且 final hash 对应当前 desired timeline。

Project-local `video-analysis` MCP 可继续拥有 technical evidence collection。它现有 `static_visuals` heuristic 必须在 P6 中改为 strategy-aware，且 `video_apply_optimization` 不得在新 mode 中未经 repair receipt 自动改变 creative intent。

Repair Receipt 必须记录：

- issue/evidence IDs；
- root-cause hypothesis；
- selected repair action；
- exact target artifacts；
- expected invalidation set；
- actor/authorization；
- before/after fingerprints；
- rerender/review result。

# 19. Cost, Security and Egress Boundaries

任何 paid/remote action 必须在 submit 前：

- 明确 provider/tool、model、billing unit 和 upper-bound estimate；
- 列出将上传的 files、hashes、sizes、MIME 和 purpose；
- 获得 project policy 允许和必要的 explicit authorization；
- 创建 reservation/decision receipt；
- 使用 secret reference，而不是写入 project state。

submit 后必须记录 actual usage/cost 或 unresolved reservation。Unknown outcome 不得 blind resubmit。

Local tools 也必须记录 tool/version 和 elapsed/resource evidence，但不需要伪造货币成本。Budget Guard 和 Cloud Egress 的详细安全 contract 复用旧 spec 的成熟设计，并在首次 paid Provider slice 前独立实施。

# 20. Legacy Compatibility and Migration

- 当前 `0.1.x` config、CLI、Manifest v1 和 flat `runs/` layout 保持不变。
- Legacy `run` / `resume` 不自动创建 v2 project，也不自动启用 Audio、renderer 或 remote Provider。
- Wan workflow loader、renderer、Comfy client 和 PipelineRunner 继续服务 Legacy mode。
- 在 future bridge slice 中，可将成功 Legacy clip 注册为 v2 `video` asset；bridge 必须保留原 Manifest path/hash 和 provenance。
- Local Wan/ComfyUI 在 v2 中保留为 future `generated_video` Visual Asset Provider adapter compatibility target，不得删除或绕开现有 production loading path。P8 先建立 provider-neutral core 与 deterministic fake；按 2026-08-17 P8 slice decision，MiniMax Hailuo V1 是第一个真实 Cloud adapter。这个顺序不把 Cloud 变成默认 path，也不阻塞 future local adapter。
- P1 的 terminal persistence、direct dependency、FPS compatibility 和 artifact rollback 保留；P1 plan 作为 historical/reusable stabilization record，不再是新 v0.2 主线。
- 旧 provider-centric spec 中 Budget、Cloud Egress、Take/Attempt 和 crash-safe job lifecycle 仍是 future P8 的 safety input，其 phase order 和 top-level domain 被本 spec supersede。

# 21. Open-Source Reuse Policy

原则：`reuse infrastructure, own production logic`。

## 21.1 Reuse

- HyperFrames：renderer、HTML composition primitives、lint/inspect、caption/audio/motion primitives。
- Remotion：仅在 optional adapter 获批时复用 React composition/render/caption primitives。
- ElevenLabs official API/SDK：voice、alignment、SFX/music capability；不复制 client。
- Existing local `video-analysis`：probe、frames、Whisper 和 technical QA evidence。
- Existing `ffmpeg_tools` / FFmpeg：media probing、normalization 和 low-level deterministic operations。

## 21.2 Own

- AI comic/video domain model；
- Character/Scene Bible；
- Storyboard/Shot contract；
- Asset Registry；
- production Manifest and dependency graph；
- selective rebuild；
- renderer-neutral Resolved Timeline；
- QA/repair receipts；
- cost/provenance；
- Codex operating contract。

## 21.3 Reference, Do Not Fork Wholesale

OpenMontage 证明了 agent-first pipeline、canonical artifacts、renderer selection、quality gates 和 no-video-provider production path 的可行性。AI-VIDEO 只融合这些边界思想，不复制其 AGPL code、整套 tool registry 或 12-pipeline architecture，也不让自身 domain 被上游内部 schema 绑定。

# 22. Phased Rollout

| Phase | Outcome | Runtime Scope |
| --- | --- | --- |
| P0 Product Reframe and Contract Migration | 新 product/spec、current audit、roadmap、contract pointers 和 supersession provenance | Docs only; completed by this reframe task |
| P1 Legacy Runtime Stabilization | terminal persistence、direct dependency、FPS contract、artifact rollback | Implemented on local `main`; release/integration still separate |
| P2 Production Project Core | ProductionProject、creative artifacts、read-only content-addressed Asset Registry verification、Shot visual strategy、validation | No writer/activation、renderer、Audio provider or cloud |
| P2A Production State Commit Protocol | atomic v2 project/registry snapshot commit、Manifest pointer switch、orphan/partial recovery contract | Required before any write-capable v2 asset/composition slice; crash-injection tests mandatory |
| P3 Deterministic Composition and HyperFrames Adapter | CompositionSpec、ResolvedTimeline、HyperFrames source/render receipts、single-renderer gate | No Remotion adapter unless separately approved |
| P4 Voice and Captions | Audio domain、Voice Provider contract、ElevenLabs opt-in candidate、alignment、CaptionTrack | Paid calls gated; no video Provider |
| P5 Dependency Graph and Selective Rebuild | fingerprints、edges、desired/applied state、precise invalidation | Migrates cross-domain rebuild truth |
| P6 Codex Review and Repair Harness | strategy-aware QA、review/repair/final acceptance receipts | No unapproved auto creative edits |
| P7 Image Asset Generation | image provider/tool contract、Character/Scene reuse、image provenance | Video Provider still unnecessary |
| P8 Optional Generated-Video Providers | Accepted Base AI Comic E2E 后先做 provider-neutral core + deterministic fake；MiniMax Hailuo V1 是首个真实 Cloud adapter，future Wan/ComfyUI local adapter复用同一 contract；cloud submit only after safety gates | generated_video asset production only；frame-accurate renderer consumption另行规划 |
| P9 Episode and Production Hardening | batching、cost rollups、migration hardening、performance、retention | Depends on proven core path |

Dependency and parallel rules are canonical in `docs/v0.2-agentic-production-roadmap.md`。

# 23. Acceptance Criteria

v0.2 product path is accepted only when：

1. 一个 explicit v2 project 可从 Story/Script 构建 Character、Scene、Storyboard 和 Shot artifacts。
2. 每个 Shot 有 valid `visual_strategy`，且至少支持 `static_image`、`image_motion` 和 `motion_graphics`。
3. 无 Video Provider 配置时仍能产出完整带 voice/captions 的 `final.mp4`。
4. HyperFrames 是默认 renderer target，Resolved Timeline 是 order/timing truth source。
5. Remotion 不在默认 path；若实现 adapter，project/run 只能选择一个 renderer。
6. Voice、music、SFX、captions 都有 typed asset/provenance。
7. Caption Track 保留 text/timing，renderer 只负责 layout/drawing。
8. 改 caption style 不触发 voice 或 visual asset regeneration。
9. 改 voice script 只重建 voice、alignment、dependent timing/composition/render/review。
10. 改一个 Hero video asset 不重建 unrelated images/voice。
11. Asset Registry 能回答 final output 的所有 source hashes、tools/providers 和 costs。
12. Resolved Timeline 对相同 inputs 产生相同 order、frame/sample boundaries 和 fingerprint。
13. Render receipt 包含 renderer/version、source hash、timeline fingerprint、output hash 和 measured metadata。
14. `video-analysis` technical QA 与 strategy-aware QA 分开记录。
15. Codex 可根据 persisted review evidence 创建 bounded Repair Receipt，并只执行 affected graph。
16. Remote/paid call 没有 explicit opt-in、budget 或 egress receipt 时 submit count 为 0。
17. Legacy `validate`、`run`、`resume`、Manifest v1 和 flat layout 继续通过 tests。
18. Local Wan path 仍可用，并且不成为 v2 non-video Shot 的隐式 dependency。
19. Crash/restart 后 project status 不依赖 Agent memory 或 console history。
20. 未实现 phase 不会被 README、AGENTS 或 baseline 写成 runtime truth。

# 24. Definition of Done

整个 v0.2 只有在以下条件全部满足时完成：

- 基础 AI 漫剧 path 在没有 Video Provider 时通过 end-to-end acceptance；
- Story、Characters、Scenes、Storyboard、Shots、Assets、Timeline、Reviews 和 Renders 都有 durable validated contracts；
- HyperFrames default render path 完成 lint、inspect、render 和 local no-network fake/fixture tests；
- Audio/Caption path 使用真实 measured duration/timing，而不是估算覆盖事实；
- dependency graph 对规定 mutation cases 通过 selective rebuild tests；
- review -> repair -> rerender loop 留下完整 receipts；
- final output 有 hash、current timeline fingerprint 和 fresh acceptance receipt；
- paid/cloud Provider 的 Budget、Egress、job persistence 和 secret redaction gates 已验证；
- Legacy suite 与 v2 suite 均通过；
- README 只描述实际落地 behavior；
- 每个 phase 有独立 acceptance、rollback 和 implementation authorization evidence。

# 25. External References

Capability 和 license 会变化，实施对应 slice 时必须重新核对 current official sources：

- HyperFrames repository and license: <https://github.com/heygen-com/hyperframes>
- HyperFrames CLI: <https://github.com/heygen-com/hyperframes/blob/main/packages/cli/README.md>
- Remotion documentation: <https://www.remotion.dev/docs>
- Remotion captions: <https://www.remotion.dev/docs/captions>
- Remotion repository and special license notice: <https://github.com/remotion-dev/remotion>
- ElevenLabs capabilities: <https://elevenlabs.io/docs/overview/intro>
- ElevenLabs speech with timing: <https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps>
- Captions.ai / Mirage video captions: <https://captions.ai/help/docs/api/video-captions>
- OpenMontage architecture reference: <https://github.com/calesthio/OpenMontage>

No external code is copied by this spec. HyperFrames and Remotion integration、ElevenLabs/Captions adapter、OpenMontage-derived structure all require their own current license and compatibility review at implementation time.
