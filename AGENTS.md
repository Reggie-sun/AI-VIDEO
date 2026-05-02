# AI-VIDEO Agent Guide

适用于在本仓库中工作的 Codex、Claude 以及其他任何编码 Agent。

## Purpose

本仓库是一个纯本地的 Python CLI，用于围绕本地 ComfyUI 服务编排长视频生成流程。

Agent 必须维护当前产品承诺：

- 默认本地优先，默认 CLI 优先。
- 以 manifest 为核心的执行与恢复机制。
- `runs/<run_id>/` 下可预测、稳定的产物目录结构。
- 对 config、workflow 渲染、pipeline 状态、resume、ffmpeg 行为、CLI 行为保持较强测试覆盖。

## Agent Communication

- 除非用户明确要求其他语言，否则面向用户的回复默认使用中文。
- 过程更新要简短、具体，并且基于真实仓库证据。
- 如果执行 review，先给出问题和风险，再给摘要。

## Read Order

1. 用户请求。
2. 本 `AGENTS.md`。
3. [`docs/agent-primary-contract-matrix.md`](/home/reggie/vscode_folder/AI-VIDEO/docs/agent-primary-contract-matrix.md)。
4. `README.md` 与直接相关的 spec / plan 文档。
5. 相关源码文件及其对应测试。
6. `.workflow/` 下的草稿或 brainstorming 产物，仅作为可选上下文。

## Conflict Resolution

当不同信息源冲突时，按以下优先级处理：

1. 用户的明确指令。
2. 当前代码、测试以及已验证的运行时行为。
3. 本 `AGENTS.md`。
4. `README.md`、设计文档和计划文档。
5. `.workflow/` 产物以及其他草稿状态。

如果用户请求会有意打破现有契约，必须在同一任务里同步更新测试与文档。

## Stable Product Contract

- 默认保持产品为纯本地形态。除非用户明确要求，否则不要引入云端视频 API、托管服务或把远程 ComfyUI 设为默认。
- 公共 CLI 面保持为 `ai-video validate`、`ai-video run`、`ai-video resume`。
- `validate` 必须保持无副作用。
- `run` 必须创建 run 目录，按顺序执行 shots，并产出 manifest 与相关产物。
- `resume` 必须基于已持久化的 manifest 状态运行，而不是重新启动一个新 run。
- run manifest 是 pipeline 状态的持久化真相源，必须原子写入。
- 除非用户要求迁移，否则保持 `README.md` 中描述的产物目录结构不变。
- 写入配置解析结果和 manifest 记录的路径必须是干净的绝对路径。
- 保持“上一镜头最后一帧可喂给下一镜头”的链式生成模型。
- 保持项目对 workflow 的通用性，依赖 template + binding，而不是在 CLI 或 pipeline 中写死节点 ID。

## Module Boundaries

- `src/ai_video/cli.py`：只负责参数解析和面向用户的命令编排。
- `src/ai_video/config.py`：负责 YAML 读取、配置校验、本地策略与路径解析。
- `src/ai_video/workflow_loader.py`：负责 workflow 模板加载与 UI 到 API 的转换。
- `src/ai_video/workflow_renderer.py`：负责纯渲染逻辑与 binding 应用。
- `src/ai_video/comfy_client.py`：负责 ComfyUI 传输、轮询、产物下载与类型化失败。
- `src/ai_video/pipeline.py`：负责 shot 顺序执行、重试、链式传递、resume 决策与进度回调。
- `src/ai_video/manifest.py`：负责 manifest 持久化、哈希和 stale/validity 辅助逻辑。
- `src/ai_video/ffmpeg_tools.py`：负责 clip 校验、抽帧、标准化与拼接。

不要随意把职责跨模块搬运。优先做局部、小范围、低漂移的修复。

## Coding Standards

- 遵循仓库现有的 Python 风格、命名方式和 import 模式。
- 优先使用朴素、可读的方案，而不是炫技式抽象。
- 函数和类尽量保持单一职责。
- 追求高内聚、低耦合。不要跨越模块边界去操作别的模块内部状态。
- 优先依赖注入，而不是硬编码外部依赖。

## Error Handling Contract

- 跨模块失败应使用 `AiVideoError` 与 `ErrorCode`。
- 是否可重试应根据类型化错误元数据决定，而不是依赖临时字符串匹配。
- 常规 CLI 成功/失败输出中不要泄露原始堆栈。

## Change Rules

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

## Checks By Change Type

- Config 或路径逻辑：`tests/test_config.py`
- Workflow 加载或渲染：`tests/test_workflow_loader.py` 和/或 `tests/test_workflow_renderer.py`
- Manifest 或 resume 逻辑：`tests/test_manifest.py`、`tests/test_pipeline.py`、`tests/test_resume_e2e.py`
- CLI 行为：`tests/test_cli.py`
- Comfy 传输行为：`tests/test_comfy_client.py`
- ffmpeg 行为：`tests/test_ffmpeg_tools.py`

如果一次改动跨越多个表面，就运行所有对应测试文件。

## Decision Gates

除非用户已经明确要求，否则遇到以下变更先暂停并确认：

- 引入新依赖。
- 修改公共 CLI 命令名、参数名或退出码语义。
- 修改 `runs/` 下的 manifest schema 或产物目录结构。
- 把本地优先策略改成默认允许远程主机。
- 引入前端、API server、队列管理、音频，或其他 MVP 规范中明确排除的子系统。

## Session Continuity

- 如果未来会话中存在 `.agent/context/session-handoff.md`，应在阅读本文件后、开始实质代码工作前读取它。
- handoff 或 `.workflow/` 记录只作为上下文，绝不能覆盖真实代码、测试或用户明确指令。

## Repository-Specific Don't Repeat This

- 不要通过对同一 `run_id` 再次调用 `run()` 来实现 resume；resume 必须从持久化 manifest 状态起步。
- 不要把带有 `..` 片段的相对产物路径写进 manifest 或已解析配置状态。
- 在更新 `final_output` 这类终态 run 状态后，不要绕过 manifest 的原子写入。
- 在测试里不要通过裸 YAML/JSON 解析去加载 workflow 模板，如果生产路径是 `load_workflow_template()`。
- 在本仓库做视频分析时，默认使用项目本地的 `video-analysis` MCP；`videoscan` 仅作为可选的全局辅助工具用于元数据或不带 AI 分析的抽帧，不要把它当作主分析通道。
- 对绑定了 `init_image` 的 workflow，不要让首镜头静默回退到模板里的占位图；首镜头必须显式提供 `shot.init_image`，或由上游 shot 提供 chain frame，`validate` 也必须能拦住这类错误。
- 做 I2V 质量迭代时，先检查“起始图构图是否支持目标动作”；不要拿“人物已居中站定”的起始图去追求“从画面左侧走入”这类需要明显重新构图的镜头，否则应先换 `init_image` 再调 prompt 或 sampler。

## Completion Standard

在宣称任务完成前，确认：

- 变更过的契约已在代码和测试中体现。
- 如果公共行为变了，相关文档也已更新。
- 对应改动面的验证确实跑过。
- 最终说明里清楚标注剩余风险或未验证区域。
