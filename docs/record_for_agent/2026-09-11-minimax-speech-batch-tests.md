---
record_kind: architecture_implementation
topic_id: minimax-speech-batch-tests
learning_eligibility: ineligible
---

# MiniMax Speech Batch Tests

## Current Result

用户明确将目标改为现有 MiniMax Speech 批量重复测试免逐次授权、免用户金额预算配置。本轮完成本地 implementation、离线入口验证及 native `reviewer_xhigh` 复审 `accept`，但最小真实语音执行进入 `OUTCOME_UNKNOWN`，没有可交付 WAV。任务在真实结果未知处停止；不得将工程通过解释为 live 成功、音质通过或原 S03 已接回声音。

## Implementation Boundary

- 入口为 `python -m scripts.minimax_speech_batch` 与 `run_minimax_speech_batch()`，使用新的独立 Production project、source Manifest SHA provenance、existing bootstrap/authoring graph、唯一 `ProductionStateCommitter.generate_voice_asset()`、voice candidate/probe/activation/Registry。没有复制或清空源账本，也没有新 lifecycle owner、Manager 或视频重生。
- `MiniMaxSpeechTestBatch.scripts` 封存有限批次，长度就是 durable submit ceiling；调用按序，首个失败或 unknown 停止。内部 one-use permit 每次仍为 `max_submit_count=1`，由程序签发每次 exact authorization，不要求用户逐次确认。完成的 exact batch 重开不重复 transport 或 Manifest write；未完成 attempt 不能自动重试。
- `paid_provider.py` 新增严格限于现有 MiniMax Speech 两个模型和原 endpoint 的 `minimax_speech_batch` contract，空金额字段表示未知，ledger 固定绑定 `voice_batch_submit_limit`。未报告费用的 MiniMax 成功输出保持 paid ACCEPTED / reservation RESERVED / actual cost null；voice asset 的 SUCCEEDED 不意味着费用已知。非 MiniMax voice 与视频金额语义保持不变。
- `voice_candidate.py` 仅提供既有 injected candidate seam 的 deterministic WAV materialize/probe；canonical Registry record 仍由 committer 重建。独立 test bundle 无 composition/render consumers，authoring graph 不宣称成片已生成。
- 已有 Chinese admission 与测试由上窗口承接。未修改已有视频相关 `_state_commit_paid_provider.py`、`paid_provider_submit_quota.py` 或其他任务 dirty 文件。新增入口和 helper 目前未显式映射 Harness category，inspection 正确回退 full tests；没有通过修改别人的 staged policy 隐藏该边界。

## Verification

- 新计数契约测试首先 RED，随后 GREEN。完整入口连续两次调用、strict reopen、零 transport/零 Manifest 写入 replay、凭证阶段已知失败、timeout/malformed unknown 停止及 durable count exhaustion 均有测试。
- 首轮 `reviewer_xhigh` 发现新目录未创建和相对 root 未规范化两个 P1。新增“相对且不存在目录”的完整入口回归先实际 RED；修复后 batch/candidate tests 为 `11 passed`，同 tier scoped re-review 为 `accept`。审查前运行的首次真实入口命令在目录 constructor 处失败，root 未创建，未到 credential/Provider。
- paid-provider/audio/voice/committer/recovery 组合 `706 passed`；reader/config/CLI/video/Seedance/Vidu/MiniMax video 组合 `1000 passed`；composition/HyperFrames/captions/generated-audio/runtime-skill 组合 `353 passed, 3 skipped`。这些是明确 working-tree 上的测试结果，不是隔离快照 receipt。
- 历史 `runs/minimax-speech-replacement-20260819-001/call-1` 与 `call-2-combined` 的 16 份 request/preview/authorization/Manifest/paid evidence 以原字节重开并通过现有 typed seals；没有改写历史 hash。
- full pytest 使用 `--maxfail=1` 实际停止于 `149 passed, 1 failed`：`test_repository_policy_audit_has_no_unmapped_owned_files` 的既有三个路径 `image_import_video_frame.py`、`paid_provider_no_effect_reconciliation.py` 和对应 test。policy-audit 同样列出三项；未改 baseline。
- Architecture Gate `--base-ref HEAD` 为 PASS，仍提示本任务 `audio.py` 增加 25 effective LOC 的 WARN，以及其他任务 `image_import.py` 的 WARN。新增独立 batch/preparer 已在独立模块；audio 中新增内容限于原 monetary fields 的 nullable 验证与共用匹配函数。
- `ruff check` 与 task diff whitespace check 通过。用户禁止 worktree/commit/push，本轮未创建 worktree、未 stage/commit/push，也没有 fresh passing exact-snapshot Harness receipt。新文件路由与既有 mapping 债务、隔离 Harness 仍未闭环。

## Live Evidence

修复并复审后唯一实际 voice execution：`runs/minimax-speech-zh-test-20260911-01`，模型 `speech-2.8-hd`、voice `male-qn-jingying`、Chinese、mono 44100 Hz PCM WAV，batch ceiling=1。Secret Service reference 沿既有 capability 读取，不记录秘密。

- attempt：`minimax-speech-zh-test-20260911-01-1`。
- standard project reopen：Manifest schema `2.6`，revision `7`，voice status `OUTCOME_UNKNOWN`，paid phase `OUTCOME_UNKNOWN`，reservation `UNSETTLED`，actual cost `null`。
- Manifest SHA-256：`532db122627ffb58227485632743deb485070c4c5c027c33c6c0a6794e705dbb`。
- request fingerprint：`d142a08ac4d905119d21dd344d8209bd57722f70cae32e70ad2ca2b147da1d07`。
- Gate：`state/paid-provider/gates/0757e64804348e5c0cc88df7cf1e8c252bed2f43adc8726423430f01bff96d54.json`。
- submit receipt：`state/paid-provider/submits/0ad92ac49b47ff7d79c44b13fa59dad098680a92dc6983cbb3e1ed02082dd8ee.json`。
- active budget：`state/paid-provider/budgets/75b1af1e252b0ace18fc99870e3285480cf7713c13f6357fc6f314322a470cfb.json`。
- 没有 WAV，不能证明远端已生成、未生成或实际扣费。当前 CLI 仅输出 `error_type=AiVideoError`，durable receipt 保留的是保守 unknown 分类，没有可用于区分 transport/HTTP/response-parse 根因的响应证据；不能凭猜测宣称 Provider 余额、密钥、格式或网络故障。

未知发生后没有重试、没有换 root/identity 自动补发，没有清理原 attempt 或结算为零。后续需要围绕这一 exact attempt 获得外部结果证据并走 explicit recovery；免逐次授权不取消 unknown gate。

原 S03 Manifest SHA-256 保持 `c340d0a5ca174835a13f4dfc511f11fa725ee797a36ea11cc368e1203f274b27`，未改 S03/S04、历史 QA/verdict 或音画状态。Agent Memory 检索返回 stale empty advisory result，本结论依赖 current source/tests/receipts。自动 `distill-ai-video-learning` evaluation 为 `no_candidate`：只有一个结果未知的 live attempt，不构成可泛化的独立质量证据。
