import React, { useEffect, useState } from "react";
import { ReferenceMedia } from "./reference-media.jsx";

const CATEGORIES = [["character", "人物"], ["shot", "Shot"], ["other", "其他素材"]];

export function ReferenceLibrary({ revision = 0, live = false }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("character");
  const [group, setGroup] = useState("");
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState(null);
  const [facets, setFacets] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const resetPage = () => { setOffset(0); setResult(null); setLoading(true); setError(""); };
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/reference-library?${new URLSearchParams({ query, category, group, offset: String(offset) })}`, { cache: "no-store", signal: controller.signal });
        const body = await response.json();
        if (!response.ok || body.error) throw new Error("参考素材读取失败，请刷新重试。");
        if (!controller.signal.aborted) { setResult(body); setFacets(body); }
      } catch (cause) {
        if (!controller.signal.aborted) setError(cause.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query, category, group, offset, revision]);
  const groups = (facets?.groups || []).filter((item) => item.category === category);
  const selected = groups.find((item) => item.group_id === (group || result?.selected_group));
  return <section className="reference-library" aria-label="参考素材库">
    <header><h2>参考素材</h2><p>先选人物或 Shot，再查看对应参考图。按 referces 目录归类；收录不代表已选用于生成。</p></header>
    <nav className="reference-library-tabs" aria-label="参考素材分类">{CATEGORIES.map(([id, label]) => <button key={id} type="button" aria-pressed={category === id} onClick={() => { if (category !== id) { setCategory(id); setGroup(""); resetPage(); } }}>{label}<span>{facets?.category_counts?.[id] ?? "…"}</span></button>)}</nav>
    <label className="reference-library-search">搜索参考素材<input type="search" value={query} placeholder="搜索人物、Shot 或文件名" onChange={(event) => { setQuery(event.target.value); setGroup(""); setFacets(null); resetPage(); }} /></label>
    <p role="status">{loading ? "正在读取参考素材…" : `当前分组 ${result?.total || 0} 张图片`}{live ? " · 目录更新自动同步" : " · 实时监视未连接，可手动刷新"}</p>
    {error && <p role="alert">{error}{result && " 保留的结果可能已过期。"}</p>}
    {result?.status === "unavailable" && <p>本地 referces 目录不可用。</p>}
    {result?.classification_unavailable && <p>人物分类配置暂不可读，未确认归属的图片可在“其他素材”查看。</p>}
    {result?.truncated && <p>目录扫描达到上限或部分目录不可读，当前结果不完整。</p>}
    <div className="reference-library-layout">
      <nav className="reference-library-groups" aria-label="参考素材分组">{groups.map((item) => <button key={item.group_id} type="button" aria-pressed={selected?.group_id === item.group_id} onClick={() => { if (selected?.group_id !== item.group_id) { setGroup(item.group_id); resetPage(); } }}><strong>{item.group_label}</strong><small>{item.project_label} · {item.count} 张</small></button>)}</nav>
      <div className="reference-library-content">
        {selected && <h3>{selected.group_label}<small>{selected.project_label}</small></h3>}
        {!loading && !error && result?.status === "available" && !result.total && <p>当前分类没有匹配图片，可切换分类或修改搜索内容。</p>}
        <div className="shot-reference-grid">{(result?.items || []).map((item) => <article key={item.relative_path}>
          <ReferenceMedia media={item.media} label={item.file_name} />
          <small className="reference-library-usage">{item.usage}</small>
          <strong>{item.file_name}</strong><small>{item.relative_path}</small>
          {item.availability === "unavailable" && <small>文件暂不可读或超出预览上限</small>}
        </article>)}</div>
        {result?.total > 0 && <nav className="library-pagination" aria-label="参考素材分页">
          <button type="button" disabled={loading || result.offset === 0} onClick={() => setOffset(Math.max(0, result.offset - result.page_size))}>上一页</button>
          <span>{result.offset + 1}–{Math.min(result.offset + result.page_size, result.total)} / {result.total}</span>
          <button type="button" disabled={loading || result.offset + result.page_size >= result.total} onClick={() => setOffset(result.offset + result.page_size)}>下一页</button>
        </nav>}
      </div>
    </div>
  </section>;
}
