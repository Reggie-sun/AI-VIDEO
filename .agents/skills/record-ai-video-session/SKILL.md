---
name: record-ai-video-session
description: Create or update durable AI-VIDEO session records under docs/record_for_agent from verified repository and runtime evidence, including reconciling prior records whose pending status or verdict is superseded by newer evidence. Use proactively when substantial AI-VIDEO implementation, documentation, live proof, media diagnosis, architecture decisions, or recovery work reaches a stable checkpoint or completion; also use before a session handoff or compaction, and whenever the user asks to record, capture, preserve, summarize, or hand off the current session. Do not trigger for trivial conversation, unfinished work without a stable checkpoint, or status questions that do not request a durable record.
---

# Record AI-VIDEO Session

## Confirm A Stable Record Boundary

Record history only after meaningful work reaches a stable checkpoint, completion, or genuine blocker. Do not interrupt unfinished implementation merely to create documentation. If the session is still progressing, finish the authorized task or wait for a stable boundary first.

This skill writes a project record; it does not authorize new implementation, local generation, live Provider calls, paid actions, releases, or changes to `sub-agents`.

## Handle Project Hook Requests

The project-local Codex hook may inject a request containing a
`capture_request_id`. Treat it as a one-time request to evaluate this skill's
stable-boundary rule, not as proof that a record is required.

- If substantial work reached a stable checkpoint, completion, or genuine
  blocker, run this skill normally and create or update the primary relevant
  record plus any directly required supersession notices, then acknowledge the
  request with outcome `recorded`. Do not create duplicate narrative records.
- If the boundary is not stable or the repository change is trivial or
  unrelated, do not create a record; acknowledge the request with outcome
  `no_record` and finish the current response normally.
- Acknowledge exactly once after the evaluation using the request's exact ID:

  ```bash
  python3 .agents/skills/record-ai-video-session/scripts/session_record_hook.py \
    acknowledge \
    --capture-request-id <capture_request_id> \
    --outcome recorded
  ```

  Use `--outcome no_record` when no durable record was created. Require the
  command to return `{"acknowledged": true}`; if it returns false, report the
  stale or unknown request instead of guessing another ID.
- Check the current topic, commits, and existing records before writing so a
  repeated hook request cannot create duplicate records.
- Hook state follows `ACKED -> PENDING -> ACKED`. `PostToolUse` only attributes
  paths from this session's `apply_patch` calls or a simple exact
  `git add <specific-files>` adoption command; unrelated HEAD, index, dirty, or
  untracked changes do not reopen an acknowledged checkpoint. Files under
  `docs/record_for_agent/` are excluded so the record cannot trigger itself.
- The hook does not authorize Provider calls, tests, network access, Git writes,
  or any scope beyond the current user request and repository rules.

## Gather Verified Truth

1. Resolve the AI-VIDEO repository root and read `../../../AGENTS.md`.
2. Read `../../../docs/record_for_agent/2026-08-19-seedance-native-audio-and-p4-mixing.md` for the expected structure and level of precision.
3. Inspect the current branch, `git status --short --branch`, recent task commits, staged state, and live writer ownership before writing.
4. Read only the task-relevant canonical spec, plan, runtime baseline, roadmap, code, tests, receipts, reports, and media metadata.
5. Verify important claims from current files or executable evidence. Treat conversation summaries, dated records, handoffs, and Agent prose as secondary context.
6. When MiniMax/sub-agent behavior matters, reference a sanitized `capture-minimax-session` report if one exists. Never copy raw rollout JSONL, prompts, commands, environment values, credentials, or full Provider output into the record.
7. Search the task-relevant existing records by exact artifact, run, verdict, or topic identity. Identify any prior `pending`, provisional, blocked, next-work, quality, or runtime claim that the new verified evidence materially changes.

## Choose The Record File

Write under `../../../docs/record_for_agent/` using:

`YYYY-MM-DD-<concise-topic-slug>.md`

Use a short topic slug that describes the durable lesson or completed slice, not the Agent name or generic words such as `session-notes`.

- Create a new file for a distinct topic or independently reusable runtime lesson.
- Update an existing record only when the current work directly extends that same topic and the existing file is not owned by another writer.
- Never overwrite, rename, or delete an unrelated record.
- Do not create `references/` copies of canonical project documents. Link to the existing source of truth instead.

## Reconcile Superseded Evidence

When newer verified evidence changes a prior record's current-facing status,
verdict, blocker, or next action, preserve history without leaving the old file
misleading when read by itself.

- Use exact artifact/run/topic identity to find directly affected records; do
  not perform an unbounded rewrite of historical records.
- Keep one primary record for the current checkpoint. In each directly affected
  older record, add a concise, prominent supersession notice that names the
  newer evidence or record, the replacement status/verdict, and the date.
- Retain the original chronology and measurements as historical evidence. Mark
  outdated conclusions and next actions as historical or superseded instead of
  silently rewriting them as though they were never true.
- A new record that mentions the correction is not sufficient when an older
  file still independently presents `pending`, provisional PASS, or another
  displaced claim as current truth.
- Do not convert a technical metric into a human verdict, or vice versa. State
  exactly which proof layer changed and which historical measurements remain
  valid.
- If an affected old record has a target-file ownership conflict, remain
  read-only on that file, report the blocker, and do not claim supersession is
  fully reconciled.
- This skill updates durable records only. It does not rebuild or refresh a RAG
  index unless the user separately authorizes the owning retrieval/index
  workflow; report that distinction when freshness matters.

## Write The Record

Follow the example's style: English section titles, Chinese narrative, original technical identifiers, and evidence-backed boundaries. Include only sections that add durable value, normally drawn from:

```markdown
# <Topic> Record

Date: YYYY-MM-DD

## Purpose

## Current Runtime Truth

## Session Work And Decisions

## Verification And Evidence

## Assessment

## Remaining Risks Or Next Work

## Agent Guardrails
```

Adapt headings to the topic rather than mechanically filling every section.

Record the distinctions future Agents are likely to confuse, including when relevant:

- docs-only contract versus implemented runtime;
- offline tests versus local live proof versus paid/cloud live proof;
- raw Provider artifact versus review derivative versus final composition output;
- technical acceptance versus human or subjective quality acceptance;
- committed, staged, untracked, local-only, pushed, and released states;
- Provider output capability versus P4 composition/audio ownership;
- exact replay/recovery evidence versus a successful one-off call.

Use exact repository-relative paths, commit IDs, receipt paths, artifact hashes, measured codec/audio/frame facts, and call counts when verified and useful. Avoid speculative chronology and omit noisy command-by-command transcripts.

## Preserve Safety And Ownership

- Do not include secrets, credential values, raw prompts, full external responses, private environment dumps, or unsanitized logs.
- Do not stage, commit, reformat, or repair unrelated working-tree changes.
- Do not claim another window's changes as work completed by this session.
- Do not convert a proposed plan or unverified observation into runtime truth.
- Do not trigger new tests, media generation, Provider calls, uploads, or network research merely to make the record look complete. Report missing evidence as a remaining risk.
- If target-file ownership conflicts with another writer, remain read-only and report the blocker instead of creating a competing record.

## Verify And Checkpoint

1. Review every changed line and confirm it traces to the session being recorded.
2. Run `git diff --check` for every exact task-owned record and Skill file.
3. Confirm the task diff contains only the intended primary record, directly
   required supersession notices, and any explicitly requested Skill update.
4. Follow current repository policy for documentation-only verification. Do not run the full repository suite solely for an agent record.
5. Stage every task-owned path explicitly. If unrelated files are already staged, use a path-limited commit only when it preserves their index state; otherwise stop and report the conflict.
6. Never push or release unless the user separately requests it.

## Report Completion

Return the clickable primary record path, every older record given a supersession notice, commit ID if created, verification performed, and any unrecorded or unresolved risk. Explicitly state whether unrelated staged/dirty files remained untouched, whether any live or paid call occurred during recording, and whether a separate RAG index remains stale or was refreshed by an independently authorized workflow.
