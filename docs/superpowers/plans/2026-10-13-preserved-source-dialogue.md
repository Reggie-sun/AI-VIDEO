# Preserved Source Dialogue Implementation Plan

**Goal:** 原剧本 typed dialogue 输入可忠实通过 existing source compiler，而未声明或矛盾字段仍拒绝。

**Scope:** 共享 source dialogue mapping、failure-path tests、原 S01/S02 data 的显式适配与忠实度矩阵。

**Contract Surfaces:** compiler v3 保持、GenerationIntent 保持、source prose 与引用 hash 保持，控制路径必须逐字段有精确声明。

**Invariants:** no Provider POST；无音轨替换、新 renderer、故事执行脚本、第二 timeline、acceptance bypass。

**Compatibility:** 无 migration；既有中文无窗对白沿原 mode/language mapping；其他未表达 rich fields 仍拒绝。

**Spec:** `docs/superpowers/specs/2026-10-13-preserved-source-dialogue.md`

## Major Milestones

### 1. Reproduce And Map Exact Dialogue Controls

- Create `src/ai_video/production/seedance_source_dialogue.py`：纯 source declaration 校验，输出有依据的 control paths。
- Modify `seedance_source_expression.py`：source compiler 消费该结果，不改写 prose。
- Create `tests/test_seedance_source_dialogue.py`：正例、错字段、漏声明、未表达其他字段、native audio 拒绝和 bytes preservation。
- Modify `.agent/harness/policy.yaml`：把新helper/test接入已有preserved-source suite与changed-path routing；不删旧检查，不降低Gate。
- Verification：targeted pytest、existing source compiler/common compiler suite；保留 red/green 证据。

### 2. Preserve Original Data And Publish Reviewable Evidence

- Owned directory `docs/canvas-projects/jieshi-original-s01-s02/`：原文映射、两个原镜 source/director data、字幕与 canonical composition 职责、真实能力缺项与有限预算提案。
- 重跑 public inspect/author/preflight，明确历史 PNG 和 future state 均未准入；raw compiler expression diagnostic 不等同 qualified runtime。
- `record-ai-video-session` 记录具体声音缺口与 Kimi mapping adjudication；exact staged Harness、Risk Gate、owned commit/push。

## Self Review

本 plan 逐项覆盖 spec；只增加一种明确 source 声音声明的通用 mapping。Compilation、真实 Gate、composition 和 human acceptance 分别报告。没有批准的新图片/视频单元，因此只继续可逆数据准备和离线验证，付费路径停止。
