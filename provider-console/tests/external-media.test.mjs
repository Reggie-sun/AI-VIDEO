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

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function pngBytes(width, height, marker) {
  const bytes = Buffer.alloc(24 + Buffer.byteLength(marker));
  Buffer.from("89504e470d0a1a0a0000000d49484452", "hex").copy(bytes);
  bytes.writeUInt32BE(width, 16);
  bytes.writeUInt32BE(height, 20);
  bytes.write(marker, 24);
  return bytes;
}

function experimentsSource(root) {
  return [{
    id: "ai-video-experiments",
    label: "AI-VIDEO Experiments",
    kind: "development_artifact",
    root,
  }];
}

async function writeM6Experiment(root, name, {
  videoBytes = Buffer.from(`m6-video-${name}`),
  shotId = `m6-${name}`,
  technicalGate = "FAIL",
  humanVerdict = "NOT_EVALUATED",
  promptText = `sealed prompt ${name}`,
  firstBytes = pngBytes(640, 360, `${name}-first`),
  lastBytes = pngBytes(640, 360, `${name}-last`),
  assetIdPrefix = name,
  findingEvidence = "exact evidence",
  requirementHash = sha256(`requirement-${name}`),
  resolvedGenerationHash = sha256(`resolved-${name}`),
  humanPass,
} = {}) {
  const experiment = path.join(root, name);
  const outputs = path.join(experiment, "outputs");
  const sidecars = path.join(experiment, "sidecars");
  const requests = path.join(sidecars, "requests");
  const gates = path.join(sidecars, "gates");
  const inputs = path.join(experiment, "inputs");
  await Promise.all([
    mkdir(outputs, { recursive: true }),
    mkdir(requests, { recursive: true }),
    mkdir(gates, { recursive: true }),
    mkdir(inputs, { recursive: true }),
  ]);

  const videoPath = path.join(outputs, "shot-b.mp4");
  const firstPath = path.join(inputs, "first.png");
  const lastPath = path.join(inputs, "last.png");
  const videoSha256 = sha256(videoBytes);
  const firstSha256 = sha256(firstBytes);
  const lastSha256 = sha256(lastBytes);
  const promptSha256 = sha256(promptText);
  await Promise.all([
    writeFile(videoPath, videoBytes),
    writeFile(firstPath, firstBytes),
    writeFile(lastPath, lastBytes),
    writeFile(path.join(requests, "b-prompt.txt"), ` \n${promptText}\n`),
  ]);

  const imageBindings = [
    { role: "first_frame", asset_id: `${assetIdPrefix}-first`, asset_sha256: firstSha256, mime_type: "image/png", width: 640, height: 360, size_bytes: firstBytes.length },
    { role: "last_frame", asset_id: `${assetIdPrefix}-last`, asset_sha256: lastSha256, mime_type: "image/png", width: 640, height: 360, size_bytes: lastBytes.length },
  ];
  const result = {
    output_path: videoPath,
    output_sha256: videoSha256,
    output_size_bytes: videoBytes.length,
    duration_seconds: 124 / 24,
    fps: 24,
    frame_count: 124,
    shot_id: shotId,
    requirement_hash: requirementHash,
    resolved_generation_hash: resolvedGenerationHash,
    prompt_sha256: promptSha256,
  };
  const targetShot = {
    shot_id: shotId,
    revision: 3,
    intent: `intent ${name}`,
    dialogue: `dialogue ${name}`,
    narration: `narration ${name}`,
    continuity_constraints: ["same screen direction", "one product"],
    visual_strategy: "generated_video",
  };
  const requirement = {
    requirement_hash: requirementHash,
    target_shot: targetShot,
    asset_evidence: imageBindings.map((binding) => ({
      role: binding.role === "first_frame" ? "continuity_terminal" : binding.role,
      asset_id: binding.asset_id,
      asset_sha256: binding.asset_sha256,
      mime_type: binding.mime_type,
      width: binding.width,
      height: binding.height,
      size_bytes: binding.size_bytes,
    })),
    generation_mode: "image_to_video",
  };
  const resolved = {
    generation_id: `generation-${name}`,
    provider_name: "comfy-local-h3",
    provider_kind: "minimax_h3_fl2va",
    model_id: "minimax-h3-fl2va",
    requirement_hash: requirementHash,
    mode: "image_to_video",
    prompt_text: promptText,
    image_bindings: imageBindings,
    resolved_generation_hash: resolvedGenerationHash,
    activation_scope: { request: {
      target_shot_id: shotId,
      target_shot_revision: 3,
      requirement_hash: requirementHash,
      mode: "image_to_video",
      prompt_text: promptText,
      image_bindings: imageBindings,
    } },
  };
  const gate = {
    schema: "m6-per-shot-post-media-gate/1",
    shot_id: shotId,
    requirement_hash: requirementHash,
    video_path: videoPath,
    video_sha256: videoSha256,
    video_size_bytes: videoBytes.length,
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    ...(humanPass === undefined ? {} : { human_pass: humanPass }),
    findings: {
      causal_state: { requirement_id: `${shotId}#causal`, verdict: technicalGate, evidence: findingEvidence },
    },
  };
  await Promise.all([
    writeFile(path.join(sidecars, "shot-b-result.json"), JSON.stringify(result)),
    writeFile(path.join(requests, "b-requirement.json"), JSON.stringify(requirement)),
    writeFile(path.join(requests, "b-resolved.json"), JSON.stringify(resolved)),
    writeFile(path.join(gates, "shot-b-gate.json"), JSON.stringify(gate)),
  ]);
  return {
    experiment,
    videoPath,
    firstPath,
    lastPath,
    videoSha256,
    promptSha256,
    requirementHash,
    resolvedGenerationHash,
    result,
    requirement,
    resolved,
    gate,
  };
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

test("public projection recursively redacts unsafe sidecar text even if an adapter regresses", () => {
  const projected = publicExternalMediaProjection({
    groups: [{
      asset_id: "/home/operator/private/reference.png",
      evidence: "https://media.invalid/file?X-Amz-Signature=private",
      note: "Traceback (most recent call last):\n  File \"/tmp/worker.py\", line 1",
      chinesePath: "路径：/home/operator/private.json",
      arrowPath: "媒体→/tmp/secret.mp4",
      windowsPath: "路径：C:\\private\\secret.json",
      safe: "shot-01 exact evidence",
      ordinaryUrl: "https://example.com/path?q=1",
      aspectRatio: "画面比例 16/9",
      playbackSpeed: "速度 1/2x",
      relativePath: "folder/subfolder",
      nested: { source_path: "/home/operator/media.mp4" },
    }],
    _media: { token: { source_path: "/home/operator/media.mp4" } },
  });

  assert.deepEqual(projected, {
    groups: [{
      asset_id: null,
      evidence: null,
      note: null,
      chinesePath: null,
      arrowPath: null,
      windowsPath: null,
      safe: "shot-01 exact evidence",
      ordinaryUrl: "https://example.com/path?q=1",
      aspectRatio: "画面比例 16/9",
      playbackSpeed: "速度 1/2x",
      relativePath: "folder/subfolder",
      nested: {},
    }],
  });
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

test("development artifact receipt and state bind exact Shot prompt, type, and reported status", async () => {
  const paths = await fixture();
  const runtime = path.join(paths.artifacts, "runtime");
  const prompts = path.join(paths.artifacts, "prompts");
  const media = path.join(runtime, "shot-problem.mp4");
  const prompt = path.join(prompts, "shot-problem.txt");
  const receipt = path.join(runtime, "shot-problem.receipt.json");
  const state = path.join(runtime, "shot-problem.state.json");
  const bytes = Buffer.from("artifact receipt media");
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  const promptText = "exact artifact prompt";
  const promptSha256 = createHash("sha256").update(promptText).digest("hex");
  await Promise.all([mkdir(runtime), mkdir(prompts)]);
  await writeFile(media, bytes);
  await writeFile(prompt, ` \n${promptText}\n\n`);
  await writeFile(receipt, JSON.stringify({
    output: { path: "artifacts/runtime/shot-problem.mp4", sha256, size_bytes: bytes.length },
    prompt_id: "prompt-1",
    prompt_path: "artifacts/prompts/shot-problem.txt",
    prompt_sha256: promptSha256,
    seed: 42,
    settings: { mode: "FL2VA" },
    shot_id: "shot-problem",
  }));
  await writeFile(state, JSON.stringify({
    output_sha256: sha256,
    prompt_id: "prompt-1",
    receipt: "artifacts/runtime/shot-problem.receipt.json",
    seed: 42,
    shot_id: "shot-problem",
    status: "completed",
  }));

  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups.find((item) => item.sha256 === sha256);
  assert.equal(group.metadata_status, "verified_artifact_receipt");
  assert.equal(group.shot_id, "shot-problem");
  assert.equal(group.prompt_text, promptText);
  assert.equal(group.generation_type, "FL2VA");
  assert.equal(group.reported_status, "completed");
  assert.deepEqual(group.evidence_refs.map((item) => item.relative_path), [
    "prompts/shot-problem.txt",
    "runtime/shot-problem.receipt.json",
    "runtime/shot-problem.state.json",
  ]);

  await writeFile(prompt, "prompt changed after generation");
  const promptMismatch = await catalogExternalMedia({ sources: sources(paths) });
  const promptMismatchGroup = promptMismatch.groups.find((item) => item.sha256 === sha256);
  assert.equal(promptMismatchGroup.metadata_status, "verified_artifact_receipt");
  assert.equal(promptMismatchGroup.shot_id, "shot-problem");
  assert.equal(promptMismatchGroup.prompt_text, null);
  assert.deepEqual(promptMismatchGroup.evidence_refs.map((item) => item.relative_path), [
    "runtime/shot-problem.receipt.json",
    "runtime/shot-problem.state.json",
  ]);

  await writeFile(state, JSON.stringify({
    output_sha256: "f".repeat(64),
    prompt_id: "prompt-1",
    receipt: "artifacts/runtime/shot-problem.receipt.json",
    seed: 42,
    shot_id: "shot-problem",
    status: "completed",
  }));
  const rejected = await catalogExternalMedia({ sources: sources(paths) });
  const rejectedGroup = rejected.groups.find((item) => item.sha256 === sha256);
  assert.equal(rejectedGroup.metadata_status, "not_evaluated");
  assert.equal(rejectedGroup.prompt_text, null);
  assert.equal(rejectedGroup.reported_status, null);
});

test("an exact final checksum exposes only the colocated declared ecommerce Shot plan", async () => {
  const paths = await fixture();
  const project = path.join(paths.artifacts, "ad-project");
  const final = path.join(project, "final");
  const media = path.join(final, "ad.mp4");
  const checksum = path.join(final, "ad.sha256");
  const bytes = Buffer.from("declared final bytes");
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  await mkdir(final, { recursive: true });
  await writeFile(media, bytes);
  await writeFile(checksum, `${sha256}  ad.mp4\n`);
  await writeFile(path.join(project, "ecommerce-package.json"), JSON.stringify({
    schema_version: "ecommerce-ad-workflow/package/2",
    storyboard: [{ shot_ids: ["shot-problem", "shot-close"] }],
    shot_intents: [
      { shot_id: "shot-problem", beat_id: "beat-shared", purpose: "建立问题", start_seconds: 0, end_seconds: 3, duration_basis: "HOOK_DENSITY", talent_action: "人物闻到异味", audio_event_ids: ["audio-problem"] },
      { shot_id: "shot-close", beat_id: "beat-shared", purpose: "产品收口", start_seconds: 3, end_seconds: 5, duration_basis: "CTA_DWELL", talent_action: null, audio_event_ids: ["audio-close"] },
    ],
    copy_graphics_plan: [
      { shot_id: "shot-problem", text: "汗湿黏腻？" },
      { shot_id: "shot-close", text: "抑汗｜净味" },
    ],
    audio_plan: { events: [
      { event_id: "audio-problem", kind: "DIALOGUE", beat_ids: ["beat-shared"], shot_ids: ["shot-problem"], verbatim_line: "试试青颜" },
      { event_id: "audio-close", kind: "VOICE_OVER", beat_ids: ["beat-shared"], shot_ids: ["shot-close"], verbatim_line: "抑汗净味" },
      { event_id: "audio-unrelated", kind: "DIALOGUE", beat_ids: ["beat-shared"], shot_ids: ["shot-other"], verbatim_line: "不得串入其他 Shot" },
    ] },
  }));

  const result = await catalogExternalMedia({ sources: sources(paths) });
  const group = result.groups.find((item) => item.sha256 === sha256);
  assert.equal(group.composition.composition_status, "declared");
  assert.equal(group.composition.association_status, "co_located_declared_package");
  assert.deepEqual(group.composition.ordered_shots, [
    {
      shot_id: "shot-problem",
      duration_basis: "HOOK_DENSITY",
      reported_status: "DECLARED_NOT_EVALUATED",
      purpose: "建立问题",
      talent_action: "人物闻到异味",
      start_seconds: 0,
      end_seconds: 3,
      copy: ["汗湿黏腻？"],
      dialogue: ["试试青颜"],
    },
    {
      shot_id: "shot-close",
      duration_basis: "CTA_DWELL",
      reported_status: "DECLARED_NOT_EVALUATED",
      purpose: "产品收口",
      talent_action: null,
      start_seconds: 3,
      end_seconds: 5,
      copy: ["抑汗｜净味"],
      dialogue: ["抑汗净味"],
    },
  ]);
  assert.deepEqual(group.evidence_refs.map((item) => item.relative_path), [
    "ad-project/ecommerce-package.json",
    "ad-project/final/ad.sha256",
  ]);

  await writeFile(checksum, `${"f".repeat(64)}  ad.mp4\n`);
  const rejected = await catalogExternalMedia({ sources: sources(paths) });
  assert.equal(rejected.groups.find((item) => item.sha256 === sha256).composition, null);
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

test("AI-VIDEO Experiments M6 evidence joins the exact Shot, prompt, layered verdicts, and reference images", async () => {
  const paths = await fixture();
  const evidence = await writeM6Experiment(paths.artifacts, "m6-v3", {
    technicalGate: "FAIL",
    humanVerdict: "NOT_EVALUATED",
  });

  const result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const group = result.groups.find((item) => item.sha256 === evidence.videoSha256);
  assert.equal(group.status, "NOT_EVALUATED");
  assert.equal(group.generation_status, "NOT_EVALUATED");
  assert.equal(group.lifecycle_status, "NOT_EVALUATED");
  assert.equal(group.reported_status, "OUTPUT_RECORDED");
  assert.equal(group.technical_gate, "FAIL");
  assert.equal(group.human_verdict, "NOT_EVALUATED");
  assert.equal(group.metadata_status, "verified_experiment_evidence");
  assert.equal(group.shot_evidence.length, 1);
  assert.deepEqual(group.shot_evidence[0], {
    entity_kind: "shot",
    association_status: "verified_experiment_evidence",
    shot_id: "m6-m6-v3",
    revision: 3,
    requirement_hash: evidence.requirementHash,
    intent: "intent m6-v3",
    dialogue: "dialogue m6-v3",
    narration: "narration m6-v3",
    continuity_constraints: ["same screen direction", "one product"],
    visual_strategy: "generated_video",
    start_seconds: 0,
    end_seconds: 124 / 24,
    duration_seconds: 124 / 24,
    timing_basis: "exact_output_clip",
    fps: 24,
    frame_count: 124,
    prompt_text: "sealed prompt m6-v3",
    generation_type: "image_to_video",
    provider_kind: "minimax_h3_fl2va",
    provider_name: "comfy-local-h3",
    model_id: "minimax-h3-fl2va",
    generation_result: "OUTPUT_RECORDED",
    technical_gate: "FAIL",
    human_verdict: "NOT_EVALUATED",
    findings: [{ requirement_id: "m6-m6-v3#causal", verdict: "FAIL", evidence: "exact evidence" }],
    reference_inputs: [
      {
        role: "first_frame",
        asset_id: "m6-v3-first",
        sha256: sha256(pngBytes(640, 360, "m6-v3-first")),
        mime_type: "image/png",
        bytes: pngBytes(640, 360, "m6-v3-first").length,
        width: 640,
        height: 360,
        token: group.shot_evidence[0].reference_inputs[0].token,
        source_id: "ai-video-experiments",
        relative_path: "m6-v3/inputs/first.png",
      },
      {
        role: "last_frame",
        asset_id: "m6-v3-last",
        sha256: sha256(pngBytes(640, 360, "m6-v3-last")),
        mime_type: "image/png",
        bytes: pngBytes(640, 360, "m6-v3-last").length,
        width: 640,
        height: 360,
        token: group.shot_evidence[0].reference_inputs[1].token,
        source_id: "ai-video-experiments",
        relative_path: "m6-v3/inputs/last.png",
      },
    ],
  });
  assert.ok(group.shot_evidence[0].reference_inputs.every((reference) => /^[A-Za-z0-9_-]{6,128}$/.test(reference.token)));
  assert.equal(result._media[group.shot_evidence[0].reference_inputs[0].token].source_path, evidence.firstPath);
  assert.equal(result._media[group.shot_evidence[0].reference_inputs[1].token].source_path, evidence.lastPath);
  assert.equal(JSON.stringify(publicExternalMediaProjection(result)).includes(paths.root), false);
  assert.equal(JSON.stringify(group.shot_evidence).includes("source_path"), false);

  await writeFile(path.join(evidence.experiment, "sidecars", "shot-b-result.json"), JSON.stringify({
    ...evidence.result,
    duration_seconds: 10,
  }));
  const mismatchedTiming = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const mismatchedShot = mismatchedTiming.groups.find((item) => item.sha256 === evidence.videoSha256).shot_evidence[0];
  assert.equal(mismatchedShot.prompt_text, "sealed prompt m6-v3");
  assert.equal(mismatchedShot.timing_basis, undefined);
  assert.equal(mismatchedShot.duration_seconds, undefined);
});

test("AI-VIDEO Experiments M6 evidence rejects wrong output identity and a mismatched Prompt hash join", async () => {
  const paths = await fixture();
  const evidence = await writeM6Experiment(paths.artifacts, "m6-rejected");
  const resultPath = path.join(evidence.experiment, "sidecars", "shot-b-result.json");
  const resolvedPath = path.join(evidence.experiment, "sidecars", "requests", "b-resolved.json");

  await writeFile(resultPath, JSON.stringify({ ...evidence.result, output_sha256: "f".repeat(64) }));
  const wrongOutput = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  let group = wrongOutput.groups.find((item) => item.sha256 === evidence.videoSha256);
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.reported_status, null);

  await writeFile(resultPath, JSON.stringify(evidence.result));
  await writeFile(resolvedPath, JSON.stringify({ ...evidence.resolved, prompt_text: "different prompt" }));
  const wrongPrompt = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  group = wrongPrompt.groups.find((item) => item.sha256 === evidence.videoSha256);
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.prompt_text, null);
  assert.equal(group.technical_gate, null);
});

test("AI-VIDEO Experiments causal handoff binds only the summary, trimmed Prompt, preview, and exact Shot gate", async () => {
  const paths = await fixture();
  const experiment = path.join(paths.artifacts, "causal-handoff");
  const outputs = path.join(experiment, "outputs");
  const sidecars = path.join(experiment, "sidecars");
  const inputs = path.join(experiment, "inputs");
  await Promise.all([
    mkdir(outputs, { recursive: true }),
    mkdir(sidecars, { recursive: true }),
    mkdir(inputs, { recursive: true }),
  ]);
  const videoPath = path.join(outputs, "handoff.mp4");
  const videoBytes = Buffer.from("causal handoff video");
  const videoSha256 = sha256(videoBytes);
  const promptText = "causal exact prompt";
  const promptSha256 = sha256(promptText);
  const resolvedGenerationHash = sha256("causal-resolved");
  const firstBytes = pngBytes(512, 512, "causal-first");
  const lastBytes = pngBytes(512, 512, "causal-last");
  const firstPath = path.join(inputs, "first.png");
  const lastPath = path.join(inputs, "last.png");
  await Promise.all([
    writeFile(videoPath, videoBytes),
    writeFile(firstPath, firstBytes),
    writeFile(lastPath, lastBytes),
    writeFile(path.join(sidecars, "prompt.txt"), `\n${promptText}\n`),
  ]);
  const shared = {
    prompt_sha256: promptSha256,
    resolved_generation_hash: resolvedGenerationHash,
    provider: "comfy-local-h3",
    provider_kind: "minimax_h3_fl2va",
    model_id: "minimax-h3-fl2va",
    fps: 24,
    frame_count: 124,
    first_frame_sha256: sha256(firstBytes),
    last_frame_sha256: sha256(lastBytes),
  };
  await writeFile(path.join(sidecars, "run-summary.json"), JSON.stringify({
    ...shared,
    output_path: videoPath,
    output_sha256: videoSha256,
    output_size_bytes: videoBytes.length,
    task_state: "succeeded",
  }));
  await writeFile(path.join(sidecars, "exact-preview.json"), JSON.stringify(shared));
  await writeFile(path.join(sidecars, "shot-gate.json"), JSON.stringify({
    schema: "ai-video-development-shot-gate/1",
    artifact_sha256: videoSha256,
    gate_verdict: "PASS",
    required_findings: [{ id: "causal.transfer", verdict: "PASS", evidence: "transfer is visible" }],
    human_first_findings: [{ id: "performance.naturalness", verdict: "NOT_EVALUATED" }],
  }));

  let result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  let group = result.groups.find((item) => item.sha256 === videoSha256);
  assert.equal(group.reported_status, "OUTPUT_RECORDED");
  assert.equal(group.technical_gate, "PASS");
  assert.equal(group.human_verdict, "NOT_EVALUATED");
  assert.equal(group.shot_evidence[0].entity_kind, "generation");
  assert.equal(group.shot_evidence[0].shot_id, null);
  assert.equal(group.shot_evidence[0].prompt_text, promptText);
  assert.equal(group.shot_evidence[0].generation_type, "minimax_h3_fl2va");
  assert.equal(group.shot_evidence[0].start_seconds, 0);
  assert.equal(group.shot_evidence[0].end_seconds, 124 / 24);
  assert.equal(group.shot_evidence[0].timing_basis, "exact_output_clip");
  assert.equal(group.shot_evidence[0].reference_inputs.length, 2);

  await writeFile(path.join(sidecars, "exact-preview.json"), JSON.stringify({ ...shared, prompt_sha256: "0".repeat(64) }));
  result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  group = result.groups.find((item) => item.sha256 === videoSha256);
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.reported_status, null);
});

test("AI-VIDEO Experiments conditioning arm binds exact evaluation and Prompt but leaves references unevaluated without an upload receipt", async () => {
  const paths = await fixture();
  const experiment = path.join(paths.artifacts, "conditioning");
  const outputs = path.join(experiment, "outputs");
  const sidecars = path.join(experiment, "sidecars");
  const workflows = path.join(experiment, "workflows");
  const inputs = path.join(experiment, "inputs");
  await Promise.all([
    mkdir(outputs, { recursive: true }),
    mkdir(sidecars, { recursive: true }),
    mkdir(workflows, { recursive: true }),
    mkdir(inputs, { recursive: true }),
  ]);
  const arm = "A_FL2VA_CURRENT_LAST";
  const videoPath = path.join(outputs, `${arm}.mp4`);
  const videoBytes = Buffer.from("conditioning arm video");
  const firstPath = path.join(inputs, "first.png");
  const lastPath = path.join(inputs, "last.png");
  const firstBytes = pngBytes(768, 768, "conditioning-first");
  const lastBytes = pngBytes(768, 768, "conditioning-last");
  const promptText = "conditioning workflow prompt";
  const workflow = {
    "5": { class_type: "MiniMaxH3ImageToVideo", inputs: { prompt: promptText, first_frame: ["15", 0], last_frame: ["16", 0] } },
    "15": { class_type: "LoadImage", inputs: { image: "upload/first.png" } },
    "16": { class_type: "LoadImage", inputs: { image: "upload/last.png" } },
  };
  const workflowBytes = Buffer.from(JSON.stringify(workflow));
  const workflowPath = path.join(workflows, `${arm}.submitted_workflow.json`);
  await Promise.all([
    writeFile(videoPath, videoBytes),
    writeFile(firstPath, firstBytes),
    writeFile(lastPath, lastBytes),
    writeFile(workflowPath, workflowBytes),
  ]);
  const contract = {
    schema: "ai-video-h3-conditioning-attribution/1",
    arms: { [arm]: { mode: "FL2VA", workflow_sha256: sha256(workflowBytes) } },
    inputs: {
      first: { path: firstPath, sha256: sha256(firstBytes) },
      current_last: { path: lastPath, sha256: sha256(lastBytes) },
    },
    fl2va_prompt_sha256: sha256(promptText),
    i2va_prompt_sha256: sha256("unused"),
  };
  const evaluation = {
    schema: "ai-video-h3-conditioning-arm-result/1",
    arm,
    video_path: videoPath,
    video_sha256: sha256(videoBytes),
    probe: { duration_seconds: 5.167, fps: 24, frame_count: 124 },
    gate_verdict: "FAIL_STOP_BEFORE_NEXT_ARM",
    human_verdict: "NOT_EVALUATED",
    requirement_findings: [{ requirement_id: "conditioning.last_frame", verdict: "FAIL", reason: "endpoint drift" }],
    human_findings: [{ requirement_id: "identity", verdict: "NOT_EVALUATED", note: "human review pending" }],
  };
  await Promise.all([
    writeFile(path.join(sidecars, "experiment_contract.json"), JSON.stringify(contract)),
    writeFile(path.join(sidecars, `${arm}.evaluation.json`), JSON.stringify(evaluation)),
  ]);

  let result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  let group = result.groups.find((item) => item.sha256 === evaluation.video_sha256);
  const armEvidence = group.shot_evidence[0];
  assert.equal(armEvidence.entity_kind, "experiment_arm");
  assert.equal(armEvidence.shot_id, arm);
  assert.equal(armEvidence.generation_type, "FL2VA");
  assert.equal(armEvidence.prompt_text, promptText);
  assert.equal(armEvidence.generation_result, "OUTPUT_RECORDED");
  assert.equal(armEvidence.start_seconds, 0);
  assert.equal(armEvidence.end_seconds, 5.167);
  assert.equal(armEvidence.timing_basis, "exact_output_clip");
  assert.equal(armEvidence.technical_gate, "FAIL_STOP_BEFORE_NEXT_ARM");
  assert.equal(armEvidence.human_verdict, "NOT_EVALUATED");
  assert.deepEqual(armEvidence.findings.map((finding) => finding.verdict), ["FAIL", "NOT_EVALUATED"]);
  assert.deepEqual(armEvidence.reference_inputs, []);
  assert.equal(armEvidence.reference_binding_status, "NOT_EVALUATED");
  assert.match(armEvidence.reference_binding_reason, /upload receipt/i);

  await writeFile(path.join(sidecars, "experiment_contract.json"), JSON.stringify({
    ...contract,
    arms: { [arm]: { ...contract.arms[arm], workflow_sha256: "f".repeat(64) } },
  }));
  result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  group = result.groups.find((item) => item.sha256 === evaluation.video_sha256);
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.prompt_text, null);
});

test("conflicting verified experiment evidence for duplicate bytes is surfaced as ambiguous", async () => {
  const paths = await fixture();
  const sharedBytes = Buffer.from("same bytes, conflicting experiment claims");
  const first = await writeM6Experiment(paths.artifacts, "m6-first", { videoBytes: sharedBytes, shotId: "shot-first" });
  await writeM6Experiment(paths.artifacts, "m6-second", { videoBytes: sharedBytes, shotId: "shot-second" });

  const result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const group = result.groups.find((item) => item.sha256 === first.videoSha256);
  assert.equal(group.locations.length, 2);
  assert.equal(group.metadata_status, "ambiguous_verified_experiment_evidence");
  assert.equal(group.association_ambiguity, true);
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.prompt_text, null);
  assert.equal(group.reported_status, null);
  assert.equal(group.technical_gate, null);
  assert.equal(group.human_verdict, null);
});

test("conflicting findings for otherwise identical experiment evidence are surfaced as ambiguous", async () => {
  const paths = await fixture();
  const sharedVideo = Buffer.from("same video and request, conflicting findings");
  const sharedFirst = pngBytes(640, 360, "shared-first");
  const sharedLast = pngBytes(640, 360, "shared-last");
  const sharedOptions = {
    videoBytes: sharedVideo,
    shotId: "shot-shared",
    promptText: "shared sealed prompt",
    firstBytes: sharedFirst,
    lastBytes: sharedLast,
    assetIdPrefix: "shared-anchor",
    requirementHash: sha256("shared-requirement"),
    resolvedGenerationHash: sha256("shared-generation"),
  };
  const first = await writeM6Experiment(paths.artifacts, "findings-first", {
    ...sharedOptions,
    findingEvidence: "handoff remains visible",
  });
  await writeM6Experiment(paths.artifacts, "findings-second", {
    ...sharedOptions,
    findingEvidence: "handoff is occluded",
  });

  const result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const group = result.groups.find((item) => item.sha256 === first.videoSha256);
  assert.equal(group.metadata_status, "ambiguous_verified_experiment_evidence");
  assert.equal(group.association_ambiguity, true);
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.prompt_text, null);
});

test("unsafe experiment sidecar strings fail closed before reaching the public projection", async () => {
  const paths = await fixture();
  const unsafeAssetId = "safe-looking-asset-id";
  const unsafeFinding = "证据路径：/home/operator/private/reference；媒体→/tmp/secret.mp4";
  const evidence = await writeM6Experiment(paths.artifacts, "unsafe-public-text", {
    assetIdPrefix: unsafeAssetId,
    findingEvidence: unsafeFinding,
  });

  const result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const group = result.groups.find((item) => item.sha256 === evidence.videoSha256);
  const serialized = JSON.stringify(publicExternalMediaProjection(result));
  assert.equal(group.metadata_status, "not_evaluated");
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.prompt_text, null);
  assert.equal(serialized.includes("/home/operator"), false);
  assert.equal(serialized.includes("/tmp/secret.mp4"), false);
});

test("legacy M6 human_pass true/false/null keeps pass distinct from unevaluated", async () => {
  const paths = await fixture();
  const passed = await writeM6Experiment(paths.artifacts, "human-pass", { humanVerdict: null, humanPass: true });
  const falseLegacy = await writeM6Experiment(paths.artifacts, "human-false", { humanVerdict: null, humanPass: false });
  const nullLegacy = await writeM6Experiment(paths.artifacts, "human-null", { humanVerdict: null, humanPass: null });

  const result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const bySha = new Map(result.groups.map((group) => [group.sha256, group]));
  assert.equal(bySha.get(passed.videoSha256).human_verdict, "PASS");
  assert.equal(bySha.get(falseLegacy.videoSha256).human_verdict, "NOT_EVALUATED");
  assert.equal(bySha.get(nullLegacy.videoSha256).human_verdict, "NOT_EVALUATED");
});

test("unknown schemas under the experiments source retain exact refs without gaining experiment semantics", async () => {
  const paths = await fixture();
  const videoPath = path.join(paths.artifacts, "unknown.mp4");
  const videoBytes = Buffer.from("unknown experiment bytes");
  await writeFile(videoPath, videoBytes);
  await writeFile(path.join(paths.artifacts, "unknown.json"), JSON.stringify({
    schema: "unknown-experiment/99",
    output_path: videoPath,
    sha256: sha256(videoBytes),
    prompt: "must stay hidden",
    status: "succeeded",
  }));

  const result = await catalogExternalMedia({ sources: experimentsSource(paths.artifacts) });
  const group = result.groups[0];
  assert.equal(group.metadata_status, "not_evaluated");
  assert.deepEqual(group.shot_evidence, []);
  assert.equal(group.prompt_text, null);
  assert.equal(group.reported_status, null);
  assert.deepEqual(group.evidence_refs, [{ source_id: "ai-video-experiments", relative_path: "unknown.json" }]);
});
