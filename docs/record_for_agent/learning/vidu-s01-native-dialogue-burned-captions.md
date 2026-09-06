---
document_kind: learning_claim
claim_id: vidu-s01-native-dialogue-burned-captions
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
pending_claim_version: 2
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

# Vidu S01 Native Dialogue Burned Captions

Date: 2026-09-06

## Active Claim

None.

## Pending Candidate

### Failure Pattern

`failure_pattern`：S01 三次独立 `viduq3-pro` I2V、native audio请求都明确要求画面无字幕，
生成物却烧入广播文字。第三次采用compiler2 prose及显式`is_rec=false`仍出现字幕；
窄范围结论是这些请求的文字禁止约束未落实，不是“Vidu必然加字幕”。

### Hypothesis

`hypothesis`：口播广播和无字画面之间的分离未被模型可靠遵守。
held constants为同一已登记首帧、同一Provider/model、4秒、1080p、native audio true。
第三次profile只续期operator上限时间，prompt编译与is_rec为变化项，且未固定seed；
不能推断audio开关造成字幕，不能推断某句提示或单个参数的因果作用。

### Supporting Evidence

`supporting_evidence`：三次独立request/submit和不同MP4；每次的工具及Agent review只计一个单位。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-09-06-jieshi-s01-native-audio-repair-gate.md#s01-native-repair-gate | request:cdf6a55c1d3586fbad30e5649306ef38f99d924afec645144d4daf5f9e96df9c | jieshi-s01-first-frame-repair | jieshi-e01-s01-vidu-i2v-attempt02 | N/A | 49e585e89585449627431e3fe7395d64c1fa4bd42c9d400a3863fdde06fcb5f8 | AGENT_REVIEW_OF_MCP | FAIL | runs/jieshi-e01-i2v-20260906-attempt02/preparation-v3/shot-01-gate.md |
| docs/record_for_agent/2026-09-06-jieshi-s01-spatial-hand-repair-gate.md#s01-spatial-repair-gate | request:4fefcd71bc735c6296f28fddd31cdb18c7dd0e127c253afc68e7b4260fd7631d | jieshi-s01-first-frame-repair | jieshi-e01-s01-vidu-i2v-attempt03 | N/A | 0bf686d428e7af6e11b8f191bf389565e74ca31728ef1048d9942d674e42d42c | AGENT_REVIEW_OF_MCP | FAIL | runs/jieshi-e01-i2v-20260906-attempt03/preparation-v1/shot-01-gate.md |
| docs/record_for_agent/2026-09-06-jieshi-s01-vidu-v2-live-gate.md#s01-v2-live-gate | request:b66d3b87c97390eacddd01140785d1702d6f566e82881908123ac576700f55c3 | jieshi-s01-first-frame-repair | jieshi-e01-s01-vidu-i2v-attempt04 | N/A | 934f7498223dc6545396b868c7c6d31ea7dbd3015a80d34f19950087bb697bec | AGENT_REVIEW_OF_MCP | FAIL | runs/jieshi-e01-i2v-20260906-attempt04/preparation-v1/shot-01-gate.md |

### Counter Evidence

`counter_evidence`：检索当前S01 records、三份exact Gate与learning目录，未找到同边界
已验收无烧录字幕的native-audio例。检索RAG存在stale提示，coverage有限。
attempt01无声音且也有非预期数字，不能用作native audio的因果对照。
attempt03左手正确，反对“prompt对动作毫无作用”的更宽泛结论，但不反对字幕重复现象。
HyperFrames caption readiness属于不同owner，不作为此claim的证据或更新目标。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

### Scope And Exclusions

`scope`：2026-09-06的S01，exact PNG `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`，
Vidu `viduq3-pro` first-frame I2V、4s、1080p、native_audio=true；compiler1两次，
compiler2 prose且is_rec=false一次。仅为这三个exact样本的重复现象。
`exclusions`：其他模型/镜头、T2V/R2V、无声路线、后期合成、广泛成功率、官方能力结论、
音频开关因果、人物/倒影质量、P6/Final Acceptance和任何额外submit授权。

### Evidence Assessment

`pending_evidence_status`：SUPPORTED，仅支持重复现象。
`admission_basis`：TWO_INDEPENDENT_ATTEMPTS，三个request identity和不同视频，不以文件数计数。
新的同边界无字幕成功样本应加入counter evidence，避免把现象晋升为必然行为。

### Recommended Action

`recommended_action`：在现有Vidu文档的native audio说明旁增加一条有日期和exact记录链接的
advisory caveat：S01三次原生广播测试（含compiler2/is_rec=false）中出现烧录字幕，不能把prompt内禁止字幕视为已实现保障；
继续消费既有逐镜Gate的文字检查。保持原生声音偏好，不自动静音、不自动重试、不新增Gate。

### Adoption Target

`adoption_target`：Provider Policy。
唯一目标 `docs/vidu-provider.md`，仅增加上述有范围的advisory说明；不改API、compiler、
Provider默认值、audio/timeline owner或预算授权。确认前不修改目标。
验证：exact-path `git diff --check`、现有documentation contract check、Harness inspect所需
docs checks；若用户继续禁止worktree，不伪造Harness receipt，按原边界报告限制。

### Confirmation

`pending_approval_status`：PENDING_CONFIRMATION。
本候选以单文件checkpoint commit与其committed bytes SHA-256共同确认，二者在用户预览提供。
用户可Confirm/Revise/Reject；任何candidate bytes或target变化都需要新确认。

### Adoption Evidence

`pending_adoption_status`：NOT_ADOPTED。没有修改目标，没有激活或新Provider/media副作用。

## Supersession And Reopen Conditions

同边界counter sample、compiler表达变化或新增官方独立字幕控制的verified实现须重新审视范围；
不得仅凭其他镜头成功就宣称本镜头通过，亦不得延续为全Provider的永久结论。
