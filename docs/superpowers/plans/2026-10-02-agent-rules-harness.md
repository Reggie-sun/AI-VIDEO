# Agent Rules Harness Implementation Plan

## Goal And Scope

按 [spec](../specs/2026-10-02-agent-rules-harness.md) 精简 root guide 与两份 context，
为 migrated deterministic rules 接入现有 Harness，保护不能离线证明的规则。Native Codex
串行执行，Parent 保留全部写入和裁决；独立 reviewer 只读。

## Milestones

1. **Executable Migration**：新 registry、gate 与 mutation tests；policy 绑定实际 existing
   invariant test nodes 和新 gate。验证失败状态、context containment、policy selection。
2. **Documentation Reduction**：`AGENTS.md` 与 `.agent/context/*.md` 删除重复契约/字段/
   历史数据，保持 anchors、Skill routing、授权/安全/逐 Shot 规则；matrix 与 baseline
   仅增加新 owner/验证入口。文档 bytes/lines 限额通过 gate。
3. **Checkpoint**：focused tests、exact snapshot Harness；同一 snapshot 的 read-only Kimi
   与 native reviewer 双独立 review。Parent 调查 findings、修复并重验；session record、
   learning evaluation、task-only commit。保留已有 staged config，不创建开发 worktree。

## Acceptance

两份入口实际变短；规则绑定到执行测试；registry/links/体量变坏会失败；fresh exact-snapshot
receipt；review blocker 全部裁决。无 Provider/media/activation/push/release。

## Self-Review

覆盖 spec 全部契约；无新增 Product owner 或 lifecycle。Harness 自身的 temporary verification
checkout 仍由原实现管理。现有 staged config 从 task staging/commit 与测试 snapshot 中排除。
