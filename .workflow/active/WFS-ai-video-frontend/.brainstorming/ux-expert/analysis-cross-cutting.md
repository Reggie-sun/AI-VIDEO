# Cross-Cutting UX Decisions: AI-VIDEO Frontend

**Framework Reference**: @../guidance-specification.md

## 1. Global Navigation Model

### Primary: Step-by-Step Wizard (MUST)

向导式导航作为主轴，四个核心步骤对应四个全屏视图：

```
Step 1: 配置项目 (F-002) → Step 2: 编辑分镜 (F-003) → Step 3: 执行监控 (F-004) → Step 4: 预览结果 (F-005)
```

**Navigation Rules**:
- 向导步骤指示器 MUST 持久显示在页面顶部，标明当前步骤和可跳转状态
- 用户 MUST 能在已完成步骤间自由跳转（非线性的完成-回看模式）
- 未到达的步骤 SHOULD 显示为锁定状态，但 MAY 允许高级用户直接跳转
- 每步 MUST 有"上一步"和"下一步/跳过"操作

### Secondary: Sidebar Navigation (SHOULD)

在向导步骤之外，提供侧边栏访问辅助功能：
- 历史记录 (F-006)
- 参数调优 (F-007)
- 项目设置（全局参数）

**Transition Rule**: 向导步骤间切换时，侧边栏 MUST 自动折叠以保持全屏单任务体验。

### Tertiary: Contextual Actions

上下文操作（如从结果画廊直接重跑、从历史记录恢复参数）MUST 通过快捷入口而非导航层级实现。

## 2. Error Handling & Feedback Strategy

### Error Classification

| Error Type | User Impact | Display Pattern | Recovery |
|------------|-------------|-----------------|----------|
| Validation | 输入不合规 | Inline message below field | 直接修正 |
| Network | API 不可达 | Toast notification + retry button | 自动/手动重试 |
| Generation | Shot 生成失败 | Node highlight in pipeline view | 重跑/跳过/调参 |
| System | 磁盘空间不足 | Full-screen blocking modal | 清理空间/取消 |

### Feedback Principles

1. **Inline > Toast > Modal**: 严重度递增，打断性递增
2. **Actionable Messages**: 错误提示 MUST 包含建议操作，禁止只显示原始错误码
3. **Error Mapping**: 后端 `ErrorCode` MUST 映射为用户友好文案，例如 `DISK_SPACE_LOW` → "存储空间不足，请清理磁盘或更换输出目录"
4. **Persistent Errors**: 生成失败的错误信息 MUST 持续显示直到用户明确处理，不可自动消失

### Loading State Patterns

- **Skeleton Loading**: 页面初始加载 MUST 使用骨架屏
- **Spinner with Label**: 短操作 (< 3s) 使用 spinner + 文案说明
- **Progress Bar**: 长操作 (> 3s) 使用进度条 + 百分比
- **SSE Stream Indicator**: 实时推送连接 MUST 有视觉指示器（脉冲点/状态标签）

## 3. Accessibility Baseline (WCAG 2.1 AA)

### MUST Compliance

- **Color Contrast**: 所有文本与背景对比度 >= 4.5:1；管道节点状态颜色 MUST NOT 作为唯一信息载体，必须配合图标/文字
- **Keyboard Navigation**: 所有交互元素 MUST 可通过键盘访问；拖拽排序 MUST 提供键盘替代方案（上下箭头移动）
- **Screen Reader**: 语义化 HTML + ARIA labels；实时状态更新（SSE）MUST 使用 `aria-live` region
- **Focus Management**: 向导步骤切换 MUST 自动聚焦到新步骤的首个交互元素
- **Text Scaling**: 界面 MUST 在 200% 缩放时保持可用

### SHOULD Compliance

- **Reduced Motion**: 尊重 `prefers-reduced-motion`，减少动画
- **High Contrast**: 检测 `prefers-contrast: more`，增强对比度
- **Focus Visible**: 自定义 focus indicator，确保可见性

## 4. Design System Consistency

### Component Governance

基于 shadcn/ui (MUST)，遵循以下治理规则：

- **Component First**: 新交互模式 MUST 优先使用 shadcn/ui 现有组件；仅当无匹配时才创建自定义组件
- **Token Compliance**: 间距、颜色、字体 MUST 使用 shadcn/ui 设计 token，禁止硬编码值
- **Variant Consistency**: 按钮、输入框、卡片等 MUST 使用统一的 variant 体系（default/destructive/outline/ghost）

### Interaction Consistency

| Pattern | Specification | Applies To |
|---------|--------------|------------|
| Card expansion | Click to expand, click outside to collapse | F-003 shot cards |
| Drag handle | Left-side grip icon, cursor: grab/grabbing | F-003 shot reorder |
| Inline edit | Click value to edit, Enter to confirm, Esc to cancel | F-003, F-007 |
| Delete confirmation | Destructive action MUST show confirmation dialog | All delete operations |
| Auto-save indicator | "Saved" / "Saving..." / "Unsaved changes" | All forms |

## 5. State Management Interaction Patterns

### Application State Model

```
CurrentProject → CurrentShotList → CurrentRun → CurrentView
```

**State Rules**:
- 项目切换 MUST 提示保存未保存变更
- Shot list 修改 MUST 实时自动保存（debounce 500ms）
- 生成运行中 MUST 阻止破坏性编辑（删除 shot、修改项目参数）
- 状态持久化 MUST 使用 localStorage 作为 fallback，避免刷新丢失

### Empty State Design

每个列表/画廊 MUST 有空状态设计：
- **空项目列表**: 引导创建第一个项目的 CTA
- **空分镜表**: 解释 shot 概念 + "添加第一个镜头"按钮
- **空历史记录**: "还没有运行记录，创建第一个视频"
- **空结果画廊**: 等待生成完成的进度提示

### Optimistic Updates

- 列表操作（添加/删除/排序 shot）MUST 使用乐观更新，立即反映到 UI
- API 失败时 MUST 回滚乐观更新并显示错误通知
- 表单提交（项目配置、shot 参数）SHOULD NOT 使用乐观更新，需等待确认

## 6. Terminology & Labeling Strategy

### User-Facing Terminology Mapping

| Internal Term | User-Facing Label | Tooltip/Description |
|---------------|-------------------|---------------------|
| Shot | 镜头 | 视频中的一个片段，每个镜头会独立生成 |
| Shot List | 分镜表 | 按顺序排列的镜头清单，定义完整视频 |
| Run | 生成任务 | 一次完整的视频生成过程 |
| Manifest | (隐藏) | 内部使用，不对用户暴露 |
| Workflow JSON | (隐藏) | 内部使用，不对用户暴露 |
| Binding | (隐藏) | 内部使用，不对用户暴露 |
| Pipeline Runner | 生成引擎 | (内部引用) |
| Frame Relay | 帧接力 | 前一个镜头的最后一帧会传递给下一个镜头 |
| ComfyUI | 生成服务 | AI 图像/视频生成后端 |
| Seed | 随机种子 | 控制生成结果的随机性，相同种子产生相同结果 |

### Labeling Rules

- UI 中 MUST 使用用户友好标签而非内部术语
- 技术 MUST 术语（如 Workflow JSON、Binding）MUST NOT 出现在主界面
- Tooltip MUST 为每个参数提供简明解释
- 错误信息 MUST 使用用户友好描述，原始错误码仅在"详情"展开中显示
