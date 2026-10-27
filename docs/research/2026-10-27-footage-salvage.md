# Footage Salvage Research And Architecture Audit

## Source Snapshots

2026-10-27 通过 GitHub connector 读取下列 immutable revision 的原文；外部 Skill 仅作为研究材料，未安装、运行或赋予 Product authority。

| Source | Read | Adopted | Limits / Rejected |
| --- | --- | --- | --- |
| [video-production-skills@8114070](https://github.com/konradre/video-production-skills/tree/8114070bbeca9ab07a00c5ab27daca49cc42c701) | `video-take-review/SKILL.md`、ACCEPTANCE-MATRIX；`video-edit-edl/SKILL.md`、EDL-CONTRACT；`client-rounds/SKILL.md`、ROUND-PROTOCOL；`video-gen-cost-gate/SKILL.md`、COST-AND-GO | 原素材身份、每 Take 独立观察、可用窗口、故障位置、先查已有版本、已通过内容保护、每个否决原因、局部 render 与生成分账 | 原资料中的像素/语速/固定尝试数是特定制作经验；不采用固定像素门槛、每次重新询问付费许可、全 Take 永久 VOID、不受约束的 fail override 或自动 provider 切换 |
| [DirectorSKILL@c65ae0d](https://github.com/wuwangzhang1216/DirectorSKILL/tree/c65ae0d14457053efb1e354c7e7f7e120d97fad1) | SKILL 的 QC/repair 路由、failure-modes、editing-and-assembly | 从具体失败定位因果；表面问题与动作/末态/空间问题分开；反复同类失败重新设计；补反应/结果/插镜作为待验证替代表达 | 不采用固定首8尾12帧盲裁、缺陷少于8帧自动遮盖、超过半条自动重生成、固定变速范围、两次失败即“确定性”的断言；“剪辑不会破坏邻镜”和插镜必然抹除观众空间记忆均不成立 |
| [OpenFilmQA@f313679](https://github.com/BaoPham9x/OpenFilmQA/tree/f3136797fe3edadc16eacd225a3508329f28533c) | SKILL.md、docs/review-contract.md、openfilmqa/repair.py | 原始 intent 不变；动作、完成与接点必须连续审片；声音独立审听；前后 exact hash、邻镜复查、遗漏项保持 unreviewed、新缺陷算回退 | 其 supplied attestations 校验不证明模型/人确实看懂；本项目复用既有 selected authority、P6 request/receipt、Registry 和 Manifest，不能直接导入其 release 状态或第二 review pipeline |
| [narrative-film-direction@4ee8b42](https://github.com/Nagacash/narrative-film-direction/tree/4ee8b42484cb57407f4a7772216aa79e20b0971f) | SKILL.md、references/editing-grammar.md、coverage-protocol.md | 轴线/视线/首尾状态、对白 J/L cut、覆盖目的、节奏服务情绪、停顿不自动缩短 | 不采用必做 master、至少五机位、每段5–8秒、每段只能一个动作、统一首尾裁4帧或每接点叠化；能力须基于当前模型及本片实测 |

## Current Architecture

| Surface | Existing Owner / Evidence | Gap Closed Here |
| --- | --- | --- |
| Director / production design | `Shot.production_intent`、`ProductionCoverage`、`ProductionUnit`、`domain_acceptance.production_allocation_issues` | 保留全部事件、组件与 assembly 职责；不另建 Director |
| Take / asset / versions | Registry `AssetRecord`、metadata、creation receipt；`ProductionSourceOption` | TakeAssessment 补完整时长、七维观察、故障/可用/保护区间、首尾状态、替代素材 |
| QA / source qualification | `SourceUseEvidence` 精确用途和 selected authority | 额外要求有时间连续性的完整原速声画证据；抽帧无法证明动作或因果 |
| Selection | `ProductionStrategyResolver` 的真实组合枚举与 v2 evidence-first | 原 candidate 加 semantic blockers，风险用偏序比较，不平均分；报告解释每个候选 |
| Execution / EDL | `ProductionPlanningService`、materialization、`ResolvedTimeline`、HyperFrames | 绑定 salvage review/plan 到原 child lineage，执行及 composition 重验，零新 writer/timeline |
| Continuity / scene | `junction_review`、`canvas_review`、`FinalOutputContract` | salvage 的接点/场景要求在原 P6 强制完整原速声画，不从 Take PASS 推导 Scene PASS |
| Retry / recovery | canonical `GenerationExperience`、`diagnose_exact_result`、Generation feedback | distinct request 的重复同类失败转 NEEDS_REPLAN；原 UNKNOWN/recovery/count/permit 保留 |
| Repair comparison | `record_approved_repair_receipt`、`record_repair_outcome`、`require_no_regression_outcome` | 复用冻结基线、新输出全部 fresh required layers 和不可抹去的失败历史 |

## Adopted Rules

1. 质量资格先于成本；候选必须解释原要求、观察、保留区间、受影响镜头和未解决事项。没有观察不是失败证明，更不是重新生成理由。
2. Take 观察在所选 QA policy 中保存；素材 bytes、版本与时序仍引用 Registry/原 source-use。帧区间使用 `[start, end)`，不从 nominal FPS 猜实际帧数。
3. TRIM 可以删除已定位局部失败，但不能删除保护区间、保留失败区间或用切点冒充未完成的必需动作。替代表达通过 authored coverage/allocation，再由新成片 Scene QA 验证。
4. 七维逐项审查，不用美观平均掉动作、因果、身份、表演或剪辑可用性。genre/scene intent 保持显式，悬疑等待可成为保护事件或保护区间，不设通用时长裁切规则。
5. 十类 repair 标签可以组合；具体 executor 以现有 ProductionOperation/adapter 能力为准。未支持的 V2V、mask/tracking 等返回 capability gap，分类不等于承诺任意后期能力。
6. Provider、local render 和时间估计分别保留范围、单位与依据，unknown 原样保留，不编造成功率，不互换货币，不从估计铸造 paid permit。
7. 全部可行剪辑/复用候选优先；仍有未审的低生成候选时补证，不花费掩盖证据缺口。可行候选内只用逐维风险偏序；不同风险或 unknown 不能比较时返回 unresolved。
8. 生成仅替换被选 coverage 的缺失组件；对全场的失效传播继续由原 P5 resolver 决定，不 blanket invalidation。连续同类失败必须更新 Shot/覆盖设计，历史计数不重置。
9. 候选只能成为 EDIT_CANDIDATE/NEEDS_GENERATION/NEEDS_REPLAN 等；`VERIFIED` 只能来自同一实际物化方案、当前 exact render 与原 P6 acceptance 链。前后投诉消失不足以证明修复。

## Evidence Boundary

本任务的 fixture 观察明确用于软件边界测试；未运行收费生成、未对任何现有作品补签 PASS，亦不声明真实影片或人工验收。真实使用时必须由有能力的 evaluator/人输入连续声画观察，并沿项目 MCP gate、P6 和原速审看完成验收。
