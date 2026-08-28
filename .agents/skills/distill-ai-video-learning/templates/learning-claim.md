---
document_kind: learning_claim
claim_id: CLAIM_ID
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

# CLAIM_TITLE

Date: YYYY-MM-DD

## Active Claim

首次候选保持 `active_claim_version: 0`，并在本节明确填写 `None`。如果已有被目标 owner 采纳的版本，完整保留仍在生效的当前 claim、适用范围、目标与 adoption evidence；新的 pending revision 不得改写本节。

## Pending Candidate

### Failure Pattern

`failure_pattern`：使用可观察、可复核的现象描述重复出现的 failure。不要用 Provider、模型或组件名称代替因果结论。

### Hypothesis

`hypothesis`：说明当前的因果解释、held constants、candidate variables，以及尚不能排除的 confounders。

### Supporting Evidence

`supporting_evidence`：逐项列出 repository-relative source、exact attempt / artifact / record identity、hash、proof layer，以及每条证据支持本 claim 的原因。

### Counter Evidence

`counter_evidence`：逐项列出反例、未复现案例、适用范围外的成功或失败，以及后续 supersession。没有已知反例时，也必须说明搜索范围与 coverage limitation。

### Scope And Exclusions

`scope`：列出候选当前适用的 Provider / model / profile、input mode、Shot / requirement、controls 与 evidence period。

`exclusions`：列出不得外推的 Provider、模型、profile、Shot 类型、Production acceptance 与其他 proof layers。

### Evidence Assessment

`pending_evidence_status`：`SINGLE_CASE | SUPPORTED | CONTESTED | REFUTED | RETIRED`。

说明当前状态成立的理由，以及哪些新证据会改变该状态。RAG score、technical score 与单一 metric 不得充当 epistemic confidence。

### Recommended Action

`recommended_action`：描述一个 bounded、可验证且不会绕过既有 owner 的动作。证据不足时，明确保持 advisory 或继续实验。

### Adoption Target

`adoption_target`：`Skill | Provider Policy | Preflight | Contract | Gate`。

列出 exact owner、target paths、预期 behavior change、unchanged contracts 与 mandatory verification。确认前不得修改这些 paths。

### Confirmation

`pending_approval_status`：`PENDING_CONFIRMATION | CONFIRMED | REJECTED`。

Pending preview 记录 candidate checkpoint commit，以及该 commit 中 exact file bytes 的 SHA-256。确认后将二者写入 `confirmed_candidate_sha256` 与 `confirmed_candidate_commit`；candidate bytes、commit 或 target 变化后，旧确认立即失效。

确认时还必须记录 sanitized `confirmed_by`、`confirmed_at` 与 durable `confirmation_evidence` pointer；不得复制 raw transcript、secret 或无关对话。

### Adoption Evidence

`pending_adoption_status`：`NOT_ADOPTED | APPLYING`。Pending candidate 在完成 target verification 前不能成为 active claim。

只有 target owner 完成实际变更并通过 verification 后，才能把 pending 内容提升到 `Active Claim`，记录 `active_adoption_status: ADOPTED`、target paths、commit、tests、Harness receipt 与 remaining scope，然后清空 pending lane。Verification 失败或 Reject 时，必须保持原 active claim 不变。

## Supersession And Reopen Conditions

记录会触发 reconfirmation、`CONTESTED`、`REFUTED` 或 `RETIRED` 的具体新证据，以及 `supersedes` / `retired_by` lineage。
