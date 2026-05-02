# System Architect Analysis: AI-VIDEO Frontend

**Framework Reference**: @../guidance-specification.md
**Role**: system-architect
**Date**: 2026-05-02

## Architecture Vision

为 AI-VIDEO 纯本地 Python CLI 构建前端层，核心挑战在于：将同步阻塞的 PipelineRunner 适配为异步可观测的 API 服务，同时保持对现有模块的零侵入包装。架构必须支撑本地单用户场景的 MVP 快速上线，并预留远程部署和并发扩展的演进路径。

## Core Data Model

系统围绕 5 个核心实体构建，直接复用现有 Pydantic 模型：

| Entity | Source | Key Fields | Lifecycle Complexity |
|--------|--------|------------|---------------------|
| Project | `ProjectConfig` | project_name, comfy, workflow, output, defaults, characters | Simple (CRUD) |
| Shot | `ShotSpec` | id, prompt, characters, seed, clip_seconds, init_image | Medium (ordered list, drag reorder) |
| Run | `RunManifest` | run_id, status, shots[], final_output | Complex (state machine: pending -> running -> succeeded/failed) |
| ShotRecord | `ShotRecord` | shot_id, status, attempts[], clip_path, last_frame_path | Complex (retry + attempt tracking) |
| Character | `CharacterProfile` | id, name, reference_images, ipadapter | Simple (CRUD) |

Run 实体具有最复杂的状态生命周期，需要完整的状态机定义（见 @analysis-F-001-api-server.md）。

## Architecture Principles

1. **零侵入包装**: API 层 MUST 通过 `run_in_executor` 包装现有同步调用，MVP 阶段 MUST NOT 修改 pipeline.py 内部实现
2. **文件系统即数据库**: MVP MUST 以 YAML/JSON 文件为持久层，SHOULD NOT 引入独立数据库
3. **SSE 先行**: 实时通信 MUST 使用 SSE，SHOULD 预留 WebSocket 升级路径
4. **渐进式异步化**: MUST 先用 executor 包装，SHOULD 逐步将热点路径改为原生 async
5. **本地优先 + 远程兼容**: MUST 支持本地文件直读，MUST NOT 假设文件系统总是可访问

## Feature Point Index

| Feature | Priority | Architecture Concern | Document |
|---------|----------|---------------------|----------|
| F-001 api-server | High | 核心枢纽，REST/SSE 端点设计，状态机，异步编排 | @analysis-F-001-api-server.md |
| F-002 project-wizard | High | 配置校验链，YAML 生成，模板继承 | @analysis-F-002-project-wizard.md |
| F-003 shot-card-editor | High | 有序列表操作，拖拽排序持久化，提示词验证 | @analysis-F-003-shot-card-editor.md |
| F-004 generation-monitor | High | SSE 事件流设计，shot 级状态上报，断线重连 | @analysis-F-004-generation-monitor.md |
| F-005 result-gallery | Medium | 静态文件服务，大文件流式传输，缩略图策略 | @analysis-F-005-result-gallery.md |
| F-006 run-history | Medium | manifest 解析，目录扫描，产物索引 | @analysis-F-006-run-history.md |
| F-007 param-tuner | Medium | workflow JSON 预渲染，schema 校验，重跑编排 | @analysis-F-007-param-tuner.md |

## Cross-Cutting Summary

跨特性架构决策集中在以下领域，详见 @analysis-cross-cutting.md：

- **分层架构**: FastAPI Router -> Service Layer -> Existing Modules (config, pipeline, comfy_client)
- **状态管理**: Run 状态机 + Shot 级状态追踪 + SSE 事件总线
- **错误体系**: 复用现有 ErrorCode 枚举，API 层统一错误响应格式
- **可观测性**: 5+ 核心指标，结构化日志，健康检查端点
- **部署策略**: 本地单进程 -> 远程分离部署的演进路径
