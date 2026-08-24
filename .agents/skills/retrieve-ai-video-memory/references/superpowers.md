# Superpowers Scope

Use `superpowers` only when the task needs historical architecture, specs,
plans, tradeoffs, phase intent, or an earlier rejected design recorded under
`docs/superpowers/`.

Do not select this scope merely because the task is large. Current accepted
contracts, code, tests, runtime baseline, and user instructions remain higher
authority than historical design artifacts.

## Query Shape

Name the architectural surface and the decision being investigated:

```text
<owner or contract> <invariant/tradeoff> <phase or failure mode>
```

Useful examples include:

- `ProductionStateCommitter single writer recovery contract`
- `ResolvedTimeline canonical timing alternate path`
- `generated video provider lifecycle unknown outcome`

Run:

```bash
python -m scripts.agent_memory --scope superpowers search \
  "<task-specific query>" --top-k 8 --json
```

This command only validates and queries the materialized main index. If it
reports a missing, stale, partial, or identity-mismatched index, return to the
parent skill's explicit `--scope all build` recovery rule; search itself must
not rebuild.

## Interpretation

- Every hit has historical design/plan authority. It is evidence of what was
  proposed or reasoned about, not proof that runtime implementation exists.
- Reopen the exact `source` and distinguish spec, plan, roadmap, and accepted
  contract status before using a claim.
- A hit cannot authorize implementation, Provider execution, schema changes,
  migration, activation, push, or release.
- When historical design conflicts with current executable behavior, report
  the conflict and follow current code/tests plus canonical repository rules.
