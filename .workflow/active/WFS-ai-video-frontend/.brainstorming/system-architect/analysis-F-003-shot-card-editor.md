# F-003: Shot Card Editor - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: High | **Related Roles**: ux-expert, ui-designer

## 1. Architecture Overview

Shot Card Editor 是向导"编辑分镜"步骤内的核心组件。架构挑战在于：有序 Shot 列表的拖拽排序持久化、参数编辑的实时校验、以及与现有 `ShotSpec` Pydantic 模型的一致性保证。

## 2. Data Model

### 2.1 ShotSpec (Existing, API Layer)

```
ShotSpec
  +-- id: str                   [REQUIRED, unique within project]
  +-- prompt: str               [REQUIRED, positive prompt text]
  +-- negative_prompt: str      [DEFAULT: ""]
  +-- characters: list[str]     [DEFAULT: [], must reference CharacterProfile.id]
  +-- seed: int|None            [DEFAULT: None -> use defaults.seed]
  +-- clip_seconds: int|None    [DEFAULT: None -> use defaults.clip_seconds]
  +-- fps: int|None             [DEFAULT: None -> use defaults.fps]
  +-- width: int|None           [DEFAULT: None -> use defaults.width]
  +-- height: int|None          [DEFAULT: None -> use defaults.height]
  +-- init_image: Path|None     [DEFAULT: None]
  +-- continuity_note: str      [DEFAULT: ""]
  +-- metadata: dict[str, Any]  [DEFAULT: {}]
```

**关键约束**：
- `id` MUST 在 Shot List 内唯一
- `characters` 列表中的每个值 MUST 引用项目中存在的 `CharacterProfile.id`
- `seed` 为 None 时表示使用 `defaults.seed` + `seed_policy` 派生
- `clip_seconds`、`fps`、`width`、`height` 为 None 时回退到 `ProjectConfig.defaults`

### 2.2 Effective Shot Config (Computed)

前端展示时 MUST 计算有效配置（合并 defaults）：

```
EffectiveShotConfig
  +-- id: str
  +-- effective_seed: int       [shot.seed ?? defaults.seed]
  +-- effective_clip_seconds: int [shot.clip_seconds ?? defaults.clip_seconds]
  +-- effective_fps: int        [shot.fps ?? defaults.fps]
  +-- effective_width: int      [shot.width ?? defaults.width]
  +-- effective_height: int     [shot.height ?? defaults.height]
  +-- overrides: list[str]      ["seed", "fps"] -- 标记哪些字段覆盖了 defaults
```

- API 响应 MUST 包含 `overrides` 标记，前端用此高亮显示非默认值
- 计算 MUST 在 API 层完成，MUST NOT 要求前端自行合并

## 3. Reorder Architecture

### 3.1 Reorder API

| Method | Path | Description |
|--------|------|-------------|
| PATCH | `/api/projects/{name}/shots/reorder` | 重排 shot 顺序 |

Request:
```json
{ "ordered_ids": ["shot_03", "shot_01", "shot_02"] }
```

**约束**：
- `ordered_ids` MUST 包含项目中所有 shot 的 id，MUST NOT 缺失或重复
- API MUST 验证 id 完整性，不合法时返回 400
- API MUST 将新顺序写回 `shots.yaml`
- 写入后 MUST 通过 `load_shots()` 回读验证

### 3.2 Reorder + Frame Relay Impact

Shot 顺序变更直接影响 Frame Relay 机制（前一 shot 的 last_frame 传递给下一 shot）。架构 MUST 处理以下场景：

- Reorder 本身 MUST NOT 触发重新生成（仅修改顺序定义）
- 下次 Run 时 PipelineRunner 自动按新顺序执行 Frame Relay
- 已有 Run 中的顺序 MUST NOT 被修改（manifest 是不可变历史记录）
- API SHOULD 在 reorder 后返回 warning，提示用户下次 Run 时 Frame Relay 链将改变

## 4. Inline Validation

### 4.1 Per-Field Validation Rules

| Field | Rule | Validation Method |
|-------|------|-------------------|
| id | non-empty, unique, alphanumeric + underscore | Pydantic `ShotSpec` model |
| prompt | non-empty | Pydantic `ShotSpec` model |
| characters | each must exist in project | `load_shots()` cross-ref check |
| seed | null or positive int | Pydantic `ShotSpec` model |
| clip_seconds | null or 1-60 | API layer range check |
| fps | null or 1-120 | API layer range check |
| width, height | null or 64-4096 (multiple of 8) | API layer range check |
| init_image | null or existing file path | API layer path check |

### 4.2 Batch Validation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{name}/shots/validate` | 校验完整 shot list |

Response:
```json
{
  "valid": false,
  "errors": [
    {"shot_id": "shot_02", "field": "characters", "message": "Unknown character: char_99"}
  ],
  "warnings": [
    {"shot_id": "shot_03", "field": "clip_seconds", "message": "Value 60 may cause long generation time"}
  ]
}
```

## 5. Prompt Engineering Support

Shot Card Editor MUST 支持提示词编辑的增强功能：

### 5.1 Character Tag Injection

- 当用户选择角色时，SHOULD 自动在 prompt 末尾追加角色相关的 style token
- 自动注入 MUST 可关闭（用户可选择手动编写完整 prompt）
- API SHOULD 提供 `POST /api/projects/{name}/shots/{shot_id}/resolve-prompt` 端点，返回解析后的完整 prompt（含角色 style_prompt 合并）

### 5.2 Continuity Note

- `continuity_note` 字段 MUST 在卡片展开时可见
- MUST 在前后 shot 卡片之间显示连线，标注 Frame Relay 关系
- API SHOULD 提供 `GET /api/projects/{name}/shots/{shot_id}/chain-context` 端点，返回前序 shot 的 last_frame 预览路径 + continuity_note

## 6. CRUD Operations Pattern

### 6.1 Optimistic Updates

前端 SHOULD 使用乐观更新策略提升编辑体验：

- 拖拽排序: 立即更新本地顺序，异步 PATCH 到服务端
- 参数编辑: debounce 500ms 后 PUT 到服务端
- 冲突处理: 服务端返回 400/409 时 MUST 回滚本地状态并显示错误

### 6.2 Auto-Save

- 向导步骤内的编辑 MUST 自动保存
- Auto-save MUST 在 debounce 1s 后触发
- MUST 在页面顶部显示保存状态指示器 (saving... / saved / error)

## 7. Risks

| Risk | Mitigation |
|------|------------|
| Reorder 后 Frame Relay 链断裂 | 显示警告，不阻止操作，Run 时自然生效 |
| 并发编辑冲突（两个浏览器标签） | MVP 不处理（单用户本地场景） |
| 大量 shot (50+) 性能 | 前端虚拟滚动 + API 分页（后续迭代） |
| Prompt 编辑丢失 | Auto-save + 服务端校验双重保障 |
