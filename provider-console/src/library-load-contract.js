// Keep browsing and playback independent of the size of the Runs catalog.
export const LIBRARY_WORKSPACE_PAGE_SIZE = 6;

export function libraryWorkspaceBatch(workspaces, limit, requested) {
  return workspaces.filter((item, index) => index < limit || requested.has(item.workspace));
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
