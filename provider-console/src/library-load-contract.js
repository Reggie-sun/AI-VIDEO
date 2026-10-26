// Keep browsing and playback independent of the size of the Runs catalog.
export const LIBRARY_WORKSPACE_PAGE_SIZE = 6;

export function libraryTargetFromSearch(search = "") {
  const params = new URLSearchParams(search);
  const workspace = params.get("workspace");
  const safe = typeof workspace === "string" && workspace.length <= 1024
    && /^[A-Za-z0-9_.\/-]+$/.test(workspace)
    && workspace.split("/").every((part) => part && part !== "." && part !== "..")
    && /\/(project\.yaml|manifest\.json)$/.test(workspace);
  const sha256 = params.get("media");
  return { workspace: safe ? workspace : null, sha256: safe && /^[a-f0-9]{64}$/.test(sha256 || "") ? sha256 : null };
}

export function includeLibraryTarget(workspaces, target) {
  if (!target) return workspaces;
  const existing = workspaces.find((item) => item.workspace === target);
  return [existing || { workspace: target, requested: true }, ...workspaces.filter((item) => item.workspace !== target)];
}

export function libraryWorkspaceBatch(workspaces, limit, requested) {
  // Recent renders/authoring edits must not crowd generation out of the first
  // page. These hints only schedule strict detail reads, never supply UI truth.
  const recentAttempts = new Set(workspaces
    .filter((item) => Number.isFinite(Date.parse(item.latest_video_attempt_at)))
    .sort((a, b) => Date.parse(b.latest_video_attempt_at) - Date.parse(a.latest_video_attempt_at))
    .slice(0, LIBRARY_WORKSPACE_PAGE_SIZE).map((item) => item.workspace));
  return workspaces.filter((item, index) => index < limit || requested.has(item.workspace) || recentAttempts.has(item.workspace));
}

export async function loadLibraryWorkspaces(workspaces, signal, readJson, onResult) {
  const pending = [...workspaces];
  const worker = async () => {
    while (pending.length && !signal.aborted) {
      const item = pending.shift();
      let result;
      try {
        result = { detail: await readJson(`/api/runs/detail?workspace=${encodeURIComponent(item.workspace)}`, signal) };
      } catch (error) { result = { error: error.message }; }
      if (!signal.aborted) onResult(item.workspace, result);
    }
  };
  // SSE and external scans also use connections; leave room for actual media.
  await Promise.all(Array.from({ length: 2 }, worker));
}
