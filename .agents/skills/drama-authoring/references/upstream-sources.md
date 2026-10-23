# Upstream Sources

## Pinned Sources And Local Rewrite

本技能使用公开仓库方法作研究来源，本文由 AI-VIDEO 独立中文改写，不复制其 SKILL 文本、schema、模板、脚本、范例或项目状态。下列链接固定到核对过的 commit，便于审查来源与改写边界。

| Source | Rewritten methods | What is excluded |
| --- | --- | --- |
| [zenstory-ai/drama-skills · `fdb7b7c58017e3eae64eca382c2a85ede368dab0`](https://github.com/zenstory-ai/drama-skills/tree/fdb7b7c58017e3eae64eca382c2a85ede368dab0) | `short-drama-develop`：故事承诺、人物动机、分集进入/退出状态；`short-drama-write`：因果行动、对白目的、听者反应和适用范围内稿件检查；`short-drama-review`：按证据定位问题 | 自有项目目录、五份 Markdown owner、JSON/status ledger、Dashboard、脚本/自动化、阈值和验收状态 |
| [eternityspring/shuohao-skills · `d28a9c539b40523d081794b25ff9113016bd98e0`](https://github.com/eternityspring/shuohao-skills/tree/d28a9c539b40523d081794b25ff9113016bd98e0) | `novel-characters` / `novel-art`：有用的角色、场景、道具视觉锚点；`novel-staging`：一场的开场位置提案 | 上游脚本/UI/JSON、英文 prompt 强制、时代/集数/道具数等猜测或固定配方、完整 outline→script→storyboard 管线 |

许可证副本：

- Zenstory MIT：[LICENSE](../licenses/zenstory-MIT.txt)
- Shuohao Apache-2.0：[LICENSE](../licenses/shuohao-Apache-2.0.txt)，[NOTICE](../licenses/shuohao-NOTICE.txt)

本技能只采纳可独立表达的方法。若未来复制或分发上游受许可作品的实质文字、素材或代码，应重新核对确切文件与适用通知，不能把此方法改写记录当作复制授权。

## Local Authority

- 剧情语义与 authoring rubric：[accepted Drama spec](../../../../docs/superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md)。
- 唯一镜头创意与调度整合：`open-video`；能力和语义交接见其 [专业模块路由](../../open-video/references/professional-specialists.md)。
- 模型语法与素材职责：仅在 Shot 已批准、exact model/version/mode 已选择后走 `seedance-authoring` 的一个 version overlay。
- Exact 媒体、项目状态、QA 和最终验收：AI-VIDEO 的 canonical owners 与 HUMAN evidence，不属于本技能。

仓库中的跨短剧方法和边界独立重写自上述固定版本，不能作为它们上游自测、生成能力或 AI-VIDEO 成片质量的证明。
