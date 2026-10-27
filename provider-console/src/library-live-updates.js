import { useEffect, useState } from "react";

const EMPTY_CONNECTION = { state: "connecting", expectedSources: [], watchedSources: [] };

export function connectLibraryLiveUpdates({ refreshRuns, refreshExternal, refreshReferences = () => {}, setConnection, EventSourceClass = globalThis.EventSource }) {
  if (typeof EventSourceClass !== "function") {
    setConnection({ state: "unavailable", expectedSources: [], watchedSources: [] });
    return undefined;
  }

  setConnection(EMPTY_CONNECTION);
  const events = new EventSourceClass("/api/library-events");
  events.onopen = () => setConnection((current) => ({ ...current, state: "connecting" }));
  events.onerror = () => setConnection((current) => ({ ...current, state: "reconnecting" }));
  const sourceStatus = (message) => {
    let event;
    try { event = JSON.parse(message.data); } catch {
      setConnection({ state: "unavailable", expectedSources: [], watchedSources: [] });
      return;
    }
    setConnection({
      state: "connected",
      expectedSources: Array.isArray(event?.expected_sources) ? event.expected_sources : (event?.sources || []),
      watchedSources: Array.isArray(event?.sources) ? event.sources : [],
    });
    // The feed has no event replay: reconcile changes missed before initial
    // subscription or while the browser was disconnected.
    if (message.type === "ready") {
      refreshRuns();
      refreshExternal();
      refreshReferences();
    }
  };
  const update = (message) => {
    let event;
    try { event = JSON.parse(message.data); } catch { return; }
    const sources = Array.isArray(event?.sources) ? event.sources : [];
    if (sources.includes("runs")) refreshRuns();
    if (sources.includes("references")) refreshReferences();
    if (sources.some((source) => source !== "runs" && source !== "references")) refreshExternal();
  };
  events.addEventListener("ready", sourceStatus);
  events.addEventListener("source-status", sourceStatus);
  events.addEventListener("catalog-change", update);
  return () => {
    events.removeEventListener("ready", sourceStatus);
    events.removeEventListener("source-status", sourceStatus);
    events.removeEventListener("catalog-change", update);
    events.close();
  };
}

export function useLibraryLiveUpdates({ refreshRuns, refreshExternal, refreshReferences }) {
  const [connection, setConnection] = useState(EMPTY_CONNECTION);
  useEffect(() => connectLibraryLiveUpdates({ refreshRuns, refreshExternal, refreshReferences, setConnection }), [refreshExternal, refreshRuns, refreshReferences]);
  return connection;
}
