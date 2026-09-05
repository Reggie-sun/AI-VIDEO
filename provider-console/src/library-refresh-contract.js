function sourceIds(values) {
  return [...new Set((Array.isArray(values) ? values : [])
    .filter((value) => typeof value === "string" && value.length > 0))];
}

export function libraryLiveStatus({
  connectionState = "connecting",
  watchedSources = [],
  expectedSources = [],
  selectedSource = "all",
  refreshFailed = false,
} = {}) {
  if (connectionState === "reconnecting") return "reconnecting";
  if (refreshFailed) return "stale";
  if (connectionState === "unavailable") return "unavailable";
  if (connectionState !== "connected") return "connecting";

  const watched = new Set(sourceIds(watchedSources));
  const expected = selectedSource === "all"
    ? sourceIds(expectedSources)
    : sourceIds([selectedSource]);
  if (!expected.length) return "unavailable";
  const covered = expected.filter((source) => watched.has(source)).length;
  if (covered === expected.length) return "live";
  return covered > 0 ? "partial" : "unavailable";
}
