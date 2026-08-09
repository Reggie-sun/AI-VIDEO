# AI-VIDEO Primary Contract Matrix

这份矩阵是 Codex、Claude 以及类似编码 Agent 共用的执行契约。

请与 `AGENTS.md` 配合使用：在修改某个表面前，先找到对应行，保留列出的不变量，并运行要求的验证。

## Global Rules

| Contract Area | 中文说明 |
| --- | --- |
| Product Scope | 当前 `0.1.x` runtime 是 local-first Python CLI + default-local ComfyUI；v0.2 是 Agent-first AI Video / AI Comic Production Harness 的分阶段目标，未落地的 slice 不属于当前行为。 |
| Truth Source | 用户请求 > 代码/测试/运行时证据 > 仓库契约 > plans/specs > `.workflow/` 草稿记录。 |
| Change Style | 小步、可测试、低漂移，并保持模块边界稳定。 |
| Error Model | 跨模块统一使用 `AiVideoError` 与 `ErrorCode`。 |
| Dependency Policy | 除非有明确理由且获得请求，否则不新增运行时依赖。 |
| Output Policy | Legacy run 保持当前 flat `runs/<run_id>/` layout；v2 layout 只能由显式 v2 config 和已批准的 Manifest v2 slice 创建。 |
| Version Gate | P0 product reframe 已完成文档迁移；P1、independently accepted P2 与 independently accepted P2A 已在 local `main`，但尚未进入 `origin/main` 或 release；P3+ 每个 slice 仍必须有独立 plan、实施授权、验收、rollback 和对应 contract/docs/tests 更新。 |
| Agent Boundary | Codex 是 Production Agent；仓库提供 durable state、validation、provenance、dependency、render 和 QA harness，不实现第二套通用 Agent runtime。 |
| Renderer Ownership | AI-VIDEO 的 resolved timeline/composition contract 是时间线真相源；默认 renderer target 是 HyperFrames。Remotion 只能作为显式选择的 optional adapter，不能与 HyperFrames 串联重复 render。 |

## Contract Matrix

| Surface | Canonical Files | Invariants To Preserve | Common Safe Changes | Required Validation |
| --- | --- | --- | --- | --- |
| CLI Contract | `src/ai_video/cli.py`、`README.md`、`tests/test_cli.py` | 公共命令保持为 `validate`、`run`、`resume`。`validate` 必须无副作用。类型化失败要输出面向用户的错误信息，而不是原始 traceback。 | 增加小型参数、优化提示文案、接入新的内部选项、扩展进度输出。 | `pytest tests/test_cli.py -v` |
| Config Loading & Path Resolution | `src/ai_video/config.py`、`src/ai_video/models.py`、`tests/test_config.py` | project 和 shot 文件通过 YAML + Pydantic 加载。相对路径解析为干净的绝对路径。非本地 ComfyUI 主机需要显式 opt-in。未知角色必须报错。 | 增加校验、优化标准化逻辑、扩展兼容字段且不破坏现有配置。 | `pytest tests/test_config.py -v` |
| Workflow Loading | `src/ai_video/workflow_loader.py`、`tests/test_workflow_loader.py` | 同时接受 API JSON 和 UI workflow JSON。UI 图转换必须走标准 loader，而不是在别处重复实现。 | 优化校验或转换规则，同时保持现有 fixture 格式继续可用。 | `pytest tests/test_workflow_loader.py -v` |
| Workflow Rendering | `src/ai_video/workflow_renderer.py`、`tests/test_workflow_renderer.py` | 渲染必须是纯逻辑：把 template + binding + shot context 转成渲染后的 workflow，且不触发网络访问。binding 失败要给出可定位的 path 信息。 | 增加 binding 覆盖、优化 output prefix 处理、通过同一 path helper 支持新映射字段。 | `pytest tests/test_workflow_renderer.py -v` |
| ComfyUI Transport | `src/ai_video/comfy_client.py`、`tests/test_comfy_client.py` | client 只负责 HTTP 传输、轮询、产物收集和清理钩子。它不能知道 shot 编排顺序。本地优先策略不变。 | 优化重试行为、错误映射、轮询细节或产物选择。 | `pytest tests/test_comfy_client.py -v` |
| Pipeline Orchestration | `src/ai_video/pipeline.py`、`tests/test_pipeline.py`、`tests/test_resume_e2e.py` | shots 必须按顺序执行。上一帧可喂给下一 shot。重试要有边界。progress callback 应为可选且不侵入。resume 必须基于 manifest 状态并跳过仍然有效的工作。 | 优化进度输出、重试记录、stale 处理或 resume 决策。 | `pytest tests/test_pipeline.py tests/test_resume_e2e.py -v` |
| Manifest Persistence | `src/ai_video/manifest.py`、`tests/test_manifest.py` | manifest 写入必须原子化。哈希必须代表已持久化产物。成功 shot 的有效性必须基于哈希判断。下游 stale 状态必须来自上游变化。 | 增加 helper、扩展 manifest 校验、收紧 stale 检测。 | `pytest tests/test_manifest.py -v` |
| ffmpeg Boundary | `src/ai_video/ffmpeg_tools.py`、`tests/test_ffmpeg_tools.py` | ffmpeg helper 负责 probe、校验、抽帧、标准化与最终拼接。当 stream copy 不可用时，拼接必须具备兜底能力。 | 优化 fallback 行为、标准化参数或命令构造，同时保持输出兼容。 | `pytest tests/test_ffmpeg_tools.py -v` |
| Test Fixtures & Realism | `tests/conftest.py`、所有测试 | 在可行时，测试夹具应复用生产加载路径。编排测试优先使用 fake。除非用户明确要求，否则真实 ComfyUI 只是可选项。 | 扩展 fixtures、增加 e2e 风格 fake 测试、提高真实性但不引入网络依赖。 | 如果 fixture 改动较广，运行受影响测试文件外加 `pytest -v`。 |
| Output Layout | `README.md`、`src/ai_video/pipeline.py`、manifest 相关测试 | runs 必须写入 `runs/<run_id>/`，包含 manifest、shot 产物、normalized clips 和 final output。路径必须足够稳定，便于 resume 和排查工具使用。 | 增加额外元数据或调试产物，但不能破坏现有预期文件。 | `pytest tests/test_pipeline.py tests/test_manifest.py -v` |
| v2 Production Project Core | `src/ai_video/production/**`、`tests/test_production_*.py` | P2 只读加载 Manifest-selected project/registry exact revision；creative/asset refs 必须 content-addressed 且留在固定 project roots。不拥有 writer、lifecycle 或 desired fingerprint。 | 收紧 schema、strategy、reference、hash 或 containment validation，保持 no-network 和 Legacy isolation。 | `pytest tests/test_production_models.py tests/test_production_validation.py tests/test_production_registry.py tests/test_production_project.py tests/test_config.py tests/test_cli.py -q` |
| P2A Production State Commit | `src/ai_video/production/models.py`、`src/ai_video/production/project.py`、`src/ai_video/production/state_commit.py`、`tests/test_production_state_commit.py`、`tests/test_production_state_recovery.py` | `ProductionManifest` 是唯一 lifecycle owner；nested project/registry pointer 必须固定 exact path、semantic identity 和 file hash。`ProductionStateCommitter` 是唯一 writer/recovery owner；POSIX same-filesystem `state/commit.lock` 下 snapshot temp 必须 file-fsync、promote-without-overwrite、parent-directory-fsync 并 reopen verify。running/failed lifecycle 也会 durable Manifest write；仅 final active-pointer replace 是 single logical commit point。恢复必须显式，只接受 exact old/new pair；bounded owned temp 可清理，complete orphan 只能 preserve/report。P2 reader 仍只读，root `project.yaml` 是 stable validated entrypoint 而非 active bytes truth。 | 补强 P2A integrity/recovery validation，不能增加第二 writer/control plane、auto-recovery、CLI 或改变 Legacy Manifest/layout。 | `pytest tests/test_production_models.py tests/test_production_validation.py tests/test_production_registry.py tests/test_production_project.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |

## Cross-Cutting Contracts

### Resume Contract

任何触及 resume 的改动，都必须保留以下规则：

- resume 从 `manifest.json` 启动，而不是重新启动一个新 run。
- 已完成且仍有效的 shots 要被跳过。
- 无效、失败或 stale 的 shots 可以被重跑。
- 缺失的下游产物应触发修复或重跑，而不是静默成功。
- 恢复成功后，最终输出和 manifest 终态必须再次持久化。

最低验证：

```bash
pytest tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py -v
```

### Manifest Contract

任何触及 manifest 结构或持久化的改动，都必须保留：

- 原子写入，
- 稳定、可读的 JSON，
- 可持久化的 `final_output`，
- 在可用时可持久化的 config/template/binding 路径与哈希字段，
- 用于有效性检查的 per-shot 产物哈希。

最低验证：

```bash
pytest tests/test_manifest.py tests/test_pipeline.py -v
```

### Local-First Contract

Agent 不得悄悄侵蚀本地优先承诺。

在没有用户明确指示时，不得引入以下内容：

- 远程服务依赖，
- 云端托管的视频生成 API，
- ComfyUI 的后台进程管理器，
- 遥测或外部状态同步，
- 把前端或 API server 变成 CLI 的隐式前置条件。

### v0.2 Planning Gate

- 当前 code/tests 仍是 runtime truth；spec 和 plan 不能覆盖未实现行为。
- P0 只迁移 product/contract 文档；不得把 spec 写成 runtime truth。
- 本地 P1 只稳定 Legacy runtime，未引入新 product domain；其 plan 作为 historical stabilization record 保留。
- P2 已建立 ProductionProject、Assets、Shot visual strategy 的 read-only durable contract；它不拥有 writer、renderer 或云服务。
- P2A 已 independently accepted 并合并到 local `main`：唯一 writer/recovery owner 写 immutable v2 snapshots，并通过 nested active pointers and one Manifest replace activate exact pair。它不改变 P2 reader 的只读语义或 Legacy Manifest v1/layout，且尚未 push 或 release。
- P3 planning artifact 只定义一个 canonical renderer adapter 的未来边界；P2A prerequisite 已满足，但 Renderer Gate、dependency-install authorization、API reconciliation 和新的显式用户授权完成前不得实施，也不得建立两条并行 canonical render path。
- P4 才允许在独立 plan 中引入 Audio/Caption production domain；任何付费调用仍需显式 opt-in。
- P5 dependency graph 完成前，不得宣称支持跨 asset 的 selective rebuild。
- P6 strategy-aware QA/repair 完成前，不得让当前 `static_visuals` heuristic 自动否决合法的 `static_image` / `image_motion` Shot。
- P8 之前不得接入真实 generated-video cloud Provider；任何 paid Provider submit 仍受 Budget Guard、Cloud Egress 和 crash-safe persistence gate。
- 新 CLI、Manifest schema、artifact layout、远程行为、Audio 或 dependency 仍命中下方 Change Escalation Matrix。

## Change Escalation Matrix

| Proposed Change | Default Agent Action |
| --- | --- |
| Tighten validation while keeping current examples working | 直接实现，并补测试。 |
| Add an optional field compatible with existing configs | 直接实现；如果用户可见则同步补测试和文档。 |
| Change CLI names, flags, or exit-code meanings | 暂停并确认。 |
| Change manifest schema or artifact layout | 暂停并确认。 |
| Add a runtime dependency | 暂停并确认。 |
| Introduce remote/networked product behavior beyond local ComfyUI | 暂停并确认。 |
| Add frontend / API / server subsystems | 暂停并确认。 |

## Minimum Done Criteria

Agent 在宣称完成前，至少确认：

1. 上表中被改动到的契约行仍然成立。
2. 对应测试已经运行。
3. 用户可见行为变化已反映到 `README.md` 或相关文档。
4. 任何剩余缺口都已明确说明。
