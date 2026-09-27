---
record_kind: provider_comparison
topic_id: creative-goal-real-api-local-tests
learning_eligibility: eligible
evidence_index_version: "1"
---

# Creative Goal Real API And Local Tests

Date: 2026-09-27

## Continuation Notice — 2026-09-28

用户后续要求增加参考图后重测；最新首尾帧输入、四次新提交、广告参考兼容性漏检及修正图未提交的 batch blocker 见 [first/last reference retests](2026-09-28-creative-goal-first-last-reference-retests.md)。新 API 剧情末态钥匙归属改善，但因果动作仍 FAIL；新 local 剧情在 novram 下仍 OOM。下文是首帧-only 的历史结果，不代表当前全部尝试；旧失败未被抹除或转换成通过。下文 local H3 / T8 标签的实际 profile 为 stock `minimax_h3_fl2va`，不是 T8 Turbo。

## Purpose And Authority

承接 [implementation record](2026-09-27-creative-goal-preservation-implementation.md)。用户要求真实广告、剧情各测一次，并分别尝试 API 和本地；另明确允许停止占用显存的 VLLM 服务后跑本地。四条路径各有一次真实生成提交，共 local 2、API 2；API repair ceiling 为 0。本轮是有界 development experiment，不是完整广告交付或 Production qualification。

主证据目录：`runs/creative-goal-real-test-20260927-001/`，以下简称 `R/`。忽略的实验产物保留在本机，不进入 Git。四次尝试分别使用独立 Production project，通过标准 loader、committer、Provider service、intent/permit、fetch 和 review seam；未手写 Manifest、激活 candidate 或签发 P6 / Final Acceptance。

## Preserved Goals

广告保留问题开场 → 老人推荐 → 使用 → 社会反应 → 原包装 hero / CTA 的完整目标；旧单图方案的拒绝未解除。此轮生成只覆盖新的使用动作候选，不能代替完整广告。剧情保留姐姐递钥匙、弟弟退避拒接、姐姐收回钥匙放松等待、弟弟看到退让再主动接取、唯一钥匙交接的可见因果，不能用字幕或旁白补齐。

`R/authoring/` 封存原 creative input、coverage、contract、direction、binding；广告 binding SHA-256 为 `63ba007d12662fb2ffe23340655c6e8c5c52a6f1ee1db8b70d0d532c01381bcc`，剧情为 `be348436dbd69ed5ba0618595b35fc65615e4c4fc84999fcc2129732728ab2b0`。两者结构预检通过，不代表执行或创作目标通过。

`R/review-authoring/` 仅修正 report 所需 visual requirement namespace，逐项保留 observables/proof，并通过 `lineage.json` 指回原合同。未改变提交前冻结的 Provider QA rubric，也未降低用户目标。

## Current Runtime Truth

| Attempt | Runtime | Outcome | Exact media SHA-256 |
| --- | --- | --- | --- |
| advertising-local-attempt-01 | local H3 / T8 | FETCHED，Gate FAIL：10–12 s 左袖消失，衣着退化 | `376b5562701c119f6eada740dbede12964dd2a2fbdbd1aefed94d47e4fbb5a68` |
| advertising-api-attempt-01 | Vidu / viduq3-pro I2V | FETCHED，Gate FAIL：1–4 s 泵头长出横向白管，随后消失 | `f29f434df0835df4b275056feb6c2dfce7ee98ce152e6cd07abd71ac7279f03a` |
| drama-local-attempt-01 | local H3 / T8 | known CUDA OOM，无 MP4；repair 在提交前被 task ceiling 阻挡 | `NO_ARTIFACT:CUDA_OOM` |
| drama-api-attempt-01 | Vidu / viduq3-pro I2V | FETCHED，Gate FAIL：等待触发缺失、交接后钥匙回到姐姐手中 | `270dbec018a5b7ab2bb312c8a11296c29572aa769606afbcd117b027d9de7bd6` |

实际媒体均为 raw Provider output。文件位置统一为 `R/<domain>/<route>/production-v5/state/video-generation/fetch/files/<SHA>.mp4`。三个文件未形成新的完整商业 composition；未绕过 source admission、QA 或 activation 拼接。

| Media | Bytes | Duration | Frames / dimensions | Audio stream |
| --- | --- | --- | --- | --- |
| local advertising | 2160466 | 12.250 s | 294 / 416×736 / 24fps H.264 | AAC stereo 32000 Hz |
| API advertising | 6890098 | 12.042 s | 289 / 720×1280 / 24fps H.264 | AAC stereo 48000 Hz |
| API drama | 4512460 | 12.042 s | 289 / 1268×724 / 24fps H.264 | AAC stereo 48000 Hz |

音轨存在不证明实际可听、同步或无额外对白。当前 Agent host 无法消费 audio input，实际完整聆听与 human full-speed acceptance 均为 `NOT_EVALUATED`。

## Gate And Recovery Evidence

三个 MP4 均调用真实 project-local `video-analysis` MCP，逐秒采样并检查 exact media；剧情追加 0.5 s 采样核对钥匙。Parent 看到 8–9 s 钥匙在弟弟掌上，10 s 又在姐姐指间、弟弟掌心空着。正式 analyzer evidence 通过 public `review_generation_attempt` 与 `ControlledPresentationVerifier` 留存；未把采样转换成 human proof。

`R/<domain>/<route>/diagnosis.json`：local 广告 failed `identity`，API 广告 failed `object`，API 剧情 failed `action, object`；三者都保留 `space`，其余缺证项不推断 PASS，`all_required_observed_pass=false`。

三个 `review-packet/result.json` 均为 `review_scope=full_contract`、`goal_chain=verified`、`verdict=fail`、`production_acceptance=not_evaluated`。`visual_quality_report check` exit 1 表示预期的负向验收结果，不是工具崩溃。完整广告链缺失与原始候选缺陷均保留在报告中。

API 剧情首次轮询出现 transport failure，既有 canonical attempt 仍是已接受的 running/polling；随后只对原 task 查询并 fetch 成功，没有再 submit、换 permit 或增加生成计数。`R/drama/api/resumed-observation.json` 与 `media.json` 记录 `resumed_existing_task=true, new_submit_count=0`。

本地剧情 OOM 已通过 public runtime-failure evaluation 留存，evidence hash `c2c0dde009f2d30de97c2d03ef0a3db666e2a699857a7d593ad13e3a529f6c3f`。环境单变量 repair authorization hash `cb4cddfe466fe5e8e92103196faa5e53b9b45bd13837abcade898538639f5911` 未消费：初始 driver 封存 batch ceiling 1，repair readiness 改为 2 时，committer 拒绝 `Generation submit ceilings cannot expand within one task.`。修复 attempt-02 只有 pre-submit state，repair submit count 0；没有 novram 生成或性能成功证据。

Own ComfyUI queue 为空后已停止 own service，原 `jianji-qwen3-vl.service` 已恢复，实际 readback `ActiveState=active, MainPID=599082`。不能把此环境恢复称为 OOM 已解决。

## UI Fix And Verification

真实长 hash/path 暴露 report 在 390px viewport 的横向溢出，article 约 666px。Parent 实际复现并修复 `scripts/visual_quality_report.py` 的长词换行及 flex wrap，commit `8f684036512e1f0ef9752ce53c31cc106392ee7e`。

使用 gstack browse 验证真实报告：local 广告在 390px 和 1280px 均无 overflow、5 张图加载，剧情 API 在 390px 和 1280px 均无 overflow、7 张图加载，显示 FAIL。local 广告原 MP4 浏览器已实际推进播放时间至 1.256906 s，muted；仅证明解码/播放，不证明完整观看或聆听。证据在 `R/browser-evidence.json`。

UI focused tests 82 PASS。code commit exact range 的 Harness receipt：`.agent/harness/runs/creative-real-report-wrap-commit-20260927-02/receipt.json`，7 checks PASS，code checkpoint 的 integrity/freshness/snapshot/artifact/coverage verification 全部通过。该 receipt 绑定 code checkpoint，不冒充后续 docs commit 的 fresh receipt。

Managed Kimi mapping invocation `bc2f9855-6eb3-42e8-b764-cc3fe4b5a47e` 返回 `PROTOCOL_ERROR`；未手工改 canonical receipt 或把不合格结果算作 review acceptance。Parent 自行核对 canonical composition/source-admission 边界。局部 CSS 为 T0；本轮没有新增 Runtime contract。

## Evidence Index

每个 independence key 绑定一次真实 request；同一 attempt 的 receipt、technical、analyzer、human 层不重复计数。下列非 Q0 keys 使用 exact request hash，runtime/model 边界见上表；无受控因果 comparison arm，`arm_id=N/A`。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ad-local-analysis | request:80073fa3d81fa7f8a43b321dc2eedd24f85999c3cf8cd500385efabae42857e5 | creative-goal-real-20260927 | advertising-local-attempt-01 | N/A | 376b5562701c119f6eada740dbede12964dd2a2fbdbd1aefed94d47e4fbb5a68 | analyzer | FAIL | QUALITY_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-real-test-20260927-001/advertising/local/diagnosis.json |
| ad-api-analysis | request:658caa81512eabd1d4d51d625d14d08ed3c73dfbcf89c89ccbde2c58546c6bcf | creative-goal-real-20260927 | advertising-api-attempt-01 | N/A | f29f434df0835df4b275056feb6c2dfce7ee98ce152e6cd07abd71ac7279f03a | analyzer | FAIL | QUALITY_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-real-test-20260927-001/advertising/api/diagnosis.json |
| drama-local-runtime | request:fc06e0acfc7ed216ebf73e34bf5a06b77d08814ff27c6e3aaef2f6f95aedb8fb | creative-goal-real-20260927 | drama-local-attempt-01 | N/A | NO_ARTIFACT:CUDA_OOM | provider_receipt | FAIL | RUNTIME_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-real-test-20260927-001/drama/local/runtime-failure.json |
| drama-api-analysis | request:38a97501f1e96eb6726008f2838e45388ba4aaf24790faf4cbf3714be21ea45c | creative-goal-real-20260927 | drama-api-attempt-01 | N/A | 270dbec018a5b7ab2bb312c8a11296c29572aa769606afbcd117b027d9de7bd6 | analyzer | FAIL | QUALITY_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-real-test-20260927-001/drama/api/diagnosis.json |

## Learning Evaluation And Remaining Work

`distill-ai-video-learning` outcome：`no_candidate`。三个媒体负例的具体失败分别是衣着、泵头、因果/交接；另一个是 OOM。没有两次支持同一有界新机制的证据，Provider、尺寸、时长和内容也未保持受控。现有 `h3-shot-local-visible-context` claim 明确限定灯塔 T2VA / 124 frames 并排除 I2V；本轮不是对其适用范围内的 material update。不能从这四次结果推导模型排名、成功率或扩大 adopted guidance。

恢复出片的最小条件：以合法且充分封存的 task ceiling 支持独立本地 repair，而非改 Manifest 或借新身份绕开旧 ceiling；修复并重验具体媒体失败；完整广告另须 canonical source admission 和 composition；最终完整原速观看与实际聆听仍必需。当前不能将任何一条路径称为合格成片。

## Publication And Checkpoint

本记录及原记录 supersession notice 只包含当前 task-owned docs；unrelated `.codex/config.toml` 保留。无 push/release。记录/learning evaluation 本身没有 Provider submit、媒体生成或为凑记录而追加测试；文档按 Harness policy 另行验证。检索使用 last-good advisory evidence，未手动 rebuild RAG index，不保证新记录已进入检索索引。

`capture_request_id=ai-video-record-26b95842b89fe19c` 已在原 implementation checkpoint ACKED，state 实际为 `recorded / no_candidate`；本轮不重复 acknowledge 同一 ID。
