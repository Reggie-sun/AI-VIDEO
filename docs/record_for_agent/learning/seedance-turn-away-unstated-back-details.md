---
document_kind: learning_claim
claim_id: seedance-turn-away-unstated-back-details
evidence_index_version: "1"
admission_basis: TWO_INDEPENDENT_ATTEMPTS
material_update_target_claim:
material_update_previous_evidence:
material_update_delta:
active_claim_version: 1
active_evidence_status: SUPPORTED
active_adoption_status: ADOPTED
active_candidate_sha256: 3b94690dc6797c77afcdb639e0cada892a31630329684d423bcd60672b1942e1
active_candidate_commit: 4ed70a8fc7a02177b944d4a80fc7ec0caad365da
active_adoption_commit: 4ea48b83368456a9a89713bf270853508adbab3f
pending_claim_version: 0
pending_evidence_status: RETIRED
pending_approval_status: CONFIRMED
pending_adoption_status: NOT_ADOPTED
confirmed_candidate_sha256: 3b94690dc6797c77afcdb639e0cada892a31630329684d423bcd60672b1942e1
confirmed_candidate_commit: 4ed70a8fc7a02177b944d4a80fc7ec0caad365da
confirmed_by: user
confirmed_at: 2026-11-24
confirmation_evidence: outputs/ai-city-takeover/logs/decisions.md#2026-11-24-learning-claim-seedance-turn-away-unstated-back-details-确认
supersedes:
retired_by:
---

# Seedance 转身镜头：首帧没有背面时，模型补造背面物件

Date: 2026-11-23

## Active Claim

Active v1 已获 exact user confirmation（2026-11-24「采纳 (Recommended)」），并在目标 Skill 验证通过后采纳。
下方保留已确认的观察、证据与适用边界；只作 authoring 提醒，不是 Gate，不证明能提高出片通过率。
原 pending preimage 保存在 `4ed70a8fc7a02177b944d4a80fc7ec0caad365da`；其他 Learning Claim 不变。

### Failure Pattern

`failure_pattern`：在 IRIS EP01 s014 与 s016 两个不同镜头里，当 prompt 要求人物转身、背对镜头，而首帧（以及参考）里没有背面，生成的片子在背对镜头后出现首帧里不存在或位置不同的背面物件与衣着：

- SG06（唱段 multimodal，投币电话旁）：最后一句改为「松开手……她转身朝画面左侧走开」，两条 take（m-1 `9713392a…`、m-2 `e1a4e319…`）Gate FAIL，原因含背面首帧没给，模型补出黑色挎包、裙变短裤；m-1 听筒自己挂回钩。
- MO07（动作 first_frame，走秀台尽头）r5：「转身……一只手按住腰间寻呼机，背对镜头朝画面右侧走开」，两条 take（r5-1 `de9eba5c…`、r5-2 `8506a2f9…`）Gate FAIL：背过身后寻呼机被挪到后腰、工牌消失；r5-1 另有后腰寻呼机亮红。同一镜头的 r4 转身时也有工牌消失、寻呼机跳到背后（同一首帧链，不另计 support unit）。

本 claim 支持的是「该现象在两个不同镜头重复出现，且改法后失败点消失」，不是「已证明转身必然补造背面」，也不是「改法保证通过」。

### Hypothesis

`hypothesis`：首帧与参考只给了正面信息时，转身后画面里的背面内容只能由模型推测，随身物件（挎包、腰挂寻呼机、工牌）与下装就会被改写。两个缓解方向：（a）唱段单元不写转身，离开画面交给剪辑；（b）动作单元在 prompt 里先在转身前完成手部动作，并写明物件始终挂在身前、背对镜头时看不见。

Held constants：SG06 的 m 与 p 引用相同的参考图与人声 asset id（`iris-c-v4-sg06-reference`、`iris-c-v4-sg06-vocal`），两版 `native-prompt.zh.txt` 只差最后一句，`driver-config.json` 除该句相关的状态文字、approval hash 与画布 `node_id` 外相同（本次逐文件核对；未核对两个 asset id 背后字节是否未变）；MO07 r5 → r6 同首帧。

Candidate variables 与未排除的 confounders：

- SG06 只有每个 arm 2 条 take，p-2 唱错词，p-1 松手后前臂多造电话线（`FOREARM_EXTRA_CORD_AFTER_RELEASE`），所以「不转身」只能说去掉了背面补造这一个失败点，不能说整体通过。
- MO07 r6 同时改了三处（手部动作前移到转身前、写明挂在身前、s014c 改作插入镜头），不是单变量；r6-1 同 prompt 仍 FAIL（甩袖来回两次、沿中线后退、开头 0.75 s 定格），说明存在抽样差异，写明物件位置并不保证通过。
- SG06 两轮的 `routing_policy.identity.policy_sha256` 不同（`205e300f…` 对 `a7a66a29…`），原因本次没有追查，是一个未排除的 confounder。
- 两个镜头都在同一作品、同一 Provider 路线（Seedance 2.0 VIP，经即梦）、同一使用者、同一 Gate 判读人；样本很小，不估计提升幅度或成功率。

### Supporting Evidence

`supporting_evidence`：SG06 m 轮与 MO07 r5 轮是两个独立失败 unit（不同镜头、不同输入模式、不同首帧、不同 prompt）；两个缓解后的 take 是各自 unit 的修复结果。每个 prompt 轮次只登记一条 take，另一条同 prompt、同首帧的 take 不另计 unit。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md#sg06-m-1-turn-away | native:9713392a407869acfbf1d306eaa3001f11480eb5a1019e8459b5a67808e6d285 | iris-ep01-sg06-turn-away-vs-stay | sd-SG06-m-1 | turn-away-in-sung-unit | 9713392a407869acfbf1d306eaa3001f11480eb5a1019e8459b5a67808e6d285 | GATE_REVIEW | FAIL | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG06-m-1/SG06/fetch-result.json |
| docs/record_for_agent/2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md#sg06-p-1-stay-in-place | native:335ce608b539e909bff4441b9801d23c0ee54bef4a643ae1ebdcf1c849c8a003 | iris-ep01-sg06-turn-away-vs-stay | sd-SG06-p-1 | stay-in-place | 335ce608b539e909bff4441b9801d23c0ee54bef4a643ae1ebdcf1c849c8a003 | GATE_REVIEW | SPAN_PASS | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG06-p-1/SG06/fetch-result.json |
| docs/record_for_agent/2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md#mo07-r5-1-turn-unstated | native:de9eba5cc9982226915632598a36993d6fab1bbe3b123632b46a5e52c8529646 | iris-ep01-mo07-turn-back-props | sd-MO07-r5-1 | r5-turn-back-props-unstated | de9eba5cc9982226915632598a36993d6fab1bbe3b123632b46a5e52c8529646 | GATE_REVIEW | FAIL | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r5-1/MO07/fetch-result.json |
| docs/record_for_agent/2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md#mo07-r6-2-front-chain-stated | native:f8ea9ac669f8db68315817e8d2ed845f24d9c6dd52ee31cdcc24d11bc0195950 | iris-ep01-mo07-turn-back-props | sd-MO07-r6-2 | r6-front-chain-stated | f8ea9ac669f8db68315817e8d2ed845f24d9c6dd52ee31cdcc24d11bc0195950 | GATE_REVIEW | PASS | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r6-2/MO07/fetch-result.json |

### Counter Evidence

`counter_evidence`：下表是已知的限制或反向案例，不是推翻。MO07 r6-1 与 r6-2 同 prompt（均写明物件挂在身前）、同首帧，r6-1 FAIL（失败原因是甩袖与后退，不是背面物件），说明写明物件位置不足以保证 take 通过；它没有显示背面物件被补造，所以不反驳失败 pattern。搜索范围仅限 `outputs/ai-city-takeover/logs/decisions.md` 2026-11-21 至 2026-11-23 各条与上述 take 目录；没有检查更早的 IRIS 记录（如 U021、c13、c14）或其他作品里的转身镜头，coverage 有限。MO12（s027）从正面首帧要求背对走远时，n 轮两条都朝镜头斜走，改成背影首帧的 p 轮主动作 PASS；这是首帧本身的改动，不是 prompt 措辞，不计入本 claim 的 support 或 counter。

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md#mo07-r6-1-front-chain-stated | native:c13132334e83099440f035dcfc2aadd5b588155cdf68088721237f0c6fec357b | iris-ep01-mo07-turn-back-props | sd-MO07-r6-1 | r6-front-chain-stated | c13132334e83099440f035dcfc2aadd5b588155cdf68088721237f0c6fec357b | GATE_REVIEW | FAIL | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r6-1/MO07/fetch-result.json |

### Scope And Exclusions

`scope`：Seedance 2.0（即梦 VIP 路线）、`first_frame` 与 `multimodal` 两种输入模式、单人全身或中景、首帧与参考不含背面、prompt 要求转身或背对镜头的 Shot；证据期 2026-11-21 至 2026-11-23；用于 authoring 阶段的提示与 Gate 查项，不用于判定生成质量。

`exclusions`：不外推到其他 Provider 或模型（H3、Vidu、Seedance 2.5）；不外推到首帧本来就含背面或另给了背面参考的 Shot；不外推到多人或群像转身；不说明转身动作本身的质量；不构成 Production 资格、P6、Final Acceptance 或 `preview_approval` 依据；不改变现有逐镜 Gate 的判据与「改判须用户当次决定」。

### Evidence Assessment

`pending_evidence_status`：`SUPPORTED`（窄范围）。`admission_basis`：`TWO_INDEPENDENT_ATTEMPTS`（SG06 与 MO07 两个独立失败 unit；两个修复结果是各自 unit 的 support，不额外计数）。

理由：两个不同镜头、不同输入模式各自出现同类失败，对应的修复各自让该失败点消失。限制见 Hypothesis 与 Counter Evidence：同作品同 Provider 路线、MO07 非单变量、样本小、没有跨作品证据。会让状态降为 `CONTESTED` 或 `REFUTED` 的新证据：在首帧不含背面、prompt 未写物件位置的情况下，转身镜头多次稳定保持背面物件；或在写明物件位置后仍多次补造背面物件。会升为更广范围的新证据：另一作品或另一角色出现同形态失败与修复。RAG score、技术分数与单一 metric 不充当 confidence。

### Recommended Action

`recommended_action`：在 Seedance authoring 阶段增加一项 advisory 检查——Shot 要求人物转身或背对镜头、且首帧与参考没有背面时：（a）唱段单元不写转身，让离开画面由剪辑承担；（b）动作单元把手部动作放在转身前，并在 prompt 里写明随身物件挂在身前、背对镜头时看不见；Gate 阶段对背面画面核对物件与下装是否与首帧一致。该检查是提醒，不替代逐镜 Gate，也不自动判 FAIL。若有条件，另做一次只改「写明物件位置」一个变量的对照再扩大范围。

### Adoption Target

`adoption_target`：`Skill`。

- Owner：`seedance-authoring`（`.agents/skills/seedance-authoring/SKILL.md`，以及采纳时由 owner 指定的该 Skill 内 reference 文件）。
- 预期行为变化：authoring 时多一条转身镜头提示；不改 Provider 选择、预算、permit、Gate 判据。
- 不变的契约：`AGENTS.md` Per-Shot Post-Media Gate、`seedance-authoring` 对版本与模式的选择规则、Provider Policy。
- 必须的验证：该 Skill 自身的测试与 `.agent/harness/policy.yaml` 对改动路径的 focused 验证；`tests/test_claude_code_adapter.py` 的 Skill 对齐检查（若新增文件）。
- 确认前不得修改以上任何 path。

### Confirmation

`pending_approval_status`：`CONFIRMED`。

Candidate checkpoint commit 为 `4ed70a8fc7a02177b944d4a80fc7ec0caad365da`（已在 `origin/main`）。2026-11-24 采纳前重算 `git show 4ed70a8f:docs/record_for_agent/learning/seedance-turn-away-unstated-back-details.md` 的 SHA-256 为 `3b94690dc6797c77afcdb639e0cada892a31630329684d423bcd60672b1942e1`，与当时工作区文件 bytes 一致。使用者看过 claim、证据、限制与唯一目标（`seedance-authoring`，advisory、不设 Gate）的预览后回复「采纳 (Recommended)」，记录见 `outputs/ai-city-takeover/logs/decisions.md` 的「2026-11-24 Learning Claim seedance-turn-away-unstated-back-details 确认」一节。候选内容、证据或目标范围变化后，本确认失效。

预览只列了两条 authoring 建议（唱段不写转身；动作单元手部动作前移并写明物件挂在身前）与限制。Recommended Action 里「Gate 阶段对背面画面核对物件与下装」一句不在本次确认的目标内，未采纳，逐镜 Gate 判据不变。

### Adoption Evidence

`active_adoption_status`：`ADOPTED`。

- 唯一 target commit：`4ea48b83368456a9a89713bf270853508adbab3f`，含 `.agents/skills/seedance-authoring/references/seedance-2.0.md` 新增 `## Advisory: Turn-Away Without Back View` 一节（scope 只含 Seedance 2.0 overlay；`SKILL.md`、`seedance-2.5.md`、`authoring-common.md` 未改）。
- 该 commit 中 target bytes SHA-256：`f690ce0112e35debb0833b6907a91a805ff1c6b8de43aa5d91e908c82b5c7175`（主会话 `git show` 重算核对一致）。
- 目标 exact-staged receipts（同一暂存内容）：
  - focused：`.agent/harness/runs/seedance-turn-away-adoption-20261124-focused/receipt.json`（passed）
  - related：`.agent/harness/runs/seedance-turn-away-adoption-20261124-related/receipt.json`（passed，closure_eligible）
- 未跑 full；离线 PASS 只证明文本契约与路由，不证明该提醒提高出片质量。

## Pending Candidate

无。`pending_claim_version: 0`；`pending_evidence_status: RETIRED` 仅表示 pending lane 已关闭，不表示 active v1 被 retired。后续 claim 或目标范围改变须创建新的 pending revision 并重新确认。

## Supersession And Reopen Conditions

- 候选 bytes、scope、证据集、recommended action 或 adoption target 变化时必须重新确认。
- 若跨作品证据显示首帧不含背面的转身镜头多次稳定通过，改为 `CONTESTED`；若只在本作品内再出现同形态，维持 `SUPPORTED` 并补证据。
- `supersedes`、`retired_by`：当前为空。
- 证据来源记录：[2026-11-23 s015–s030 检查点](../2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md)。
