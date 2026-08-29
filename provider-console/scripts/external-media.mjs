import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { lstat, open, realpath, readdir } from "node:fs/promises";
import path from "node:path";
import { EXPERIMENT_SOURCE_ID, experimentEvidenceForMedia, indexExperimentImages } from "./experiment-evidence.mjs";

const VIDEO_MIME_TYPES = new Map([
  [".mp4", "video/mp4"],
  [".mov", "video/quicktime"],
  [".webm", "video/webm"],
  [".m4v", "video/x-m4v"],
]);
const DEFAULT_LIMITS = Object.freeze({
  maxDepth: 10,
  maxMediaPerRoot: 1024,
  maxEntriesPerRoot: 10_000,
  maxSidecarsPerRoot: 1024,
  maxSidecarBytes: 2 * 1024 * 1024,
});
const SOURCE_PRIORITY = Object.freeze({
  development_artifact: 0,
  external_project_asset: 1,
  raw_provider_output: 2,
});
const EXTERNAL_METADATA_SCHEMA = "ai-video-external-media-metadata/1";
const LONG_VIDEO_MANIFEST_FORMAT = "minimax_h3_t8_accepted_manifest";
const MEDIA_SCAN_CONCURRENCY = 8;
const EMBEDDED_METADATA_MAX_BYTES = 2 * 1024 * 1024;
const EMBEDDED_METADATA_TIMEOUT_MS = 5_000;
const COMFY_PROMPT_NODE_TYPES = new Set([
  "MiniMaxH3AudioConditioningT8",
  "MiniMaxH3ImageToVideo",
]);
const METADATA_ALIASES = Object.freeze({
  prompt: ["prompt", "prompt_text", "positive_prompt"],
  shot: ["shot", "shot_id"],
  shot_type: ["shot_type", "type"],
  generation_type: ["generation_type", "mode"],
  status: ["status", "state", "success"],
});
const BINDING_KEYS = new Set(["path", "file", "output_path", "local_path"]);
const PRIVATE_PROJECTION_KEYS = new Set(["_media", "source_path", "source_root", "identity"]);
const POSIX_ABSOLUTE_PATH = /(^|[^A-Za-z0-9_:/\\])\/(?!\/)[^\s"'`)\]},;]+/;
const WINDOWS_ABSOLUTE_PATH = /(^|[^A-Za-z0-9_:/\\])(?:[A-Za-z]:[\\/]|\\\\)[^\s"'`)\]},;]+/;
const SIGNED_URL = /\b(?:https?|s3):\/\/\S*[?&](?:x-amz-|x-goog-|signature=|sig=|token=|access[_-]?key|expires=)/i;
const SECRET_TEXT = /\b(?:bearer\s+[A-Za-z0-9._~-]{12,}|(?:api[_-]?key|secret|access[_-]?token)\s*[:=]\s*\S+)/i;
const TRACEBACK_TEXT = /Traceback \(most recent call last\):|(?:^|\n)\s*File\s+"[^"]+",\s+line\s+\d+|(?:^|\n)\s*at\s+\S+\s+\([^\n)]+:\d+:\d+\)/;
const MARKUP_CLOSING_TAG = /<\/[A-Za-z][A-Za-z0-9_-]{0,63}>/g;

function containedPath(root, candidate) {
  return candidate === root || candidate.startsWith(`${root}${path.sep}`);
}

function sameNonEmptyString(left, right) {
  return typeof left === "string" && left.length > 0 && left === right;
}

function configuredLimits(limits = {}) {
  const result = { ...DEFAULT_LIMITS };
  for (const key of Object.keys(DEFAULT_LIMITS)) {
    if (Number.isSafeInteger(limits[key]) && limits[key] >= 0) result[key] = limits[key];
  }
  return result;
}

function sourcePriority(kind) {
  return SOURCE_PRIORITY[kind] ?? Number.MAX_SAFE_INTEGER;
}

function safeSourceId(source) {
  return /^[A-Za-z0-9_-]{1,64}$/.test(source?.id || "") ? source.id : null;
}

function relativeLocation(root, sourcePath) {
  const relativePath = path.relative(root, sourcePath).split(path.sep).join("/");
  return { relative_path: relativePath, file_name: path.basename(sourcePath) };
}

function safeSourceLabel(source) {
  const label = typeof source?.label === "string" ? source.label.trim() : "";
  if (!label || label.includes("\0") || path.isAbsolute(label)) return "外部媒体来源";
  if (typeof source?.root === "string" && label.includes(source.root)) return "外部媒体来源";
  return label.slice(0, 256);
}

function publicSource(source, status, extra = {}) {
  return {
    id: safeSourceId(source) || "invalid_source",
    label: safeSourceLabel(source),
    kind: typeof source?.kind === "string" ? source.kind : "unknown",
    status,
    ...extra,
  };
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

function openedIdentity(stat) {
  return [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String);
}

function sameIdentity(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function embeddedComfyMetadata(promptTag) {
  if (typeof promptTag !== "string" || !promptTag || Buffer.byteLength(promptTag) > EMBEDDED_METADATA_MAX_BYTES) return null;
  let graph;
  try {
    graph = JSON.parse(promptTag);
  } catch {
    return null;
  }
  if (!graph || typeof graph !== "object" || Array.isArray(graph)) return null;
  const candidates = new Map();
  for (const node of Object.values(graph)) {
    if (!node || typeof node !== "object" || Array.isArray(node) || !COMFY_PROMPT_NODE_TYPES.has(node.class_type)) continue;
    const prompt = primitiveMetadataValue(node.inputs?.prompt);
    if (typeof prompt !== "string") continue;
    const declaredType = typeof node.inputs?.task_type === "string" && /^[A-Za-z0-9_-]{1,64}$/.test(node.inputs.task_type)
      ? node.inputs.task_type
      : node.class_type;
    const metadata = { prompt, generation_type: declaredType };
    candidates.set(JSON.stringify(metadata), metadata);
  }
  return candidates.size === 1 ? [...candidates.values()][0] : null;
}

async function probeEmbeddedComfyMetadata(file) {
  return new Promise((resolve) => {
    const child = spawn("ffprobe", [
      "-v", "error",
      "-show_entries", "format_tags=prompt",
      "-of", "json",
      "/proc/self/fd/3",
    ], { stdio: ["ignore", "pipe", "ignore", file.fd] });
    const chunks = [];
    let bytes = 0;
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(value);
    };
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      finish(null);
    }, EMBEDDED_METADATA_TIMEOUT_MS);
    child.stdout.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes > EMBEDDED_METADATA_MAX_BYTES) {
        child.kill("SIGKILL");
        finish(null);
        return;
      }
      chunks.push(chunk);
    });
    child.on("error", () => finish(null));
    child.on("close", (code) => {
      if (settled || code !== 0) return finish(null);
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        finish(embeddedComfyMetadata(value?.format?.tags?.prompt));
      } catch {
        finish(null);
      }
    });
  });
}

async function inspectMedia(root, sourcePath) {
  const file = await open(sourcePath, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat({ bigint: true }),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (!stat.isFile() || openedPath !== sourcePath || !containedPath(root, openedPath)) return null;
    const size = Number(stat.size);
    if (!Number.isSafeInteger(size) || size < 0) return null;
    const identity = openedIdentity(stat);
    const sha256 = await digestOpenedFile(file, size);
    const embedded_metadata = path.extname(sourcePath).toLowerCase() === ".mp4"
      ? await probeEmbeddedComfyMetadata(file)
      : null;
    const [finalStat, finalOpenedPath] = await Promise.all([
      file.stat({ bigint: true }),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (
      !finalStat.isFile()
      || Number(finalStat.size) !== size
      || finalOpenedPath !== sourcePath
      || !sameIdentity(identity, openedIdentity(finalStat))
    ) return null;
    return {
      bytes: size,
      mtime_ms: Number(stat.mtimeMs),
      sha256,
      identity,
      embedded_metadata,
    };
  } finally {
    await file.close();
  }
}

async function walkRoot(root, limits) {
  const files = [];
  let entriesSeen = 0;
  async function visit(directory, depth) {
    if (depth > limits.maxDepth || entriesSeen >= limits.maxEntriesPerRoot) return;
    let entries;
    try {
      entries = await readdir(directory, { withFileTypes: true });
    } catch {
      return;
    }
    entries.sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      if (entriesSeen >= limits.maxEntriesPerRoot) return;
      entriesSeen += 1;
      const candidate = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) {
        await visit(candidate, depth + 1);
        continue;
      }
      if (entry.isFile()) files.push(candidate);
    }
  }
  await visit(root, 0);
  return files;
}

function isExactPathBinding(value, sidecarPath, mediaPath) {
  if (typeof value !== "string" || !value || value.includes("\0")) return false;
  const resolved = path.resolve(path.dirname(sidecarPath), value);
  return resolved === mediaPath;
}

function isDirectBinding(node, sidecarPath, media) {
  if (!node || typeof node !== "object" || Array.isArray(node)) return false;
  let strongIdentity = false;
  if (Object.hasOwn(node, "sha256")) {
    if (typeof node.sha256 !== "string" || node.sha256.toLowerCase() !== media.sha256) return false;
    strongIdentity = true;
  }
  if (Object.hasOwn(node, "size_bytes")) {
    if (!Number.isSafeInteger(node.size_bytes) || node.size_bytes !== media.bytes) return false;
  }
  for (const key of BINDING_KEYS) {
    if (!Object.hasOwn(node, key)) continue;
    if (!isExactPathBinding(node[key], sidecarPath, media.source_path)) return false;
    strongIdentity = true;
  }
  return strongIdentity;
}

function primitiveMetadataValue(value) {
  if (typeof value === "string") return value.trim().slice(0, 8_000) || undefined;
  if (typeof value === "boolean" || Number.isFinite(value)) return value;
  return undefined;
}

function collectMetadata(value, sidecarPath, media, inheritedBinding = false, collected = {}) {
  if (!value || typeof value !== "object") return collected;
  if (Array.isArray(value)) {
    for (const item of value) collectMetadata(item, sidecarPath, media, inheritedBinding, collected);
    return collected;
  }
  const bound = inheritedBinding || isDirectBinding(value, sidecarPath, media);
  if (bound) {
    for (const [field, aliases] of Object.entries(METADATA_ALIASES)) {
      if (collected[field] !== undefined) continue;
      for (const alias of aliases) {
        const metadataValue = primitiveMetadataValue(value[alias]);
        if (metadataValue !== undefined) {
          collected[field] = metadataValue;
          break;
        }
      }
    }
  }
  for (const child of Object.values(value)) collectMetadata(child, sidecarPath, media, bound, collected);
  return collected;
}

function hasDirectBinding(value, sidecarPath, media) {
  if (!value || typeof value !== "object") return false;
  if (Array.isArray(value)) return value.some((item) => hasDirectBinding(item, sidecarPath, media));
  if (isDirectBinding(value, sidecarPath, media)) return true;
  return Object.values(value).some((child) => hasDirectBinding(child, sidecarPath, media));
}

function collectDirectBindingNodes(value, sidecarPath, media, collected = []) {
  if (!value || typeof value !== "object") return collected;
  if (Array.isArray(value)) {
    for (const item of value) collectDirectBindingNodes(item, sidecarPath, media, collected);
    return collected;
  }
  if (isDirectBinding(value, sidecarPath, media)) collected.push(value);
  for (const child of Object.values(value)) collectDirectBindingNodes(child, sidecarPath, media, collected);
  return collected;
}

async function externalMetadataForMedia(value, sidecarPath, media, limits, collected) {
  collectMetadata(value, sidecarPath, media, false, collected);
  if (collected.prompt !== undefined) return null;
  for (const node of collectDirectBindingNodes(value, sidecarPath, media)) {
    const promptPath = resolveSourceReference(media.source_root, node.prompt_path);
    if (!promptPath) continue;
    const prompt = await readBoundPrompt(promptPath, node.prompt_sha256, limits, media.source_root);
    if (!prompt) continue;
    collected.prompt = prompt;
    return promptPath;
  }
  return null;
}

function exactRelativeBinding(base, reference, root, mediaPath) {
  if (typeof reference !== "string" || !reference || reference.includes("\0") || path.isAbsolute(reference)) return false;
  const parts = reference.split(/[\\/]/);
  if (parts.some((part) => !part || part === "." || part === "..")) return false;
  const resolved = path.resolve(base, ...parts);
  return containedPath(root, resolved) && resolved === mediaPath;
}

function longVideoMetadata(node) {
  const prompt = primitiveMetadataValue(node?.prompt);
  if (
    typeof prompt !== "string"
    || typeof node?.model_id !== "string"
    || !node.model_id.trim()
    || typeof node?.candidate_id !== "string"
    || !node.candidate_id.trim()
    || !Number.isSafeInteger(node?.index)
    || node.index < 0
  ) return null;
  return { prompt, shot_type: "long_video_segment" };
}

function longVideoCandidateEvidence(sidecarPath, value, media) {
  if (
    path.basename(sidecarPath) !== "candidate.json"
    || value?.schema !== 1
    || value?.status !== "candidate"
    || !/^[A-Za-z0-9_-]{1,256}$/.test(value?.chain_id || "")
    || !/^[A-Za-z0-9_-]{1,256}$/.test(value?.candidate_id || "")
    || !Number.isSafeInteger(value?.index)
    || value.index < 0
    || String(value?.video_sha256 || "").toLowerCase() !== media.sha256
  ) return null;
  let chainRoot = path.dirname(sidecarPath);
  while (containedPath(media.source_root, chainRoot) && path.basename(chainRoot) !== value.chain_id) {
    const parent = path.dirname(chainRoot);
    if (parent === chainRoot) return null;
    chainRoot = parent;
  }
  const expectedDirectory = path.join(chainRoot, "candidates", `segment_${String(value.index).padStart(5, "0")}`, value.candidate_id);
  if (
    path.basename(chainRoot) !== value.chain_id
    || path.dirname(sidecarPath) !== expectedDirectory
    || sidecarPath !== path.join(expectedDirectory, "candidate.json")
    || media.source_path !== path.join(expectedDirectory, "candidate.mp4")
    || !exactRelativeBinding(chainRoot, value.video_path, media.source_root, media.source_path)
  ) return null;
  const metadata = longVideoMetadata(value);
  return metadata ? {
    status: "bound",
    metadata,
    evidence_refs: [path.relative(media.source_root, sidecarPath).split(path.sep).join("/")],
  } : null;
}

function longVideoManifestEvidence(sidecarPath, value, media) {
  if (
    path.basename(sidecarPath) !== "manifest.json"
    || value?.schema !== 2
    || value?.format !== LONG_VIDEO_MANIFEST_FORMAT
    || !Array.isArray(value?.segments)
  ) return null;
  const matches = value.segments
    .filter((segment) => (
      String(segment?.video_sha256 || "").toLowerCase() === media.sha256
      && exactRelativeBinding(path.dirname(sidecarPath), segment?.video_path, media.source_root, media.source_path)
    ))
    .map(longVideoMetadata)
    .filter(Boolean);
  const unique = new Map(matches.map((metadata) => [JSON.stringify(metadata), metadata]));
  if (unique.size !== 1) return null;
  return {
    status: "bound",
    metadata: [...unique.values()][0],
    evidence_refs: [path.relative(media.source_root, sidecarPath).split(path.sep).join("/")],
  };
}

function longVideoEvidence(sidecarPath, value, media) {
  return longVideoCandidateEvidence(sidecarPath, value, media)
    || longVideoManifestEvidence(sidecarPath, value, media);
}

async function metadataForMedia(sidecars, media, limits, experimentImages) {
  const metadata = {};
  const evidenceRefs = [];
  const parsedSidecars = [];
  const longVideoChains = [];
  let verifiedChain = null;
  let composition = null;
  for (const sidecarPath of sidecars) {
    try {
      const parsed = await readSidecarObject(sidecarPath, limits, media.source_root);
      if (!parsed) continue;
      parsedSidecars.push({ path: sidecarPath, value: parsed });
      if (hasDirectBinding(parsed, sidecarPath, media)) {
        evidenceRefs.push(path.relative(media.source_root, sidecarPath).split(path.sep).join("/"));
        if (media.source_kind === "external_project_asset" && path.basename(sidecarPath) === "result.json") {
          verifiedChain = await externalProjectEvidenceChain(sidecarPath, parsed, media, limits) || verifiedChain;
        }
      }
      if (media.source_kind === "development_artifact" && sidecarPath.endsWith(".receipt.json")) {
        verifiedChain = await artifactReceiptEvidenceChain(sidecarPath, parsed, media, limits) || verifiedChain;
      }
      if (media.source_kind === "development_artifact" && path.basename(sidecarPath) === "ecommerce-package.json") {
        composition = await declaredEcommerceComposition(sidecarPath, parsed, media, limits) || composition;
      }
      if (parsed.schema === EXTERNAL_METADATA_SCHEMA) {
        const promptPath = await externalMetadataForMedia(parsed, sidecarPath, media, limits, metadata);
        if (promptPath) evidenceRefs.push(path.relative(media.source_root, promptPath).split(path.sep).join("/"));
      }
      const longVideoChain = longVideoEvidence(sidecarPath, parsed, media);
      if (longVideoChain) {
        longVideoChains.push(longVideoChain);
        evidenceRefs.push(...longVideoChain.evidence_refs);
      }
    } catch {
      // Sidecars are advisory. Their parse errors are deliberately not projected.
    }
  }
  const experimentChain = media.source_id === EXPERIMENT_SOURCE_ID
    ? await experimentEvidenceForMedia(parsedSidecars, media, limits, experimentImages, experimentEvidenceHelpers)
    : null;
  const longVideoSignatures = new Set(longVideoChains.map((chain) => JSON.stringify(chain.metadata)));
  const longVideoAmbiguity = longVideoSignatures.size > 1;
  const longVideoChain = longVideoAmbiguity ? null : longVideoChains[0];
  const embeddedChain = media.embedded_metadata && !Object.keys(metadata).length
    ? {
        status: "bound",
        metadata: media.embedded_metadata,
        evidence_refs: [relativeLocation(media.source_root, media.source_path).relative_path],
      }
    : null;
  const selectedChain = experimentChain || verifiedChain || longVideoChain || embeddedChain;
  const associationAmbiguityTiers = [];
  if (longVideoAmbiguity) associationAmbiguityTiers.push("bound");
  if (selectedChain?.association_ambiguity === true) {
    associationAmbiguityTiers.push(experimentChain ? "experiment" : selectedChain.status?.startsWith("verified_") ? "verified" : "bound");
  }
  return {
    metadata: { ...metadata, ...(selectedChain?.metadata || {}) },
    metadata_status: selectedChain?.status || (Object.keys(metadata).length ? "bound" : "not_evaluated"),
    evidence_refs: [...new Set([...evidenceRefs, ...(selectedChain?.evidence_refs || [])])].sort(),
    composition,
    shot_evidence: selectedChain?.shot_evidence || [],
    technical_gate: selectedChain?.technical_gate ?? null,
    human_verdict: selectedChain?.human_verdict ?? null,
    experiment_signature: selectedChain?.experiment_signature || null,
    association_ambiguity: associationAmbiguityTiers.length > 0,
    association_ambiguity_tiers: [...new Set(associationAmbiguityTiers)],
    reference_descriptors: selectedChain?.reference_descriptors || {},
  };
}

async function readSidecarObject(sidecarPath, limits, root) {
  const file = await open(sidecarPath, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat(),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (!stat.isFile() || stat.size > limits.maxSidecarBytes || openedPath !== sidecarPath || !containedPath(root, openedPath)) return null;
    const parsed = JSON.parse(await file.readFile({ encoding: "utf8" }));
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
  } finally {
    await file.close();
  }
}

async function externalProjectEvidenceChain(resultPath, result, media, limits) {
  try {
    const directory = path.dirname(resultPath);
    const names = ["resolved_request.json", "fetch_receipt.json", "observation.json", "submit_result.json"];
    const [resolved, fetchReceipt, observation, submitResult] = await Promise.all(
      names.map((name) => readSidecarObject(path.join(directory, name), limits, media.source_root)),
    );
    const request = resolved?.activation_scope?.request;
    const sha = media.sha256;
    if (
      !request
      || String(result.sha256 || "").toLowerCase() !== sha
      || String(fetchReceipt?.artifact_sha256 || "").toLowerCase() !== sha
      || !sameNonEmptyString(fetchReceipt.observation_fingerprint, observation?.observation_fingerprint)
      || !sameNonEmptyString(observation?.submit_result_fingerprint, submitResult?.result_fingerprint)
      || !sameNonEmptyString(submitResult?.resolved_generation_hash, resolved?.resolved_generation_hash)
      || !sameNonEmptyString(submitResult?.generation_id, resolved?.generation_id)
      || !sameNonEmptyString(request.target_shot_id, result.shot)
      || Number(resolved?.effective_seed) !== Number(result.seed)
      || !sameNonEmptyString(request.prompt_text, resolved?.prompt_text)
      || !sameNonEmptyString(request.mode, resolved?.mode)
      || typeof observation?.state !== "string"
      || !observation.state
    ) return null;
    return {
      status: "verified_evidence_chain",
      metadata: {
        prompt: resolved.prompt_text,
        shot: request.target_shot_id,
        generation_type: resolved.mode,
        status: observation.state,
      },
      evidence_refs: [path.basename(resultPath), ...names]
        .map((name) => path.relative(media.source_root, path.join(directory, name)).split(path.sep).join("/")),
    };
  } catch {
    return null;
  }
}

function resolveSourceReference(root, reference) {
  if (typeof reference !== "string" || !reference || reference.includes("\0") || path.isAbsolute(reference)) return null;
  const normalized = reference.split("\\").join("/");
  const sourcePrefix = `${path.basename(root)}/`;
  const rootRelative = normalized.startsWith(sourcePrefix) ? normalized.slice(sourcePrefix.length) : normalized;
  const parts = rootRelative.split("/");
  if (!parts.length || parts.some((part) => !part || part === "." || part === "..")) return null;
  const resolved = path.resolve(root, ...parts);
  return containedPath(root, resolved) ? resolved : null;
}

async function readBoundPrompt(promptPath, expectedSha256, limits, root) {
  if (!/^[a-f0-9]{64}$/i.test(expectedSha256 || "")) return null;
  const file = await open(promptPath, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat(),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (!stat.isFile() || stat.size > limits.maxSidecarBytes || openedPath !== promptPath || !containedPath(root, openedPath)) return null;
    const bytes = await file.readFile();
    // Development artifact receipts bind the producer's stripped prompt text;
    // the text file's storage whitespace is not part of that receipt identity.
    const prompt = bytes.toString("utf8").trim();
    if (createHash("sha256").update(prompt, "utf8").digest("hex") !== expectedSha256.toLowerCase()) return null;
    return prompt ? prompt.slice(0, 8_000) : null;
  } finally {
    await file.close();
  }
}

async function artifactReceiptEvidenceChain(receiptPath, receipt, media, limits) {
  try {
    const outputPath = resolveSourceReference(media.source_root, receipt?.output?.path);
    if (
      outputPath !== media.source_path
      || String(receipt?.output?.sha256 || "").toLowerCase() !== media.sha256
      || Number(receipt?.output?.size_bytes) !== media.bytes
    ) return null;

    const statePath = receiptPath.replace(/\.receipt\.json$/, ".state.json");
    if (statePath === receiptPath) return null;
    const state = await readSidecarObject(statePath, limits, media.source_root);
    const declaredReceiptPath = resolveSourceReference(media.source_root, state?.receipt);
    const promptPath = resolveSourceReference(media.source_root, receipt?.prompt_path);
    const shot = boundedString(receipt?.shot_id);
    const generationType = boundedString(receipt?.settings?.mode);
    const reportedStatus = boundedString(state?.status);
    if (
      !state
      || declaredReceiptPath !== receiptPath
      || String(state.output_sha256 || "").toLowerCase() !== media.sha256
      || !sameNonEmptyString(state.shot_id, receipt.shot_id)
      || !sameNonEmptyString(state.prompt_id, receipt.prompt_id)
      || Number(state.seed) !== Number(receipt.seed)
      || !shot
      || !generationType
      || !reportedStatus
    ) return null;
    const prompt = promptPath
      ? await readBoundPrompt(promptPath, receipt.prompt_sha256, limits, media.source_root)
      : null;
    return {
      status: "verified_artifact_receipt",
      metadata: {
        ...(prompt ? { prompt } : {}),
        shot,
        generation_type: generationType,
        status: reportedStatus,
      },
      evidence_refs: [...(prompt ? [promptPath] : []), receiptPath, statePath]
        .map((reference) => path.relative(media.source_root, reference).split(path.sep).join("/")),
    };
  } catch {
    return null;
  }
}

async function checksumBindsMedia(checksumPath, media, limits) {
  const file = await open(checksumPath, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat(),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (!stat.isFile() || stat.size > Math.min(limits.maxSidecarBytes, 4_096) || openedPath !== checksumPath || !containedPath(media.source_root, openedPath)) return false;
    const match = /^([a-f0-9]{64})(?:\s+[^\r\n]+)?$/i.exec((await file.readFile({ encoding: "utf8" })).trim());
    return Boolean(match && match[1].toLowerCase() === media.sha256);
  } finally {
    await file.close();
  }
}

function boundedString(value) {
  return typeof value === "string" ? value.trim().slice(0, 8_000) || null : null;
}

function ecommerceShotProjection(shotId, intent, packageValue) {
  const copy = Array.isArray(packageValue.copy_graphics_plan)
    ? packageValue.copy_graphics_plan
      .filter((entry) => entry?.shot_id === shotId)
      .map((entry) => boundedString(entry?.text))
      .filter(Boolean)
    : [];
  const audioEventIds = new Set(Array.isArray(intent.audio_event_ids) ? intent.audio_event_ids : []);
  const dialogue = Array.isArray(packageValue.audio_plan?.events)
    ? packageValue.audio_plan.events
      .filter((event) => {
        const kind = String(event?.kind || "").toUpperCase();
        return (kind === "DIALOGUE" || kind === "VOICE_OVER")
          && audioEventIds.has(event?.event_id)
          && Array.isArray(event?.shot_ids)
          && event.shot_ids.includes(shotId);
      })
      .map((event) => boundedString(event?.verbatim_line) || boundedString(event?.text))
      .filter(Boolean)
    : [];
  return {
    shot_id: shotId,
    duration_basis: boundedString(intent.duration_basis),
    reported_status: "DECLARED_NOT_EVALUATED",
    purpose: boundedString(intent.purpose),
    talent_action: boundedString(intent.talent_action),
    ...(boundedString(intent.product_state) ? { product_state: boundedString(intent.product_state) } : {}),
    ...(boundedString(intent.camera_intent) ? { camera_intent: boundedString(intent.camera_intent) } : {}),
    ...(boundedString(intent.visual_strategy_need) ? { visual_strategy_need: boundedString(intent.visual_strategy_need) } : {}),
    start_seconds: Number.isFinite(intent.start_seconds) ? intent.start_seconds : null,
    end_seconds: Number.isFinite(intent.end_seconds) ? intent.end_seconds : null,
    copy,
    dialogue,
  };
}

async function declaredEcommerceComposition(packagePath, packageValue, media, limits) {
  try {
    if (packageValue?.schema_version !== "ecommerce-ad-workflow/package/2") return null;
    const projectRoot = path.dirname(packagePath);
    const relativeMedia = path.relative(projectRoot, media.source_path);
    const mediaParts = relativeMedia.split(path.sep);
    if (path.isAbsolute(relativeMedia) || mediaParts[0] !== "final" || mediaParts.length < 2) return null;
    const extension = path.extname(media.source_path);
    const checksumPath = `${media.source_path.slice(0, -extension.length)}.sha256`;
    if (!await checksumBindsMedia(checksumPath, media, limits)) return null;
    if (!Array.isArray(packageValue.storyboard) || !Array.isArray(packageValue.shot_intents)) return null;
    const orderedShotIds = packageValue.storyboard.flatMap((group) => Array.isArray(group?.shot_ids) ? group.shot_ids : []);
    if (
      !orderedShotIds.length
      || orderedShotIds.length > 200
      || orderedShotIds.some((shotId) => !boundedString(shotId))
      || new Set(orderedShotIds).size !== orderedShotIds.length
    ) return null;
    const intents = new Map();
    for (const intent of packageValue.shot_intents) {
      const shotId = boundedString(intent?.shot_id);
      if (!shotId || intents.has(shotId)) return null;
      intents.set(shotId, intent);
    }
    if (orderedShotIds.some((shotId) => !intents.has(shotId))) return null;
    return {
      composition_status: "declared",
      association_status: "co_located_declared_package",
      ordered_shots: orderedShotIds.map((shotId) => ecommerceShotProjection(shotId, intents.get(shotId), packageValue)),
      evidence_refs: [packagePath, checksumPath]
        .map((reference) => path.relative(media.source_root, reference).split(path.sep).join("/")),
    };
  } catch {
    return null;
  }
}

async function mapWithConcurrency(values, concurrency, mapper) {
  const results = new Array(values.length);
  let nextIndex = 0;
  async function worker() {
    while (nextIndex < values.length) {
      const index = nextIndex;
      nextIndex += 1;
      results[index] = await mapper(values[index]);
    }
  }
  await Promise.all(Array.from(
    { length: Math.min(Math.max(concurrency, 1), values.length) },
    () => worker(),
  ));
  return results;
}

async function scanSource(source, limits) {
  const sourceId = safeSourceId(source);
  if (!sourceId || !["development_artifact", "raw_provider_output", "external_project_asset"].includes(source?.kind)) {
    return { source: publicSource(source, "unavailable"), records: [] };
  }
  const sourceLabel = safeSourceLabel(source);
  let root;
  try {
    const stat = await lstat(source.root);
    if (!stat.isDirectory()) return { source: publicSource(source, "unavailable"), records: [] };
    root = await realpath(source.root);
  } catch {
    return { source: publicSource(source, "unavailable"), records: [] };
  }
  const files = await walkRoot(root, limits);
  const experimentImages = await indexExperimentImages(files, root, sourceId, experimentEvidenceHelpers);
  const sidecars = files
    .filter((file) => path.extname(file).toLowerCase() === ".json")
    .slice(0, limits.maxSidecarsPerRoot);
  const mediaFiles = files
    .filter((sourcePath) => VIDEO_MIME_TYPES.has(path.extname(sourcePath).toLowerCase()))
    .slice(0, limits.maxMediaPerRoot);
  const scannedRecords = await mapWithConcurrency(mediaFiles, MEDIA_SCAN_CONCURRENCY, async (sourcePath) => {
    const mime_type = VIDEO_MIME_TYPES.get(path.extname(sourcePath).toLowerCase());
    try {
      const inspected = await inspectMedia(root, sourcePath);
      if (!inspected) return null;
      const media = {
        source_path: sourcePath,
        source_id: sourceId,
        source_root: root,
        source_kind: source.kind,
        mime_type,
        ...inspected,
      };
      const {
        metadata,
        metadata_status,
        evidence_refs,
        composition,
        shot_evidence,
        technical_gate,
        human_verdict,
        experiment_signature,
        association_ambiguity,
        association_ambiguity_tiers,
        reference_descriptors,
      } = await metadataForMedia(sidecars, media, limits, experimentImages);
      return {
        ...media,
        source_label: sourceLabel,
        metadata,
        metadata_status,
        evidence_refs: [...new Set([...evidence_refs, ...(composition?.evidence_refs || [])])].sort(),
        composition,
        shot_evidence,
        technical_gate,
        human_verdict,
        experiment_signature,
        association_ambiguity,
        association_ambiguity_tiers,
        reference_descriptors,
      };
    } catch {
      // A file that changes while being inspected is omitted rather than guessed.
      return null;
    }
  });
  const records = scannedRecords.filter(Boolean);
  return { source: publicSource(source, "available", { media_count: records.length }), records };
}

function compareRecords(left, right) {
  if (right.mtime_ms !== left.mtime_ms) return right.mtime_ms - left.mtime_ms;
  if (left.sha256 !== right.sha256) return left.sha256.localeCompare(right.sha256);
  return left.source_path.localeCompare(right.source_path);
}

function externalToken(record) {
  const relative = relativeLocation(record.source_root, record.source_path).relative_path;
  const locationHash = createHash("sha256").update(relative).digest("hex").slice(0, 16);
  const token = `external_${record.source_id}_${record.sha256.slice(0, 16)}_${locationHash}`;
  return token.slice(0, 128);
}

const experimentEvidenceHelpers = Object.freeze({
  inspectMedia,
  readBoundPrompt,
  externalToken,
  relativeLocation,
});

function metadataRecordsConflict(records) {
  return ["prompt", "shot", "shot_type", "generation_type", "status"].some((field) => {
    const values = new Set(records
      .map((record) => record.metadata?.[field])
      .filter((value) => value !== undefined && value !== null && value !== "")
      .map((value) => JSON.stringify(value)));
    return values.size > 1;
  });
}

function recordAmbiguousAtTier(record, tier) {
  if (!record.association_ambiguity) return false;
  if (Array.isArray(record.association_ambiguity_tiers)) return record.association_ambiguity_tiers.includes(tier);
  if (tier === "experiment") return Boolean(record.experiment_signature);
  if (tier === "verified") return record.metadata_status.startsWith("verified_");
  return record.metadata_status === "bound";
}

function groupProjection(records) {
  const bySha = new Map();
  for (const record of records) {
    const group = bySha.get(record.sha256) || [];
    group.push(record);
    bySha.set(record.sha256, group);
  }
  const media = {};
  const groups = [...bySha.entries()].map(([sha256, duplicates]) => {
    duplicates.sort((left, right) => {
      const priority = sourcePriority(left.source_kind) - sourcePriority(right.source_kind);
      if (priority) return priority;
      return compareRecords(left, right);
    });
    const preview = duplicates[0];
    const experimentRecords = duplicates.filter((record) => record.experiment_signature || recordAmbiguousAtTier(record, "experiment"));
    const verifiedRecords = duplicates.filter((record) => record.metadata_status.startsWith("verified_") || recordAmbiguousAtTier(record, "verified"));
    const boundRecords = duplicates.filter((record) => record.metadata_status === "bound" || recordAmbiguousAtTier(record, "bound"));
    const selectedTier = experimentRecords.length ? "experiment" : verifiedRecords.length ? "verified" : "bound";
    const selectedEvidenceTier = selectedTier === "experiment"
      ? experimentRecords
      : selectedTier === "verified" ? verifiedRecords : boundRecords;
    const experimentSignatures = new Set(experimentRecords.map((record) => record.experiment_signature));
    const associationAmbiguity = selectedEvidenceTier.some((record) => recordAmbiguousAtTier(record, selectedTier))
      || experimentSignatures.size > 1
      || metadataRecordsConflict(selectedEvidenceTier);
    const experimentSource = associationAmbiguity ? null : duplicates.find((record) => record.experiment_signature);
    const metadataSource = experimentSource
      || duplicates.find((record) => record.metadata_status.startsWith("verified_"))
      || duplicates.find((record) => record.metadata_status === "bound")
      || preview;
    const compositionSource = duplicates.find((record) => record.composition);
    const token = externalToken(preview);
    const locations = duplicates
      .map((record) => {
        const locationToken = externalToken(record);
        media[locationToken] = {
          source_path: record.source_path,
          source_root: record.source_root,
          source_id: record.source_id,
          mime_type: record.mime_type,
          bytes: record.bytes,
          sha256: record.sha256,
          identity: record.identity,
        };
        if (!associationAmbiguity) Object.assign(media, record.reference_descriptors || {});
        return {
          source_id: record.source_id,
          source_label: record.source_label,
          source_kind: record.source_kind,
          token: locationToken,
          modified_at: new Date(record.mtime_ms).toISOString(),
          bytes: record.bytes,
          ...relativeLocation(record.source_root, record.source_path),
        };
      })
      .sort((left, right) => `${left.source_id}/${left.relative_path}`.localeCompare(`${right.source_id}/${right.relative_path}`));
    return {
      sha256,
      token,
      bytes: preview.bytes,
      mime_type: preview.mime_type,
      modified_at: new Date(preview.mtime_ms).toISOString(),
      status: "NOT_EVALUATED",
      evidence_level: "non_canonical",
      preview: {
        token,
        source_id: preview.source_id,
        mime_type: preview.mime_type,
        bytes: preview.bytes,
        ...relativeLocation(preview.source_root, preview.source_path),
      },
      locations,
      metadata: associationAmbiguity ? {} : metadataSource.metadata,
      metadata_status: associationAmbiguity
        ? (experimentRecords.length ? "ambiguous_verified_experiment_evidence" : "ambiguous_bound_evidence")
        : metadataSource.metadata_status,
      prompt_text: associationAmbiguity ? null : (metadataSource.metadata.prompt ?? null),
      shot_id: associationAmbiguity ? null : (metadataSource.metadata.shot ?? null),
      shot_type: associationAmbiguity ? null : (metadataSource.metadata.shot_type ?? null),
      generation_type: associationAmbiguity ? null : (metadataSource.metadata.generation_type ?? null),
      reported_status: associationAmbiguity ? null : (metadataSource.metadata.status ?? null),
      evidence_refs: [...new Map(duplicates
        .flatMap((record) => record.evidence_refs.map((relative_path) => ({ source_id: record.source_id, relative_path })))
        .map((reference) => [`${reference.source_id}/${reference.relative_path}`, reference])).values()]
        .sort((left, right) => `${left.source_id}/${left.relative_path}`.localeCompare(`${right.source_id}/${right.relative_path}`)),
      composition: compositionSource?.composition || null,
      shot_evidence: associationAmbiguity ? [] : (metadataSource.shot_evidence || []),
      technical_gate: associationAmbiguity ? null : (metadataSource.technical_gate ?? null),
      human_verdict: associationAmbiguity ? null : (metadataSource.human_verdict ?? null),
      association_ambiguity: associationAmbiguity,
      generation_status: "NOT_EVALUATED",
      lifecycle_status: "NOT_EVALUATED",
      evidence_classification: "non_canonical",
      _mtime_ms: Math.max(...duplicates.map((record) => record.mtime_ms)),
    };
  });
  groups.sort((left, right) => (right._mtime_ms - left._mtime_ms) || left.sha256.localeCompare(right.sha256));
  return {
    groups: groups.map(({ _mtime_ms, ...group }) => group),
    media,
  };
}

export function publicExternalMediaProjection(value) {
  if (typeof value === "string") {
    const pathScanValue = value.replace(MARKUP_CLOSING_TAG, " ");
    if (
      value.includes("\0")
      || POSIX_ABSOLUTE_PATH.test(pathScanValue)
      || WINDOWS_ABSOLUTE_PATH.test(value)
      || SIGNED_URL.test(value)
      || SECRET_TEXT.test(value)
      || TRACEBACK_TEXT.test(value)
    ) return null;
    return value;
  }
  if (Array.isArray(value)) return value.map(publicExternalMediaProjection);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value)
    .filter(([key]) => !PRIVATE_PROJECTION_KEYS.has(key))
    .map(([key, item]) => [key, publicExternalMediaProjection(item)]));
}

export async function catalogExternalMedia({ sources = [], limits = {} } = {}) {
  const appliedLimits = configuredLimits(limits);
  const scanned = await Promise.all(sources.map((source) => scanSource(source, appliedLimits)));
  const records = scanned.flatMap(({ records }) => records);
  const { groups, media } = groupProjection(records);
  const available = scanned.filter(({ source }) => source.status === "available").length;
  return {
    status: available === sources.length ? "available" : available ? "partial" : "unavailable",
    boundary: { read_only: true, evidence_classification: "non_canonical" },
    sources: scanned.map(({ source }) => source),
    groups,
    summary: {
      source_count: sources.length,
      available_source_count: available,
      unique_media_count: groups.length,
      location_count: records.length,
    },
    _media: media,
  };
}

export const __test__ = { configuredLimits, collectMetadata, embeddedComfyMetadata, groupProjection, isDirectBinding, safeSourceId };
