import { useEffect, useState } from "react";

const EMPTY_CONNECTION = { state: "connecting", expectedSources: [], watchedSources: [] };

export function useLibraryLiveUpdates({ refreshRuns, refreshExternal }) {
  const [connection, setConnection] = useState(EMPTY_CONNECTION);

  useEffect(() => {
    if (typeof EventSource !== "function") {
      setConnection({ state: "unavailable", expectedSources: [], watchedSources: [] });
      return undefined;
    }

    setConnection(EMPTY_CONNECTION);
    const events = new EventSource("/api/library-events");
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
    };
    const update = (message) => {
      let event;
      try { event = JSON.parse(message.data); } catch { return; }
      const sources = Array.isArray(event?.sources) ? event.sources : [];
      if (sources.includes("runs")) refreshRuns();
      if (sources.some((source) => source !== "runs")) refreshExternal();
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
  }, [refreshExternal, refreshRuns]);

  return connection;
}
