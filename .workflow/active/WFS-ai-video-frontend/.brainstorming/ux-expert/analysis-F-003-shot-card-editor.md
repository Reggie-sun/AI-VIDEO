# UX Analysis: F-003 Shot Card Editor

**Feature**: 卡片式 Shot List 编辑器，支持拖拽排序、参数编辑、提示词输入
**Priority**: High | **UX Concern Level**: Critical
**Framework Reference**: @../guidance-specification.md

## User Journey

```
进入分镜编辑步骤 → 查看空/已有分镜表
  → 添加镜头 (创建空卡片 / 从模板 / 复制已有)
  → 编辑卡片 (展开 → 填写提示词 → 关联角色 → 调整参数)
  → 排序镜头 (拖拽调整顺序)
  → 预览分镜表 (缩略图/提示词概览)
  → 确认 → 进入下一步
```

## Information Architecture

### Card Anatomy

每个 Shot 卡片 MUST 包含以下层级信息：

**Collapsed State (默认)**:
```
┌────────────────────────────────────────────────┐
│ ⋮⋮  #1  shot_001                    [复制][删除] │
│      hero enters a quiet studio, medium shot    │
│      角色: hero · 2s · 512x512 · 16fps         │
└────────────────────────────────────────────────┘
```

**Expanded State (点击展开)**:
```
┌────────────────────────────────────────────────┐
│ ⋮⋮  #1  shot_001                    [复制][删除] │
│────────────────────────────────────────────────│
│ 提示词 (必填)                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ hero enters a quiet studio, medium shot      ││
│ └──────────────────────────────────────────────┘│
│ 反向提示词                                      │
│ ┌──────────────────────────────────────────────┐│
│ │ blur, inconsistent face                      ││
│ └──────────────────────────────────────────────┘│
│ 角色: [hero ✓]  [+ 添加角色]                    │
│ 连续性说明: [hero 保持同一服装和光线]             │
│────────────────────────────────────────────────│
│ ▸ 高级参数 (默认折叠)                            │
│   时长: [2s]  FPS: [16]  分辨率: [512x512]      │
│   种子: [自动]  初始图像: [无]                    │
└────────────────────────────────────────────────┘
```

### Field Mapping (ShotSpec → UI)

| ShotSpec Field | UI Label | Input Type | Required | Default | Group |
|----------------|----------|------------|----------|---------|-------|
| `id` | 镜头编号 | 自动生成 (可编辑) | Yes | `shot_NNN` | Basic |
| `prompt` | 提示词 | Textarea | Yes | — | Basic |
| `negative_prompt` | 反向提示词 | Textarea | No | 项目默认 | Basic |
| `characters` | 角色 | Checkbox list | No | [] | Basic |
| `continuity_note` | 连续性说明 | Text input | No | "" | Basic |
| `clip_seconds` | 时长 | Slider (1-10s) | No | 项目默认 | Advanced |
| `fps` | 帧率 | Select (8/16/24) | No | 项目默认 | Advanced |
| `width`/`height` | 分辨率 | Preset select | No | 项目默认 | Advanced |
| `seed` | 随机种子 | Number (或"自动") | No | 自动 | Advanced |
| `init_image` | 初始图像 | File upload | No | None | Advanced |
| `metadata` | (隐藏) | — | — | — | Hidden |

## Interaction Design

### Drag-and-Drop Reordering

**MUST Requirements**:
- 拖拽手柄 MUST 在卡片左侧，使用 `⋮⋮` 图标
- 拖拽开始时：原位显示虚线占位符，被拖卡片半透明跟随光标
- 拖拽过程中：目标位置显示插入指示线
- 拖拽释放时：MUST 平滑动画过渡到新位置
- 排序变更 MUST 即时保存（debounce 300ms）

**Keyboard Alternative** (WCAG):
- 聚焦卡片后，`Alt+Up/Down` 移动位置
- MUST 提供屏幕阅读器公告："镜头 1 已移动到第 3 位"

### Card Operations

| Operation | Trigger | Confirmation | Undo |
|-----------|---------|-------------|------|
| 添加 | "添加镜头"按钮 / 快捷键 `N` | 无 | 删除 |
| 复制 | 卡片右上角按钮 | 无 | 删除 |
| 删除 | 卡片右上角按钮 | MUST 确认 | `Ctrl+Z` |
| 展开/折叠 | 点击卡片标题区 | 无 | — |
| 批量删除 | 多选 + 删除 | MUST 确认 | `Ctrl+Z` |

### Prompt Input UX

提示词是最高频输入字段，MUST 优化输入体验：
- **Textarea with Auto-resize**: 输入区域 MUST 随内容自动增高（最小 2 行，最大 6 行）
- **Character Count**: MUST 显示字符数，接近上限时预警
- **Template Suggestions**: SHOULD 在空输入时显示常用提示词模板
- **Prompt History**: SHOULD 记录最近使用的提示词，支持快速复用
- **Multi-language**: MUST 支持中英文混合输入，无需切换输入法

### Character Association

角色关联是 Frame Relay 的关键输入：
- 角色 MUST 以 checkbox 标签形式展示（而非文本输入），避免拼写错误
- 已选角色 MUST 显示为可点击标签，点击取消选择
- 角色列表 MUST 从项目配置中读取，编辑器中不可新增角色（需回项目设置添加）
- 当 shot 关联角色时，MUST 在卡片折叠态显示角色缩略图

## Layout Transition

### Wizard-to-Card-List Transition

根据 guidance-specification.md 决策 D-015，向导步骤间全屏单任务，进入"编辑分镜"步骤后切换为卡片列表布局：

**Transition Rules**:
1. 从"配置项目"步骤进入"编辑分镜"步骤时，MUST 平滑过渡到卡片列表视图
2. 顶部向导步骤指示器 MUST 保留，但缩小为紧凑模式
3. 卡片列表 MUST 填充主要区域，底部固定"确认分镜表 → 下一步"按钮
4. 返回上一步时，MUST 保留已编辑的卡片数据

### Card List Layout

- 卡片 MUST 垂直排列，间距 12px
- 卡片宽度 MUST 填满容器（响应式）
- 超过 5 个镜头时，MUST 提供"全部折叠"按钮以减少滚动
- 侧边 SHOULD 提供缩略图时间线预览（可选增强）

## Error Prevention & Validation

### Real-time Validation

- `id` MUST 实时检查唯一性，重复时立即标红
- `prompt` 为空时，卡片 MUST 在折叠态显示警告图标
- `characters` 引用不存在的角色时（正常情况不应发生），MUST 标红提示
- `init_image` 文件不存在时，MUST 显示"文件未找到"警告

### Pre-Flight Check

进入"下一步"（启动生成）前，MUST 执行预检查：
- 至少 1 个镜头
- 所有镜头都有提示词
- 所有角色引用有效
- 项目配置完整（ComfyUI 可连接）

## Cognitive Load Control

### Progressive Disclosure

- 新卡片默认只显示 `prompt` 和 `characters` 两个字段
- `negative_prompt` 和 `continuity_note` MUST 在提示词下方，默认可见但非突出
- 高级参数（`seed`, `init_image`, `fps`, `clip_seconds`, `width/height`）MUST 折叠在"高级参数"区域
- 折叠区域 MUST 显示当前非默认值的数量："高级参数 (2 项已自定义)"

### Visual Hierarchy

- 卡片序号 MUST 醒目（大号加粗）
- 提示词 MUST 是卡片中最大字号的文本
- 参数标签 MUST 使用次要颜色
- 操作按钮 MUST 在 hover 时才显示（减少视觉噪音）

## Recommendations

1. **Shot Preview Thumbnail**: SHOULD 在卡片左侧显示 init_image 或上一个 shot 的 last_frame 缩略图
2. **Batch Edit**: SHOULD 支持多选卡片后批量修改共有参数（如统一修改 FPS）
3. **Import from YAML**: MUST 支持导入已有 `shots.yaml`，自动生成卡片
4. **Shot Templates**: SHOULD 提供 3-5 个常用 shot 模板（开场、过渡、特写、结尾）
5. **Undo Stack**: MUST 维护操作历史栈，`Ctrl+Z` 可撤销最近的添加/删除/排序操作
