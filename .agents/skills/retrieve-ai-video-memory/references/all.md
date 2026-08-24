# All Scope

Use `all` only when one decision genuinely needs both lived project experience
and historical architecture/spec/plan evidence. If either source family alone
answers the question, select its narrower scope instead.

At the default Agent-facing Top-N of 8, retrieval allocates an approximate 4/4
quota between `experience` and `superpowers` before the final merge. Eligible
run summaries participate through the experience side. The quota preserves
visibility; it does not make the two authority classes equivalent.

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

## Interpretation

- Group the result mentally by `authority` and `corpus_kind` before drawing a
  conclusion. Do not flatten experience and historical plans into one truth.
- Use experience hits to understand observed outcomes and failure history.
- Use superpowers hits to understand historical intent and tradeoffs.
- Reopen important sources, then reconcile both groups against current code,
  tests, contracts, receipts, and runtime evidence.
- If the two groups disagree, preserve the disagreement explicitly; do not let
  RRF order or a higher score resolve an authority conflict.
