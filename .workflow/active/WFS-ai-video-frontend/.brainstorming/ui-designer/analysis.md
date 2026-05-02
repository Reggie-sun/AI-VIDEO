# UI Designer Analysis: AI-VIDEO Frontend

**Role**: ui-designer | **Framework**: @../guidance-specification.md | **Date**: 2026-05-02

## Design Vision

AI-VIDEO 的前端设计核心目标是让非技术背景的内容创作者/设计师无需手写 YAML，即可完成从项目创建到视频预览的完整流程。设计语言必须传达"创作工具"而非"开发者工具"的定位，视觉上强调温暖、直觉、可控。

**Design Principles**:
- **Progressive Disclosure**: 向导式流程先展示最少选项，高级参数按需展开
- **Visual Primacy**: 视频和帧图像优先展示，文字参数次之
- **Safe Exploration**: 所有操作可撤销/回退，鼓励用户探索参数
- **Consistent Motion**: 状态变化使用统一动效语言，降低认知负荷

## Feature Point Index

| Feature | Document | UI Focus |
|---------|----------|----------|
| F-001 api-server | @analysis-F-001-api-server.md | API 消费层的界面适配、错误态、加载态 |
| F-002 project-wizard | @analysis-F-002-project-wizard.md | 向导步骤组件、表单设计、路径选择器 |
| F-003 shot-card-editor | @analysis-F-003-shot-card-editor.md | 卡片组件、拖拽交互、参数面板、提示词输入 |
| F-004 generation-monitor | @analysis-F-004-generation-monitor.md | 管道节点视图、状态色彩、SSE 实时更新动效 |
| F-005 result-gallery | @analysis-F-005-result-gallery.md | 视频播放器、帧画廊、下载交互 |
| F-006 run-history | @analysis-F-006-run-history.md | 时间线列表、manifest 展示、产物导航 |
| F-007 param-tuner | @analysis-F-007-param-tuner.md | 参数面板、JSON 预览、验证反馈、重跑触发 |

Cross-cutting concerns: @analysis-cross-cutting.md

## Confirmed Design Decisions

Per @../guidance-specification.md Section 6:

- **Design System**: shadcn/ui + Tailwind CSS (MUST)
- **Video Player**: Native HTML5 first, swappable enhancement reserved (MUST native / SHOULD enhanced)
- **Layout**: Full-screen single-task (MUST)
- **Conflict Resolution**: Wizard embeds card list within editing step (MUST)

## User Persona Summary

**Primary Persona**: 内容创作者/设计师
- 非技术背景，不熟悉 YAML/CLI
- 重视视觉反馈和直觉操作
- 期望"创作流"而非"配置流"
- 对参数含义不熟悉，需要内联解释

## Design System Foundation

- **Component Library**: shadcn/ui (Radix primitives + Tailwind styling)
- **Color Strategy**: 暗色主题为默认（视频创作者偏好），支持亮色切换
- **Typography**: Inter (UI) + JetBrains Mono (技术数据/JSON)
- **Icon Set**: Lucide Icons (shadcn/ui 内置)
- **Spacing**: Tailwind 4px 基础网格，8px 组件间距
- **Border Radius**: shadcn/ui 默认 `--radius: 0.5rem`，卡片 `0.75rem`
