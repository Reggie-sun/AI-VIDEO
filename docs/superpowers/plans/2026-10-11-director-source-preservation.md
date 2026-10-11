# Director Source Preservation Plan

## Goal

按用户本次“修改”授权，修正 Director routing：已有画布/原 prompt 的复刻先保持生成输入，
新创作或已授权优化进入 Director design；已知失败只做对应范围内的 repair。

## Scope And Owners

- `.agent/context/control-plane-playbook.md`：请求目的分类与最小 routing pointer。
- `.agents/skills/open-video/SKILL.md`：Director 核对、优化、修复的 advisory 边界。
- `.agents/skills/seedance-authoring/SKILL.md` 与 `references/authoring-common.md`：保留来源输入、技术适配与 native prompt 边界。
- `docs/agent-primary-contract-matrix.md`：同步既有 surface 的 owner、invariant、禁止旁路及验证边界。
- 既有 Skill tests：保持结构/来源/约束/strategy 验证；仅同步已改变的 routing 文案契约。

## Contracts And Invariants

用户选定的完整来源方案与“尚未导入 approved Shot”的技术状态分开；后者不自动授权优化。
复刻保留原文、参考职责与顺序，转换 Shot Contract 时保持语义；缺证据、冲突或不能无损表达时报告缺口。
新创作继续遵守 Director Coverage v3/v4 validator；本次不修改该 schema，也不引入 Product runtime Skill 调用。
repair 绑定已知失败、完整目标与已满足部分，展示最小差异，不因失败默认重新创作。
内部 enums、验证记录、完整 contract 序列化不直接拼入模型 prompt；实际提交输入核对 source/diff。
Provider/model/参数、预算、egress、凭据、permit、唯一 committer、unknown fail-closed 及媒体 Gate 保持。

## Out Of Scope

不继续未完成的 paid-retarget 代码，不生成视频，不改旧 attempt、历史 receipt、Learning Claim 或既有 source snapshot。
不把该规则修订当作 prompt 质量结论；旧片 POV FAIL 保留。

## Acceptance And Verification

1. routing/两项 Skills/matrix 对复刻、新创作和已知失败修复的边界一致，来源保留不会绕过 canonical Shot/Provider gates。
2. 新创作仍有结构与 verbatim source 验证，原样复刻不被重新归类为任意 draft optimization。
3. native prompt 边界明确排除内部制作字段；必要技术适配有可见差异，实质改写沿 accepted human decision gate。
4. 运行既有 `test_open_video_skill.py`、`test_seedance_authoring_skill.py`、runtime boundary tests 和 exact staged Harness。
5. Parent 裁决一次 bounded read-only Kimi mapping，完成 Risk Gate、自审、record/learning evaluation，再仅提交本次 paths、push main 并核验 SHA。

## Self-Review

本计划与用户明确 scope 相符，保持已批准来源、生产安全和真实媒体验收；不新增逐镜机械批准步骤。
规则 verification 只能证明 routing 文案契约和既有 validator 行为，不证明 future Agent 判断或影片质量。
