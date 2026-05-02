# UX Analysis: F-004 Generation Monitor

**Feature**: 管道节点视图展示生成进度，shot 级状态上报，SSE 实时推送
**Priority**: High | **UX Concern Level**: High
**Framework Reference**: @../guidance-specification.md

## User Journey

```
确认分镜表 → 点击"开始生成"
  → 预检查（项目完整性/ComfyUI连接/磁盘空间）
  → 进入监控视图
  → 观察管道节点状态变化（排队→执行中→完成/失败）
  → 等待期间：查看单个节点详情 / 编辑后续shot / 浏览已完成结果
  → 全部完成 → 自动跳转结果预览
  → 部分失败 → 显示失败摘要 + 可操作建议
```

## Information Architecture

### Pipeline Node View (MUST)

核心视觉元素：将 Shot List 映射为水平管道节点链：

```
┌─────────────────────────────────────────────────────────────────┐
│  生成进度: 1/3 完成                                               │
│                                                                 │
│  ●━━━━━●━━━━━○━━━━━○                                           │
│  完成    完成   执行中  排队                                      │
│  #1     #2    #3     #4                                         │
│                                                                 │
│  ┌─ 镜头 #3 详情 ──────────────────────────┐                    │
│  │ 状态: 正在生成 (已用时 2:30)              │                    │
│  │ 提示词: hero walks toward a doorway...    │                    │
│  │ 角色: hero                               │                    │
│  │ [查看日志] [取消此镜头]                     │                    │
│  └──────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Node Status Visual Specification

| Status | Color | Shape | Animation | Label |
|--------|-------|-------|-----------|-------|
| queued | Gray (#9CA3AF) | Filled circle | None | "排队中" |
| running | Blue (#3B82F6) | Filled circle | Pulse glow (2s cycle) | "生成中" |
| completed | Green (#10B981) | Filled circle + checkmark | None | "已完成" |
| failed | Red (#EF4444) | Filled circle + X mark | None | "失败" |

**Accessibility**: 颜色 MUST NOT 是唯一区分手段，每个节点 MUST 同时显示文字标签和图标。

### Frame Relay Visualization

Frame Relay 是 AI-VIDEO 的核心概念，MUST 在管道视图中可视化：
- 已完成的节点 MUST 在右侧边缘显示 `→` 箭头，指示 last_frame 传递方向
- 箭头 MUST 标注"帧接力"文字
- 当下一个 shot 正在执行时，MUST 在箭头旁显示"传递上一帧..."提示

## Interaction Design

### Node Click → Detail Panel

- 点击任意节点 MUST 展开详情面板（在管道下方或右侧抽屉）
- 详情面板 MUST 显示：
  - 状态 + 已用时间
  - 提示词摘要
  - 角色信息
  - 错误信息（如果失败）
  - 操作按钮

### Operation Buttons per Status

| Node Status | Available Actions |
|-------------|-------------------|
| queued | 取消排队 |
| running | 取消生成 |
| completed | 预览结果 / 重新生成 |
| failed | 查看错误 / 重试 / 跳过 / 调整参数后重试 |

### Global Controls

- **暂停/继续**: MUST 提供，暂停后排队 shot 不自动开始
- **取消全部**: MUST 提供且需二次确认
- **整体进度**: 顶部 MUST 显示 "已完成 X/Y 个镜头" + 预估剩余时间

### Real-time Update Behavior

- SSE 事件到达时，节点颜色 MUST 平滑过渡（300ms animation）
- 新状态 MUST 触发短暂的 highlight 动画（scale 1.05 → 1.0），吸引用户注意
- 完成节点 MUST 显示 1s 的成功动画（checkmark 划入）
- 失败节点 MUST 显示 1s 的错误动画（shake + 红色闪烁）

## Waiting Experience Design

### Core Challenge

单个 shot 生成可能 2-30 分钟，3-shot 视频总时长可能 1-1.5 小时。等待体验是此功能最大的 UX 挑战。

### Strategies

1. **Progress Transparency**: 即使没有细粒度进度，MUST 显示已用时间和预估剩余
2. **Partial Results**: 已完成的 shot MUST 立即可预览（无需等待全部完成）
3. **Background Operation**: 生成 MUST 不阻塞 UI，用户可继续编辑未执行的 shot 或浏览历史
4. **Notification on Completion**: MUST 提供浏览器通知（Notification API），允许用户切换到其他工作
5. **Estimated Time**: 基于 `job_timeout_seconds` 和历史平均时间，SHOULD 提供粗略预估

### Time Display

| Elapsed Time | Display Format |
|-------------|----------------|
| < 60s | "已用时 X 秒" |
| 1-60 min | "已用时 X:XX" |
| > 60 min | "已用时 X 小时 X 分" |

### Timeout Handling

当 shot 执行时间接近 `job_timeout_seconds`（默认 1800s）时：
- 剩余 5 分钟时，MUST 显示黄色警告："镜头 #X 已接近超时限制"
- 超时后，MUST 标记为失败并显示："生成超时，可以增加超时时间或简化参数后重试"
- MUST 提供快捷操作："延长超时 (+10分钟) 并重试"

## Error Handling

### Shot Failure UX

- 失败节点 MUST 在管道中突出显示
- 点击失败节点 MUST 显示错误详情和可操作建议
- 错误信息 MUST 将技术原因翻译为用户可理解的建议：
  - `JOB_TIMEOUT` → "生成时间过长，建议减少片段时长或降低分辨率"
  - `JOB_FAILED` → "生成过程中出错，建议检查提示词或尝试不同随机种子"
  - `COMFY_UNREACHABLE` → "无法连接到生成服务，请检查 ComfyUI 是否正在运行"

### Partial Failure Recovery

当部分 shot 失败时：
- MUST 清晰区分已完成和失败的 shot
- MUST 提供"重试失败项"按钮（仅重跑失败的 shot）
- MUST 提供"跳过失败项继续"选项（跳过失败 shot，生成不完整视频）
- MUST 提供"全部重新生成"选项

## SSE Connection Resilience

- SSE 连接断开时 MUST 显示连接状态指示器（红色脉冲点 + "连接中断，正在重连..."）
- 重连成功后 MUST 自动同步缺失的状态更新
- 如果重连失败超过 3 次，MUST 提示用户手动刷新
- 前端 MUST 实现指数退避重连策略（1s → 2s → 4s → 8s → 16s → 30s max）

## Recommendations

1. **Sound Notification**: SHOULD 在全部完成时播放提示音（可配置开关）
2. **Mini Progress Bar**: SHOULD 在页面标题或浏览器 tab 中显示微型进度
3. **Log Viewer**: SHOULD 为每个 shot 提供可展开的日志面板，高级用户可查看 ComfyUI 输出
4. **Queue Management**: SHOULD 允许在运行中调整后续 shot 的排队顺序
5. **Snapshot Comparison**: MAY 在 shot 完成后立即显示生成的 last_frame 缩略图
