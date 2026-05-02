# UX Analysis: F-001 API Server

**Feature**: FastAPI 后端 API 层，包装现有 CLI 模块为 REST + SSE 端点
**Priority**: High | **UX Concern Level**: Medium
**Framework Reference**: @../guidance-specification.md

## UX Impact Assessment

API Server 是前端所有交互的基础设施层，用户不直接与之交互，但其设计质量深刻影响前端体验：

- **响应延迟** → 直接影响操作反馈感知
- **错误格式** → 决定前端能否提供可操作的错误提示
- **SSE 事件粒度** → 决定进度展示的精确度
- **API 一致性** → 影响前端状态管理复杂度

## User-Facing API Contract Requirements

### Error Response Format (MUST)

当前后端 `errors.py` 定义了结构化错误（`AiVideoError` with `code`, `user_message`, `technical_detail`）。API 层 MUST 将此结构透传到 HTTP 响应：

```json
{
  "error": {
    "code": "CONFIG_INVALID",
    "message": "项目配置验证失败：ComfyUI 地址不可达",
    "detail": "Connection refused: http://127.0.0.1:8188",
    "suggestion": "请确认 ComfyUI 已启动，或修改项目设置中的生成服务地址"
  }
}
```

**UX Rules**:
- `message` MUST 是用户可读的中文描述
- `suggestion` MUST 提供可操作的下一步建议
- `detail` (原始技术信息) SHOULD 在前端"详情"折叠区展示
- 缺少 `suggestion` 时前端 MAY 显示通用建议（"请检查设置或稍后重试"）

### SSE Event Schema (MUST)

SSE 事件 MUST 遵循统一结构以支撑管道节点视图：

```
event: shot_status
data: {
  "run_id": "run_001",
  "shot_id": "shot_001",
  "status": "running",          // queued | running | completed | failed
  "progress": null,             // MVP: null; future: 0-100
  "message": "正在生成第 1/3 个镜头",
  "timestamp": "2026-05-02T10:00:00Z"
}
```

**UX Rules**:
- 每个 SSE 事件 MUST 包含 `message` 字段，前端可直接显示为状态文案
- `status` MUST 映射为视觉状态：queued=灰色, running=蓝色脉冲, completed=绿色, failed=红色
- MVP 阶段 `progress` 为 null，前端 MUST 处理为"不确定进度"模式

### REST Endpoint Consistency (SHOULD)

- CRUD 端点 MUST 遵循 RESTful 规范，前端可预测 URL 结构
- 列表端点 MUST 支持分页（`offset`/`limit`），避免大数据量加载延迟
- 文件服务端点（视频/帧图片）MUST 支持 `Range` 请求头，确保大文件可部分加载

## Loading & Performance UX

### API Latency Budget

| Operation | Target Latency | Fallback UX |
|-----------|---------------|-------------|
| 项目 CRUD | < 500ms | Inline spinner |
| Shot 列表 | < 300ms | Skeleton list |
| 启动生成 | < 1s (异步) | 立即跳转到监控页 |
| 文件上传（参考图） | < 2s / 1MB | 进度条 |
| 视频文件加载 | N/A (本地直读) | 渐进式加载 |

### Connection State Awareness

- 前端 MUST 检测 API 连接状态，断开时显示全局 banner："无法连接到服务，请确认应用正在运行"
- SSE 连接断开 MUST 自动重连（指数退避，最大 30s），重连成功后 MUST 同步缺失状态
- 网络波动期间，本地操作 MUST 继续可用（乐观更新 + 离线队列）

## Error Code to UX Mapping

基于 `errors.py` 中的 `ErrorCode` 枚举，以下映射 MUST 在前端实现：

| ErrorCode | User Message | Suggested Action |
|-----------|-------------|-----------------|
| CONFIG_INVALID | "配置有误" | 引导用户到对应配置项 |
| DISK_SPACE_LOW | "存储空间不足" | 提示清理或更换输出目录 |
| COMFY_UNREACHABLE | "生成服务无法连接" | 提示检查 ComfyUI 状态 |
| JOB_TIMEOUT | "生成超时" | 建议增加超时时间或简化参数 |
| JOB_FAILED | "生成失败" | 建议检查参数或重试 |

## Recommendations

1. **API Response Envelope**: 所有 API 响应 MUST 使用统一信封格式 `{ data, error, meta }`，前端可统一处理
2. **Request ID**: 每个 API 请求 MUST 返回 `X-Request-ID` header，便于用户反馈问题时引用
3. **Health Endpoint**: MUST 提供 `/health` 端点，前端启动时检测后端可用性
4. **SSE Heartbeat**: SSE 流 MUST 每 15s 发送 heartbeat 事件，前端据此检测连接存活
