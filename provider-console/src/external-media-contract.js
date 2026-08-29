const SUCCESS_STATES = new Set(["success", "succeeded", "completed", "complete", "fetched", "output_recorded"]);
const FAILURE_STATES = new Set(["failed", "failure", "error", "blocked", "cancelled", "canceled"]);

export function externalStatus(group) {
  if (group?.association_ambiguity === true) {
    return {
      raw: "AMBIGUOUS_EXPERIMENT_EVIDENCE",
      label: "证据关联冲突",
      badge: "证据冲突",
      tone: "blocked",
      evaluated: false,
      evidence_state: "conflict",
      ambiguous: true,
    };
  }
  if ((group?.run_bindings || []).length > 0 && !preferredRunBinding(group)) {
    return {
      raw: "AMBIGUOUS_RUNS_CONTEXT",
      label: "同一 exact media 关联到不同 Runs 语义",
      badge: "Runs 关联冲突",
      tone: "blocked",
      evaluated: false,
      evidence_state: "conflict",
      ambiguous: true,
    };
  }
  const reported = group?.reported_status;
  const raw = String(reported ?? "NOT_EVALUATED").trim();
  const normalized = raw.toLowerCase();
  if (reported === true || SUCCESS_STATES.has(normalized)) {
    return { raw, label: `外部报告：${raw}`, badge: raw, tone: "ready", evaluated: true, evidence_state: "linked" };
  }
  if (reported === false || FAILURE_STATES.has(normalized)) {
    return { raw, label: `外部报告：${raw}`, badge: raw, tone: "blocked", evaluated: true, evidence_state: "linked" };
  }
  if (reported !== undefined && reported !== null && normalized && normalized !== "not_evaluated") {
    return { raw, label: `外部报告：${raw}`, badge: raw, tone: "gated", evaluated: true, evidence_state: "linked" };
  }
  if ((group?.run_bindings || []).length > 0) {
    return {
      raw: "NOT_EVALUATED",
      label: "Runs exact SHA 已关联；生成状态未评估",
      badge: "Runs 已关联",
      tone: "interrupted",
      evaluated: false,
      evidence_state: "linked",
    };
  }
  if (group?.metadata_status === "bound" && (group?.evidence_refs || []).length > 0) {
    return {
      raw: "NOT_EVALUATED",
      label: "Prompt、Shot 或类型已与 exact bytes 绑定；生成状态未评估",
      badge: "旁证已关联",
      tone: "interrupted",
      evaluated: false,
      evidence_state: "linked",
    };
  }
  if (group?.runs_context_complete === false) {
    return {
      raw: "INCOMPLETE_RUNS_CONTEXT",
      label: "Runs 关联证据尚不完整，无法证明该视频没有绑定",
      badge: "Runs 待恢复",
      tone: "gated",
      evaluated: false,
      evidence_state: "incomplete",
    };
  }
  if ((group?.evidence_refs || []).length > 0) {
    return {
      raw: "UNPARSED_BOUND_EVIDENCE",
      label: "存在 exact-bound 旁证，但当前 schema 尚未支持",
      badge: "旁证待解析",
      tone: "gated",
      evaluated: false,
      evidence_state: "unparsed",
    };
  }
  return {
    raw: "NOT_EVALUATED",
    label: "没有与 exact bytes 绑定的证据",
    badge: "无绑定证据",
    tone: "unknown",
    evaluated: false,
    evidence_state: "unbound",
  };
}

export function externalEvidenceState(group) {
  return externalStatus(group).evidence_state;
}

export function groupMatchesEvidenceFilter(group, filter) {
  return !filter || filter === "all" || externalEvidenceState(group) === filter;
}

export function externalEvidenceFilterOptions(groups) {
  const candidates = Array.isArray(groups) ? groups : [];
  const definitions = [
    ["all", "全部证据状态"],
    ["linked", "已关联"],
    ["incomplete", "Runs 待恢复"],
    ["unparsed", "旁证待解析"],
    ["unbound", "无绑定证据"],
    ["conflict", "证据冲突"],
  ];
  return definitions
    .map(([id, label]) => ({
      id,
      label,
      count: id === "all" ? candidates.length : candidates.filter((group) => externalEvidenceState(group) === id).length,
    }))
    .filter((option) => option.id !== "conflict" || option.count > 0);
}

export function runsMediaContextNotice(index) {
  const boundary = index?.boundary;
  if (boundary?.complete === true) return "";
  const failed = index?.summary?.failed_workspace_count ?? "部分";
  if (boundary?.identity_coverage_complete === true) {
    const recovered = index?.summary?.recovered_workspace_count ?? 0;
    return `Runs context 已按 exact media identity 隔离：${recovered} 个 workspace 恢复了封存视频证据，${failed} 个 workspace 无法完整重开；未命中 unresolved media 的视频可判定为无绑定。`;
  }
  return `Runs context 部分可用：${failed} 个 workspace 无法严格重开；仅展示已确认的 exact match。`;
}

export function attachRunsMediaIndex(catalog, index) {
  if (!catalog || typeof catalog !== "object") return catalog;
  const boundary = index?.boundary;
  const indexIsTrusted = boundary?.read_only === true
    && boundary?.association === "exact_sha256_and_bytes"
    && boundary?.lifecycle_projection === false
    && typeof boundary?.complete === "boolean";
  const bindings = indexIsTrusted && Array.isArray(index?.bindings) ? index.bindings : [];
  const unresolvedMedia = Array.isArray(index?.unresolved_media) ? index.unresolved_media : null;
  const identityCoverageIsTrusted = indexIsTrusted
    && boundary?.identity_coverage_complete === true
    && unresolvedMedia !== null
    && unresolvedMedia.every((identity) => (
      /^[0-9a-f]{64}$/.test(identity?.sha256 || "")
      && Number.isSafeInteger(identity?.bytes)
      && identity.bytes >= 0
    ));
  const byIdentity = new Map();
  for (const binding of bindings) {
    if (!/^[0-9a-f]{64}$/.test(binding?.sha256 || "") || !Number.isSafeInteger(binding?.bytes) || binding.bytes < 0) continue;
    const identity = `${binding.sha256}:${binding.bytes}`;
    const existing = byIdentity.get(identity) || [];
    existing.push(binding);
    byIdentity.set(identity, existing);
  }
  const unresolvedIdentities = new Set();
  if (identityCoverageIsTrusted) {
    for (const identity of unresolvedMedia) {
      unresolvedIdentities.add(`${identity.sha256}:${identity.bytes}`);
    }
  }
  return {
    ...catalog,
    groups: (catalog.groups || []).map((group) => {
      const identity = `${group.sha256}:${group.bytes}`;
      return {
        ...group,
        run_bindings: byIdentity.get(identity) || [],
        runs_context_complete: indexIsTrusted && (
          boundary.complete === true
          || (identityCoverageIsTrusted && !unresolvedIdentities.has(identity))
        ),
      };
    }),
    runs_media_context: indexIsTrusted ? boundary : null,
  };
}

function runBindingSemanticKey(binding) {
  return JSON.stringify([
    binding?.target_shot_id || null,
    binding?.target_shot_revision ?? null,
    binding?.target_shot_content_hash || null,
    binding?.generation_type || null,
    binding?.prompt_text || null,
    binding?.shot_snapshot_status || null,
    binding?.shot_snapshot?.content_hash || null,
  ]);
}

export function preferredRunBinding(group) {
  const bindings = Array.isArray(group?.run_bindings) ? group.run_bindings : [];
  if (!bindings.length) return null;
  return new Set(bindings.map(runBindingSemanticKey)).size === 1 ? bindings[0] : null;
}

export function externalDisplayMetadata(group) {
  const runBinding = preferredRunBinding(group);
  return {
    shot_id: group?.shot_id ?? runBinding?.target_shot_id ?? null,
    shot_type: group?.shot_type ?? null,
    generation_type: group?.generation_type ?? runBinding?.generation_type ?? null,
    prompt_text: group?.prompt_text ?? runBinding?.prompt_text ?? null,
    run_binding: runBinding,
    source: group?.shot_id || group?.generation_type || group?.prompt_text ? "external_evidence" : runBinding ? "runs_exact_sha" : "none",
  };
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
  const metadata = externalDisplayMetadata(group);
  if (metadata.run_binding) {
    const binding = metadata.run_binding;
    const snapshot = binding.shot_snapshot_status === "verified" ? binding.shot_snapshot : null;
    return [{
      ...(snapshot || { shot_id: binding.target_shot_id }),
      prompt_text: binding.prompt_text,
      generation_type: binding.generation_type,
      evidence_source: "runs_exact_sha",
      snapshot_available: Boolean(snapshot),
    }];
  }
  if (!metadata.shot_id) return [];
  return [{
    shot_id: metadata.shot_id,
    prompt_text: metadata.prompt_text,
    shot_type: group?.shot_type,
    generation_type: metadata.generation_type,
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
  const runsValues = (group?.run_bindings || []).flatMap((binding) => [
    binding?.workspace,
    binding?.attempt_id,
    binding?.target_shot_id,
    binding?.generation_type,
    binding?.prompt_text,
    binding?.shot_snapshot?.intent,
    binding?.shot_snapshot?.dialogue,
    binding?.shot_snapshot?.narration,
    binding?.shot_snapshot?.visual_strategy,
    ...(binding?.shot_snapshot?.continuity_constraints || []),
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
    ...runsValues,
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
