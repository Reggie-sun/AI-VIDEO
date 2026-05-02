# F-007: Param Tuner - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: Medium | **Related Roles**: system-architect, ux-expert

## 1. Architecture Overview

Param Tuner 是面向高级用户的参数调优面板，核心架构挑战在于：实时验证用户修改的参数合法性、预览 Workflow JSON 渲染结果、以及一键重跑（re-run）的编排机制。Param Tuner MUST 复用现有 `workflow_renderer.py` 模块进行预渲染验证。

## 2. Data Flow

```
[User edits param] ---> [API: validate] ---> Pydantic model validation
       |                        |
       v                        v
[API: preview workflow]  [ValidationResult]
       |
       v
workflow_renderer.render_workflow() ---> Workflow JSON preview
       |
       v
[User clicks "Re-run"]
       |
       v
[API: start run with modified params] ---> PipelineRunner (F-001)
```

## 3. API Design

### 3.1 Parameter Validation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{name}/params/validate` | 校验参数修改 |

Request:
```json
{
  "defaults": {
    "width": 768,
    "height": 768,
    "fps": 24,
    "clip_seconds": 3,
    "seed": 42,
    "negative_prompt": "blurry, low quality",
    "max_attempts": 3
  },
  "shot_overrides": {
    "shot_01": {"seed": 99, "clip_seconds": 4},
    "shot_02": {"width": 1024}
  }
}
```

Response:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {"field": "defaults.width", "message": "Resolution 768x768 may increase generation time by 2x"},
    {"field": "shot_overrides.shot_02.width", "message": "Width 1024 is not a multiple of 8, may be adjusted by ComfyUI"}
  ],
  "estimated_vram_mb": 6144
}
```

**校验规则**：
- MUST 使用 `DefaultsConfig.model_validate()` 校验 defaults
- MUST 使用 `ShotSpec.model_validate()` 校验每个 shot_override
- SHOULD 估算显存需求（基于分辨率和模型类型的经验值）
- MUST NOT 实际修改项目文件（仅预校验）

### 3.2 Workflow Preview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{name}/shots/{shot_id}/workflow-preview` | 预览渲染后的 Workflow JSON |

Request:
```json
{
  "param_overrides": {
    "seed": 99,
    "clip_seconds": 4,
    "width": 768
  }
}
```

Response:
```json
{
  "workflow": {
    "3": {"class_type": "KSampler", "inputs": {"seed": 99, ...}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, ...}},
    ...
  },
  "resolved_params": {
    "seed": 99,
    "width": 768,
    "height": 512,
    "fps": 16
  },
  "binding_applied": true
}
```

**约束**：
- MUST 调用 `render_workflow()` 进行真实渲染（dry-run 模式）
- MUST NOT 提交到 ComfyUI（仅预览）
- MUST 包含 resolved_params（合并 defaults + overrides 后的最终值）
- MUST 在渲染失败时返回具体错误（如 JSONPath 绑定失败）

### 3.3 Re-run with Modified Params

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/runs/re-run` | 基于历史 Run 修改参数后重跑 |

Request:
```json
{
  "base_run_id": "run-20260502-143000-abcd1234",
  "param_overrides": {
    "defaults": {"seed": 99},
    "shots": {
      "shot_02": {"prompt": "a new prompt", "clip_seconds": 4}
    }
  }
}
```

**Re-run 约束**：
- MUST 创建新的 Run（新 run_id），MUST NOT 修改原 Run
- MUST 基于原 Run 的项目配置应用 overrides
- MUST 写入修改后的临时 `project.yaml` 和 `shots.yaml` 到新 Run 目录
- MUST 通过 `run_in_executor` 执行 PipelineRunner（与 F-001 一致）
- MUST 通过 SSE 推送进度（与 F-004 一致）
- 原始 Run 的 manifest MUST 保持不可变

## 4. Parameter Categories

### 4.1 Global Defaults (Project-level)

| Parameter | Type | Range | Impact |
|-----------|------|-------|--------|
| width | int | 64-4096 (8x) | VRAM, generation time |
| height | int | 64-4096 (8x) | VRAM, generation time |
| fps | int | 1-120 | Generation time, file size |
| clip_seconds | int | 1-60 | Generation time, file size |
| seed | int | any positive | Reproducibility |
| seed_policy | str | derived/fixed/random | Per-shot seed behavior |
| negative_prompt | str | any text | Quality control |
| style_prompt | str | any text | Style control |
| max_attempts | int | 1-10 | Error recovery |
| poll_interval_seconds | float | 0.5-30.0 | Responsiveness vs CPU |
| job_timeout_seconds | float | 60-7200 | Max wait per shot |

### 4.2 Per-Shot Overrides

| Parameter | Type | Notes |
|-----------|------|-------|
| prompt | str | Core creative input |
| negative_prompt | str | Shot-specific exclusions |
| characters | list[str] | Character references |
| seed | int|None | Override default seed |
| clip_seconds | int|None | Override default duration |
| fps | int|None | Override default fps |
| width/height | int|None | Override default resolution |
| init_image | Path|None | First frame reference |
| continuity_note | str | Context for next shot |

## 5. Workflow JSON Diff View

Param Tuner SHOULD 支持修改前后的 Workflow JSON 对比：

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{name}/shots/{shot_id}/workflow-diff` | 对比两个 Workflow JSON |

Request:
```json
{
  "baseline": {"seed": 1, "width": 512},
  "modified": {"seed": 99, "width": 768}
}
```

Response:
```json
{
  "diff": [
    {"node": "3", "field": "inputs.seed", "old": 1, "new": 99},
    {"node": "5", "field": "inputs.width", "old": 512, "new": 768}
  ],
  "affected_nodes": ["3", "5"]
}
```

- MUST 递归对比两个 Workflow JSON 的节点差异
- MUST 只返回有差异的字段
- 前端 MUST 高亮显示变更节点

## 6. One-Click Re-run (Quick Rerun)

对于参数微调场景，SHOULD 支持快速重跑单个 shot：

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/runs/{run_id}/shots/{shot_id}/re-run` | 重跑单个 shot |

**约束**：
- 单 shot 重跑 MUST 创建新的 Run（包含完整 shot list，但只重新执行指定 shot）
- 其他 shot MUST 从原 Run 复制产物（hard link 或 copy）
- 前序 shot 的 last_frame MUST 从原 Run 获取
- 此功能 MAY 在 MVP 中推迟实现（需要 PipelineRunner 支持单 shot 重跑）

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| render_workflow 阻塞事件循环 | Medium | run_in_executor 包装 |
| 参数组合导致 OOM | High | VRAM 估算 + 警告（不强制阻止） |
| Re-run 配置文件临时写入冲突 | Low | 使用独立临时目录 + UUID |
| Workflow JSON diff 对比大文件性能 | Low | 限制 diff 深度 + 前端延迟渲染 |
| 单 shot 重跑需要 PipelineRunner 改造 | Medium | MVP 推迟，或仅支持全量重跑 |
