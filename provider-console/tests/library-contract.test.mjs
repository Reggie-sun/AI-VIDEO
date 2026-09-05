import assert from "node:assert/strict";
import test from "node:test";

import {
  buildLibraryEntries,
  filterLibraryEntries,
  libraryLifecycle,
  selectLibraryEntry,
  versionGroups,
} from "../src/library-contract.js";

const sha = (letter) => letter.repeat(64);

test("external videos can be found by their source-relative run directory", () => {
  const output = media("e", "externalvideo");
  const entries = buildLibraryEntries([], { groups: [{ ...output, locations: [{ source_id: "runs-outputs", token: "externalvideo", file_name: "subtitled.mp4", relative_path: "drama-preview-v81/subtitled.mp4" }] }] });
  assert.equal(filterLibraryEntries(entries, { query: "drama-preview-v81" }).length, 1);
  assert.equal(filterLibraryEntries(entries, { query: "drama-preview-v77" }).length, 0);
});

test("strict render output is searchable and ordered without inventing a Shot or Provider attempt", () => {
  const rendered = { ...media("d", "rendertoken"), source_kind: "active_render", relative_path: `state/render/outputs/${sha("d")}.mp4`, started_at: "2026-09-05T11:00:00Z" };
  const entries = buildLibraryEntries([
    { workspace: "lighthouse/final-production/project.yaml", project: { project_id: "final", title: "The Lighthouse Awakens" }, attempts: [], active_render_media: rendered },
    detail("source", attempt({ fetched_media: media("a", "sourcetoken") })),
  ], null);
  assert.equal(entries.length, 2);
  const [entry] = filterLibraryEntries(entries, { query: `${sha("d")}.mp4` });
  assert.equal(entries[0], entry);
  assert.match(entry.title, /The Lighthouse Awakens.*合成成片/);
  assert.equal(entry.url, "/api/runs/media/rendertoken");
  assert.equal(entry.contexts[0].role, "active_render");
  assert.equal(entry.contexts[0].attempt, null);
  assert.equal(entry.contexts[0].versionKey, null);
  assert.equal(entry.model, null);
  const unavailable = buildLibraryEntries([{ active_render_media: { ...rendered, token: undefined } }], null);
  assert.equal(unavailable[0].available, false);
});

test("registry roles supplement the same owner but never choose a different Project title", () => {
  const output = media("a", "registered");
  const first = detail("owner-a", attempt({ fetched_media: output }));
  first.workspace_media = [output];
  assert.equal(buildLibraryEntries([first], null)[0].ambiguous, false);
  const second = { workspace: "owner-b", project: { project_id: "other", title: "Other title" }, workspace_media: [output] };
  assert.equal(buildLibraryEntries([{ ...first, attempts: [] }, second], null)[0].ambiguous, true);
  assert.equal(buildLibraryEntries([{ ...first, attempts: [] }, second], null)[0].title, null);
});

test("recovered exact bindings remain individually selectable without inventing lifecycle or versions", () => {
  const output = media("a", "external");
  const group = { ...output, locations: [{ source_id: "artifacts", token: "external", file_name: "clip.mp4" }], run_bindings: [
    { sha256: output.sha256, bytes: output.bytes, workspace: "broken-a", attempt_id: "a", target_shot_id: "shot-a", prompt_text: "A" },
    { sha256: output.sha256, bytes: output.bytes, workspace: "broken-b", attempt_id: "b", target_shot_id: "shot-b", prompt_text: "B" },
  ] };
  const [entry] = buildLibraryEntries([], { groups: [group] });
  assert.equal(entry.ambiguous, true);
  const bindings = entry.contexts.filter((context) => context.runBinding);
  assert.equal(bindings.length, 2);
  assert.equal(bindings[0].runBinding.prompt_text, "A");
  assert.equal(bindings[1].runBinding.prompt_text, "B");
  assert.ok(bindings.every((context) => !context.attempt && !context.versionKey));
});

function media(letter, token, bytes = 100) {
  return { sha256: sha(letter), bytes, mime_type: "video/mp4", token };
}

function detail(workspace, attempt) {
  return {
    workspace,
    project: { project_id: `project-${workspace}`, title: `Project ${workspace}` },
    attempts: [attempt],
  };
}

function attempt(overrides = {}) {
  return {
    attempt_id: "attempt-1",
    status: "running",
    phase: "validate",
    started_at: "2026-09-05T10:00:00.000Z",
    target_shot_id: "shot-1",
    target_shot_revision: 2,
    target_shot_content_hash: sha("c"),
    shot_snapshot_status: "verified",
    shot_snapshot: { shot_id: "shot-1", revision: 2, content_hash: sha("c") },
    provider: { model: "Seedance 2.5" },
    ...overrides,
  };
}

test("deduplicates exact bytes while retaining every source and output role", () => {
  const entries = buildLibraryEntries([
    detail("run-a", attempt({
      candidate_media_items: [{ role: "candidate-1", media: media("a", "candidate-1") }],
      fetched_media: media("a", "fetched-1"),
      output_media: media("b", "output-1"),
    })),
  ], {
    groups: [{
      sha256: sha("a"), bytes: 100, mime_type: "video/mp4",
      locations: [{ source_id: "artifacts", token: "external-1", file_name: "same.mp4", modified_at: "2026-09-01T00:00:00Z" }],
    }],
  });

  assert.equal(entries.length, 2);
  const same = entries.find((entry) => entry.id === `${sha("a")}:100`);
  assert.equal(same.contexts.length, 3);
  assert.deepEqual(same.contexts.map((context) => context.role), ["candidate-1", "fetched_media", "external_output"]);
  assert.equal(same.available, true);
  assert.equal(same.url, "/api/runs/media/candidate-1");
  assert.equal(entries.find((entry) => entry.sha256 === sha("b")).contexts[0].role, "output_media");
});

test("does not choose conflicting semantic metadata and rejects invalid descriptors", () => {
  const entries = buildLibraryEntries([
    detail("one", attempt({ candidate_media: media("d", "one-token") })),
    detail("two", attempt({ target_shot_id: "shot-2", provider: { model: "Mini" }, candidate_media: media("d", "two-token") })),
    detail("bad", attempt({ candidate_media: { sha256: sha("e"), bytes: 0, mime_type: "video/mp4", token: "bad-token" } })),
  ], null);

  assert.equal(entries.length, 1);
  assert.equal(entries[0].ambiguous, true);
  assert.equal(entries[0].title, null);
  assert.equal(entries[0].model, null);
});

test("keeps Prompt-bearing semantic bindings separate even when title and model match", () => {
  const first = detail("one", attempt({
    prompt_text: "first sealed prompt",
    candidate_media: media("a", "first-token"),
  }));
  first.project.title = "Same Project";
  const second = detail("two", attempt({
    prompt_text: "second sealed prompt",
    candidate_media: media("a", "second-token"),
  }));
  second.project.title = "Same Project";
  const [entry] = buildLibraryEntries([first, second], null);

  assert.equal(entry.ambiguous, true);
  assert.equal(entry.title, null);
  assert.equal(entry.model, "Seedance 2.5");
  assert.deepEqual(entry.contexts.map((context) => context.prompt), ["first sealed prompt", "second sealed prompt"]);
});

test("includes strict workspace registry videos without inventing attempt metadata", () => {
  const registryDetail = detail("greenhouse-mini", attempt());
  registryDetail.attempts = [];
  registryDetail.project.title = "Greenhouse Mini";
  registryDetail.workspace_media = [{ ...media("b", "registry-token"), asset_id: "greenhouse-final" }];
  const [entry] = buildLibraryEntries([registryDetail], null);

  assert.equal(entry.title, "Greenhouse Mini · greenhouse-final");
  assert.equal(entry.model, null);
  assert.equal(entry.startedAt, null);
  assert.deepEqual(entry.versionKeys, []);
  assert.equal(entry.contexts[0].role, "workspace_media");
  assert.equal(entry.contexts[0].title, "Greenhouse Mini · greenhouse-final");
});

test("only exact verified project snapshots create version groups", () => {
  const valid = detail("run-a", attempt({ candidate_media: media("f", "valid-token") }));
  const mismatched = detail("run-a", attempt({
    attempt_id: "bad-snapshot",
    shot_snapshot: { shot_id: "shot-1", revision: 3, content_hash: sha("c") },
    candidate_media: media("e", "bad-token"),
  }));
  const zeroRevision = detail("run-a", attempt({
    attempt_id: "zero-revision",
    target_shot_revision: 0,
    shot_snapshot: { shot_id: "shot-1", revision: 0, content_hash: sha("c") },
    candidate_media: media("a", "zero-token"),
  }));
  const invalidHash = detail("run-a", attempt({
    attempt_id: "invalid-hash",
    target_shot_content_hash: "not-a-sha",
    shot_snapshot: { shot_id: "shot-1", revision: 2, content_hash: "not-a-sha" },
    candidate_media: media("b", "hash-token"),
  }));
  const entries = buildLibraryEntries([valid, mismatched, zeroRevision, invalidHash], null);
  const groups = versionGroups(entries);
  assert.equal(entries.length, 4);
  assert.equal(entries.find((entry) => entry.sha256 === sha("e")).contexts[0].versionKey, null);
  assert.equal(groups.size, 1);
  const group = [...groups.values()][0];
  assert.equal(group.entries.length, 1);
  assert.equal(group.contexts[0].context.attemptId, "attempt-1");
});

test("search and filters apply to contexts, preserve ordering, and retain unavailable pins", () => {
  const entries = buildLibraryEntries([
    detail("greenhouse-mini", attempt({ started_at: "2026-09-04T10:00:00Z", provider: { model: "Mini" }, candidate_media: media("b", "mini-token") })),
    detail("greenhouse-pro", attempt({ started_at: "2026-09-05T10:00:00Z", provider: { model: "Pro" }, candidate_media: media("d", "pro-token") })),
    detail("unavailable", attempt({ started_at: "2026-09-03T10:00:00Z", candidate_media: media("e", null) })),
  ], null);

  assert.deepEqual(entries.map((entry) => entry.sha256), [sha("d"), sha("b"), sha("e")]);
  assert.equal(entries[0].title, "Project greenhouse-pro · shot-1");
  assert.equal(entries[1].title, "Project greenhouse-mini · shot-1");
  assert.equal(filterLibraryEntries(entries, { query: "greenhouse-mini" }).length, 1);
  assert.equal(filterLibraryEntries(entries, { model: "Pro" }).length, 1);
  assert.equal(filterLibraryEntries(entries, { availability: "unavailable" }).length, 1);
  assert.equal(filterLibraryEntries(entries, { evidence: "linked" }).length, 3);
  assert.equal(selectLibraryEntry(entries, "deleted-media", false), "deleted-media");
  assert.equal(selectLibraryEntry(entries, "deleted-media", true), entries[0].id);
});

test("external file time is only a fallback and lifecycle keeps raw typed state", () => {
  const entries = buildLibraryEntries([], {
    groups: [{
      sha256: sha("f"), bytes: 77, mime_type: "video/mp4",
      locations: [{ source_id: "external", token: "external-token", file_name: "fallback.mp4", modified_at: "2026-09-02T00:00:00Z" }],
    }],
  });
  assert.equal(entries[0].timeKind, "file");
  assert.equal(entries[0].url, "/api/external-media/media/external-token");
  assert.equal(libraryLifecycle({ status: "running", phase: "validate" }), "等待验证（running / validate）");
  assert.equal(libraryLifecycle({ status: "failed", phase: "fetch" }), "failed / fetch");
});
