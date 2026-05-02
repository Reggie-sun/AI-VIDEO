# UX Analysis: F-007 Param Tuner

**Feature**: 参数调优面板，实时验证、workflow JSON 预览、一键重跑
**Priority**: Medium | **UX Concern Level**: Medium
**Framework Reference**: @../guidance-specification.md

## User Journey

```
从结果画廊/历史记录进入参数调优
  → 选择要调优的 shot（单 shot 或全部）
  → 修改参数（提示词/种子/时长/角色权重等）
  → 实时验证参数合法性
  → 可选：预览 workflow JSON 变更
  → 点击"重新生成" → 跳转到生成监控 (F-004)
  → 或：保存参数但不运行 → 返回分镜编辑器
```

## Information Architecture

### Panel Layout

参数调优面板 MUST 从侧边栏或结果画廊的操作入口进入，采用侧面板 + 主内容双栏布局：

```
┌──────────────────────────────────┬──────────────────────┐
│  主内容区: 当前结果预览            │  参数面板              │
│                                  │                      │
│  ┌────────────────────────────┐  │  镜头: #1 shot_001   │
│  │ ▶ 当前视频预览              │  │  ─────────────────   │
│  │  [====================]    │  │  提示词               │
│  └────────────────────────────┘  │  ┌────────────────┐  │
│                                  │  │ hero enters... │  │
│  上次运行结果:                    │  └────────────────┘  │
│  种子: 42 · 耗时: 2:45           │  反向提示词           │
│                                  │  ┌────────────────┐  │
│                                  │  │ blur, ...      │  │
│                                  │  └────────────────┘  │
│                                  │  种子: [42] [随机]    │
│                                  │  角色: [hero ✓]      │
│                                  │  IPAdapter 权重:      │
│                                  │  ──────[0.8]──────   │
│                                  │                      │
│                                  │  ▸ 高级参数           │
│                                  │                      │
│                                  │  [验证 ✓] [预览JSON]  │
│                                  │  [重新生成]           │
└──────────────────────────────────┴──────────────────────┘
```

### Parameter Groups

参数按逻辑分组，映射 `ShotSpec` 和 `ProjectConfig.defaults` 的字段：

**Group 1: 创意参数 (始终可见)**
- `prompt` — 提示词（Textarea）
- `negative_prompt` — 反向提示词（Textarea）
- `characters` — 角色关联（Checkbox list）
- `continuity_note` — 连续性说明（Text input）

**Group 2: 生成参数 (默认展开)**
- `seed` — 随机种子（Number input + "随机"按钮）
- `clip_seconds` — 片段时长（Slider 1-10s）
- `fps` — 帧率（Select 8/16/24）
- `width` / `height` — 分辨率（Preset select）

**Group 3: 高级参数 (默认折叠)**
- `init_image` — 初始图像（File upload）
- IPAdapter 权重（从 `CharacterProfile.ipadapter.weight` 读取）
- IPAdapter 起止点（`start_at`, `end_at`）

### Parameter Scope Selection

调优 MUST 支持选择作用范围：

| Scope | Description | When to Use |
|-------|-------------|-------------|
| 当前镜头 | 仅修改选中的 shot | 精细调优单个 shot |
| 全部镜头 | 修改所有 shot 的共有参数 | 批量调整 FPS/时长/分辨率 |
| 项目默认 | 修改项目级 defaults | 影响未来新建的 shot |

**UI Pattern**: 面板顶部 MUST 提供 scope 切换（Tab 或 Radio），默认为"当前镜头"。

## Interaction Design

### Real-time Validation (MUST)

- 参数修改后 MUST 在 300ms 内显示验证结果
- 验证 MUST 检查：
  - 必填字段非空（prompt）
  - 数值范围（seed >= 0, clip_seconds 1-10, fps > 0）
  - 角色引用有效性
  - 文件路径存在性（init_image）
- 验证状态 MUST 使用内联指示器：
  - ✓ 绿色对勾 — 合法
  - ⚠ 黄色警告 — 可用但不推荐（如极高分辨率）
  - ✗ 红色叉号 — 非法

### Seed Interaction Design

种子参数是调优中最常用的控件，MUST 优化其交互：
- 默认显示当前种子值
- "随机"按钮 MUST 生成新的随机种子并立即显示
- "锁定"按钮 MUST 固定种子，确保重新生成结果一致
- SHOULD 提供"递增"按钮（seed + 1），便于系统性探索

### IPAdapter Weight Slider

角色 IPAdapter 权重是影响角色一致性的关键参数：
- MUST 使用滑块控件，范围 0.0-1.0，步长 0.1
- MUST 显示当前数值标签
- SHOULD 在滑块旁显示效果说明："低=更多创意自由，高=更严格遵循参考图"

### Workflow JSON Preview (SHOULD)

高级用户 MAY 需要查看参数如何映射到 ComfyUI workflow：
- 点击"预览 JSON"按钮 MUST 打开 modal 显示当前 workflow JSON
- 修改参数后 MUST 实时高亮变更的节点/字段
- JSON 预览 MUST 支持折叠/展开节点
- MUST 提供"复制 JSON"按钮

**Rule**: 此功能面向高级用户，MUST NOT 干扰普通用户的调优流程。

### One-Click Rerun Flow

"重新生成"是参数调优的核心闭环：
1. 用户点击"重新生成"
2. 系统验证所有参数（MUST 拦截非法参数）
3. 显示确认摘要："将重新生成镜头 #1，参数变更：种子 42→87, 时长 2s→3s"
4. 用户确认 → 保存参数 → 跳转到生成监控页 (F-004)
5. 取消 → 回到编辑状态

**Important**:
- 重新生成 MUST 创建新 run，MUST NOT 覆盖已有结果
- 参数变更摘要 MUST 清晰列出所有修改，避免用户遗忘差异

## Cognitive Load Control

### Parameter Visibility Strategy

- 参数面板 MUST 分组显示，每组不超过 5 个字段
- 高级参数 MUST 默认折叠，标题 MUST 显示自定义项数量："高级参数 (2 项已自定义)"
- 非当前编辑的参数组 SHOULD 折叠

### Change Tracking

- 已修改的参数 MUST 视觉区分（左侧色条或背景色变化）
- 面板底部 MUST 显示变更计数："已修改 3 项参数"
- "重置为默认值"按钮 MUST 可用，逐项或全部重置

### Context-Aware Defaults

- 从结果画廊进入时，MUST 预填充该 run 的参数值
- 从历史记录恢复时，MUST 显示历史值与当前值的对比
- 新建 shot 调优时，MUST 使用项目 defaults 作为基线

## Error Prevention

### Invalid Parameter Prevention

- 数值输入 MUST 使用 `min`/`max`/`step` 约束
- 分辨率 MUST 优先提供预设选项，减少自由输入
- 角色 checkbox MUST 仅显示项目中已定义的角色
- 文件上传 MUST 限制文件类型（.png/.jpg for init_image）

### Destructive Action Safeguards

- 批量修改全部 shot 时 MUST 显示影响范围确认
- "重置为默认值" MUST 确认
- 未保存的参数变更 MUST 在离开页面时提示保存

## Recommendations

1. **Parameter Presets**: SHOULD 允许用户保存参数组合为预设（如"高质量慢动作"、"快速预览"），便于复用
2. **Before/After Comparison**: SHOULD 在重新生成后提供新旧结果并排对比
3. **Auto-suggest Seed**: SHOULD 在生成失败时自动建议不同种子值
4. **Batch Parameter Edit**: SHOULD 支持选中多个 shot 后批量修改共有参数
5. **Parameter History**: MAY 为每个 shot 维护参数变更历史，便于追踪"哪个参数影响了结果"
