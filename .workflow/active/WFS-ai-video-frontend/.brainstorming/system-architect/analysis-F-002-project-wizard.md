# F-002: Project Wizard - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: High | **Related Roles**: ux-expert, ui-designer

## 1. Architecture Overview

Project Wizard 向导式项目创建流程，核心架构挑战在于：将 YAML 驱动的配置模型转化为分步引导式表单，同时保持配置校验与现有 `config.py` 的完全一致性。向导 MUST NOT 引入新的配置格式，MUST 生成与 `load_project()` 兼容的 `project.yaml`。

## 2. Data Flow

```
[Wizard Step 1: Basic Info] --+
[Wizard Step 2: ComfyUI Config] --+--> ProjectConfig (Pydantic model)
[Wizard Step 3: Workflow Setup]  --+        |
[Wizard Step 4: Defaults]       --+        v
[Wizard Step 5: Characters]     --+   config.py: load_project() validation
                                     |
                              +------v------+
                              | YAML write  | --> project.yaml
                              +-------------+
```

## 3. API Design

### 3.1 Wizard Session

向导 MUST 支持草稿保存，避免用户中途丢失配置：

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/draft` | 创建草稿项目（部分字段） |
| GET | `/api/projects/draft/{draft_id}` | 获取草稿 |
| PUT | `/api/projects/draft/{draft_id}` | 更新草稿（增量） |
| POST | `/api/projects/draft/{draft_id}/finalize` | 校验并创建正式项目 |

**约束**：
- 草稿 MUST 存储为独立文件（`~/.ai-video/drafts/{draft_id}.json`），MUST NOT 混入正式项目目录
- finalize MUST 调用 `ProjectConfig.model_validate()` 进行完整校验
- finalize 成功后 MUST 删除草稿文件

### 3.2 Validation Endpoints

向导每一步 SHOULD 支持实时校验：

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/validate/comfy-url` | 校验 ComfyUI 可达性 |
| POST | `/api/validate/workflow-template` | 校验 workflow 模板文件存在且格式合法 |
| POST | `/api/validate/binding` | 校验 binding 文件存在且 JSONPath 合法 |

**约束**：
- `/validate/comfy-url` MUST 调用 `comfy.check_available()`，MUST 设置 5s 超时
- 校验端点 MUST 返回 `{valid: bool, errors: list[str], warnings: list[str]}`

## 4. Template System

### 4.1 Project Templates

向导 SHOULD 预置项目模板，降低用户起始门槛：

```
templates/
  basic-video.yaml      # 基础视频生成：单角色，默认参数
  multi-character.yaml  # 多角色：支持 IP-Adapter 角色一致性
  image-to-video.yaml   # 图生视频：首帧驱动
```

- 模板 MUST 是合法的 `project.yaml` 文件
- 模板 MUST 使用占位符标记用户必须填写的字段（如 `__PROJECT_NAME__`）
- API MUST 提供模板列表端点: `GET /api/templates`

### 4.2 Workflow Template Discovery

向导 MUST 支持 workflow 模板文件的浏览和选择：

- `GET /api/workflow-templates?dir={path}` -- 列出指定目录下的 JSON 文件
- 响应 MUST 包含: filename, path, size, modified_at
- MUST NOT 自动解析 JSON 内容（避免安全风险）

## 5. YAML Generation Strategy

### 5.1 Write Path

```
ProjectConfig (Pydantic) -> model_dump(exclude_defaults=True) -> yaml.dump() -> project.yaml
```

**约束**：
- MUST 使用 `exclude_defaults=True` 减少输出噪音
- MUST 保持 YAML 可读性（flow style for simple values, block style for nested）
- MUST 写入后通过 `load_project()` 回读验证，确保 round-trip 一致性

### 5.2 Shot List Generation

向导完成项目创建后 SHOULD 生成空的 `shots.yaml` 模板：

```yaml
shots:
  - id: "shot_01"
    prompt: ""
    characters: []
```

- MUST 包含至少一个占位 shot
- 用户后续在 F-003 (shot-card-editor) 中编辑

## 6. Character Reference Image Handling

向导第 5 步（角色设置）涉及图片上传：

- API MUST 提供 `POST /api/projects/{name}/characters/{char_id}/reference-image` 端点
- 上传 MUST 存储到项目目录的 `characters/` 子目录
- MUST 支持多图上传（`reference_images` 是 list）
- MUST 限制文件大小（建议 20MB per image）
- MUST 限制文件类型（jpg, png, webp）
- 上传后 MUST 调用 `comfy.prepare_image()` 验证 ComfyUI 可接受

## 7. Risks

| Risk | Mitigation |
|------|------------|
| YAML round-trip 丢失注释 | MVP 接受（前端生成的新 YAML 无需保留注释） |
| ComfyURL 校验耗时阻塞向导 | 异步校验 + 前端 debounce |
| 大量参考图片上传阻塞 | 分片上传或限制数量 |
| 模板文件路径不合法 | 服务端路径校验 + 沙箱限制 |
