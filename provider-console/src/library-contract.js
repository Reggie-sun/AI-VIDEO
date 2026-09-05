import {
  externalGroupTitle,
  groupMatchesEvidenceFilter,
} from "./external-media-contract.js";

const SHA256 = /^[a-f0-9]{64}$/;
const TOKEN = /^[A-Za-z0-9_-]{6,128}$/;

function validMedia(media) {
  return (
    media
    && typeof media === "object"
    && SHA256.test(media.sha256 || "")
    && Number.isSafeInteger(media.bytes)
    && media.bytes > 0
    && typeof media.mime_type === "string"
    && media.mime_type.toLowerCase().startsWith("video/")
  );
}

function mediaUrl(media, prefix) {
  const token = media?.token || media?.media_token;
  return typeof token === "string" && TOKEN.test(token)
    ? `${prefix}${encodeURIComponent(token)}`
    : null;
}

function timestamp(value) {
  const result = Date.parse(value || "");
  return Number.isFinite(result) ? result : null;
}

function valueOrNull(value) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function uniqueValues(values) {
  return [...new Set(values.filter(Boolean))];
}

function verifiedSnapshot(detail, attempt) {
  const workspace = valueOrNull(detail?.workspace);
  const projectId = valueOrNull(detail?.project?.project_id);
  const shotId = valueOrNull(attempt?.target_shot_id || attempt?.shot_id);
  const revision = attempt?.target_shot_revision;
  const contentHash = valueOrNull(attempt?.target_shot_content_hash);
  const snapshot = attempt?.shot_snapshot;
  return Boolean(
    !workspace
    ? false
    : projectId
      && shotId
      && Number.isSafeInteger(revision)
      && revision > 0
      && SHA256.test(contentHash || "")
      && attempt?.shot_snapshot_status === "verified"
      && snapshot?.shot_id === shotId
      && snapshot?.revision === revision
      && snapshot?.content_hash === contentHash,
  );
}

function exactVersionKey(detail, attempt) {
  if (!verifiedSnapshot(detail, attempt)) return null;
  const workspace = valueOrNull(detail.workspace);
  const projectId = valueOrNull(detail.project?.project_id);
  const shotId = valueOrNull(attempt.target_shot_id || attempt.shot_id);
  return JSON.stringify([workspace, projectId, shotId]);
}

function runTitle(detail, attempt) {
  const projectTitle = valueOrNull(detail?.project?.title);
  const shotId = valueOrNull(attempt?.target_shot_id || attempt?.shot_id);
  const snapshotTitle = verifiedSnapshot(detail, attempt)
    ? valueOrNull(attempt?.shot_snapshot?.title)
    : null;
  const shotTitle = snapshotTitle && snapshotTitle !== shotId
    ? `${snapshotTitle} · ${shotId || ""}`.trim()
    : shotId;
  return [projectTitle, shotTitle].filter(Boolean).join(" · ") || null;
}

function runModel(attempt) {
  return valueOrNull(attempt?.provider?.model || attempt?.model);
}

function candidateDescriptors(attempt) {
  const descriptors = [];
  const candidates = Array.isArray(attempt?.candidate_media_items) ? attempt.candidate_media_items : [];
  for (const [index, item] of candidates.entries()) {
    descriptors.push({
      role: valueOrNull(item?.role) || `candidate_media_items:${index + 1}`,
      media: item?.media && typeof item.media === "object" ? item.media : item,
    });
  }
  for (const role of ["candidate_media", "fetched_media", "output_media", "video_media"]) {
    if (attempt?.[role]) descriptors.push({ role, media: attempt[role] });
  }
  return descriptors;
}

function runBindingKey(detail, attempt, attemptId) {
  return JSON.stringify([
    valueOrNull(detail?.workspace),
    valueOrNull(detail?.project?.project_id),
    attemptId,
    valueOrNull(attempt?.target_shot_id || attempt?.shot_id),
    attempt?.target_shot_revision ?? null,
    valueOrNull(attempt?.target_shot_content_hash),
    valueOrNull(attempt?.prompt_text),
  ]);
}

function runContexts(details) {
  const contexts = [];
  for (const detail of Array.isArray(details) ? details : []) {
    for (const [attemptIndex, attempt] of (Array.isArray(detail?.attempts) ? detail.attempts : []).entries()) {
      const attemptId = valueOrNull(attempt?.attempt_id || attempt?.id) || `attempt-${attemptIndex + 1}`;
      const model = runModel(attempt);
      const title = runTitle(detail, attempt);
      const versionKey = exactVersionKey(detail, attempt);
      const semanticBinding = runBindingKey(detail, attempt, attemptId);
      for (const [mediaIndex, descriptor] of candidateDescriptors(attempt).entries()) {
        if (!validMedia(descriptor.media)) continue;
        contexts.push({
          id: `runs:${detail?.workspace || ""}:${attemptId}:${descriptor.role}:${mediaIndex}`,
          sourceId: "runs",
          workspace: valueOrNull(detail?.workspace),
          ownerKey: JSON.stringify([detail?.workspace, detail?.project?.project_id]),
          attemptId,
          role: descriptor.role,
          title,
          semanticTitle: title,
          semanticBinding,
          model,
          prompt: valueOrNull(attempt?.prompt_text),
          startedAt: valueOrNull(attempt?.started_at),
          timeKind: timestamp(attempt?.started_at) === null ? null : "attempt",
          media: descriptor.media,
          url: mediaUrl(descriptor.media, "/api/runs/media/"),
          detail,
          attempt,
          group: null,
          versionKey,
          fileName: valueOrNull(descriptor.media?.asset_id),
          ambiguous: false,
        });
      }
    }
    const workspaceMedia = Array.isArray(detail?.workspace_media) ? detail.workspace_media : [];
    for (const [mediaIndex, media] of [...(detail?.active_render_media ? [detail.active_render_media] : []), ...workspaceMedia].entries()) {
      if (!validMedia(media)) continue;
      const isRender = media === detail.active_render_media;
      const projectTitle = valueOrNull(detail?.project?.title);
      const fileName = valueOrNull(media?.asset_id || media?.relative_path);
      contexts.push({
        id: `runs:${detail?.workspace || ""}:${isRender ? "active_render" : "workspace_media"}:${fileName || mediaIndex}`,
        sourceId: "runs",
        workspace: valueOrNull(detail?.workspace),
        ownerKey: JSON.stringify([detail?.workspace, detail?.project?.project_id]),
        attemptId: null,
        role: isRender ? "active_render" : "workspace_media",
        title: [projectTitle, isRender ? "合成成片" : fileName].filter(Boolean).join(" · ") || null,
        semanticTitle: null,
        semanticBinding: null,
        model: null,
        prompt: null,
        startedAt: isRender ? valueOrNull(media.started_at) : null,
        timeKind: isRender && timestamp(media.started_at) !== null ? "attempt" : null,
        media,
        url: mediaUrl(media, "/api/runs/media/"),
        detail,
        attempt: null,
        group: null,
        versionKey: null,
        fileName,
        ambiguous: false,
      });
    }
  }
  return contexts;
}

function externalContexts(catalog, canonicalContexts) {
  const contexts = [];
  for (const group of Array.isArray(catalog?.groups) ? catalog.groups : []) {
    if (!validMedia(group)) continue;
    const locations = Array.isArray(group.locations) ? group.locations : [];
    const title = valueOrNull(group?.shot_id);
    const model = valueOrNull(group?.model_id || group?.metadata?.model_id);
    for (const [index, location] of locations.entries()) {
      const sourceId = valueOrNull(location?.source_id);
      if (!sourceId) continue;
      const modifiedAt = valueOrNull(location?.modified_at || group?.modified_at);
      const media = {
        ...location,
        sha256: group.sha256,
        bytes: group.bytes,
        mime_type: group.mime_type,
      };
      contexts.push({
        id: `external:${sourceId}:${location?.relative_path || index}:${group.sha256}:${group.bytes}`,
        sourceId,
        workspace: null,
        attemptId: null,
        role: "external_output",
        title: title || externalGroupTitle({ ...group, preferred_location: location }),
        semanticTitle: title,
        semanticBinding: group?.association_ambiguity === true ? null : valueOrNull(group?.shot_id || group?.prompt_text || group?.model_id)
          ? JSON.stringify([group?.shot_id || null, group?.prompt_text || null, group?.model_id || group?.metadata?.model_id || null])
          : null,
        model,
        prompt: valueOrNull(group?.prompt_text),
        startedAt: modifiedAt,
        timeKind: timestamp(modifiedAt) === null ? null : "file",
        media,
        url: mediaUrl(location, "/api/external-media/media/"),
        detail: null,
        attempt: null,
        group,
        versionKey: null,
        fileName: valueOrNull(location?.file_name || location?.relative_path?.split("/").at(-1)),
        ambiguous: group?.association_ambiguity === true,
      });
      for (const [bindingIndex, binding] of (group.run_bindings || []).entries()) {
        if (binding.sha256 !== group.sha256 || binding.bytes !== group.bytes) continue;
        if (canonicalContexts.some((context) => context.workspace === binding.workspace && context.attemptId === binding.attempt_id && context.media.sha256 === group.sha256 && context.media.bytes === group.bytes)) continue;
        contexts.push({
          id: `external-binding:${sourceId}:${index}:${group.sha256}:${bindingIndex}`,
          sourceId,
          workspace: binding.workspace,
          ownerKey: JSON.stringify([binding.workspace, null]),
          attemptId: binding.attempt_id,
          role: `Runs evidence · ${(binding.media_roles || []).join(" / ")}`,
          title: binding.target_shot_id || "Shot 未提供",
          semanticTitle: binding.target_shot_id || null,
          semanticBinding: runBindingKey({ workspace: binding.workspace }, binding, binding.attempt_id),
          model: null,
          startedAt: null,
          timeKind: null,
          media,
          url: mediaUrl(location, "/api/external-media/media/"),
          detail: null,
          attempt: null,
          runBinding: binding,
          group,
          versionKey: null,
          fileName: location.file_name || null,
          ambiguous: false,
        });
      }
    }
  }
  return contexts;
}

function entryTimestamp(contexts, kind) {
  const matches = contexts.filter((context) => context.timeKind === kind && timestamp(context.startedAt) !== null);
  if (!matches.length) return null;
  return matches.reduce((latest, context) => (
    timestamp(context.startedAt) > timestamp(latest.startedAt) ? context : latest
  ));
}

function toEntry(id, contexts) {
  const attemptTime = entryTimestamp(contexts, "attempt");
  const fileTime = attemptTime ? null : entryTimestamp(contexts, "file");
  const chosenTime = attemptTime || fileTime;
  const semanticTitles = uniqueValues(contexts.map((context) => context.semanticTitle));
  const semanticBindings = uniqueValues(contexts.map((context) => context.semanticBinding));
  const owners = uniqueValues(contexts.map((context) => context.ownerKey));
  const models = uniqueValues(contexts.map((context) => context.model));
  const ambiguous = contexts.some((context) => context.ambiguous)
    || semanticTitles.length > 1
    || semanticBindings.length > 1
    || owners.length > 1
    || models.length > 1;
  const fallbackTitle = contexts.find((context) => context.title)?.title || null;
  return {
    id,
    sha256: contexts[0].media.sha256,
    bytes: contexts[0].media.bytes,
    contexts,
    title: ambiguous ? null : semanticTitles.length === 1 ? semanticTitles[0] : fallbackTitle,
    model: models.length === 1 ? models[0] : null,
    startedAt: chosenTime?.startedAt || null,
    timeKind: chosenTime?.timeKind || null,
    url: contexts.find((context) => context.url)?.url || null,
    available: contexts.some((context) => Boolean(context.url)),
    ambiguous,
    versionKeys: uniqueValues(contexts.map((context) => context.versionKey)),
  };
}

/** Build exact-content library entries from strict Runs details and the external catalog. */
export function buildLibraryEntries(details, externalCatalog) {
  const byIdentity = new Map();
  const canonical = runContexts(details);
  for (const context of [...canonical, ...externalContexts(externalCatalog, canonical)]) {
    const identity = `${context.media.sha256}:${context.media.bytes}`;
    const current = byIdentity.get(identity) || [];
    current.push(context);
    byIdentity.set(identity, current);
  }
  return [...byIdentity.entries()]
    .map(([id, contexts]) => toEntry(id, contexts))
    .sort((left, right) => (
      (timestamp(right.startedAt) ?? Number.NEGATIVE_INFINITY) - (timestamp(left.startedAt) ?? Number.NEGATIVE_INFINITY)
      || left.id.localeCompare(right.id)
    ));
}

function matchesQuery(entry, query) {
  const needle = String(query || "").trim().toLocaleLowerCase();
  if (!needle) return true;
  return entry.contexts.some((context) => [
    context.title,
    context.workspace,
    context.media?.relative_path,
    context.attempt?.target_shot_id,
    context.attempt?.shot_id,
    context.model,
    context.fileName,
  ].some((value) => String(value || "").toLocaleLowerCase().includes(needle)));
}

/** Filter the unified list; `linked` evidence includes canonical Runs bindings only. */
export function filterLibraryEntries(entries, {
  query = "",
  source = "all",
  model = "all",
  availability = "all",
  evidence = "all",
} = {}) {
  return (Array.isArray(entries) ? entries : []).filter((entry) => (
    matchesQuery(entry, query)
    && (source === "all" || entry.contexts.some((context) => context.sourceId === source))
    && (model === "all" || entry.contexts.some((context) => context.model === model))
    && (availability === "all" || (availability === "available" ? entry.available : availability === "unavailable" ? !entry.available : true))
    && (evidence === "all" || entry.contexts.some((context) => (
      context.sourceId === "runs" ? evidence === "linked" : groupMatchesEvidenceFilter(context.group, evidence)
    )))
  ));
}

export function libraryLifecycle(attempt) {
  const status = valueOrNull(attempt?.status) || "未标注";
  const phase = valueOrNull(attempt?.phase);
  if (status === "running" && phase === "validate") return "等待验证（running / validate）";
  return phase ? `${status} / ${phase}` : status;
}

export function selectLibraryEntry(entries, currentId, followLatest) {
  if (!followLatest) return currentId || null;
  return Array.isArray(entries) && entries.length ? entries[0].id : currentId || null;
}

/**
 * Map versionKey to `{ entries, contexts }`, where contexts contain `{ entry, context }`.
 * Keys are only emitted for strict Runs project/shot snapshot bindings.
 */
export function versionGroups(entries) {
  const groups = new Map();
  for (const entry of Array.isArray(entries) ? entries : []) {
    for (const context of entry.contexts || []) {
      if (!context.versionKey) continue;
      const group = groups.get(context.versionKey) || { entries: [], contexts: [] };
      if (!group.entries.includes(entry)) group.entries.push(entry);
      group.contexts.push({ entry, context });
      groups.set(context.versionKey, group);
    }
  }
  return groups;
}
