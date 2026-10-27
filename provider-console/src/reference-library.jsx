import React, { useEffect, useState } from "react";
import { ReferenceMedia } from "./reference-media.jsx";

export function ReferenceLibrary({ revision = 0, live = false }) {
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/reference-library?${new URLSearchParams({ query, offset: String(offset) })}`, { cache: "no-store", signal: controller.signal });
        const body = await response.json();
        if (!response.ok || body.error) throw new Error("参考素材读取失败，请刷新重试。");
        if (!controller.signal.aborted) setResult(body);
      } catch (cause) {
        if (!controller.signal.aborted) setError(cause.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query, offset, revision]);
  return <section className="reference-library" aria-label="参考素材库">
    <header><h2>referces · 本地参考素材</h2><p>按原目录浏览；收录不代表已选用于当前 Shot 或已提交生成。</p></header>
    <label className="reference-library-search">搜索参考素材<input type="search" value={query} placeholder="文件名或目录，如 lin-xu、courier" onChange={(event) => { setQuery(event.target.value); setOffset(0); setResult(null); }} /></label>
    <p role="status">{loading ? "正在读取参考素材…" : `共 ${result?.total || 0} 张匹配图片`}{live ? " · 目录更新自动同步" : " · 实时监视未连接，可手动刷新"}</p>
    {error && <p role="alert">{error}{result && " 保留的结果可能已过期。"}</p>}
    {result?.status === "unavailable" && <p>本地 referces 目录不可用。</p>}
    {result?.truncated && <p>目录扫描达到上限或部分目录不可读，当前结果不完整。</p>}
    {!loading && !error && result?.status === "available" && !result.total && <p>没有匹配图片。支持 PNG、JPEG 和 WebP。</p>}
    <div className="shot-reference-grid">{(result?.items || []).map((item) => <article key={item.relative_path}>
      <ReferenceMedia media={item.media} label={item.file_name} />
      <strong>{item.file_name}</strong><small>{item.relative_path}</small>
      {item.availability === "unavailable" && <small>文件暂不可读或超出预览上限</small>}
    </article>)}</div>
    {result?.total > 0 && <nav className="library-pagination" aria-label="参考素材分页">
      <button type="button" disabled={loading || result.offset === 0} onClick={() => setOffset(Math.max(0, result.offset - result.page_size))}>上一页</button>
      <span>{result.offset + 1}–{Math.min(result.offset + result.page_size, result.total)} / {result.total}</span>
      <button type="button" disabled={loading || result.offset + result.page_size >= result.total} onClick={() => setOffset(result.offset + result.page_size)}>下一页</button>
    </nav>}
  </section>;
}
