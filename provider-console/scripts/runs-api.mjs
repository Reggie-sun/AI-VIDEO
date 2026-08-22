import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { lstat, open, realpath } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

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

function createPythonProjector(repoRoot) {
  const runsRoot = path.join(repoRoot, "runs");
  const python = process.env.AI_VIDEO_PYTHON || "python";
  return async (command, workspace) => {
    const args = ["-m", "ai_video.provider_console", command, "--runs-root", runsRoot];
    if (workspace) args.push("--workspace", workspace);
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
      const status = code === "WORKSPACE_NOT_FOUND" ? 404 : code === "INVALID_WORKSPACE" ? 400 : 503;
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
  const resolved = await realpath(source);
  if (resolved !== source || (resolved !== root && !resolved.startsWith(`${root}${path.sep}`))) return null;
  const stat = await lstat(source, { bigint: true });
  if (!stat.isFile() || stat.isSymbolicLink()) return null;
  if (Number.isSafeInteger(entry.bytes) && BigInt(entry.bytes) !== stat.size) return null;
  return {
    source,
    root,
    mimeType: entry.mime_type,
    size: Number(stat.size),
    identity: [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String),
  };
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

export function createRunsApiHandler({ repoRoot, runProjector = createPythonProjector(repoRoot) }) {
  const runsRoot = path.join(repoRoot, "runs");
  const mediaCache = new Map();

  return async function runsApi(req, res, next) {
    const parsed = new URL(req.url || "/", "http://127.0.0.1");
    if (!parsed.pathname.startsWith("/api/runs")) {
      next();
      return;
    }
    if (!isLoopbackRequest(req)) {
      send(res, 403, { error: { code: "LOCAL_ONLY", message: "runs API 仅允许本机访问。" } });
      return;
    }

    try {
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

      const mediaMatch = /^\/api\/runs\/media\/([A-Za-z0-9_-]{6,128})$/.exec(parsed.pathname);
      if (mediaMatch) {
        if (req.method !== "GET" && req.method !== "HEAD") return methodNotAllowed(res, "GET, HEAD");
        const media = mediaCache.get(mediaMatch[1]);
        if (!media) {
          send(res, 404, { error: { code: "MEDIA_NOT_FOUND", message: "媒体不存在或尚未验证。" } });
          return;
        }
        await sendMedia(req, res, media);
        return;
      }

      send(res, 404, { error: { code: "NOT_FOUND", message: "接口不存在。" } });
    } catch {
      send(res, 503, { error: { code: "RUNS_SOURCE_UNAVAILABLE", message: "本地 runs 数据源不可用。" } });
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
