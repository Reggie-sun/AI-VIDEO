---
record_kind: architecture_implementation
topic_id: canvas-current-input-control
learning_eligibility: ineligible
---

# Canvas Current Input Control

Date: 2026-10-20

## Problem And Scope

用户明确要求修复上层控制层。原[上传画风试片](2026-10-20-jieshi-3d-anime-minimax-test.md#uploaded-style-s01-actual-result)的实际native preview含6,224字符，素材职责三段、美术方向两段，旧四秒与新五秒白模说明共存；只更新两位核心人物图，其余参考保留旧风格。源码核对表明上层操作把历史说明追加进新source，现有preserved-source compiler按合同逐字发送，并非Planner或Provider自行添加这些文字。此为已知输入问题，不将单次多变量生成解释成已证明的模型失败机制。

本轮只修复共享Canvas上层authoring、reference preflight和prepare/start输入一致性；不新增作品执行链、Provider、Production schema、timeline、renderer或writer。原文compiler的逐字/引用校验、历史付费次数与unknown规则保留。没有新的图片、视频、音频Provider调用，旧试片仍为`video_quality_rejected`，未取得原速完整视听或用户风格验收。

## Implemented Contract

`canvas_source_revision`校验显式完整当前sections及上一版parts逐项`retained/superseded`处置。baseline从标准loader的canonical director input按Shot ID重开，改Canvas节点名不重置历史；已有Shot改原始prompt、有效Shot.intent或preserved source expression（含移除）即需声明，不因省略visual-style字段绕过。当前sections须逐项匹配本次inspection，observed无parts原文按单个text part列入；baseline同时绑定原始parts及有效intent/expression，legacy无保留表达式时还包括typed GenerationIntent，旧revision不能绕入改稿replay快捷路径；旧段落标记被替换后仍完整存在、漏处置、stale SHA、重复section或未声明追加均拒绝。历史保留在既有immutable authoring input，不流入新native prompt。已批准版本可重开/exact replay；后续修订不能静默丢掉已启用的source/style控制声明。检查不自动改写原文，也不代替Agent对剧情、声音和已满足项的语义审核。

`canvas_visual_style`绑定实际selected Registry图片作为style anchor，每条选中图片按asset/SHA/role/owner及当前anchor SHA审查，包括人物辅助图和场景；typed offscreen角色沿原表演契约。全镜`whole_shot`不允许旧风格`identity_layout_only`例外冒充全量；明确混合路线必须填写范围和理由，报告`PARTIAL_REFERENCE_STYLE`。完整端点图可声明其实际审核的`covered_owner_ids`，不强制换成多图路线。图片是否真的匹配目标审美仍为`NOT_EVALUATED`，不能凭SHA或文字声明推出图像质量。

现有`author_canvas_project`、service `_load`、preflight、prepare/repair及start前接入同一校验。prepared barrier逐项核对实际requirement image evidence、resolved image bindings及native scope，缺图、换图、额外未审图、owner漂移或scope未表达时在创建生成attempt前停止。声明随原director provenance保存；legacy未声明仍兼容但报告`NOT_DECLARED`，Agent处理新的明确画风变更必须使用新契约，不借兼容入口跳过审查。功能入口、操作方式和边界只由[工作流](../canvas-production-harness.md#current-inputs)维护。

## Verification And Evidence

先运行public authoring/preflight回归确认RED，再实现GREEN；使用真实fixture PNG、标准Project loading/committer和现有Planner/Router/compiler，Provider transport/credential seam禁止执行。覆盖当前稿替换旧4秒/画风指令、历史保留、canonical revision/reopen/idempotency、坏声明写前拒绝、完整/缺失/陈旧引用、whole-shot/mixed分流、offscreen与frame coverage。

Seedance与MiniMax H3 Max均验证真实离线prepare能携带全部审核图。另只注入缺图的compiler结果，实际application prepare/start均返回typed input error，Manifest bytes保持不变；不是用mock成功冒充Provider或媒体通过。H3测试首次因fixture未显式声明adaptive output而被原capability门拒绝，修正测试输入为既有5秒adaptive契约，无Production逻辑放宽。

当前source revision回归22项通过，完整focused组合最终以Harness为准；原nominal十五秒示例的两条路径、原导演intent修订的两条路径在补齐修订声明后继续通过，重复引用/tray-only及实际compiler断言保留。较大focused回归曾通过178项；最终shared Canvas checks以exact staged Harness为准：`.agent/harness/runs/canvas-current-input-control-20261020-r9/receipt.json`。policy只将新增回归加入原Canvas suite/path routing，没有删旧检查或刷新Architecture baseline。该凭据仅为工程验证，不代签画风、动作、倒影或成片。

## Review And Publication

Risk Gate为`NATIVE_REVIEW_REQUIRED`：该修复约束后续付费生成的上层输入，跨source revision、引用覆盖与实际编译绑定仍有语义审查价值。首轮review发现并确认`CIC-001`：仅比parts会放行直接改Shot.intent/移除原文表达以及observed无parts改稿；先用public author/revise回归确认RED，再补有效prompt基线、observed inventory、superseded原文不能从有效intent回流及replay条件，19项source回归GREEN。第二轮继续确认同类CIC-001的typed GenerationIntent入口以及CIC-002的rich-source handoff兼容缺口；补动作/表演单改与replay回归，handoff在Registry commit前由既有owner生成retained inventory，22项source回归GREEN。新增rich-source交接/replay集成测试通过；更换参考后旧画风review失效的路径也先RED再修复为Registry commit前阻断，Manifest bytes和service direction保持不变。前两轮证据保留在r7/r8目录；最终候选的native profile、exact staged tree/file hashes、轮次、findings和Parent裁决记录在r9目录的`native-review.json`；不将实现worker等同独立reviewer，不以静态审查代替实片验收。

`record-ai-video-session`评估record；自动`distill-ai-video-learning`为`no_candidate`。这是用户明确授权的确定性缺陷修复，没有新的受控媒体比较或可推广模型质量结论，不自动修改Skill或全局memory。publication范围仅为本任务owned代码、测试、contract/workflow和本记录；commit/push及remote SHA按当前repository规则核验，所有foreign dirty路径保留。

## Remaining Boundary

新契约验证明确声明及最终输入身份，不能自动发现未声明legacy自然语言里的全部矛盾，也不能核验图片审美或保证生成时不多手、不串道具、不补倒影。下一次真实试片须重新准备并实际查看一致参考和完整当前稿，沿原授权/预算与逐镜媒体Gate执行；本轮工程通过不会恢复旧permit、退回预算或自动提交新片。
