---
name: record-ai-video-session
description: Create or update durable AI-VIDEO session records under docs/record_for_agent from verified repository and runtime evidence. Use proactively when substantial AI-VIDEO implementation, documentation, live proof, media diagnosis, architecture decisions, or recovery work reaches a stable checkpoint or completion; also use before a session handoff or compaction, and whenever the user asks to record, capture, preserve, summarize, or hand off the current session. Do not trigger for trivial conversation, unfinished work without a stable checkpoint, or status questions that do not request a durable record.
---

# Record AI-VIDEO Session

## Confirm A Stable Record Boundary

Record history only after meaningful work reaches a stable checkpoint, completion, or genuine blocker. Do not interrupt unfinished implementation merely to create documentation. If the session is still progressing, finish the authorized task or wait for a stable boundary first.

This skill writes a project record; it does not authorize new implementation, local generation, live Provider calls, paid actions, releases, or changes to `sub-agents`.

## Gather Verified Truth

1. Resolve the AI-VIDEO repository root and read `../../../AGENTS.md`.
2. Read `../../../docs/record_for_agent/2026-08-19-seedance-native-audio-and-p4-mixing.md` for the expected structure and level of precision.
3. Inspect the current branch, `git status --short --branch`, recent task commits, staged state, and live writer ownership before writing.
4. Read only the task-relevant canonical spec, plan, runtime baseline, roadmap, code, tests, receipts, reports, and media metadata.
5. Verify important claims from current files or executable evidence. Treat conversation summaries, dated records, handoffs, and Agent prose as secondary context.
6. When MiniMax/sub-agent behavior matters, reference a sanitized `capture-minimax-session` report if one exists. Never copy raw rollout JSONL, prompts, commands, environment values, credentials, or full Provider output into the record.

## Choose The Record File

Write under `../../../docs/record_for_agent/` using:

`YYYY-MM-DD-<concise-topic-slug>.md`

Use a short topic slug that describes the durable lesson or completed slice, not the Agent name or generic words such as `session-notes`.

- Create a new file for a distinct topic or independently reusable runtime lesson.
- Update an existing record only when the current work directly extends that same topic and the existing file is not owned by another writer.
- Never overwrite, rename, or delete an unrelated record.
- Do not create `references/` copies of canonical project documents. Link to the existing source of truth instead.

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
2. Run `git diff --check` for the exact record file.
3. Confirm the task diff contains only the intended record artifact.
4. Follow current repository policy for documentation-only verification. Do not run the full repository suite solely for an agent record.
5. Stage with the exact record path. If unrelated files are already staged, use a path-limited commit only when it preserves their index state; otherwise stop and report the conflict.
6. Never push or release unless the user separately requests it.

## Report Completion

Return the clickable record path, commit ID if created, verification performed, and any unrecorded or unresolved risk. Explicitly state whether unrelated staged/dirty files remained untouched and whether any live or paid call occurred during recording.
