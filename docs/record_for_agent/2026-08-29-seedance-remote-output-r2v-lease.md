---
record_kind: architecture_implementation
topic_id: seedance-remote-output-r2v-materialization
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Seedance Remote Output R2V Lease Record

Date: 2026-08-29

## Purpose

本文记录 Seedance 生成结果直接作为后续 Shot `reference_video` 的 provider-output
垂直切片，以及 Ark `Active asset + human confirmation` 的真实边界。

本记录是 architecture implementation checkpoint。它不证明 live paid R2V、两段媒体的
continuity quality、P6、Final Acceptance、push 或 release；代码、测试与 exact Harness
receipt 仍是 executable truth。

## Official Constraint Versus Repository Contract

官方 ordinary reference-video API 接受 Provider 可访问的 HTTP(S) URL，也支持
`asset://...`。因此，Ark Console `Active asset` 不是普通 R2V 的唯一 API 通路；
`SeedanceAssetMaterializationReceipt` 中的 human-observed `Active` 是 AI-VIDEO 为
already-materialized Ark identity 建立的本地 fail-closed contract。

完整调查、官方链接与 prior-art 见
`docs/research/2026-08-29-seedance-r2v-usage-and-ark-asset-flow.md`。关键边界是：

- Provider output URL 是短期 transport locator，不是 durable identity。
- durable evidence 必须绑定 task/model、opaque Provider file identity、locator hash/origin、
  exact downloaded bytes SHA-256、size、MIME 与 fetch lineage。
- raw local path 或 Registry ID 不能伪装成 URL 或 `asset://`。
- Ark `Active` lane 继续服务既有 trusted/materialized assets，不因本 slice 被删除。

## Implemented Runtime Truth

当前 runtime 已支持同一 Seedance Provider 的 exact fetched output 作为下一次 Mini
`VIDEO_EXTEND` / R2V 输入：

1. `src/ai_video/production/remote_media.py` 的
   `RemoteMediaMaterializationReceipt` 保存 durable、provider-neutral remote identity，
   但不持久化完整 signed URL。
2. Seedance exact fetch 将 remote materialization 附着到 `VideoFetchReceipt`；历史没有该字段
   的 receipt 保持原 fingerprint/serialization compatibility。
3. `VideoGenerationService.refresh_remote_reference_lease_once()` 是唯一 refresh authority。
   它先通过 Manifest replay 验证 source attempt 仍是 exact current-active video，再重开
   submit/status/fetch evidence，并签发 process-local one-use permit。
4. Seedance helper 消费该 permit 后重新查询同一 Provider locator，并用完整 GET 验证
   exact bytes、MIME 与 container 未变化，才能签发最长五分钟的
   `SeedanceRemoteReferenceLease`。
5. `SeedanceRemoteReferenceResolver` 只把 exact matching `reference_video` binding 投影成
   HTTPS input；resolve 与最终 paid POST 前都会重新验证 lease 与 source-active 状态。

stale source、公开/重复 mint、locator rotation、bytes drift、lease expiry、identity mismatch
或 refresh-to-POST TOCTOU 都在 paid permit 消费和 POST 前 fail closed。该 transport failure
不会静默退化成 I2V。

Continuity contract 仍负责选择语义路径：需要完整动作、运镜或时间上下文延续时选择
`reference_video` R2V/extension；只需要 terminal frame 视觉锚点时可选择 last-frame I2V。
I2V 不是基础设施失败后的 fallback。

## Implementation And Publication State

本 slice 的 task commits：

- `e153985` — `feat: enable verified Seedance output R2V leases`
- `59ce71f` — `refactor: isolate remote media contracts`
- `416df80` — `test: route remote media through video policy`
- `0e11625` — 保持 shared tree 不变的 verification merge；其第二 parent
  `26fb249` 构造仅包含本 task 14 个 paths 的 exact diff base。

涉及的 canonical docs、Provider/runtime modules、tests 与 Harness routing 已进入本地
`main`。本 session 没有执行 push 或 release；共享 `main` 后续还有其他 writers 的无关
commits，因此不能把当前 `HEAD` 本身等同于本 task snapshot。

## Verification And Review Evidence

authoritative exact-snapshot receipt：

`.agent/harness/runs/seedance-r2v-remote-identity-final-v4-workspace/.agent/harness/runs/seedance-r2v-remote-identity-final-v4/receipt.json`

receipt 对 `26fb249..0e11625` 的 14 个 task-owned paths 报告 `status=passed`，且
`verify-receipt` 的 integrity、scope、snapshot、freshness、closure、workspace-stability 与
cleanup assertions 均为 true。主要 executable evidence：

- final policy matrix：`560 passed`；
- focused Seedance/video-generation matrix：`227 passed`；
- Harness policy tests：`133 passed`；
- full Production contract check：`2945 passed, 3 skipped, 1262 deselected`；
- Harness-own tests：`204 passed`；
- CLI config：`13 passed`；
- provider-neutral video requirement：`359 passed`；
- Architecture Gate：`PASS`，zero errors，两个 existing oversized-growth warnings。

native `reviewer_xhigh` 对 implementation、authority owner、lease/bytes/TOCTOU、architecture
relocation 与 policy mapping 做了 scoped re-review，最终 verdict 为 `accept`，无 blocking
issue 或 non-blocking concern。

以上全部是 offline engineering evidence。本 slice 没有调用 credential、paid Provider、
remote submit、媒体生成、upload、activation、P6 或 Final Acceptance。

## Remaining Risks And Next Work

- local H3/T8 MP4 自动上传受控 object storage、presigned URL refresh、egress/provenance 与
  provider-neutral materialization receipt 尚未实现；不得把当前 Seedance-output-only permit
  泛化为本地 uploader authority。
- 尚未执行真实 Seedance Shot 1 -> Shot 2 R2V chain；API acceptance、billing settlement、
  transient URL lifetime 与 continuity quality 仍是 live/empirical uncertainty。
- 两个 15 秒电影感连续 Shot 仍需独立 approved creative contract、paid execution gates、
  每 Shot `video-analysis` Gate 与 human quality verdict。
- RAG index 没有在本 session 刷新；本记录的 repository bytes 已提交不等于 retrieval index
  已包含它。

## Agent Guardrails

- `remote_url exists` 不等于 durable materialization；必须验证 exact bytes 与完整 lineage。
- `fetch succeeded` 不等于 source attempt 仍是 Manifest current active。
- `RemoteMediaMaterializationReceipt` 不得保存完整 signed URL。
- `SeedanceRemoteReferenceLease` 是短期 in-memory transport authority，不是 durable asset。
- provider-output R2V offline PASS 不等于 live chaining、continuity quality、P6 或 delivery。
- H3/T8 object-storage path 必须作为新的 authorized slice 实现，不得旁路
  `VideoGenerationService`、Cloud Egress、Budget/permit、provenance 或 canonical committer。
