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

首次candidate保持`active_claim_version: 0`，并在这里明确写`None`。已有adopted版本时，完整保留仍被target消费的current claim、scope、target与adoption evidence；pending revision不得改写本节。

## Pending Candidate

### Failure Pattern

`failure_pattern`：用可观察、可复核的现象描述重复 failure，不用 Provider、模型或组件名称代替因果结论。

### Hypothesis

`hypothesis`：说明当前因果解释、held constants、candidate variables 与尚不能排除的 confounders。

### Supporting Evidence

`supporting_evidence`：逐项列出 repository-relative source、exact attempt/artifact/record identity、hash、proof layer 与它支持 claim 的原因。

### Counter Evidence

`counter_evidence`：逐项列出反例、未复现案例、scope 外成功/失败、后续 supersession；没有已知反例时也必须说明搜索范围与coverage limitation。

### Scope And Exclusions

`scope`：列出candidate当前适用的Provider/model/profile、input mode、Shot/requirement、controls与evidence period。

`exclusions`：列出不得外推的 Provider、模型、profile、Shot 类型、Production acceptance 与其他proof layers。

### Evidence Assessment

`pending_evidence_status`：`SINGLE_CASE | SUPPORTED | CONTESTED | REFUTED | RETIRED`。

说明为什么当前状态成立，以及哪些新证据会改变它。RAG score、technical score与单一metric不得作为epistemic confidence。

### Recommended Action

`recommended_action`：描述一个bounded、可验证、不会绕过既有owner的动作；证据不足时明确保持advisory或继续实验。

### Adoption Target

`adoption_target`：`Skill | Provider Policy | Preflight | Contract | Gate`。

列出exact owner、target paths、预期behavior change、unchanged contracts与mandatory verification。确认前不得修改这些paths。

### Confirmation

`pending_approval_status`：`PENDING_CONFIRMATION | CONFIRMED | REJECTED`。

Pending preview记录candidate checkpoint commit与该commit中exact file bytes的SHA-256。确认后将二者写入`confirmed_candidate_sha256`与`confirmed_candidate_commit`；candidate bytes、commit或target变化后旧确认立即失效。

确认时还必须记录sanitized `confirmed_by`、`confirmed_at`与durable `confirmation_evidence` pointer；不得复制raw transcript、secret或无关对话。

### Adoption Evidence

`pending_adoption_status`：`NOT_ADOPTED | APPLYING`。Pending candidate未完成target verification前不能成为active claim。

只有target owner实际变更并通过verification后，才把pending内容提升到`Active Claim`，记录`active_adoption_status: ADOPTED`、target paths、commit、tests、Harness receipt与remaining scope，然后清空pending lane。Verification失败或Reject必须保留原active claim不变。

## Supersession And Reopen Conditions

记录会触发reconfirmation、`CONTESTED`、`REFUTED`或`RETIRED`的具体新证据，以及`supersedes` / `retired_by` lineage。
