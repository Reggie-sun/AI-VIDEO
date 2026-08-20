# AI-VIDEO 5-Minute Rough Cut Reality Validation Specification

**Target Repository:** `Reggie-sun/AI-VIDEO`
**Target Slice:** 5-minute real short-drama rough cut
**Status:** Proposed reality-validation specification
**Purpose:** 在现有 P2-P8、Shot Router、H3 quality lane 和 Provider portability smoke 基础上，第一次用真实约 5 分钟内容验证 AI-VIDEO 是否能完成完整生产闭环。

---

# 1. Objective

本轮目标不是制作商业级成片，也不是继续证明架构正确。

目标是：

> **使用 AI-VIDEO 当前已经实现的能力，完成一部约 5 分钟、从 Story 到 final.mp4 的真实短剧 rough cut，并记录真实生产过程中出现的问题、成本、失败和返工路径。**

本轮最终必须产出一个实际可播放的完整视频。

成功标准不是“每个镜头都完美”，而是：

```text
Story
→ Character / Scene
→ Shot Plan
→ Image / Generated Video Assets
→ Voice / Captions
→ Continuity
→ ResolvedTimeline
→ HyperFrames
→ QA
→ Selective Repair
→ final.mp4
```

这条链在真实 5 分钟作品中能够成立。

---

# 2. Entry Gate

开始本 Spec 前，以下能力视为已有前置：

* H3 local quality lane 已冻结；
* H3 exact-terminal continuity 已有真实 proof；
* H3 → Hailuo bounded Provider portability smoke 已通过；
* unsupported reference capability 会 typed block，不允许静默降级；
* Provider 不由 Shot Router 自动排名、fallback 或切换；
* Hailuo 历史 MP4 已证明可以进入现有：
  `CompositionSpec -> ResolvedTimeline -> HyperFrames`；
* 当前 ProductionProject、Asset Registry、Manifest、Dependency Graph、StateCommitter、ResolvedTimeline ownership 不变。

本轮不重新证明这些基础契约。

---

# 3. Core Question

本轮只回答一个核心问题：

> **AI-VIDEO 能不能真正完成一部约 5 分钟的 AI 短剧，并且在中途出现问题时能够定位、局部修复并重新输出完整视频？**

以下问题属于本轮必须通过真实生产回答的问题：

* 角色在 30～45 个 Shot 中会不会逐渐漂移？
* 场景和服装状态能否保持？
* 不同 Shot 之间动作和空间关系是否自然？
* 哪些 Shot 真正值得使用生成视频？
* 哪些 Shot 用静态图或轻运动更合适？
* H3 作为主要本地视频模型是否足够实用？
* 生成失败后是否能明确定位原因？
* 修一个 Shot 是否只影响真正依赖它的部分？
* 配音、字幕和镜头长度是否能够协调？
* 整体 5 分钟生产时间和人工干预量是多少？

---

# 4. Scope

本轮只制作：

```text
1 部短剧
约 5 分钟
1 个完整故事
1 个主要角色
最多 1 个主要配角
1～2 个主要场景
约 30～45 个 Shots
```

目标时长：

```text
270～330 秒
```

不要求精确等于 300 秒。

---

# 5. Production Profile

第一部 rough cut 必须主动限制变量。

推荐默认结构：

```text
Static Image / Image Motion
≈ 40～60%

H3 I2V / continuity video
≈ 30～50%

T2V / identity-free generated video
少量

Cloud Provider
仅必要 Shot
```

这些比例不是硬性验收值。

核心原则：

> 不需要真实视频运动的 Shot，不得为了“看起来高级”强制使用 Video Provider。

---

# 6. Shot Strategy Rules

每个 Shot 必须先明确 `visual_strategy`。

允许：

```text
static_image
image_motion
motion_graphics
generated_video
existing_video
hybrid
```

不得默认：

```text
所有 Shot = generated_video
```

### Static / Image Motion

优先用于：

* 对话反应；
* 人物特写；
* 情绪停顿；
* 简单环境展示；
* 无明显身体动作；
* 可以通过 push-in / pan / parallax 表达的镜头。

### Generated Video

优先用于：

* 行走；
* 起身；
* 开门；
* 明显身体动作；
* 动作连续；
* 复杂镜头运动；
* 关键剧情动作；
* Hero Shot。

---

# 7. Provider Policy

本轮 Provider selection 保持显式。

默认：

```text
Local MiniMax H3
= generated-video primary lane
```

H3 用于：

* 本地 draft；
* ordinary dynamic Shots；
* exact-terminal continuation；
* 已证明 capability 范围内的 I2V。

不得因为 H3 某一次生成失败自动切换 Provider。

### Hailuo

Hailuo 只作为：

```text
explicit alternate / rescue / selected important Shot
```

当前已有 Provider portability evidence，但不意味着本轮自动授权新的 remote submit。

如果需要真实 Hailuo 调用，必须遵守现有 AI-VIDEO Paid Provider Gate 和 task-scoped authorization。

### Seedance

本轮默认不作为必须 Provider。

不得为了完成 rough cut 顺手扩大为：

* Seedance benchmark；
* Seedance Router integration；
* 多 Provider quality ranking；
* automatic fallback。

---

# 8. Continuity Policy

不同 Shot 不允许统一使用“上一镜最后一帧作为下一镜第一帧”。

必须根据 Shot transition 类型选择连续方式。

### A. Exact Terminal Continuity

适合：

```text
同一动作继续
同一机位继续
连续运动
clip extension
```

允许：

```text
Shot N terminal frame
→ Shot N+1 first frame
```

### B. Reference Continuity

适合：

```text
保持人物/服装/场景
但下一镜换机位或重新构图
```

继承：

* Character references；
* Scene references；
* outfit/state；
* previous close-state evidence。

不得强行复用上一镜构图。

### C. Semantic Continuity

用于：

* 时间跳跃；
* 地点切换；
* 明显新场次。

只继承故事和角色状态，不要求视觉首尾完全连续。

---

# 9. Shot State

涉及重要连续性的 Shot，应至少明确：

```text
open_state
changes_here
close_state
```

关注：

* 人物身份；
* 服装；
* 道具；
* 人物位置；
* 屏幕方向；
* 动作阶段；
* 光线；
* 环境状态；
* 声音状态。

不要求本轮新增新的 durable schema。

如果当前 AI-VIDEO domain 已有足够字段表达，应优先复用现有 contract。

不得仅为了本 Spec 创建第二套 production truth。

---

# 10. Creative Skill Usage

外部 Skill 继续只作为建议层。

### Hell-Grind

用于：

* Shot open/close state；
* 跨 Shot 连续性；
* prompt structure；
* generation failure diagnosis。

### Higgsfield

用于：

* H3/Hailuo/其他模型对应的 prompt/mode advice；
* Provider-specific generation guidance。

### video-shotcraft

用于：

* image motion；
* motion graphics；
* pacing；
* transition；
* SFX；
* shot language。

所有建议最终必须转换为 AI-VIDEO 自己的 Shot / Asset / Composition / Provider contracts。

---

# 11. Story Requirements

第一部 rough cut 不追求复杂剧本。

故事必须满足：

* 5 分钟内可以讲完整；
* 主角目标明确；
* 开头、发展、结果清楚；
* 避免大量群演；
* 避免频繁换场；
* 避免大规模战争或复杂打斗；
* 避免需要大量独立角色 reference；
* 至少包含几个真正需要 generated video 的动作 Shot。

目标是验证生产系统，不是挑战模型极限。

---

# 12. Image Assets

在开始大量视频生成前，必须先锁定：

```text
Character Reference Pack
Scene Reference Pack
主要服装状态
关键道具
```

重要角色不得每个 Shot 重新从纯文字生成。

如果 Character / Scene reference 本身质量不合格，应先修 reference，而不是通过视频 Prompt 强行修复。

---

# 13. Voice and Captions

rough cut 必须包含真实可听的：

* Dialogue / Narration；
* CaptionTrack；
* 最终字幕；
* 基础音频混合。

允许声音质量不是最终版。

但必须能够验证：

```text
文本
→ voice
→ timing
→ CaptionTrack
→ ResolvedTimeline
→ final render
```

如果语音长度导致 Shot duration 改变，应记录真实问题，不允许只通过测试 fixture 隐藏。

---

# 14. Production Order

推荐实际执行顺序：

```text
1. Brief / Story
2. Character + Scene lock
3. Storyboard
4. Shot list
5. Shot visual strategy
6. Static/image assets
7. Voice + captions
8. Generated-video Shots
9. ResolvedTimeline
10. First complete rough cut
11. Watch full video
12. Record defects
13. Selective repair
14. Second complete render
15. Final rough-cut acceptance
```

核心规则：

> 必须尽快得到第一版完整 5 分钟视频。

不得在 Shot 1～5 上无限优化，导致永远没有完整 rough cut。

---

# 15. First Complete Cut Gate

第一版完整 rough cut 可以包含：

* 尚未完全理想的 H3 Shot；
* 少量静态占位；
* 未最终调色的素材；
* 基础 BGM/SFX；
* 暂时不是最终质量的字幕样式。

但必须：

```text
从第 0 秒播放到最后
故事完整
无缺失文件
无断掉的 timeline
声音基本可听
字幕基本可读
所有 Shot 有明确 asset 来源
```

只要达到这一点，就先输出第一版。

---

# 16. Reality Review

第一版完整视频必须至少完整观看三次。

### Pass A — Story

只检查：

* 是否看得懂；
* 节奏是否拖；
* Shot 是否过长/过短；
* 哪些镜头没有存在价值。

### Pass B — Visual / Continuity

检查：

* 人脸；
* 身材；
* 服装；
* 场景；
* 道具；
* 屏幕方向；
* 动作；
* 光线；
* 镜头连接。

### Pass C — Production System

检查：

* 哪些问题应该在哪一层修；
* selective rebuild 是否正确；
* 是否发生不必要的重新生成；
* 是否需要人工绕开系统；
* 是否存在无法追踪的 asset；
* 是否存在 silent fallback。

---

# 17. Per-Shot Production Record

每个 Shot 最少记录：

```text
shot_id
visual_strategy
continuity_mode
provider/profile（若使用）
generation mode
生成次数
最终 candidate
是否一次成功
失败原因
是否需要人工干预
是否存在 identity drift
是否存在 continuity defect
本地生成耗时
remote cost（如有）
最终是否接受
```

不要求为了记录这些数据新建第二套数据库。

优先使用当前已有 receipt / evidence / Manifest / logs。

缺失的数据可以作为单独 rough-cut report 汇总。

---

# 18. Failure Classification

发现问题后，先定位责任层。

例如：

```text
角色 reference 本身错误
→ Asset

Shot open/close state 错误
→ Shot / continuity

Prompt 运动描述错误
→ Prompt

正确输入但模型输出漂移
→ Provider/model

字幕时间错
→ Caption / timing

字幕位置错
→ Composition / renderer

改一个 Shot 导致全片重做
→ Dependency

QA 没发现明显错误
→ Review/QA
```

不得所有生成问题都直接归因于模型。

---

# 19. Repair Rule

第一版完成后，只修：

```text
阻碍观看
明显身份错误
严重连续性错误
严重声音/字幕错误
系统级错误
```

不要第一轮就追求：

* 所有表情完美；
* 所有镜头商业级；
* 每个转场精修；
* 所有镜头重新生成到最好。

优先完成一次：

```text
真实 defect
→ diagnosis
→ selective repair
→ rerender
```

闭环。

---

# 20. Architecture Freeze

本轮默认冻结以下能力：

* ProductionProject schema；
* Manifest schema；
* Registry layout；
* P5 dependency ownership；
* ProductionStateCommitter ownership；
* ResolvedTimeline ownership；
* HyperFrames default renderer；
* Shot Router Provider-selection boundary；
* H3 sealed technical/quality profiles。

只有真实 5 分钟生产发现阻断性 bug 时才允许修改。

修改前必须证明：

> 不修这个问题，rough cut 无法继续，或者会产生错误 production truth。

不得因为“以后可能需要”扩展架构。

---

# 21. Explicit Non-Goals

本轮不做：

* P9 全面生产硬化；
* Studio UI；
* 自动 Provider ranking；
* 自动 Provider fallback；
* 多 Provider 全面 benchmark；
* 全模型价格比较系统；
* Remotion 第二 renderer；
* 新 timeline；
* 新 Manifest；
* 新 Registry writer；
* 大规模 schema redesign；
* LoRA training pipeline；
* 自动生成完整商业级作品；
* 全自动无人值守生产。

---

# 22. Stop Conditions

以下问题不会阻止 rough cut：

```text
某个非关键 Shot 质量一般
Hailuo 不支持 R2V
部分 Shot 使用静态图
部分 SFX/BGM 不完美
少量镜头需要人工选择 candidate
```

以下问题属于必须修复的 blocker：

```text
无法生成完整 timeline
无法输出 final.mp4
production state 无法恢复
asset provenance 丢失
silent Provider fallback
重要角色 reference 被静默丢弃
修改单 Shot 导致错误 blanket rebuild
真实 Shot 无法进入 composition
严重 continuity state 无法表达
```

---

# 23. Acceptance Criteria

本轮通过需要同时满足：

## A. Deliverable

存在一份真实：

```text
约 270～330 秒
可完整播放
有画面
有语音
有字幕
的 final rough-cut MP4
```

## B. Production

证明至少使用：

* image/static lane；
* generated-video lane；
* voice/caption；
* composition/render；
* QA/review。

## C. Continuity

至少有一组真实多 Shot sequence，验证：

```text
Shot N
→ continuity
→ Shot N+1
→ Shot N+2
```

并人工检查角色/状态/动作连续性。

## D. Repair

至少完成一次：

```text
真实 defect
→ 定位
→ 局部修改
→ selective rebuild
→ final rerender
```

不得整部从零重做。

## E. Provider

H3 可以作为主要 generated-video lane。

不要求 Hailuo/Seedance 在本轮必须产生新媒体。

## F. Evidence

最终报告必须能回答：

* 总 Shot 数；
* 各 visual strategy 数量；
* generated-video Shot 数；
* H3 使用次数；
* remote Provider 使用次数和费用；
* 总生成次数；
* accepted candidate 比例；
* 最常见三类失败；
* 人工介入次数；
* 哪些地方发生 selective repair；
* 最终 5 分钟生产的主要瓶颈。

---

# 24. Success Definition

本轮真正的成功不是：

> “我做出了一部非常好看的 AI 短剧。”

而是：

> **AI-VIDEO 第一次证明自己可以组织真实 Story、Characters、Assets、Video、Voice、Captions、Continuity、Timeline、QA 和 Repair，生产出一部完整约 5 分钟作品。**

如果成片质量一般，但系统能够明确告诉我们：

```text
哪里不好
为什么不好
应该改哪一层
改完以后哪些东西需要重做
```

本轮仍然具有非常高的验证价值。

---

# 25. Next Decision

完成本轮后，再根据真实数据决定下一步。

可能包括：

```text
提高 H3 质量
增加 ref2va
使用更多 Hailuo / Seedance
改进 Character Reference
改进 Continuity
改进 Shot Router
加强 QA
优化 Image Motion
增加 Studio UI
进入 P9
```

但这些决定必须基于本次 5 分钟真实生产数据。

**在 rough cut 完成之前，不提前启动上述扩展。**
