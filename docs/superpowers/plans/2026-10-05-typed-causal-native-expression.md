# Typed Causal Native Expression Implementation Plan

**Goal:** 仅让 exact verified sequence opening hash 由 shared native owner确定性表达。

**Scope:** ephemeral evidence seam、shared grammar、remote compiler pass-through、canonical prepare/recompile、
tests 与 canonical research/spec/baseline/record。Spec 为 [typed-causal-native-expression](../specs/2026-10-05-typed-causal-native-expression.md)。

**Invariants:** state kind不变；previous-close/current-open/current-close严格分离；无凭据/Provider effects；
existing continuity、Router、Planner、QA owner不变。无 evidence时 fail closed；TYPED_TEXT bytes不变。

## Milestone 1: Owner-Issued Read-Only Evidence

Files：`production/_sequence_source.py` 复用现有 accepted source/column/Planner reopen，
独立小模块保存 ephemeral verified opening context；`planning/sequence_continuity.py`
仅复用 existing preimage字段保存所有materialized edge。context绑定完整requirement与bound seals。
Acceptance：只读 standard source lifecycle签发；完整十维、exact policy/target/binding/hash拒绝路径均覆盖。
无public facts constructor，无新durable schema，historical缺字段不得取得新coverage。

## Milestone 2: Shared Grammar And Canonical Wiring

Files：`_remote_video_native_prompt.py` 保留text path并只展开verified opening；
METASO/H3/Hailuo/Seedance/Vidu和`_vidu_prompt.py`仅传optional context；
shared `video_compiler.py`、voice/subject verification沿同一context重编译。
`generation_feedback.py` / `video_generation.py` 在canonical preparation / current recompile重新签发。
Acceptance：无hash narrative；current close hash拒绝；新control coverage不能仅caller自报；
旧two-argument calls与非共享grammar保持行为；0真实effect。

## Milestone 3: Offline Proof And Delivery

Tests：独立typed-expression suite与METASO canonical-style integration；重用standard Project/Manifest
source fixture，明确scripted fixture不证明real source acceptance。先red后green；原text/native body
hash regression、remote adapters、sequence、execution、voice、subjects相关suites。
执行`make harness-inspect`与exact staged Harness；源码/receipt hashes核验后在stable snapshot双独立review。
Parent裁决并修复阻断findings，semantic fix重验/必要re-review；不降低checks或质量要求。
完成AOCI维护评估、record/learning evaluation、精确owned paths commit/push main，报告出版状态。

## Self Review

Spec各项对应owner/evidence、grammar/wiring或verification milestone；无独立生命周期扩张。
current close与cross-stack seed限制在最终报告保留，不能把工程compile视为media acceptance。
