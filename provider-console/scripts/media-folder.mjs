import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { open, realpath } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export async function openMediaFolder(directory) {
  // GIO uses desktop activation even when the dev server has no DISPLAY.
  const runtimeRoot = process.env.XDG_RUNTIME_DIR || `/run/user/${process.getuid()}`;
  await execFileAsync("gio", ["open", directory], {
    timeout: 5000, maxBuffer: 64 * 1024,
    env: { ...process.env, DBUS_SESSION_BUS_ADDRESS: process.env.DBUS_SESSION_BUS_ADDRESS || `unix:path=${runtimeRoot}/bus` },
  });
}

function reply(res, status, code, message) {
  res.statusCode = status;
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(code ? { error: { code, message } } : { opened: true }));
}

export async function handleMediaFolderRequest(req, res, { resolveMedia, openFolder = openMediaFolder }) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    reply(res, 405, "METHOD_NOT_ALLOWED", "打开所在文件夹需要点击按钮。");
    return;
  }
  // Custom header prevents simple cross-site POSTs; Origin binds the local page.
  const origin = req.headers?.origin;
  let sameOrigin = false;
  try {
    const url = new URL(origin);
    sameOrigin = ["http:", "https:"].includes(url.protocol) && url.host === req.headers.host;
  } catch { /* Missing or invalid Origin is denied. */ }
  if (!sameOrigin || req.headers["x-ai-video-action"] !== "open-media-folder"
    || (req.headers["sec-fetch-site"] && req.headers["sec-fetch-site"] !== "same-origin")
    || new URL(req.url, "http://127.0.0.1").search) {
    reply(res, 403, "LOCAL_ACTION_DENIED", "请在本机视频库中打开所在文件夹。");
    return;
  }
  let media;
  try { media = await resolveMedia(); } catch { /* Invalid files are unavailable. */ }
  if (!media || !media.mimeType.startsWith("video/")) {
    reply(res, 404, "MEDIA_NOT_FOUND", "视频文件不可用，请刷新后重试。");
    return;
  }
  let file;
  try {
    file = await open(media.source, constants.O_RDONLY | constants.O_NOFOLLOW);
    const [stat, openedPath, root] = await Promise.all([
      file.stat({ bigint: true }), realpath(`/proc/self/fd/${file.fd}`), realpath(media.root),
    ]);
    const identity = [stat.dev, stat.ino, stat.mtimeNs, stat.ctimeNs].map(String);
    if (!stat.isFile() || Number(stat.size) !== media.size || openedPath !== media.source
      || !openedPath.startsWith(`${root}${path.sep}`)
      || identity.some((value, index) => value !== media.identity[index])) throw new Error("changed");
  } catch {
    reply(res, 409, "MEDIA_CHANGED", "视频文件已变化或不可用，请刷新后重试。");
    return;
  } finally { await file?.close(); }
  try {
    await openFolder(path.dirname(media.source));
    reply(res, 200);
  } catch {
    reply(res, 503, "FOLDER_OPEN_FAILED", "无法打开所在文件夹，请检查本机文件管理器。");
  }
}
