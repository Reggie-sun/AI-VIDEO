# F-005: Result Gallery - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: Medium | **Related Roles**: ui-designer, ux-expert

## 1. Architecture Overview

Result Gallery 负责视频和帧的预览、浏览与下载。架构核心挑战在于：本地大文件的高效传输、多产物类型（clip/last_frame/final）的统一索引，以及与现有 Run 目录结构的一致映射。

## 2. File Serving Architecture

### 2.1 Static File Strategy

现有 Run 目录结构：

```
runs/
  run-20260502-143000-abcd1234/
    manifest.json
    shots/
      shot_01/
        clip.mp4
        last_frame.png
        attempt_1/
          workflow.json
      shot_02/
        clip.mp4
        last_frame.png
    normalized/
      shot_01.mp4
      shot_02.mp4
    final/
      final.mp4
```

**约束**：
- API Server MUST 通过 `StaticFiles` 中间件提供 `runs/` 目录的只读访问
- MUST 限制访问范围到 `output.root` 目录，MUST NOT 允许路径遍历攻击
- MUST 设置合理的 `Content-Type`（mp4 -> video/mp4, png -> image/png）

### 2.2 Gallery API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs/{run_id}/gallery` | 获取 Run 的所有产物索引 |
| GET | `/api/runs/{run_id}/gallery/{shot_id}/{kind}` | 获取特定 shot 的特定产物 |

**Gallery 索引响应**：

```json
{
  "run_id": "run-...",
  "final_output": {
    "video": "/api/gallery/runs/run-.../final/final.mp4",
    "duration_s": 8.0
  },
  "shots": [
    {
      "shot_id": "shot_01",
      "clip": "/api/gallery/runs/run-.../shots/shot_01/clip.mp4",
      "last_frame": "/api/gallery/runs/run-.../shots/shot_01/last_frame.png",
      "normalized_clip": "/api/gallery/runs/run-.../normalized/shot_01.mp4",
      "duration_s": 2.0
    }
  ]
}
```

**kind** 参数值: `clip` | `last_frame` | `normalized_clip`

## 3. Large File Handling

### 3.1 Video Streaming

- API MUST 支持 HTTP Range Requests，使浏览器可进行视频 seek
- FastAPI 的 `FileResponse` 默认支持 Range Requests
- MUST 设置 `Accept-Ranges: bytes` header
- 对于大于 100MB 的文件 SHOULD 使用流式响应而非全量加载

### 3.2 Thumbnail Strategy

MVP 的缩略图策略 MUST 最小化实现复杂度：

- **视频缩略图**: MUST 使用 `last_frame.png` 作为视频卡片缩略图（已有产物）
- **无需额外生成**: MUST NOT 在 Run 完成后额外生成缩略图
- **后续迭代**: MAY 使用 ffmpeg 抽取第 1 帧作为备选缩略图（当 last_frame 不存在时）

### 3.3 Download Support

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs/{run_id}/gallery/{shot_id}/{kind}/download` | 下载单个产物 |
| GET | `/api/runs/{run_id}/gallery/download-all` | 打包下载全部产物 |

**约束**：
- 单个下载 MUST 设置 `Content-Disposition: attachment` header
- 打包下载 MVP MAY 返回 501 Not Implemented（后续用 zip 流式压缩）
- 下载 MUST 进行路径校验，MUST NOT 允许 `../` 路径遍历

## 4. Security Considerations

### 4.1 Path Traversal Prevention

- Gallery API MUST 验证所有路径参数
- MUST 确保解析后的绝对路径在 `output.root` 下
- MUST 使用 `Path.resolve()` + `startswith()` 检查
- MUST NOT 依赖前端路径校验

### 4.2 File Size Limits

- 视频文件大小 SHOULD 无硬限制（本地场景）
- MUST 设置响应超时（默认 300s）以处理大文件慢速传输
- SHOULD 在 Gallery 索引中包含文件大小信息，便于前端展示

## 5. Cross-Run Comparison

Gallery SHOULD 支持跨 Run 对比（同一 shot 在不同 Run 中的结果）：

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/gallery/compare` | 跨 Run 对比 |

Request: `?project={name}&shot_id={id}&runs=run1,run2,run3`

Response:
```json
{
  "shot_id": "shot_01",
  "runs": [
    {"run_id": "run-1", "clip": "...", "last_frame": "...", "status": "succeeded"},
    {"run_id": "run-2", "clip": "...", "last_frame": "...", "status": "succeeded"}
  ]
}
```

- 此功能 MAY 在 MVP 中推迟实现
- 对比视图 MUST 保留原始视频分辨率，MUST NOT 强制统一分辨率

## 6. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| 大文件传输阻塞事件循环 | Medium | FastAPI 异步 FileResponse（默认支持） |
| 路径遍历攻击 | High | resolve() + startswith() 校验 |
| 大量 Run 目录扫描性能 | Low | 限制列表分页 + 缓存 |
| 首次加载无缩略图 | Low | 使用 last_frame.png 作为替代 |
