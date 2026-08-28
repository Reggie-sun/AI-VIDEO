const RUNS_WORKSPACE_PREFIX = "runs-workspace:";

export function workspaceSourceValue(workspace) {
  return `${RUNS_WORKSPACE_PREFIX}${workspace || ""}`;
}

export function videoSourceSelectionValue(selectedSource, workspace) {
  return selectedSource === "runs" ? workspaceSourceValue(workspace) : (selectedSource || "all");
}

export function resolveVideoSourceSelection(value, runsCatalog) {
  const workspace = (Array.isArray(runsCatalog) ? runsCatalog : []).find(
    (item) => workspaceSourceValue(item?.workspace) === value,
  )?.workspace;
  if (workspace) return { sourceId: "runs", workspace };
  if (String(value).startsWith(RUNS_WORKSPACE_PREFIX)) return { sourceId: "runs", workspace: null };
  return { sourceId: value, workspace: null };
}

export function videoSourceIsRefreshing(selectedSource, runsLoading, externalLoading) {
  if (selectedSource === "runs") return Boolean(runsLoading);
  if (selectedSource === "all") return Boolean(runsLoading || externalLoading);
  return Boolean(externalLoading);
}
