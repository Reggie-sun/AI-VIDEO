---
record_kind: session_summary
topic_id: physical-action-description-constraints
learning_eligibility: ineligible
---

# Physical Action Description Constraints

用户直接要求“这是skill层面的缺陷,对于描述的约束,修改”。本次是明确授权的作者指导修订，
不是从单个失败自动采纳模型效果规律；不修改 runtime、QA 标准、预算或既有 sealed 输入。

真人 S03 attempt-003 已实际生成并 fetch，SHA `fb70d66ac802ed1133afffae2b9f4af8b9be0be0493bc2b3119be9866f632c28`。
实际输入写了略倾持瓶、放稳承重后松手、消失后瓶子不动和枪立即下落，但没有明确退手及枪的
落点/路径与瓶子的避让。结果未清楚完成落瓶过程，随后瓶子被带倒；这同时包含已有指令未落实，
不能认定遗漏是唯一根因。证据在 `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/S03/`
的 `native-prompt.txt`、`fetch-output.json`、`post-media-observations.json` 和 `observed-props.png`。

`open-video/references/event-led-timing.md` 拥有条件性的物理动作因果检查；
`seedance-authoring/references/authoring-common.md` 引用该 owner 并要求保留到 actual native preview。
`open-video/SKILL.md` 增加条件入口，已有时长无需修改时也加载该约束。
不规定固定时长、坐标、通用落物方向或每镜必填模板，不声称静态文字检查能保证生成物理正确。

Parent Risk Gate：`NATIVE_REVIEW_NOT_REQUIRED`，局部可逆 Skill 文本改动，无执行/权限/持久化逻辑变化。
学习评估 `no_candidate`：无受控补写前后生成对比，不提出普遍效果结论。本轮没有新增生成或拼接；
新 Shot 3 仍未获用户认可，后续拼接等待用户明确点头。

## Verification

两项 Skill 测试共 56 PASS，docs contract 检查通过；focused Harness 中通用 Harness 测试
319 PASS / 2 FAIL：既有 dirty policy 缺 `authored_visual_revision_tests` 的 full coverage 登记，
以及其他未映射源码路径；未为本任务改写共享 policy 或掩盖这些失败。
focused receipt：`.agent/harness/runs/physical-action-description-focused-20261026/receipt.json`。
关联验证另见 `.agent/harness/runs/physical-action-description-related-20261026/receipt.json`；
本记录不将局部 Skill 通过声明为整体 Harness 通过，也不证明新规则改善实际生成效果。
