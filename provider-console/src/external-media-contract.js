const SUCCESS_STATES = new Set(["success", "succeeded", "completed", "complete", "fetched"]);
const FAILURE_STATES = new Set(["failed", "failure", "error", "blocked", "cancelled", "canceled"]);

export function externalStatus(group) {
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

export function externalMediaUrl(group) {
  const token = preferredExternalLocation(group)?.token;
  return token ? `/api/external-media/media/${encodeURIComponent(token)}` : null;
}

export function groupMatchesSource(group, sourceId) {
  if (!sourceId || sourceId === "all") return true;
  return (group?.locations || []).some((item) => item?.source_id === sourceId);
}

export function groupMatchesQuery(group, query) {
  const needle = String(query || "").trim().toLocaleLowerCase();
  if (!needle) return true;
  const values = [
    externalGroupTitle(group),
    group?.shot_id,
    group?.shot_type,
    group?.generation_type,
    group?.reported_status,
    group?.prompt_text,
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
