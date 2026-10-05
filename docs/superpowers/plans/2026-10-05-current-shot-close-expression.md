# Current Shot Close Expression Implementation Plan

**Goal:** 提供 authoritative current-close preimage并贯通 compiler / raw evaluator / accepted source。

**Scope:** existing GenerationIntent additive facts、shared validation/rendering、remote/local grammar、QA projection、focused fixtures。

**Contract Surfaces:** typed state单载荷、Planner/Router selection、immutable requirement、evaluation presentation、Manifest ownership。

**Invariants:** opaque digest只作seal；opening不授权closing；canonical facts与close hash精确一致；0 live effects。

**Compatibility:** absent facts不序列化，历史hash/text golden不变；旧证据不重写。

**Spec:** [bounded spec](../specs/2026-10-05-current-shot-close-expression.md)。

## Major Milestones

### Milestone 1: Authoritative Current Close

Files：`video_requirement.py` additive field与validation；new production leaf `_causal_state_expression.py`
负责 complete ordering/hash、sealed current-close verification、shared endpoint renderer。
author提供全部十维，schema拒绝missing/unresolved/mismatch；旧无facts serialization相同。
Acceptance：schema/requirement负例、hash congruence、wrong Shot/stale binding拒绝。

### Milestone 2: Native Expression

Files：`_remote_video_native_prompt.py`、`_h3_prompt.py`、`video_compiler.py`，以及四个local H3 consumers。
remote closing 从 sealed requirement独立获取；local arbitrary hashes拒绝，verified opening使用existing owner，
closing复用同一leaf；exact compiler按grammar重新验证，不由adapter拼truth。
Acceptance：endpoint authority separation/equal digest、remote regression、local与text goldens。

### Milestone 3: QA Preimage And Offline Bootstrap

Files：`generation_evaluation_criteria.py`、`generation_evaluation.py`、`generation_feedback.py`、
`generation_experience.py`、`generation_diagnosis.py`、`_sequence_source.py`、
`ai_video_mcp/generation_feedback.py`及现有evaluation validation callers（仅透传sealed requirement）。
QA facts从execution projection派生并bound到question/item；完整recipe规则保留close hash，
fresh事实要求marked evaluator问题，不接受hash-only的PASS。
Tests：new `tests/test_current_shot_close_expression.py`，复用existing standard project/runtime factory。
Acceptance：fresh Planner/Router/selected METASO compiler/exact pre-submit 0 effects；
scripted fetched result → controlled analyzer PASS → activation/terminal → accepted_source，
明确为offline lifecycle evidence；缺失/过期preimage与question均阻断。

### Milestone 4: Verification And Closure

更新contract matrix/runtime baseline；focused tests与Architecture Gate后对owned commit range运行Harness，
核验receipt scope/policy/artifact hashes。Parent self-review与Implementation Risk Gate绑定stable candidate。
按record-ai-video-session记录并评估learning；只commit/push owned paths，不夹带existing staged Harness changes。
若review所需外部route违背当前0 effects约束，明确边界并使用只读native工程review。

## Self Review

每项Spec acceptance映射以上milestone；无未定schema/owner或microstep placeholders。
Native Codex保持primary，串行写入；不创建development worktree。
