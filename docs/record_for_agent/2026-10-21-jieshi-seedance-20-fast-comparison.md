---
record_kind: provider_comparison
topic_id: jieshi-uploaded-style-seedance-20-fast
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi Seedance 2.0 And Fast Comparison

Date: 2026-10-21

## Scope And Inputs

用户要求按刚修改的策略重写 prompt，分别测试 Seedance 2.0 和 Fast，且明确确认八人为项目自有 AI 虚构人物、允许提交同一首帧。用户最后指定 `SEEDANCE_API_KEY`；本次仅由 injected supplier 在内存读取指定私有文件的该字段，没有显示密钥、搜索其他来源或自动切换 METASO。

证据根 `R = runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-seedance-20261021-001/`。每模型仅一次 POST；两条均已成功 fetch 原始 MP4。没有重抽、S02、自动 activation、P6、Final Acceptance 或最终 composition。

- 两条实际发送相同 447 字中文视觉顺序 prompt，文件 `R/prompt.txt`，SHA `28934483d7c8fb62f10b0415608929d6a8df9bea5c97e7c7044fb853701547e0`。不将内部枚举、序列化因果字段或全部 QA 文本机械拼入 native prompt。
- 相同唯一 `first_frame`：asset `jieshi-s01-uploadedstyle-fullframe-20261021-002`，SHA `93c4d6bc6d3467bc444a61ba492293ad9e98a5f8b123589cd7afb3476b0fe7d9`；现代八人、车厢构图和上传画风职责保留。不绑定额外白模；本次对照以完整首帧固定起始布局、文字描述动作，不声称参考或短 prompt 保证效果。
- 相同 5 秒、720p、9:16、24fps、native audio；当前 canonical source 为 Project36，component `S01-production-source`，parent task 保持原项目。原 16 项 raw / 38 项 FinalOutput 与 0–3 秒采用要求保留；镜尾 character-presence 仅改为可读的原座在场表达，不能代签其他质量要求。
- Fast 的 canonical comparison 实际只改变 `model_id`、`provider_profile`、`execution_stack_hash`；prompt、图像、output、compiler 等保持相同。两条 seed 均 uncontrolled。比较绑定 `R/fast/frozen-input-model-comparison.json`，没有模型优越性的先验质量声明，也不能由每模型一个样本推出因果排名。

## Human Feedback And Module Diagnosis

用户实际反馈“你没有觉得还是很不自然吗”，继而要求定位相关模块。此为明确的用户观感负反馈，不能继续把人物/构图稳定当作自然表演成立，也不把会话反馈伪造成 canonical HUMAN receipt。以下为同一双臂的新增分析层，不增加独立媒体样本。

- **Authoring / performance intent：** exact `generation-context-row.json` 的作者数据含“留原座，不转头”（71行）、“不另加滑屏手势”（167行）、“不移动头身”（186行），各人强度均为 subtle。这些是 Agent 写入的表演设计，不是 `performance_direction.py` 自动生成的动作。`performance_authoring.py:49` 只检查完整填写与 selected QA 路径覆盖；实际机制仍为 model prompt guidance。过多姿态锁定可能压缩自然表演空间，但影响程度尚未由隔离实验建立。
- **Seedance native prompt binding：** 两臂实际 resolved request 均为 compiler/2、正文与447字 `prompt.txt`完全一致，Shot没有 `preserved_source_expression`。`seedance_native_prompt.py:48–62` 先编译包含完整逐人物方向的长文，再把它的 `expressed_control_paths` 交给 binding；`SeedanceNativePromptBinding.compile:131–155` 改用 authored短正文却沿用这些控制路径。`generation_recipe.py:180–204` 对已声明路径跳过相应未表达检查。短正文将七人的方向概括为日常状态/错开呼吸或眨眼，未逐项保留各人的呼吸、情绪及阶段描述。源码已证明这条覆盖声明来源与最终正文不一致的路径；尚未运行针对性 reproducer/test，不能据此断言它是画面不自然的唯一原因，也不能用补回整段长文冒充已验证修复。
- **First-frame / style review：** exact row539行曾声明全体统一3D CG；后续用户与Parent画面观感认为主角CG与偏写实的背景人物/车厢统一不足。`canvas_visual_style.py:82–106` 验证显式参考覆盖并保留 `aesthetic_acceptance=NOT_EVALUATED`，不自动判断审美。这里需要纠正 Agent 对参考美术与全场统一性的判断，不能把 COMPLETE coverage 当作视觉质量通过。
- **Media review / reporting：** 两臂 `s01-character-performance`、`s01-3d-anime-style` 原本都为 NOT_EVALUATED，未获得 activation/Final Acceptance。Gate没有误签自然表演PASS；Parent早先口头评价偏重身份/构图保持，没有及时以整体僵硬感作为主要结论。Sparse frames也不能证明完整正常速度表演或声音语义。

Parent与一名 native `code_mapper` 做只读交叉定位，并用CodeGraph核对调用关系；未修改上述实现、运行测试或新增Provider/媒体调用。静态源码快照：`seedance_native_prompt.py=f8d9252a40a82bb364f1380a8a403b163d10b7ee7434f428164ac9e0808aaa3c`；`generation_recipe.py=690b66290c923719d79d751f7479fabc38f6718046b1bb6adda5e421e8e0f858`；`performance_authoring.py=08fd507cb9f7ad616cb825d8b0cba1ecb2af629bdadba6de9b801b32d6385146`；`canvas_visual_style.py=f19e89fb6c05520e87ef9a5753edc2f3b2744d654eee0131eac529798e87ef4b`。既有[表演模块记录](2026-10-20-character-performance-control.md)也明确工程接通不证明已解决僵尸感。

本次record增补后的自动learning评估仍为 `no_candidate`：新证据为同一媒体链的用户反馈与静态调用链，不是新的独立质量实验或已验证修复，不提出Skill/Policy/Gate adoption。性能等待、渲染器、视频下载没有本轮证据可解释画面僵硬；Seedance模型能力占比仍未知，不把本次定位扩成后端模型结论。

## Proposed Repair Specification

后续状态（2026-10-22）：用户在 spec-only 交付后明确要求共享修复，已进入[实施计划](../superpowers/plans/2026-10-21-shot-performance-and-prompt-fidelity-repair.md)与[工程修复记录](2026-10-21-shot-performance-and-prompt-fidelity-repair.md)。下文 draft-only 描述保留为原交付时点；后续代码/验证不改写本对照的媒体、裁决、计数或费用，也不证明自然度已改善。

用户随后要求“写一个修复的specs”。已形成[Shot Performance And Prompt Fidelity Repair Spec](../superpowers/specs/2026-10-21-shot-performance-and-prompt-fidelity-repair.md)，状态为Draft/spec-only。范围覆盖最终prompt表达声明、逐人物表演设计、参考美术审查与原片审片/汇报，明确旧compiler/replay兼容、最小确定性回归和真实媒体验收的不同证明边界。未将draft采纳为Skill/Policy/Gate，未改实现或Production输入，未新增测试、Provider或媒体调用，未自动创建implementation plan。

Parent自审与本地文档路径/空白检查用于spec交付，不是实现验证或full Harness receipt；按当前先交片审片规则，未获用户效果认可的相关实现及本轮文档仍在工作区，未commit/push。`record-ai-video-session`复用本主记录，自动learning评估仍为 `no_candidate`：新增spec是修复提案，不是已验证修复，也不增加媒体独立样本。

## Actual Outputs And Execution

| Arm | Attempt | Exact MP4 SHA-256 | Bytes |
| --- | --- | --- | --- |
| 2.0 | `canvas-fb05156b96de4c3b5c0c57184e6d97b903b54516` | `132c5ef918e5ed140292a30982a7ffeb6a6509603e7fa1d9c0a641c2c3fffc38` | 2,439,853 |
| Fast | `canvas-69acbf16341c82376f9092a89e823cd8f545e21a` | `4e7120457f4f6b58dc8b25b8b1bbd095da9c99094540a0aa78305448d5c170ae` | 3,129,232 |

交片分别为 `R/2.0/outputs/Jieshi-S01-uploaded-style-Seedance-2.0-20261021.mp4` 与 `R/fast/outputs/Jieshi-S01-uploaded-style-Seedance-fast-20261021.mp4`；均为 canonical fetched bytes 的原样副本，无转码、剪辑或后配音。实测均 H264 720×1280 / 24fps / 121 帧，AAC stereo32kHz，container5.088 秒；最后视频帧120在5.0秒。文件存在和音轨存在不是视听验收。

| Arm | POST pending UTC | HTTP200 UTC | First observed succeeded UTC |
| --- | --- | --- | --- |
| 2.0 | 2026-10-20 21:39:50.071392 | 21:39:52.855190 | 21:43:44.494126 |
| Fast | 2026-10-20 22:03:53.879251 | 22:03:56.677169 | 22:06:36.676782 |

每臂 `wire-observations.jsonl` 的 pending/200 是同一个 POST 的两次观察，body hash 与 `exact-native-preview.json` 一致。2.0下载初次因结果 origin allowlist 阻断；只对已知成功的同任务执行 fetch-only profile 恢复，增加实际返回的官方 Ark TOS origin，未重发生成。旧 submit profile/request/permit 保留。Fast预先绑定该结果 origin，正常 fetch。

历史计数从14保留，有限 ceiling14→15→16。原内部项目上界600,000,000→700,000,000 microCNY，每次沿用50,000,000内部单次上界；见 `R/2.0/pair-budget-extension.json` 和两臂 `quota-extension.json`、`paid-authorization.json`。这些是 operator sealed bounds，不是市场价格、账单、余额或实际成本结算；没有清空预算、退回次数或复用 permit。

## Exact Media Review And Current State

两臂均显式调用 project-local `video_analyze`，各取得0–5秒、每0.25秒一帧的21张样帧；Parent 实际查看 contact sheet 和关键原图。Fast另查看原生帧66/71/72/78/120。`mcp-call.json`、`mcp-response.json`、`controlled-presentation.json`、`controlled-answers.json`、`diagnosis.json` 保留 exact artifact/rubric/presentation binding。没有实际听音或 audio-understand，不将 AAC 或 prompt 内容当作广播语义证据。

| Arm | Raw findings | Canonical state | Current conclusion |
| --- | --- | --- | --- |
| 2.0 | 5 PASS / 1 FAIL / 10 NOT_EVALUATED | Manifest242关闭，`failed / video_quality_rejected` | 2.50/2.75/3.00秒存在随实体左手运动的玻璃掌指倒影；2.75秒是明确的0–3秒窗内失败证据。对应空蓝座仍无人，灰卫衣背影属于陈立。 |
| Fast | 5 PASS / 0 FAIL / 11 NOT_EVALUATED | Manifest254，`running / validate`，已持久化 experience，未激活 | 约2.5–2.75秒开始抬手，比2.0晚；3.25–5秒可见手部倒影。靠近3秒边界的浅色区域不足以明确裁决0–3秒内失败，也不足以证明全窗无倒影。保留 `s01-reflections=NOT_EVALUATED`，不套用2.0的2.75秒失败。 |

两臂可观察的 camera、terminal presence、八人 identity、林砚右手唯一手机、车厢空间为 PASS；工牌细字、完整原声/嘴唇同步、全帧手部解剖及物理2cm、不完全可见道具、最终采用窗、八人细微表演和完整风格一致性等仍未完整证明。前景3D CG建模/发丝/材质保留，不冒称用户已经认可整片画风。

Fast保存观察时发生一次本地 answer schema 错误（误用 `reason` 而非 `observation`），发生在反馈持久化之前。仅修正字段并经新的 controlled presentation 绑定同一份已核验 MCP evidence，没有再次调用 MCP 或 Provider；原失败 presentation/answers 和 `evidence-serialization-repair.json` 保留。随后 canonical experience 为 `22823b4f328f368dc00ebfdd1b6cc0bb222800088927fcb77a78e7940788160c`，diagnosis为 `EVIDENCE_GAP`。

Fast尝试 quality abandonment 被 canonical owner 拒绝：没有已证明的 raw `QUALITY_FAILURE`，不得把证据不足写成质量失败。拒绝前后 Manifest254和 budget pointer均未改变；实际 `review-stop.actual.json` 明确记录 known media outcome、STOP/NOT_EVALUATED、零重抽/下一镜/激活。`running / validate` 指待证据审查的本地 lifecycle，服务端任务已成功完成。2.0关闭证据为 `closure-status.actual.json`；Fast不伪造同名成功关闭文件。

## Remaining Control-Plane Latency

Fast `paid-authorization.json::issued_at` 为21:58:03.379147 UTC，实际 POST pending 为22:03:53.879251 UTC，之间本地流程约350.5秒；HTTP200后至首次 observed succeeded约160秒。不能把本地等待计作模型生成时间，也不能宣称既有 reader 局部修复已解决整条路径的耗时。

当前代码只读定位仍见提交前重复标准加载/历史 binding 与 experience 重开。2.0/Fast封存的 execution-binding 分别约25.6MB/27.9MB；这只是规模证据，没有同快照 profiling 或受控优化前后测量。本次没有为视频再扩建通用缓存、放宽 Guard 或运行完整回归。旧局部修复证据见[历史读取记录](2026-10-21-paid-history-read-reuse.md)。

## Evidence Index

`R` 的展开路径见 Scope And Inputs；每行 `source` 都是该根下实际文件。两个模型臂是两个 attempt；同一臂的技术与 analyzer 层不增加独立样本数。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seedance20-technical | seedance:canvas-fb05156b96de4c3b5c0c57184e6d97b903b54516 | jieshi-s01-seedance-pair-20261021-001 | canvas-fb05156b96de4c3b5c0c57184e6d97b903b54516 | 2.0 | 132c5ef918e5ed140292a30982a7ffeb6a6509603e7fa1d9c0a641c2c3fffc38 | FETCH_AND_PROBE | PASS | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-seedance-20261021-001/2.0/output-identity.actual.json |
| seedance20-analyzer | seedance:canvas-fb05156b96de4c3b5c0c57184e6d97b903b54516 | jieshi-s01-seedance-pair-20261021-001 | canvas-fb05156b96de4c3b5c0c57184e6d97b903b54516 | 2.0 | 132c5ef918e5ed140292a30982a7ffeb6a6509603e7fa1d9c0a641c2c3fffc38 | EXACT_MEDIA_ANALYZER | FAIL | QUALITY_FAILURE,EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | seedance20-technical | runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-seedance-20261021-001/2.0/controlled-answers.json |
| seedancefast-technical | seedance:canvas-69acbf16341c82376f9092a89e823cd8f545e21a | jieshi-s01-seedance-pair-20261021-001 | canvas-69acbf16341c82376f9092a89e823cd8f545e21a | fast | 4e7120457f4f6b58dc8b25b8b1bbd095da9c99094540a0aa78305448d5c170ae | FETCH_AND_PROBE | PASS | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-seedance-20261021-001/fast/output-identity.actual.json |
| seedancefast-analyzer | seedance:canvas-69acbf16341c82376f9092a89e823cd8f545e21a | jieshi-s01-seedance-pair-20261021-001 | canvas-69acbf16341c82376f9092a89e823cd8f545e21a | fast | 4e7120457f4f6b58dc8b25b8b1bbd095da9c99094540a0aa78305448d5c170ae | EXACT_MEDIA_ANALYZER | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | seedancefast-technical | runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-seedance-20261021-001/fast/controlled-answers.json |

## Record And Publication Boundary

`record-ai-video-session`：record。自动 `distill-ai-video-learning`：`no_candidate`。已检索相关 experience、核对现有 learning 的范围及反证；两臂并无全项通过的修复，随机性未控制，已有“参考和 prompt 不保证执行”的约束覆盖观察，尚无有据的新 adoption action。保留本次独立臂及不同 proof，不增加占位 claim，不修改 Skill/Policy/Gate 或全局 memory。RAG返回 advisory fragments并提示后台 stale-shard维护，不将检索分数当作质量证据，不等待或重复刷新。

本次新工作限有界 operator wiring、ignored run receipts/媒体和记录；无新的共享 Seedance核心代码变更。此前相关 dirty修复及所有 foreign dirty/index工作保留。按当前 AGENTS 的先交片审片规则，尚未获用户明确效果认可，完整工程 suite、fresh full Harness receipt及 commit/push 暂缓；当前 publication为本地试片交付，非代码发布或 Production acceptance。下一步仅同 bytes 补证/用户审片，不能自动重生成或推进S02。
