# F-006: Run History - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: Medium | **Related Roles**: ux-expert

## 1. Architecture Overview

Run History 基于 `manifest.json` 文件提供历史执行记录浏览。架构挑战在于：目录扫描效率、Manifest 解析容错、以及与 F-005 (result-gallery) 的产物浏览整合。

## 2. Data Source Architecture

### 2.1 Manifest as Record Source

`RunManifest` 是 Run History 的唯一数据源：

```
runs/
  run-20260502-143000-abcd1234/
    manifest.json          <-- Run History 读取此文件
    shots/shot_01/clip.mp4 <-- 产物引用
    final/final.mp4        <-- 最终输出
  run-20260502-150000-efgh5678/
    manifest.json
    ...
```

**约束**：
- Run History MUST 通过扫描 `output.root` 下的 `manifest.json` 文件获取 Run 列表
- MUST NOT 维护独立的数据库索引
- MUST 依赖 `RunManifest.model_validate_json()` 解析，复用现有模型

### 2.2 Directory Scanning Strategy

| Strategy | MVP | Future |
|----------|-----|--------|
| 全量扫描 | YES | NO |
| 增量索引 | NO | MAY |
| 缓存 + 文件系统 watch | NO | SHOULD |

**MVP 扫描约束**：
- MUST 限制扫描深度为 1（`output.root/*/manifest.json`）
- MUST 处理损坏的 manifest.json（跳过 + 日志警告，MUST NOT 导致整体失败）
- MUST 按创建时间倒序排列
- MUST 支持分页（`?page=1&per_page=20`）
- SHOULD 设置扫描缓存 TTL（30s），避免频繁磁盘 I/O

## 3. API Design

### 3.1 Run List

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs` | 列出所有 Run |
| GET | `/api/runs/{run_id}` | 获取 Run 详情 |

**列表查询参数**：

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: running, succeeded, failed |
| `project` | string | Filter by project name (from project_config_path) |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 20, max: 100) |
| `sort` | string | Sort field: created_at (default), run_id |
| `order` | string | Sort order: desc (default), asc |

**Run Summary Response**:

```json
{
  "items": [
    {
      "run_id": "run-20260502-143000-abcd1234",
      "status": "succeeded",
      "created_at": "2026-05-02T14:30:00Z",
      "project_name": "my-project",
      "shot_count": 4,
      "completed_shots": 4,
      "final_output": "/api/gallery/runs/run-.../final/final.mp4",
      "duration_s": 180.5
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

- `project_name` MUST 从 `manifest.project_config_path` 中提取（解析路径）
- `duration_s` MUST 从 `created_at` 和最后一个 shot 的 `completed_at` 计算
- `completed_shots` MUST 统计 status == "succeeded" 的 shot 数

### 3.2 Run Detail

**Run Detail Response**:

```json
{
  "run_id": "run-...",
  "status": "succeeded",
  "created_at": "...",
  "updated_at": "...",
  "project_name": "my-project",
  "project_config_hash": "abc...",
  "shots": [
    {
      "shot_id": "shot_01",
      "status": "succeeded",
      "attempts": 1,
      "started_at": "...",
      "completed_at": "...",
      "duration_s": 45.2,
      "clip_path": "/api/gallery/...",
      "last_frame_path": "/api/gallery/...",
      "seed": 42,
      "error": null
    }
  ],
  "final_output": "/api/gallery/...",
  "config_snapshot": {
    "project_config_hash": "abc...",
    "workflow_template_hash": "def...",
    "workflow_binding_hash": "ghi..."
  }
}
```

- 产物路径 MUST 转换为 Gallery API 路径（相对路径 -> API URL）
- `config_snapshot` MUST 包含 hash 校验信息，用于判断配置是否被修改

## 4. Config Drift Detection

Run History MUST 支持配置漂移检测，告知用户当前项目配置是否与该 Run 时一致：

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs/{run_id}/config-drift` | 检测配置是否变更 |

Response:
```json
{
  "run_id": "run-...",
  "drifted": true,
  "changes": [
    {
      "file": "project_config",
      "run_hash": "abc123",
      "current_hash": "def456",
      "changed": true
    },
    {
      "file": "workflow_template",
      "run_hash": "ghi789",
      "current_hash": "ghi789",
      "changed": false
    }
  ]
}
```

- MUST 对比 `manifest.project_config_hash` 与当前文件的 `sha256_file()` 结果
- 漂移检测 MUST 在用户查看历史 Run 时自动触发
- 前端 MUST 在 Run 详情中显示配置漂移警告

## 5. Resume from History

历史失败的 Run MUST 支持从 Run History 直接恢复：

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/runs/{run_id}/resume` | 恢复失败 Run |

**约束**：
- MUST 检查 Run status == "failed"
- MUST 检查 manifest 中 `project_config_path` 和 `shot_list_path` 存在
- MUST 检查配置文件未被修改（如有漂移，SHOULD 警告但不阻止）
- Resume 逻辑 MUST 复用 `PipelineRunner.resume()`
- Resume 后 MUST 通过 SSE 推送进度（与 F-004 一致）

## 6. Cleanup & Retention

- API SHOULD 提供 `DELETE /api/runs/{run_id}` 端点用于清理旧 Run
- 删除 MUST 先移除目录再移除 manifest（原子性最佳努力）
- MUST NOT 删除正在运行的 Run
- MUST 确认用户意图（前端弹窗确认）
- 保留策略: MVP 无自动清理，SHOULD 在后续迭代中支持基于时间/数量的自动清理

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| 大量 Run 目录全量扫描慢 | Medium | 缓存 TTL + 分页 + 限制扫描深度 |
| 损坏 manifest 导致列表异常 | Medium | try/except 跳过 + 日志 + 标记为 "corrupted" |
| 项目路径提取失败 | Low | 容错：显示为 "unknown project" |
| 配置漂移检测阻塞响应 | Low | 异步检测 + 缓存结果 |
