const RUNS_WORKSPACE_PREFIX = "runs-workspace:";

export function videoSourceSelectionValue(selectedSource) {
  return selectedSource || "all";
}

export function resolveVideoSourceSelection(value) {
  if (String(value).startsWith(RUNS_WORKSPACE_PREFIX)) return { sourceId: "runs", workspace: null };
  return { sourceId: value || "all", workspace: null };
}

export function videoSourceIsRefreshing(selectedSource, runsLoading, externalLoading) {
  if (selectedSource === "runs") return Boolean(runsLoading);
  if (selectedSource === "all") return Boolean(runsLoading || externalLoading);
  return Boolean(externalLoading);
}
