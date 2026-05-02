# Feature Spec: F-002 - project-wizard

**Priority**: High
**Contributing Roles**: system-architect, ux-expert, ui-designer
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- 向导 MUST 以分步引导方式将 YAML 驱动的配置模型转化为用户可理解的表单，MUST NOT 引入新的配置格式
- 向导 MUST 生成与 `load_project()` 完全兼容的 `project.yaml`
- 向导 MUST 支持草稿保存，避免用户中途丢失配置
- 向导 MUST 提供 ComfyUI 连接测试功能（EP-005），实时验证可达性
- 向导 MUST 预填充 Smart Defaults，使用户无需修改任何参数即可完成项目创建（零配置启动）
- 向导完成项目创建后 SHOULD 生成包含至少一个占位 shot 的 `shots.yaml`
- 向导 MUST 支持导入已有 `project.yaml`，将 CLI 用户迁移到前端
- 角色配置步骤 MUST 支持图片上传，MUST 限制文件大小（20MB）和类型（jpg/png/webp）

### 用户体验需求

- 向导 MUST 遵循全屏单任务布局（D-014），每步内容居中显示（max-width 680px）
- 每步 MUST 不超过 5 个可交互字段（EP-008 渐进披露原则）
- 高级参数 MUST 折叠在"高级设置"中（EP-008 L3 层）
- 角色配置步骤 MUST 可跳过，MUST 有明显可见的"跳过此步"按钮
- 用户 MUST 可随时返回修改已完成步骤，已填数据 MUST 保留
- 每步完成 MUST 自动保存为草稿，刷新页面不丢失
- 每个配置项 MUST 有 `?` 图标 hover 显示解释文案（WCAG 2.1 AA — EP-003）
- 向导步骤指示器 MUST 在顶部持久显示，标明当前步骤和完成状态
- 向导 MUST 支持键盘导航，步骤切换 MUST 自动聚焦到新步骤的首个交互元素（EP-003）

### 技术需求

- 草稿 MUST 存储为独立文件（`~/.ai-video/drafts/{draft_id}.json`），MUST NOT 混入正式项目目录
- finalize MUST 调用 `ProjectConfig.model_validate()` 进行完整校验
- YAML 生成 MUST 使用 `exclude_defaults=True`，写入后 MUST 通过 `load_project()` 回读验证
- 校验端点 MUST 返回 `{valid: bool, errors: list[str], warnings: list[str]}`
- 分辨率预设 MUST 作为主要交互模式，原始数值输入作为次要（EP-008 Essential/Advanced 分层）

## 2. Design Decisions

### Decision 1: 向导步骤分解与配置映射

- **Context**: `ProjectConfig` 包含 5 个配置组（`comfy`, `workflow`, `output`, `defaults`, `characters`），需转化为用户可理解的步骤
- **Options Considered**:
  - (A) 严格按配置组分步（5 步，每步对应一个配置组）— 技术导向，用户不理解"ComfyUI 配置"含义
  - (B) 以用户目标为导向分步（4 步：项目信息 → 连接服务 → 默认参数 → 角色）— 减少步骤数，合并 workflow 选择到项目信息
  - (C) 极简分步（3 步：项目 → 参数 → 确认）— 步骤过少，单步信息量过大
- **Chosen Approach**: 方案 B，结合角色设计具体方案。4 步向导：
  - Step 1: 项目基本信息（名称、输出目录、工作流模板、绑定文件）
  - Step 2: 连接生成服务（ComfyUI 地址 + 连接测试）
  - Step 3: 默认参数（分辨率、FPS、时长、种子、提示词）
  - Step 4: 角色配置（可选）→ 确认摘要
- **Trade-offs**: 优势：步骤数适中，用户认知负担低；劣势：Step 1 信息密度较高，需通过折叠和 Smart Defaults 缓解
- **Source**: ux-expert (Step Decomposition), ui-designer (Step-by-Step Design), system-architect (API Design)

### Decision 2: Smart Defaults 零配置启动

- **Context**: 非技术用户应能在不修改任何参数的情况下完成项目创建
- **Options Considered**:
  - (A) 所有字段留空，强制用户填写 — 认知负荷高，新手无法完成
  - (B) 预填充所有默认值，用户仅需输入项目名 — 零配置启动
- **Chosen Approach**: 方案 B。预填充 `comfy.base_url=http://127.0.0.1:8188`、`width/height=512x512`、`fps=16`、`clip_seconds=2`、`seed=随机`、`negative_prompt`/`style_prompt` 模板值。用户只需输入项目名即可完成创建
- **Trade-offs**: 优势：新手友好，快速上手；劣势：默认值可能不适合所有场景，但可通过高级设置修改
- **Source**: ux-expert (Smart Defaults Strategy), ui-designer (Step 2 Default Parameters)

### Decision 3: ComfyUI 连接测试 (EP-005)

- **Context**: 用户需确认 ComfyUI 可用后再进入后续步骤，避免配置完成后才发现服务不可达
- **Options Considered**:
  - (A) 仅在 finalize 时检查 — 太晚，浪费用户时间
  - (B) 在 ComfyUI 地址输入处提供即时连接测试按钮 — 主动预防
  - (C) 持久健康指示器 — 实时但过于打扰
- **Chosen Approach**: 方案 B。ComfyUI 地址字段 MUST 提供内联"测试连接"按钮，点击后调用 `/api/validate/comfy-url`，显示验证结果（绿勾/红叉 + 重试）。连接状态不持久显示（避免干扰）
- **Trade-offs**: 优势：用户在正确时机获得反馈；劣势：需主动点击，不会自动检测
- **Source**: EP-005, ux-expert (Connection Test), ui-designer (Connection Test Button)

### Decision 4: 角色管理 UI 间隙 (EP-002)

- **Context**: 当前 `CharacterProfile` 数据模型存在但前端缺少角色管理 UI，向导的角色步骤需填补此间隙
- **Options Considered**:
  - (A) 角色步骤作为必填步骤 — 阻止不需要角色的用户
  - (B) 角色步骤可跳过，提供卡片式轻量角色添加 — 平衡功能与易用性
- **Chosen Approach**: 方案 B。角色步骤 MUST 可跳过，使用卡片式添加（Collapsible 卡片），参考图 MUST 显示缩略图预览。IPAdapter 参数 MUST 折叠在卡片内（EP-008 L3 层）
- **Trade-offs**: 优势：不强制角色配置，支持无角色视频；劣势：用户可能跳过但后续发现需要角色一致性
- **Source**: EP-002, ux-expert (Step 5 角色), ui-designer (Character Card)

### Decision 5: 参数 3 层分类 (EP-008)

- **Context**: 向导中参数数量多，需组织信息层级以降低认知负荷
- **Options Considered**:
  - (A) 所有参数平铺展示 — 信息量过大
  - (B) 二层分类（基本/高级）— 不够精细，高级参数中仍有重要度差异
  - (C) 三层分类（Essential/Advanced/Expert）— EP-008 建议的 3 层体系
- **Chosen Approach**: 方案 C，具体映射：
  - L1 Essential（始终可见）：项目名、ComfyUI 地址、工作流选择
  - L2 Recommended（默认展开）：分辨率预设、FPS、时长
  - L3 Advanced（默认折叠）：具体数值、种子策略、超时设置、远程连接
- **Trade-offs**: 优势：渐进披露精确，用户不被不相关参数干扰；劣势：三层折叠增加交互深度
- **Source**: EP-008, ux-expert (Progressive Disclosure), conflict_map F-003 (SUGGESTED: 3-tier taxonomy)

### Decision 6: 布局过渡 — 向导到卡片列表 (D-015)

- **Context**: 向导步骤间全屏单任务，但进入"编辑分镜"步骤后需切换为卡片列表（F-003）
- **Resolution**: 向导内嵌卡片列表。Step Indicator 保留但缩小为紧凑模式，内容区扩展为全宽卡片列表。过渡 MUST 使用 300ms 动画
- **Source**: guidance-specification.md D-015, conflict_map F-002 (RESOLVED: wizard embeds card list)

## 3. Interface Contract

### 草稿 API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/draft` | 创建草稿项目 |
| GET | `/api/projects/draft/{draft_id}` | 获取草稿 |
| PUT | `/api/projects/draft/{draft_id}` | 更新草稿（增量） |
| POST | `/api/projects/draft/{draft_id}/finalize` | 校验并创建正式项目 |

### 校验 API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/validate/comfy-url` | 校验 ComfyUI 可达性 |
| GET | `/api/validate/workflow-template` | 校验 workflow 模板 |
| GET | `/api/validate/binding` | 校验 binding 文件 |

### 模板 API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/templates` | 列出预置项目模板 |
| GET | `/api/workflow-templates?dir={path}` | 浏览 workflow JSON 文件 |

### 组件接口

**`<WizardStep>`**: Props: `title`, `description`, `children`
**`<ParameterField>`**: Props: `label`, `description`, `tooltip`, `required`, `error` (EP-008 分层)
**`<PathSelector>`**: 文件/目录选择器，支持类型过滤
**`<ConnectionTestButton>`**: ComfyUI 连接测试按钮（idle/loading/success/failure 四态）

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| YAML round-trip 丢失注释 | Low | MVP 接受（前端生成新 YAML 无需保留注释） |
| ComfyURL 校验耗时阻塞向导 | Medium | 异步校验 + 前端 debounce |
| 大量参考图片上传阻塞 | Medium | 分片上传或限制数量（MVP 限制 5 张/角色） |
| 模板文件路径不合法 | Medium | 服务端路径校验 + 沙箱限制 |
| 向导到卡片列表布局过渡突兀 | Medium | 300ms 动画 + Step Indicator 保留 |

## 5. Acceptance Criteria

1. 用户仅输入项目名 MUST 可完成项目创建，其余字段使用 Smart Defaults
2. 向导步骤间切换 MUST 保留已填数据，返回上一步 MUST 显示之前输入
3. ComfyUI 连接测试 MUST 在 5s 内返回结果，MUST 正确反映服务可达性
4. finalize 后生成的 `project.yaml` MUST 通过 `load_project()` 回读验证一致
5. 草稿自动保存 MUST 在每步完成后触发，刷新页面 MUST 恢复草稿数据
6. 角色配置步骤 MUST 可跳过，跳过后项目 MUST 可正常创建
7. 参考图上传 MUST 限制 20MB/张，MUST 仅接受 jpg/png/webp
8. 每步 MUST 不超过 5 个可交互字段（不含折叠区域）
9. 所有参数 MUST 有 tooltip 解释（`?` 图标 hover 显示）
10. 导入已有 `project.yaml` MUST 自动填充所有步骤字段

## 6. Detailed Analysis References

- @../system-architect/analysis-F-002-project-wizard.md — 数据流、草稿 API、模板系统、YAML 生成策略、角色图片处理
- @../ux-expert/analysis-F-002-project-wizard.md — 用户旅程、步骤分解、Smart Defaults、错误预防、认知负荷控制
- @../ui-designer/analysis-F-002-project-wizard.md — 步骤布局设计、字段设计、组件规格、校验策略
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: F-001 (项目 CRUD API, 校验 API, 模板 API)
- **Required by**: F-003 (向导完成后进入分镜编辑), F-007 (向导定义了参数默认值体系)
- **Shared patterns**:
  - `<ParameterField>` 组件 — F-002, F-003, F-007 共用
  - `<PathSelector>` 组件 — F-002, F-007 共用
  - Smart Defaults 体系 — F-003, F-007 继承项目默认值
  - EP-008 三层参数分类 — F-003, F-007 均需遵循
- **Integration points**:
  - F-003: 向导 Step 4 确认后进入分镜编辑器（D-015 布局过渡）
  - F-007: 向导中的 defaults 成为参数调优的基线值
  - F-001: 项目创建调用 `POST /api/projects`，校验调用 validate 端点
