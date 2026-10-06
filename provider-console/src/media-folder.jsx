import React, { useState } from "react";
import { FolderOpen } from "@phosphor-icons/react";

export function MediaFolderButton({ entry }) {
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState("");
  const supported = /^\/api\/(runs|external-media)\/media\/[A-Za-z0-9_-]{6,128}$/.test(entry.url || "");
  const openFolder = async () => {
    if (pending || !entry.available || !supported) return;
    setPending(true);
    setNotice("");
    try {
      const response = await fetch(`${entry.url}/open-folder`, {
        method: "POST", headers: { "X-AI-Video-Action": "open-media-folder" },
      });
      const result = await response.json();
      setNotice(response.ok && result.opened ? "已请求打开所在文件夹。" : result.error?.message || "无法打开所在文件夹，请稍后重试。");
    } catch { setNotice("无法连接本机服务，请稍后重试。"); }
    finally { setPending(false); }
  };
  return <div className="library-folder-action">
    <button type="button" disabled={pending || !entry.available || !supported} onClick={openFolder}>
      <FolderOpen size={16} aria-hidden="true" />{pending ? "正在打开…" : "打开所在文件夹"}
    </button>
    {notice && <p role="status">{notice}</p>}
  </div>;
}
