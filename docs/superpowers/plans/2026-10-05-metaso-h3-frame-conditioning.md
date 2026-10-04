# METASO H3 Frame Conditioning Implementation Plan

**Goal:** existing METASO H3 stack 正式消费 first / optional last conditioning，到达 exact pre-submit。

**Scope:** `metaso_h3.py` 与 METASO tests；现有 Provider docs/runtime baseline 与新 continuation record。

**Spec:** [accepted spec](../specs/2026-10-05-metaso-h3-frame-conditioning.md)，Parent task-scope self-review。

**Invariants:** Ref2VA native body/variant/profile serialization 不变；continuity owners 不变；
Registry bytes 保持；所有项目验证 offline，H3 credential/transport/effects 为零。

## Milestone 1: Exact Offline Regressions

在 `tests/test_production_metaso_h3.py` 新增 frame input fixture 与矩阵：first-only、
optional last、native ordering、missing/wrong roles、bytes/MIME/geometry/size defects；
Router existing EXACT_TERMINAL/HardCut C2 fixtures 使用真实 METASO capabilities，
compile/resolve/preview/native body 经无 effect spies 验证。先确认 baseline 上新增测试失败。

## Milestone 2: Bounded Adapter Coverage

在 `src/ai_video/production/metaso_h3.py` 保持 Ref2VA variant，adaptive profile 新增
single FL2VA variant。resolve 按 supported mode 选择 variant；frame size 必需。
native payload 保持 Ref2VA 原逻辑，frame role 使用 existing binding.role、按 first/last 排序，
省略 ratio，验证 encoded image metadata/bytes。不改 shared grammar、continuity或 transport。
等待 sealed read-only research receipt 校验后才修改冻结源码。

## Milestone 3: Verification And Delivery

运行 METASO → Router/continuity → local H3/provider family；复核 exact diff、未修改 owners、
Ref2VA fingerprints/native bytes、no H3 effects。更新 `docs/metaso-h3-provider.md` 与
`docs/v0.2-runtime-baseline.md`，新增 session continuation。按 stable snapshot Review Risk Gate
裁决，运行 scoped Harness 并验证 receipt；只 stage/commit owned files，push main。
保留历史 admission STOP 与 S02/S03 verdict；后续创建 fresh accepted source。

## Self Review

spec 的 capability、native、validation、compatibility、fail-closed 和 integration 均有上述
milestone/验证 seam；无架构扩展、隐式 Provider effects 或待定 implementation choices。
