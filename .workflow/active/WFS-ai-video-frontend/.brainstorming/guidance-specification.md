# AI-VIDEO Frontend - Confirmed Guidance Specification

**Metadata**: 2026-05-02 | brainstorming | focus: frontend-for-local-video-pipeline | roles: system-architect, ux-expert, ui-designer

## 1. Project Positioning & Goals

**CONFIRMED Objectives**: 为 AI-VIDEO 纯本地 Python CLI 增加前端界面，服务非技术背景的内容创作者/设计师，降低 YAML 手写门槛，提供可视化编辑、生成监控、结果预览和历史浏览能力。

**CONFIRMED Success Criteria**:
- 非技术用户无需手写 YAML 即可完成从项目创建到视频预览的完整流程
- 向导式引导覆盖核心工作流，降低认知负荷
- 渐进式演进，前端作为 CLI 的可视化辅助起步，逐步独立

## 2. Concepts & Terminology

**Core Terms**: The following terms are used consistently throughout this specification.

| Term | Definition | Aliases | Category |
|------|------------|---------|----------|
| Shot | 视频链中一个镜头单元，对应一次 ComfyUI 生成 | 镜头、shot | core |
| Shot List | 有序镜头清单，定义完整视频生成流程 | 分镜表、shots.yaml | core |
| Run | 一次完整的视频生成执行，包含多个 shot 的执行记录 | 运行、执行 | core |
| Manifest | Run 的元数据记录，追踪每个 shot 的状态和产物 | manifest.json | technical |
| Workflow JSON | ComfyUI 可执行的节点图描述 | workflow、API prompt | technical |
| Binding | Shot 配置字段到 Workflow JSON 节点 ID 的映射规则 | binding.yaml | technical |
| Pipeline Runner | 编排 shot 顺序执行、帧传递、拼接的核心引擎 | pipeline | technical |
| Frame Relay | 前一 shot 的 last_frame 传递给下一 shot 的机制 | 帧接力 | core |

**Usage Rules**:
- All documents MUST use the canonical term
- Aliases are for reference only
- New terms introduced in role analysis MUST be added to this glossary

## 3. Non-Goals (Out of Scope)

The following are explicitly OUT of scope for this project:

- **多用户/权限系统**: MVP 只做本地单用户，多用户和权限管理后续考虑

**Rationale**: 聚焦单用户本地场景，避免过早引入认证授权复杂度。

## 4. System-Architect Decisions

### SELECTED Choices

**API 服务器技术选型**: FastAPI (Python)
- **Rationale**: Python 生态一致性好，可直接复用现有 comfy_client/pipeline 模块，asyncio 原生支持
- **Impact**: The system MUST use FastAPI as the API server framework. The backend MUST NOT introduce a secondary runtime (Node.js)
- **Requirement Level**: MUST

**实时通信方案**: SSE 先行 + WebSocket 预留
- **Rationale**: MVP 用 SSE 快速上线（单向推送足够），后续按需升级为 WebSocket（ComfyUI 原生支持 WS，未来可扩展交互控制）
- **Impact**: The system MUST implement SSE for generation progress in MVP. The API layer SHOULD reserve WebSocket upgrade capability for future phases
- **Requirement Level**: MUST (SSE) / SHOULD (WS 预留)

**Pipeline 非阻塞改造**: 渐进式异步化
- **Rationale**: MVP 用低侵入的 run_in_executor 包装同步代码，验证后逐步将热点方法改为 async
- **Impact**: The system MUST wrap PipelineRunner.run() in run_in_executor for MVP. The system SHOULD progressively refactor hot-path methods (poll_job, etc.) to native async in subsequent iterations
- **Requirement Level**: MUST (executor 包装) / SHOULD (逐步 async)

## 5. UX-Expert Decisions

### SELECTED Choices

**核心页面布局**: 向导式流程
- **Rationale**: 非技术用户需要步步引导，最小化认知负荷。步骤：配置项目 → 编辑分镜 → 执行监控 → 预览结果
- **Impact**: The frontend MUST present a step-by-step wizard as the primary navigation pattern
- **Requirement Level**: MUST

**Shot List 编辑模式**: 卡片式
- **Rationale**: 每个 shot 一张卡片，拖拽排序，展开编辑参数，直觉化操作
- **Impact**: The frontend MUST implement a card-based shot editor with drag-and-drop reordering
- **Requirement Level**: MUST

**生成进度展示**: 管道节点视图
- **Rationale**: 每个 shot 是管道中的一个节点，颜色表示状态（排队/执行中/完成/失败），比线性进度条更直观
- **Impact**: The frontend MUST render generation progress as a pipeline node view with shot-level status indicators
- **Requirement Level**: MUST

## 6. UI-Designer Decisions

### SELECTED Choices

**设计系统/组件库**: shadcn/ui
- **Rationale**: Tailwind + shadcn/ui 轻量可定制，社区活跃，适合快速 MVP
- **Impact**: The frontend MUST use shadcn/ui as the component library with Tailwind CSS for styling
- **Requirement Level**: MUST

**视频预览播放器**: 原生先行 + 增强预留
- **Rationale**: MVP 用 HTML5 原生 video 标签，简单可靠；后续按需升级为 video.js/plyr 等增强播放器
- **Impact**: The frontend MUST use native HTML5 video for MVP. The video player component SHOULD be designed for swappable enhancement
- **Requirement Level**: MUST (原生) / SHOULD (增强预留)

**布局策略**: 全屏单任务
- **Rationale**: 向导式流程偏好全屏单任务，每次只显示一个步骤，最小化认知负荷
- **Impact**: The frontend MUST use full-screen single-task layout as the primary layout strategy
- **Requirement Level**: MUST

## 7. Cross-Role Conflict Resolutions

**布局冲突 — 全屏单任务 vs 卡片式多 shot 编辑**:
- **Resolution**: 向导内嵌卡片列表。向导步骤间全屏单任务，进入"编辑分镜"步骤后切换为卡片列表布局，完成编辑后回到向导流程
- **Affected Roles**: ux-expert, ui-designer
- **Decision**: The frontend MUST embed card-based shot list within the wizard's editing step, transitioning from full-screen single-task to card-list layout within that step

**进度粒度冲突 — 渐进式异步化 vs 管道节点视图**:
- **Resolution**: MVP 只上报 shot 级状态（排队/执行中/完成/失败），管道视图仅显示节点颜色；节点级进度作为后续迭代
- **Affected Roles**: system-architect, ux-expert
- **Decision**: The system MUST report shot-level status in MVP. The system MAY report node-level progress in future iterations

## 8. Cross-Role Integration

**CONFIRMED Integration Points**:
- API Server → Pipeline Runner: FastAPI 包装 pipeline.run()，通过 SSE 上报状态
- API Server → ComfyClient: 复用现有 HTTP 通信，MVP 不改造 ComfyClient
- API Server → File System: 提供静态文件服务（clip.mp4, last_frame.png, final.mp4）
- Frontend → API Server: REST 端点用于 CRUD 操作，SSE 端点用于实时进度
- Frontend → YAML/Config: 通过 API Server 读写 project.yaml 和 shots.yaml

## 9. Risks & Constraints

**Identified Risks**:
- Pipeline 阻塞调用 → 缓解: run_in_executor 包装 + 状态回调上报
- ComfyUI WebSocket 事件未接入前端 → 缓解: MVP 用 SSE 轮询 pipeline 状态，后续直连 ComfyUI WS
- 大文件视频传输延迟 → 缓解: 本地文件服务直读，不走额外转码
- 非技术用户的参数验证 → 缓解: 前端表单验证 + API 端 schema 校验双保险

## 10. Feature Decomposition

**Constraints**: Max 8 features | Each independently implementable | ID format: F-{3-digit}

| Feature ID | Name | Description | Related Roles | Priority |
|------------|------|-------------|---------------|----------|
| F-001 | api-server | FastAPI 后端 API 层，包装现有 CLI 模块为 REST + SSE 端点 | system-architect | High |
| F-002 | project-wizard | 向导式项目创建/配置流程，引导非技术用户设定项目参数 | ux-expert, ui-designer | High |
| F-003 | shot-card-editor | 卡片式 Shot List 编辑器，支持拖拽排序、参数编辑、提示词输入 | ux-expert, ui-designer | High |
| F-004 | generation-monitor | 管道节点视图展示生成进度，shot 级状态上报，SSE 实时推送 | system-architect, ux-expert | High |
| F-005 | result-gallery | 视频和帧预览画廊，支持 clip/last_frame/final 浏览和下载 | ui-designer, ux-expert | Medium |
| F-006 | run-history | 历史 runs 浏览，基于 manifest.json 展示执行记录和产物 | ux-expert | Medium |
| F-007 | param-tuner | 参数调优面板，实时验证、workflow JSON 预览、一键重跑 | system-architect, ux-expert | Medium |

## 11. Next Steps

**Automatic Continuation** (auto mode):
- Auto mode assigns agents for role-specific analysis
- Each selected role (system-architect, ux-expert, ui-designer) gets conceptual-planning-agent
- Agents read this guidance-specification.md for context

## Appendix: Decision Tracking

| Decision ID | Category | Question | Selected | Phase | Rationale |
|-------------|----------|----------|----------|-------|-----------|
| D-001 | Intent | 前端主要用户画像 | 内容创作者/设计师 | 1 | 非技术背景，需图形化引导 |
| D-002 | Intent | 前端与 CLI 关系 | 渐进式演进 | 1 | MVP 做 CLI 辅助，逐步独立 |
| D-003 | Intent | 部署环境 | 本地优先 + 远程兼容 | 1 | 先本地模式，预留远程能力 |
| D-004 | Scope | Non-Goals | 多用户/权限系统 | 1.5 | MVP 只做单用户 |
| D-005 | Roles | 角色选择 | system-architect, ux-expert, ui-designer | 2 | 覆盖架构、体验、视觉三个维度 |
| D-006 | system-architect | API 技术选型 | FastAPI (Python) | 3 | 生态一致性好，复用现有代码 |
| D-007 | system-architect | 实时通信 | SSE 先行 + WS 预留 | 3 | MVP 快速上线，后续升级 |
| D-008 | system-architect | Pipeline 改造 | 渐进式异步化 | 3 | 低侵入包装，逐步改 async |
| D-009 | ux-expert | 核心页面 | 向导式流程 | 3 | 非技术用户需步步引导 |
| D-010 | ux-expert | Shot 编辑 | 卡片式 | 3 | 拖拽排序，直觉化操作 |
| D-011 | ux-expert | 进度展示 | 管道节点视图 | 3 | 节点颜色表示状态，直观 |
| D-012 | ui-designer | 设计系统 | shadcn/ui | 3 | 轻量可定制，快速 MVP |
| D-013 | ui-designer | 视频播放器 | 原生先行 + 增强预留 | 3 | MVP 简单可靠，后续升级 |
| D-014 | ui-designer | 布局策略 | 全屏单任务 | 3 | 最小化认知负荷 |
| D-015 | Cross-Role | 布局冲突 | 向导内嵌卡片列表 | 4 | 编辑步骤内切换为卡片布局 |
| D-016 | Cross-Role | 进度粒度 | Shot 级状态 (MVP) | 4 | MVP 粗粒度，后续细化 |
