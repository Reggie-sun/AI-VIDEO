---
document_kind: learning_claim
claim_id: h3-i2v-first-frame-condition-renders-at-head
evidence_index_version: "1"
admission_basis: CONTROLLED_MULTI_ARM
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

# H3 I2V First-Frame Condition Renders At Head

Date: 2026-09-20

## Active Claim

首次候选，`active_claim_version: 0`，无已采纳版本。

## Pending Candidate

### Failure Pattern

`failure_pattern`：在本地 MiniMax H3 fl2va `image_to_video` lane 上，当 first-frame conditioning 资产的场景/亮度属性与 Shot sealed open state 冲突时，生成成片头部（至少前 2 帧 / ~83ms）会忠实呈现 conditioning 帧的原始场景（本例为明亮门店内部：价格海报、横幅、瓷砖地面），随后才硬切到 prompt 描述的夜景，构成真实的 `shot.continuity.in_out` 违约，且能被 Per-Shot Gate 的逐帧头部采样稳定捕获。

### Hypothesis

`hypothesis`：fl2va 的 i2v 语义把 first-frame conditioning 当作成片头部的 literal 内容，再向 prompt 场景过渡；因此 conditioning 帧的场景/亮度/构图属性会原样出现在头部。held constants：同一 provider profile（loopback ComfyUI MiniMax H3 fl2va）、同一源照片派生、同一 prompt 结构、同 frame_count/fps。candidate variable：conditioning 资产身份（暗化 `ff-hook` vs 全亮度 `ff-body`）。尚不能排除的 confounder：seed 敏感性未评估；两 arm 虽同配方但 frame content 不同（车头近景 vs 全身构图）；不能证明其他 provider/model 有相同行为。

### Supporting Evidence

`supporting_evidence`：两条 arm 构成一个 controlled comparison（同一 experiment、同一源照片、单变量为 conditioning 资产身份；暗化 arm PASS、全亮度 arm FAIL）。相同 `independence_key` 只计一个 support unit。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-09-20-ninebot-h3-first-frame-conditioning-head-continuity.md#N3-HOOK-PASS | attempt-shot-hook-2 | ninebot-h3-first-frame-conditioning | attempt-shot-hook-2 | arm:darkened-ff-hook | 24a71b0c7f49bfa18eaa852720dfcdc2d7e84428d2e2b6cf5257470c54b497c1 | AGENT_GATE | PASS | `runs/ninebot-n3-lighting-ad-20260920-001/evidence/shot-hook.review.json` |
| docs/record_for_agent/2026-09-20-ninebot-h3-first-frame-conditioning-head-continuity.md#N3-INTRO-FAIL | attempt-shot-intro-2 | ninebot-h3-first-frame-conditioning | attempt-shot-intro-2 | arm:bright-ff-body | 55edf38230e4e0ea43b339049aad6264fde279d3623469dd15e36b55ca7d6d70 | AGENT_GATE | FAIL | `runs/ninebot-n3-lighting-ad-20260920-001/evidence/shot-intro.review.json` |
| docs/record_for_agent/2026-09-20-ninebot-h3-first-frame-conditioning-head-continuity.md#N3-INTRO-HEAD-FRAMES | attempt-shot-intro-2 | ninebot-h3-first-frame-conditioning | attempt-shot-intro-2 | arm:bright-ff-body | 55edf38230e4e0ea43b339049aad6264fde279d3623469dd15e36b55ca7d6d70 | ANALYZER | FAIL | `runs/ninebot-n3-lighting-ad-20260920-001/evidence/shot-intro-head-{1..10}.png` |

### Counter Evidence

`counter_evidence`：在当前 `docs/record_for_agent/` 中检索了 first-frame / conditioning 相关记录（含 `2026-09-12-s05-first-frame-preparation.md`、`2026-08-24-shot-continuity-e0c-prompt-schedule-relay-experiment.md` 等），未发现「conditioning 场景与 sealed open state 冲突但头部未出现该场景」的反例；也未发现同一 provider 上本 claim 的 supersession。搜索范围限于本仓库记录，coverage limitation：未覆盖无记录的历史 run，不能证明该行为在所有 seed/构型下稳定。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

### Scope And Exclusions

`scope`：本机 loopback ComfyUI MiniMax H3 fl2va `image_to_video` profile（`comfy-local-h3`）、first-frame 绑定静态派生 PNG 的 input mode、Per-Shot Post-Media Gate 的 `shot.continuity.in_out` 取证；evidence period 2026-09-20。适用规则：选择 conditioning 资产时，其场景/亮度/open state 必须与 Shot sealed intent 的开场状态一致；冲突时优先复用已注册的、配方匹配的暗化资产，而不是全亮度原图。

`exclusions`：不得外推到 t2va、其他 MiniMax profile、其他 Provider/model（Vidu/Seedance 等）、paid/remote lane；不构成 Production qualification、Provider activation 或 P6/Final Acceptance；不以本 claim 替代逐 Shot 的 Gate 取证；attempt-4（repair 输出）取证完成前，本 claim 不声称「暗化 conditioning 一定通过 Gate」。

### Evidence Assessment

`pending_evidence_status`：SUPPORTED。

`admission_basis`：CONTROLLED_MULTI_ARM。一个 experiment（`ninebot-h3-first-frame-conditioning`）、两个非 N/A arm（`arm:darkened-ff-hook` PASS / `arm:bright-ff-body` FAIL）、每个 arm 有 distinct `independence_key`。

SUPPORTED 的理由：单变量对照（同一源照片、同一暗化配方族、同一 provider/prompt 结构）下，头部场景差异与 conditioning 亮度/场景属性精确共变；头部帧 ANALYZER 层证据独立复核了同一 artifact bytes。会改变状态的新证据：同 provider 上「conditioning 冲突但头部干净」的反例（→ CONTESTED）；attempt-4 在暗化 conditioning 下同类连续性 FAIL（→ 削弱 hypothesis，可能 CONTESTED）；其他 provider 上的受控对照（→ 扩展 scope，需 reconfirm）。

### Recommended Action

`recommended_action`：作为 advisory 规则加入 Shot authoring / first-frame 选择 preflight：在 H3 fl2va i2v lane 上，提交前检查 first-frame conditioning 资产的场景/亮度是否与 Shot sealed open state 一致；不一致时先派生/复用匹配 open state 的 conditioning 资产（如暗化裁剪），再进入 canonical submit seam。不改变任何 Gate、Provider 或 Production contract；不绕过 Per-Shot Gate。

### Adoption Target

`adoption_target`：Skill。

- Exact owner：`.agents/skills/h3-video/`（H3 authoring guidance，advisory knowledge）。
- Target paths：`.agents/skills/h3-video/` 中与 i2v first-frame 选择相关的 guidance 文档及其 tests（如有）。
- 预期 behavior change：H3 authoring guidance 增加 first-frame/open-state 一致性检查条目。
- Unchanged contracts：Provider Policy、Preflight、Contract、Gate target、Manifest/Registry ownership 均不变。
- Mandatory verification：target owner 既有 tests / Harness routing 对 Skill 文档变更的要求；确认前不得修改这些 paths。

### Confirmation

`pending_approval_status`：PENDING_CONFIRMATION。

Candidate checkpoint commit 与 exact file bytes SHA-256 在 candidate 提交后记录于此：

- candidate_commit：TBD
- candidate_sha256：TBD

### Adoption Evidence

`pending_adoption_status`：NOT_ADOPTED。

## Supersession And Reopen Conditions

- attempt-4 Gate 结果（PASS 或新类别 FAIL）出来后可更新本 claim 的 pending evidence 说明，但不改变 admission basis。
- 若 attempt-4 出现同类别连续性 FAIL 且无新可隔离变量，按 repair-loop 停止条件终止，本 claim 保持 SUPPORTED 但 recommended_action 需加「该 provider 上暗化策略不充分」的限定。
- 其他 provider/model 上的受控对照证据出现时，scope 扩展需用户 reconfirm。
