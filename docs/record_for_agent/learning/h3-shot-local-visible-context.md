---
document_kind: learning_claim
claim_id: h3-shot-local-visible-context
evidence_index_version: "1"
admission_basis: TWO_INDEPENDENT_ATTEMPTS
material_update_target_claim:
material_update_previous_evidence:
material_update_delta:
active_claim_version: 0
active_evidence_status: NONE
active_adoption_status: NOT_ADOPTED
active_candidate_sha256:
active_candidate_commit:
active_adoption_commit:
pending_claim_version: 1
pending_evidence_status: SUPPORTED
pending_approval_status: PENDING_CONFIRMATION
pending_adoption_status: NOT_ADOPTED
confirmed_candidate_sha256:
confirmed_candidate_commit:
confirmed_by:
confirmed_at:
confirmation_evidence:
supersedes:
retired_by:
---

# H3 Shot-Local Visible Context Consistency

Date: 2026-09-05

## Active Claim

None。尚无已采纳版本；已有其他 Learning Claim 不受本候选影响。

## Pending Candidate

### Failure Pattern

`failure_pattern`：在本次灯塔 T2VA authoring 中，明确的当前 Shot 开闭状态/构图与同一
effective prompt 的其他字段发生冲突：Shot01 要求全程暗灯，palette 却仍描述 amber lamp light；
Shot05 要求 sea-only、灯塔画外，camera subject 却是 lighthouse，materials/exposure 又强调玻璃。
这两个不同 request 的既存逐项 Gate 分别观察到提前亮灯、画内出现灯塔。

本 claim 支持的是“这种跨字段冲突在两个生成 attempt 中重复出现，值得在 authoring 时检查”，
不是“已证明这些字段导致失败”，也不是“检查后保证成功”。

### Hypothesis

`hypothesis`：共享场景描述或通用模板可能把未来状态、画外物件重新带进当前 Shot 的
可见画面指导。应把 narrative location 与当前可见 subject/state 区分，并检查实际编译结果，
不能只看主动作句中的否定描述。

两组补拍均保留原 required intent，清理/细化有关字段后通过原 Gate。但每组同时改变了多处
相关文字与 effective seed，属于一个语义 repair 方向而非单字段、固定 seed 的 controlled A/B。
同主题、同 authoring 模板、同 Agent 抽样判读也限制了外部有效性；不估计提升幅度或成功率。

### Supporting Evidence

`supporting_evidence`：两条 initial FAIL 是重复冲突的两个支持 unit；两条 repair PASS
另列 Adjacent Repair Observations，不进入机器 support 计数，也不当作因果证明。
四条 exact execution identity 均保留；不是以四份文档或多个 proof layers 凑数。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#shot-01-media | h3:a213b70147300fda55b2d1f82913de72656a2154608b49267561cb7469619f22 | lighthouse-30s-20260905 | shot-01-video-30s | N/A | a2625cc547a90a3fa4e5d33da79060fcd7c195295fad13da09f07eed1b3a4f73 | AGENT_VISUAL | FAIL | runs/director-h3-lighthouse-30s-20260905-001/shot-01/media-gate.json |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#shot-05-media | h3:04014045bb2758574974f1563ef9142763f5a23f10973296e137663d11b8b05b | lighthouse-30s-20260905 | shot-05-video-30s | N/A | 73937df49aaf0977c53e017849891245d957c8390cb61d0a550b6cb6413e1dfd | AGENT_VISUAL | FAIL | runs/director-h3-lighthouse-30s-20260905-001/shot-05/media-gate.json |

- Shot01：`dark_lantern=FAIL`，0–5s 抽样持续 amber；补拍该项 PASS。
  effective seed 从 `420528493903203057` 到 `4113312321067224885`。
- Shot05：`sea_only_composition=FAIL`，灯室占左侧约三分之一；补拍该项 PASS。
  effective seed 从 `7472916145632921645` 到 `6520314297962062376`。
- 对应目录均位于 `runs/director-h3-lighthouse-30s-20260905-001/`。
  本轮重开 `resolved.json`、`media-gate.json`、`mcp-frame-review.json` 并重算 MP4 SHA-256；
  没有新做视觉分析或改写历史 Gate。

### Adjacent Repair Observations

以下新 execution 依赖各自 initial failure，只保留修复后的观察，不进入 admission 支持表：

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#shot-01-repair-01-media | h3:44f92d833a47b5a175d491fd2dabcaa0049cc6ac0341b90e9e3b69d4e5875fc2 | lighthouse-30s-20260905 | shot-01-repair-01-video-30s | N/A | bf82c78ac79b9bec701e390494e03bd3f764079f98d92ed8c58baa6bb44c2fc9 | AGENT_VISUAL | PASS | runs/director-h3-lighthouse-30s-20260905-001/shot-01-repair-01/media-gate.json |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#shot-05-repair-01-media | h3:77bf42aeb183f2fadafa884ff18f88d7150dca6a075d10fc2197e0cb00bf9063 | lighthouse-30s-20260905 | shot-05-repair-01-video-30s | N/A | 0fe033bb5189ec4c339e27789fd84763826a90ace7e9daccda740f9021ca8476 | AGENT_VISUAL | PASS | runs/director-h3-lighthouse-30s-20260905-001/shot-05-repair-01/media-gate.json |

### Source Byte Anchors

下表固定关键源文件 bytes：

| Attempt | resolved.json SHA-256 | media-gate.json SHA-256 |
| --- | --- | --- |
| shot-01 | 6d7f70fa857487f4f6f75aa3b774344e559fdc9a99614403a4c8fa05632441ae | 698103272953cc4e2231c588396649ab7dd7fc2f4fca32b049c4aaa56da3bd35 |
| shot-01-repair-01 | e3fc33246b2ef7e3d44edae7ec9c3be15b22f556135bf41397574d86350b2730 | 4040e23ff9435046eb6770ca768aa0e347cbf8771de1b79e97bab9259fd55992 |
| shot-05 | 3cf2762ba9d036d6c2866b72798e96d2441a4c8aaca38961748b2597d3d90da7 | 5fca06b276abcbdd3801f9d819303f10182e23bb0adf3c0d523980da2df1726f |
| shot-05-repair-01 | e8aa4d10b295f1ca1357dd8edebb6fcf9469e83deb38acd037ccc4cd682e8a81 | 5dd8e4870132f903ebd9fe1a981327f1ce3eec0bc8c8dcb883d17ecc71272c17 |

### Counter Evidence

`counter_evidence`：以下不否定“已观察到两次冲突”，但限制必要性、充分性及整镜质量外推。
严格保留原 overall verdict；不把局部 PASS 偷换成 overall PASS。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#shot-02-media | h3:2e04687f4023e53719350f5644a671a91ca3c8c591b2a5733582bc4294f106a9 | lighthouse-30s-20260905 | shot-02-video-30s | N/A | ecb88f58b8aef00affff61d7b3eae128783eab7cfa2e1e82d943316c4de0686c | AGENT_VISUAL | PASS | runs/director-h3-lighthouse-30s-20260905-001/shot-02/media-gate.json |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#shot-03-media | h3:ec5d0b7e62510c90f44e89110d789fbdd81f092adb6984071007e30e2c13679c | lighthouse-30s-20260905 | shot-03-video-30s | N/A | 4f9e36c22cf19ce15a4a26d4487ef78c2b94fde88c52ed9681cc9a230cfd4ec6 | AGENT_VISUAL | PASS | runs/director-h3-lighthouse-30s-20260905-001/shot-03/media-gate.json |
| docs/record_for_agent/2026-09-05-local-h3-lighthouse-director-test.md#h3-repair-media | h3:1adb21ee3aeb06134086a67ef496abcf68b201196686852ca65380b981670d21 | lighthouse-h3-20260905 | lighthouse-h3-video-002 | N/A | 2cc1188fda2a0471e8677a8100a42ccc2d50b3d1174acdd5ded26a013e42528e | AGENT_VISUAL | FAIL | runs/director-h3-lighthouse-20260905-002/media-gate.json |

- Shot02、Shot03 初次即 PASS，说明不是所有 Shot 都失败或必须预防性补拍。
- 旧短片 002 的可见暗到亮改为 PASS，但雨窗扫光 FAIL，overall 仍 FAIL；
  一个字段/目标修好不证明其他 requirements 不回退。该 raw MP4 本轮重算 hash 与表一致。
- Shot05 repair 的 `scene lighthouse` 仍保留而 sea-only PASS；不能制定
  “任何灯塔词都必须删除”的词汇黑名单。画外光源仍可解释当前可见照明。
- Shot04/06 各有独立 FAIL→PASS repair，但分别改变 pan endpoints/amplitude 和 whole-tower
  framing，不用它们支持本次更窄的共享可见 context 冲突 claim。
- 对照检索：Drama v1/v2 同 quality profile 有左右位置/locked framing 局部 PASS，
  但 compiler/情节不同且 overall 因音频 FAIL，不计作本 claim 的独立支持。
  M6、V8 三镜头 summary、upstream Long Video/FL2VA 与 Turbo comparison 涉及不同
  conditioning、recipe 或 repair 类型，也不并入计数。
- 搜索当前 `docs/record_for_agent/learning/` 没有同范围 existing claim；
  不把已有 HyperFrames caption claim 当作 material-update target。

### Scope And Exclusions

`scope`：2026-09-05 灯塔场景；`minimax-h3-t8-t2va-quality-v1`、
`text_to_video`、compiler `comfy-local-h3-t8-video-compiler/3`、
profile SHA-256 `4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`，
1344×768、124 frames、24fps、20 steps、native audio，当前源证据的 Agent sampled-visual 层。
建议只作为该 lane 的 authoring 检查案例。

`exclusions`：不外推到其他场景的实证成功率、I2V/FL2VA/Ref2VA、Turbo、Seedance、
未来 stack、连续镜头空间/建筑精确一致性、音频/全速主观验收、P6 或 Final Acceptance。
不按时长或有无 prompt 强制 single_take/multi_shot，不自动选择 Provider、补拍或删词。
不同 request 是可区分的 execution unit，不表示统计独立或随机抽样。

### Evidence Assessment

`pending_evidence_status`：`SUPPORTED`，只针对上述重复跨字段冲突的观察与有限 authoring 建议。
修复的因果机制与泛化效力仍未确立。

`admission_basis`：`TWO_INDEPENDENT_ATTEMPTS`。Shot01 与 Shot05 的 request、seed、MP4、
Gate 均不同；没有使用共享 input/reference MP4 来伪装新输出，也没有以同一成片的技术、
抽帧、用户认可重复计数。repair 依赖各自旧失败，显式保留关联而不称其为 controlled arms。
本候选不是 `CONTROLLED_MULTI_ARM` 或 `MATERIAL_EXISTING_CLAIM_UPDATE`。

首次 RAG 为 `experience`，query `H3 T2VA lighthouse prompt camera framing repair seed`；
experience 返回 stale-tagged last-good，run summary 单独标记 fresh。随后因发现跨字段冲突，
focused query `H3 shot-local palette camera subject offscreen state conflict` 返回 M6 的 fresh
对照片段。RAG 仅作 discovery；上述确切当前文件已重开，不使用 score 推断证据强度。
没有手工重建/等待索引；CLI 自行排队的派生索引维护不证明新候选已被索引。

### Recommended Action

`recommended_action`：经 exact confirmation 后，在 H3 authoring 的现有三字段指导处增加
一个简短的 Shot-local consistency 检查提示：

1. 从已批准 Shot 判断此时可见/不可见、已发生/未发生的状态。
2. 对照 palette、lighting、materials、camera subject 与 endpoints，发现与当前画面要求的
   实质冲突时回到 authoring owner 修正，再走原 compiler；保留有意义的画外因果解释。
3. 检查 actual compiled prompt 是否仍含相反指导；不直接 patch resolved request，
   不把该静态检查作为媒体 PASS，仍逐项执行原有 Gate。

这是针对既有 authoring owner 的 advisory guidance，不是新增 deterministic validator、
mandatory schema、runtime hook、自动重试或泛化的 prompt 优化器。

### Adoption Target

`adoption_target`：`Skill`。
唯一目标：`.agents/skills/h3-video/SKILL.md` 的 `C. Craft the 3-field prompt`。
只添加上述有限检查及非因果/非保证边界，引用本候选；不修改其他 Skill、Policy、Preflight、
Contract、Gate、compiler 或 Product source。确认前该目标保持不变。

Unchanged contracts：approved creative intent、Director 自主 strategy、exact request、
canonical compiler/committer、预算/permit、逐 Shot MCP Gate、Production acceptance ownership。

确认后 planned verification：`git diff --check`、按当前 Harness inspection 路由执行
exact staged verification 和 receipt verification。当前目标路由为
`scope_diff_check`、`docs_contract_check`、`policy_audit_check`、
`product_runtime_skill_boundary_tests`、`local_comfyui_supervisor_tests`、`harness_tests`；
实际变更时重新 inspection，另验证 intended guidance 与 unchanged boundaries 的 focused
Skill assertions。无需新增媒体/Provider 调用，tests 不证明模型效果。

### Confirmation

`pending_approval_status`：`PENDING_CONFIRMATION`。用户这次“确认”只批准补评估，
不是采纳本候选。仅本文件的 candidate checkpoint commit 和从该 commit 读取的 exact bytes
SHA-256 在交付中展示；避免把自引用 hash 写进自身 bytes。候选或目标改变须重新确认。

### Adoption Evidence

`pending_adoption_status`：`NOT_ADOPTED`。本轮没有修改 adoption target；
没有 Production state、Provider/media、P6、Final Acceptance、push 或 release effect。

## Supersession And Reopen Conditions

本候选收窄并取代两个灯塔记录中对“没有可提炼经验”的当前泛化解释，原 FAIL/PASS 与历史
`no_candidate` 判断保留为当时范围的事实。两个旧记录已加指向此处的更正/关联说明。
不存在需要替换的已采纳同范围 claim。

若 exact prompt/Gate identity 不符或既存观察被可信重审否定，应标记 `CONTESTED` 并复核；
若希望主张因果改善、其他场景泛化或自动 policy，需要新证据和新 candidate confirmation。
若其他 owner 已吸收相同指导，应重新评估必要性，不能创建第二控制路径。
