# UX Analysis: F-006 Run History

**Feature**: 历史 runs 浏览，基于 manifest.json 展示执行记录和产物
**Priority**: Medium | **UX Concern Level**: Medium
**Framework Reference**: @../guidance-specification.md

## User Journey

```
侧边栏打开"历史记录"
  → 浏览 runs 列表（按时间倒序）
  → 选择某个 run → 展开详情
  → 查看 shot 级状态和产物
  → 操作：预览结果 / 恢复参数 / 重新运行 / 删除记录
  → 对比不同 run 的结果
```

## Information Architecture

### Run List View

```
┌─────────────────────────────────────────────────────────┐
│ 历史记录                                    [筛选] [搜索] │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Run #3 — 2026-05-02 14:30          ● 3/3 完成 ✓    │ │
│ │ 项目: demo · 时长: 6s · 耗时: 8分32秒               │ │
│ │ [查看结果] [重新运行]                                 │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ Run #2 — 2026-05-01 10:15          ● 2/3 完成 △    │ │
│ │ 项目: demo · 时长: 4s · 耗时: 6分15秒               │ │
│ │ [查看结果] [重试失败项]                               │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ Run #1 — 2026-04-30 16:00          ● 1/3 完成 ✗    │ │
│ │ 项目: test · 时长: 2s · 耗时: 3分45秒               │ │
│ │ [查看结果] [查看错误]                                 │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Run Card Fields

每个 Run 卡片 MUST 展示以下信息（来自 manifest.json）：

| Field | Source | Display Priority |
|-------|--------|-----------------|
| Run 时间戳 | manifest | High - 主标题 |
| 项目名 | manifest/project | High - 副标题 |
| 完成状态 | shot 状态汇总 | High - 状态标签 |
| 总时长 | clip_seconds 汇总 | Medium |
| 执行耗时 | start/end 时间差 | Medium |
| Shot 完成数 | completed/total | Medium |
| 错误摘要 | failed shot 错误 | Low - 展开后 |

### Run Detail View

点击某个 run 后展开详情：

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    Run #3 — 2026-05-02 14:30                  │
│                                                         │
│ 项目: demo                                              │
│ 执行耗时: 8分32秒 · 生成参数: 512x512, 16fps, 2s/shot    │
│                                                         │
│ 镜头执行记录:                                            │
│ ┌─────┬──────────┬────────┬────────┬──────┐            │
│ │ #   │ 提示词    │ 状态    │ 耗时    │ 操作 │            │
│ ├─────┼──────────┼────────┼────────┼──────┤            │
│ │ 1   │ hero...  │ ✓ 完成  │ 2:45   │ 预览  │            │
│ │ 2   │ hero...  │ ✓ 完成  │ 2:52   │ 预览  │            │
│ │ 3   │ hero...  │ ✓ 完成  │ 2:55   │ 预览  │            │
│ └─────┴──────────┴────────┴────────┴──────┘            │
│                                                         │
│ [查看最终视频] [恢复此参数配置] [重新运行] [删除记录]       │
└─────────────────────────────────────────────────────────┘
```

## Interaction Design

### List Operations

| Operation | Trigger | Confirmation |
|-----------|---------|-------------|
| 查看 run | 点击 run 卡片 | 无 |
| 删除 run | 卡片右上角删除按钮 | MUST 确认 |
| 批量删除 | 多选 + 删除 | MUST 确认 |
| 筛选 | 筛选按钮（状态/项目/日期） | 无 |
| 搜索 | 搜索框（提示词/项目名） | 无 |

### Run Detail Actions

| Action | UX Flow | Effect |
|--------|---------|--------|
| 查看结果 | 跳转到结果画廊 (F-005) | 显示该 run 的产物 |
| 恢复参数 | 加载参数到向导 + 跳转到参数调优 (F-007) | 回填所有 shot 参数 |
| 重新运行 | 二次确认 → 跳转到生成监控 (F-004) | 以相同参数重新执行 |
| 删除记录 | 二次确认 → 删除 | 移除 manifest 和产物文件 |

### "Restore Parameters" Flow (SHOULD)

"恢复参数"是历史记录最有价值的功能——允许用户回到某个配置状态重新尝试：
1. 点击"恢复此参数配置"
2. 系统加载该 run 的 project.yaml 和 shots.yaml 快照
3. 跳转到分镜编辑器，所有字段预填充
4. 用户修改后可立即重新生成

**Important**: 恢复参数 MUST 创建新的项目/shot 配置副本，而不是覆盖当前配置，避免意外丢失当前工作。

## Data Display Considerations

### Manifest Parsing

基于 `manifest.py` 中的数据结构，前端 MUST 解析 manifest.json 并展示：
- 每个 shot 的状态 (queued/running/completed/failed)
- 每个 shot 的产物文件路径
- 执行时间戳
- 错误信息（如有）

### Pagination

- Run 列表 MUST 支持分页（每页 20 条），避免长列表性能问题
- 新 run 完成后 MUST 自动出现在列表顶部
- 列表 MUST 支持无限滚动作为分页替代方案

### Time Display

- 相对时间："2 小时前"、"昨天"、"3 天前"
- 超过 7 天显示绝对日期："2026-04-25"
- 详情页 MUST 显示完整时间戳

## State Management

### Empty State

无历史记录时 MUST 显示：
- "还没有运行记录"
- "创建你的第一个视频"按钮 → 跳转到项目向导

### Loading State

- 首次加载 MUST 显示骨架屏
- 后续加载（翻页/筛选）MUST 显示列表底部 spinner

### Run in Progress

- 正在执行的 run MUST 在列表中显示为"进行中"状态
- MUST 提供快捷链接跳转到生成监控页

## Recommendations

1. **Run Comparison**: SHOULD 支持选择两个 run 并排对比结果（A/B 对比参数变化的效果）
2. **Parameter Diff**: SHOULD 在"恢复参数"时显示当前配置与历史配置的差异
3. **Run Tagging**: MAY 允许用户为 run 添加标签/备注（如"降低 seed 尝试"、"新角色版本"）
4. **Disk Usage**: SHOULD 显示历史记录占用磁盘空间，支持一键清理旧记录
5. **Auto-cleanup**: MAY 提供自动清理策略（保留最近 N 个 run / 保留 N 天内的记录）
