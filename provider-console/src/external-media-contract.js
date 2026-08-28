const SUCCESS_STATES = new Set(["success", "succeeded", "completed", "complete", "fetched", "output_recorded"]);
const FAILURE_STATES = new Set(["failed", "failure", "error", "blocked", "cancelled", "canceled"]);

export function externalStatus(group) {
  if (group?.association_ambiguity === true) {
    return {
      raw: "AMBIGUOUS_EXPERIMENT_EVIDENCE",
      label: "证据关联冲突",
      tone: "blocked",
      evaluated: false,
      ambiguous: true,
    };
  }
  const reported = group?.reported_status;
  const raw = String(reported ?? "NOT_EVALUATED").trim();
  const normalized = raw.toLowerCase();
  if (reported === true || SUCCESS_STATES.has(normalized)) {
    return { raw, label: `外部报告：${raw}`, tone: "ready", evaluated: true };
  }
  if (reported === false || FAILURE_STATES.has(normalized)) {
    return { raw, label: `外部报告：${raw}`, tone: "blocked", evaluated: true };
  }
  if (reported !== undefined && reported !== null && normalized && normalized !== "not_evaluated") {
    return { raw, label: `外部报告：${raw}`, tone: "gated", evaluated: true };
  }
  return { raw: "NOT_EVALUATED", label: "状态未评估", tone: "unknown", evaluated: false };
}

export function preferredExternalLocation(group) {
  const locations = Array.isArray(group?.locations) ? group.locations : [];
  if (group?.preferred_location?.token) return group.preferred_location;
  if (group?.preview_token) {
    return locations.find((item) => item?.token === group.preview_token) || { token: group.preview_token };
  }
  return locations.find((item) => item?.token) || null;
}

export function sourceLabel(source, fallback) {
  return source?.label || fallback || source?.id || "未知来源";
}

export function externalMediaUrl(group) {
  const token = preferredExternalLocation(group)?.token;
  return token ? `/api/external-media/media/${encodeURIComponent(token)}` : null;
}

export function externalReferenceUrl(reference) {
  const token = typeof reference?.token === "string" && /^[A-Za-z0-9_-]{6,128}$/.test(reference.token)
    ? reference.token
    : null;
  return token ? `/api/external-media/media/${encodeURIComponent(token)}` : null;
}

function evidencePriority(group) {
  if ((group?.shot_evidence || []).length > 0) return 5;
  if ((group?.composition?.ordered_shots || []).length > 0) return 4;
  if (group?.shot_id && group?.prompt_text) return 3;
  if (group?.shot_id || group?.prompt_text || group?.shot_type || group?.generation_type || group?.reported_status) return 2;
  return 1;
}

export function preferredExternalGroup(groups) {
  const candidates = Array.isArray(groups) ? groups : [];
  if (!candidates.length) return null;
  return candidates.reduce((preferred, group) => (
    evidencePriority(group) > evidencePriority(preferred) ? group : preferred
  ));
}

export function externalStoryboardShots(group) {
  const exactShots = group?.shot_evidence;
  if (Array.isArray(exactShots) && exactShots.length > 0) return exactShots;
  const compositionShots = group?.composition?.ordered_shots;
  if (Array.isArray(compositionShots) && compositionShots.length > 0) return compositionShots;
  if (!group?.shot_id) return [];
  return [{
    shot_id: group.shot_id,
    prompt_text: group.prompt_text,
    shot_type: group.shot_type,
    generation_type: group.generation_type,
    reported_status: group.reported_status,
  }];
}

export function groupMatchesSource(group, sourceId) {
  if (!sourceId || sourceId === "all") return true;
  return (group?.locations || []).some((item) => item?.source_id === sourceId);
}

export function externalSourceOptions(catalog) {
  const groups = Array.isArray(catalog?.groups) ? catalog.groups : [];
  const sources = Array.isArray(catalog?.sources) ? catalog.sources : [];
  return [
    { id: "all", label: "全部外部来源", count: groups.length, disabled: false },
    ...sources.map((source) => ({
      id: source.id,
      label: source.label || source.id || "未知来源",
      count: groups.filter((group) => groupMatchesSource(group, source.id)).length,
      disabled: source.status !== "available",
    })),
  ];
}

export function groupMatchesQuery(group, query) {
  const needle = String(query || "").trim().toLocaleLowerCase();
  if (!needle) return true;
  const shotEvidenceValues = (group?.shot_evidence || []).flatMap((shot) => [
    shot?.entity_kind,
    shot?.shot_id,
    shot?.intent,
    shot?.dialogue,
    shot?.narration,
    shot?.visual_strategy,
    shot?.prompt_text,
    shot?.generation_type,
    shot?.provider_kind,
    shot?.provider_name,
    shot?.model_id,
    shot?.generation_result,
    shot?.technical_gate,
    shot?.human_verdict,
    shot?.reference_binding_status,
    shot?.reference_binding_reason,
    ...(shot?.continuity_constraints || []),
    ...(shot?.reference_inputs || []).flatMap((reference) => [reference?.role, reference?.asset_id, reference?.sha256]),
    ...(shot?.findings || []).flatMap((finding) => [finding?.requirement_id, finding?.verdict, finding?.evidence, finding?.reason]),
  ]);
  const compositionValues = (group?.composition?.ordered_shots || []).flatMap((shot) => [
    shot?.shot_id,
    shot?.shot_type,
    shot?.purpose,
    shot?.talent_action,
    shot?.product_state,
    shot?.camera_intent,
    shot?.visual_strategy_need,
    shot?.prompt_text,
    shot?.reported_status,
    ...(shot?.copy || []),
    ...(shot?.dialogue || []),
  ]);
  const values = [
    externalGroupTitle(group),
    group?.shot_id,
    group?.shot_type,
    group?.generation_type,
    group?.reported_status,
    group?.prompt_text,
    ...shotEvidenceValues,
    ...compositionValues,
    ...(group?.locations || []).flatMap((item) => [item?.relative_path, item?.source_label, item?.source_id]),
  ];
  return values.some((value) => String(value || "").toLocaleLowerCase().includes(needle));
}

export function externalGroupTitle(group) {
  const location = preferredExternalLocation(group);
  return location?.file_name || location?.relative_path?.split("/").at(-1) || `视频 ${String(group?.sha256 || "").slice(0, 8)}`;
}

export async function readExternalCatalogResponse(response) {
  let body = null;
  try { body = await response?.json(); } catch { /* Sites/static may return a non-JSON 404 body. */ }
  if (!response?.ok || !body || typeof body !== "object" || Array.isArray(body) || body.error) {
    const message = typeof body?.error?.message === "string" && body.error.message.trim()
      ? body.error.message
      : "外部媒体数据源不可用。";
    throw new Error(message);
  }
  return body;
}
