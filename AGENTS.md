# AI-VIDEO Agent Guide

适用于在本仓库中工作的 Codex、Claude 以及其他任何编码 Agent。

## Purpose

当前仓库有边界不同的已实现产品表面：稳定的 `0.1.x` Legacy local-first Python CLI，以及 v0.2 P2-P8 提供的 read-only Production Project、explicit P2A State Commit/Recovery、deterministic Composition/HyperFrames、Voice/Captions、immutable Dependency Graph/selective rebuild、Codex Review/Repair、local-only image asset generation 与 optional generated-video Provider Python APIs。P7 lineage 与 P3-P7 combined Base AI Comic E2E 已合入 local `main`。P7.1 的 offline/runtime-contract 部分增加了 sealed loopback-only ComfyUI image adapter 与 truthful human web-image import；2026-08-18 fresh authorized rerun 已通过 Qwen 与 FLUX M7 technical live-local acceptance，M8 仍未验收。P8 provider core、Paid Provider Gate、Fake、MiniMax H3/Hailuo 与 Seedance offline adapters 已验收；Seedance Mini另有一次diagnostic live succeeded/fetched evidence，但tracked audio-opt-out payload、billing settlement与activation仍未live accepted；P9 仍只是规划。

Agent 必须维护当前产品承诺：

- 默认本地优先，默认 CLI 优先。
- 以 manifest 为核心的执行与恢复机制。
- `runs/<run_id>/` 下可预测、稳定的产物目录结构。
- 对 config、workflow 渲染、pipeline 状态、resume、ffmpeg 行为、CLI 行为保持较强测试覆盖。
- P2 的 strict schema、content hash、path containment、Shot strategy/reference 和 Asset Registry snapshot 验证保持 read-only、no-network，并与 Legacy loader 隔离。

## Versioned Product Boundary

- 当前已实现的 `0.1.x` / legacy runtime 仍是 local-first Python CLI，默认只连接本地 ComfyUI；非本地 ComfyUI 必须显式设置 `allow_non_local: true`。公共命令仍只有三个，产物仍使用当前 flat artifact layout。
- 当前已实现的 P2 Production Project Core 通过 `ai_video.production.load_production_project()` 暴露，只读取并验证显式物化的 v2 project、creative artifacts、Manifest-selected revision 和 Asset Registry snapshot；它不写入、不激活、不增加 CLI。
- 当前已实现并验收的 P2A Production State Commit Protocol 通过 `ai_video.production` Python API 暴露，拥有唯一 v2 writer/recovery owner、exact project/registry snapshot activation 和 explicit crash recovery；它不增加 CLI，也不改变 Legacy Manifest/layout。
- 当前已实现的 P3/P4 通过同一个 `CompositionSpec` -> `ResolvedTimeline` -> pinned local HyperFrames path提供deterministic render、audio/voice/caption contracts；P4已于`f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80` fast-forward合入local `main`，并随 P5 ancestry push 到 `origin/main`，尚未 release。
- P5 已于 `0d663566c4db4542922e38d770608e3e02d53745` fast-forward 合入 local `main` 并 push 到 `origin/main`：`DependencyGraphSnapshot`只保存immutable typed graph inputs，Manifest 2.3独占active graph与desired/applied/lifecycle，`ProductionStateCommitter`仍独占graph write/co-activation/recovery；P5不增加CLI、Provider、renderer或automatic recovery，且尚未 release。
- P6 已完成并整合到 local `main`：Manifest 2.4 与既有 `ProductionStateCommitter` 提供 durable review/repair/final-acceptance lifecycle；P5 graph 仍不保存 mutable review state。P6 尚未 push/release。
- P7 与 Base AI Comic E2E 已通过 `abc69c39b9d3d5f9ba317ecb65bbf26f1070d7d8` 合入 local `main`，但尚未 push、release 或 publish。P7 的 provider-neutral contract、Manifest 2.5 lifecycle、generated PNG provenance、target Shot/Registry/graph atomic activation、exact replay/recovery 与 combined no-Video-Provider proof 保持不变。
- P8 provider-neutral core、Manifest 2.7 / Registry 2.2、Paid Provider Gate、durable submit/poll/fetch/recovery、candidate activation、Fake 与 MiniMax H3/Hailuo adapters 已进入 local `main`；Seedance offline adapter通过 `c54435f`进入，最终activation/recovery closure通过`a089eac`进入。Hailuo已有三条真实 succeeded/fetched MP4 proof；H3 live已到达真实API但因余额不足返回`402 / code 1008`，因此H3只有offline acceptance而无live success。Seedance Mini在2026-08-19一次授权diagnostic中以one POST到达`succeeded`并fetch H.264 MP4；该请求省略`generate_audio`并产生AAC音轨，只证明cloud connectivity，不证明当前tracked audio-opt-out payload、billing settlement或activation已live accepted。所有adapter都保持显式、可删除、非默认且不得remote fallback。
- 独立 generated-MP4 composition compatibility slice 已于2026-08-19在local `main`实现并完成technical local acceptance：带exact `VideoAssetMetadata`的H.264 MP4可作为`GENERATED_VIDEO` / `EXISTING_VIDEO` visual span进入既有`CompositionSpec -> ResolvedTimeline -> HyperFrames`，由同一个P4 timeline完成audio/caption mix与mux；不新增timeline、renderer、writer、CLI、manifest schema或dependency。三个Hailuo MP4已生成`423@24fps`且含AAC audio stream的本地成片。此compatibility不等于P8 fetched candidate已自动完成Registry/Project/Graph activation，也不授权新的Provider调用。
- P7.1 offline/runtime-contract implementation 提供 sealed `ComfyLocalImageProvider`、exact local component/profile/workflow binding、R+1 前 read-only compatibility preflight，以及 `chatgpt_images_2_web` human import receipt/activation。2026-08-18 首次 M7 授权 session 因 smoke reference fixture 不是可解码 PNG 而 fail closed 并止步 FLUX；第二次已证明 Qwen，但 FLUX 被 `ImageScaleToTotalPixels` 缺 `resolution_steps` 拒绝；最终 fix 在 live required-input preflight 与 `resolution_steps=1` 之后，本日 fresh authorized rerun 在 loopback `http://127.0.0.1:8188` 上同时对 Qwen 与 FLUX 通过 technical live acceptance（exactly one provider call per lane, replay adds zero, no remote/browser）。M7 现在是 accepted 的 technical live-local milestone；M8 仍缺人工 ChatGPT outputs 与 blinded review evidence，因此 P7.1 仍不得称为 quality-accepted。任何未来 live smoke/benchmark 仍需 explicit authorization。
- `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md` 是新的 v0.2 planning target；它不是已实现行为，也不是一次性实施授权。
- `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md` 已被 supersede，只保留为 provider-centric 历史设计与可复用安全契约来源。
- v0.2 的每个 runtime slice 都必须拥有独立 plan、明确验收、回滚路径和用户实施授权。P0-P8 与 Base AI Comic E2E 的当前状态见 runtime baseline 与 roadmap；P9+ 或任何新的 Provider/live slice 的 plan 不等于 runtime 实施授权，也不得据此推断后续 slice 已实现。P8 offline acceptance不授权新的paid/live submit。
- 某个 slice 落地前，与该 slice 冲突的当前契约继续有效；不得通过只改文档把 proposed behavior 描述成 runtime truth。
- Local Wan + ComfyUI 始终保持 legacy default，并在新 domain 中作为 optional `generated_video` asset capability 保留。任何远程 Provider 都必须在后续独立 slice 中满足 explicit opt-in、Budget Guard、Cloud Egress 和 crash-safe persistence gate。

## Agent Communication

- 除非用户明确要求其他语言，否则面向用户的回复默认使用中文。
- 过程更新要简短、具体，并且基于真实仓库证据。
- 如果执行 review，先给出问题和风险，再给摘要。

## Read Order

1. 用户请求。
2. 本 `AGENTS.md`。
3. [`docs/agent-primary-contract-matrix.md`](/home/reggie/vscode_folder/AI-VIDEO/docs/agent-primary-contract-matrix.md)。
4. [`.agent/harness/policy.yaml`](/home/reggie/vscode_folder/AI-VIDEO/.agent/harness/policy.yaml)，确认 task-owned paths 对应的 mandatory checks。
5. [`docs/v0.2-runtime-baseline.md`](/home/reggie/vscode_folder/AI-VIDEO/docs/v0.2-runtime-baseline.md)，确认当前已实现行为。
6. [`docs/v0.2-agentic-production-roadmap.md`](/home/reggie/vscode_folder/AI-VIDEO/docs/v0.2-agentic-production-roadmap.md)，确认 phase 状态与 gate。
7. `README.md`、active spec 和当前 slice 的 plan。
8. 相关源码文件及其对应测试。
9. `.agent/bug-memory/` 下与当前回归直接相关的记录，仅作为案例证据。
10. `.workflow/` 下的草稿或 brainstorming 产物，仅作为可选上下文。

## Conflict Resolution

当不同信息源冲突时，按以下优先级处理：

1. 用户的明确指令。
2. 当前代码、测试以及已验证的运行时行为。
3. 本 `AGENTS.md`。
4. `README.md`、设计文档和计划文档。
5. `.workflow/` 产物以及其他草稿状态。

如果用户请求会有意打破现有契约，必须在同一任务里同步更新测试与文档。

## Stable Product Contract

- Legacy runtime 保持 local-first/default-local；v0.2 远程 Provider 只有在对应 slice 获批并完成安全前置后才允许以 opt-in 方式加入，且永不成为默认 fallback。
- v0.2 的顶层 Agent 是 Codex；仓库不得另造通用 Agent runtime。仓库未来只拥有 durable production contract、asset/provenance state、dependency/invalidation、render adapter 和 QA/repair receipts。
- v0.2 基础 Production Path 必须在没有 Video Provider 时仍能用 image、motion graphics、voice、captions 和 deterministic composition 产出完整视频；`generated_video` 只是 Shot 的可选 visual strategy。
- 当前公共 CLI 面保持为 `ai-video validate`、`ai-video run`、`ai-video resume`；任何 v0.2 新命令必须在独立 plan 中同步 CLI tests、README 和退出码契约。
- `validate` 必须保持无副作用；默认不得联网、上传素材、创建 run 目录或触发付费调用。
- `run` 必须创建 run 目录，按顺序执行 shots，并产出 manifest 与相关产物。
- `resume` 必须基于已持久化的 manifest 状态运行，而不是重新启动一个新 run。
- run manifest 是 pipeline 状态的持久化真相源，必须原子写入。
- 除非用户要求迁移，否则保持 `README.md` 中描述的产物目录结构不变。
- 写入配置解析结果和 manifest 记录的路径必须是干净的绝对路径。
- Legacy mode 保持“上一镜头最后一帧可喂给下一镜头”的链式生成模型；v0.2 P5 dependency graph必须保持precise transitive invalidation，不得退化为顺序式blanket stale。
- 保持项目对 workflow 的通用性，依赖 template + binding，而不是在 CLI 或 pipeline 中写死节点 ID。
- P2 Production Project Core 是当前 runtime truth：只读加载 strict v2 schemas、验证 semantic hashes、project-root containment、六种 Shot `visual_strategy`、concrete references 和 exact Asset Registry revision。
- P2 reader 不拥有 writer、activation、lifecycle mutation、desired fingerprint、renderer 或 Provider。已验收的 P2A `ProductionStateCommitter` 是 v2 project/registry/render/graph snapshot 写入、active pointer 切换与 explicit recovery 的唯一 owner。
- P3/P4 `ResolvedTimeline` 是唯一 order/frame/sample/timing owner；P5只能把它作为opaque fingerprint input消费，不得在graph中推导或另造canonical timeline。
- P5 immutable graph不得保存fresh/stale/failed/blocked/superseded等mutable state；Manifest 2.3是active graph、desired/applied fingerprints与lifecycle的唯一owner。Same-desired failure不得auto-retry，exact replay不得重复调用provider/renderer或推进state。Composition、ResolvedTimeline、renderer source与render只能由同一次final `RenderStateSnapshot` activation原子标记fresh，旧render evidence不得分别推进这些node。
- P7 不修改或复制 P5 resolver：`ImageGenerationRequest` 必须显式绑定 exact Character/Scene/reference inputs；generated PNG 激活后，只能由既有 dependency graph/resolver 计算 target Shot visual projection 及其精确下游 invalidation。Manifest 2.5 组合 P6/P7 mutable lifecycle，`ProductionStateCommitter` 仍是 image evidence、project/registry/graph activation 与 explicit recovery 的唯一 public writer owner。

## Module Boundaries

- `src/ai_video/cli.py`：只负责参数解析和面向用户的命令编排。
- `src/ai_video/config.py`：负责 YAML 读取、配置校验、本地策略与路径解析。
- `src/ai_video/workflow_loader.py`：负责 workflow 模板加载与 UI 到 API 的转换。
- `src/ai_video/workflow_renderer.py`：负责纯渲染逻辑与 binding 应用。
- `src/ai_video/comfy_client.py`：负责 ComfyUI 传输、轮询、产物下载与类型化失败。
- `src/ai_video/pipeline.py`：负责 shot 顺序执行、重试、链式传递、resume 决策与进度回调。
- `src/ai_video/manifest.py`：负责 manifest 持久化、哈希和 stale/validity 辅助逻辑。
- `src/ai_video/ffmpeg_tools.py`：负责 clip 校验、抽帧、标准化与拼接。
- `src/ai_video/production/models.py`：负责 strict v2 schemas、envelopes 和 cross-field model invariants。
- `src/ai_video/production/hashing.py`：负责 canonical semantic hash、artifact sealing 和 hash verification。
- `src/ai_video/production/paths.py`：负责 project-root containment、symlink 防逃逸和 v2 path resolution。
- `src/ai_video/production/validation.py`：负责 Shot visual strategy、reference 和 project-level static validation。
- `src/ai_video/production/registry.py`：负责 read-only Asset Registry snapshot、revision、entry bytes 和 containment verification。
- `src/ai_video/production/project.py` 及 private `_image_project_reader.py` / `_voice_project_reader.py` helpers：负责 read-only v2 bundle loading、Manifest-selected project/registry selection verification 与 selected image/voice candidate evidence reopen；不得写入、恢复或激活 state。
- `src/ai_video/production/dependency.py`：负责pure immutable graph construction、desired fingerprint resolution、blocked/frontier propagation和selective rebuild decision；不得写文件、Manifest、registry或runtime status。
- `src/ai_video/production/image.py`：负责 pure P7 image request/preview/authorization/result/provenance contract、PNG measured validation、candidate scope validation 与 `ImageAssetProvider` protocol；不得写文件、调用 Provider 或修改 Manifest。
- `src/ai_video/production/comfy_image.py`：负责 sealed P7.1 local execution profile、loopback-only ComfyUI adapter、exact workflow binding 与 pre-submit compatibility preflight；不得成为第二 writer，也不得接受 remote endpoint。
- `src/ai_video/production/image_import.py`：负责 truthful human web-image import receipt、PNG validation 与 exact candidate commit preparation；实际写入仍只能由 `ProductionStateCommitter` 完成。
- `src/ai_video/production/state_commit.py` 及 private `_state_commit_*` implementation modules：共同实现 P2A 唯一 v2 state writer、snapshot activation、commit-point error mapping 和 explicit recovery；`ProductionStateCommitter` façade仍是唯一 public owner，private modules不得形成第二 writer。
- `src/ai_video/production/__init__.py`：只暴露已批准的v0.2 public imports，不承载实现逻辑。

P2 reader、registry、validation和P5 dependency modules均不得写入或激活state；P2A writer/commit/recovery protocol必须继续由`state_commit.py`单一拥有，不得把mutation分散到reader、registry、dependency或Legacy manifest/pipeline。不要随意把职责跨模块搬运。优先做局部、小范围、低漂移的修复。

## Coding Standards

- 遵循仓库现有的 Python 风格、命名方式和 import 模式。
- 优先使用朴素、可读的方案，而不是炫技式抽象。
- 函数和类尽量保持单一职责。
- 追求高内聚、低耦合。不要跨越模块边界去操作别的模块内部状态。
- 优先依赖注入，而不是硬编码外部依赖。

## Architecture Ratchet

- 当 architecture boundary 与追求 minimal local diff 发生实质冲突时，architecture boundary 优先；“保持改动最小”不得被解释为可以继续扩大已有 oversized、multi-responsibility module。
- Architecture gate baseline 只用于 grandfather existing debt；不得为了隐藏 regression 而刷新或放宽 baseline。Correctness-critical transaction lifecycle 应保持为一个 cohesive domain boundary，不能为了减小文件而机械拆散 transaction invariant。

## Error Handling Contract

- 跨模块失败应使用 `AiVideoError` 与 `ErrorCode`。
- 是否可重试应根据类型化错误元数据决定，而不是依赖临时字符串匹配。
- 常规 CLI 成功/失败输出中不要泄露原始堆栈。

## Change Rules

- 本仓库单人、单 writer 开发默认直接在 `main` 工作。除非用户明确要求，否则不要创建 feature branch 或 `worktree`；不要仅因为存在可保留且与任务不冲突的 dirty 修改、改动多个文件、使用 plan/spec 或 skill 而增加 Git 隔离。
- 编辑前先研究现有源码和测试，匹配当前命名、imports 和数据流。
- 改动要增量化、范围收敛。
- 除非用户明确批准或任务明确要求，否则不要新增运行时依赖。
- 不要在不同时更新测试和文档的情况下修改 manifest schema、产物布局、CLI 参数或退出码语义。
- 除非任务明确与这些输出相关，否则不要编辑 `.workflow/`、`runs/` 或生成产物。
- 当仓库已有标准生产加载路径时，测试不要绕开它。例如 workflow 模板测试应走 `load_workflow_template()`。
- 如果用户可见行为发生变化，在同一任务里更新最近的相关文档。
- 如果工作区里已有与本任务无关的用户改动，不要碰它们，要绕开它们工作。
- 如果当前任务与现有未提交改动冲突，先停下并报告冲突，不要覆盖。

## Tooling Preferences

- 搜索与文件发现优先使用 `rg` 和 `rg --files`。
- 优先直接调用二进制，并显式设置工作目录。
- 日常文件编辑使用 `apply_patch`。
- 除非用户明确要求，否则避免破坏性 git 命令。
- 只 stage 属于当前任务的文件。

## Verification Rules

- 任何用户可见行为变更，都要新增或更新测试。
- 迭代时优先跑定向测试，结束前再跑对应的更大范围测试。
- 对纯文档/规则变更，代码测试可以不跑；对行为变更，测试是必需的。
- 除非用户明确要求真实本地冒烟，否则 ComfyUI 和 ffmpeg 编排优先使用 mock 或 fake 测试。
- 新增或修改行为时，要覆盖 public function、边界情况和错误情况。

## Development Verification Harness

- 本仓库的开发 Harness 是 [`scripts/agent_harness.py`](/home/reggie/vscode_folder/AI-VIDEO/scripts/agent_harness.py)；它把 exact staged delta 或 commit range 路由到已有 mandatory tests/checks，并在 `.agent/harness/runs/<run_id>/receipt.json` 写 execution evidence。`--path` 只允许 advisory inspect，不得生成 completion receipt。
- [`.agent/harness/policy.yaml`](/home/reggie/vscode_folder/AI-VIDEO/.agent/harness/policy.yaml) 是 changed-path category、check command 与 fail-safe fallback 的 machine-readable truth。修改映射时必须同步 Harness tests 与 contract matrix。
- `make harness-inspect` 显示当前 Git changes 需要的 checks；`make harness-verify` 只验证 non-empty staged scope；已提交 changes 使用 `make harness-verify-range BASE_REF=<ref> HEAD_REF=<ref>`，其中 `HEAD_REF` 必须解析到当前 `HEAD`；`make harness-test` 只验证 Harness 自身。
- Completion verification MUST 在 detached temporary worktree 中执行 exact staged snapshot 或 exact head commit；source HEAD/index scope 在 checks 前后必须一致。这样 unrelated dirty work 不进入 execution tree，也不需要通过手写 path list 隐藏。
- 任何 code 或 executable tooling change 在完成前 MUST 有 fresh passing receipt，并用 `make harness-receipt RECEIPT=<path>` 校验 self-hash、policy hash 与 current snapshot。Documentation-only change可以只命中 `scope_diff_check`；Harness/control-plane change还必须命中 `harness_tests`。
- Production/source category 使用 task-delta Architecture Gate（`--base-ref`）；version-controlled baseline 的 repository-wide health 只由 `make harness-repository` 单独报告，不得让历史 debt 阻断 unrelated task receipt。
- 未被 policy 映射的 task path必须 fail safe 到 full pytest suite与task-delta Architecture Gate；`make harness-audit` 必须拒绝 owned source/test/workflow 的 mapping drift。
- Harness check subprocess 使用 argv + `shell=False`、explicit timeout、sanitized credential/proxy/tool environment；pytest Python process 由 `scripts/harness_pytest_guard.py` 阻止 non-loopback address-bearing socket/DNS API。该 guard 不是 subprocess/OS network namespace；policy不得把可能联网的 child executable列为默认 check。Harness 不调度 Agent、不修改产品 state、不执行 live Provider smoke，也不替代代码、测试或 runtime evidence。
- [`.github/workflows/mandatory-gate.yml`](/home/reggie/vscode_folder/AI-VIDEO/.github/workflows/mandatory-gate.yml) 在每个 targeting `main` 的 pull request 上以 exact PR base/head SHA 运行 `make harness-audit` 与现有 `make harness-verify-range`；required check context MUST 稳定为 `mandatory-gate / verify`。CI 必须从 GitHub runner 生成自己的 receipt、JUnit 与 logs artifact，MUST NOT 信任开发者提交的本地 receipt，也不得读取 Provider secret 或运行 live Provider、ComfyUI、付费 smoke。
- Workflow 存在或 workflow-only push 不等于 server enforcement。GitHub `main` ruleset 必须 active，要求 pull request、branch up to date 与 `mandatory-gate / verify`，并阻止 force push/deletion；普通 actor 不得 bypass。服务端 gate 完成状态必须通过 GitHub API 读取 workflow run/check、ruleset enforcement 和 branch protection/ruleset truth 来证明。

## Checks By Change Type

- Config 或路径逻辑：`tests/test_config.py`
- Workflow 加载或渲染：`tests/test_workflow_loader.py` 和/或 `tests/test_workflow_renderer.py`
- Manifest 或 resume 逻辑：`tests/test_manifest.py`、`tests/test_pipeline.py`、`tests/test_resume_e2e.py`
- CLI 行为：`tests/test_cli.py`
- Comfy 传输行为：`tests/test_comfy_client.py`
- ffmpeg 行为：`tests/test_ffmpeg_tools.py`
- P2 schema、hash、path、strategy、registry 或 loader：`tests/test_production_models.py`、`tests/test_production_validation.py`、`tests/test_production_registry.py`、`tests/test_production_project.py`
- P2 与 Legacy Config/CLI isolation：在上述 P2 tests 之外加跑 `tests/test_config.py`、`tests/test_cli.py`
- P5 graph/resolution/Manifest/recovery：`tests/test_production_dependency.py`、`tests/test_production_selective_rebuild.py`、`tests/test_production_models.py`、`tests/test_production_project.py`、`tests/test_production_state_commit.py`、`tests/test_production_state_recovery.py`
- P7 image contract/activation/recovery：`tests/test_production_image.py`、`tests/test_production_image_e2e.py`、`tests/test_production_models.py`、`tests/test_production_registry.py`、`tests/test_production_validation.py`、`tests/test_production_project.py`、`tests/test_production_dependency.py`、`tests/test_production_selective_rebuild.py`、`tests/test_production_state_commit.py`、`tests/test_production_state_recovery.py`
- Harness、policy、runtime/network guard、runs contract 或 `Makefile`：`tests/test_agent_harness.py`

如果一次改动跨越多个表面，就运行所有对应测试文件。

## Decision Gates

除非用户已经明确要求，否则遇到以下变更先暂停并确认：

- 引入新依赖。
- 修改公共 CLI 命令名、参数名或退出码语义。
- 修改 `runs/` 下的 manifest schema 或产物目录结构。
- 把本地优先策略改成默认允许远程主机。
- 引入前端、API server、队列管理、音频，或其他 MVP 规范中明确排除的子系统。
- 执行 P7.1 live smoke/benchmark、任何新的 P8 Provider/live submit、v0.2 P9 runtime slice，或把未验收的 plan/spec contract 写成当前行为。P2-P8 与 Base AI Comic E2E 已在 local `main`；P7.1 已通过 offline executable gates 与 2026-08-18 technical live-local acceptance，但仍未通过 M8 blinded quality benchmark。任何未来 P7.1 live smoke、benchmark、H3/Seedance live submit、新 P8 adapter 或 P9 runtime slice仍需各自独立 explicit authorization。任何新的 v2 writer、activation、schema/layout mutation仍需独立授权与 crash-safety tests。P1只允许在其Legacy scope内做独立bugfix/release handling，不得借此扩展新product domain。

## Session Continuity

- 如果未来会话中存在 `.agent/context/session-handoff.md`，应在阅读本文件后、开始实质代码工作前读取它。
- 涉及已有回归类时，先查 `.agent/bug-memory/` 下直接相关记录；bug-memory 是案例证据，不覆盖 code、tests、spec 或本文件。
- handoff 或 `.workflow/` 记录只作为上下文，绝不能覆盖真实代码、测试或用户明确指令。

## Repository-Specific Don't Repeat This

- 不要通过对同一 `run_id` 再次调用 `run()` 来实现 resume；resume 必须从持久化 manifest 状态起步。
- 不要把带有 `..` 片段的相对产物路径写进 manifest 或已解析配置状态。
- 在更新 `final_output` 这类终态 run 状态后，不要绕过 manifest 的原子写入。
- 在测试里不要通过裸 YAML/JSON 解析去加载 workflow 模板，如果生产路径是 `load_workflow_template()`。
- 在本仓库做视频分析时，默认使用项目本地的 `video-analysis` MCP；`videoscan` 仅作为可选的全局辅助工具用于元数据或不带 AI 分析的抽帧，不要把它当作主分析通道。

## Completion Standard

在宣称任务完成前，确认：

- 变更过的契约已在代码和测试中体现。
- 如果公共行为变了，相关文档也已更新。
- 对应改动面的验证确实跑过。
- Code 或 executable tooling change 已生成 fresh passing Harness receipt，并在 final delivery 中报告其 repository-relative path。
- 最终说明里清楚标注剩余风险或未验证区域。
