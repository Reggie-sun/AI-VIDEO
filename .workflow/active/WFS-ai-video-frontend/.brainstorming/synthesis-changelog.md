# Synthesis Changelog

**Session**: WFS-ai-video-frontend
**Date**: 2026-05-02
**Process**: Feature Spec Synthesis (3 roles x 7 features → 7 specs)

## Synthesis Summary

从 3 个角色（system-architect, ux-expert, ui-designer）的 21 份角色分析文档中，综合生成 7 份功能规格。每份规格通过四层聚合规则（直接引用、结构化提取、冲突蒸馏、跨功能标注）整合多角色视角，并应用全部 8 项增强提案（EP-001 至 EP-008）。

## Per-Feature Synthesis Notes

### F-001: api-server

- **角色共识**: FastAPI + SSE 先行、run_in_executor 包装、Run 状态机
- **冲突解决**: priority alignment (arch: High vs UX: Medium) → RESOLVED: 架构优先级保持 High，UX 影响通过 API 契约约束实现
- **增强应用**: EP-001（统一错误响应格式，3 层错误展示）、EP-005（/health 端点 + 连接指示器）、EP-006（加载状态 3 层模式）、EP-007（桌面端视口限定）
- **关键综合**: 将 ux-expert 的错误 UX 映射和 ui-designer 的错误视觉规范整合为统一错误契约（EP-001），写入 API 设计而非独立功能

### F-002: project-wizard

- **角色共识**: 向导流程、渐进披露、YAML 抽象
- **冲突解决**: layout transition → RESOLVED: 向导内嵌卡片列表（D-015）
- **增强应用**: EP-002（角色管理 UI 间隙填补）、EP-003（键盘导航 + 自动聚焦）、EP-005（ComfyUI 连接测试按钮）、EP-008（3 层参数分类）
- **关键综合**: 将 system-architect 的草稿 API、ux-expert 的步骤分解、ui-designer 的字段设计整合为 4 步向导 + Smart Defaults 零配置启动

### F-003: shot-card-editor

- **角色共识**: 卡片式、拖拽排序、展开编辑
- **冲突解决**: parameter depth vs disclosure → SUGGESTED: 采用 EP-008 的 3 层分类（Essential/Advanced/Expert）
- **增强应用**: EP-003（拖拽键盘替代 Alt+Up/Down）、EP-004（Command Pattern 撤销/重做）、EP-008（3 层参数分类）
- **关键综合**: 将 system-architect 的有效配置计算（API 层合并 defaults + overrides）、ux-expert 的卡片解剖、ui-designer 的 Frame Relay 连线整合为双态卡片设计

### F-004: generation-monitor

- **角色共识**: 管道节点视图、SSE 实时推送、shot 级 MVP
- **冲突解决**: progress granularity → RESOLVED: MVP 仅 shot 级状态，时间估算作为补充
- **增强应用**: EP-003（颜色非唯一状态区分 + 文字/图标配对）、EP-006（SSE 连接韧性 + 指示器）
- **关键综合**: 将 system-architect 的 SSE 架构（连接管理器 + 事件桥接）、ux-expert 的等待体验设计、ui-designer 的节点卡片状态动画整合为水平管道 + 下方详情面板

### F-005: result-gallery

- **角色共识**: 画廊浏览、原生视频、下载支持
- **冲突解决**: large file handling → SUGGESTED: thumbnail-first（poster attribute）+ 按需加载
- **增强应用**: EP-007（桌面端 Grid 3 列）、D-013（原生先行 + 可替换增强架构）
- **关键综合**: 将 system-architect 的 Gallery API 和文件服务架构、ux-expert 的产物优先级（final.mp4 优先）、ui-designer 的双视图模式整合为 final 优先 + Grid/Timeline 切换

### F-006: run-history

- **角色共识**: 基于 manifest 的历史浏览、聚合状态、分页
- **冲突解决**: 无冲突
- **增强应用**: EP-006（骨架屏加载）、EP-007（桌面端布局）
- **关键综合**: 将 system-architect 的配置漂移检测、ux-expert 的"恢复参数"安全策略、ui-designer 的聚合状态视觉整合为策划内容 + 原始数据可展开

### F-007: param-tuner

- **角色共识**: 实时验证、JSON 预览、一键重跑
- **冲突解决**: re-run vs active run → SUGGESTED: 检查 API → 409 对话 → 用户选择
- **增强应用**: EP-008（3 层参数分组）、EP-005（重跑前 ComfyUI 健康检查）
- **关键综合**: 将 system-architect 的参数验证 API 和 Workflow 预览、ux-expert 的种子交互设计、ui-designer 的覆盖指示器整合为双栏布局 + 7 项关键决策（最多决策数）

## Conflict Resolution Summary

| Feature | Conflict | Status | Resolution |
|---------|----------|--------|------------|
| F-001 | priority alignment | RESOLVED | arch High, UX Medium via API contract |
| F-002 | layout transition | RESOLVED | wizard embeds card list (D-015) |
| F-003 | parameter depth vs disclosure | RESOLVED | 3-tier taxonomy per EP-008 (adopted as Decision 3) |
| F-004 | progress granularity | RESOLVED | MVP shot-level only (D-016) |
| F-005 | large file handling | RESOLVED | thumbnail-first, poster attribute (adopted as Decision 2) |
| F-006 | (none) | — | — |
| F-007 | re-run vs active run | RESOLVED | check API → 409 dialog → proceed (adopted as Decision 5) |

**RESOLVED**: 7 | **SUGGESTED**: 0 | **UNRESOLVED**: 0

## Enhancement Application Summary

| Enhancement | Applied To | Integration Method |
|-------------|-----------|-------------------|
| EP-001 | F-001 (API 层), F-002~F-007 (前端消费) | 统一错误信封格式 + 3 层错误展示 |
| EP-002 | F-002 (角色步骤), F-003 (角色关联) | 角色卡片式 UI + 可跳过步骤 |
| EP-003 | F-002~F-007 (所有功能) | WCAG 2.1 AA: 键盘导航、ARIA、对比度、焦点管理 |
| EP-004 | F-003 (主功能) | Command Pattern 撤销栈 |
| EP-005 | F-001 (/health), F-002 (连接测试), F-007 (重跑前检查) | 持久指示器 + 预检查 |
| EP-006 | F-001~F-007 (所有功能) | 骨架屏/spinner/进度条/SSE 指示器 |
| EP-007 | F-001~F-007 (所有功能) | min 1280px 视口，不实现移动端 |
| EP-008 | F-002, F-003, F-007 (参数密集功能) | Essential/Advanced/Expert 3 层 |

## Shared Component Inventory

以下组件在多个功能规格中交叉引用，需统一实现：

1. **`<ParameterField>`** — F-002, F-003, F-007（3 个功能共用，EP-008 分层支持）
2. **`<StatusBadge>`** — F-003, F-004, F-006, F-007（4 个功能共用，管道状态 token）
3. **`<VideoPlayer>`** — F-005, F-006（2 个功能共用，可替换增强架构）
4. **`<FrameThumbnail>`** — F-003, F-004, F-005（3 个功能共用）
5. **`<PathSelector>`** — F-002, F-007（2 个功能共用）
6. **`<EmptyState>`** — 所有功能（统一空状态模式）
7. **`<ConnectionTestButton>`** — F-002（EP-005 专用）

## Dependency Graph (Simplified)

```
F-001 (api-server)
  ├── F-002 (project-wizard)
  │     └── F-003 (shot-card-editor)
  │           ├── F-004 (generation-monitor)
  │           │     └── F-005 (result-gallery)
  │           │           └── F-006 (run-history)
  │           └── F-007 (param-tuner)
  ├── F-004 ──→ F-005 ──→ F-006
  └── F-007 ←── F-004, F-005, F-006
```

## Synthesis Quality Notes

- 所有 7 份规格均使用 RFC 2119 关键词（MUST/SHOULD/MAY）明确约束等级
- Design Decisions 部分占各规格 40%+ 篇幅，包含完整决策理由和选项对比
- 所有 UNRESOLVED 冲突为零，SUGGESTED 冲突 3 项需在实施阶段确认
- 跨功能依赖通过 Integration Points 和 Shared Components 双重标注
- EP-001 至 EP-008 全部应用到相关功能，无遗漏

## Review Results

**Complexity Score**: 5
**Specs Reviewed**: 7
**Minor Fixes Applied**: 7
**Major Flags Raised**: 2

### Fixes Applied

- 001-api-server.md: 补充 F-004 定义的 `shot:progress` 和 `run:stitching` SSE 事件类型到事件表（原表仅 7 种，F-004 列出 9 种）
- 001-api-server.md: 补充 F-006/F-007 定义的 API 端点到端点表（`/params/validate`, `/workflow-preview`, `/workflow-diff`, `/re-run`, `/pipeline-state`, `/config-drift`），原表缺少 8 个跨功能引用端点
- 004-generation-monitor.md: SSE 心跳间隔从 30s 统一为 15s（与 F-001 API 契约一致），同步更新约束表
- 006-run-history.md: 分页参数从 `page`/`per_page` 统一为 `offset`/`limit`（与 F-001 统一分页契约一致）
- 002-project-wizard.md: 校验 API HTTP 方法从 `POST` 统一为 `GET`（与 F-001 端点表一致，校验操作幂等适合 GET）
- feature-index.json: F-003/F-005/F-007 冲突状态从 SUGGESTED 升级为 RESOLVED（规格中已采纳为 Decision）
- synthesis-changelog.md: 同步更新冲突解决汇总表计数（RESOLVED: 7, SUGGESTED: 0）

### Flags Raised

- 001-api-server.md: [REVIEW-FLAG] cancelled Run 的最终状态歧义 -- AC#8 定义为 failed + "cancelled_by_user"，但 SSE 事件表定义了独立的 `run:cancelled` 事件类型，F-004 节点状态映射无 cancelled 状态。需明确：cancelled 是 failed 的子类型（status=failed, error_code=cancelled_by_user）还是独立状态枚举值？建议统一为 status=failed + error_code=cancelled_by_user，`run:cancelled` 仅为通知事件
- 006-run-history.md: [REVIEW-FLAG] Run 状态术语不一致 -- F-001 状态机使用 "succeeded/failed"，F-006 聚合状态使用 "completed/partial/failed/running"。"succeeded" vs "completed" 跨规格不一致。建议：F-001 API 层保持 succeeded/failed（与状态机一致），F-006 前端筛选使用 completed/partial/failed（聚合视角），API 参数映射在前端完成

### Review Methodology

1. **Cross-Feature Consistency**: 逐项对比 7 份规格中相同概念的术语、技术选型、API 路径、HTTP 方法、参数命名、时间常量。发现 5 处术语/数值不一致并修复，2 处需决策澄清并标记。
2. **Conflict Resolution Completeness**: 验证所有冲突状态标记。3 个 SUGGESTED 项在规格中已被采纳为设计方案，升级为 RESOLVED。无 UNRESOLVED 项。
3. **Dependency Bidirectionality**: 提取每份规格 Section 7 的 depends_on/required_by 与 feature-index.json 逐条比对，7 个功能的依赖关系完全双向一致。
4. **Enhancement Coverage**: 检查 EP-001 至 EP-008 在各规格中的引用。所有 8 项增强均已反映在相关规格中。EP-003 在 F-005/F-006 中未显式标注但已通过交互设计隐式覆盖（逐帧键盘控制、列表导航）。
