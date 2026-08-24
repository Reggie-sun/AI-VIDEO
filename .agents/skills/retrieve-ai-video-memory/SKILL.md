---
name: retrieve-ai-video-memory
description: Retrieve authority-separated AI-VIDEO project docs, experience, run summaries, research, deferred decisions, or historical specs/plans before substantial work involving production quality, Provider/model behavior, continuity, repeated failures, recovery, or prior architecture decisions. Use when project evidence would improve the task; do not use for trivial edits or as a substitute for current code search.
---

# Retrieve AI-VIDEO Memory

Use the project-local Agent Memory RAG as advisory context. This skill is the
prompt-aware routing layer; it does not create a lifecycle hook or a Product
Runtime dependency.

## Decide Whether To Retrieve

Retrieve before substantial execution when the task involves one or more of:

- real media production, rough-cut quality, final output quality, or visual QA;
- a known regression, repeated failure, incident, or recovery decision;
- Provider/model behavior or generation strategy;
- continuity, identity drift, reference usage, or image/video prompting;
- an architecture decision with prior rejected approaches;
- an explicit request to find earlier AI-VIDEO experience, decisions, specs, or plans.

Skip retrieval for formatting, typos, unrelated trivial tests, or isolated
mechanical refactors. For exact current source symbols, call paths, or file
contents, use `rg`, code search, and current code instead of treating RAG as
the source of truth.

## Select The Scope

- Use `experience` by default. It searches `docs/record_for_agent/` and merges
  eligible `runs/<run_id>/SUMMARY.md` records. Those hits use
  `authority=auto_generated_run_summary_advisory` and
  `document_kind=run_summary`, with `run_id`, `run_family`, `run_version`, and
  `summary_sha256` provenance.
- Use `superpowers` only when historical specs/plans are specifically relevant.
- Use `all` when the task needs cross-category project evidence. It searches
  experience and Superpowers plus top-level current Markdown under `docs/`,
  `docs/research/`, and `docs/when_to_do/`. Preserve every hit's authority:
  current contracts/baselines, roadmap, research, deferred decisions,
  experience, and historical plans are not interchangeable.

After selecting the scope, read exactly one matching mode reference before
constructing the query:

- [`references/experience.md`](references/experience.md) for `experience`;
- [`references/superpowers.md`](references/superpowers.md) for `superpowers`;
- [`references/all.md`](references/all.md) for `all`.

Do not load all three references for one search.

## Run The Search

From the AI-VIDEO repository root, distill the task into a short query with the
domain, failure or decision, and important exact identifiers. Do not put
credentials, raw Provider responses, signed URLs, or private data in the query.

Run the exact command in the selected scope reference. `search` is
validation/query-only: it never builds, refreshes, or repairs an index. Exit
code `0` with `[]` is a valid answerability abstention. Exit code `2` with an
error on stderr is a retrieval failure, not an empty result.

If and only if that error explicitly says an index is missing, stale, partial,
or identity-mismatched,
run `python -m scripts.agent_memory --scope all build` once with the pinned
local backend, then retry the original selected-scope search once. Treat build
as a separate potentially long-running phase; do not include it in the search
timeout. The `all` build materializes all five collections in the shared main
index plus eligible run summaries; it does not broaden the retry query or the
authority of its results. Otherwise report the
fail-closed error and continue from current repository evidence. Never download
a model, use the fake embedding backend, enable a network fallback, or broaden
the search scope to force a result.

## Use The Results

- Treat returned items as fragments with `source`, heading metadata,
  `chunk_id`, scores, and `admission_lane`; use `source` to reopen the exact
  document when a claim matters.
- An empty result is a valid abstention. Do not lower the `0.7` admission gate,
  invent a match, or silently broaden to unrelated corpora.
- Separate current contract/baseline/roadmap, `advisory_research`,
  `deferred_decision_advisory`, `advisory_experience`,
  `historical_design_plan`, and auto-generated run-summary authority in the
  working conclusion.
- Resolve conflicts in this order: user request, current code/tests and live
  runtime evidence, current repository contracts, then retrieved history.
- RAG cannot authorize Provider calls, production mutation, activation,
  recovery, quality acceptance, push, or release.

For production quality, Provider behavior, or known-failure work, run a focused
follow-up search before completion when implementation findings materially
change the original query. Do not repeat an equivalent search merely as
ceremony.

Current retrieval behavior and maintenance boundaries are recorded in
`docs/record_for_agent/2026-08-21-agent-memory-rag-scope-and-retrieval.md`.
