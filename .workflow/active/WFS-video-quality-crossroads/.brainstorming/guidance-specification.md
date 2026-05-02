# AI-VIDEO 质量十字路口 — Confirmed Guidance Specification

**Generated**: 2026-05-02
**Type**: Brainstorming — Direction & Strategy
**Focus**: 视频质量优先 vs Pipeline 功能扩展的战略决策
**Roles**: system-architect, product-manager, subject-matter-expert

---

## 1. Project Positioning & Goals

**CONFIRMED Objective**: 将 AI-VIDEO 从"能跑通"推进到"能发布"——视频质量达到商业级，人物和场景跨 clip 一致，最终产出可发布的完整长视频。

**CONFIRMED Success Criteria**:
- 单个 clip 质量达标（无崩坏、语义正确、视觉可接受）
- 多 clip 拼接后人物外观和场景基本一致
- 完整 15秒+ 视频可直接发布
- 质量调优体系可复用于未来换工作流/换模型

**CONFIRMED Current State**:
- Pipeline 功能完备（run/resume/stitch/manifest/hash 验证），31 个测试通过
- 真实 ComfyUI 端到端运行成功（first-real-run + quick-verify）
- **视频质量极差**：单 clip 质量差 + 跨 clip 不连贯，两者都有
- 根因判断：**参数未优化**（非模型上限问题）

## 2. Concepts & Terminology

| Term | Definition | Aliases | Category |
|------|------------|---------|----------|
| I2V | Image-to-Video，从单帧图片生成视频片段 | img2vid | core |
| Last-frame Chaining | 用上一 clip 的最后一帧作为下一 clip 的 init_image，保持视觉连贯性 | frame chaining, 帧链接 | core |
| IPAdapter | 通过参考图保持生成人物外观一致的技术 | IP-Adapter, 参考图适配 | core |
| Clip | 单次 I2V 生成的短视频片段（当前 5秒 @ 16fps） | shot clip, 片段 | core |
| Workflow | ComfyUI 的工作流 JSON 定义，包含模型加载、采样、解码等节点 | 工作流 | technical |
| Binding | workflow 中可替换字段的路径映射（prompt/seed/image 等） | 绑定 | technical |
| Normalize | 将不同编码参数的 clip 统一为相同分辨率/fps/编码的中间步骤 | 标准化 | technical |
| Stitch | 将多个 normalized clip 拼接为最终长视频 | 拼接 | technical |
| Manifest | 记录整个 run 的元数据、每个 shot 的状态和 artifact 路径的 JSON 文件 | 运行清单 | technical |
| Quality Gate | 在 pipeline 某个阶段检查视频质量的自动化判断点 | 质量门 | strategy |

## 3. Non-Goals (Out of Scope)

- **分布式训练/推理**: 不做多机多卡、集群调度，只跑本地单机单卡
- **云端部署**: 不做云端服务化，只做本地 CLI pipeline
- **后期编辑**: 不做视频剪辑/特效/后期处理软件
- **实时预览**: 不做流式输出或实时预览
- **音频生成**: 当前阶段不涉及语音/音效生成

## 4. System-Architect Decisions

### SELECTED: 质量优先 → 功能
**Strategy**: 先把 Wan2.2 workflow 参数调优到单 clip 质量达标，再推进 pipeline 功能。理由是质量是产品的根基，功能扩展在质量不稳定时价值为零。

- The project MUST prioritize video quality optimization before adding new pipeline features
- The project SHOULD establish a quality baseline (at least 1 acceptable clip) before resuming feature work
- Quality optimization MUST be model-agnostic where possible, to support future workflow/model switching

### SELECTED: 参数未优化是当前瓶颈
**Diagnosis**: 当前视频质量差的原因是 workflow 参数未优化（采样步数、CFG、LoRA、Prompt 等），而非模型本身的能力上限。

- The team MUST first diagnose which parameters have the largest quality impact
- Parameter tuning experiments MUST be systematically recorded for reproducibility
- The project SHOULD build a parameter experiment framework that works across different models/workflows

### Cross-Role Considerations
**Quality + Pipeline dependency**: Pipeline features (like resume, parallel shots) depend on quality being acceptable — if a clip is bad, re-running it with the same parameters won't help. Therefore quality optimization is a hard prerequisite.

## 5. Product-Manager Decisions

### SELECTED: 完整可发布视频是成功标准
**MVP Definition**: 不是单 clip 达标就算成功，而是完整的多 clip 拼接视频可直接发布。

- The project MUST deliver a complete publishable video (quality + consistency + stitching) as the first milestone
- Each quality improvement iteration MUST produce a full stitched video for evaluation, not just individual clips
- The project SHOULD define concrete quality criteria for "publishable" (e.g., no face morphing, consistent outfit, coherent motion)

### SELECTED: 不急，慢慢来
**Timeline**: 没有时间压力，愿意花时间把质量调好。

- Quality optimization MAY take multiple iterations without deadline pressure
- Each iteration SHOULD produce measurable improvement over the previous one
- The project MUST NOT rush to add features before quality is acceptable

### Cross-Role Considerations
**Definition of "publishable"**: Product-manager's "complete publishable video" and subject-matter-expert's quality criteria need alignment. This will be resolved in synthesis.

## 6. Subject-Matter-Expert Decisions

### SELECTED: 复用社区方案
**Tuning Strategy**: 先研究 Wan2.2 I2V 的最佳实践和社区成熟配置，复用已验证的参数组合，而非从头摸索。

- The project MUST research Wan2.2 community best practices before custom tuning
- Parameter configurations from community SHOULD be tested as-is first, then adapted
- The project SHOULD maintain a knowledge base of proven parameter sets per model/workflow

### SELECTED: IPAdapter + Last-frame Chaining 两者结合
**Consistency Strategy**: 同时使用 IPAdapter 保持人物外观一致 + last-frame chaining 保持视觉连贯性。

- The project MUST implement IPAdapter support in the workflow (currently missing — only last-frame chaining exists)
- The project SHOULD configure IPAdapter weight and reference images for character consistency
- The two consistency mechanisms MUST NOT conflict (IPAdapter for appearance, chaining for motion continuity)

### Cross-Role Considerations
**Workflow changes**: Adding IPAdapter requires workflow template changes (new nodes, new binding fields). This affects system-architect's pipeline design — the workflow template + binding schema must support IPAdapter configuration.

### Additional: Future Model/Workflow Switching
**CONFIRMED**: The user plans to switch models and workflows in the future. Quality optimization processes MUST be transferable.

- The quality evaluation framework MUST be model-agnostic
- Parameter experiment records MUST include model/workflow version information
- The project SHOULD design workflow templates as interchangeable units with consistent binding interfaces

## 7. Feature Decomposition

| Feature ID | Name | Description | Related Roles | Priority |
|------------|------|-------------|---------------|----------|
| F-001 | wan22-quality-baseline | 研究 Wan2.2 社区最佳配置，建立单 clip 质量基线 | subject-matter-expert | High |
| F-002 | ipadapter-consistency | 在 workflow 中集成 IPAdapter 节点和绑定，实现跨 clip 人物一致性 | subject-matter-expert, system-architect | High |
| F-003 | quality-evaluation-framework | 建立视频质量评估体系（自动化+人工），支持跨模型复用 | product-manager, system-architect | High |
| F-004 | param-experiment-tracker | 参数实验记录框架，追踪每次调参的配置、输出和效果 | system-architect, subject-matter-expert | Medium |
| F-005 | full-video-evaluation-loop | 完整视频评估闭环：跑全流程 → 评估质量 → 调参 → 重跑 | product-manager, system-architect | Medium |

## 8. Risks & Constraints

- **Risk**: Wan2.2 模型可能有质量上限，即使参数调优也达不到商业级 → **Mitigation**: 先用社区方案建立基线，如果仍不够，考虑换模型
- **Risk**: IPAdapter 与 last-frame chaining 可能冲突 → **Mitigation**: 分阶段验证，先确认 IPAdapter 单独效果，再加 chaining
- **Risk**: 社区方案针对的场景可能与本项目不同 → **Mitigation**: 选择最接近的场景（人物 I2V），作为起点而非终点
- **Constraint**: 本地单机 RTX 5090，32GB VRAM → 限制可用的模型大小和 batch size

## 9. Next Steps

**⚠️ Automatic Continuation**: Auto mode will assign agents for role-specific analysis.
- system-architect: 技术路线图设计
- product-manager: 迭代计划和质量标准定义
- subject-matter-expert: Wan2.2 参数调优策略和 IPAdapter 集成方案

## Appendix: Decision Tracking

| Decision ID | Category | Question | Selected | Phase | Rationale |
|-------------|----------|----------|----------|-------|-----------|
| D-001 | Intent | 视频乱的类型 | 两者都有（质量+不连贯） | 1 | 决定两个问题都要解决 |
| D-002 | Intent | 优先方向 | 先调质量 | 1 | 质量是产品根基 |
| D-003 | Intent | 质量预期 | 商业级 | 1 | 高标准目标 |
| D-004 | Arch | 推进策略 | 质量优先→功能 | 3 | 功能扩展在质量差时无价值 |
| D-005 | Arch | 质量瓶颈 | 参数未优化 | 3 | 非模型上限问题 |
| D-006 | PM | 成功标准 | 完整可发布视频 | 3 | 不只单 clip，要全流程可用 |
| D-007 | PM | 时间压力 | 不急 | 3 | 质量优先，慢慢调 |
| D-008 | SME | 调参策略 | 复用社区方案 | 3 | 避免重复摸索 |
| D-009 | SME | 一致性方案 | IPAdapter + Chaining | 3 | 双重保障 |
| D-010 | Additional | 未来换模型 | 质量体系可复用 | 4.5 | 不做 Wan2.2 专属方案 |
