// Disposable exact-byte browser previews. At most two decoders and 60 JPEGs.
const cache = new Map();
const queue = [];
let active = 0;

export async function classifyPlaybackFailure(code, url, signal, request = fetch) {
  if (signal.aborted || code === 1) return null;
  try {
    const response = await request(url, { method: "HEAD", cache: "no-store", signal });
    if (signal.aborted) return null;
    if (response.status === 404 || response.status === 410) return "unavailable";
    return response.ok && (code === 3 || code === 4) ? "decode" : "network";
  } catch { return signal.aborted ? null : "network"; }
}

export function playbackFailureLabel(kind) {
  return kind === "decode" ? "当前浏览器无法解码此视频" : kind === "network" ? "播放请求失败，请刷新后重试" : "";
}

function drain() {
  while (active < 2 && queue.length) {
    const task = queue.shift();
    if (task.signal.aborted) { task.resolve(null); continue; }
    active += 1;
    decode(task).then(task.resolve).finally(() => { active -= 1; drain(); });
  }
}

function decode({ entry, signal }) {
  return new Promise((resolve) => {
    const video = document.createElement("video");
    let done = false;
    const finish = (result) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      signal.removeEventListener("abort", abort);
      video.onloadeddata = null;
      video.onerror = null;
      video.pause();
      video.removeAttribute("src");
      video.load();
      if (result && !signal.aborted) {
        cache.set(entry.id, result);
        while (cache.size > 60) cache.delete(cache.keys().next().value);
      }
      resolve(result);
    };
    const abort = () => finish(null);
    const timer = setTimeout(() => finish({ failed: true }), 12000);
    signal.addEventListener("abort", abort, { once: true });
    video.muted = true;
    video.preload = "auto";
    video.onerror = () => finish({ failed: true });
    video.onloadeddata = () => {
      const measurement = {
        duration: Number.isFinite(video.duration) ? video.duration : null,
        width: video.videoWidth,
        height: video.videoHeight,
      };
      try {
        const canvas = document.createElement("canvas");
        canvas.width = 360;
        canvas.height = Math.max(1, Math.round(360 * video.videoHeight / video.videoWidth));
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        finish({ ...measurement, poster: canvas.toDataURL("image/jpeg", 0.75) });
      } catch { finish({ ...measurement, failed: true }); }
    };
    video.src = entry.url;
    video.load();
  });
}

export function requestLibraryPreview(entry, signal) {
  if (signal.aborted || !entry.url) return Promise.resolve(null);
  if (cache.has(entry.id)) return Promise.resolve(cache.get(entry.id));
  return new Promise((resolve) => { queue.push({ entry, signal, resolve }); drain(); });
}

export function keepOneAudio(media, root) {
  if (media.muted || media.volume === 0) return;
  root?.querySelectorAll("video").forEach((other) => {
    if (other !== media) other.muted = true;
  });
}
