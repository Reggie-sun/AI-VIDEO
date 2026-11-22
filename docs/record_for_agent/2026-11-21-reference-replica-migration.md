---
record_kind: architecture_implementation
topic_id: reference-replica-migration
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Reference Replica Migration Record

Date: 2026-11-21

## Ownership

从 AI_daily `80abf28cf6558a72b622c1f034153e451f8a6ded` 迁入独立 Agentcut 复刻工具。原片参考、整稿确认、隐私复查及本地交付由 `reference-replica` Skill 路由。Production 的时序、渲染和验收继续走原 owner。配音通过独立声音项目的现有 MiniMax adapter、Paid Provider Gate、Registry 和 `ProductionStateCommitter`。语义审核交给 `audio_understand`。实现范围与验收入口见 [迁移方案](../superpowers/specs/2026-11-21-reference-replica.md)。

## Offline Evidence

将原提交的源码和范例提取到临时目录，为原脚本和迁移脚本分别创建空 Agentcut 项目。以下 SHA-256 来自逐字节相等的三份 `layers.json`。范例中只有镜头表与数据。

| Cut | Bytes | SHA-256 |
| --- | ---: | --- |
| 完整版 | 52,188 | `49d4e08528d7f6af3e217cfc366c95814b654cb78c2cfb5d5dc73761e20c95ab` |
| 上集 | 37,825 | `5417f39ba1321e7f5bcf6ca34525ab12b88735e6ccb8c8e4ceca810e7a42cdd4` |
| 下集 | 17,263 | `555f7aea6b998fc0c31badae638e0e91d9503f309cf1aad81515c487f9cf91cd` |

本地 pytest 共 51 项，通过 27 项源行为回归、两项独立工程用例、六项配音用例及 Claude adapter 检查。配音用 fake transport 测试同一期的 canonical 写入和重开，覆盖结果未知、请求中断、WAV 缺失及仅重配改动段。实际 CLI 回归验证受信 operator 可加载，且拒绝授权时停止。打码、拼图、交付转码和封面使用本地合成素材烟测。期间没有启动 Agentcut、调用付费服务或访问已交付客户的工程。

首次 `make harness-verify LEVEL=focused` 在 `task_architecture_gate` 失败，receipt 为 `.agent/harness/runs/reference-replica-20261121-focused/receipt.json`。当时基础 `964cf680` 中 `architecture_gate.toml` 对 `production/_sequence_source.py` 读取 `planning.video_planner` 的例外已于 2026-11-05 到期。首次迁移阶段保留该文件和依赖关系。仓库级 Architecture Gate 重现 `ARCH004`。

## Architecture Repair

用户随后授权修复门禁。基于当时 HEAD `9482f04d`，将已有 Planner、exact projection 与 Readiness 的纯实现归到 `production/generation_preflight/`。原公开入口重用同一对象。序列读回仍重算 neutral seed 和 sealed final request，ARCH103 到期例外已删除。方案与当前 owner 见 [Planning Preflight Boundary Repair](../superpowers/specs/2026-11-21-planning-preflight-boundary.md)。

仓库级 Architecture Gate 以当前日期通过，0 个错误。与 `9482f04d` 的隔离副本相比，代表性的 v2、动态 v3 和静态 v3 request、plan、readiness request/result 及其内含 projection 共 72,322 字节逐字节一致，SHA-256 为 `e7c480abab92adc821a27861e9247c8627a7d7f6d0dcb072652478ca735377b1`。原门禁失败回执继续作为当时的证据。

## Evidence Limits

真实配音仍以获授权音色、可信 operator 及客户用途许可为前提。实际 Agentcut 渲染、语义听审、打码完整性和用户观感留给制作时的原片证据。当前只有迁移和确定性技术证据，learning 评估为 `no_candidate`。
