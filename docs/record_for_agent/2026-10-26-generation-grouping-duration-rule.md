# Generation Grouping And Duration Rule

Date: 2026-10-26

## Diagnosis And Scope

用户指出Seedance 2.5支持30秒，却持续生成短片，并明确要求“这个正在生成的不用管,这个时候你先把规则改了”。本轮只改规则，不继续审片、合成、生成或修改已封存的视频请求、profile、历史与预算。

当前`jimeng_models.py`对`seedance_2.5`声明max_seconds=30；原整集`director-coverage.json`为31个unit、合计276秒，现有S03实际请求`effective_output.duration_seconds=10`。短片是作者规划及请求主动选择，不是Provider把长请求截短。既有原则已区分摄影镜头与生成片段，但旧短段时长仍被直接沿用，遗漏了独立生成分组的判断。

## Rule Change

在AGENTS现有一句原则中明确：摄影先服务叙事与表演；生成另按完整行动反应和模型能力分组定长，不默认短段或一镜一段，也不强凑模型上限。保留修复已满足效果及不冻结机位剪辑的原意，未改变真实验收、预算或执行准入。

`open-video/SKILL.md`将Event-Led Timing的触发从“时长尚未决定”扩展为“选择或修订生成分组/时长，包括复用已有短时长coverage”。原`event-led-timing.md`增加分组职责：连续行动、倾听与回应优先保持完整；一个生成片段可含多个摄影切镜；旧8–10秒、试片长度、API默认值不是常规上限，模型最大时长也不是必须用满的目标；原作者稿应说明覆盖过程、切镜、交接与定长理由，并核对实际请求。沿现有Shot/authoring/settings，不新建时间线或分组runtime。

## Verification And Limits

Skill quick_validate通过；open-video、Seedance authoring、docs contract与agent rules四个相关测试文件共123项通过。AGENTS为13,997 bytes，保留14,000-byte上限，无放宽预算或以测试模拟审美证明。Parent按两个反例自查：完整对话与反应可在一个较长片段内切镜；短暂证据插入仍可用短段，无需凑满上限。这是规则语义检查，不是新片效果验证。

本轮policy-audit实测仍列出既有八个未映射路径、其中四个未登记测试（Jimeng qualification trial、preview source clock、qualification preview input、watermark preset）。相关policy与这些路径未在本轮修改；不为消除baseline失败扩围或放宽Gate。本轮exact staged related Harness receipt入口为`.agent/harness/runs/generation-grouping-duration-rule-20261026/receipt.json`；按其实际结果报告，不能把直接测试通过说成完整Harness通过。

本轮规则修改没有新增Provider/生成/分析付费调用、没有发布。用户指示前已有S03首发结果只保留，不在此规则修改中改判为合格或继续处理。record-ai-video-session评估为recorded；distill-ai-video-learning为no_candidate：本轮是用户直接授权的原则与Skill路由修改，不是独立重复媒体实验或自动学习采纳。Parent Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：仅现有advisory规则与引用更新、可逆且无runtime/权限/预算变更，已执行对应检查。
