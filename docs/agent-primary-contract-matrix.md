# AI-VIDEO Primary Contract Matrix

这份矩阵是 Codex、Claude 以及类似编码 Agent 共用的执行契约。

请与 `AGENTS.md` 配合使用：在修改某个表面前，先找到对应行，保留列出的不变量，并运行要求的验证。

## Global Rules

| Contract Area | 中文说明 |
| --- | --- |
| Product Scope | 纯本地、Python CLI、本地 ComfyUI 编排、不得隐式依赖托管服务。 |
| Truth Source | 用户请求 > 代码/测试/运行时证据 > 仓库契约 > plans/specs > `.workflow/` 草稿记录。 |
| Change Style | 小步、可测试、低漂移，并保持模块边界稳定。 |
| Error Model | 跨模块统一使用 `AiVideoError` 与 `ErrorCode`。 |
| Dependency Policy | 除非有明确理由且获得请求，否则不新增运行时依赖。 |
| Output Policy | 保持 `runs/<run_id>/` 下可预测、稳定的产物目录结构。 |

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

### Local-Only Contract

Agent 不得悄悄侵蚀本地优先承诺。

在没有用户明确指示时，不得引入以下内容：

- 远程服务依赖，
- 云端托管的视频生成 API，
- ComfyUI 的后台进程管理器，
- 遥测或外部状态同步，
- 把前端或 API server 变成 CLI 的隐式前置条件。

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
