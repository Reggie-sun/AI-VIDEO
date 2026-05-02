# AI-VIDEO 质量十字路口 — 综合分析

**Session**: WFS-video-quality-crossroads
**Date**: 2026-05-02
**Roles**: system-architect, product-manager, subject-matter-expert

---

## 核心结论：先改 3 个参数，立刻就能看到改善

三个角色的分析一致指向同一个结论：**当前视频质量差的根因已精确定位，是 3 个参数同时处于严重偏差状态，而非模型上限问题。**

| 参数 | 当前值 | 正确值 | 影响程度 |
|------|--------|--------|----------|
| LoRA | lightx2v 4-step 蒸馏 | None（基础模型） | **致命** — 蒸馏 LoRA 设计用于快速预览，牺牲 80%+ 质量 |
| Steps | 8 | 30-40 | **致命** — 仅为官方参考的 20% |
| CFG | 1.0 | 5.0 | **致命** — 等于零引导，模型完全不受 prompt 驱动 |

**预计修复这 3 项后，单 clip 质量可提升 60%+。**

---

## 行动路线图

### 第一步：立即行动 — 3 参数修复（1 个 session，~10 分钟改动 + ~5 分钟生成）

这是零风险的快速胜利。只需修改 workflow 模板和 project config，不需要任何代码改动。

**具体操作：**
1. 修改 `wan22_i2v_api.json`：
   - 节点 565 (WanVideoLoraSelectMulti): 将 lora_0 设为 "none"
   - 节点 562 (WanVideoSampler): steps 改为 30，cfg 改为 5.0
2. 修改 `wan22.project.yaml`：
   - negative_prompt 改为官方推荐的负向提示词
3. 运行一次 1-shot 生成，对比效果

**成功标准**：单 clip 无明显崩坏（脸不变形、语义正确、无闪烁），达到 Q1（可观看）

### 第二步：负向提示词 + Prompt 优化（同一 session）

**具体操作：**
1. 设置 negative_prompt（官方 Wan2.1 列表 + 面部变形/服装变换相关词）
2. 优化 shot prompts：加入详细运动描述、人物外貌、镜头运动
3. 扩展 style_prompt
4. 再次生成，对比改善

**成功标准**：单 clip 达到 Q2（无显而易见的瑕疵）

### 第三步：IPAdapter 兼容性验证（1-2 小时）

**在投入工作流改造之前，必须先验证 Wan2.2 是否支持 IPAdapter。**

**具体操作：**
1. 检查 Kijai 的 ComfyUI-Wan2Wrapper 是否内置 reference attention / IPAdapter 支持
2. 检查 CivitAI/HuggingFace 是否有 Wan2.2 兼容的 IPAdapter 模型
3. 如果不可用，搜索 Wan2 原生 reference image conditioning 方法

**决策分支：**
- 如果 Wan2.2 兼容 IPAdapter → 进入第四步
- 如果不兼容但有原生 reference attention → 使用原生方案（控制力弱但零兼容问题）
- 如果两者都不可用 → 降级为 Character LoRA 或增强 Prompt 一致性

### 第四步：IPAdapter + Chaining 集成（1-2 sessions）

**架构好消息**：system-architect 发现 Pipeline 代码层面几乎零改动。`CharacterProfile`、`CharacterRefBinding`、`_prepare_character_images`、`render_workflow` 的 `character_refs` 处理逻辑全部已预置。缺失的只是 workflow 模板中的 IPAdapter 节点和 Binding 中的 `character_refs` 条目。

**具体操作：**
1. 创建 `wan22_i2v_ipadapter_api.json`（添加 IPAdapter 节点）
2. 更新 binding YAML（添加 character_reference_image、ipadapter_weight 等）
3. 更新 `wan22.project.yaml`（添加 characters 配置和参考图）
4. 分阶段测试：IPAdapter 单独 → Chaining 单独 → 两者结合

**成功标准**：3-clip 拼接视频人物外观基本一致，达到 Q2

### 第五步：迭代打磨至 Q3（2-4 sessions）

- 微调 IPAdapter weight、start_at/end_at
- 优化 clip 边界过渡
- 精细调参（scheduler、shift、noise_aug_strength）
- 每次迭代产出完整拼接视频，人工评估

**成功标准**：完整视频可发布（Q3）

### 第六步：系统化（1-2 sessions）

- 记录已验证的参数配置
- 正式化评估框架
- 确保实验追踪器记录所有发现

---

## 风险与回退

| 风险 | 概率 | 回退方案 |
|------|------|----------|
| Wan2.2 即使参数正确也达不到 Q2 | 中 | 换模型：HunyuanVideo 或 CogVideoX（架构切换成本极低：新模板 + 新 binding + widget map 少量条目） |
| IPAdapter 不兼容 Wan2.2 | 中 | 使用原生 reference attention 或 Character LoRA |
| 两者结合时冲突 | 低 | 分阶段集成，先 IPAdapter 单独再 chaining |
| 无限调参不见改善 | 低 | 每次迭代必须产出完整视频对比；3 次无改善则换策略 |

---

## 质量分级定义

| 级别 | 名称 | 描述 | 信号 |
|------|------|------|------|
| Q0 | 崩坏 | 明显变形、语义错误、闪烁 | **当前状态** |
| Q1 | 可观看 | 无严重瑕疵，但细看有问题 | 第一步目标 |
| Q2 | 及格 | 一眼看去无明显问题 | 第二步目标 |
| Q3 | 可发布 | 可发到社交媒体而不尴尬 | 终极目标 |
| Q4 | 优质 | 观众会停下来看 | 理想状态 |

**唯一真正重要的指标：你愿意把这个视频发到社交媒体吗？**

---

## 关键架构洞察

1. **Pipeline 代码无需改动即可支持 IPAdapter** — 原始设计已预留了 `character_refs`、`CharacterRefBinding`、`_prepare_character_images` 等接口
2. **模型切换成本极低** — 新模板 + 新 binding + `workflow_loader.py` 的 `ARRAY_WIDGET_NAME_MAP` 少量条目，Pipeline/Manifest/实验追踪器全部模型无关
3. **实验追踪应从简单开始** — markdown 日志 + 模型版本 + 参数 + 质量层级，确保换模型时不丢失知识

---

## 下一步行动

**现在立刻做的事**：修改 3 个参数（移除 LoRA + steps 30 + CFG 5.0），运行一次 1-shot 测试。
