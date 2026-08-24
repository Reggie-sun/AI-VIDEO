# Experience Scope

Use `experience` for reusable runtime lessons, actual failures, recovery
evidence, Provider/model observations, continuity work, media-quality findings,
and prior production decisions recorded under `docs/record_for_agent/`.

This scope also merges eligible one-level `runs/<run_id>/SUMMARY.md` records
through the separate run-summary derived index. Run-summary hits use
`authority=auto_generated_run_summary_advisory` and
`document_kind=run_summary`, and expose status, `run_id`, `run_family`,
`run_version`, and `summary_sha256` provenance.

## Query Shape

Build a compact query from the current task:

```text
<surface or provider> <failure/quality/decision> <important identifier>
```

Useful examples include:

- `H3 cross-shot identity continuity terminal frame`
- `Seedance fetched candidate native audio failure`
- `ProductionStateCommitter recovery unknown outcome`

Run:

```bash
python -m scripts.agent_memory --scope experience search \
  "<task-specific query>" --top-k 8 --json
```

This command queries the canonical per-corpus shards. Stale last-good fragments
are explicitly tagged and their exact shards are queued for detached refresh;
missing or legacy layout returns exit `3` after queueing materialization.
Follow the parent skill's non-blocking result rules and never run a foreground
recovery build.

Prefer one precise query. A second query is justified only when the first
reveals a distinct historical term, owner, or failure signature needed by the
task. Do not broaden merely because the result abstains.

## Interpretation

- `authority=advisory_experience` records lived project lessons, not current
  runtime truth.
- `document_kind=run_summary` records an auto-generated run summary; it is not
  activation, quality acceptance, or delivery truth.
- Reopen the returned `source` before relying on a specific claim, path,
  receipt, hash, or historical outcome.
- Recheck current code, tests, manifests, receipts, and runtime evidence before
  acting on retrieved history.
