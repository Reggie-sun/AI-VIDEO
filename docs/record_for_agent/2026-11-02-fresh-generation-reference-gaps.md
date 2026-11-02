---
record_kind: architecture_implementation
topic_id: fresh-generation-reference-gaps
learning_eligibility: ineligible
---

# Fresh Generation Reference Evidence Closure

## Scope

補上 [先前記錄](2026-11-02-drift-root-cause-rules-and-gate.md) 的三項確定性缺口。只修 fresh execution binding，不改歷史重開、Production 生命週期或媒體驗收。未生成媒體、呼叫付費 Provider 或替真實範例編造使用者認可。

## Implementation

- 身份義務取 Shot `character_ids` 與 visible performers 的聯集；Shot 角色僅在明確 offscreen 且有非空理由時例外。身份延續、required identity anchor 或已封存認可的 waiver 才能覆蓋；電商同樣核對 waiver。
- `GenerationDecisionExecutionBinding.create` 傳入最終 resolved request，逐項核對 `image_bindings` 與 `media_bindings.asset_sha256` 屬於認可 preview SHA 集合，包含首尾幀。多餘的 review-only preview 不強制送模。
- 劇情 execution binding 缺 `source_project` 即 fail closed。輕量結構預檢可沒有 target Shot／Project，不能代替 typed execution binding。
- 入口盤點：唯一 production create caller 為 `GenerationFeedbackOrchestrator.prepare`；`for_project()` 重新載入並供給 Project。Canvas、Production Planning、generation／Jimeng feedback driver 及 strategy regression script 均沿此路徑。
- 夾具經既有 authoring／committer／loader 封存 synthetic approval，無 production bypass。Compiler-only 夾具的獨立 evidence Project 僅證明無 transport 的 wiring，不證明真實 current-project lineage。

## Verification

獨立 Codex OMX code-reviewer 已審核心門禁、共用夾具及整合差異，沒有 HIGH／MEDIUM 意見。定向驗證包括 reference authoring 48、execution/guards/runtime repair 101、local/provider wiring 80、generated-video e2e 52、quota/unsubmitted 37、quality rejection 23、sequence continuity 55 項通過。重疊測試不可相加當成獨立證據。

本次 exact staged snapshot 的三級 Harness receipt 由執行產生，結果以 receipt 本身為準：

- `.agent/harness/runs/fresh-generation-gaps-focused-20261102/receipt.json`
- `.agent/harness/runs/fresh-generation-gaps-related-20261102/receipt.json`
- `.agent/harness/runs/fresh-generation-gaps-full-20261102/receipt.json`

全套測試先以八組在無外網／移除憑據環境執行，再由 Harness 隔離驗證。初次工作區測試發現 Agent Memory 全語料 answerability calibration 失敗；未修改其測試或門檻，另以 HEAD 語料核對基線，該校準案例 1 passed；隔離快照結果另見 receipt。工作區掃描不冒充 immutable snapshot 證據。

## Golden Hash Causality

僅更新 `test_generation_quality_rejection.py` 五個與 `test_generation_history_import_receipt.py` 三個 fresh-fixture golden。隔離 interpreter 重開 HEAD 的 gate 與 fixture，精確重現原八個值；目前 payload 也由 `GenerationExperience` 重開驗證。獨立 reviewer 核對差異僅為 Shot preview provenance、`reference_planning.preview_approval.approval_hash` 及衍生 request／requirement／projection／recipe／evidence identities，沒有行為欄位變更。history-import／generation-evaluation 組合 21 passed，Seedance fidelity 遷移 17 passed。既有歷史 `/1` hash 保持原值。未新增 production 序列化欄位。

## Boundaries

程式只能核對證據存在、封存與輸入一致，不證明使用者原話真實、參考充分、模型服從、創作品質或人工驗收。`docs/canvas-projects/subject-reference/project.json` 仍沒有真實 preview approval，真實生成仍須先取得使用者認可。

兩份 canonical 文件的既有未提交改動經使用者同意保留，只提交本任務差異；其他音訊、motion-kit、outputs 及設定改動不納入。

`record-ai-video-session`: recorded。`distill-ai-video-learning`: no_candidate；本次是單一工程門禁修補，沒有新的獨立媒體實驗，不建立 Learning Claim、不修改全域記憶。
