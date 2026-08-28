import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { open, realpath } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { catalogExternalMedia } from "./external-media.mjs";

const execFileAsync = promisify(execFile);
const JSON_HEADERS = { "Content-Type": "application/json; charset=utf-8" };

export class RunsApiError extends Error {
  constructor(status, code) {
    super(code);
    this.status = status;
    this.code = code;
  }
}

function send(res, status, body, headers = {}) {
  const payload = body === undefined ? Buffer.alloc(0) : Buffer.from(JSON.stringify(body));
  res.statusCode = status;
  res.setHeader("Cache-Control", "no-store");
  for (const [name, value] of Object.entries({ ...JSON_HEADERS, ...headers })) res.setHeader(name, value);
  res.setHeader("Content-Length", payload.length);
  res.end(payload);
}

function methodNotAllowed(res, allow) {
  send(res, 405, { error: { code: "METHOD_NOT_ALLOWED", message: "此接口不允许该请求方法。" } }, { Allow: allow });
}

function isSafeWorkspace(value) {
  if (!value || value.includes("\0") || value.includes("\\") || path.posix.isAbsolute(value)) return false;
  const segments = value.split("/");
  return segments.every((segment) => segment && segment !== "." && segment !== "..");
}

function isLoopbackRequest(req) {
  const address = req.socket?.remoteAddress;
  if (!address) return false;
  return address === "::1" || address.startsWith("127.") || address.startsWith("::ffff:127.");
}

function publicProjection(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  const { _media, ...safe } = value;
  return safe;
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function canonicalSha256(value) {
  return createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

function validateContinuityProjection(result) {
  const request = result?.review_request;
  const media = result?.media;
  if (!request || !media || typeof request !== "object" || typeof media !== "object") {
    throw new RunsApiError(503, "CONTINUITY_REVIEW_INVALID");
  }
  const sha = /^[0-9a-f]{64}$/;
  const identity = request.required_reviewer;
  const automatic = request.automatic_evaluator;
  const { content_hash: contentHash, ...semantic } = request;
  const expected = canonicalSha256({ schema: "human-continuity-review-request/1", ...semantic });
  if (
    !sha.test(contentHash || "")
    || contentHash !== expected
    || !sha.test(request.artifact_sha256 || "")
    || request.media_identity !== `sha256:${request.artifact_sha256}`
    || media.sha256 !== request.artifact_sha256
    || typeof media.token !== "string"
    || !/^[A-Za-z0-9_-]{6,128}$/.test(media.token)
    || !identity?.name?.trim() || !identity?.version?.trim()
    || !automatic?.name?.trim() || !automatic?.version?.trim()
  ) {
    throw new RunsApiError(503, "CONTINUITY_REVIEW_INVALID");
  }
  return result;
}

function continuityIdentityArgs() {
  const values = {
    "--automatic-evaluator-name": process.env.AI_VIDEO_CONTINUITY_AUTOMATIC_EVALUATOR_NAME,
    "--automatic-evaluator-version": process.env.AI_VIDEO_CONTINUITY_AUTOMATIC_EVALUATOR_VERSION,
    "--reviewer-name": process.env.AI_VIDEO_CONTINUITY_HUMAN_REVIEWER_NAME,
    "--reviewer-version": process.env.AI_VIDEO_CONTINUITY_HUMAN_REVIEWER_VERSION,
  };
  if (Object.values(values).some((value) => !value?.trim())) {
    throw new RunsApiError(503, "CONTINUITY_REVIEW_CONFIG_UNAVAILABLE");
  }
  return Object.entries(values).flatMap(([flag, value]) => [flag, value]);
}

function createPythonProjector(repoRoot) {
  const runsRoot = path.join(repoRoot, "runs");
  const python = process.env.AI_VIDEO_PYTHON || "python";
  return async (command, workspace, attemptId) => {
    const args = ["-m", "ai_video.provider_console", command, "--runs-root", runsRoot];
    if (workspace) args.push("--workspace", workspace);
    if (command === "continuity-review") {
      args.push("--attempt-id", attemptId, ...continuityIdentityArgs());
    }
    const env = {
      PATH: process.env.PATH,
      LANG: process.env.LANG || "C.UTF-8",
      LC_ALL: process.env.LC_ALL || "C.UTF-8",
      PYTHONPATH: path.join(repoRoot, "src"),
    };
    try {
      const { stdout } = await execFileAsync(python, args, { cwd: repoRoot, env, maxBuffer: 20 * 1024 * 1024 });
      return JSON.parse(stdout);
    } catch (cause) {
      let code = "RUNS_SOURCE_UNAVAILABLE";
      try { code = JSON.parse(cause?.stdout || "{}").error?.code || code; } catch { /* sanitized below */ }
      const status = code === "WORKSPACE_NOT_FOUND" ? 404 : code === "INVALID_WORKSPACE" ? 400 : code === "CONTINUITY_REVIEW_UNAVAILABLE" ? 409 : 503;
      throw new RunsApiError(status, code);
    }
  };
}

async function validatedMedia(entry, runsRoot) {
  if (!entry || typeof entry.source_path !== "string" || typeof entry.mime_type !== "string") return null;
  if (!/^(image|video)\//.test(entry.mime_type)) return null;
  const source = path.resolve(entry.source_path);
  const root = await realpath(runsRoot);
  if (source !== root && !source.startsWith(`${root}${path.sep}`)) return null;
  const file = await open(source, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat({ bigint: true }),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    if (!stat.isFile() || openedPath !== source || (openedPath !== root && !openedPath.startsWith(`${root}${path.sep}`))) return null;
    if (Number.isSafeInteger(entry.bytes) && BigInt(entry.bytes) !== stat.size) return null;
    if (entry.sha256 !== undefined) {
      if (!/^[0-9a-f]{64}$/.test(entry.sha256)) return null;
      const digest = createHash("sha256");
      let position = 0;
      while (position < Number(stat.size)) {
        const chunk = Buffer.alloc(Math.min(1024 * 1024, Number(stat.size) - position));
        const { bytesRead } = await file.read(chunk, 0, chunk.length, position);
        if (!bytesRead) return null;
        digest.update(chunk.subarray(0, bytesRead));
        position += bytesRead;
      }
      if (digest.digest("hex") !== entry.sha256) return null;
    }
    return {
      source,
      root,
      mimeType: entry.mime_type,
      size: Number(stat.size),
      identity: [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String),
    };
  } finally {
    await file.close();
  }
}

function parseRange(header, size) {
  if (!header) return null;
  const match = /^bytes=(\d*)-(\d*)$/.exec(header);
  if (!match || (!match[1] && !match[2])) return false;
  let start;
  let end;
  if (!match[1]) {
    const suffix = Number(match[2]);
    if (!Number.isSafeInteger(suffix) || suffix <= 0) return false;
    start = Math.max(0, size - suffix);
    end = size - 1;
  } else {
    start = Number(match[1]);
    end = match[2] ? Number(match[2]) : size - 1;
  }
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start > end || start >= size) return false;
  return { start, end: Math.min(end, size - 1) };
}

function acceptsHtml(req) {
  const raw = req.headers?.accept;
  if (typeof raw !== "string") return false;
  return raw.split(",").some((token) => token.trim().toLowerCase().startsWith("text/html"));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  })[ch]);
}

function mediaHtml(token, media) {
  const mime = media.mimeType || "application/octet-stream";
  const isVideo = mime.startsWith("video/");
  const safeToken = escapeHtml(token);
  const safeMime = escapeHtml(mime);
  const mediaSrc = `/api/runs/media/${token}`;
  const mediaTag = isVideo
    ? `<section class="video-frame">
  <video id="registered-video" class="frame" src="${mediaSrc}" controls preload="metadata" playsinline aria-label="已注册视频"></video>
  <div class="sound-control">
    <span id="sound-status">默认未静音；如没有声音，请点击右侧按钮。</span>
    <button id="enable-sound" type="button">开启声音并播放</button>
  </div>
</section>`
    : `<img class="frame" src="${mediaSrc}" alt="已注册图片" />`;
  const shortToken = token.length > 16 ? `${token.slice(0, 8)}…${token.slice(-4)}` : token;
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="referrer" content="no-referrer" />
<link rel="icon" href="data:," />
<title>已注册媒体 · Provider Console</title>
<style>
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body { margin: 0; background: #0b1218; color: #d6dee5; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; }
  header { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid #1c2730; gap: 12px; }
  header .meta { font-size: 13px; color: #9aa7b0; }
  header .meta code { color: #d6dee5; font-size: 12px; margin-left: 4px; }
  a.back { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: #1c2730; color: #d6dee5; border-radius: 6px; text-decoration: none; font-size: 13px; }
  a.back:hover, a.back:focus { background: #283542; outline: none; }
  main { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 56px - 44px); padding: 24px; }
  .video-frame { max-width: 100%; background: #020508; border: 1px solid #283542; border-radius: 6px; overflow: hidden; }
  video.frame, img.frame { display: block; max-width: 100%; max-height: calc(100vh - 56px - 44px - 48px); background: #020508; border: 0; object-fit: contain; }
  .sound-control { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 10px; border-top: 1px solid #283542; background: #0c151e; color: #aeb7c1; font-size: 12px; }
  .sound-control button { min-height: 30px; padding: 0 10px; border: 1px solid #6656c2; border-radius: 4px; background: #29234d; color: #eeeaff; font: inherit; cursor: pointer; }
  .sound-control button:hover, .sound-control button:focus { background: #342b61; outline: none; }
  footer { padding: 10px 20px; font-size: 12px; color: #7d8a93; border-top: 1px solid #1c2730; display: flex; gap: 16px; flex-wrap: wrap; }
  footer code { color: #9aa7b0; }
</style>
</head>
<body>
<header>
  <div class="meta">已注册媒体<code>${escapeHtml(shortToken)}</code></div>
  <a class="back" href="/" rel="noopener">← 返回 Console</a>
</header>
<main>${mediaTag}</main>
<footer>
  <span>MIME：<code>${safeMime}</code></span>
  <span>大小：<code>${media.size.toLocaleString("en-US")} bytes</code></span>
  <span>关闭此标签或点“返回 Console”回到工作区。</span>
</footer>
${isVideo ? `<script>
  const video = document.getElementById("registered-video");
  const soundButton = document.getElementById("enable-sound");
  const soundStatus = document.getElementById("sound-status");
  video.defaultMuted = false;
  video.muted = false;
  video.volume = 1;
  soundButton.addEventListener("click", async () => {
    video.defaultMuted = false;
    video.muted = false;
    video.volume = 1;
    try {
      await video.play();
      soundStatus.textContent = "声音已开启并开始播放。";
    } catch {
      soundStatus.textContent = "浏览器阻止了播放，请再点一次视频播放键。";
    }
  });
</script>` : ""}
</body>
</html>`;
}

function sendMediaHtml(res, token, media) {
  res.statusCode = 200;
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.end(mediaHtml(token, media));
}

async function sendMedia(req, res, media) {
  const range = parseRange(req.headers?.range, media.size);
  if (range === false) {
    res.statusCode = 416;
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("Content-Range", `bytes */${media.size}`);
    res.end();
    return;
  }
  const start = range?.start ?? 0;
  const end = range?.end ?? media.size - 1;
  const length = end - start + 1;
  res.statusCode = range ? 206 : 200;
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Accept-Ranges", "bytes");
  res.setHeader("Content-Type", media.mimeType);
  res.setHeader("Content-Length", length);
  if (range) res.setHeader("Content-Range", `bytes ${start}-${end}/${media.size}`);
  const file = await open(media.source, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const [stat, openedPath] = await Promise.all([
      file.stat({ bigint: true }),
      realpath(`/proc/self/fd/${file.fd}`),
    ]);
    const identity = [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String);
    if (!stat.isFile() || Number(stat.size) !== media.size || openedPath !== media.source) throw new Error("media changed after validation");
    if (identity.some((value, index) => value !== media.identity[index])) throw new Error("media identity changed after validation");
    if (openedPath !== media.root && !openedPath.startsWith(`${media.root}${path.sep}`)) throw new Error("media escaped runs root");
    if (req.method === "HEAD") {
      res.end();
      return;
    }
    const bytes = Buffer.alloc(length);
    const { bytesRead } = await file.read(bytes, 0, length, start);
    if (bytesRead !== length) throw new Error("media changed while reading");
    res.end(bytes);
  } finally {
    await file.close();
  }
}

export function createRunsApiHandler({
  repoRoot,
  runProjector = createPythonProjector(repoRoot),
  externalSources = [],
  externalCatalog = catalogExternalMedia,
}) {
  const runsRoot = path.join(repoRoot, "runs");
  const mediaCache = new Map();
  const externalDescriptors = new Map();
  const externalMediaCache = new Map();
  const externalSourceRoots = new Map();
  const configuredExternalSources = [];
  for (const source of externalSources) {
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(source?.id || "") || typeof source?.root !== "string" || externalSourceRoots.has(source.id)) continue;
    externalSourceRoots.set(source.id, source.root);
    configuredExternalSources.push(source);
  }

  return async function runsApi(req, res, next) {
    const parsed = new URL(req.url || "/", "http://127.0.0.1");
    const isRunsRequest = parsed.pathname.startsWith("/api/runs");
    const isExternalRequest = parsed.pathname.startsWith("/api/external-media");
    if (!isRunsRequest && !isExternalRequest) {
      next();
      return;
    }
    if (!isLoopbackRequest(req)) {
      send(res, 403, { error: { code: "LOCAL_ONLY", message: "Provider Console 只读 API 仅允许本机访问。" } });
      return;
    }

    try {
      if (parsed.pathname === "/api/external-media") {
        if (req.method !== "GET") return methodNotAllowed(res, "GET");
        const result = await externalCatalog({ sources: configuredExternalSources });
        externalDescriptors.clear();
        externalMediaCache.clear();
        const entries = result?._media && typeof result._media === "object" ? Object.entries(result._media) : [];
        for (const [token, entry] of entries) {
          if (!/^[A-Za-z0-9_-]{6,128}$/.test(token) || !externalSourceRoots.has(entry?.source_id)) continue;
          externalDescriptors.set(token, entry);
        }
        send(res, 200, publicProjection(result));
        return;
      }

      const externalMediaMatch = /^\/api\/external-media\/media\/([A-Za-z0-9_-]{6,128})$/.exec(parsed.pathname);
      if (externalMediaMatch) {
        if (req.method !== "GET" && req.method !== "HEAD") return methodNotAllowed(res, "GET, HEAD");
        const token = externalMediaMatch[1];
        const descriptor = externalDescriptors.get(token);
        if (!descriptor) {
          send(res, 404, { error: { code: "EXTERNAL_MEDIA_NOT_FOUND", message: "外部媒体不存在或尚未扫描。" } });
          return;
        }
        let media = externalMediaCache.get(token);
        if (!media) {
          media = await validatedMedia(descriptor, externalSourceRoots.get(descriptor.source_id));
          if (!media) throw new RunsApiError(503, "EXTERNAL_MEDIA_CHANGED");
          externalMediaCache.set(token, media);
        }
        await sendMedia(req, res, media);
        return;
      }

      if (isExternalRequest) {
        send(res, 404, { error: { code: "NOT_FOUND", message: "接口不存在。" } });
        return;
      }

      if (parsed.pathname === "/api/runs") {
        if (req.method !== "GET") return methodNotAllowed(res, "GET");
        const result = await runProjector("catalog");
        send(res, 200, publicProjection(result));
        return;
      }

      if (parsed.pathname === "/api/runs/detail") {
        if (req.method !== "GET") return methodNotAllowed(res, "GET");
        const workspace = parsed.searchParams.get("workspace");
        if (!isSafeWorkspace(workspace)) {
          send(res, 400, { error: { code: "INVALID_WORKSPACE", message: "workspace 参数无效。" } });
          return;
        }
        let result;
        try {
          result = await runProjector("detail", workspace);
        } catch (cause) {
          const status = cause instanceof RunsApiError ? cause.status : 503;
          const code = cause instanceof RunsApiError ? cause.code : "RUNS_SOURCE_UNAVAILABLE";
          const message = status === 404 ? "workspace 不存在。" : status === 400 ? "workspace 参数无效。" : "本地 runs 数据源不可用。";
          send(res, status, { error: { code, message } });
          return;
        }
        const entries = result?._media && typeof result._media === "object" ? Object.entries(result._media) : [];
        for (const [token, entry] of entries) {
          if (!/^[A-Za-z0-9_-]{6,128}$/.test(token)) continue;
          const media = await validatedMedia(entry, runsRoot);
          if (media) mediaCache.set(token, media);
        }
        send(res, 200, publicProjection(result));
        return;
      }

      if (parsed.pathname === "/api/runs/continuity-review") {
        if (req.method !== "GET") return methodNotAllowed(res, "GET");
        const workspace = parsed.searchParams.get("workspace");
        const attemptId = parsed.searchParams.get("attempt");
        if (!isSafeWorkspace(workspace) || !/^[A-Za-z0-9._:/-]{1,256}$/.test(attemptId || "")) {
          send(res, 400, { error: { code: "INVALID_REVIEW_TARGET", message: "review target 参数无效。" } });
          return;
        }
        let result;
        try {
          result = validateContinuityProjection(
            await runProjector("continuity-review", workspace, attemptId)
          );
          if (
            result.workspace !== workspace
            || result.attempt_id !== attemptId
            || result.review_request.attempt_id !== attemptId
          ) throw new RunsApiError(503, "CONTINUITY_REVIEW_INVALID");
        } catch (cause) {
          const status = cause instanceof RunsApiError ? cause.status : 503;
          const code = cause instanceof RunsApiError ? cause.code : "CONTINUITY_REVIEW_UNAVAILABLE";
          const message = status === 404 ? "workspace 不存在。" : status === 409 ? "该 attempt 当前不可人工 review。" : "continuity review 投影不可用。";
          send(res, status, { error: { code, message } });
          return;
        }
        const entries = result?._media && typeof result._media === "object" ? Object.entries(result._media) : [];
        let exactMediaRegistered = false;
        for (const [token, entry] of entries) {
          if (!/^[A-Za-z0-9_-]{6,128}$/.test(token)) continue;
          if (
            token === result.media.token
            && entry?.sha256 !== result.media.sha256
          ) continue;
          const media = await validatedMedia(entry, runsRoot);
          if (media) {
            mediaCache.set(token, media);
            if (token === result.media.token) exactMediaRegistered = true;
          }
        }
        if (!exactMediaRegistered) {
          send(res, 503, { error: { code: "CONTINUITY_REVIEW_INVALID", message: "continuity review 投影不可用。" } });
          return;
        }
        send(res, 200, publicProjection(result));
        return;
      }

      const mediaMatch = /^\/api\/runs\/media\/([A-Za-z0-9_-]{6,128})$/.exec(parsed.pathname);
      if (mediaMatch) {
        if (req.method !== "GET" && req.method !== "HEAD") return methodNotAllowed(res, "GET, HEAD");
        const token = mediaMatch[1];
        const media = mediaCache.get(token);
        if (!media) {
          send(res, 404, { error: { code: "MEDIA_NOT_FOUND", message: "媒体不存在或尚未验证。" } });
          return;
        }
        if (req.method === "GET" && acceptsHtml(req)) {
          sendMediaHtml(res, token, media);
          return;
        }
        await sendMedia(req, res, media);
        return;
      }

      send(res, 404, { error: { code: "NOT_FOUND", message: "接口不存在。" } });
    } catch {
      const external = parsed.pathname.startsWith("/api/external-media");
      send(res, 503, { error: external
        ? { code: "EXTERNAL_MEDIA_SOURCE_UNAVAILABLE", message: "外部媒体数据源不可用或文件已变化。" }
        : { code: "RUNS_SOURCE_UNAVAILABLE", message: "本地 runs 数据源不可用。" } });
    }
  };
}

export function createRunsApiPlugin(options) {
  const handler = createRunsApiHandler(options);
  return {
    name: "ai-video-runs-api",
    configureServer(server) { server.middlewares.use(handler); },
    configurePreviewServer(server) { server.middlewares.use(handler); },
  };
}
