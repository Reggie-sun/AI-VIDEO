import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { attachRunsMediaIndex, readExternalCatalogResponse, runsMediaContextNotice } from "./external-media-contract.js";
import { useLibraryLiveUpdates } from "./library-live-updates.js";

async function readJson(url, signal) {
  const response = await fetch(url, { cache: "no-store", signal });
  const body = await response.json();
  if (!response.ok || body?.error || body?.status === "invalid") {
    throw new Error([body?.error?.message || "本地数据源不可用", body?.error?.code].filter(Boolean).join(" · "));
  }
  return body;
}

export function useLibraryData() {
  const [catalog, setCatalog] = useState({ workspaces: [] });
  const [details, setDetails] = useState({});
  const [external, setExternal] = useState(null);
  const [runsLoading, setRunsLoading] = useState(true);
  const [externalLoading, setExternalLoading] = useState(true);
  const [runsError, setRunsError] = useState("");
  const [externalError, setExternalError] = useState("");
  const [mediaIndex, setMediaIndex] = useState(null);
  const [indexLoading, setIndexLoading] = useState(true);
  const [indexNotice, setIndexNotice] = useState("");
  const indexRequest = useRef(null);
  const runsRequest = useRef(null);
  const externalRequest = useRef(null);
  const runsInFlight = useRef(false);
  const runsQueued = useRef(false);

  const refreshIndex = useCallback(async () => {
    indexRequest.current?.abort();
    const controller = new AbortController();
    indexRequest.current = controller;
    setIndexLoading(true);
    setMediaIndex(null);
    try {
      const body = await readJson("/api/runs/media-context-index", controller.signal);
      if (!controller.signal.aborted) { setMediaIndex(body); setIndexNotice(runsMediaContextNotice(body)); }
    } catch (error) {
      if (!controller.signal.aborted) setIndexNotice(error.message);
    } finally { if (!controller.signal.aborted) setIndexLoading(false); }
  }, []);

  const refreshRuns = useCallback(async () => {
    if (runsInFlight.current) { runsQueued.current = true; return; }
    runsInFlight.current = true;
    const controller = new AbortController();
    runsRequest.current = controller;
    setRunsLoading(true);
    setRunsError("");
    try {
      do {
        runsQueued.current = false;
        const body = await readJson("/api/runs", controller.signal);
        if (controller.signal.aborted) return;
        setCatalog(body);
        const workspaces = body.workspaces || [];
        const keys = new Set(workspaces.map((item) => item.workspace));
        setDetails((current) => Object.fromEntries(Object.entries(current).filter(([key]) => keys.has(key)).map(([key, value]) => [key, { ...value, refreshing: true }])));
        const pending = [...workspaces].sort((a, b) => (Date.parse(b.latest_video_attempt_at) || 0) - (Date.parse(a.latest_video_attempt_at) || 0));
        const worker = async () => {
          while (pending.length && !controller.signal.aborted) {
            const item = pending.shift();
            let result;
            try {
              result = { detail: await readJson(`/api/runs/detail?workspace=${encodeURIComponent(item.workspace)}`, controller.signal) };
            } catch (error) { result = { error: error.message }; }
            if (!controller.signal.aborted) setDetails((current) => ({ ...current, [item.workspace]: result }));
          }
        };
        await Promise.all(Array.from({ length: 3 }, worker));
      } while (runsQueued.current && !controller.signal.aborted);
    } catch (error) {
      if (!controller.signal.aborted) setRunsError(error.message);
    } finally {
      if (runsRequest.current === controller) {
        runsInFlight.current = false;
        if (!controller.signal.aborted) setRunsLoading(false);
      }
    }
  }, []);

  const refreshExternal = useCallback(async ({ force = false } = {}) => {
    externalRequest.current?.abort();
    const controller = new AbortController();
    externalRequest.current = controller;
    setExternalLoading(true);
    setExternalError("");
    try {
      const response = await fetch(force ? "/api/external-media?refresh=1" : "/api/external-media", { cache: "no-store", signal: controller.signal });
      const body = await readExternalCatalogResponse(response);
      if (!controller.signal.aborted) setExternal(body);
    } catch (error) {
      if (!controller.signal.aborted) setExternalError(error.message);
    } finally {
      if (!controller.signal.aborted) setExternalLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshRuns();
    refreshExternal();
    refreshIndex();
    return () => {
      runsRequest.current?.abort();
      runsInFlight.current = false;
      externalRequest.current?.abort();
      indexRequest.current?.abort();
    };
  }, [refreshRuns, refreshExternal, refreshIndex]);
  const refreshRunsAndIndex = useCallback(() => Promise.all([refreshRuns(), refreshIndex()]), [refreshRuns, refreshIndex]);
  const connection = useLibraryLiveUpdates({ refreshRuns: refreshRunsAndIndex, refreshExternal });
  const loaded = useMemo(() => Object.values(details).flatMap((result) => result.detail ? [result.detail] : []), [details]);
  const enrichedExternal = useMemo(() => attachRunsMediaIndex(external, mediaIndex), [external, mediaIndex]);
  return { catalog, details, loaded, external: enrichedExternal, runsLoading, externalLoading, runsError, externalError, indexLoading, indexNotice, connection, refreshRuns: refreshRunsAndIndex, refreshExternal };
}
