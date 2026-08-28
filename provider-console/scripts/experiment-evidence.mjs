import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { open, realpath } from "node:fs/promises";
import path from "node:path";

export const EXPERIMENT_SOURCE_ID = "ai-video-experiments";

const EXPERIMENT_IMAGE_MIME_TYPES = new Map([
  [".png", "image/png"],
]);
const M6_GATE_SCHEMA = "m6-per-shot-post-media-gate/1";
const CAUSAL_GATE_SCHEMA = "ai-video-development-shot-gate/1";
const CONDITIONING_EVALUATION_SCHEMA = "ai-video-h3-conditioning-arm-result/1";
const CONDITIONING_CONTRACT_SCHEMA = "ai-video-h3-conditioning-attribution/1";
const REFERENCE_BINDING_NOT_EVALUATED = "缺少绑定 submitted workflow LoadImage 与 exact uploaded bytes 的 content-hash upload receipt";
const POSIX_ABSOLUTE_PATH = /(^|[^A-Za-z0-9_:/\\])\/(?!\/)[^\s"'`)\]},;]+/;
const WINDOWS_ABSOLUTE_PATH = /(^|[^A-Za-z0-9_:/\\])(?:[A-Za-z]:[\\/]|\\\\)[^\s"'`)\]},;]+/;
const SIGNED_URL = /\b(?:https?|s3):\/\/\S*[?&](?:x-amz-|x-goog-|signature=|sig=|token=|access[_-]?key|expires=)/i;
const SECRET_TEXT = /\b(?:bearer\s+[A-Za-z0-9._~-]{12,}|(?:api[_-]?key|secret|access[_-]?token)\s*[:=]\s*\S+)/i;
const TRACEBACK_TEXT = /Traceback \(most recent call last\):|(?:^|\n)\s*File\s+"[^"]+",\s+line\s+\d+|(?:^|\n)\s*at\s+\S+\s+\([^\n)]+:\d+:\d+\)/;

function containedPath(root, candidate) {
  return candidate === root || candidate.startsWith(`${root}${path.sep}`);
}

function sameNonEmptyString(left, right) {
  return typeof left === "string" && left.length > 0 && left === right;
}

async function digestOpenedFile(file, size) {
  const digest = createHash("sha256");
  let offset = 0;
  while (offset < size) {
    const chunk = Buffer.alloc(Math.min(1024 * 1024, size - offset));
    const { bytesRead } = await file.read(chunk, 0, chunk.length, offset);
    if (!bytesRead) throw new Error("short read");
    digest.update(chunk.subarray(0, bytesRead));
    offset += bytesRead;
  }
  return digest.digest("hex");
}

async function inspectExperimentImage(root, sourcePath, sourceId, mimeType) {
  const file = await open(sourcePath, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat({ bigint: true }),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (!stat.isFile() || openedPath !== sourcePath || !containedPath(root, openedPath)) return null;
    const size = Number(stat.size);
    if (!Number.isSafeInteger(size) || size < 24 || mimeType !== "image/png") return null;
    const header = Buffer.alloc(24);
    const { bytesRead } = await file.read(header, 0, header.length, 0);
    const signature = Buffer.from("89504e470d0a1a0a0000000d49484452", "hex");
    if (bytesRead !== header.length || !header.subarray(0, 16).equals(signature)) return null;
    const width = header.readUInt32BE(16);
    const height = header.readUInt32BE(20);
    if (!width || !height) return null;
    return {
      source_path: sourcePath,
      source_root: root,
      source_id: sourceId,
      mime_type: mimeType,
      bytes: size,
      width,
      height,
      sha256: await digestOpenedFile(file, size),
      identity: [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String),
    };
  } finally {
    await file.close();
  }
}

function boundedString(value) {
  return typeof value === "string" ? value.trim().slice(0, 8_000) || null : null;
}

function boundedPositiveNumber(value, maximum = 7_200) {
  const number = typeof value === "number" ? value : Number(value);
  return Number.isFinite(number) && number > 0 && number <= maximum ? number : null;
}

function exactOutputTiming(value) {
  const probe = value?.probe;
  const directDuration = boundedPositiveNumber(
    value?.duration_seconds ?? probe?.duration_seconds ?? probe?.format?.duration,
  );
  const videoStream = Array.isArray(probe?.streams)
    ? probe.streams.find((stream) => stream?.codec_type === "video")
    : null;
  const frameCount = boundedPositiveNumber(
    value?.frame_count ?? probe?.frame_count ?? videoStream?.nb_frames,
    Number.MAX_SAFE_INTEGER,
  );
  const fps = boundedPositiveNumber(value?.fps ?? probe?.fps, 1_000)
    || (() => {
      const [numerator, denominator] = String(videoStream?.r_frame_rate || "").split("/").map(Number);
      return denominator > 0 ? boundedPositiveNumber(numerator / denominator, 1_000) : null;
    })();
  const derivedDuration = boundedPositiveNumber(frameCount && fps ? frameCount / fps : null);
  if (directDuration && derivedDuration && Math.abs(directDuration - derivedDuration) > 0.05) return {};
  const duration = directDuration || derivedDuration;
  if (!duration) return {};
  return {
    start_seconds: 0,
    end_seconds: duration,
    duration_seconds: duration,
    timing_basis: "exact_output_clip",
    ...(fps ? { fps } : {}),
    ...(frameCount ? { frame_count: frameCount } : {}),
  };
}

function safePublicExperimentString(value) {
  return typeof value === "string"
    && !value.includes("\0")
    && !POSIX_ABSOLUTE_PATH.test(value)
    && !WINDOWS_ABSOLUTE_PATH.test(value)
    && !SIGNED_URL.test(value)
    && !SECRET_TEXT.test(value)
    && !TRACEBACK_TEXT.test(value);
}

function safePublicExperimentValue(value, depth = 0) {
  if (depth > 12) return false;
  if (typeof value === "string") return safePublicExperimentString(value);
  if (value === null || typeof value === "boolean" || typeof value === "number") return true;
  if (Array.isArray(value)) return value.every((item) => safePublicExperimentValue(item, depth + 1));
  if (!value || typeof value !== "object") return false;
  return Object.entries(value).every(([key, item]) => (
    safePublicExperimentString(key) && safePublicExperimentValue(item, depth + 1)
  ));
}

function normalizedSha256(value) {
  return /^[a-f0-9]{64}$/i.test(value || "") ? value.toLowerCase() : null;
}

function resolvedExperimentReference(root, sidecarPath, reference) {
  if (typeof reference !== "string" || !reference || reference.includes("\0")) return null;
  const resolved = path.isAbsolute(reference)
    ? path.normalize(reference)
    : path.resolve(path.dirname(sidecarPath), reference);
  return containedPath(root, resolved) ? resolved : null;
}

function exactExperimentOutput(media, sidecarPath, outputPath, outputSha256, outputSize) {
  if (resolvedExperimentReference(media.source_root, sidecarPath, outputPath) !== media.source_path) return false;
  if (normalizedSha256(outputSha256) !== media.sha256) return false;
  return outputSize === undefined || outputSize === null || Number(outputSize) === media.bytes;
}

function imageDescriptor(record) {
  return {
    source_path: record.source_path,
    source_root: record.source_root,
    source_id: record.source_id,
    mime_type: record.mime_type,
    bytes: record.bytes,
    sha256: record.sha256,
    identity: record.identity,
  };
}

function publicImageReference(record, role, assetId, helpers) {
  const token = helpers.externalToken(record);
  return {
    role,
    asset_id: assetId,
    sha256: record.sha256,
    mime_type: record.mime_type,
    bytes: record.bytes,
    width: record.width,
    height: record.height,
    token,
    source_id: record.source_id,
    relative_path: helpers.relativeLocation(record.source_root, record.source_path).relative_path,
  };
}

export async function indexExperimentImages(files, root, sourceId, helpers) {
  const empty = { bySha: new Map(), byPath: new Map(), byToken: new Map() };
  if (sourceId !== EXPERIMENT_SOURCE_ID) return empty;
  for (const sourcePath of files) {
    const mimeType = EXPERIMENT_IMAGE_MIME_TYPES.get(path.extname(sourcePath).toLowerCase());
    if (!mimeType) continue;
    try {
      const record = await inspectExperimentImage(root, sourcePath, sourceId, mimeType);
      if (!record) continue;
      const matches = empty.bySha.get(record.sha256) || [];
      matches.push(record);
      matches.sort((left, right) => left.source_path.localeCompare(right.source_path));
      empty.bySha.set(record.sha256, matches);
      empty.byPath.set(record.source_path, record);
      empty.byToken.set(helpers.externalToken(record), record);
    } catch {
      // Invalid or changing reference images are unavailable to experiment adapters.
    }
  }
  return empty;
}

function exactExperimentImage(images, expected, exactPath = null, preferredRoot = null) {
  const sha256 = normalizedSha256(expected?.sha256 ?? expected?.asset_sha256);
  if (!sha256) return null;
  const indexed = exactPath ? [images.byPath.get(exactPath)] : (images.bySha.get(sha256) || []);
  const candidates = preferredRoot ? indexed.filter((record) => record && containedPath(preferredRoot, record.source_path)) : indexed;
  return candidates.find((record) => record
    && record.sha256 === sha256
    && (!expected.mime_type || expected.mime_type === record.mime_type)
    && (expected.size_bytes === undefined || Number(expected.size_bytes) === record.bytes)
    && (expected.width === undefined || Number(expected.width) === record.width)
    && (expected.height === undefined || Number(expected.height) === record.height)) || null;
}

function referenceDescriptors(references, images) {
  const descriptors = {};
  for (const reference of references) {
    const record = images.byToken.get(reference.token);
    if (record) descriptors[reference.token] = imageDescriptor(record);
  }
  return descriptors;
}

function boundedStringArray(value) {
  if (!Array.isArray(value) || value.length > 200) return [];
  return value.map((item) => boundedString(item)).filter(Boolean);
}

function projectedFinding(value, idKey = "requirement_id") {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const requirementId = boundedString(value[idKey]);
  const verdict = boundedString(value.verdict);
  if (!requirementId || !verdict) return null;
  const evidence = boundedString(value.evidence) || boundedString(value.reason) || boundedString(value.note);
  return { requirement_id: requirementId, verdict, ...(evidence ? { evidence } : {}) };
}

function projectedFindingMap(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.values(value).map((finding) => projectedFinding(finding)).filter(Boolean).slice(0, 200);
}

function projectedFindingArray(value, idKey = "requirement_id") {
  if (!Array.isArray(value)) return [];
  return value.map((finding) => projectedFinding(finding, idKey)).filter(Boolean).slice(0, 200);
}

function aggregateHumanVerdict(findings) {
  const verdicts = findings.map((finding) => String(finding.verdict || "").toUpperCase()).filter(Boolean);
  if (verdicts.some((verdict) => verdict.includes("FAIL"))) return "FAIL";
  if (verdicts.length && verdicts.every((verdict) => verdict === "PASS" || verdict === "HUMAN_PASS")) return "PASS";
  return "NOT_EVALUATED";
}

function experimentSignature(value) {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function comparableReference(reference) {
  return {
    role: reference.role ?? null,
    asset_id: reference.asset_id ?? null,
    sha256: reference.sha256 ?? null,
    mime_type: reference.mime_type ?? null,
    bytes: reference.bytes ?? null,
    width: reference.width ?? null,
    height: reference.height ?? null,
  };
}

function comparableExperimentCandidate(candidate) {
  return {
    metadata: candidate.metadata,
    shot_evidence: candidate.shot_evidence.map((evidence) => ({
      ...evidence,
      reference_inputs: (evidence.reference_inputs || []).map(comparableReference),
    })),
    technical_gate: candidate.technical_gate,
    human_verdict: candidate.human_verdict,
  };
}

function acceptedExperimentCandidate(candidate) {
  if (!candidate) return null;
  const publicFields = {
    metadata: candidate.metadata,
    evidence_refs: candidate.evidence_refs,
    shot_evidence: candidate.shot_evidence,
    technical_gate: candidate.technical_gate,
    human_verdict: candidate.human_verdict,
  };
  if (!safePublicExperimentValue(publicFields)) return null;
  return {
    ...candidate,
    experiment_signature: experimentSignature(comparableExperimentCandidate(candidate)),
  };
}

function sameImageBinding(left, right) {
  return Boolean(left && right
    && sameNonEmptyString(left.role, right.role)
    && sameImageIdentity(left, right));
}

function sameImageIdentity(left, right) {
  return Boolean(left && right
    && sameNonEmptyString(left.asset_id, right.asset_id)
    && normalizedSha256(left.asset_sha256) === normalizedSha256(right.asset_sha256)
    && sameNonEmptyString(left.mime_type, right.mime_type)
    && Number(left.width) === Number(right.width)
    && Number(left.height) === Number(right.height)
    && Number(left.size_bytes) === Number(right.size_bytes));
}

function exactSidecar(parsedSidecars, expectedPath) {
  return parsedSidecars.find((sidecar) => sidecar.path === expectedPath) || null;
}

async function m6ExperimentEvidence(resultSidecar, parsedSidecars, media, limits, images, helpers) {
  const result = resultSidecar.value;
  if (!/^shot-[A-Za-z0-9_-]+-result\.json$/.test(path.basename(resultSidecar.path))) return null;
  if (!exactExperimentOutput(media, resultSidecar.path, result.output_path, result.output_sha256, result.output_size_bytes)) return null;
  const shotId = boundedString(result.shot_id);
  const requirementHash = normalizedSha256(result.requirement_hash);
  const resolvedGenerationHash = normalizedSha256(result.resolved_generation_hash);
  const promptSha256 = normalizedSha256(result.prompt_sha256);
  if (!shotId || !requirementHash || !resolvedGenerationHash || !promptSha256) return null;

  const sidecarRoot = path.dirname(resultSidecar.path);
  const requestRoot = path.join(sidecarRoot, "requests");
  const resolvedMatches = parsedSidecars.filter(({ path: sidecarPath, value }) => (
    path.dirname(sidecarPath) === requestRoot
    && sidecarPath.endsWith("-resolved.json")
    && normalizedSha256(value?.resolved_generation_hash) === resolvedGenerationHash
    && normalizedSha256(value?.requirement_hash) === requirementHash
  ));
  if (resolvedMatches.length !== 1) return null;
  const resolvedSidecar = resolvedMatches[0];
  const resolved = resolvedSidecar.value;
  const requestStem = path.basename(resolvedSidecar.path, "-resolved.json");
  const requirementSidecar = exactSidecar(parsedSidecars, path.join(requestRoot, `${requestStem}-requirement.json`));
  const promptPath = path.join(requestRoot, `${requestStem}-prompt.txt`);
  const requirement = requirementSidecar?.value;
  const targetShot = requirement?.target_shot;
  const request = resolved?.activation_scope?.request;
  const promptText = boundedString(resolved?.prompt_text);
  if (
    !requirement
    || normalizedSha256(requirement.requirement_hash) !== requirementHash
    || !sameNonEmptyString(targetShot?.shot_id, shotId)
    || !Number.isSafeInteger(Number(targetShot?.revision))
    || !request
    || !sameNonEmptyString(request.target_shot_id, shotId)
    || Number(request.target_shot_revision) !== Number(targetShot.revision)
    || normalizedSha256(request.requirement_hash) !== requirementHash
    || !sameNonEmptyString(request.mode, resolved.mode)
    || !sameNonEmptyString(request.prompt_text, resolved.prompt_text)
    || !sameNonEmptyString(requirement.generation_mode, resolved.mode)
    || !promptText
    || (result.prompt_text !== undefined && boundedString(result.prompt_text) !== promptText)
    || createHash("sha256").update(promptText, "utf8").digest("hex") !== promptSha256
  ) return null;
  const prompt = await helpers.readBoundPrompt(promptPath, promptSha256, limits, media.source_root);
  if (prompt !== promptText) return null;

  const resolvedBindings = Array.isArray(resolved.image_bindings) ? resolved.image_bindings : [];
  const requestBindings = Array.isArray(request.image_bindings) ? request.image_bindings : [];
  const assetEvidence = Array.isArray(requirement.asset_evidence) ? requirement.asset_evidence : [];
  if (!resolvedBindings.length || resolvedBindings.length > 10 || requestBindings.length !== resolvedBindings.length) return null;
  const references = [];
  for (const binding of resolvedBindings) {
    if (!["first_frame", "last_frame"].includes(binding?.role)) return null;
    const requestBinding = requestBindings.find((candidate) => candidate?.role === binding.role);
    const asset = assetEvidence.find((candidate) => candidate?.asset_id === binding.asset_id);
    const anchor = binding.role === "first_frame" ? result.first_anchor : result.last_anchor;
    if (
      !sameImageBinding(binding, requestBinding)
      || !sameImageIdentity(binding, asset)
      || (anchor && (
        !sameNonEmptyString(anchor.asset_id, binding.asset_id)
        || normalizedSha256(anchor.sha256) !== normalizedSha256(binding.asset_sha256)
        || Number(anchor.size_bytes) !== Number(binding.size_bytes)
      ))
    ) return null;
    const image = exactExperimentImage(images, binding, null, path.dirname(sidecarRoot));
    if (!image) return null;
    references.push(publicImageReference(image, binding.role, binding.asset_id, helpers));
  }

  const gateRoot = path.join(sidecarRoot, "gates");
  const gates = parsedSidecars.filter(({ path: sidecarPath, value }) => (
    path.dirname(sidecarPath) === gateRoot
    && value?.schema === M6_GATE_SCHEMA
    && sameNonEmptyString(value.shot_id, shotId)
    && normalizedSha256(value.requirement_hash) === requirementHash
    && normalizedSha256(value.video_sha256) === media.sha256
    && resolvedExperimentReference(media.source_root, sidecarPath, value.video_path) === media.source_path
    && (value.video_size_bytes === undefined || value.video_size_bytes === null || Number(value.video_size_bytes) === media.bytes)
  ));
  if (gates.length !== 1) return null;
  const gateSidecar = gates[0];
  const technicalGate = boundedString(gateSidecar.value.technical_gate);
  const humanVerdict = boundedString(gateSidecar.value.human_verdict)
    || (gateSidecar.value.human_pass === true ? "PASS" : "NOT_EVALUATED");
  if (!technicalGate) return null;
  const findings = projectedFindingMap(gateSidecar.value.findings);
  const generationType = boundedString(resolved.mode);
  const providerKind = boundedString(resolved.provider_kind);
  const providerName = boundedString(resolved.provider_name);
  const modelId = boundedString(resolved.model_id);
  if (!generationType || !providerKind || !providerName || !modelId) return null;

  const evidence = {
    entity_kind: "shot",
    association_status: "verified_experiment_evidence",
    shot_id: shotId,
    revision: Number(targetShot.revision),
    requirement_hash: requirementHash,
    intent: boundedString(targetShot.intent),
    dialogue: boundedString(targetShot.dialogue),
    narration: boundedString(targetShot.narration),
    continuity_constraints: boundedStringArray(targetShot.continuity_constraints),
    visual_strategy: boundedString(targetShot.visual_strategy),
    ...exactOutputTiming(result),
    prompt_text: promptText,
    generation_type: generationType,
    provider_kind: providerKind,
    provider_name: providerName,
    model_id: modelId,
    generation_result: "OUTPUT_RECORDED",
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    findings,
    reference_inputs: references,
  };
  const evidenceRefs = [resultSidecar.path, requirementSidecar.path, resolvedSidecar.path, promptPath, gateSidecar.path]
    .map((reference) => path.relative(media.source_root, reference).split(path.sep).join("/"));
  return {
    status: "verified_experiment_evidence",
    metadata: { prompt: promptText, shot: shotId, generation_type: generationType, status: "OUTPUT_RECORDED" },
    evidence_refs: evidenceRefs,
    shot_evidence: [evidence],
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    reference_descriptors: referenceDescriptors(references, images),
    experiment_signature: experimentSignature({
      kind: "m6",
      shotId,
      requirementHash,
      resolvedGenerationHash,
      promptSha256,
      generationType,
      providerKind,
      providerName,
      modelId,
      technicalGate,
      humanVerdict,
      references: references.map(({ role, asset_id, sha256 }) => ({ role, asset_id, sha256 })),
    }),
  };
}

function causalReferenceInputs(summary, preview, images, experimentRoot, helpers) {
  const references = [];
  for (const [role, field] of [["first_frame", "first_frame_sha256"], ["last_frame", "last_frame_sha256"]]) {
    const summarySha = normalizedSha256(summary[field]);
    const previewSha = normalizedSha256(preview[field]);
    if (!summarySha && !previewSha) continue;
    if (!summarySha || summarySha !== previewSha) return null;
    const image = exactExperimentImage(images, { sha256: summarySha }, null, experimentRoot);
    if (!image) return null;
    references.push(publicImageReference(image, role, role, helpers));
  }
  return references;
}

async function causalHandoffExperimentEvidence(summarySidecar, parsedSidecars, media, limits, images, helpers) {
  if (path.basename(summarySidecar.path) !== "run-summary.json") return null;
  const summary = summarySidecar.value;
  if (
    !exactExperimentOutput(media, summarySidecar.path, summary.output_path, summary.output_sha256, summary.output_size_bytes)
    || boundedString(summary.task_state)?.toLowerCase() !== "succeeded"
  ) return null;
  const directory = path.dirname(summarySidecar.path);
  const previewSidecar = exactSidecar(parsedSidecars, path.join(directory, "exact-preview.json"));
  const gateSidecar = exactSidecar(parsedSidecars, path.join(directory, "shot-gate.json"));
  const preview = previewSidecar?.value;
  const gate = gateSidecar?.value;
  const promptSha256 = normalizedSha256(summary.prompt_sha256);
  const resolvedGenerationHash = normalizedSha256(summary.resolved_generation_hash);
  const providerName = boundedString(summary.provider);
  const providerKind = boundedString(summary.provider_kind);
  const modelId = boundedString(summary.model_id);
  if (
    !preview
    || !gate
    || gate.schema !== CAUSAL_GATE_SCHEMA
    || normalizedSha256(gate.artifact_sha256) !== media.sha256
    || !promptSha256
    || normalizedSha256(preview.prompt_sha256) !== promptSha256
    || !resolvedGenerationHash
    || normalizedSha256(preview.resolved_generation_hash) !== resolvedGenerationHash
    || !providerName
    || !providerKind
    || !modelId
    || !sameNonEmptyString(preview.provider, providerName)
    || !sameNonEmptyString(preview.provider_kind, providerKind)
    || !sameNonEmptyString(preview.model_id, modelId)
  ) return null;
  const promptPath = path.join(directory, "prompt.txt");
  const promptText = await helpers.readBoundPrompt(promptPath, promptSha256, limits, media.source_root);
  if (!promptText) return null;
  const references = causalReferenceInputs(summary, preview, images, path.dirname(directory), helpers);
  if (!references) return null;
  const technicalGate = boundedString(gate.gate_verdict);
  if (!technicalGate) return null;
  const requiredFindings = projectedFindingArray(gate.required_findings, "id");
  const humanFindings = projectedFindingArray(gate.human_first_findings, "id");
  const humanVerdict = aggregateHumanVerdict(humanFindings);
  const findings = [...requiredFindings, ...humanFindings];
  const evidence = {
    entity_kind: "generation",
    association_status: "verified_experiment_evidence",
    shot_id: null,
    revision: null,
    requirement_hash: null,
    intent: null,
    dialogue: null,
    narration: null,
    continuity_constraints: [],
    visual_strategy: null,
    ...exactOutputTiming(summary),
    prompt_text: promptText,
    generation_type: providerKind,
    provider_kind: providerKind,
    provider_name: providerName,
    model_id: modelId,
    generation_result: "OUTPUT_RECORDED",
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    findings,
    reference_inputs: references,
  };
  const evidenceRefs = [summarySidecar.path, previewSidecar.path, promptPath, gateSidecar.path]
    .map((reference) => path.relative(media.source_root, reference).split(path.sep).join("/"));
  return {
    status: "verified_experiment_evidence",
    metadata: { prompt: promptText, generation_type: providerKind, status: "OUTPUT_RECORDED" },
    evidence_refs: evidenceRefs,
    shot_evidence: [evidence],
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    reference_descriptors: referenceDescriptors(references, images),
    experiment_signature: experimentSignature({
      kind: "causal_handoff",
      resolvedGenerationHash,
      promptSha256,
      providerName,
      providerKind,
      modelId,
      technicalGate,
      humanVerdict,
      references: references.map(({ role, sha256 }) => ({ role, sha256 })),
    }),
  };
}

function validWorkflowImageLink(workflow, link) {
  if (!Array.isArray(link) || link.length !== 2 || !["string", "number"].includes(typeof link[0])) return null;
  const loader = workflow[String(link[0])];
  const imageName = boundedString(loader?.inputs?.image);
  if (loader?.class_type !== "LoadImage" || !imageName) return null;
  return imageName;
}

async function conditioningExperimentEvidence(evaluationSidecar, parsedSidecars, media, images, helpers) {
  const evaluation = evaluationSidecar.value;
  if (
    evaluation?.schema !== CONDITIONING_EVALUATION_SCHEMA
    || !exactExperimentOutput(media, evaluationSidecar.path, evaluation.video_path, evaluation.video_sha256)
  ) return null;
  const arm = boundedString(evaluation.arm);
  if (!/^[A-Za-z0-9_-]{1,128}$/.test(arm || "")) return null;
  const directory = path.dirname(evaluationSidecar.path);
  const contractSidecar = exactSidecar(parsedSidecars, path.join(directory, "experiment_contract.json"));
  const contract = contractSidecar?.value;
  const armContract = contract?.arms?.[arm];
  const mode = boundedString(armContract?.mode);
  const workflowSidecar = exactSidecar(
    parsedSidecars,
    path.join(path.dirname(directory), "workflows", `${arm}.submitted_workflow.json`),
  );
  const workflowSha256 = normalizedSha256(armContract?.workflow_sha256);
  if (contract?.schema !== CONDITIONING_CONTRACT_SCHEMA || !mode || !workflowSidecar || !workflowSha256) return null;
  const inspectedWorkflow = await helpers.inspectMedia(media.source_root, workflowSidecar.path);
  if (!inspectedWorkflow || inspectedWorkflow.sha256 !== workflowSha256) return null;
  const workflow = workflowSidecar.value;
  const promptNodes = Object.values(workflow).filter((node) => (
    typeof node?.class_type === "string"
    && node.class_type.startsWith("MiniMaxH3")
    && typeof node?.inputs?.prompt === "string"
  ));
  if (promptNodes.length !== 1) return null;
  const promptNode = promptNodes[0];
  const promptText = promptNode.inputs.prompt;
  if (!promptText || promptText.length > 8_000 || promptText !== promptText.trim()) return null;
  const expectedPromptSha256 = normalizedSha256(
    mode === "FL2VA" ? contract.fl2va_prompt_sha256 : mode === "I2VA" ? contract.i2va_prompt_sha256 : null,
  );
  if (!expectedPromptSha256 || createHash("sha256").update(promptText, "utf8").digest("hex") !== expectedPromptSha256) return null;
  const firstLoader = validWorkflowImageLink(workflow, promptNode.inputs.first_frame);
  const lastLoader = promptNode.inputs.last_frame === null || promptNode.inputs.last_frame === undefined
    ? null
    : validWorkflowImageLink(workflow, promptNode.inputs.last_frame);
  if (!firstLoader || (mode === "FL2VA" && !lastLoader) || (mode === "I2VA" && lastLoader)) return null;
  const references = [];
  const technicalGate = boundedString(evaluation.gate_verdict);
  const humanVerdict = boundedString(evaluation.human_verdict) || "NOT_EVALUATED";
  if (!technicalGate) return null;
  const findings = [
    ...projectedFindingArray(evaluation.requirement_findings),
    ...projectedFindingArray(evaluation.human_findings),
  ];
  const evidence = {
    entity_kind: "experiment_arm",
    association_status: "verified_experiment_evidence",
    shot_id: arm,
    revision: null,
    requirement_hash: null,
    intent: null,
    dialogue: null,
    narration: null,
    continuity_constraints: [],
    visual_strategy: null,
    ...exactOutputTiming(evaluation),
    prompt_text: promptText,
    generation_type: mode,
    provider_kind: null,
    provider_name: null,
    model_id: null,
    generation_result: "OUTPUT_RECORDED",
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    findings,
    reference_inputs: references,
    reference_binding_status: "NOT_EVALUATED",
    reference_binding_reason: REFERENCE_BINDING_NOT_EVALUATED,
  };
  const evidenceRefs = [evaluationSidecar.path, contractSidecar.path, workflowSidecar.path]
    .map((reference) => path.relative(media.source_root, reference).split(path.sep).join("/"));
  return {
    status: "verified_experiment_evidence",
    metadata: { prompt: promptText, shot: arm, generation_type: mode, status: "OUTPUT_RECORDED" },
    evidence_refs: evidenceRefs,
    shot_evidence: [evidence],
    technical_gate: technicalGate,
    human_verdict: humanVerdict,
    reference_descriptors: referenceDescriptors(references, images),
    experiment_signature: experimentSignature({
      kind: "conditioning",
      arm,
      mode,
      workflowSha256,
      promptSha256: expectedPromptSha256,
      technicalGate,
      humanVerdict,
      references: references.map(({ role, asset_id, sha256 }) => ({ role, asset_id, sha256 })),
    }),
  };
}

export async function experimentEvidenceForMedia(parsedSidecars, media, limits, images, helpers) {
  try {
    const candidates = [];
    for (const sidecar of parsedSidecars) {
      if (/^shot-[A-Za-z0-9_-]+-result\.json$/.test(path.basename(sidecar.path))) {
        const candidate = acceptedExperimentCandidate(
          await m6ExperimentEvidence(sidecar, parsedSidecars, media, limits, images, helpers),
        );
        if (candidate) candidates.push(candidate);
      }
      if (path.basename(sidecar.path) === "run-summary.json") {
        const candidate = acceptedExperimentCandidate(
          await causalHandoffExperimentEvidence(sidecar, parsedSidecars, media, limits, images, helpers),
        );
        if (candidate) candidates.push(candidate);
      }
      if (sidecar.value?.schema === CONDITIONING_EVALUATION_SCHEMA) {
        const candidate = acceptedExperimentCandidate(
          await conditioningExperimentEvidence(sidecar, parsedSidecars, media, images, helpers),
        );
        if (candidate) candidates.push(candidate);
      }
    }
    if (!candidates.length) return null;
    const signatures = new Set(candidates.map((candidate) => candidate.experiment_signature));
    if (signatures.size > 1) {
      return {
        status: "ambiguous_verified_experiment_evidence",
        metadata: {},
        evidence_refs: [...new Set(candidates.flatMap((candidate) => candidate.evidence_refs))].sort(),
        shot_evidence: [],
        technical_gate: null,
        human_verdict: null,
        reference_descriptors: {},
        experiment_signature: null,
        association_ambiguity: true,
      };
    }
    return candidates[0];
  } catch {
    return null;
  }
}
