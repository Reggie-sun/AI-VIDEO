# Feature Spec: F-004 - generation-monitor

**Priority**: High
**Contributing Roles**: system-architect, ux-expert, ui-designer
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- 监控视图 MUST 以管道节点视图展示 Shot 级生成进度，节点颜色表示状态（排队/执行中/完成/失败）
- MVP MUST 仅上报 shot 级状态（D-016），MAY 在后续迭代中上报 ComfyUI 节点级进度
- SSE 事件 MUST 实时推送 shot 状态变更，前端 MUST 平滑过渡节点状态
- 监控视图 MUST 提供"取消全部"操作（需二次确认），MUST 在当前 Shot 完成后软取消
- 监控视图 MUST 支持部分失败恢复：重试失败项 / 跳过失败项继续 / 全部重新生成
- 监控视图 MUST 支持超时处理：接近 `job_timeout_seconds` 时显示警告，超时后标记失败
- SSE 连接 MUST 支持断线重连（指数退避 1s→30s），重连后 MUST 同步缺失状态
- 监控视图 MUST 在全部完成后自动跳转到结果画廊（F-005）

### 用户体验需求

- 节点状态颜色 MUST NOT 作为唯一区分手段，每个节点 MUST 同时显示文字标签和图标（EP-003）
- SSE 状态变更 MUST 平滑过渡（300ms 动画），新状态 MUST 触发短暂 highlight
- 完成/失败节点 MUST 分别显示成功动画（checkmark 划入）和错误动画（shake + 红色闪烁）
- Frame Relay MUST 在管道中可视化：已完成节点右侧显示箭头，标注"帧接力"传递方向
- 等待体验 MUST 提供已用时间显示、已完成 Shot 的即时预览、浏览器通知（Notification API）
- 时间显示格式 MUST 统一：< 60s 显示秒，1-60min 显示 X:XX，> 60min 显示 X小时X分
- SSE 连接状态 MUST 持久可见（connected=绿/reconnecting=黄脉冲/disconnected=红）
- 全部完成后主 CTA MUST 变为"查看结果"，跳转到 F-005
- 桌面端最小视口 1280px（EP-007），管道节点水平排列可横向滚动

### 技术需求

- SSE Manager MUST 为每个 run_id 维护独立订阅者集合，MUST 使用 asyncio.Queue 缓冲事件（容量 100）
- SSE Manager MUST 15s 心跳保活（与 F-001 API 契约一致），Run 完成后保持连接 60s 再关闭
- 线程-事件循环桥接 MUST 通过 `asyncio.run_coroutine_threadsafe()` 实现
- 取消机制 MUST 使用软取消（`_cancelled = True` 标志位），当前 Shot MUST 完成后再停止
- 进度估算 MVP SHOULD 使用时间估算策略（已用时间/预估总时间），MUST 标注为"estimated"
- 前端 SSE 客户端 MUST 在断线后发送 `Last-Event-ID` header

## 2. Design Decisions

### Decision 1: MVP Shot 级状态 vs 节点级进度 (D-016)

- **Context**: conflict_map 标记 F-004 存在进度粒度冲突
- **Options Considered**:
  - (A) ComfyUI 节点级进度 — 精确但需接入 ComfyUI WebSocket，MVP 复杂度高
  - (B) Shot 级状态（排队/执行中/完成/失败）— 粗粒度但实现简单
  - (C) Shot 级状态 + 时间估算 — 粗粒度状态 + 估算进度补充
- **Chosen Approach**: 方案 C。MVP 仅上报 shot 级状态，节点级进度作为后续迭代。MVP SHOULD 使用时间估算策略提供粗略进度，MUST 标注为"estimated"避免误导
- **Trade-offs**: 优势：MVP 快速上线，后续可渐进增强；劣势：进度信息不精确，用户可能误解
- **Source**: guidance-specification.md D-016, conflict_map F-004 (RESOLVED: MVP shot-level only)

### Decision 2: 管道节点视图水平布局

- **Context**: 需要可视化 Shot 的执行序列和状态
- **Options Considered**:
  - (A) 垂直列表 + 状态标签 — 简单但缺乏"管道"概念
  - (B) 水平节点链 + 连接线 — 直观表达"管道"和"帧接力"
  - (C) 甘特图 — 过于技术化，非技术用户不理解
- **Chosen Approach**: 方案 B。Shot 映射为水平管道中的节点卡片（140px x 100px），节点间用带箭头的连接线串联。节点卡片显示状态颜色、图标、序号、时间。点击节点展开详情面板（在管道下方）
- **Trade-offs**: 优势：视觉直观，Frame Relay 方向明确；劣势：Shot 数量多时需横向滚动
- **Source**: ux-expert (Pipeline Node View), ui-designer (Node View Layout)

### Decision 3: 节点详情面板 — 下方展开 vs 右侧抽屉

- **Context**: 点击节点需展示详情，需选择面板位置
- **Options Considered**:
  - (A) 右侧抽屉 — 不遮挡管道视图，但挤占水平空间
  - (B) 管道下方展开 — 不挤占管道宽度，但可能需滚动
  - (C) 弹出 Modal — 遮挡管道视图，上下文丢失
- **Chosen Approach**: 方案 B。详情面板 MUST 在管道下方展开（300ms slide-down 动画），MUST NOT 阻挡管道视图。点击另一个节点 MUST 替换面板内容
- **Trade-offs**: 优势：管道始终可见，上下文不丢失；劣势：长详情面板需滚动
- **Source**: ux-expert (Node Click → Detail Panel), ui-designer (Detail Panel)

### Decision 4: 等待体验设计

- **Context**: 单个 Shot 生成可能 2-30 分钟，总时长 1-1.5 小时，等待是最大 UX 挑战
- **Options Considered**:
  - (A) 阻塞式等待 — 用户只能盯着进度
  - (B) 非阻塞 + 部分结果 + 通知 — 用户可继续其他工作
- **Chosen Approach**: 方案 B。生成 MUST 不阻塞 UI，用户可继续编辑未执行的 shot 或浏览历史。已完成 shot MUST 立即可预览。全部完成时 MUST 提供浏览器通知（Notification API）。MUST 显示已用时间和预估剩余
- **Trade-offs**: 优势：用户不浪费时间等待；劣势：后台操作需更多状态管理
- **Source**: ux-expert (Waiting Experience Design), ui-designer (Real-Time Status Updates)

### Decision 5: 部分失败恢复策略

- **Context**: 部分 shot 失败时，用户需选择如何处理
- **Options Considered**:
  - (A) 全部失败 — 一个失败即全部中止
  - (B) 继续执行剩余 — 自动跳过失败，生成不完整视频
  - (C) 用户选择 — 提供重试/跳过/取消三个选项
- **Chosen Approach**: 方案 C。Shot 失败后管道暂停（剩余 shot 保持排队），详情面板 MUST 展示三个选项：重试失败项、跳过失败项继续、取消全部。每个选项 MUST 有清晰说明
- **Trade-offs**: 优势：用户有控制权，避免数据丢失；劣势：需处理多种恢复路径
- **Source**: ux-expert (Partial Failure Recovery), ui-designer (Error State Design)

### Decision 6: SSE 连接韧性 (EP-006)

- **Context**: SSE 连接可能断开，需确保用户不丢失进度信息
- **Options Considered**:
  - (A) 断线即报错 — 过于激进，短暂断线可恢复
  - (B) 自动重连 + 状态同步 — 对用户透明
  - (C) 自动重连 + 持久指示器 — 可见但非阻塞
- **Chosen Approach**: 方案 C。SSE 断线 MUST 自动重连（指数退避 1s→2s→4s→8s→16s→30s），MUST 在 header 显示连接状态指示器。重连后 MUST 自动同步缺失状态。重连失败超 3 次 MUST 提示手动刷新
- **Trade-offs**: 优势：用户始终知道连接状态，短暂断线不影响体验；劣势：指示器增加视觉元素
- **Source**: EP-006, ux-expert (SSE Connection Resilience), ui-designer (SSE Connection State)

## 3. Interface Contract

### SSE 事件类型

| Event Type | Data Schema | 触发时机 |
|------------|-------------|---------|
| `run:started` | `{run_id, shot_count, project_name}` | Run 进入 running |
| `shot:started` | `{run_id, shot_id, index, total, attempt}` | Shot 开始 |
| `shot:progress` | `{run_id, shot_id, percentage}` | Shot 执行中（MVP 估算） |
| `shot:completed` | `{run_id, shot_id, clip_path, last_frame_path, duration_s}` | Shot 成功 |
| `shot:failed` | `{run_id, shot_id, error_code, message, retryable, next_attempt}` | Shot 失败 |
| `run:stitching` | `{run_id, current_shot, total_shots}` | 开始拼接 |
| `run:completed` | `{run_id, final_output, total_duration_s}` | Run 成功 |
| `run:failed` | `{run_id, error_code, message}` | Run 失败 |
| `run:cancelled` | `{run_id}` | Run 被取消 |

### 管道状态 API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs/{run_id}/pipeline-state` | 获取当前管道状态快照 |

### 节点状态视觉映射

| Status | 颜色 | 图标 | 动画 |
|--------|------|------|------|
| queued | Gray (#9CA3AF) | Clock | None |
| running | Blue (#3B82F6) | Loader2 (spin) | 脉冲 (2s) |
| completed | Green (#10B981) | CheckCircle2 | Checkmark 划入 (1s) |
| failed | Red (#EF4444) | XCircle | Shake (200ms) |

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| SSE 连接泄漏导致内存增长 | Medium | 心跳超时 + 最大连接数限制（10） |
| 线程-事件循环桥接死锁 | High | `run_coroutine_threadsafe` + 非阻塞 queue |
| 断线重连丢失事件 | Medium | 事件缓冲（200 条）+ Last-Event-ID 重放 |
| 进度估算不准确 | Low | 明确标注"estimated"，后续接入 ComfyUI WS |
| 长时间无事件导致代理超时 | Medium | 15s 心跳保活（与 F-001 一致） |
| Shot 数量超出视口宽度 | Medium | 水平滚动 + 缩略模式 |

## 5. Acceptance Criteria

1. 管道节点视图 MUST 水平排列所有 shot，节点间 MUST 显示方向箭头
2. SSE 事件到达时，节点颜色 MUST 在 300ms 内平滑过渡
3. Shot 完成时 MUST 显示 1s 成功动画，失败时 MUST 显示 shake + 红色闪烁
4. 节点颜色 MUST NOT 作为唯一状态区分手段，MUST 同时显示文字标签和图标
5. 点击节点 MUST 在管道下方展开详情面板（300ms 动画）
6. "取消全部" MUST 需二次确认，取消后当前 Shot MUST 完成再停止
7. 部分失败时 MUST 提供三个选项：重试/跳过/取消
8. SSE 断线 MUST 自动重连（指数退避），MUST 在 header 显示连接状态
9. 全部完成 MUST 自动跳转到结果画廊（2s 延迟）
10. 已用时间 MUST 每秒更新，格式符合 < 60s / 1-60min / > 60min 规则
11. 超时前 5 分钟 MUST 显示黄色警告
12. 浏览器通知 MUST 在全部完成时触发（需用户授权）

## 6. Detailed Analysis References

- @../system-architect/analysis-F-004-generation-monitor.md — SSE 架构、连接管理器、事件桥接、状态机、取消流程、重连策略
- @../ux-expert/analysis-F-004-generation-monitor.md — 用户旅程、管道视图、等待体验、错误处理、SSE 连接韧性
- @../ui-designer/analysis-F-004-generation-monitor.md — 节点视图布局、实时状态更新、详情面板、控制栏、完成状态
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: F-001 (Run API + SSE 流), F-003 (Shot List 定义管道节点)
- **Required by**: F-005 (完成后跳转画廊), F-007 (重跑入口)
- **Shared patterns**:
  - SSE Manager — F-004 和 F-007 的 re-run 共用
  - `<StatusBadge>` 组件 — F-003, F-004, F-006, F-007 共用
  - `<FrameThumbnail>` 组件 — 完成节点的 clip 缩略图预览
  - EP-006 加载/SSE 状态模式 — 全局 SSE 连接指示器
- **Integration points**:
  - F-001: `POST /api/runs` 启动 + `GET /api/runs/{run_id}/events` SSE 流
  - F-005: 全部完成后"查看结果"跳转画廊
  - F-007: 失败 shot "调整参数后重试" 跳转参数调优
