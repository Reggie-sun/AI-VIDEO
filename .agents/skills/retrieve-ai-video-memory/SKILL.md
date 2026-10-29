---
name: retrieve-ai-video-memory
description: Retrieve authority-separated AI-VIDEO project docs, experience, research, deferred decisions, or historical specs before substantial work involving production quality, Provider/model behavior, continuity, repeated failures, recovery, or prior architecture decisions. Use when project evidence would improve the task; do not use for trivial edits or as a substitute for current code search.
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

- Use `experience` by default. It searches `docs/record_for_agent/`, including
  Learning Claims.
- Use `superpowers` only when historical specs are specifically relevant.
  Executed implementation plans are not indexed; read
  `docs/superpowers/plans/` directly when a specific plan matters.
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

Run the exact command in the selected scope reference. The retrieval core is
read-only. The index keeps itself current: when shards trail the corpus, the
CLI first refreshes them incrementally in the foreground, re-embedding only new
or edited chunks (at most 64 across all searched shards; usually 5–15 seconds),
and never waits for another builder. Larger refreshes are queued for a detached
worker instead.

- Exit code `0` with fresh hits or `[]` is a normal result; `[]` is a valid
  answerability abstention. A stderr line saying a shard was refreshed
  incrementally before search is normal.
- Exit code `0` with `index_freshness=stale` means the refresh exceeded the
  foreground bound or another builder held the shard. The CLI returns only
  physically valid, tagged last-good fragments and queues the exact stale
  shards. Use those fragments as stale advisory context and continue; do not
  wait, poll, or retry in the same task merely to obtain fresh results.
- Exit code `3` means the local sharded layout is missing, needs one-time
  migration, or contains shards materialized by a different library stack.
  The CLI has queued the exact required shards; continue from current
  repository evidence without retrying in this task.
- Exit code `2` is a strict failure such as schema, embedding, authority,
  manifest, or physical collection corruption. Report it and continue from
  current repository evidence; do not enqueue, rebuild, or weaken validation.

Never run `build` or another recovery build from this skill; the CLI's bounded
refresh is the only foreground maintenance. Never download a model, use the
fake embedding backend, enable a network fallback, or broaden the search scope
to force a result. Refreshes write only local derived Agent Memory state and are
not a lifecycle hook or Product Runtime dependency.

## Keep The Corpus Current

Outdated documents leave retrieval without being deleted:

- Executed `docs/superpowers/plans/` and work-specific
  `docs/superpowers/artifacts/` are excluded by path.
- Any indexed Markdown whose frontmatter contains `retrieval: retired` is
  excluded; add `superseded_by: <path>` so a reader of the file can find its
  replacement. Use it only when no current-facing claim in the document remains
  valid; a partially superseded record keeps its supersession notice and stays
  retrievable.
- `record-ai-video-session` applies this marker when it fully supersedes an
  older record. Removing the marker restores the document on the next search.

## Use The Results

- Treat returned items as fragments with `source`, heading metadata,
  `chunk_id`, scores, and `admission_lane`; each document contributes at most
  its best-scoring fragment. Use `source` to reopen the exact document when a
  claim matters.
- An empty result is a valid abstention. Do not lower the `0.7` admission gate,
  invent a match, or silently broaden to unrelated corpora.
- Separate current contract/baseline/roadmap, `advisory_research`,
  `deferred_decision_advisory`, `advisory_experience`,
  `advisory_learning`, and `historical_design_plan` authority in the working
  conclusion. A Learning Claim is a current scoped
  advisory synthesis, not raw history; reopen it and verify its
  active/pending lanes, `pending_approval_status`, active/pending adoption
  status, confirmed candidate commit/hash, evidence sources, and current bytes
  before use.
- Resolve conflicts in this order: user request, current code/tests and live
  runtime evidence, current repository contracts, then retrieved history.
- RAG cannot authorize Provider calls, production mutation, activation,
  recovery, quality acceptance, push, or release.
- A returned `advisory_learning` hit cannot authorize its own adoption. Only an
  exact user-confirmed candidate followed by the target owner's verification
  can reach `ADOPTED`.

For production quality, Provider behavior, or known-failure work, run a focused
follow-up search before completion when implementation findings materially
change the original query. Do not repeat an equivalent search merely as
ceremony.

Current retrieval behavior and maintenance boundaries are recorded in
`docs/record_for_agent/2026-08-21-agent-memory-rag-scope-and-retrieval.md` and
`docs/record_for_agent/2026-10-29-agent-memory-corpus-pruning-and-incremental-refresh.md`.
