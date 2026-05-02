# Feature Spec: F-007 - param-tuner

**Priority**: Medium
**Contributing Roles**: system-architect, ux-expert, ui-designer
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- 参数调优面板 MUST 支持实时验证用户修改的参数合法性
- 调优面板 MUST 支持 Workflow JSON 预览，调用 `workflow_renderer.py` 进行 dry-run 渲染
- 调优面板 MUST 支持一键重跑（re-run），MUST 创建新 Run（新 run_id），MUST NOT 修改原 Run
- 参数验证 MUST 使用 `DefaultsConfig.model_validate()` 和 `ShotSpec.model_validate()` 校验
- Workflow 预览 MUST 调用 `render_workflow()` 进行真实渲染，MUST NOT 提交到 ComfyUI
- Re-run MUST 基于原 Run 的项目配置应用 overrides，MUST 写入修改后的临时配置到新 Run 目录
- Re-run MUST 通过 `run_in_executor` 执行 PipelineRunner，MUST 通过 SSE 推送进度（与 F-004 一致）
- 调优面板 MUST 支持三种作用域：当前镜头、全部镜头、项目默认
- 调优面板 MUST 支持从多个入口进入：分镜编辑器、结果画廊、运行历史、生成监控

### 用户体验需求

- 调优面板 MUST 采用双栏布局：左侧参数编辑（40%）、右侧预览（60%）
- 参数 MUST 按逻辑分组（EP-008 三层分类），每组不超过 5 个字段
- 高级参数 MUST 默认折叠，标题 MUST 显示自定义项数量
- 参数修改后 MUST 在 300ms 内显示验证结果（内联指示器：绿勾/黄警告/红叉）
- 覆盖项目默认值的参数 MUST 显示"Custom" badge + "Reset to default"按钮
- 种子参数 MUST 优化交互：显示当前值 + "随机"按钮 + "锁定"按钮 + "递增"按钮
- Workflow JSON 预览 MUST 实时更新（300ms debounce），MUST 高亮变更节点/字段
- "重新生成" MUST 先显示参数变更摘要，用户确认后跳转到生成监控（F-004）
- 面板底部 MUST 显示变更计数："已修改 3 项参数"
- 未保存的参数变更 MUST 在离开页面时提示保存

### 技术需求

- `render_workflow` MUST 通过 `run_in_executor` 包装，避免阻塞事件循环
- 参数验证 SHOULD 估算显存需求（VRAM），基于分辨率和模型类型的经验值
- Re-run MUST 使用独立临时目录 + UUID 避免配置文件冲突
- 单 shot 重跑 MAY 在 MVP 中推迟实现（需 PipelineRunner 改造）
- Workflow JSON diff MUST 递归对比，只返回有差异的字段
- 原始 Run 的 manifest MUST 保持不可变

## 2. Design Decisions

### Decision 1: 双栏布局 — 参数编辑 + 预览

- **Context**: 调优时需同时看到参数和效果预览
- **Options Considered**:
  - (A) 全屏参数表单 — 无法同时看到预览
  - (B) 侧面板参数 + 主区域预览 — 预览空间大但参数空间受限
  - (C) 双栏布局（40%/60%）— 平衡编辑和预览
- **Chosen Approach**: 方案 C。左侧 40% 宽度参数面板（可滚动），右侧 60% 宽度预览面板（sticky，不随左侧滚动）。MVP 面板分隔固定，后续 MAY 支持拖拽调整
- **Trade-offs**: 优势：编辑时预览始终可见；劣势：小屏幕时两侧空间都不足（EP-007 限定 1280px+）
- **Source**: ux-expert (Panel Layout), ui-designer (Split-Panel Layout)

### Decision 2: 作用域选择 — 当前/全部/默认

- **Context**: 用户可能想调优单个 shot，也可能想批量修改所有 shot 的共有参数
- **Options Considered**:
  - (A) 仅支持单 shot 调优 — 无法批量修改
  - (B) 仅支持全局默认 — 无法精细调优
  - (C) 三种作用域可切换 — 最灵活
- **Chosen Approach**: 方案 C。面板顶部 MUST 提供 scope 切换（Tab 或 Radio）：当前镜头（默认）、全部镜头、项目默认。切换 scope 时 MUST 保留当前修改，MUST 显示影响范围
- **Trade-offs**: 优势：灵活覆盖所有调优场景；劣势：三种 scope 的交互逻辑不同，增加实现复杂度
- **Source**: ux-expert (Parameter Scope Selection)

### Decision 3: 实时验证 vs 提交验证

- **Context**: 参数验证时机影响用户体验
- **Options Considered**:
  - (A) 仅提交时验证 — 用户可能长时间填写错误值
  - (B) 实时验证（每次修改后）— 即时反馈但可能打扰
  - (C) 防抖实时验证（300ms）— 即时反馈且不频繁
- **Chosen Approach**: 方案 C。参数修改后 MUST 在 300ms 内显示验证结果。验证 MUST 检查必填字段、数值范围、角色引用有效性、文件路径存在性。跨字段验证（分辨率/帧数过大）MUST 显示警告
- **Trade-offs**: 优势：即时反馈，减少提交时错误；劣势：高频 API 调用，需 debounce
- **Source**: ux-expert (Real-time Validation), ui-designer (Validation Rules)

### Decision 4: Workflow JSON 预览 — 技术用户专属

- **Context**: Workflow JSON 预览对高级用户有价值，但非技术用户不理解
- **Options Considered**:
  - (A) 始终显示 JSON 预览 — 非技术用户困惑
  - (B) 不提供 JSON 预览 — 高级用户缺失重要信息
  - (C) 双模式预览（JSON/Visual），默认 JSON — 高级用户可用，普通用户可切换
- **Chosen Approach**: 方案 C。右侧预览面板 MUST 支持两种模式：JSON 模式（默认，语法高亮 + 实时更新 + 变更高亮）和 Visual 模式（前 shot last_frame、init_image、角色参考图）。Tab 切换 [JSON] [Visual]
- **Trade-offs**: 优势：两种用户类型都满足；劣势：Visual 模式需额外实现
- **Source**: ux-expert (Workflow JSON Preview rule: "MUST NOT 干扰普通用户"), ui-designer (Dual Preview Modes)

### Decision 5: 重跑与活跃 Run 冲突处理

- **Context**: conflict_map 标记 F-007 存在"re-run vs active run"冲突
- **Options Considered**:
  - (A) 静默拒绝 — 用户不知道为什么无法重跑
  - (B) 直接排队 — 但本地仅支持 1 个 Run
  - (C) 检查 API → 409 对话 → 用户选择 — 透明处理
- **Chosen Approach**: 方案 C。点击"重新生成"时 MUST 先检查是否有活跃 Run（调用 API）。如有活跃 Run，MUST 显示对话框说明"当前有生成任务正在执行，请等待完成或取消后再试"，提供"查看进度"和"取消"选项
- **Trade-offs**: 优势：用户理解为什么无法重跑，有操作选择；劣势：增加一次 API 调用
- **Source**: conflict_map F-007 (SUGGESTED: check API → 409 dialog → proceed)

### Decision 6: 覆盖指示器 (Override Indicators)

- **Context**: 用户需区分哪些参数是自定义的、哪些继承自项目默认值
- **Options Considered**:
  - (A) 不区分 — 用户不知道参数来源
  - (B) 仅视觉区分（背景色）— 不够明确
  - (C) "Custom" badge + "Reset to default"按钮 — 明确且可操作
- **Chosen Approach**: 方案 C。覆盖项目默认值的参数 MUST 显示小"Custom" badge（`bg-accent/10 text-accent`），旁边 MUST 出现"Reset to default"按钮。点击 reset 恢复为项目默认值，badge 消失
- **Trade-offs**: 优势：非技术用户明确知道自定义了什么；劣势：增加 UI 元素
- **Source**: ui-designer (Override Indicators), EP-008 参数分层

### Decision 7: 参数变更摘要确认

- **Context**: 重跑前用户需确认参数变更，避免遗忘差异
- **Options Considered**:
  - (A) 直接重跑 — 用户可能忘记修改了什么
  - (B) 仅确认对话框 — 信息不足
  - (C) 变更摘要确认 — 列出所有修改项
- **Chosen Approach**: 方案 C。点击"重新生成"MUST 显示确认摘要："将重新生成镜头 #1，参数变更：种子 42→87, 时长 2s→3s"。用户确认后保存参数并跳转到生成监控
- **Trade-offs**: 优势：防止用户误操作；劣势：增加一步操作
- **Source**: ux-expert (One-Click Rerun Flow)

## 3. Interface Contract

### 参数验证 API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{name}/params/validate` | 校验参数修改 |

### Workflow 预览 API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{name}/shots/{shot_id}/workflow-preview` | 预览渲染后的 Workflow JSON |
| POST | `/api/projects/{name}/shots/{shot_id}/workflow-diff` | 对比两个 Workflow JSON |

### Re-run API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/runs/re-run` | 基于历史 Run 修改参数后重跑 |
| POST | `/api/runs/{run_id}/shots/{shot_id}/re-run` | 重跑单个 shot（MAY 推迟） |

### 入口上下文

| 入口 | 预填充状态 | 聚焦字段 |
|------|-----------|---------|
| 分镜编辑器 (F-003) | 当前 shot 参数 | prompt |
| 结果画廊 (F-005) | shot 运行参数 | prompt |
| 运行历史 (F-006) | Run 完整配置 | 第一个参数组 |
| 生成监控 (F-004) | 失败 shot 参数 | 失败参数 |

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| render_workflow 阻塞事件循环 | Medium | run_in_executor 包装 |
| 参数组合导致 OOM | High | VRAM 估算 + 警告（不强制阻止） |
| Re-run 配置文件临时写入冲突 | Low | 使用独立临时目录 + UUID |
| Workflow JSON diff 对比大文件性能 | Low | 限制 diff 深度 + 前端延迟渲染 |
| 单 shot 重跑需 PipelineRunner 改造 | Medium | MVP 推迟，仅支持全量重跑 |
| 活跃 Run 时 409 冲突 | Medium | 前端预检查 + 友好对话框 |

## 5. Acceptance Criteria

1. 双栏布局 MUST 左侧参数（40%）右侧预览（60%），预览面板 MUST sticky
2. 参数 MUST 按 EP-008 三层分组，高级组默认折叠
3. 参数修改后 MUST 在 300ms 内显示验证结果（绿勾/黄警告/红叉）
4. 覆盖默认值的参数 MUST 显示"Custom" badge 和"Reset to default"按钮
5. 种子参数 MUST 提供：当前值 + 随机按钮 + 锁定按钮 + 递增按钮
6. Workflow JSON 预览 MUST 在 300ms debounce 后更新，MUST 高亮变更字段
7. 预览面板 MUST 支持 JSON 和 Visual 两种模式切换
8. "重新生成"MUST 先显示参数变更摘要，确认后跳转到 F-004
9. 有活跃 Run 时 MUST 显示 409 对话框，提供"查看进度"和"取消"选项
10. Re-run MUST 创建新 Run，原始 Run manifest MUST 保持不可变
11. 作用域切换（当前/全部/默认）MUST 保留当前修改
12. 面板底部 MUST 显示变更计数
13. 未保存变更离开页面 MUST 提示保存
14. 从 F-003/F-005/F-006/F-004 入口进入 MUST 正确预填充参数

## 6. Detailed Analysis References

- @../system-architect/analysis-F-007-param-tuner.md — 数据流、API 设计、参数分类、Workflow diff、Re-run 约束
- @../ux-expert/analysis-F-007-param-tuner.md — 用户旅程、面板布局、交互设计、种子交互、认知负荷控制
- @../ui-designer/analysis-F-007-param-tuner.md — 双栏布局设计、参数面板设计、预览面板、验证规则、入口设计
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: F-001 (参数验证 API, Re-run API, Workflow 预览 API), F-003 (Shot 参数模型), F-004 (重跑后跳转监控 + SSE 推送)
- **Required by**: 无（F-007 是调优终端功能，其他功能通过入口链接到它）
- **Shared patterns**:
  - `<ParameterField>` 组件 — F-002, F-003, F-007 共用
  - `<StatusBadge>` 组件 — F-003, F-004, F-006, F-007 共用
  - `<PathSelector>` 组件 — F-002, F-007 共用
  - SSE Manager — F-004 和 F-007 的 re-run 共用
  - EP-008 三层参数分类 — F-002, F-003, F-007 均需遵循
- **Integration points**:
  - F-003: 从分镜编辑器入口进入，预填充当前 shot 参数
  - F-004: 重跑后跳转到监控页；失败 shot "调整参数后重试"跳转到调优
  - F-005: 画廊中"Open in Tuner"跳转到调优
  - F-006: 历史记录"恢复参数"跳转到调优预填充历史配置
  - F-001: Re-run 调用 `POST /api/runs/re-run`，Workflow 预览调用 workflow-preview 端点
