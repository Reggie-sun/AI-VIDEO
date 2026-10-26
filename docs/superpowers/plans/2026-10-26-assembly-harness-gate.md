# Assembly Harness Evidence Gate

**Goal:** 让连续片交付前通过可执行入口核验逐接点审看记录，防止技术导出成功掩盖重复动作和接点漏检。

**Scope:** 复用 `junction_review.py` 的时间线接点推导与裁决；在现有 Harness CLI 增加 prepare/verify assembly 命令，检查当前 MP4、ResolvedTimeline、HyperFrames report 和逐接点重复动作/状态连续性/声音观察的精确绑定。缺失、陈旧及 FAIL 均不能验证通过。

**Boundaries:** 不生成或自动分析新媒体，不新建 timeline、Product state 或验收 owner；Harness 只读核对现有文件和显式观察，不能保证观察属实或自动理解扫码，不能代签人工接受。允许交付明确标为未验证的审看片；不得将其称为接点验证通过。

**Compatibility:** 既有工程 verify/receipt 与 legacy visual review 默认行为保持；更严格的动作项由新的 assembly 验证入口强制。当前本地 HyperFrames report 未重复提供 timeline_frames 时，以已有 measured.duration_frames 与时间线核验，显式冲突仍拒绝。

## Implementation

- `junction_review.py` 增加可选的重复动作、状态连续性与节奏观察；严格模式要求这些项目且保留已见 FAIL，原默认模式不改。
- `scripts/agent_harness_assembly.py` 只读重验当前输入、输出待填模板或调用原 Gate；`agent_harness_cli.py` 先于工程 scope 路由独立命令，退出码区分通过、未通过和无效输入。
- 既有 Harness policy 映射新测试；`open-video` 既有交付流程要求连续片交付前执行验证，细节归 `docs/visual-quality-gate.md` 与既有 owner；不为此扩大已超预算的AGENTS常驻上下文。
- 用标准 Production composition fixture 验证真实 resolved 接点，覆盖漏项、重复动作FAIL、动作/声音/速度不足、错片、错时间线、错report、错接点ID、旧输入绑定和CLI路径；当前33.875秒成片只实测未填写记录会阻断，不伪造PASS。

## Verification And Completion

先运行新精准测试与原junction suite，再运行相关 Harness/visual contract检查及 exact staged Harness。Parent自审；本改动不写Production或付费状态，无重大不可逆失败路径，默认无需新增独立review。保留全部并行改动；只提交owned路径或owned新增hunk，push并核验SHA。记录实际receipt、测试层级、机器验证与人工接受边界，不将普通fixture或当前未验证成片标为已接受。
