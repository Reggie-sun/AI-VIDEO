# AI-VIDEO Control-Plane Playbook

这份文件承接 AI-VIDEO control-plane 的低频执行细节。

它是 repo-local playbook，不是新的 workflow 真源，也不拥有 Product state、Manifest、Registry、Dependency Graph、Timeline、Renderer、Provider lifecycle 或 delivery truth。

冲突时遵循 `AGENTS.md` 的 `Conflict Resolution`；本文件只能补充执行细节，不能覆盖用户指令、当前 code/tests/runtime evidence、`docs/agent-primary-contract-matrix.md` 或 `.agent/harness/policy.yaml`。

## 1. Creative Skill Routing And Preflight

AI-VIDEO remains the sole owner of production truth. External Skills provide advisory knowledge only unless an explicitly approved project contract says otherwise. Skill guidance MUST be translated into AI-VIDEO domain contracts before execution and MUST NOT mutate or own canonical state.

Use the minimum matching Skill set. Installation、description matching 或“本仓库生产视频”本身不构成触发条件。纯 production-state、asset、schema、dependency、timeline、render、activation、recovery 或 Provider-lifecycle 工作只使用 AI-VIDEO code 与 accepted contracts。

### Agent-Side Image Generation Provider Preference

当用户明确要求 Agent 实际生成图片时，默认优先使用 project-local `gpt-image-2` MCP 的 `chatgpt-web` backend；本地 ComfyUI 作为次选。该优先级只约束 Codex / Agent 的交互式工具选择，不是 Production runtime Provider selector，不改变 Legacy local-first default，也不得让 MCP 成为 `ImageAssetProvider`、writer、Asset Registry、Manifest、activation、recovery 或 delivery truth owner。

- 调用前必须用 `backend_status` 验证 selected backend 精确为 `chatgpt-web` 且 ready；禁止为了可用性切换到 `api` 或 `auto`。Provider preference 本身不构成 live authorization；只有用户当前明确要求实际生图时，才可在该 accepted scope 内执行最少必要调用。
- 只有在 MCP 于任何 remote submit 前明确未配置或不可用，或用户明确指定本地生成时，才可选择 loopback-only ComfyUI。`generate_image` 已调用、超时或 outcome unknown 后必须 fail closed，不得自动切换 ComfyUI、重复提交或把 fallback 当成 retry。
- MCP 返回的文件、metadata、`saved` / `ready` 状态只是真实来源待核验的 raw candidate，不是 canonical asset、provenance、QA acceptance、activation 或 final delivery。候选进入 Production 时必须通过既有 truthful import contract 记录实际 actor/source，或通过未来单独批准的 AI-VIDEO Provider adapter；任何 durable mutation 仍只归 `ProductionStateCommitter`。
- 不得保存、打印或提交 ChatGPT session material、browser profile、signed source URL 或 raw credential。MCP output directory 不得作为 Production artifact root；失败诊断截图、页面文本与 conversation metadata 不得进入 repository、receipt 或交付物。

### Creative Skill Preflight Gate

当 task 包含 generated-video Shot 设计、跨 Shot continuity、image/video prompt 编写或修改、Provider/model-specific prompt adaptation、camera/motion design、generation failure diagnosis 或 creative iteration 时，匹配的 Creative Skill 从建议项升级为 task-level mandatory preflight。Agent MUST 在首次编写或修改 prompt、continuity contract 或 execution script 之前完成步骤 1–2，并在进入 live/paid Provider exact preview、permit mint/consume 或 POST 之前完成步骤 3–4：

1. 根据 Routing Precedence 选择并实际读取最小匹配 Skill；不得仅凭记忆、Skill 名称或 `AGENTS.md` 摘要声称已使用。
2. 在 commentary 中声明选中的 Skill、选择原因，以及每个 Skill 将约束的具体 creative concern。
3. 在进入 live/paid Provider exact preview、permit mint/consume 或 POST 之前，报告最小 `Creative Skill Preflight Evidence`：
   - semantic Shot `open_state`、`close_state` 与必须保持/改变的 continuity invariants；
   - actual terminal / reference handoff、screen axis、action direction 与 camera endpoint；
   - Provider/model-specific prompt adaptation，以及 Skill guidance 对最终 prompt 造成的具体变化；
   - relevant Skill lint/preflight 结果，或该 Skill 没有 executable lint surface 的明确说明。
4. 若 mandatory preflight 或上述 evidence 不完整，Agent MUST fail closed，不得进入付费 preview、mint/consume submit permit 或执行 Provider POST。

该 gate 是 Agent authoring/process prerequisite，不是 Production runtime contract。Run script、Provider adapter、Manifest、receipt、timeline 与 renderer MUST NOT import、联网调用或依赖 Creative Skill；`runtime_skill_calls = 0` 是正确边界，不能被解释为 Agent authoring 阶段可以跳过 Skill。若 task 只涉及 production state、asset identity、schema、dependency、timeline consumption、render execution、activation、recovery 或 Provider lifecycle，且不创作或修改 creative intent/prompt，则不触发本 preflight；Agent 应明确说明该判定，不能把它用于规避真实 creative work。

### Skill Selection

`open-video` MUST use when the task needs Director-level concept/script decomposition、ordered Shot planning、coverage、per-Shot objective、multi-Shot segmentation、transition/handoff intent 或 review criteria。它是 project-local Shot Planning knowledge Skill；其 `plan -> craft -> validate -> generate -> judge -> refine -> stitch -> deliver` 只作为 authoring rubric。Agent MAY 提取 shot decomposition、H3 prompt grammar、continuity questions 与 judging heuristics，然后必须将结果翻译成 approved AI-VIDEO Character / Scene / Shot artifacts 和现有 contracts。

`open-video` MUST NOT 运行或安装其 product/CLI/Python runtime，不得执行 `open-video install/pull/status/run`、ComfyUI submit、generation、judge loop、refine loop、ffmpeg stitch、artifact/receipt write，也不得成为 video engine、Provider、renderer、Production runtime 或 Agent runtime/lifecycle owner。上游 multi-shot Director path 标记为 evolving/design-scaffold；其 capability、constraint、model 与 quality claims 只能作为候选知识，使用前必须由当前 AI-VIDEO code、sealed profile、tests 或 runtime evidence 重新验证。

`h3-video` MUST use only when an approved AI-VIDEO Shot Contract and Generation Requirement already exist and the task explicitly targets MiniMax H3 guidance. It consumes those fixed inputs and returns advisory `recommended H3 mode`、`required inputs`、`prompt considerations` 与 `known limitations`。It MAY advise on the H3 3-field prompt grammar、T2V/I2V/FL2VA/R2V mode fit、camera/audio/visible-audible wording、resolution/steps/scheduler/quant constraints and H3-specific failure diagnosis. It MUST NOT accept Story-only input, choose a Provider, modify the Shot or Generation Requirement, or promote advice into canonical truth.

Within AI-VIDEO, the operational sections of upstream `h3-video` are reference-only. The Skill MUST NOT install or run OpenVideo、download H3 weights、inspect or start ComfyUI、execute dry-run/generation/review/delivery commands、read `OPEN_VIDEO_VLM_KEY` or any other credential、call a Provider/API, or write media/receipt/runtime state. Exact capability、profile、mode token、setting and limitation claims MUST be revalidated against the selected AI-VIDEO MiniMax H3 adapter、sealed profile、workflow、tests and current runtime evidence before use. `h3-video` owns neither the adapter nor its execution lifecycle.

`hell-grind-aigc-skill` MUST use when the task includes semantic Shot design、open/close state、cross-Shot continuity、identity/state/spatial/axis/action/light/environment/audio continuity、image/video prompt structure、generation failure diagnosis、iteration 或 candidate reasoning。它优先回答“Shots 之间什么必须保持或改变？”以及“generated Shot 为什么失败？”。AI-VIDEO Character、Scene、Shot 与 asset records 始终是 source of truth；不得创建平行的 project schema、asset registry、generation ledger、review state 或 delivery truth。

`seedance-authoring` MUST use when an approved AI-VIDEO Shot / Generation Requirement already exists、the selected target is Seedance、and the task needs prompt/reference authoring or creative repair。它消费 exact selected version、generation mode、runtime surface 与 semantic reference roles；先加载 shared authoring knowledge，再且仅再加载一个 `2.0` 或 `2.5` overlay。T2V/I2V/R2V/FLF2V/edit/extend 都是 injected mode profile，不是独立 Skill。Unknown/future/mixed version 或缺失 deterministic selection 时 fail closed；不得猜测 capability、surface 或 transport。

`seedance-authoring` 只拥有 Agent-side Seedance prompt/reference expression。它不得选择 Provider/model/profile、创建 asset manifest、验证runtime cardinality/parameter、编译transport payload、运行official API/ComfyUI/community runtime、提交/轮询/抓取/retry、写Manifest/Registry、决定continuity/P6/Final Acceptance或复制Harness。Runtime/API/ComfyUI failure返回selected adapter typed failure path；semantic continuity返回`hell-grind-aigc-skill`与existing continuity owners。`runtime_skill_calls = 0`保持不变。

AI-VIDEO 内旧的direct Seedance dispatch targets `higgsfield-seedance`、`higgsfield-seedance-2-5`、`higgsfield-seedance-vfx`，以及`higgsfield-troubleshoot`的Seedance分支已经retired，MUST NOT direct-dispatch。它们的global frontmatter/trigger不覆盖本仓库routing；只有在`seedance-authoring`已经selected后，Agent才可按需读取其中一段作为non-authoritative advisory source，且不得迁移其version/runtime/Provider事实或扩大Skill authority。

`higgsfield` MUST use when the task includes Non-Seedance provider/model-specific prompt adaptation、Hailuo/Kling/Veo guidance、corresponding T2V/I2V/reference/continuation/extension mode guidance、provider-specific camera vocabulary 或 generation troubleshooting。它只在 AI-VIDEO semantic Shot / continuity intent 已建立后使用，不得接管Seedance authoring、选择 active Provider、读取 credential、提交 generation 或绕过 AI-VIDEO gates。

`video-shotcraft` MUST use when the task includes motion design、image motion、motion graphics、shot language、camera movement、pacing、transition、SFX、beat sync 或 visual QA ideas。其 Remotion implementation、recipe、timeline 与 renderer 只是 creative / implementation reference；选定方案必须翻译成 AI-VIDEO composition directives。

`ecommerce-ad-workflow` MUST use for ecommerce、SKU、product advertising、direct-response product video 或 commercial product brief authoring。它只产出 Development-side Product Truth、claim ledger、Hook、ad beats、copy/audio intent、CTA、creative variants 与 capability-aware handoff；不得安装或调用 external ad system、读取 credential、选择 Provider、生成媒体、写 Project/Registry/Manifest、重算 `ResolvedTimeline`、选择 renderer 或给出 P6 / Final Acceptance。AI comic、episode、serial 与 cliffhanger request 不得路由到该 Skill。

Routing precedence：

- 命中 `Agent Memory Retrieval Routing` -> 先调用 `retrieve-ai-video-memory`；retrieval 只提供 advisory evidence，不重定义下游 contract。
- Ecommerce / SKU / product advertising authoring -> `ecommerce-ad-workflow`；具体 continuity、Provider prompt 或 deterministic motion concern 再进入对应下游 Skill。
- Concept/script -> ordered Director coverage / Shot plan -> `open-video`。
- Semantic continuity / Shot-state problem -> `hell-grind-aigc-skill`。
- Approved Shot + Generation Requirement + selected MiniMax H3 target -> `h3-video`。
- Approved Shot + Generation Requirement + selected Seedance target -> `seedance-authoring`。
- Other supported Non-Seedance generative model / Provider prompting problem -> `higgsfield`。
- Deterministic motion design / graphics / pacing problem -> `video-shotcraft`。
- Production state / assets / dependency / timeline / render / Provider execution / activation / recovery -> AI-VIDEO code and contracts。

多 Skill 组合必须按依赖顺序调用；后续 Skill 可以适配前序 advisory result，但不能重定义上游 semantic contract 或下游 production truth。

```text
multi-shot direction:
AI-VIDEO concept / script
  -> open-video: advisory coverage, Shot order, objectives, transitions, review questions
  -> AI-VIDEO approved Character / Scene / Shot artifacts
  -> downstream matching Creative Skills only when their concerns are present

generated-video continuity:
AI-VIDEO Shot intent
  -> hell-grind-aigc-skill: establish semantic continuity
  -> seedance-authoring: adapt prompt/reference expression for a selected Seedance target
     OR higgsfield: adapt a selected Non-Seedance target
  -> AI-VIDEO Provider Request: provenance, lifecycle, activation, recovery

MiniMax H3 generation guidance:
AI-VIDEO approved Shot Contract + Generation Requirement + preselected H3 target
  -> h3-video: advisory H3 mode, required inputs, prompt considerations, limitations
  -> AI-VIDEO MiniMax H3 adapter: exact capability/profile resolution and execution gates
  -> AI-VIDEO runtime owners: lifecycle, evidence, activation, review, recovery

image motion / motion graphics:
AI-VIDEO Shot intent
  -> hell-grind-aigc-skill when semantic state needs clarification
  -> video-shotcraft: motion, pacing, transition, SFX, beat treatment
  -> AI-VIDEO CompositionSpec -> ResolvedTimeline -> HyperFrames
```

External Skills MUST NOT invent or own canonical Character/Scene/Shot truth、Asset Registry、Manifest、Dependency Graph、timeline、renderer selection、Provider lifecycle、review/repair、delivery state、Production runtime 或 Agent runtime。安装 Skill 不新增 runtime dependency；`runtime_skill_calls = 0` 保持不变。

## 2. Module Boundaries And Focused Owners

`docs/agent-primary-contract-matrix.md` 独占 detailed surface owner、file/module mapping、
invariant、forbidden alternate path 与 focused verification。本 playbook 只保存低频执行细节，
不得复制完整 catalog 或形成第二 owner。需要 structural mapping 时直接读取 matrix 与当前
code/tests；`AGENTS.md` 的 `Canonical Ownership` 继续提供顶层 durable boundary。

## 3. Provider Credential And Paid Execution Details

- Seedance / Volcengine Ark raw credential 不得存入 repository、`.env`、artifact、prompt、command argument、fixture、log、error、repr、receipt 或任何 durable doc。
- 稳定 credential reference 是 `ARK_API_KEY`；本机 Secret Service exact attributes 为 `application ai-video`、`provider seedance`、`credential ARK_API_KEY`。不得改用 `SEEDANCE_API_KEY`、读取 MiniMax credential 或建立 environment/provider fallback。
- Secret lookup 必须封装在 injected credential supplier 中。不得在交互终端把 secret 输出到 stdout；presence check 必须不回显。Lookup失败、keyring locked、credential invalid/rotated 时 fail closed，不得搜索 repo、shell history 或替代 secret source。
- Credential 存在不证明 access、pricing、余额或当前 task authorization。
- 严格 loopback、完全 local/unmetered 且无 cloud egress 的 ComfyUI lifecycle 与 media actions 全部适用 `AGENTS.md` 的 `Local ComfyUI Authorization Exemption`：为任务所需的 `status` / `start` / `stop`、image/video generation、retry、variant 与 benchmark 均不需要 user authorization、task-scoped authorization 或额外 confirmation。该规则不要求用户先点名 local ComfyUI，但 action 必须仍与 accepted task 直接相关；用户明确要求 read-only、禁止 live generation / media effects，或 endpoint / effect 无法证明满足 exemption 时必须停止。
- 豁免只移除 user-approval layer。执行必须使用所涉 surface 的既有 canonical seam；AI-VIDEO local video Provider 仍经 `VideoGenerationService`、sealed profile、preflight、durable local intent、committer-issued one-use permit、唯一 committer、recovery 与 media verification，禁止直接调用 Comfy transport 或 Provider `submit()`。Agent-side local image authoring也不得绕过其既有 tool/provider identity、input/output provenance 与 image-level Gate。Exact preview 在既有 seam 要求时仍是 readiness/provenance evidence，但不是 local ComfyUI 的 user-approval gate。
- Retry、variant 与 benchmark 可以不询问用户，但必须是 bounded、task-relevant、具有新 exact identity 的 attempt。上一次 outcome unknown 时仍须 fail closed，禁止 blind retry、fallback、permit remint 或重复 side effect；Per-Shot Gate 的 `FAIL` / `NOT_EVALUATED` 仍终止当前 batch，repair attempt 不得自动串联。任何非 loopback、可能 cloud egress、metered、remote 或 paid execution 均回到对应 authorization 与 Provider gates。
- 用户明确要求执行一个必然包含 remote/paid call 的任务时，该请求构成该 accepted scope 的 task-scoped authorization；Docs-only、plan、review、可行性分析或“能否执行”不构成 live authorization。
- Authorization 仅覆盖 accepted Provider/model、inputs、budget 与完成目标所需的最少调用；不得复用于 benchmark、额外 variants、不同 Provider/model 或扩大后的 scope。
- Task-scoped authorization 不替代 Paid Provider Gate。调用前仍需 exact preview、finite budget ceiling/reservation、cloud-egress approval、secret reference、durable submit intent 与 one-use permit。
- 若费用超过 ceiling、scope/provider/egress 变化、需要更多调用，或上一次 outcome unknown，必须停止并报告；不得 blind retry、remint permit 或把授权解释为无限额度。
- 历史 live evidence、offline tests、现有 credential/余额或旧 run 不授权新的调用。

## 4. Verification, Pilot And Delivery Details

- `.agent/harness/policy.yaml` 是 changed-path routing 与 mandatory checks 的 machine-readable truth；`docs/agent-primary-contract-matrix.md` 提供 human-readable focused verification。两者的 routing 变更必须同步并测试。
- Harness inspection 后，完成验证必须针对 non-empty exact staged snapshot 或 exact commit range，并在 detached temporary worktree 中运行，使 unrelated dirty changes 不进入 execution tree。
- Code 或 executable tooling change 必须有 fresh passing receipt，并验证 scope、policy、artifact hashes 与 freshness；documentation/control-plane change 也必须执行 policy 路由的真实 checks。
- Unmapped owned paths 必须 fail safe 到 full tests 与 task-delta Architecture Gate；历史 repository debt 不得伪装成当前 task regression，反之也不得通过刷新 baseline 隐藏 regression。
- Behavioral change 必须有覆盖 public behavior、boundary 与 failure path 的 executable evidence；未实际执行不得声称 passing。
- Harness 不调度 Agent、不修改产品 state、不读取 Provider secret，也不执行 live Provider、ComfyUI、paid smoke 或媒体生成。CI 必须生成自己的 evidence，不能信任提交的本地 receipt。
- Workflow 文件存在不等于 server enforcement；需要声明 remote protection/publish truth 时必须重新验证当前 GitHub ruleset / branch protection。
- Real media 或 rough-cut 批量生产前，必须先完成约 30～60 秒、连续 4～8 Shots 的真实 Pilot，包含 task 所需的主要角色、static/image-motion、generated-video、voice、captions 与最终 HyperFrames composition；Pilot 必须由人实际观看并给出明确 GO/NO-GO，NO-GO 时不得继续扩量。
- Character / Scene reference asset 默认只提供 identity、state、space 或 style guidance，不得自动成为观众最终看到的 Shot visual。Final Shot Visual 必须绑定 Shot-specific visual intent；跨非连续 Shots 复用同一 final asset 时必须有明确导演理由并进入人工 review。

### Empirical Uncertainty Triage

当 task 涉及新视频/图像/音频模型或 Provider、新 ComfyUI workflow、LoRA / Turbo、continuity / identity / reference strategy、long-video、lip sync、motion / camera control、multi-character、upscaling / refine、prompt strategy或音频感知质量时，在最小技术前置条件关闭后记录：

```text
next_empirical_question: <当前最影响继续/停止/选路的真实媒体问题>
cheapest_valid_experiment: <能证伪或支持该问题的最小安全实验>
blocking_prerequisite: <真实 blocker；没有则写 none>
```

若 `blocking_prerequisite = none`，下一关键动作默认执行 `cheapest_valid_experiment`，而不是继续增加非必要 qualification infrastructure、schema、lifecycle、Harness 或 integration。推荐顺序是：

```text
Safety / Applicable Authorization Or Local Exemption
  -> Minimum Technical Prerequisite
  -> Cheap Empirical Falsification
  -> Production Qualification
  -> Lifecycle / Replay / Recovery Closure
  -> Promotion
```

`development_experiment` 只是 evidence / reporting classification 与 sequencing policy，不是新的 execution plane、API、schema enum、registry record 或 persistent lifecycle state。实验复用所选工具当前已批准或按`Local ComfyUI Authorization Exemption`免授权的execution seam：AI-VIDEO local video Provider仍必须经`VideoGenerationService`、sealed profile、preflight、local permit、唯一 committer、recovery与media verification，禁止直接调用Comfy transport或Provider `submit()`；remote / paid experiment仍须满足当前用户授权、budget、cloud-egress、secret、durable intent、one-use permit与unknown-outcome rules。实验 output / metadata 必须与 active Production truth隔离，结果只接受bounded technical / human triage，不得直接产生active capability、Production qualification、Manifest / Registry activation、P6 / Final Acceptance或release truth。Development experiment PASS / FAIL 均不得偷换frozen rubric或Production contract。

## 5. Repository-Specific Don't Repeat This

本 section 保存可复用的 implementation pitfall 与工具选择；已经真实发生、可复现且值得
防止重犯的独立 regression/incident 才进入 `.agent/bug-memory/`。普通操作手册、环境说明、
设计建议或未发生风险不得放入 bug memory。

- 不要对同一 `run_id` 再次调用 `run()` 来实现 resume；从持久化 Manifest 恢复。
- 不要将包含 `..` 的相对 artifact path 写入 Manifest 或 resolved config；持久化路径必须是干净绝对路径。
- 不要在更新 `final_output` 等 terminal state 后绕过 atomic Manifest write。
- 不要在测试中用裸 YAML/JSON parsing 绕过标准 `load_workflow_template()` 或 Production loader。
- Production invalidation 不得退化为 Shot-order blanket stale；只沿 canonical typed dependency edges 传播。
- 不要让 native media audio 绕过 canonical P4 mixer，也不要让 graph、Provider 或 Skill 重算 `ResolvedTimeline`。
- Project-local `video-analysis` 是本仓库默认视频检查工具；全局 `videoscan` 只可作为 metadata/frame helper，不能成为 Production QA owner。
- 交付 generated-video 时只提供真实 live/fetched/validated output；不得把 preflight、fake fixture、smoke artifact、technical evidence 或 fetch success冒充 activated、quality-accepted 或 final delivery truth。

### Per-Shot Post-Media Gate

该 Gate 属于 Agent-controlled sequential generation 的 synchronous stop condition，不是
background hook、Provider callback、Product Runtime writer 或新的 P6 lifecycle。执行顺序固定为：

```text
resolve Shot N SourceAudioPolicy against the already-selected Provider capability
  -> bind the chosen audio route into the exact request
  -> generate Shot N once
  -> exact MP4 exists and SHA-256 is fixed
  -> call project-local video-analysis MCP on that exact path
  -> map raw evidence to exact Shot requirements
  -> PASS: allow submit of Shot N+1
  -> FAIL / NOT_EVALUATED: stop before any next submit
```

- 多 Shot task 必须按 one-Shot-at-a-time orchestration 执行；不得先提交整个 batch，再补分析。
- `SourceAudioPolicy`是逐Shot authoring intent，不选择Provider。Agent必须在submit前将它与
  已选Provider的exact output capability合并为单一路线，禁止用统一的“先静音、以后P4补音”
  默认值覆盖已声明的source-audio intent：
  - `source_type=GENERATED`且`policy=KEEP`或`TRIM_THEN_MIX`时，request必须声明
    `native_audio=true`；对Seedance adapter即`generate_audio=true`。Capability不支持`true`、
    request被改成`false`或exact request identity无法证明时，必须在submit前STOP，不得静音降级、
    更换Provider或把未来P4配音当作等价满足。
  - `policy=MUTE`或`REPLACE`时，source audio不得满足该Shot的最终audio coverage；所有仍需的
    dialogue、VO、BGM、SFX或ambience必须由显式P4 audio requirements覆盖。逐Shot raw-MP4
    Gate只验证exact request/source route和这些P4 coverage requirements已经声明；最终是否真正
    静音或替换只能在P4 render后的final-composition Gate检查，不得提前伪造PASS或因此阻断下一Shot。
  - `source_type=NONE`只允许empty `MUTE` route；不得伪造KEEP、trim或measurement intent。
  - `source_type=NATIVE`的KEEP/TRIM route必须绑定exact existing source-audio identity；不得把它
    偷换成Provider新生成的音轨。
- 显式 MCP 调用至少覆盖 exact media probe 与 sampled visual review；需要 audio、scene-change、
  lip-sync 或 continuity evidence 时，调用对应 MCP capability。异步 Generated-Video Analysis
  Hook只用于advisory background capture，queue/result均不能满足本 Gate。
- Gate input必须绑定`shot_id`、exact output path、output SHA-256、selected Shot intent/rubric、
  applicable requirement IDs，以及从Shot 2开始所需的前序accepted end-state evidence。
- Gate output必须逐项记录`requirement_id`、evidence reference、`PASS` / `FAIL` /
  `NOT_EVALUATED`与简洁reason。不得用一个quality score覆盖identity、action、product/object、
  camera、duration、prompt adherence、audio或continuity等独立required findings。
- `GENERATED + KEEP/TRIM_THEN_MIX`的exact MP4除了audio-stream parity外，还必须逐项检查
  decoded audio可用、audibility、与画面/动作同步、required dialogue或recommendation语义、
  speaker/lip-sync binding，以及重复广告词或非预期静音。任一required audio finding缺少可信
  evidence都必须`NOT_EVALUATED`；有音轨本身不构成audio PASS。
- Raw Provider MP4的audio PASS只关闭当前Shot barrier，不证明该音轨进入最终成片。若最终路径
  使用canonical P4 composition，KEEP/TRIM source必须先作为exact generated audio asset进入
  `CompositionSpec -> ResolvedTimeline -> HyperFrames`；当前lane缺少该能力时必须报告
  `REQUIRES_RUNTIME_CAPABILITY`并停止final-composition与delivery claim，但不把已经关闭的raw Shot
  barrier倒退为FAIL；不得移除`muted`或direct mux旁路。
- 只有全部required findings为`PASS`时，Agent才可提交下一Shot。MCP unavailable/error、
  output identity drift、missing/stale evidence或任何required finding无法可靠判断都必须
  `NOT_EVALUATED`并fail closed。
- `FAIL`或`NOT_EVALUATED`后只允许报告诊断与建议的targeted repair，当前batch必须停止。符合
  `Local ComfyUI Authorization Exemption`的后续bounded repair/retry无需用户授权，但必须作为具有
  新exact identity的独立attempt重新进入全部Provider与media gates；不得自动串联重生成、fallback
  或继续batch。Remote / paid retry仍须具备适用authorization。
- MCP raw evidence与Agent verdict不得直接写Manifest、Registry、activation、P6 receipt或
  Final Acceptance。进入Production acceptance时，仍须由existing review contract与
  `ProductionStateCommitter`重新绑定、adjudicate和持久化。

Final-composition audio Gate在P4 render后独立执行：`KEEP/TRIM_THEN_MIX`必须证明accepted source
audio按exact trim/mix进入最终`ResolvedTimeline`；`MUTE/REPLACE`必须证明source audio未泄漏且
replacement coverage存在；intentional silence必须保持预期。该Gate不允许下一Shot submit，也不
重复生成Provider media，只决定final-media是否可继续进入P6 / Final Acceptance。

## 6. Agent Experience Memory Routing

Agent Memory 是 scoped、local、advisory knowledge source。调用入口与 authoritative
failure behavior 以 `.agents/skills/retrieve-ai-video-memory/SKILL.md` 为准；本 section
只保存 repo-local routing detail。

- 默认使用 `experience`，检索 `docs/record_for_agent/` 并合并 eligible run summaries。
- 只有明确需要 historical specs/plans 时使用 `superpowers`。
- 需要 current top-level docs、research、deferred decisions、experience 与 historical
  plans 的 cross-category evidence 时使用 `all`；必须保留各 hit 的 authority distinction。
- 每次只读取一个 matching scope reference，并执行一个 focused query；不得为了强行命中
  而降低 admission gate、重复等价查询或无依据扩大 scope。

`runs/<run_id>/SUMMARY.md`（auto-generated run summaries）通过独立的 derived
index `.agent/memory/run-summaries`（collection `agent_memory_run_summaries`，
authority `auto_generated_run_summary_advisory`）被发现，无需手动复制或单独
build。experience / all 检索会在 corpus digest 变化时自动重建该 derived
index；schema 仍然保持 v1；缺失的 `runs/` root 不会产生 hit。只有精确的一层
`runs/<run_id>/SUMMARY.md` regular non-symlink 文件才参与；带 `Status` 行；
trailing `-vN` 解析为 `run_family`/`run_version`，同 family 只保留最高版本。
`superpowers` scope 不会触达 runs。Run-summary `Hit` 显式包含 source、
status、`document_kind=run_summary`、`run_id` / `run_family` / `run_version`、
`summary_sha256` 与 formatted authority 标签。

Use `retrieve-ai-video-memory` before substantial execution when the task involves:

- real media production;
- rough-cut or final output quality;
- known regressions or repeated failures;
- Provider/model behavior;
- continuity, identity drift, reference usage;
- image/video generation strategy;
- architecture decisions with previous rejected approaches;
- recovery from previous incidents。

The Agent SHOULD NOT query memory for trivial changes such as formatting,
typo fixes, isolated refactors, or tests with no relation to previous
production experience.

Result handling 必须 fail closed 且 non-blocking：

- exit `0` + fresh hits 或 `[]` 是正常结果；`[]` 是有效 abstention。
- exit `0` + `index_freshness=stale` 只返回 physically valid、tagged last-good fragments，
  并异步 queue exact stale shards；继续使用当前文件证据，不等待、不轮询、不重复检索。
- exit `3` 表示 local sharded layout missing 或需要 one-time migration；CLI 已 queue
  materialization，本 task 继续使用当前 repository evidence，不在前台重试。
- exit `2` 是 schema、embedding、authority、manifest 或 physical collection strict
  failure；显式报告并继续当前文件证据，不 enqueue/rebuild、不降低 validation。

Runtime 不得自动下载 embedding model、使用 fake embedding、联网 fallback 或把 Agent
Memory 接入 Production state。Derived-index maintenance 不是 lifecycle hook，也不授权
Product Runtime mutation。

Retrieved memories are advisory only. They MUST NOT override:

1. user instructions;
2. current code and tests;
3. runtime evidence;
4. current architecture contracts。

只有 implementation findings materially 改变原 query 并暴露 distinct term/owner/failure
signature 时，完成前才允许一次 focused follow-up；不得把重复检索当作 completion ceremony。

### Experience Learning And Confirmation

Memory/record 保留 exact historical evidence；Learning Claim 是基于多条evidence的current、scoped、
可撤销advisory synthesis。两者继续共享 `experience` query，但
`docs/record_for_agent/learning/**/*.md` 必须返回
`authority=advisory_learning` 与 `document_kind=learning_claim`，不能被普通record或frontmatter伪造。

`record-ai-video-session` 创建或materially更新substantial stable record后，必须自动调用
`distill-ai-video-learning`，不得等待用户另行要求。Evaluation只有两种有效结果：

1. `no_candidate`：没有达到多attempt、controlled comparison或existing-claim material update
   threshold，不创建空artifact，不请求形式化确认。
2. `pending_candidate`：只创建或更新一个most-relevant
   `docs/record_for_agent/learning/<claim-id>.md`。Claim分离`Active Claim`与`Pending Candidate`；
   新candidate不得覆盖仍被target消费的adopted active版本。Pending固定
   `pending_approval_status=PENDING_CONFIRMATION`、
   `pending_adoption_status=NOT_ADOPTED`，只把claim path形成candidate checkpoint commit，
   再向用户展示support/counter evidence、scope/exclusions、evidence status、recommended action、
   exact target paths、verification、candidate commit与该commit中exact file bytes SHA-256。

Session boundary只触发evaluation；experiment/attempt/controlled-arm boundary才产生evidence identity。
新建或实质更新、准备进入automatic distillation的empirical record使用flat scalar envelope：
`record_kind`、`topic_id`、`learning_eligibility`与`evidence_index_version: "1"`。其中
`learning_eligibility=eligible`要求正文包含`## Evidence Index`，以`evidence_id`引用proof item，
以`independence_key`作为唯一support/counter计数单位，并同时记录`experiment_id`、`attempt_id`、
`arm_id`、`artifact_sha256`、`proof_layer`、`verdict`、`failure_class`、`relation_kind`、
`related_evidence_id`与`source`。Pre-artifact failure使用`NO_ARTIFACT:<TYPED_REASON>`；没有arm或relation
分别使用`N/A`与`NONE`，不得用空值掩盖identity uncertainty。

Q0 `AttemptIdentityKey.identity_hash`存在时，`independence_key`优先为`q0:<identity_hash>`；否则record
必须提供stable non-Q0 key，并以runtime/provider/model/workflow boundary、experiment、attempt及至少一个
request/result/artifact anchor支撑。Document path、Markdown heading、RAG chunk与artifact version均不得自动合成
key。一个key不得指向两个experiment/attempt/arm tuples，同一tuple也不得同时mint Q0/non-Q0或其他多个keys；
同一artifact/source anchor也不得mint多个keys；该bijection在本次显式validation set内fail closed。同一个key跨
records、chunks或proof layers始终只计一个unit；相同SHA但真实attempt identity不同的evidence不得只因bytes相同
被合并，并必须保留distinct exact request/result source。

`Evidence Index` relation区分`NEW_ATTEMPT`、`SAME_EVIDENCE_NEW_PROOF_LAYER`、
`CONCLUSION_SUPERSEDED`与`INPUT_REUSE_ONLY`。Technical PASS与后续human FAIL可在同一key下作为不同proof
layers并存，不能互相擦除或算作两次独立实验；`INPUT_REUSE_ONLY`本身不能进入support/counter threshold。
Learning Claim的Supporting/Counter tables以`evidence_ref`引用record row，并声明exact identity tuple与proof；
admission仅允许`TWO_INDEPENDENT_ATTEMPTS`、`CONTROLLED_MULTI_ARM`或
`MATERIAL_EXISTING_CLAIM_UPDATE`。Material update还必须命名target claim、previous evidence与具体delta。

`.agents/skills/distill-ai-video-learning/scripts/validate_evidence_identity.py`只读取caller显式提供的Markdown
paths，不扫描corpus、不刷新Agent Memory、不调用Provider/media/network，也不写回文件。它对blank/malformed
identity、duplicate record-local `evidence_id`、unresolved relation、source-reference mismatch、非法重复计数与
不满足basis的candidate fail closed，并输出每个document的distinct support/counter keys与admission result。
Legacy record/claim没有`evidence_index_version: "1"`时仍可检索但不自动admit；`needs_identity`允许人工阅读，
不得fallback到document/hit count。Forward-only rollout不批量迁移历史record，也不原地改写既有confirmed或
pending candidate preimage。

Agent Memory只从existing flat frontmatter向`Hit`、JSON与human-readable provenance投影allowlisted
`record_kind`、`topic_id`、`learning_eligibility`、`evidence_index_version`。这些字段不改变ranking、filter、
chunk identity、path-owned `authority`/`document_kind`、admission、confidence、confirmation或adoption；同一document
产生多个hits仍只是retrieval结果，不是independent evidence count。

确认只对previewed candidate commit、hash与bounded target有效。`Confirm`前必须用
`git show <candidate-commit>:<claim-path>`重开immutable preimage并重算hash，同时要求current pending
bytes未漂移；确认还必须保存sanitized actor/time与durable evidence pointer，不复制raw transcript。
Bytes/evidence/commit变化或target scope扩大都使旧确认失效。`Revise`产生新checkpoint
与hash并重新确认；`Reject`只拒绝pending lane，必须保留active claim与其adoption evidence。确认后的
target implementation继续走原owner、decision gate、tests、review与Harness；只有target实际修改且
verification通过后，pending才可提升为active并记录`ADOPTED`。Skill/claim本身不授权Provider/media、
Manifest/Registry/P6/Final Acceptance、retry、activation、target commit、push或release；确认前唯一允许
的commit是只包含claim path的candidate checkpoint。

Session hook把自动evaluation作为completion handshake的一部分：`recorded` ACK只接受
`learning_outcome=no_candidate|pending_candidate`，`no_record`只接受
`learning_outcome=not_applicable`。因此Agent不能在有durable record时跳过evaluation后直接关闭checkpoint；
hook仍不负责synthesis、确认或target mutation。

## 7. Durable Session Record Gate

`record-ai-video-session` 是 substantial AI-VIDEO work 的 completion-time durable capture
owner。它不是只在 hook 注入 `capture_request_id` 时才生效；hook只是backstop，主动评估由
当前Agent负责。

在 final response、handoff 或 compaction 前按以下顺序判断：

1. 当前 task 是否包含 substantial implementation、documentation、local/remote live proof、
   real media generation或diagnosis、architecture decision、recovery或independently reusable
   runtime lesson。
2. 工作是否已达到 stable checkpoint、completion或genuine blocker；尚未完成时先继续工作，
   不得为了写record打断主任务。
3. 检查repository内外effects。`/home/reggie/ComfyUI/output/`、`/tmp/`、Provider artifacts、
   fetched media与analysis derivatives即使没有tracked diff，也属于record trigger evidence。
4. 若1与2成立，主动读取并执行`.agents/skills/record-ai-video-session/SKILL.md`；不得因
   PostToolUse未归属path、没有hook request或没有`capture_request_id`而跳过。
5. Formatting、trivial conversation、unfinished work或没有durable value的status question明确
   判定为`no_record`。不要创建空泛session note，也不要让record触发另一份record。

Record只能保存verified evidence与边界，不能授权新实现、generation、Provider call、push、
release或Production mutation。若hook提供exact `capture_request_id`，仍按Skill要求只acknowledge
一次；没有ID时不运行acknowledgement command。
