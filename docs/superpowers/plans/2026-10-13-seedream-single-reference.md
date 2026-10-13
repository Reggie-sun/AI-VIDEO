# Seedream Single PNG Reference Implementation Plan

**Goal:** 原首帧/clean plate 可经现有 image owner 绑定单张 exact PNG，而旧纯文字路线不变。

**Spec:** `docs/superpowers/specs/2026-10-13-seedream-single-reference.md`

**Scope:** request/preview/result 的窄版本扩展、opt-in profile、reference byte resolver、paid egress 和公共 lifecycle 验证；不生成图片。

**Invariants:** 原文不强制视频 overlay；不创建第二 timeline/renderer/state；raw per-shot Gate 不变；没有本任务的新付费许可。

## File Ownership

- `production/seedream_reference.py`：单 PNG reference measurement、版本与 preview consistency 的纯 helper，避免扩大 image God Module。
- `production/image.py`：复用 helper 验单 scene reference，区分 `/4` 与 `/5` request/result identity。
- `production/seedream.py`：显式 opt-in profile，注入 exact byte resolver，egress/native payload 和 permit 前重验。
- `tests/test_seedream_remote_image.py`：公共 committer activation/reopen/replay 与 failure-path；保留旧 T2I checks。
- `.agent/harness/policy.yaml`、matrix：把新 helper 归 existing image suite/owner，不降低 checks。
- 原候选 README / current record：纠正“clean plate 必須视频 overlay”的过早假设，保留几何、audio、人验及 paid 缺口。

## Major Milestones

### 1. Seal Exact Single Reference Without Changing Text-Only Identity

红测先覆盖旧 profile 拒绝与新 profile 公共生成、preview reference accounting、reference drift 在 credential/permit 前拒绝。增加 pure helper 和 adapter 接线，使用现有 canonical ImageReferenceBinding/PNG measurement/remote egress。只接一张 scene PNG，返回 Provider original PNG，不重编码。Native text 原样，包括作者审核后的 `<bbox>`；helper 不猜坐标。

### 2. Verify And Publish The Necessary Capability Boundary

运行 focused image/remote lineage suites、Architecture Gate、exact staged Harness/fresh receipt。稳定候选按 SUBAGENTS Risk Gate 判断一次；mapping 调用不代替 final review。使用 record-ai-video-session 记录 parent 对 Kimi findings 的裁决及新增工程证据；自动 learning 为无独立媒体证据时 no_candidate。只 commit/push owned paths 并核验远端 main SHA。

## Self Review

没有承诺新图、plate 几何、听音、qualified 视频 preview 或成片 PASS。未使用旧 B 额度或 Vidu permit。Spec 每个 contract 有输入/失败/兼容性验证；新画像最终仍须独立准入、QA 与 fresh 付费授权才能进入原 S01。
