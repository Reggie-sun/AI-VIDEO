# UX Expert Analysis: AI-VIDEO Frontend

**Role**: UX Expert | **Session**: WFS-ai-video-frontend | **Date**: 2026-05-02
**Framework Reference**: @../guidance-specification.md

## UX Vision

AI-VIDEO 前端的核心体验目标是：让非技术背景的内容创作者/设计师无需手写 YAML，即可完成从项目创建到视频预览的完整工作流。体验质量属性按优先级排序为：**易学性 > 效率 > 容错性 > 一致性 > 可发现性**。

## User Persona

**Primary Persona — 创意工作者 (Creative Creator)**
- 背景：内容创作者、视频编辑、设计师，无编程经验
- 目标：快速将创意想法转化为 AI 生成视频
- 痛点：YAML 语法门槛高，参数概念晦涩，错误信息不可读
- 心智模型：类似 Canva/Figma 的图形化操作，而非命令行工具
- 关键需求：引导式流程、直觉化操作、即时反馈、可逆操作

## Experience Principles

1. **Progressive Disclosure**: 复杂参数按需展示，默认只暴露必要字段
2. **Immediate Feedback**: 每个操作 200ms 内必须有视觉响应
3. **Error Prevention over Recovery**: 约束输入而非事后报错
4. **Recognition over Recall**: 可视化选择而非文本输入
5. **Guided Autonomy**: 向导引导但不限制，高级用户可跳过步骤

## Feature Point Index

| Feature | Analysis Document | UX Priority | Core UX Concern |
|---------|-------------------|-------------|-----------------|
| F-001 api-server | @analysis-F-001-api-server.md | Medium | 错误信息可读性、加载状态 |
| F-002 project-wizard | @analysis-F-002-project-wizard.md | Critical | 向导流程设计、认知负荷控制 |
| F-003 shot-card-editor | @analysis-F-003-shot-card-editor.md | Critical | 拖拽交互、参数编辑可用性 |
| F-004 generation-monitor | @analysis-F-004-generation-monitor.md | High | 状态可视化、等待体验 |
| F-005 result-gallery | @analysis-F-005-result-gallery.md | Medium | 画廊浏览、预览交互 |
| F-006 run-history | @analysis-F-006-run-history.md | Medium | 历史导航、信息密度平衡 |
| F-007 param-tuner | @analysis-F-007-param-tuner.md | Medium | 参数验证反馈、重跑流程 |

## Primary User Journey

```
启动应用 → [F-002] 创建/选择项目 → [F-003] 编辑分镜表 → [F-007] 调优参数(可选)
       → [F-004] 启动生成并监控 → [F-005] 预览结果 → [F-006] 查看历史(可选)
```

关键转场时刻：
- 项目创建到分镜编辑：MUST 自动保存项目配置，无缝过渡
- 分镜编辑到启动生成：MUST 提供预检查摘要，减少"最后一刻发现错误"
- 生成完成到结果预览：MUST 自动跳转，零等待感知

## Cross-Cutting Summary

跨功能 UX 决策详见 @analysis-cross-cutting.md，涵盖：
- 全局导航模型与信息架构
- 错误处理与反馈机制统一策略
- 可访问性基线 (WCAG 2.1 AA)
- 设计系统一致性治理
- 状态管理交互模式

## Key UX Risks

1. **YAML 概念映射**: 项目配置参数(originally YAML)到 UI 控件的映射 MAY 丢失语义，需用描述性标签和 tooltip 补偿
2. **等待体验**: 单个 shot 生成可能长达 30 分钟，MUST 设计有效的进度反馈和中断机制
3. **参数爆炸**: shot 可配置参数超过 10 个，MUST 通过折叠/分组/智能默认控制认知负荷
4. **错误恢复**: 非技术用户面对生成失败时，MUST 提供可操作的建议而非原始错误栈
