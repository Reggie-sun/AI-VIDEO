# Feature Spec: F-006 - run-history

**Priority**: Medium
**Contributing Roles**: ux-expert, ui-designer
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- 历史记录 MUST 基于 `manifest.json` 文件展示历史执行记录，MUST NOT 维护独立数据库索引
- 历史列表 MUST 支持：按状态筛选（completed/partial/failed）、分页（每页 20 条）、按时间倒序
- 历史 Run MUST 支持以下操作：查看结果（跳转 F-005）、恢复参数（跳转 F-007）、重新运行、删除记录
- 历史 Run MUST 支持配置漂移检测，对比当前项目配置与 Run 时配置的 hash 差异
- 失败 Run MUST 支持从历史记录直接恢复（resume）
- 删除 Run MUST 先移除目录再移除 manifest，MUST NOT 删除正在运行的 Run
- MVP MUST 使用全量扫描 `output.root/*/manifest.json`，SHOULD 设置扫描缓存 TTL（30s）

### 用户体验需求

- Run 列表 MUST 以时间倒序排列，每个 Run 卡片 MUST 显示：时间戳、项目名、完成状态、总时长、执行耗时
- 时间戳 MUST 使用相对时间（"2 小时前"/"昨天"），超过 7 天显示绝对日期，详情页 MUST 显示完整时间戳
- Run 卡片 MUST 显示聚合状态（全部完成/部分完成/全部失败），使用 mini shot 状态点指示
- 聚合状态 MUST 通过左侧色条视觉区分：completed=绿色、partial=黄色、failed=红色
- 空状态 MUST 显示引导 CTA："还没有运行记录，创建第一个视频"
- 加载状态 MUST 使用骨架屏，翻页/筛选使用底部 spinner
- "恢复参数" MUST 创建新的项目/shot 配置副本，MUST NOT 覆盖当前配置
- "重新运行" MUST 需二次确认
- 正在执行的 Run MUST 在列表中显示为"进行中"，提供跳转到监控页的快捷链接

### 技术需求

- 目录扫描 MUST 处理损坏的 manifest.json（跳过 + 日志警告），MUST NOT 导致整体失败
- `project_name` MUST 从 `manifest.project_config_path` 中解析路径提取
- `duration_s` MUST 从 `created_at` 和最后一个 shot 的 `completed_at` 计算
- 产物路径 MUST 转换为 Gallery API 路径（相对路径 -> API URL）
- 配置漂移检测 MUST 对比 `manifest.project_config_hash` 与当前文件的 `sha256_file()` 结果
- 分页 MUST 使用 "Load More" 按钮（非无限滚动），MUST 显示总数

## 2. Design Decisions

### Decision 1: 基于 manifest.json 的无数据库方案

- **Context**: 需要选择历史记录的数据存储方式
- **Options Considered**:
  - (A) SQLite 数据库 — 查询灵活，但需维护索引和迁移
  - (B) 直接扫描 manifest.json — 无额外存储，但全量扫描有性能风险
  - (C) 扫描 + 缓存 — 无数据库但有缓存层
- **Chosen Approach**: 方案 C。MVP 全量扫描 `manifest.json`，使用 30s TTL 缓存结果。后续迭代 MAY 引入增量索引或文件系统 watch
- **Trade-offs**: 优势：零额外存储，实现简单；劣势：大量 Run 时扫描性能下降，缓存可能导致短暂数据不一致
- **Source**: system-architect (Directory Scanning Strategy)

### Decision 2: 聚合状态计算与视觉

- **Context**: Run 包含多个 shot，需在列表层面展示整体状态
- **Options Considered**:
  - (A) 仅显示 Run 级状态 — 信息不足，无法区分"部分完成"
  - (B) 聚合状态 + mini shot 状态点 — 一眼区分
- **Chosen Approach**: 方案 B。聚合逻辑：全部 completed → "3/3 Completed"；部分 completed + 部分 failed → "2/3 Partial"；全部 failed → "0/3 Failed"；有 running → "In Progress"。左侧色条 + 状态 Badge + mini shot 状态点
- **Trade-offs**: 优势：信息密度高，用户快速判断；劣势：需在 API 层计算聚合状态
- **Source**: ux-expert (Run Card Fields), ui-designer (Aggregate Status Logic)

### Decision 3: "Load More" 分页 vs 无限滚动

- **Context**: 需选择分页交互方式
- **Options Considered**:
  - (A) 无限滚动 — 浏览流畅但不可预测，非技术用户可能困惑
  - (B) "Load More" 按钮 — 可预测，用户主动控制
  - (C) 传统分页 — 过于技术化
- **Chosen Approach**: 方案 B。使用"Load More"按钮，MUST 显示总数"Showing 5 of 12 runs"。每页 20 条
- **Trade-offs**: 优势：可预测，用户不迷失位置；劣势：需额外点击
- **Source**: ux-expert (Pagination), ui-designer (Pagination)

### Decision 4: 配置漂移检测

- **Context**: 用户查看历史 Run 时需知道当前配置是否已变更
- **Options Considered**:
  - (A) 不检测 — 用户可能不知道配置已变更
  - (B) 自动检测 + 警告 — 主动告知
  - (C) 按需检测 — 用户点击时检测
- **Chosen Approach**: 方案 B。用户查看 Run 详情时 MUST 自动触发漂移检测，如有变更 MUST 在详情中显示警告。MUST 对比 project_config、workflow_template、workflow_binding 三个 hash
- **Trade-offs**: 优势：用户不会误操作过期配置；劣势：hash 计算增加 API 延迟（MUST 异步）
- **Source**: system-architect (Config Drift Detection)

### Decision 5: 恢复参数安全策略

- **Context**: "恢复参数"是有价值的功能，但可能覆盖当前工作
- **Options Considered**:
  - (A) 直接覆盖当前配置 — 危险，可能丢失当前工作
  - (B) 创建配置副本 — 安全，保留当前工作
- **Chosen Approach**: 方案 B。"恢复参数" MUST 创建新的项目/shot 配置副本，MUST NOT 覆盖当前配置。MUST 在跳转到分镜编辑器时所有字段预填充为历史值
- **Trade-offs**: 优势：安全，不丢失当前工作；劣势：可能产生冗余配置副本
- **Source**: ux-expert ("Restore Parameters" Flow), system-architect (Resume from History)

### Decision 6: Run 详情展示 — 策划内容 vs 原始数据

- **Context**: manifest.json 包含大量技术数据，需决定展示方式
- **Options Considered**:
  - (A) 直接展示完整 manifest.json — 技术用户可理解，但非技术用户无法理解
  - (B) 仅展示策划后的关键字段 — 用户友好，但技术信息需另查
  - (C) 策划展示 + 原始数据可展开 — 两全
- **Chosen Approach**: 方案 C。详情页 MUST 展示策划后的关键字段（项目信息、shot 状态表、产物链接），MUST NOT 直接展示原始 manifest.json。SHOULD 提供"查看原始数据"可展开区域
- **Trade-offs**: 优势：非技术用户可理解；劣势：需 API 层策划数据
- **Source**: ux-expert (Run Detail View), ui-designer (Run Detail View)

## 3. Interface Contract

### Run History API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs` | 列出所有 Run（支持筛选/分页） |
| GET | `/api/runs/{run_id}` | Run 详情 |
| POST | `/api/runs/{run_id}/resume` | 恢复失败 Run |
| DELETE | `/api/runs/{run_id}` | 删除 Run |
| GET | `/api/runs/{run_id}/config-drift` | 配置漂移检测 |

### Run 列表查询参数

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | running / completed / partial / failed（API 层 Run 状态使用 succeeded/failed，前端聚合状态独立映射为 completed/partial/failed，映射在前端完成）|
| `project` | string | 项目名筛选 |
| `offset` | int | 偏移量（默认 0） |
| `limit` | int | 每页条数（默认 20，最大 100） |

### 聚合状态逻辑

| Shot 状态组合 | 聚合状态 | Badge | 左侧色条 |
|--------------|---------|-------|---------|
| 全部 completed | Completed | "3/3 Completed" | `--status-completed` |
| 部分 completed + 部分 failed | Partial | "2/3 Partial" | `--status-warning` |
| 全部 failed | Failed | "0/3 Failed" | `--status-failed` |
| 有 running | Running | "In Progress" | `--status-running` |

### URL 路由

- `/history` — 历史记录列表
- `/history/{run_id}` — Run 详情

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| 大量 Run 目录全量扫描慢 | Medium | 缓存 TTL 30s + 分页 + 限制扫描深度 |
| 损坏 manifest 导致列表异常 | Medium | try/except 跳过 + 日志 + 标记为 "corrupted" |
| 项目路径提取失败 | Low | 容错：显示为 "unknown project" |
| 配置漂移检测阻塞响应 | Low | 异步检测 + 缓存结果 |
| 恢复参数产生冗余配置 | Low | 可接受的副作用，SHOULD 提供清理引导 |

## 5. Acceptance Criteria

1. Run 列表 MUST 按时间倒序排列，每页 20 条
2. 每个 Run 卡片 MUST 显示：时间戳（相对时间）、项目名、聚合状态、总时长、执行耗时
3. 聚合状态 MUST 正确计算：completed/partial/failed/running 四种
4. 状态筛选 MUST 支持 All/Completed/Partial/Failed 四个选项
5. "Load More" 按钮 MUST 显示总数"Showing X of Y runs"
6. 点击"查看结果" MUST 跳转到结果画廊（F-005），显示该 Run 的产物
7. 点击"恢复参数" MUST 创建配置副本，跳转到分镜编辑器预填充历史值
8. 点击"重新运行" MUST 需二次确认，确认后跳转到生成监控
9. 配置漂移检测 MUST 在查看详情时自动触发，有变更时 MUST 显示警告
10. 损坏的 manifest.json MUST 不导致列表崩溃，MUST 跳过并记录日志
11. 删除 Run MUST 需确认，MUST NOT 删除正在运行的 Run
12. 骨架屏 MUST 匹配 Run 卡片结构
13. 时间显示：7 天内相对时间，超过 7 天绝对日期

## 6. Detailed Analysis References

- @../system-architect/analysis-F-006-run-history.md — 数据源架构、目录扫描策略、API 设计、配置漂移检测、恢复机制
- @../ux-expert/analysis-F-006-run-history.md — 用户旅程、信息架构、交互设计、数据展示、状态管理
- @../ui-designer/analysis-F-006-run-history.md — 布局设计、Run 卡片设计、聚合状态、详情面板、筛选排序
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: F-001 (Run API + 列表/详情/删除端点), F-005 (查看结果跳转画廊)
- **Required by**: F-007 (恢复参数跳转调优面板)
- **Shared patterns**:
  - `<StatusBadge>` 组件 — F-003, F-004, F-006, F-007 共用
  - `<VideoPlayer>` 组件 — F-005, F-006 共用
  - `<EmptyState>` 组件 — 所有功能共用
  - 时间显示格式 — F-004, F-006 共用
- **Integration points**:
  - F-005: "查看结果" 跳转到画廊
  - F-007: "恢复参数" 跳转到调优面板预填充
  - F-004: "重新运行" 跳转到监控页，正在进行的 Run 提供快捷跳转
  - F-001: 配置漂移检测调用 hash 对比 API
