export function createWorkspaceSelectionGuard() {
  let epoch = 0;
  return {
    beginSelection() {
      epoch += 1;
      return epoch;
    },
    snapshot() {
      return epoch;
    },
    canCommit(token) {
      return token === epoch;
    },
  };
}

export function createLatestRequestGuard() {
  let epoch = 0;
  return {
    beginRequest() {
      epoch += 1;
      return epoch;
    },
    snapshot() {
      return epoch;
    },
    canCommit(token) {
      return token === epoch;
    },
  };
}

function timestampOf(value) {
  const parsed = Date.parse(value || "");
  return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY;
}

export function sortAttemptsNewest(attempts = []) {
  return [...attempts]
    .map((item, index) => ({
      item,
      index,
      timestamp: timestampOf(item?.started_at || item?.finished_at),
    }))
    .sort((left, right) => right.timestamp - left.timestamp || right.index - left.index)
    .map(({ item }) => item);
}

export function sortVideoWorkspacesNewest(items = []) {
  return [...items]
    .map((item, index) => ({ item, index, timestamp: timestampOf(item?.latest_video_attempt_at) }))
    .filter(({ timestamp }) => Number.isFinite(timestamp))
    .sort((left, right) => right.timestamp - left.timestamp || left.index - right.index)
    .map(({ item }) => item);
}

export function refreshOrder({ items = [], currentKey = "", followLatest = true, keyOf = (item) => item } = {}) {
  const values = [...items];
  if (followLatest || !currentKey) return values;
  const currentIndex = values.findIndex((item) => keyOf(item) === currentKey);
  if (currentIndex <= 0) return values;
  return [values[currentIndex], ...values.slice(0, currentIndex), ...values.slice(currentIndex + 1)];
}

export function refreshSelectionKey({ items = [], currentKey = "", followLatest = true, keyOf = (item) => item } = {}) {
  if (!items.length) return "";
  if (!followLatest && items.some((item) => keyOf(item) === currentKey)) return currentKey;
  return keyOf(items[0]);
}

export function selectionTracksNewest({ items = [], selectedKey = "", keyOf = (item) => item } = {}) {
  if (!selectedKey) return true;
  return items.length > 0 && keyOf(items[0]) === selectedKey;
}

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
