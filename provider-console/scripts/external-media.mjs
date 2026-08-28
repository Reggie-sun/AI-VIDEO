import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { lstat, open, realpath, readdir } from "node:fs/promises";
import path from "node:path";

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
const METADATA_ALIASES = Object.freeze({
  prompt: ["prompt", "prompt_text", "positive_prompt"],
  shot: ["shot", "shot_id"],
  shot_type: ["shot_type", "type"],
  generation_type: ["generation_type", "mode"],
  status: ["status", "state", "success"],
});
const BINDING_KEYS = new Set(["path", "file", "output_path", "local_path"]);

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
    return {
      bytes: size,
      mtime_ms: Number(stat.mtimeMs),
      sha256: await digestOpenedFile(file, size),
      identity: [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String),
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
  if (typeof node.sha256 === "string" && node.sha256.toLowerCase() === media.sha256) return true;
  return [...BINDING_KEYS].some((key) => isExactPathBinding(node[key], sidecarPath, media.source_path));
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

async function metadataForMedia(sidecars, media, limits) {
  const metadata = {};
  const evidenceRefs = [];
  let verifiedChain = null;
  for (const sidecarPath of sidecars) {
    try {
      const parsed = await readSidecarObject(sidecarPath, limits, media.source_root);
      if (!parsed) continue;
      if (hasDirectBinding(parsed, sidecarPath, media)) {
        evidenceRefs.push(path.relative(media.source_root, sidecarPath).split(path.sep).join("/"));
        if (media.source_kind === "external_project_asset" && path.basename(sidecarPath) === "result.json") {
          verifiedChain = await externalProjectEvidenceChain(sidecarPath, parsed, media, limits) || verifiedChain;
        }
      }
      if (parsed.schema === EXTERNAL_METADATA_SCHEMA) {
        collectMetadata(parsed, sidecarPath, media, false, metadata);
      }
    } catch {
      // Sidecars are advisory. Their parse errors are deliberately not projected.
    }
  }
  return {
    metadata: { ...metadata, ...(verifiedChain?.metadata || {}) },
    metadata_status: verifiedChain ? "verified_evidence_chain" : Object.keys(metadata).length ? "bound" : "not_evaluated",
    evidence_refs: [...new Set([...evidenceRefs, ...(verifiedChain?.evidence_refs || [])])].sort(),
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
  const sidecars = files
    .filter((file) => path.extname(file).toLowerCase() === ".json")
    .slice(0, limits.maxSidecarsPerRoot);
  const records = [];
  for (const sourcePath of files) {
    if (records.length >= limits.maxMediaPerRoot) break;
    const mime_type = VIDEO_MIME_TYPES.get(path.extname(sourcePath).toLowerCase());
    if (!mime_type) continue;
    try {
      const inspected = await inspectMedia(root, sourcePath);
      if (!inspected) continue;
      const media = {
        source_path: sourcePath,
        source_id: sourceId,
        source_root: root,
        source_kind: source.kind,
        mime_type,
        ...inspected,
      };
      const { metadata, metadata_status, evidence_refs } = await metadataForMedia(sidecars, media, limits);
      records.push({
        ...media,
        source_label: sourceLabel,
        metadata,
        metadata_status,
        evidence_refs,
      });
    } catch {
      // A file that changes while being inspected is omitted rather than guessed.
    }
  }
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
    const metadataSource = duplicates.find((record) => record.metadata_status === "verified_evidence_chain")
      || duplicates.find((record) => record.metadata_status === "bound")
      || preview;
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
      metadata: metadataSource.metadata,
      metadata_status: metadataSource.metadata_status,
      prompt_text: metadataSource.metadata.prompt ?? null,
      shot_id: metadataSource.metadata.shot ?? null,
      shot_type: metadataSource.metadata.shot_type ?? null,
      generation_type: metadataSource.metadata.generation_type ?? null,
      reported_status: metadataSource.metadata.status ?? null,
      evidence_refs: [...new Map(duplicates
        .flatMap((record) => record.evidence_refs.map((relative_path) => ({ source_id: record.source_id, relative_path })))
        .map((reference) => [`${reference.source_id}/${reference.relative_path}`, reference])).values()]
        .sort((left, right) => `${left.source_id}/${left.relative_path}`.localeCompare(`${right.source_id}/${right.relative_path}`)),
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
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  const { _media, ...safe } = value;
  return safe;
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

export const __test__ = { configuredLimits, collectMetadata, isDirectBinding, safeSourceId };
