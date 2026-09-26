# Creative Completion Loop

## Goal And Root Cause

将用户要求的成片目标贯穿创作、审片、修复和交付，适用于广告与电视剧。已知问题不得因技术 PASS、复用素材或“预览”名称被当作任务完成。

直接反例是 `f8f775e4357d4ec8030142f93e8f07d2631d370884e4717ff97f35d42353c6ce`：青颜六秒样片技术渲染成功，但没有完整创作目标和交付前导演复核；parent 随后承认包装文字错误和广告表达不足。现有 `AGENTS.md`、Director Coverage v4 与 Final-output-first 已有规则，问题包含 Agent 未执行规则，不能伪称只修一个 Python bug 就解决审美。

当前 `scripts.visual_quality_report.prepare()` 只生成五项视觉合同；完整叙事、音频、表演或商品要求无法原样进入该开发报告。正式 Production Review / Final Acceptance 已有完整合同裁决，不能新增第二套验收 owner。

## Scope And Owners

- Native Codex 继续拥有任务 lifecycle、导演判断和最终交付责任。
- `open-video` 的局部 reference 承接创作完成实践；playbook 仅声明必经入口。复用素材的重剪、字幕和配乐也是创作，不能按纯 render execution 豁免。
- `scripts.visual_quality_report.py` 增加可选完整 `FinalOutputContract` 输入，复用 `adjudicate_final_output`，不增加评分器、Production state 或 acceptance authority。
- 既有 `visual-review-packet/1`、Python positional API 和视觉专用行为兼容；新完整合同 packet 使用 `/2`。公共 `ai-video` CLI、Production schema、writer、renderer、timeline、QA 语义不变。

## Creative Behavior

制作前将用户原意、Agent 的创作选择和最低质量要求分开记录。以现有 Director v4 intent / coverage、Story / Scene / Shot 与 QA-owned `FinalOutputContract` 表达，不另建 creative schema。每个段落说明观众需要理解或感受到什么，以及镜头、表演、声音怎样完成它；允许有理由的静止、重复、长镜头与留白，不能强迫三镜头或统一节奏。

广告按具体目标评估商品可信度、信息表达和期望行动；品牌氛围片不强制购买理由或 CTA。电视剧按具体场景评估人物目标、行动/反应、关系或情绪变化、空间和视听连续性；不套营销模板。不因素材易用反向缩小用户目标。

交付前在新的评审上下文中对原目标和 exact 成片复核；不能只提供作者的解释或技术成绩。独立 reviewer 提供证据，Parent 裁决，不接管 Production acceptance。没有看/听的项目保持未评估，AI 不填写 HUMAN。发现缺陷先诊断并在原授权和有限预算内修复；不允许删除要求、换目标版本或仅换文件名消除失败。

已知失败素材可以为诊断或征求具体反馈而展示，但必须明确失败项、未完成状态和下一修复动作；不能把分享失败证据说成完成作品。缺少人类最终审美反馈不阻止诚实展示候选，也不能让 Agent 将基础质量检查转嫁给用户。

## Local Report Contract

`prepare(..., final_output_contract=None)` 保留旧行为；传入完整合同则在任何 probe、抽帧或 output mkdir 前，验证其中五项视觉要求与显式 direction 的完整定义完全一致，额外 requirements 原样保留，不按维度过滤。新私有 CLI `--contract` 可传同一合同 JSON，`--direction` 与 `--content-kind` 继续必需。

完整 packet `/2` 保存 caller 的原 `goal_id`、`goal_version`、`user_goal`、requirements 与 hash；reopen 校验版本、完整五项视觉维度及 kind-specific ID，允许无 visual_dimension 的额外要求。旧 `/1` 仍仅允许原五项。所有 finding 必须命中完整合同，缺项仍由同一 adjudicator 判 `NOT_EVALUATED`，任一有效 FAIL 阻断整体 PASS。HTML 展示全部要求与原用户目标，非视觉项用 requirement ID 作标签并转义。

结果明确标识 `review_scope=visual_only|full_contract`；这仅说明输入覆盖范围，不代表 Production acceptance 或语义完整性。工具不能证明 caller 提供了全部用户要求、评审者真实观看、AI 判断正确或任意聊天/脚本已执行本工具；这些限制必须显式保留。`prepare` exit 0 只表示准备成功，不能当作审片 PASS。

## Acceptance And Verification

1. 广告与电视剧参数化反例：五项视觉全部 PASS，但额外商品/叙事项 FAIL 时整体 FAIL，缺项时 NOT_EVALUATED。
2. 完整合同身份与内容原样 round-trip，HTML 呈现额外要求和原目标；视觉定义不匹配在任何媒体副作用前拒绝。
3. 旧 packet/API 与 cross-genre、换片/换帧、stale answers、human proof 回归全部保留。
4. 对 exact 已失败青颜样片用现有合同模型记录事后诊断要求与实际可观察缺陷，不能伪称原渲染前已封存合同或人类已观看。验证它不能仅靠原技术 PASS 获得报告 PASS；不重新生成媒体。
5. 广告/电视剧的创作完成实践和 caller 限制明确；最终 implementation review 不能把文档或程序检查当作主观质量成功。

## Out Of Scope

不新增模型、Provider、remote call、音视频生成、自动发布或 runtime acceptance gate；不修改已封存旧 render/QA；不承诺每部作品自动好看。目标是减少已知缺陷放行与目标替换，并给出可复查的完成依据。
