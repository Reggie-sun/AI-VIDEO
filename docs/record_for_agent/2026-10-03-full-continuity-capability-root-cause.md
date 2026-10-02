---
record_kind: architecture_implementation
topic_id: full-continuity-capability-honesty
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Full Continuity Capability Root Cause

## Goal And Scope

基于 current source `b16ec55`，调查 COCO / Nosha METASO H3 S03 raw
`OPENING_STATE_RESET` 的 repo-level 根因，并在已有 continuity owners 内阻止显式
FULL edge 退化为 soft Ref2VA。用户只授权离线实现、验证和本地 commit；本轮不读取
credential、不调用 Provider、不生成媒体、不改历史判定、不 push/release/deploy。
详细 A–H 分析和边界见 [spec](../superpowers/specs/2026-10-03-full-continuity-capability-honesty.md)，
执行 owner 与验证计划见 [plan](../superpowers/plans/2026-10-03-full-continuity-capability-honesty.md)。

## Exact Historical Execution

已核对 HEAD/history：`b2ba4b3`、`bd30c787`、`e62a0db7` 及两份实际媒体记录
[original experiment](2026-10-02-fanxiang-transom-metaso-h3-test.md) 和
[cut repair](2026-10-03-metaso-h3-cut-continuity-repair.md)。只读历史
`runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/prepare.py` 和
`shot03/{planning,plan,execution-binding}.json`，未执行脚本或修改 runs。

该路径在 authoring→planning 没有 materialize pairwise policy：
`previous_shot_state=None` → Planner `NONE` → neutral `/4` Ref2VA，四项 continuity
CapabilityNeed 为 false → 无 readiness policy → Router upstream terminal/semantic state
为 null → execution binding continuity_routing=null → canonical images、preceding
video soft reference 和 prompt。历史 submit 不携 exact first/last-frame conditioning。
S02→S03 的预期是 HARD_CUT/FULL/DIRECT；C detached、holder=floor/no holder、release
completed、moving right 必须 carry，不能由 canonical 标准图或 prompt 代替 typed edge。

另有三个可复现实现缺口：显式 policy 被 NONE/旧 requirement 的 readiness 条件跳过；
FULL 首帧 gate 仅覆盖跨 stack；Router 未复用 v2 target intent/carry 校验。需要限定旧行为：
显式 same-stack FULL+soft 请求仍会被末端 lifecycle validator 拒绝；不能把其 selected
中间结果描述为已允许 POST。本轮将拒绝前移为稳定 capability result。

## Existing Contract And Repair

`ContinuityTransitionPolicy`、`RouterContinuityState`、`ContinuityReferenceBinding`
及 `HardCutKeyframeBinding` 已具备所需语义和 lineage，没有新增 continuity owner。
FULL 的四 anchor roles 是 edge 输入/证据集合；C4 request complete grammar 仍由原 gate
负责。METASO capability 继续只声明 reference-only Ref2VA，不改成 exact terminal、
extension 或 first-frame。原 local H3 I2V/FL2VA 能力保留。

生产修复限定：

- `_video_intent_validation.py`：复用 sealed target/causal declarations 校验；readiness
  对 FULL 要求中立首帧 conditioning；reset 不要求 previous-shot conditioning。v1
  保留 legacy target/obligation 校验，原 `/4` continuity 仍要求 v2 causal evidence。
- `shot_readiness_gate.py`：明确提供的 policy 始终检查，不因 NONE/旧 requirement 跳过。
- `_video_requirement_routing.py`：所有 FULL stacks 要求 exact terminal 或已绑定
  hard-cut keyframe first_frame；不满足返回现有
  `BLOCKED_CAPABILITY / CONTINUITY_FRAME_CONDITIONING_REQUIRED`，不创建 bound request。
  C2 精确核对 target、source terminal 和 keyframe bytes/metadata；只允许 HARD_CUT/REFERENCE。
  EXACT_TERMINAL 不允许由 derived keyframe 替代原末帧。
- `shot_router.py`：原两个调用点传入 lifecycle；原 compiler、image activation、
  provenance、canonical reference lineage 与 sole committer 保持。
- `_asset_readiness.py` / `video_planner.py`：将非 Commercial、非 semantic-jump 的 angle
  change + 单 FIRST_FRAME 复用原首帧分支，保留 exact Shot/hash/role binding；标准
  Planner/readiness 产生 REFERENCE + I2V，不需要手工重封 plan projection。

## Regression Evidence

新增 fixture 使用真实 METASO capability，canonical Character 标准状态为 C attached，
source close 的完整 v2 causal declarations 为 C detached/release completed/moving right。
credential/reference resolver 一旦调用即测试失败，transport 不可用。

覆盖 same-stack FULL+soft Ref2VA 和公共 `resolve_requirement` 的 BLOCKED_EXECUTION、
identity/style/reset 正向 controls、carry mismatch/target intent mismatch/缺失 dimension、
C2 derived first_frame/I2V/compiler 正向、keyframe/terminal/target lineage 变异、
continuous-take 禁用 C2、显式 FULL/NONE readiness 阻断及 reset/NONE readiness 放行。
v1 FULL/identity/reset 正向、v1 wrong target 阻断、`/4` 拒绝 v1 causal policy 与
EXACT_TERMINAL 拒绝 derived keyframe 也有独立回归。
现有 exact-terminal、local H3、legacy serialization/hash 和 METASO multiple views 用例保留。

扩大后的 11 组相关测试曾为 558 PASS。首轮 exact staged tree
`8ce7d2d52d5c43ac816f545498d620be0ef09467` 的 Harness 001 为 11 PASS/1 covered skip，
receipt freshness/scope/artifact/policy 验证通过。两位独立 reviewer 各提出一个
blocking_candidate：FC-R1（v1 policy 误封）与 FC2-EXACT-001（派生图冒充 exact terminal）。
Parent 均用本地复现确认并采纳，四项新可靠 RED 后完成修复；最新五组 targeted suites
为 170 PASS，无新 warnings。新 snapshot 的 Harness 002 与双独立复审是最终 completion
前的一次 checkpoint，最终证据以如下 Harness 003 为准。
Harness 002 实际 PASS 且 receipt 校验通过；该 tree 的双独立复审第一位无 findings，第二位
提出 FC2-HANDOFF-002（non_blocking）：C2 的标准 Planner 首帧分支要求 previous=None。
Parent 核对并复现：legacy intent 为 BLOCKED，rich intent 因 Ref2VA conditioning mismatch
抛 ValidationError。该问题属于用户要求 P2，故补上既有分支的有限换机位条件；两项可靠 RED
后修复，新增五项错误资产/continuous-take controls。六组最新 targeted suites 为
314 PASS；最终 Harness 003 和同一 snapshot 双独立审查另行封存。

## Final Verified Checkpoint

代码与 Spec/Plan 已本地提交 `d234233`，tree
`576752aa0c81c4df1828a4858c670eb05b00e2dd` 与第三轮双独立审查完全相同。
实际 [Harness 003 receipt](../../.agent/harness/runs/full-continuity-capability-20261003-003/receipt.json)
为 PASS：13 checks PASS、1 covered skip（seedance_local_video_tests 被同轮 PASS 的
production_video_provider_tests 覆盖）。Provider suite 860 PASS/20 项已有 Pydantic warnings，
voice source 47、Vidu 194、neutral requirement 435、router 363、planner 140、readiness 245 PASS；
这些 suites 有重叠，不合计成 unique test 数。Targeted 六组 314 PASS 无新 warnings。
commit 前实际 `make harness-receipt` 的 scope/policy/artifact hashes/freshness/snapshot、
same-run coverage、workspace stability/cleanup 与 complete_completion_proof 均为 true。
staged receipt 绑定的是该 commit 前快照，不宣称后续文档 checkpoint 仍是同一 staged scope。

第三轮 reviewer 2 无 findings，reviewer 1 的 FC-R2 为 non_blocking：rich intent 首帧
缺失/wrong owner/stale owner/unbound 时，requirement constructor 抛 ValidationError，
而非返回 BLOCKED plan。Parent 对四类输入分别运行 new C2 与 unchanged initial-frame lane，
均得到相同 `asset_evidence.first_anchor / capability_need.needs_first_frame` 失败；没有 plan
或可提交请求。此项为沿用的 error-shape debt，保留为 limitation，不扩大 scope 重做 Planner。
没有 unresolved blocking finding；Parent 调查和裁决见
[review adjudication](../../.agent/harness/runs/full-continuity-capability-20261003-003/review-adjudication.md)。

## Media Evidence Boundary

S03 conditioning reference 来源为 S02 edited.mp4 7.25–11.25s，而最终 review 使用
S02 edited-v2 至 frame250 exclusive=10.4167s，S03 raw 从 3s 开始。两个 source boundary
不相同。保留原 raw FAIL/OPENING_STATE_RESET 和 edited limited visual PASS；后者不证明
Provider continuity capability PASS。本轮没有改这些历史证据或把 FAIL 改成 PASS。

## Limitations And Next Evidence

没有 typed edge 的 NONE/独立 Ref2VA 仍合法，系统不能从 prompt 推断 FULL。Caller 必须
通过已有 readiness/handoff 提供 exact source/target policy 与实际 conditioning binding。
本轮不重做 Planner，不自动更换 Provider，不生成 derived keyframe。
typed equality/lineage 与 first-frame conditioning 不证明媒体中 C 的实际状态、动作或运动
连续性；原逐 Shot exact-media Gate 仍必需。
rich intent 的无效/缺失首帧在既有 requirement constructor 可能抛 ValidationError；fail closed
保持，但统一为标准 BLOCKED plan/typed STOP 的错误输出改进未包含在本 slice。

要声称 H3 质量改善，后续仍需单独授权、同输入受控的真实 A/B 和 exact raw verdict。
离线 submit 前阻断修复的成立不依赖新付费实验；editorial repair 不能代替 raw acceptance。

## Governance And Publication

Native Codex 是唯一 writer；一次 read-only mapping 已完成。当前禁 credential/paid remote
约束下未调用 Kimi，不制造 failure fallback receipt；T3 使用同一 candidate 的两次独立
Native read-only review，Parent 保留 findings 裁决及最终责任。未建 development worktree。
Publication 为 source `d234233` 的本地 commit，当前工程记录完成 checkpoint；没有 push、release
或 deploy。没有真实 credential lookup/Provider POST/remote generation/新媒体 effect。

AOCI `aoci_maintain` 实际返回 `stopped / blocked`、candidates=[]、零正式索引写入：
最终维护尝试的 scope 有 25 个 observed pending paths（含任务前已有漂移），以及本轮 baseline stale。
工具要求先复核全部 observe 证据；未 blanket acknowledge 未核验的其他 paths，也未修改
scope/index 旁路。此次分析以当前源码、CodeGraph 和 tests 为证据，不宣称 AOCI 全量对齐。

自动 `distill-ai-video-learning` 结果为 `no_candidate`：本轮为工程契约修复，没有新的
独立真实媒体 attempt 或 controlled arms，不更新已有 H3 advisory claims，不创建占位候选。
