---
record_kind: architecture_implementation
topic_id: s01-prospective-semantics-proof-binding
learning_eligibility: ineligible
---

# S01 Prospective Semantics And Proof Binding

Date: 2026-09-10

## Scope

本轮仅修复 pure diagnosis / Router 的 proof mismatch，以及将既有 requirement semantics
正式接入后续 S01 QA。没有新增 Resolver、Manager、state machine、QA lifecycle、Director
system、best-of-N、Exploration engine 或 VIDEO_EDIT；零 Provider 请求、零媒体生成。
本记录不改写任何历史 verdict，也不证明媒体或 human Final Acceptance。

## Current Production Selection

Root：`runs/jieshi-e01-i2v-20260907-attempt10/production-s01-v10`。
使用现有 `ProductionStateCommitter.activate_qa_policy()` 将 Manifest `62 → 63`；实际只改变
`manifest_revision` 和 `active_qa_policy`。标准 reader 读取 Manifest-selected project r6，
不能把 bootstrap `project.yaml` 的 r5 当成当前 selection。

| Identity | Value |
| --- | --- |
| Selected project | `abf50bc855435bbbf57e0964767cde729e1b5090ae829d810836357a89ba22e2` |
| Selected S01 r6 | `4c442c56961d589931ebba34aad987a73ed997f0eeb44755d0f6cc2fb8593d30` |
| QA policy version | `jieshi-s01-generation-qa / 3.0` |
| QA content hash | `3ae75134be69407d677d894041980623b1477635b1993ada7b7e6cba1895b48a` |
| Generation rubric | `9611f8b6b0db47b137c18e6bda7c1e00db2de5ae06845419087c9e19179bddac` |
| Exact parent rubric | `6e95f68134a326906d23b266c2a9a556cffe10988be7c48c0a19074191459820` |
| Before Manifest bytes | `d1a59f248ec07a7f9873e306a8fc5b9f41d20db4d5d9756fc00c69a8ccf05479` |
| After Manifest bytes | `09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db` |

可重用的完整 QA artifact 是
[s01-prospective-qa-v3.json](../superpowers/artifacts/drama/jieshi-episode-01/s01-prospective-qa-v3.json)。
它从 selected Brief / Shot、source-bound episode proposal 的广播 cue、原有 accepted hand/audio
quality floor 推导；`prospective_from_rubric_hash` 只允许从指定旧 rubric 进入显式新 goal，
不把旧 failure 改写成 repair success。

## Acceptance And Preference

Hard acceptance 共 16 项，FinalOutputContract 逐 ID 覆盖相同观看要求：

| Group | Requirement IDs |
| --- | --- |
| 前三秒异常与倒影对照 | `anomaly-readable`, `protagonist-no-reflection`, `others-reflection-contrast` |
| 自然手部、可读悬停与连续动态 | `natural-hand`, `hover-readable`, `natural-dynamics` |
| 人物、服装、手机、场景 continuity | `identity-continuity`, `phone-scene-continuity` |
| 广播核心信息、正式窗口、音质及闭嘴倾听 | `broadcast-core`, `broadcast-window`, `native-audio-quality`, `silent-protagonist` |
| 用户固定内容与后期结果 | `no-generated-text`, `genre-fixed`, `s02-cut-state`, `final-subtitle` |

`arrival-margin`（≤1.5s）、`immediate-onset`、`hand-trajectory`、`fixed-palm`、
`zero-camera-motion`、`broadcast-margin`（≤2.2s）全部是 `recipe_hint`；不生成 required
Finding，不进入 failed requirements、QUALITY_FAILURE 或失败统计。非法将 hint 写成 Finding
仍形成 rubric/evidence conflict。正式广播时间 predicate 是 source-media `100–2700ms`，
segment endpoint 不能替代最后音节的 bounded measurement。

原 registered input / exact bytes、geometry、fps、source duration、native-audio、provenance、
quota、permit、recovery、activation 与 no-regression 工程 gate 保持原 owner；不因艺术 QA
去掉旧 technical inventory 项而放宽。`video_artifact.py` 的 output parity checks 未修改。

## Proof Correctness

`diagnose_attempt()` 和 `diagnose_exact_result()` 对 marked Findings 使用原 source admission：
核对完整 canonical item/question、proof、stage、rubric/QA、request、媒体及 source projection。
没有 source 的裸 Finding 不能证明 PASS。非法 remainder 不参与满足 requirement，但同条记录
内独立验证成立的 FAIL 保留。不同 QA snapshot 的部分 PASS 不能跨 evaluator 权限拼接。
这些约束已传入 Router、experience、feedback、rejection/reopen 和前序 component gate。

受控 evaluator 接收 QA items 与 raw analysis；不再接收 request、recipe 或 authoring projection。
时间 verdict 由 typed predicate 校验，不以通用数值正则解释自由文本。显式错误 criterion ID
仍被拒绝。正确结构不证明自由文本内容真实；本轮没有构建新的可信 Human Evidence Protocol。

既有 `_expressions` 同时修复了必要的接线：列表形式 authored text 正常进入 generation
guidance，Enum 仍由原 compiler control mapping 负责；二者均不改变 evaluator criterion。
跨 rubric 不再产生旧失败的 intervention proposal。

## Exact History And Shadow Results

标准 `load_production_project()` 与 committer 重开全部 8 份旧 experience。激活前的 274 个
历史文件逐一比对，除授权改变的当前 Manifest 外全部 bytes/hash 相同；旧 QA、verdict、
Finding、experience、rejection/abandonment 原样保留。激活前 Manifest exact bytes 另存于
`preparation-v6/manifest-before-qa-v3.json`。

| Result | Exact MP4 SHA-256 | Prospective assessment |
| --- | --- | --- |
| attempt12 | `c56b05e2da5d38bfeddd2d6f58322d84a7d8433c01589112b87d1865b388b7f3` | `EVIDENCE_GAP`；1.5s 偏离仅 advisory；不自动 PASS |
| attempt13 | `d6a636d5fe19c1a9cbdd23d5bbb160ce3b2e91b8379d40346ff12e69aebff922` | `EVIDENCE_GAP`；2.32/2.44s segment 数据不能证明词尾；2.2s 不参与正式 verdict |
| freeze derivative | `090b4c605a400b712fa41d27028352bd6b38d6ba0436dda280b78a730b9840e3` | 保持原 human `FAIL`；整帧冻结破坏连续自然动态，违反 no-regression |

attempt12 原 exact hand/gap/audio “都正常”仅作为这三个未改窄 observable 的 shadow 参考，
不是新 QA presentation，不证明最终叙事、cut point 或其他新 hard item。attempt13 不继承
这些 human PASS；起手更早不被解释为整体更好。正式新 QA diagnosis 未伪造任何新 Finding。

本次 run evidence 位于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-v6/`：

| File | SHA-256 |
| --- | --- |
| `prospective-validation.json` | `118c2b20d34d5b399e96fda403cfe550c9736e5af29ae8c0f0babff219eb5dab` |
| `prospective-shadow.json` | `9528898b1f02702e31e39dd524e822b98772d77f86c7aff2a0685f9e02707d1b` |
| `prospective-decision.json` | `5952afaba18f569677575d2174a918fdeaa60662e083e538eecf6091bb2a25df` |
| `prospective-code-snapshot.json` | `b65368bc54688fb6cb83977cfa6fecbb99dc40c9f642feb15f72ed22b9e82e48` |

## Actual Next-Step Behavior

真实 `GenerationFeedbackOrchestrator.for_project.prepare()` 已选择 rubric `9611f8b6…`，
interventions 为空，返回 `BLOCKED_EXECUTION`。目标 I2V 的原因是 `TASK_SUBMIT_CEILING`，
实际已用 `4/4`；其他未批准/不兼容 variants 仍被阻断。旧 `legacy-03` QUALITY_FAILURE
只存在于保留的 historical diagnosis，不驱动新 QA 的 timing repair。

使用此新 QA、原 exact projection 与原 Vidu grammar 的 expression coverage 通过；进一步
调用纯 `compile_provider_video_request()` 返回 `CompiledProviderVideoRequest`，没有发起请求。
这不解除 quota，不创建新 attempt，不产生媒体或 acceptance。

## Verification And Remaining Work

独立 `reviewer_xhigh` 最终 scoped verdict 为 accept；same-record FAIL、跨 QA 合并、typed
时间 criterion、列表/Enum 编译与 freeze 反例均已复核。最终代码的 focused suites、当前
working-tree mandatory check union 与正式 Harness 的结果分别记录，不相互替代。

最终代码的六个 focused modules（feedback review、quality rejection、execution guards、
no-regression、evaluation binding、S01 semantics replay）实际通过 `128 passed in 82.77s`。
另有 semantics/replay/feedback 的 `40 passed`、纯 diagnosis/Router/history 的回归验证。
Mandatory checks 的 65 个 test modules 合并运行实际通过 `2666 passed`；该长运行期间
最后的 proof / compiler 增量仍在收口，因此这不是 exact-snapshot Harness receipt。
最后的 C-only advisory 回归另经 `63 passed` 与独立 reviewer 的权限反例验证：合法 advisory
不妨碍同 exact result 的完整 hard PASS；非法 actor/proof/QA/artifact/request 仍 fail closed。
Documentation contract gate、policy audit 与当前 working-tree Architecture Gate 均通过；
后者仅保留 `_state_commit_video.py` 原 oversized module 增加一行调用参数的 WARN。

目前不再需要扩大 QA / Harness / requirement architecture。下一高杠杆动作是针对
attempt12 exact bytes 的 holistic review：前三秒异常可读性、3s实际cut与S02接续，以及完整
A/B floor。真实 human/final proof 仍有缺口；human host 未资格化，不能宣称已经正式接受。
Exploration / best-of-N 未实现或启动；开始真实实验仍需完成该复核并获得新的有限 submit 授权。

本轮 learning evaluation 为 `no_candidate`：这是一项 correctness/selection 修复及既有
exact evidence 的 shadow，不构成新的独立媒体实验或已证明的经验收益。
已有其他工作区 dirty/staged changes 保留；共享 canonical docs 的同文件追加、task-owned
commit 与 Harness 临时 worktree 的授权问题尚待用户回复。本记录不冒称 formal closure。
