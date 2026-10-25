---
record_kind: session_summary
topic_id: ad-creative-hook-product-direction
learning_eligibility: ineligible
---

# Ad Creative Hook And Product Direction

Date: 2026-10-25 (Asia/Hong_Kong)

## User Intent And Scope

用户要求“我需要把广告这层的内容skill固定下,前3秒夸张钩子,后面要有产品表现力”。这是一项直接授权的广告内容指导修订，不是重新生成视频、修改Drama层、Provider或Runtime验收的请求。

## Change

修改唯一内容owner `.agents/skills/ad-creative/SKILL.md` 及其 `references/strategy-and-hooks.md`、`references/video-creative.md`，替换旧的宽泛/条件式表述，入口描述也明确前三秒夸张钩子和产品视觉表达。新创作或获准整体重构的商品广告视频默认必须执行：

- 第一秒可读到异常/反差，前3秒用夸张动作、戏剧性反差或直观视觉隐喻形成事件，并建立使用问题与商品本体/动作的联系；包装并非唯一入口。
- 后续主体用可读本体与细节、关键使用/展示动作及反馈承载真实卖点；不给商品机械规定镜头数/露出占比，不以闪现包装和旁白铺满代替。
- 主要剧情、笑点或隐喻回扣真实商品/使用反馈，结尾兑现开头；场地是否变化服从连续性。
- 前3秒和后段分别按观众实际可见的信息复核。夸张不授权虚构功效，仍回填既有G2/G3/G5并沿原媒体review。

用户当次明确另定风格/忠实复刻时遵从；局部改色、字幕或指定片段修复不自动重做整片。未写入全局AGENTS、Drama或Provider Skill，未修改Runtime Gate/schema；既有 `runtime_skill_calls = 0` 与Product Truth职责保持。当前dirty的Ecommerce/共用导演文件由其它工作保留，没有混写。

## Verification

`skill-creator/scripts/quick_validate.py` 对最终Skill通过，owned diff whitespace检查通过。Parent以新剧情广告、只有末尾露商品、快闪产品加全程口播、只改片首颜色、用户明确要求克制品牌风格五种情境自审：前两类必须有实际商品因果与后段呈现；快闪/口播不能代动作展示；局部修片与明确另定风格保留原范围。此为作者判断自审，非独立Agent测试或真实媒体/营销效果证据。

使用exact staged scope，只含上述3个owned文件，未把整个dirty工作区当任务输入：

- 精准级receipt：`.agent/harness/runs/ad-creative-hook-product-focused-20261025/receipt.json`，PASS；docs contract及Harness相关测试321项通过。
- 相关级receipt：`.agent/harness/runs/ad-creative-hook-product-related-20261025/receipt.json`，PASS；包含scope/docs/rules/policy/runtime-skill boundary/Harness及规则invariants检查。提交前 `verify-receipt --require-level related` 返回 `fresh=true`、`integrity=true`、`complete_completion_proof=true`、`verification_level=related`、`full_regression_passed=false`。

没有运行full或生成媒体；不将相关回归称为完整回归或下条视频质量保证。实现提交 `8d268b251e6a1b0c7cfbaa218aadff758ee2e515` 仅包含3个owned Skill文件。

## Publication State

当前本地Skill已生效。修改开始时main已比远端main领先两个其他任务提交：`5daa3d6`、`136038a`。实际 `ls-remote origin refs/heads/main` 返回 `2d17c49e0f22ce2ffb44a713b25c81ef7a546aa6`，不是远端引用缓存误差。其owner记录 `2026-10-25-harness-three-level-verification.md` 明确full失败11项，保留未push/未合并/未发布的状态。

推送本任务当前main会一并发布上述已被明确阻断的外来提交，因此本任务仅提交owned变更，暂不push；不force-push、不重排/回滚他人历史、不为Skill文字修改扩围修复其Product失败。最小恢复条件是原owner关闭该发布阻断并整理可正常推送的main。此Git发布限制不妨碍当前工作区读取已修改的Skill；没有媒体发布或Production activation。

## Record And Learning

使用record-ai-video-session记录当前独立Skill任务，未改写热敷贴媒体的验收状态。distill-ai-video-learning评估no_candidate：用户直接指定内容偏好，不是跨独立实验的实证结论，不创建Learning Claim，也不宣称留存/转化提高。保留其他dirty/index工作，未调用Provider或媒体工具。
