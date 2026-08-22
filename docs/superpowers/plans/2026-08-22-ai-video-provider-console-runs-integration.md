# AI-VIDEO Provider Console Runs Integration Implementation Plan

## Status

Executable。Governing spec：
`docs/superpowers/specs/2026-08-22-ai-video-provider-console-runs-integration.md`。

## Contract Checkpoint Before Code

- **Problem boundary:** 当前 Provider Console 是硬编码 demo，没有消费 `runs/`。
- **Single read projection owner:** new `ai_video.provider_console`。
- **Canonical readers:** Production `load_production_project()` +
  `load_video_request_receipt()`；Legacy `load_manifest()`。
- **Old path to retire:** `App.jsx` 的 static `LANES`、Alice Project/Shot/evidence 和 prototype intent。
- **Unchanged contract:** no Production/Legacy mutation、no Provider/network、no fallback、no raw payload。
- **Focused verification:**
  `python -m pytest -p no:cacheprovider tests/test_provider_console.py -q`。

## Change Surface

### Create

- `src/ai_video/provider_console.py`
- `tests/test_provider_console.py`
- `provider-console/scripts/runs-api.mjs`
- `provider-console/tests/runs-api.test.mjs`

### Modify

- `provider-console/vite.config.mjs`
- `provider-console/src/App.jsx`
- `provider-console/src/styles.css`
- `provider-console/design-qa.md`
- `provider-console/AGENTS.md`，记录 durable “real runs, no static demo fallback” rule。
- canonical runtime docs / Harness policy only if exact changed-path inspection requires routing updates。

### Must Not Modify

`runs/**`、Production Manifest/models/committer/provider owners、Quality Intelligence、`.workflow/**`、
其它 Agent 正在修改的 files。

## Implementation Sequence

### T1 — Python RED/GREEN projection

先写 tests，覆盖 bounded discovery、Production strict detail、latest real attempt projection、Legacy root
manifest、invalid workspace、traversal/symlink、sanitization、media token allowlist 与 zero writes。观察 RED 后
实现 minimum projector，并用同一 command GREEN。

### T2 — Node local bridge RED/GREEN

测试 GET/HEAD routes、405、400/404、Python subprocess failure、JSON sanitization、opaque media token、range、
no-store 与 static fallback。实现 dependency-free Vite middleware；不修改 Sites worker contract。

### T3 — Data-driven Chinese UI

把静态 constants 替换为 fetch state：workspace selector、refresh、real attempt rail、real Project/Shot header、
real capability/evidence、registered image/video preview、loading/empty/invalid/unavailable states。保留选定视觉
source的布局与中文层级；CTA保持只读。

### T4 — Verification And Review

运行：

```bash
python -m pytest -p no:cacheprovider tests/test_provider_console.py -q
npm --prefix provider-console run test:sites
npm --prefix provider-console run build
node --test provider-console/tests/runs-api.test.mjs
```

启动 local preview，用用户已选择的 Chrome 检查真实 catalog、Local H3 workspace、cloud workspace、媒体、
错误/空状态、键盘可访问性、console/page/network errors，并对比 reference layout。运行 independent reviewer。

### T5 — Exact Closure

比较 `runs/` pre/post tree snapshot；只 stage task-owned files；运行 exact staged Harness，commit，再运行 exact
commit-range Harness/receipt verification。报告 local commit、receipt、未 push/deploy 与 remaining boundary。

## Rollback

回滚仅删除/恢复本 task tracked files与frontend integration；不删除任何 `runs/` artifact或Harness history。
