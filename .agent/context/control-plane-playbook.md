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

`hell-grind-aigc-skill` MUST use when the task includes semantic Shot design、open/close state、cross-Shot continuity、identity/state/spatial/axis/action/light/environment/audio continuity、image/video prompt structure、generation failure diagnosis、iteration 或 candidate reasoning。它优先回答“Shots 之间什么必须保持或改变？”以及“generated Shot 为什么失败？”。AI-VIDEO Character、Scene、Shot 与 asset records 始终是 source of truth；不得创建平行的 project schema、asset registry、generation ledger、review state 或 delivery truth。

`higgsfield` MUST use when the task includes provider/model-specific prompt adaptation、Seedance/Hailuo/Kling/Veo guidance、T2V/I2V/reference/continuation/extension mode guidance、provider-specific camera vocabulary 或 generation troubleshooting。它只在 AI-VIDEO semantic Shot / continuity intent 已建立后使用，不得选择 active Provider、读取 credential、提交 generation 或绕过 AI-VIDEO gates。

`video-shotcraft` MUST use when the task includes motion design、image motion、motion graphics、shot language、camera movement、pacing、transition、SFX、beat sync 或 visual QA ideas。其 Remotion implementation、recipe、timeline 与 renderer 只是 creative / implementation reference；选定方案必须翻译成 AI-VIDEO composition directives。

Routing precedence：

- Concept/script -> ordered Director coverage / Shot plan -> `open-video`。
- Semantic continuity / Shot-state problem -> `hell-grind-aigc-skill`。
- Specific generative model / Provider prompting problem -> `higgsfield`。
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
  -> higgsfield: adapt the approved contract to Provider prompt/mode guidance
  -> AI-VIDEO Provider Request: provenance, lifecycle, activation, recovery

image motion / motion graphics:
AI-VIDEO Shot intent
  -> hell-grind-aigc-skill when semantic state needs clarification
  -> video-shotcraft: motion, pacing, transition, SFX, beat treatment
  -> AI-VIDEO CompositionSpec -> ResolvedTimeline -> HyperFrames
```

External Skills MUST NOT invent or own canonical Character/Scene/Shot truth、Asset Registry、Manifest、Dependency Graph、timeline、renderer selection、Provider lifecycle、review/repair、delivery state、Production runtime 或 Agent runtime。安装 Skill 不新增 runtime dependency；`runtime_skill_calls = 0` 保持不变。

## 2. Module Boundaries And Focused Owners

- `src/ai_video/cli.py`：CLI parsing 与用户命令编排。
- `src/ai_video/config.py`：YAML/config validation、本地策略与路径解析。
- `src/ai_video/workflow_loader.py` / `workflow_renderer.py`：标准 workflow loading、UI-to-API conversion 与 pure binding/rendering。
- `src/ai_video/comfy_client.py`：ComfyUI transport、polling、artifact download 与 typed transport failure。
- `src/ai_video/pipeline.py` / `manifest.py`：Legacy Shot orchestration、resume 与 atomic Legacy Manifest persistence。
- `src/ai_video/ffmpeg_tools.py`：probe、clip validation、frame extraction、normalization 与 stitching。
- `src/ai_video/production/models.py` / `hashing.py` / `paths.py` / `validation.py`：strict schemas、sealing、containment 与 static validation。
- `src/ai_video/production/registry.py` / `project.py` / `_*project_reader.py`：read-only selected Asset Registry / Production Project evidence loading；不得写入、恢复或激活。
- `src/ai_video/production/state_commit.py` / `_state_commit_*`：唯一 public v2 writer、activation、commit 与 recovery boundary；private modules不得形成第二 writer。
- `src/ai_video/production/dependency.py`：pure immutable graph、desired fingerprint、precise invalidation 与 rebuild decisions；不得写文件、Manifest、Registry 或 runtime status。
- `src/ai_video/production/composition.py` / `hyperframes.py` / `visual_media.py`：canonical composition resolution、media validation 与 selected HyperFrames execution；不得另造 timeline。
- `src/ai_video/production/audio.py` / `captions.py` / voice adapters：audio、voice、caption contracts；timing仍归 `ResolvedTimeline`，durable mutation仍归 committer。
- `src/ai_video/production/review.py` 与 `src/ai_video_mcp/**`：pure review contracts或 raw analysis evidence；不得自判或写入 Production acceptance。
- `src/ai_video/production/image.py` / `video.py` / Provider adapters：provider-neutral contracts与显式 adapter execution；不得成为 writer、resolver、Provider selector 或 activation owner。
- `src/ai_video/production/__init__.py`：只暴露 approved public imports，不承载 implementation。

更细的 surface owner、forbidden alternate path 与 focused tests 以 `docs/agent-primary-contract-matrix.md` 为准。

## 3. Provider Credential And Paid Execution Details

- Seedance / Volcengine Ark raw credential 不得存入 repository、`.env`、artifact、prompt、command argument、fixture、log、error、repr、receipt 或任何 durable doc。
- 稳定 credential reference 与本机 Secret Service exact attributes 以 `AGENTS.md` 为准；不得改用未声明的 environment key、读取其他 Provider credential 或建立 environment/provider fallback。
- Secret lookup 必须封装在 injected credential supplier 中。不得在交互终端把 secret 输出到 stdout；presence check 必须不回显。Lookup失败、keyring locked、credential invalid/rotated 时 fail closed，不得搜索 repo、shell history 或替代 secret source。
- Credential 存在不证明 access、pricing、余额或当前 task authorization。
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

## 5. Repository-Specific Don't Repeat This

- 不要对同一 `run_id` 再次调用 `run()` 来实现 resume；从持久化 Manifest 恢复。
- 不要将包含 `..` 的相对 artifact path 写入 Manifest 或 resolved config；持久化路径必须是干净绝对路径。
- 不要在更新 `final_output` 等 terminal state 后绕过 atomic Manifest write。
- 不要在测试中用裸 YAML/JSON parsing 绕过标准 `load_workflow_template()` 或 Production loader。
- Production invalidation 不得退化为 Shot-order blanket stale；只沿 canonical typed dependency edges 传播。
- 不要让 native media audio 绕过 canonical P4 mixer，也不要让 graph、Provider 或 Skill 重算 `ResolvedTimeline`。
- Project-local `video-analysis` 是本仓库默认视频检查工具；全局 `videoscan` 只可作为 metadata/frame helper，不能成为 Production QA owner。
- 交付 generated-video 时只提供真实 live/fetched/validated output；不得把 preflight、fake fixture、smoke artifact、technical evidence 或 fetch success冒充 activated、quality-accepted 或 final delivery truth。

## 6. Agent Experience Memory Routing

Agent Memory 是 scoped、local、advisory knowledge source。`experience` scope
检索 `docs/record_for_agent/`；`superpowers` scope 检索 `docs/superpowers/`
中的历史 specs/plans。后者必须标记为 historical design/plan，不能升级为
current runtime truth、implementation authorization 或 accepted contract。

Use `scripts/agent_memory.py search` before substantial execution when
the task involves:

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

默认只使用 `experience`。只有 task 需要历史 architecture/spec/plan evidence 时
才使用 `--scope superpowers` 或 `--scope all`。Runtime 不得自动下载 embedding
model、联网 fallback 或把 Agent Memory 接入 Production state；index manifest
identity mismatch 或 stale corpus 必须 fail closed 并显式 rebuild。

Retrieved memories are advisory only. They MUST NOT override:

1. user instructions;
2. current code and tests;
3. runtime evidence;
4. current architecture contracts。

Before completing a task involving production quality, Provider behavior,
or known failure domains, perform a final relevant memory search to check
for repeated mistakes。
