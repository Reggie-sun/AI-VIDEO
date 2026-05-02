# Feature Spec: F-003 - shot-card-editor

**Priority**: High
**Contributing Roles**: system-architect, ux-expert, ui-designer
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- 编辑器 MUST 以卡片式展示 Shot List，支持拖拽排序、参数编辑、提示词输入
- 编辑器 MUST 嵌入向导"编辑分镜"步骤内（D-015），从全屏单任务布局过渡到全宽卡片列表
- 拖拽排序 MUST 通过 `PATCH /api/projects/{name}/shots/reorder` 持久化
- 编辑器 MUST 支持有效配置计算（合并 `defaults` + shot overrides），API 响应 MUST 包含 `overrides` 标记
- 编辑器 MUST 支持实时内联校验（id 唯一性、prompt 非空、角色引用有效性）
- 编辑器 MUST 支持批量校验 `POST /api/projects/{name}/shots/validate`
- 编辑器 MUST 支持撤销/重做（EP-004，Command Pattern），Ctrl+Z 可撤销添加/删除/排序操作
- 编辑器 MUST 支持 Shot CRUD 操作（添加、复制、删除），删除 MUST 需确认
- 编辑器 MUST 支持导入已有 `shots.yaml`，自动生成卡片
- 排序变更 MUST NOT 触发重新生成，已有 Run 中的顺序 MUST NOT 被修改

### 用户体验需求

- 卡片 MUST 有两种状态：折叠态（显示摘要）和展开态（编辑参数），默认折叠
- 提示词 MUST 是卡片中最大字号的文本，MUST 使用 Textarea 自动增高（min 2 行，max 6 行）
- 拖拽手柄 MUST 在卡片左侧，MUST 提供键盘替代方案（Alt+Up/Down，EP-003 WCAG）
- 角色关联 MUST 以 checkbox 标签形式展示，MUST NOT 允许自由文本输入（避免拼写错误）
- 高级参数 MUST 折叠在"高级参数"区域，折叠标题 MUST 显示自定义项数量："高级参数 (2 项已自定义)"（EP-008）
- 卡片间 MUST 显示 Frame Relay 连线，标注传递方向
- 操作按钮 MUST 在 hover 时才显示（减少视觉噪音）
- 超过 5 个镜头时 MUST 提供"全部折叠"按钮
- 编辑 MUST 自动保存（debounce 1s），MUST 在顶部显示保存状态指示器（EP-006）

### 技术需求

- 编辑器 SHOULD 使用乐观更新策略：拖拽排序立即更新本地顺序，异步 PATCH 到服务端
- 参数编辑 MUST 在 debounce 500ms 后 PUT 到服务端
- 服务端返回 400/409 时 MUST 回滚本地状态并显示错误
- API 响应 MUST 在 API 层计算有效配置（合并 defaults），MUST NOT 要求前端自行合并
- Frame Relay 排序变更后 API SHOULD 返回 warning，提示用户下次 Run 时链将改变

## 2. Design Decisions

### Decision 1: 卡片折叠/展开双态设计

- **Context**: 用户需要同时浏览多个 shot 的概览，也需要深入编辑单个 shot 的参数
- **Options Considered**:
  - (A) 所有卡片始终展开 — 超过 3 个 shot 时页面过长
  - (B) 折叠态显示摘要，点击展开编辑 — 平衡浏览与编辑
  - (C) 侧边栏列表 + 主区域编辑 — 类邮件客户端，导航复杂度高
- **Chosen Approach**: 方案 B。折叠态显示序号、prompt 摘要（2 行截断）、角色标签、时长/分辨率/种子。展开态显示完整表单，左侧显示 accent 色条。新卡片 MUST 立即展开
- **Trade-offs**: 优势：概览效率高，编辑聚焦；劣势：需要用户主动展开，可能忽略未填参数
- **Source**: ux-expert (Card Anatomy), ui-designer (Card Structure), conflict_map F-003 (RESOLVED: expand-to-edit)

### Decision 2: 拖拽排序 + 键盘替代 (EP-003)

- **Context**: Shot 顺序决定视频生成序列和 Frame Relay，排序是核心操作
- **Options Considered**:
  - (A) 仅拖拽排序 — 不满足 WCAG 键盘导航要求
  - (B) 仅上下箭头按钮 — 操作效率低
  - (C) 拖拽 + 键盘替代（Alt+Up/Down）— 完整可访问
- **Chosen Approach**: 方案 C。拖拽手柄在卡片左侧（6 点 grip 图标），拖拽时原位虚线占位、目标位置插入指示线。键盘替代：Alt+Up/Down 移动位置，MUST 提供屏幕阅读器公告
- **Trade-offs**: 优势：所有用户可操作，符合 WCAG 2.1 AA；劣势：键盘操作需额外实现
- **Source**: EP-003, ux-expert (Drag-and-Drop), ui-designer (Keyboard Alternative)

### Decision 3: 参数深度 vs 渐进披露 (EP-008)

- **Context**: conflict_map 标记 F-003 存在参数深度 vs 披露冲突，建议使用 EP-008 的 3 层分类
- **Options Considered**:
  - (A) 所有参数平铺在展开态 — 非技术用户被大量参数淹没
  - (B) 二层分类（基本/高级）— 高级中仍有使用频率差异
  - (C) 三层分类（Essential/Advanced/Expert）— EP-008 建议
- **Chosen Approach**: 方案 C，卡片内映射：
  - L1 Essential（展开态始终可见）：prompt, negative_prompt, characters, continuity_note
  - L2 Recommended（展开态默认可见）：seed, clip_seconds, fps, width/height
  - L3 Advanced（折叠区域）：init_image, IPAdapter 参数
- **Trade-offs**: 优势：新用户只看 L1 即可完成编辑；劣势：高级用户需多次展开
- **Source**: EP-008, conflict_map F-003 (SUGGESTED: 3-tier taxonomy per EP-008)

### Decision 4: 撤销/重做机制 (EP-004)

- **Context**: 误操作（如删除 shot、误排序）是编辑器中常见的用户痛点
- **Options Considered**:
  - (A) 无撤销 — 误操作不可恢复，用户焦虑
  - (B) 简单撤销（仅最后一项）— 有限但不够
  - (C) Command Pattern 完整撤销栈 — 支持多步撤销/重做
- **Chosen Approach**: 方案 C。MUST 维护操作历史栈，`Ctrl+Z` 撤销、`Ctrl+Shift+Z` 重做。支持撤销的操作：添加/删除/排序/参数修改。删除确认 MUST 提供"撤销"选项而非仅确认弹窗
- **Trade-offs**: 优势：用户信心提升，编辑体验专业；劣势：需维护 Command 栈状态，增加前端复杂度
- **Source**: EP-004, ux-expert (Undo Stack)

### Decision 5: 角色关联以 checkbox 标签形式

- **Context**: 角色是 Frame Relay 一致性的关键输入，需确保引用正确
- **Options Considered**:
  - (A) 自由文本输入角色名 — 易拼写错误，导致引用失效
  - (B) 下拉选择 — 可用但不够直观
  - (C) Checkbox 标签列表 — 直观，可多选，不可拼写错误
- **Chosen Approach**: 方案 C。角色 MUST 以可点击标签形式展示（`[hero x]`），点击取消选择，"添加"按钮打开可用角色下拉。角色列表 MUST 从项目配置中读取，编辑器中不可新增角色
- **Trade-offs**: 优势：引用准确性 100%，交互直观；劣势：需回项目设置添加新角色
- **Source**: ux-expert (Character Association), ui-designer (Character Selection)

### Decision 6: Frame Relay 可视化

- **Context**: Shot 顺序决定 Frame Relay（前 shot 的 last_frame 传递给下一个 shot），用户需理解此关系
- **Options Considered**:
  - (A) 不可视化 — 用户不了解帧接力机制
  - (B) 卡片间显示连线 + 箭头 — 直观表示传递方向
  - (C) 连线 + hover 显示详细说明 — 最完整
- **Chosen Approach**: 方案 C。卡片间 MUST 显示序号 + 连接线箭头，hover 连线 MUST 显示"Last frame from Shot N feeds into Shot N+1"。排序后连线 MUST 自动更新
- **Trade-offs**: 优势：Frame Relay 概念可视化，减少用户困惑；劣势：增加渲染复杂度
- **Source**: ux-expert (Layout Transition), ui-designer (Visual Sequence Indicator)

## 3. Interface Contract

### Shot CRUD API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/{name}/shots` | 列出镜头（含有效配置和 overrides 标记） |
| POST | `/api/projects/{name}/shots` | 添加镜头 |
| PUT | `/api/projects/{name}/shots/{shot_id}` | 更新镜头 |
| DELETE | `/api/projects/{name}/shots/{shot_id}` | 删除镜头 |
| PATCH | `/api/projects/{name}/shots/reorder` | 重排镜头 |
| POST | `/api/projects/{name}/shots/validate` | 批量校验 |

### 有效配置响应

```json
{
  "id": "shot_01",
  "prompt": "hero enters...",
  "overrides": ["seed", "fps"],
  "effective_seed": 42,
  "effective_fps": 16,
  "effective_width": 512,
  "effective_height": 512,
  "effective_clip_seconds": 2
}
```

### 校验结果响应

```json
{
  "valid": false,
  "errors": [{"shot_id": "shot_02", "field": "characters", "message": "Unknown character: char_99"}],
  "warnings": [{"shot_id": "shot_03", "field": "clip_seconds", "message": "Value 60 may cause long generation time"}]
}
```

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| Reorder 后 Frame Relay 链断裂 | Medium | API 返回 warning，不阻止操作，Run 时自然生效 |
| 并发编辑冲突（两个标签页） | Low | MVP 不处理（单用户本地场景） |
| 大量 shot (50+) 性能 | Medium | 前端虚拟滚动 + API 分页（后续迭代） |
| Prompt 编辑丢失 | Medium | Auto-save debounce 1s + 服务端校验双重保障 |
| Command Pattern 栈内存占用 | Low | 限制栈深度（50 步） |

## 5. Acceptance Criteria

1. 卡片 MUST 默认折叠，点击展开，折叠态 MUST 显示 prompt 摘要和角色标签
2. 拖拽排序 MUST 平滑过渡，释放后 MUST 在 300ms 内 PATCH 到服务端
3. 键盘 Alt+Up/Down MUST 移动 shot 位置，MUST 触发屏幕阅读器公告
4. `id` 字段 MUST 实时检查唯一性，重复时 MUST 标红
5. `prompt` 为空时，卡片折叠态 MUST 显示警告图标
6. Ctrl+Z MUST 撤销最近的添加/删除/排序操作（EP-004）
7. Auto-save MUST 在 1s debounce 后触发，顶部 MUST 显示 saving/saved/error 状态
8. 角色引用 MUST 仅展示项目已定义角色，MUST NOT 允许自由文本输入
9. 卡片间 MUST 显示 Frame Relay 连线和方向箭头
10. 高级参数折叠区 MUST 显示非默认值计数："高级参数 (2 项已自定义)"
11. 导入 `shots.yaml` MUST 自动生成对应卡片
12. 全部折叠按钮 MUST 在 shot 数量 > 5 时显示

## 6. Detailed Analysis References

- @../system-architect/analysis-F-003-shot-card-editor.md — 数据模型、Reorder 架构、校验规则、CRUD 模式、Prompt 增强支持
- @../ux-expert/analysis-F-003-shot-card-editor.md — 用户旅程、卡片解剖、交互设计、布局过渡、认知负荷控制
- @../ui-designer/analysis-F-003-shot-card-editor.md — 布局过渡动画、卡片设计规格、拖拽交互、字段设计、序列指示器
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: F-001 (Shot CRUD API, Reorder API, Validate API), F-002 (项目配置提供角色列表和 defaults 基线)
- **Required by**: F-004 (Shot List 确定管道节点), F-007 (Shot 参数为调优面板输入)
- **Shared patterns**:
  - `<ParameterField>` 组件 — F-002, F-003, F-007 共用
  - `<FrameThumbnail>` 组件 — F-003, F-004, F-005 共用
  - EP-008 三层参数分类 — F-002, F-003, F-007 均需遵循
  - EP-004 Command Pattern — 编辑器核心撤销机制
- **Integration points**:
  - F-002: 向导 Step 4 确认后进入编辑器（D-015 布局过渡）
  - F-004: 编辑器确认后的 Shot List 定义管道节点
  - F-007: 从编辑器入口进入参数调优，预填充当前 shot 参数
  - F-001: Reorder API 排序后 Frame Relay 链变更 warning
