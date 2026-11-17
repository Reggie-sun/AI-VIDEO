# Jimeng Seedance Gap-Driven Skill Candidates

## Scope And Method

检索日期：2026-11-16。先由历史审计定位即梦渠道的真实问题，再定向搜索动作因果、接点和声音衔接；不把 Ark/API 的 2.0/Fast 对照纳入即梦效果证据。历史具体输入、媒体和限制见同日 [history](2026-11-16-jimeng-seedance-history.md)。本页只是来源核验与候选建议，不是 Learning Claim 采纳、模型效果排名或新的生产 owner。

搜索起点：颜生源 `seedance_2.0_vip` 拿瓶/持瓶接点；失帧即梦2.5支撑消失后道具悬停、纸的消失/重现、重复笑声和后续真人版重复扫码。需要的是定位失败所在状态和已完成事件，而不是继续堆砌形容词。检索词分别围绕 Seedance motion/contact、continuation handoff/completed beats、match cut/audio、physics failure，未先安装合集。

使用 GitHub API 解析每个仓库默认分支的 full SHA，再按该 SHA 下载正文和 LICENSE 到临时研究目录，阅读后记录证据。未安装 Skill、执行上游脚本、更新本地固定副本或发起生成。以下决定是供主会话裁决的建议；正式经验采纳遵守现有 exact confirmation 流程。

## Official Capability Boundary

[Seedance 2.0 官方发布](https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0)（2026-02-12）介绍多模态参考与复杂互动；[2.5 官方发布](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)（2026-07-31）介绍30秒、运动/白模参考和长叙事，并列出即梦上线入口。它们是模型级发布陈述，不能证明当前账号的模式槽位、项目 adapter 支持、Fast/Mini 能力或历史片段的质量。本文不据此承诺物理、接点或声音一定正确。

## Candidate Findings

### LearnPrompt — Keep Existing Pin

核验 `LearnPrompt/awesome-seedance@abcf369603f120db13bfe843a7d0ec3b2862a857`，MIT。实际读取 [workflow L10–39](https://github.com/LearnPrompt/awesome-seedance/blob/abcf369603f120db13bfe843a7d0ec3b2862a857/agents/skills/seedance-production-workflow/SKILL.md#L10-L39) 与 [QA L1–15](https://github.com/LearnPrompt/awesome-seedance/blob/abcf369603f120db13bfe843a7d0ec3b2862a857/agents/skills/seedance-production-workflow/references/qa-rubric.md#L1-L15)。它已有接触点、入口/出口、运动参考、逐时间点失败和有界修复指导；QA还要求事件只出现一次。

两份正文 hash 与本地 `open-video` 固定副本完全相同，因此更新整个仓库没有为这些历史缺口带来新正文。建议 **保留** 本地 pin `67df3707a4f25f860088790fb0a74d8f99a50cbb`，把真实案例接入离线评测。上游评分与 run-manifest 指令仍由现有本地映射隔离，不导入第二状态机。

### Scenario — Keep Scoped Adapter

核验 `scenario-labs/skills@a14d061fe5db33d339b1d89f775f37337481295f`，MIT。读 [storyboard L1–132](https://github.com/scenario-labs/skills/blob/a14d061fe5db33d339b1d89f775f37337481295f/skills/scenario-seedance-storyboard/SKILL.md#L1-L132) 与 [chained-lane L1–86](https://github.com/scenario-labs/skills/blob/a14d061fe5db33d339b1d89f775f37337481295f/skills/scenario-seedance-storyboard/references/chained-lane.md#L1-L86)。后者 hash 与已集成副本相同；相邻边界姿态和位置检查已经存在。

建议 **保留** 当前 `scenario-seedance-storyboard` 适配，不再新增同类 Skill。上游把共享边界帧描述为连续动作保证、带 Scenario `model_run`/schema字段及无人值守继续流程，不可直接用于即梦。首尾姿态一致不能证明中间接触、加速度或掉落时间正确。新增运动参考若确有必要，应由现有 reference owner 准备并验证，不把静态边界链升级为物理成功证据。

### LeoYeAI — Narrow Advisory Candidate, No Router Import

核验 `LeoYeAI/seedance-skills@797e16efaa3c5ac01c0e391d0b8466a87cc5aadc`，MIT。motion frontmatter 自报6.6.0、2026-07-04，且指向 Emily2040 上游；因此这是此 fork 的固定快照，不等同原作者最新版本。

实际读 [motion L25–68](https://github.com/LeoYeAI/seedance-skills/blob/797e16efaa3c5ac01c0e391d0b8466a87cc5aadc/skills/seedance-motion/SKILL.md#L25-L68)、[handoff L5–75](https://github.com/LeoYeAI/seedance-skills/blob/797e16efaa3c5ac01c0e391d0b8466a87cc5aadc/references/continuation-handoff.md#L5-L75)、[retake L5–49](https://github.com/LeoYeAI/seedance-skills/blob/797e16efaa3c5ac01c0e391d0b8466a87cc5aadc/references/retake-protocol.md#L5-L49)。有价值的窄参考是把可见作用力/结果分开，以及把已完成动作、未完成运动、对白和声音阶段写入交接。可针对重复扫码/笑声设计离线反例。

但项目已有 intent/reference planning 和接点 owner；不能引入该库的 sequence canon、路由、默认预算或反复重抽规则。其“数次失败即可认定 prompt 有问题”、固定 fast 草稿数及“接受偏差”不能成为本项目事实或 Gate。建议 **仅保留候选链接**；若案例证明缺口，再给 `open-video` 提出窄 advisory 增补，禁止给 `seedance-authoring` 加第二轮导演改写。

### DirectorSKILL — Diagnostic Reference, Reject Blanket Rules

核验 `wuwangzhang1216/DirectorSKILL@c65ae0d14457053efb1e354c7e7f7e120d97fad1`，MIT。读 [F14 physics L427–444](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/failure-modes.md#L427-L444)、[F19 permanence L509–529](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/failure-modes.md#L509-L529)、[editing L147–217](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/editing-and-assembly.md#L147-L217)、[prop handoff L299–385](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/continuity-bible.md#L299-L385)。有具体症状、接触/持物状态例子，适合帮助区分道具悬停、遮挡后丢失、接点状态跳变。

建议 **不安装独立 Director**。切走接触、把后果放画外可能删除用户要求；固定丢弃片头/尾、强制运动重叠/景别变化会破坏既有成片。其原因排序、像素/时长阈值和“失败几次必拆镜”均不是当前即梦实证。仅作为定位用术语参考，所有方案回现有 Director 保留创作意图后裁决。

## Evidence Fingerprints

所有上述仓库均读取对应 SHA 的 LICENSE，内容为 MIT。未复制上游正文进仓库；如果后续经确认 vendoring，需保留原许可并固定 hash。

| Repo / source | SHA-256 of inspected bytes |
| --- | --- |
| LearnPrompt workflow | `b40482f047a3463cd9a4c7cb4fcbf65997b6ae12d35b67d6187334c458ff0ef4` |
| LearnPrompt QA | `1e85bff0411091782e47364280b6980744a865ea00b01c6b941d1f818b2a79a8` |
| Scenario storyboard | `4df04db278e4198d8875f9b13ac4dfda04c58ffd298d94b8f8a1ce418ad69008` |
| Scenario chained lane | `9e4e934ccacb6a4de2b0ea514f39001fec3449d915f5db9802073a4188396bf8` |
| Leo motion | `29dcb5b1718fe9742fea8498da3b468f47309d595ad56c9c62d65edccdbf52c7` |
| Leo handoff | `c7c24f8079639cfdf7431efe06cb14bc0384862e85e473126525e9603ed0ee50` |
| Leo retake | `c85ec247c18d27ff0ce69eaeb05504fb33d306283e377847e5ef06bf05ee7183` |
| Director failure | `9a374e78ac8257ed8c91d7c247ebc2f1d27a3484b0c1486fee7d77e554fb9be7` |
| Director editing | `8256bb843e8d45ba66aba927edef30cd586a0a32030e4a4639d26be156e850de` |
| Director continuity | `92aad85488aee0fcad6d432ce29f66286d66245bb2a17499a325afb356c74826` |

## Integration Decision And Validation Limits

建议本阶段 **零新增可发现 Skill、零替换 owner、零自动更新**。已有缺口首先是历史输入/出片/用户反馈没有成为可重复检查的失败案例，而不是缺少第四套导演模板。优先新增历史证据 fixtures、固定输入的离线回归、按精确渠道/版本/模式过滤历史经验；具体实现由现有 owner 负责。

待真实验证假设：状态图或连续运动参考是否改善支撑消失后立即掉落；观察末态与已完成事件交接是否减少重复扫码/笑声；针对拿瓶过程的参考修正是否保住原动作而修复接点。静态结构和 Mock 只能证明拒绝遗漏/错配，不能证明模型遵从。没有受控 A/B，不报告成功率、成本或版本优劣；本页没有批准任何新生成。
