import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { catalogExternalMedia, publicExternalMediaProjection } from "../scripts/external-media.mjs";

async function fixture() {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-external-media-"));
  const artifacts = path.join(root, "artifacts");
  const raw = path.join(root, "raw");
  const external = path.join(root, "external");
  await Promise.all([mkdir(artifacts), mkdir(raw), mkdir(external)]);
  return { root, artifacts, raw, external };
}

function sources(paths) {
  return [
    { id: "artifact", label: "开发产物", kind: "development_artifact", root: paths.artifacts },
    { id: "raw", label: "原始输出", kind: "raw_provider_output", root: paths.raw },
    { id: "qingyan", label: "青颜", kind: "external_project_asset", root: paths.external },
  ];
}

test("catalog is allowlisted, marks missing roots unavailable, and ignores symlinks", async () => {
  const paths = await fixture();
  await writeFile(path.join(paths.artifacts, "accepted.mp4"), "artifact bytes");
  await writeFile(path.join(paths.raw, "outside.mp4"), "outside bytes");
  await symlink(path.join(paths.raw, "outside.mp4"), path.join(paths.artifacts, "linked.mp4"));
  const result = await catalogExternalMedia({
    sources: [...sources(paths), { id: "missing", label: "缺失", kind: "raw_provider_output", root: path.join(paths.root, "missing") }],
  });

  assert.equal(result.status, "partial");
  assert.equal(result.sources.at(-1).status, "unavailable");
  assert.equal(result.groups.length, 2);
  const accepted = result.groups.find((group) => group.preview.file_name === "accepted.mp4");
  assert.ok(accepted);
  assert.equal(result.groups.some((group) => group.preview.file_name === "linked.mp4"), false);
  assert.equal(accepted.evidence_classification, "non_canonical");
  assert.equal(accepted.generation_status, "NOT_EVALUATED");
  assert.equal(accepted.lifecycle_status, "NOT_EVALUATED");
});

test("deduplicates exact bytes across sources with a stable source-qualified token and priority preview", async () => {
  const paths = await fixture();
  await writeFile(path.join(paths.artifacts, "from-artifact.mp4"), "same exact bytes");
  await writeFile(path.join(paths.raw, "from-raw.mp4"), "same exact bytes");
  await writeFile(path.join(paths.external, "different.mov"), "different bytes");
  const configuredSources = sources(paths);
  configuredSources[2].label = paths.external;
  const result = await catalogExternalMedia({ sources: configuredSources });

  assert.equal(result.groups.length, 2);
  const duplicate = result.groups.find((group) => group.locations.length === 2);
  assert.equal(duplicate.preview.source_id, "artifact");
  assert.equal(duplicate.preview.file_name, "from-artifact.mp4");
  assert.match(duplicate.token, /^external_artifact_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{16}$/);
  assert.deepEqual(duplicate.locations.map((location) => location.source_id), ["artifact", "raw"]);
  assert.ok(duplicate.locations.every((location) => /^[A-Za-z0-9_-]{6,128}$/.test(location.token)));
  assert.ok(duplicate.locations.every((location) => location.source_label && location.source_kind && location.file_name));
  assert.equal(result.summary.location_count, 3);
  assert.equal(result.summary.unique_media_count, 2);
  assert.equal(result._media[duplicate.token].source_id, "artifact");
  assert.equal(result.sources.find((source) => source.id === "qingyan").label, "外部媒体来源");
  const externalOnly = result.groups.find((group) => group.preview.source_id === "qingyan");
  assert.equal(externalOnly.locations[0].source_label, "外部媒体来源");
  assert.equal(JSON.stringify(publicExternalMediaProjection(result)).includes(paths.external), false);
});

test("public projection never leaks absolute media paths while private descriptors retain service identity", async () => {
  const paths = await fixture();
  const media = path.join(paths.external, "nested", "clip.webm");
  await mkdir(path.dirname(media));
  await writeFile(media, "video bytes");
  const result = await catalogExternalMedia({ sources: sources(paths) });
  const projected = publicExternalMediaProjection(result);

  assert.equal(JSON.stringify(projected).includes(paths.root), false);
  assert.equal(JSON.stringify(projected).includes("source_path"), false);
  assert.equal(JSON.stringify(projected).includes("source_root"), false);
  assert.equal(result._media[result.groups[0].token].source_path, media);
  assert.match(result.groups[0].token, /^[A-Za-z0-9_-]{6,128}$/);
});

test("sidecar symlinks are ignored instead of projecting metadata from outside the allowlisted root", async () => {
  const paths = await fixture();
  const media = path.join(paths.external, "clip.mp4");
  const bytes = "video bytes";
  const outside = path.join(paths.root, "outside.json");
  await writeFile(media, bytes);
  await writeFile(outside, JSON.stringify({
    sha256: createHash("sha256").update(bytes).digest("hex"),
    prompt_text: "must not enter the projection",
    status: "succeeded",
  }));
  await symlink(outside, path.join(paths.external, "linked.json"));

  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups[0];
  assert.equal(group.metadata_status, "not_evaluated");
  assert.equal(group.prompt_text, null);
  assert.equal(group.reported_status, null);
});

test("deduplicates repeated exact-byte evidence references within a SHA group", async () => {
  const paths = await fixture();
  const first = path.join(paths.artifacts, "v1", "clip.mp4");
  const second = path.join(paths.artifacts, "v2", "clip.mp4");
  const bytes = "reused artifact bytes";
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  await Promise.all([mkdir(path.dirname(first)), mkdir(path.dirname(second))]);
  await Promise.all([writeFile(first, bytes), writeFile(second, bytes)]);
  await writeFile(path.join(paths.artifacts, "receipt.json"), JSON.stringify({ sha256, status: "completed" }));

  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups.find((item) => item.sha256 === sha256);
  assert.equal(group.locations.length, 2);
  assert.deepEqual(group.evidence_refs, [{ source_id: "artifact", relative_path: "receipt.json" }]);
});

test("metadata is accepted only when a sidecar directly binds the exact path or sha256", async () => {
  const paths = await fixture();
  const media = path.join(paths.external, "shot-7.mp4");
  await writeFile(media, "bound media");
  await writeFile(path.join(paths.external, "bound.json"), JSON.stringify({
    schema: "ai-video-external-media-metadata/1",
    output_path: "shot-7.mp4",
    prompt_text: "a verified prompt",
    shot_id: "shot-7",
    generation_type: "T2V",
    state: "completed",
  }));
  await writeFile(path.join(paths.external, "unbound.json"), JSON.stringify({
    prompt: "must not appear",
    shot: "shot-other",
    status: "success",
  }));
  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups[0];

  assert.equal(group.metadata_status, "bound");
  assert.deepEqual(group.metadata, {
    prompt: "a verified prompt", shot: "shot-7", generation_type: "T2V", status: "completed",
  });
  assert.equal(group.generation_status, "NOT_EVALUATED");
  assert.equal(group.lifecycle_status, "NOT_EVALUATED");
  assert.equal(group.status, "NOT_EVALUATED");
  assert.equal(group.reported_status, "completed");
  assert.equal(group.prompt_text, "a verified prompt");
  assert.equal(group.shot_id, "shot-7");
  assert.equal(group.generation_type, "T2V");
  assert.deepEqual(group.evidence_refs, [{ source_id: "qingyan", relative_path: "bound.json" }]);
});

test("external project evidence chain joins exact result bytes to sealed prompt, mode, and provider outcome", async () => {
  const paths = await fixture();
  const evidence = path.join(paths.external, "evidence", "shot01");
  const media = path.join(paths.external, "raw", "shot01.mp4");
  const bytes = Buffer.from("chain-bound-media");
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  await Promise.all([mkdir(evidence, { recursive: true }), mkdir(path.dirname(media), { recursive: true })]);
  await writeFile(media, bytes);
  await writeFile(path.join(evidence, "result.json"), JSON.stringify({ path: "../../raw/shot01.mp4", sha256, shot: "shot01", seed: 42 }));
  await writeFile(path.join(evidence, "resolved_request.json"), JSON.stringify({
    generation_id: "generation-1",
    resolved_generation_hash: "resolved-1",
    effective_seed: 42,
    mode: "text_to_video",
    prompt_text: "sealed exact prompt",
    activation_scope: { request: { target_shot_id: "shot01", mode: "text_to_video", prompt_text: "sealed exact prompt" } },
  }));
  await writeFile(path.join(evidence, "fetch_receipt.json"), JSON.stringify({ artifact_sha256: sha256, observation_fingerprint: "observation-1" }));
  await writeFile(path.join(evidence, "observation.json"), JSON.stringify({ observation_fingerprint: "observation-1", submit_result_fingerprint: "submit-1", state: "succeeded" }));
  await writeFile(path.join(evidence, "submit_result.json"), JSON.stringify({ result_fingerprint: "submit-1", resolved_generation_hash: "resolved-1", generation_id: "generation-1" }));

  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups.find((item) => item.sha256 === sha256);
  assert.equal(group.metadata_status, "verified_evidence_chain");
  assert.equal(group.prompt_text, "sealed exact prompt");
  assert.equal(group.shot_id, "shot01");
  assert.equal(group.generation_type, "text_to_video");
  assert.equal(group.reported_status, "succeeded");
  assert.equal(group.status, "NOT_EVALUATED");
  assert.deepEqual(group.evidence_refs.map((item) => item.relative_path), [
    "evidence/shot01/fetch_receipt.json",
    "evidence/shot01/observation.json",
    "evidence/shot01/resolved_request.json",
    "evidence/shot01/result.json",
    "evidence/shot01/submit_result.json",
  ]);

  await writeFile(path.join(evidence, "fetch_receipt.json"), JSON.stringify({ artifact_sha256: sha256 }));
  await writeFile(path.join(evidence, "observation.json"), JSON.stringify({ submit_result_fingerprint: "submit-1", state: "succeeded" }));
  const missingFingerprint = await catalogExternalMedia({ sources: sources(paths) });
  const rejectedGroup = missingFingerprint.groups.find((item) => item.sha256 === sha256);
  assert.equal(rejectedGroup.metadata_status, "not_evaluated");
  assert.equal(rejectedGroup.prompt_text, null);
  assert.equal(rejectedGroup.reported_status, null);
});

test("a direct sha256 sidecar binding is accepted without inferring anything from the filename", async () => {
  const paths = await fixture();
  const media = path.join(paths.raw, "opaque-name.m4v");
  const bytes = "sha-bound media";
  await writeFile(media, bytes);
  await writeFile(path.join(paths.raw, "receipt.json"), JSON.stringify({
    schema: "ai-video-external-media-metadata/1",
    sha256: createHash("sha256").update(bytes).digest("hex"),
    positive_prompt: "a sha-bound prompt",
    type: "closeup",
  }));
  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups[0];

  assert.equal(group.metadata_status, "bound");
  assert.equal(group.prompt_text, "a sha-bound prompt");
  assert.equal(group.shot_type, "closeup");
  assert.deepEqual(group.evidence_refs, [{ source_id: "raw", relative_path: "receipt.json" }]);
});

test("unknown sidecar schemas retain exact evidence refs without interpreting generic fields", async () => {
  const paths = await fixture();
  const media = path.join(paths.raw, "unknown-schema.mp4");
  const bytes = "unknown-schema media";
  await writeFile(media, bytes);
  await writeFile(path.join(paths.raw, "unknown.json"), JSON.stringify({
    schema: "quality-gate/99",
    sha256: createHash("sha256").update(bytes).digest("hex"),
    prompt: "must remain uninterpreted",
    type: "review",
    status: "failed",
  }));

  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups[0];
  assert.equal(group.metadata_status, "not_evaluated");
  assert.equal(group.prompt_text, null);
  assert.equal(group.shot_type, null);
  assert.equal(group.reported_status, null);
  assert.deepEqual(group.evidence_refs, [{ source_id: "raw", relative_path: "unknown.json" }]);
});

test("unbound sidecars fail closed and scan limits are deterministic", async () => {
  const paths = await fixture();
  await writeFile(path.join(paths.raw, "one.mp4"), "one");
  await writeFile(path.join(paths.raw, "two.mp4"), "two");
  await writeFile(path.join(paths.raw, "metadata.json"), JSON.stringify({ prompt: "not associated" }));
  const result = await catalogExternalMedia({
    sources: sources(paths),
    limits: { maxMediaPerRoot: 1, maxDepth: 10, maxEntriesPerRoot: 100, maxSidecarsPerRoot: 10, maxSidecarBytes: 1024 },
  });
  const rawGroup = result.groups.find((group) => group.preview.source_id === "raw");

  assert.equal(rawGroup.metadata_status, "not_evaluated");
  assert.deepEqual(rawGroup.metadata, {});
  assert.equal(result.sources.find((source) => source.id === "raw").media_count, 1);
});
