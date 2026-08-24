# All Scope

Use `all` when one decision genuinely needs cross-category project evidence.
It covers all project Markdown under `docs/` through authority-separated
collections: top-level current docs, experience records, Superpowers history,
research, and deferred when-to-do decisions. If experience or Superpowers alone
answers the question, select its narrower scope instead.

At the default Agent-facing Top-N of 8, the five main collections receive a
stable `2/2/2/1/1` quota for `experience`, `superpowers`, `current_docs`,
`research`, and `deferred` before the final merge. Eligible run summaries are
queried through their separate index. The quota preserves visibility; it does
not make the authority classes equivalent.

## Query Shape

Use shared terms that occur in both implementation history and design intent:

```text
<surface> <observed problem> <contract or intended decision>
```

Useful examples include:

- `cross-shot continuity rejected attempts provider-neutral contract`
- `state recovery incident single writer design`
- `native audio observed artifact canonical mixer ownership`

Run:

```bash
python -m scripts.agent_memory --scope all search \
  "<task-specific query>" --top-k 8 --json
```

This command queries five dedicated main-corpus shards plus the eligible
run-summary shard. Stale last-good fragments identify their shard via
`corpus_kind` and `index_freshness=stale`; only those shards are queued for
detached refresh. Missing or legacy layout returns exit `3` after queueing the
required materialization. Follow the parent skill's non-blocking result rules
and never run a foreground recovery build.

## Interpretation

- Group the result by `authority` and `corpus_kind` before drawing a
  conclusion. Do not flatten experience and historical plans into one truth.
- Use current contract and runtime-baseline hits only after reopening the exact
  source and checking freshness; roadmap hits describe direction, not runtime.
- Use experience hits to understand observed outcomes and failure history.
- Use superpowers hits to understand historical intent and tradeoffs.
- Use research as advisory external evidence and deferred hits as conditional
  timing guidance, never as current execution authorization.
- Reopen important sources, then reconcile both groups against current code,
  tests, contracts, receipts, and runtime evidence.
- If the two groups disagree, preserve the disagreement explicitly; do not let
  RRF order or a higher score resolve an authority conflict.
