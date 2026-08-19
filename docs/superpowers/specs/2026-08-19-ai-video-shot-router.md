# AI-VIDEO Shot Router Specification

## Status

本规范是独立的 docs-only proposed contract。当前 runtime 没有 Shot Router：`Shot.visual_strategy` 由 authoring data 显式给出，`VideoGenerationRequest` 由 caller 显式选择 mode/provider/profile，`VideoProviderRegistry` 只做 exact lookup 并禁止 selection/fallback。

本规范可以在 [Minimal Shot Continuity Proof specification](./2026-08-19-ai-video-minimal-shot-continuity-proof.md) 验收前完成设计，但 Router runtime implementation 被其 `C2_HARD_CUT_KEYFRAME_I2V` exit gate 阻塞。已有 `C1_CONTINUATION_I2V` technical proof 只证明尾帧原样续拍，不能替代该 gate。本文不得被描述为当前行为或 implementation authorization。

## Goal

用户只提供 Character Bible、canonical references、scene/shot intent、动作和质量/预算偏好。系统为每个 Shot 确定合适的 visual strategy 与 provider-neutral generation mode，使 AI 漫剧优先保持角色和场景一致性，而不是要求用户手工判断 T2V、I2V 或 R2V。

Router 的核心原则是：

- 固定主角、连续剧情、同服装、同场景和对话镜头优先使用视觉锚点；
- T2V 用于不依赖固定身份的自由生成，而不是 continuity 的默认路径；
- 上层 `Shot` 保持 provider-neutral，不出现 `h3_reference_to_video_with_three_images` 等 model-specific enum；
- planning-time 可以选择不同策略，但 sealed request 之后不得静默降级或 fallback；
- Provider selection、network、budget 和 authorization 始终显式。

## Current Runtime Truth

| Surface | Current Contract | Router Constraint |
| --- | --- | --- |
| `Shot.visual_strategy` | `static_image`、`image_motion`、`motion_graphics`、`generated_video`、`existing_video`、`hybrid` | 继续保持粗粒度 authoring/asset strategy，不增加 Provider-specific values |
| `Shot.character_ids`、`scene_id`、`continuity_constraints`、`motion_directives` | 提供高层叙事、身份与动作信息 | Router 只消费 exact revisions/hashes，不成为新的 authoring truth |
| `VideoGenerationMode` | `text_to_video`、`image_to_video`、`reference_to_video`、`video_edit`、`video_extend` | generation mode 属于 `VideoGenerationRequest`，不抬高到 `Shot.visual_strategy` |
| `VideoGenerationRequest` | sealed provider/model/profile、image/media bindings、continuity binding、output、base tuple 与 request hash | Router 输出必须在 request seal 之前被解析；sealed request 后不得改写 |
| `VideoProviderRegistry` | exact injected name lookup；未知 provider fail closed；无 selection/fallback | Router 不得把 Registry 改成隐式 ranking/fallback engine |
| P5 dependency resolver | 唯一 desired fingerprint 与 precise downstream invalidation owner | P5 只消费 activated Shot 与 sealed generation request 的 semantic projection，不消费并列 Router truth |
| `ProductionStateCommitter` | 唯一 durable writer/activation/recovery owner | Router 只能提出 authoring proposal；只有 committer 可把 proposal 物化为新 Shot/Storyboard revision 并激活 |

## Scope

本规范覆盖两个彼此分离的 pure resolver，但不增加第二份 durable `visual_strategy` truth：

1. `ShotVisualResolver`：从当前 Shot/Storyboard revision、intent 和可用资产产生 coarse `VisualStrategy` authoring proposal。proposal 不是 runtime truth；只有 `ProductionStateCommitter` 将其物化并激活为新的 Shot/Storyboard revision 后，`Shot.visual_strategy` 才成为 canonical truth。
2. `VideoGenerationResolver`：只读取已经激活、明确为 `generated_video` 或含 generated-video layer 的 `hybrid` Shot，决定 provider-neutral `VideoGenerationMode`、required reference roles、capability requirements 和 execution requirements。

Provider 实例仍由 Router core 之外的显式 production policy、authorization 和 exact registry name 选择。Router core 只返回 required capability set 和 execution requirements，不返回 ranked/eligible Provider list；它不得自行调用 Provider、申请预算、读取 secret、提交任务、激活候选或渲染。

## Non-Goals

- 不创建新的通用 Agent runtime、episode orchestrator、queue 或 public CLI。
- 不实现 Provider marketplace、自动成本竞价、自动 cloud fallback 或自动消耗免费 quota。
- 不修改 `Shot.visual_strategy` 为 model/provider-specific enum。
- 不把 `first_last_frame` 变成新的最高层 strategy；它属于 I2V request 的 binding/capability shape。
- 不改变 Manifest schema、artifact layout、Registry schema 或 CLI；若 durable Router receipt 被证明不可避免，必须另行 scope-expansion authorization。
- 不替代 Character Bible、storyboard、image generation、P5 dependency、P6 review/repair 或 human final acceptance。
- 不把 prompt 调整、crossfade、插帧或 V2V cleanup 描述成 continuity routing。

## Ownership Model

```text
Character Bible + Scene/Shot intent + exact available assets
                         |
                         v
                ShotVisualResolver
                         |
              authoring proposal only
                         |
                         v
       ProductionStateCommitter materializes/activates
                         |
                         v
        canonical activated Shot.visual_strategy
                         |
                         v
    explicit production policy selects exact Provider/profile
                         |
                         v
             VideoGenerationResolver
                         |
       mode + required bindings + capability requirements
                         |
                         v
       existing VideoGenerationRequest / P8 lifecycle
```

`ShotVisualResolver` 和 `VideoGenerationResolver` 均为 deterministic, no-I/O, no-network pure decision functions。它们不得持久化 mutable state。`ShotVisualResolver` 的 proposal 不得被 P5、composition 或 Provider 直接消费；只有 committer 激活后的 Shot revision 才能进入这些路径。`ProductionStateCommitter`、P5、`ResolvedTimeline` 和 HyperFrames 的既有 ownership 不变。

## Router Input Contract

`ShotVisualResolver` input 必须绑定 exact revisions/hashes，至少包括：

- Shot identity、intent、dialogue/narration presence、duration policy；
- `character_ids` 与每个角色的 narrative importance；
- Character Bible 与 canonical character reference identities；
- Scene identity 与 canonical scene reference；
- available Shot keyframe/first-frame/last-frame identities及其derivation lineage；
- activated upstream terminal evidence 与 `ContinuityConstraintSet`；
- motion directives：subject motion、camera motion、complexity、required performance；
- framing、camera axis/direction、entrance/exit 与 spatial-storytelling requirements；
- allowed visual strategies、generation modes和execution kinds；
- quality tier、latency/resource policy、episode budget policy与 explicit authorization state；
- Router policy id/version/content hash。

`VideoGenerationResolver` 额外读取 activated Shot、由外部 production policy 预先选择的一个 exact Provider/profile identity，以及该 profile 的 sealed capability snapshot。它不得看到一个用于自动 fallback 的 Provider list。若这个 exact selection 不支持 required mode/roles/output，结果是 blocked，不选择下一个 Provider。

缺失 reference 不能被解释为“可以 T2V”。Router 必须显式区分：资产确实不需要、资产尚未准备、Provider 不支持、策略不允许、预算不允许与授权缺失。

## Router Output Contract

`ShotVisualResolver` 的逻辑输出是 `ShotVisualRoutingProposal`，至少包含：

- exact target Shot identity/revision/content hash；
- proposed coarse `visual_strategy` 与需要物化的 provider-neutral Shot fields；
- stable semantic reason codes；
- policy id/version/hash 与 audit proposal hash；
- outcome：`proposed`、`blocked_missing_input`、`blocked_policy` 或 `blocked_authorization`。

proposal 不能作为 second truth 被 request、P5、composition 或 render 消费。若被接受，`ProductionStateCommitter` 必须创建并激活一个新的 Shot/Storyboard revision；既有 `Shot.visual_strategy`、`required_asset_roles`、`motion_directives` 等字段仍是唯一 durable authoring truth。policy-only 或解释文本变化若没有改变 authoring semantic projection，不得创建新 Shot revision。

`VideoGenerationResolver` 的逻辑输出是 `VideoGenerationRoutingDecision`，至少包含：

- exact activated target Shot identity/revision/content hash；
- 当需要 video generation 时的 selected `VideoGenerationMode`；
- ordered required binding roles，例如 `first_frame`、`last_frame`、`reference`、`reference_video`、`reference_audio`；
- exact required input asset identities/hashes；
- required capability set，而不是 Provider-specific payload；
- required execution kind/policy constraints，不包含 ranked/eligible Provider list；
- stable semantic reason codes 与 human-readable rationale；
- `semantic_routing_hash`：只覆盖会改变生成语义的 selected mode、bindings、inputs、capability/output requirements；
- `audit_decision_hash`：额外覆盖 policy id/version/hash 与解释信息；
- outcome：`selected`、`blocked_missing_input`、`blocked_capability`、`blocked_policy` 或 `blocked_authorization`。

只有 `semantic_routing_hash` 对应的 selected mode/bindings/inputs/capability/output projection可进入现有 request/P5 desired fingerprint。`audit_decision_hash` 和 policy identity本身不得导致 generation stale。第一版实现应优先由现有 activated Shot 与 `VideoGenerationRequest` 承载 durable semantic truth；默认不新增 Manifest/Registry schema。若 crash-safe audit 必须独立 reopen Router receipt，需先用 executable spike 证明现有 evidence 无法承载，再提出独立 schema/layout scope expansion。

## Stable Reason Codes

第一版至少稳定以下 provider-neutral reason codes：

- `NO_MOTION_REQUIRED`
- `LIGHT_MOTION_FROM_KEYFRAME`
- `IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR`
- `UPSTREAM_TERMINAL_REQUIRES_I2V`
- `HARD_CUT_REQUIRES_DERIVED_KEYFRAME`
- `CONTINUOUS_TAKE_USES_TERMINAL_FIRST_FRAME`
- `CANONICAL_REFERENCES_ENABLE_R2V`
- `FREE_ENVIRONMENT_MOTION_ENABLES_T2V`
- `HERO_SHOT_REQUIRES_HYBRID_OR_V2V`
- `MISSING_CHARACTER_REFERENCE`
- `MISSING_SCENE_REFERENCE`
- `MISSING_CONTINUITY_TERMINAL`
- `PROVIDER_CAPABILITY_DENIED`
- `LOCAL_RESOURCE_POLICY_DENIED`
- `REMOTE_AUTHORIZATION_REQUIRED`
- `BUDGET_POLICY_DENIED`

Reason codes 不得包含 model name，不能通过自由文本决定 replay/invalidation semantics。

## Deterministic Routing Rules

规则按以下优先级执行，前面的 blocking rule 不得被后面的自由生成覆盖：

### Rule 1: Existing or Static Asset Suffices

- 已有 exact video asset 且无需再生成：`existing_video`。
- 没有可见运动要求：`static_image`。
- 只有 pan/zoom/parallax/轻微层运动，且不需要角色真实动作：`image_motion`。
- 主要是文字、图形、粒子或版式动画：`motion_graphics`。

### Rule 2: Continuity Is Required

Router必须先区分continuity intent，不能只因存在upstream terminal就统一选择同一种I2V：

- `continuous_take`：叙事要求从exact terminal pose/pixels直接续拍。选择`generated_video + image_to_video`，`first_frame`必须直接绑定upstream terminal，reason为`CONTINUOUS_TAKE_USES_TERMINAL_FIRST_FRAME`。
- `hard_cut`：叙事要求新的framing或camera distance，但仍需延续角色、场景、轴线和动作。先进入P7 hard-cut keyframe preparation，required references为`character + continuity_terminal`；keyframe激活后再选择`generated_video + image_to_video`，`first_frame`绑定derived keyframe，reason为`HARD_CUT_REQUIRES_DERIVED_KEYFRAME`。

hard-cut decision必须seal“terminal -> keyframe request/output -> video first frame”lineage。不得把terminal原样first-frame伪装为hard cut，也不得生成一个只看character/scene、不真实消费terminal的独立keyframe。

如果selected Provider/profile不支持required role set，返回capability blocked。不得删除terminal lineage改跑普通R2V/T2V，也不得静默切换Provider。

### Rule 3: Important Character Without Upstream Terminal

- 有 canonical character/scene references 且预先选择的 exact Provider/profile 明确支持 exact reference set：`reference_to_video`。
- 预先选择的 exact Provider/profile 只支持 first-frame I2V：先通过现有 image path 生成/选择绑定 Character Bible 与 Scene reference 的 Shot keyframe，再选择 `image_to_video`。
- 没有可验证 character reference：返回 `blocked_missing_input`，进入 keyframe/reference preparation；不得静默选择 T2V。

### Rule 4: Free Generation Is Appropriate

没有重要固定角色、没有 continuity edge、没有必须保持的精确场景 identity，且需要复杂自由运动时，允许 `text_to_video`。典型场景包括 establishing shot、环境、风景、梦境、抽象画面、特效和无固定角色过场。

### Rule 5: Hero and Repair Paths

明确的 hero shot、已有视频重演、style transfer 或局部修复可选择 `video_edit`、`video_extend` 或 `hybrid`，但必须由单独 policy 明确允许并具备 exact source video binding。它们不是 continuity failure 的自动 fallback。

## Decision Matrix

| Important Character | Upstream Terminal | Canonical References | Motion Need | Decision |
| --- | --- | --- | --- | --- |
| No | No | Not required | None | `static_image` |
| No | No | Not required | Light transform only | `image_motion` |
| No | No | Not required | Complex/free | `generated_video + text_to_video` |
| Yes | Yes, continuous-take | Any | Character action | `generated_video + image_to_video + terminal first_frame` |
| Yes | Yes, hard-cut | Character + terminal | Character action/new framing | prepare derived keyframe, then `generated_video + image_to_video` |
| Yes | No | Yes, Provider supports exact set | Character action | `generated_video + reference_to_video` |
| Yes | No | Yes, Provider only supports first frame | Character action | prepare keyframe, then `generated_video + image_to_video` |
| Yes | No | No | Any generated motion | `blocked_missing_input` |
| Any | Any | Any | Existing approved clip suffices | `existing_video` |

相同 inputs、policy version 与 capability snapshot 必须产生相同 audit decision；相同 selected strategy/mode/bindings/inputs/capability/output projection 必须产生相同 semantic routing hash。规则冲突必须按固定 priority 解决，不能依赖 dict order、Provider registration order 或模型自由文本判断。

## Provider and Capability Resolution

Router core 只输出 capability requirements。Provider-specific mapping 保留在 adapter/profile：

- Local H3 `fl2va`用于terminal-first-frame或derived-keyframe-first-frame；optional `ref2va`保持独立capability；
- MiniMax cloud Hailuo 2.3；
- Seedance 2.0 Mini；
- 未来明确注册的 Provider。

Router core 之外的 production policy 必须显式给出 exact provider/profile，再交由 `VideoProviderRegistry.resolve(name)` 做 exact lookup。Provider/profile identity随后进入 sealed `VideoGenerationRequest`。capability denial、resource denial、budget denial或 authorization denial必须 fail closed，不得尝试列表中的“下一个 Provider”。

planning-time 在 decision seal 之前可以比较 allowed options，例如优先 local draft、人工选择 paid final。decision/request seal 之后，mode、reference roles、Provider、profile、output 或 execution kind 的任何变化都必须产生新 decision/request identity，而不是 runtime downgrade。

## Portfolio Guidance

对第一版约 5 分钟 AI 漫剧，以下比例只作为 planning prior，不是逐集硬 quota 或 validation rule：

- `50-60%`：Static Image / Image Motion；
- `25-35%`：I2V / Reference-to-Video；
- `5-15%`：T2V；
- 少量：V2V / Hybrid / Hero Shots。

Router 不得为了凑比例违背单 Shot 的 continuity、quality 或 capability constraints。比例只用于成本/动态度预估和事后报告，不进入 Shot acceptance verdict。

## Budget and Authorization

- Local GPU 不是零成本；resource policy必须限制 concurrent jobs、VRAM、最长时长与 bounded retry。
- Remote Provider 必须经过 existing Paid Provider Gate、Cloud Egress、secret reference、budget reservation 和 one-use permit。
- `.env` 中存在 key、Provider 有免费次数、旧 live proof 成功或 episode budget 尚有余额，都不等于当前 Shot 已授权。
- Router 最多返回 `blocked_authorization` 或 remote execution/capability requirement；不得返回自动候选排序、自行 mint permit、submit、升级 local draft 或消耗 quota。

## P5 Invalidation and Replay

Router 不建立第二 dependency graph。P5 继续从 activated Shot 和 sealed request 消费以下 semantic inputs：

- target Shot revision/content hash；
- activated Shot 的 selected strategy与生成相关 fields；
- selected mode；
- required reference/terminal asset hashes；
- selected Provider/profile/capability snapshot；
- selected output requirement与其他会改变 generated bytes语义的 canonical fields。

Router policy id/version/hash、audit decision hash、解释文本以及没有改变上述 semantic projection 的 reason-code变化只用于 audit，不进入 P5 desired fingerprint。

变化只沿既有 P5 graph 的真实 closure传播：

- Router policy变化若没有改变 activated Shot 或 generation semantic projection，该 Shot不得 stale，也不得仅为记录新policy创建Shot revision；
- activated Shot semantic fields、generation semantic routing、reference、terminal或Provider/profile identity变化，只 stale对应 Shot generation与真实 downstream closure；
- 不得因 episode 中一个 Shot 改路由而 blanket stale所有后续 Shot；
- exact replay必须复用相同 decision/request/evidence，Provider submit/fetch/activation/render 增量为零。

## P3 and P4 Invariants

- `ResolvedTimeline` 继续独占 order/frame/sample/timing。
- generated MP4、existing video、static image和hybrid layers继续进入既有 `CompositionSpec -> ResolvedTimeline -> HyperFrames`。
- narration、dialogue、ambience、SFX、BGM、captions与final mux语义不变。
- Provider native audio不能绕过P4 audio ownership。
- transition只是表现手段，不能改变 Router 对 continuity conditioning 的选择。

## Failure Semantics

Router 失败必须是 typed, stable, user-actionable：

- missing reference：指出缺失的 role/asset，进入 image/reference preparation；
- capability denial：指出 mode/role/output不支持，Provider call count为零；
- local resource denial：保持 blocked，不 fallback remote；
- remote authorization/budget denial：保持 blocked，不 fallback另一个账户或Provider；
- contradictory authoring inputs：返回 invalid decision，不猜测用户意图；
- sealed policy/input drift：拒绝复用旧 decision/request，要求重新 resolve。

## Acceptance

### Unit Contract Tests

1. Decision Matrix 中每一行都有 deterministic test。
2. important character 缺 reference 时 blocked，不选择 T2V。
3. upstream terminal 存在时优先 I2V，且不能被 R2V/T2V覆盖。
4. static、image motion、motion graphics、existing video和hybrid边界分别测试。
5. 相同 canonical inputs 产生相同 audit/semantic hashes；无关自由文本/registration order不改变 semantic result。
6. policy-only变化只改变 audit hash；reference/terminal/capability/selected output变化精确改变 semantic hash。
7. authoring proposal不能被P5/request/render消费；只有committer激活后的新Shot revision成为canonical strategy。

### Integration Contract Tests

1. accepted authoring proposal只能由`ProductionStateCommitter`物化/激活为新Shot revision；P5继续只消费activated Shot。
2. `VideoGenerationRoutingDecision`可构造现有 `VideoGenerationRequest`，不增加 Provider-specific core fields。
3. unsupported role/mode/profile 在 preview/submit前 fail closed，transport call count为零。
4. Local-only policy不触发 remote lookup、secret access、Budget Guard或network。
5. remote option未授权时返回 blocked；授权后仍由 existing Paid Provider/committer lifecycle拥有 submit。
6. exact replay不重复 decision side effects、Provider、activation或render。
7. policy-only audit变化不 stale；semantic变化时P5仅 stale受影响 Shot与真实 downstream closure。

### Quality Acceptance

Router technical acceptance只证明规则实现正确，不证明生成质量。至少用一组 representative episode shot list 做人工 audit：每个 Shot 的 strategy/mode、reason code、required references和blocked reason必须可解释；所有固定主角 continuity Shot不得被路由到裸 T2V。

Local H3、Hailuo、Seedance等各 Provider 的 live/quality acceptance继续独立报告。一个 Provider成功不能证明 Router 对另一 Provider的选择正确。

## Implementation Gate

开始 Router runtime implementation 前必须同时满足：

1. Minimal Shot Continuity Proof 的 `C2_HARD_CUT_KEYFRAME_I2V` 已达到technical、local live与subjective continuity acceptance；C1 proof不能替代；
2. Router implementation plan 已独立完成并获用户授权；
3. exact file/module ownership、RED tests、focused verification 与 rollback 已稳定；
4. 已确认第一版不需要 schema/layout/CLI mutation，或对应 scope expansion 已另行获批；
5. live/paid Provider 调用仍有独立 task-scoped authorization。

## Rollback

Router 必须可以作为 pure proposal/decision layer整体删除。删除后恢复当前显式 authoring/caller behavior：`Shot.visual_strategy` 由项目数据给出，caller 显式构造 `VideoGenerationRequest` 并选择 exact Provider/profile，`VideoProviderRegistry` 继续 exact lookup。移除 Router 不得删除已经由 committer 激活的合法 Shot revisions。P8 lifecycle、continuity evidence、P5、P3/P4、Static Image、Legacy CLI/layout 与历史 artifacts 不受影响。
