import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { buildLibraryEntries, filterLibraryEntries, libraryLifecycle, selectLibraryEntry, versionGroups } from "./library-contract.js";
import { useLibraryData } from "./library-data.js";
import { classifyPlaybackFailure, keepOneAudio, playbackFailureLabel } from "./library-preview.js";
import { durationLabel, entryTitle, VideoLibraryRail } from "./video-library-rail.jsx";
import { attemptId } from "./run-detail-contract.js";
import { libraryLiveStatus } from "./library-refresh-contract.js";
import "./library-browser.css";

export function ExactPlayer({ entry, measurement, onMeasured, onUnavailable }) {
  const ref = useRef(null);
  const errorRequest = useRef(null);
  useEffect(() => {
    const media = ref.current;
    if (media && entry.url && media.getAttribute("src") !== entry.url) { media.src = entry.url; media.load(); }
    return () => { errorRequest.current?.abort(); if (media) { media.pause(); media.removeAttribute("src"); media.load(); } };
  }, [entry.id, entry.url, measurement?.playbackError]);
  if (!entry.available || !entry.url) return <p role="status">文件不可用，请刷新重新读取。所选视频保持固定。</p>;
  if (measurement?.playbackError) return <div role="status"><p>{playbackFailureLabel(measurement.playbackError)}。原文件未被替换。</p><a href={entry.url} download={`${entry.sha256 || entry.id}.mp4`}>下载原文件</a></div>;
  return <video ref={ref} src={entry.url} poster={measurement?.poster} controls muted playsInline preload="metadata" aria-label={`预览 ${entryTitle(entry)}`} data-media-identity={entry.id}
    onLoadedMetadata={(event) => { const v = event.currentTarget; onMeasured(entry.id, { duration: Number.isFinite(v.duration) ? v.duration : null, width: v.videoWidth, height: v.videoHeight }); }}
    onVolumeChange={(event) => keepOneAudio(event.currentTarget, event.currentTarget.closest(".library-shell"))}
    onError={async (event) => {
      errorRequest.current?.abort();
      const controller = new AbortController();
      errorRequest.current = controller;
      const kind = await classifyPlaybackFailure(event.currentTarget.error?.code, entry.url, controller.signal);
      if (kind === "unavailable") onUnavailable(entry.id);
      else if (kind) onMeasured(entry.id, { playbackError: kind });
    }} />;
}

export function StatusSummary({ context, available, playbackError }) {
  return <dl className="library-status">
    <div><dt>媒体</dt><dd>{available ? playbackFailureLabel(playbackError) || "已获取 · 可预览" : "文件不可用"}</dd></div>
    <div><dt>生成记录</dt><dd>{context?.attempt ? libraryLifecycle(context.attempt) : "未提供"}</dd></div>
    <div><dt>质量证据</dt><dd>未评估 · 请查看 exact 证据层</dd></div>
  </dl>;
}

function ContextPicker({ entry, value, onChange }) {
  return <label className="library-context">{entry.ambiguous ? "多个绑定有歧义，请选择详情上下文" : "来源与输出角色"}
    <select value={value} onChange={(event) => onChange(event.target.value)} aria-label="选择视频详情上下文">
      <option value="">{entry.contexts.length} 个来源 / 角色</option>
      {entry.contexts.map((context) => <option key={context.id} value={context.id}>{context.title || "名称未提供"} · {context.model || "模型未提供"} · {context.workspace || context.sourceId} · {context.role}</option>)}
    </select>
  </label>;
}

function Preview({ entry, measurements, onMeasured, onUnavailable, entries, renderContext, onSelect }) {
  const [contextId, setContextId] = useState("");
  const context = entry.contexts.find((item) => item.id === contextId) || (!entry.ambiguous ? entry.contexts.find((item) => item.attempt) || entry.contexts[0] : null);
  const groups = versionGroups(entries);
  const members = context?.versionKey ? groups.get(context.versionKey)?.contexts || [] : [];
  const measurement = measurements[entry.id];
  return <section className="library-preview" aria-label="视频预览详情">
    <header><span className="library-eyebrow">视频预览</span><h1>{context?.title || entryTitle(entry)}</h1><p>{context?.model || entry.model || "模型未提供"} · {durationLabel(measurement)}{measurement?.width ? ` · ${measurement.width} × ${measurement.height}` : " · 实测尺寸未提供"}</p></header>
    <ExactPlayer key={`${entry.id}:${entry.url}`} entry={entry} measurement={measurement} onMeasured={onMeasured} onUnavailable={onUnavailable} />
    <StatusSummary context={context} available={entry.available} playbackError={measurement?.playbackError} />
    <ContextPicker entry={entry} value={contextId} onChange={setContextId} />
    <details className="library-sources"><summary>全部来源与 exact identity（{entry.contexts.length}）</summary><code>{entry.sha256} · {entry.bytes} bytes</code>{entry.contexts.map((item) => <p key={item.id}>{item.workspace || item.sourceId} · {item.role}<br />{item.media?.asset_id || item.media?.relative_path || item.group?.preview?.relative_path || "相对文件标识未提供"}</p>)}</details>
    <details><summary>版本（仅限严格验证的同 Project / Shot）</summary>{members.length ? members.map(({ entry: video, context: binding }) => <button type="button" key={`${video.id}:${binding.id}`} onClick={() => onSelect(video.id)}>{entryTitle(video)} · revision {binding.attempt.target_shot_revision} · {binding.model || "模型未提供"} · {binding.startedAt || "时间未提供"} · {binding.role}</button>) : <p>没有可归组的版本。独立 Project 保持独立，可手动选择比较。</p>}</details>
    {context ? <details className="library-diagnostics"><summary>创作意图 / 生成详情 / 证据</summary><div className="library-diagnostic-content">{renderContext(context)}</div></details> : <p>请选择一个来源上下文后查看 Prompt、生成详情和证据。</p>}
  </section>;
}

function Comparison({ entries, measurements, onMeasured, onUnavailable, onClose }) {
  const close = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    close.current?.focus();
    const escape = (event) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("keydown", escape); previous?.focus?.(); };
  }, [onClose]);
  return <section className="library-comparison" aria-label="双视频比较"><header><div><h1>比较视频</h1><p>独立播放与定位 · 默认静音 · 不对齐时长</p></div><button ref={close} type="button" onClick={onClose}>退出比较</button></header><div className="library-comparison-grid">{entries.map((entry) => <article key={entry.id}><h2>{entryTitle(entry)}</h2><p>{entry.model || "模型未提供"} · {durationLabel(measurements[entry.id])}</p><ExactPlayer entry={entry} measurement={measurements[entry.id]} onMeasured={onMeasured} onUnavailable={onUnavailable} /><StatusSummary available={entry.available} playbackError={measurements[entry.id]?.playbackError} context={!entry.ambiguous && entry.contexts.find((item) => item.attempt)} /><code>{entry.contexts.map((item) => item.workspace || item.sourceId).filter((v, i, a) => a.indexOf(v) === i).join(" · ")}</code></article>)}</div></section>;
}

export function LibraryBrowser({ sidebar, renderContext, renderRecord }) {
  const data = useLibraryData();
  const [view, setView] = useState("library");
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [model, setModel] = useState("all");
  const [availability, setAvailability] = useState("all");
  const [evidence, setEvidence] = useState("all");
  const [selectedId, setSelectedId] = useState("");
  const [followLatest, setFollowLatest] = useState(false);
  const [compareIds, setCompareIds] = useState([]);
  const [comparing, setComparing] = useState(false);
  const [notice, setNotice] = useState("");
  const [measurements, setMeasurements] = useState({});
  const [unavailable, setUnavailable] = useState(new Set());
  const [record, setRecord] = useState(null);
  const [recordQuery, setRecordQuery] = useState("");
  const lastSelected = useRef(null);
  const listScroll = useRef(null);
  const savedScroll = useRef(0);
  const entries = useMemo(() => buildLibraryEntries(data.loaded, data.external).map((entry) => unavailable.has(entry.id) ? { ...entry, available: false, url: null } : entry), [data.loaded, data.external, unavailable]);
  const filtered = useMemo(() => filterLibraryEntries(entries, { query, source, model, availability, evidence }), [entries, query, source, model, availability, evidence]);
  useEffect(() => { setSelectedId((current) => selectLibraryEntry(filtered, current, followLatest)); }, [filtered, followLatest]);
  const current = entries.find((item) => item.id === selectedId);
  if (current) lastSelected.current = current;
  const selected = current || (lastSelected.current?.id === selectedId ? { ...lastSelected.current, available: false, url: null } : null);
  const onSelect = (id) => { setFollowLatest(false); setSelectedId(id); };
  const onMeasured = useCallback((id, measurement) => setMeasurements((current) => {
    const next = { ...current, [id]: { ...current[id], ...measurement } };
    const posters = Object.keys(next).filter((key) => next[key].poster);
    for (const key of posters.slice(0, Math.max(0, posters.length - 60))) {
      const { poster, ...metadata } = next[key];
      next[key] = metadata;
    }
    return next;
  }), []);
  const onUnavailable = useCallback((id) => setUnavailable((current) => new Set([...current, id])), []);
  const onCompare = (id) => {
    setNotice("");
    if (!compareIds.includes(id) && compareIds.length === 2) { setNotice("最多选择两段视频；请先取消其中一段。"); return; }
    setCompareIds((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]);
  };
  const compareEntries = compareIds.map((id) => entries.find((item) => item.id === id)).filter(Boolean);
  const canCompare = compareEntries.length === 2 && compareEntries.every((entry) => entry.available);
  const closeComparison = useCallback(() => setComparing(false), []);
  useEffect(() => { if (!comparing && listScroll.current) listScroll.current.scrollTop = savedScroll.current; }, [comparing]);
  const refresh = () => { setUnavailable(new Set()); setMeasurements((current) => Object.fromEntries(Object.entries(current).map(([id, value]) => [id, { ...value, playbackError: null }]))); data.refreshRuns(); data.refreshExternal({ force: true }); };
  const failed = Object.values(data.details).filter((item) => item.error);
  const partial = data.runsError || data.externalError || data.indexNotice || data.catalog.truncated || data.loaded.some((item) => item.workspace_media_truncated || item.status === "recovered_video_evidence" || item.attempts?.some((attempt) => attempt.candidate_media_truncated)) || (data.external?.sources || []).some((item) => item.truncated || item.status !== "available");
  const liveStatus = libraryLiveStatus({ connectionState: data.connection.state, expectedSources: data.connection.expectedSources, watchedSources: data.connection.watchedSources, selectedSource: source, refreshFailed: Boolean(data.runsError || data.externalError) });
  const recordItems = (data.catalog.workspaces || []).filter((item) => `${item.workspace} ${data.details[item.workspace]?.detail?.project?.title || ""}`.toLowerCase().includes(recordQuery.toLowerCase()));
  const recordDetail = record && data.details[record.workspace]?.detail;
  return <div className="library-shell" onVolumeChangeCapture={(event) => keepOneAudio(event.target, event.currentTarget)}>{sidebar}<main className="library-main">
    <header className="library-header"><div><span className="library-eyebrow">AI-VIDEO / 本地媒体</span><h1>视频库</h1></div><div className="library-view-tabs"><button type="button" aria-pressed={view === "library"} onClick={() => { setView("library"); setComparing(false); }}>视频库</button><button type="button" aria-pressed={view === "records"} onClick={() => { setView("records"); setComparing(false); }}>生成记录</button></div><button type="button" onClick={refresh}>刷新</button></header>
    <div className="library-coverage" role="status">已加载 {filtered.length} 段（当前筛选） · {data.loaded.length} / {(data.catalog.workspaces || []).length} 个工作区 · {data.runsLoading || data.externalLoading || data.indexLoading ? "扫描 / 关联进行中" : partial || failed.length ? "扫描结束 · 覆盖不完整" : "已完成当前允许范围扫描"} · {liveStatus === "live" ? "实时更新已连接" : liveStatus === "partial" ? "部分来源未实时监视，可手动刷新" : "实时更新连接中、过期或不可用，可手动刷新"}
      {(data.runsError || data.externalError) && <p className="library-warning">刷新失败，保留的结果可能已过期：{data.runsError} {data.externalError}</p>}
      {Boolean(failed.length) && <details><summary>{failed.length} 个工作区不可用</summary>{Object.entries(data.details).filter(([, item]) => item.error).map(([key, item]) => <p key={key}>{key} · {item.error}</p>)}</details>}
      {data.indexNotice && <p>Runs 证据关联：{data.indexNotice}</p>}
      {partial && <p>扫描截断、恢复旁证或部分来源不可用；当前列表不是全部内容的完整索引。</p>}
      {(data.external?.sources || []).filter((item) => item.status !== "available" || item.truncated).map((item) => <p key={item.id}>{item.label || item.id} · {item.status}{item.truncated ? " · 扫描截断" : ""}</p>)}
    </div>
    {view === "library" && <>
      <div className="library-filters"><label>搜索已加载视频<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="作品 / Run / Shot / 模型 / 文件名" /></label><label>来源<select id="video-source-select" value={source} onChange={(event) => setSource(event.target.value)}><option value="all">全部视频来源</option><option value="runs">Runs</option>{(data.external?.sources || []).map((item) => <option key={item.id} value={item.id}>{item.label || item.id}</option>)}</select></label><label>模型<select value={model} onChange={(event) => setModel(event.target.value)}><option value="all">全部模型</option>{[...new Set(entries.flatMap((entry) => entry.contexts.map((item) => item.model)).filter(Boolean))].sort().map((value) => <option key={value}>{value}</option>)}</select></label><label>媒体状态<select value={availability} onChange={(event) => setAvailability(event.target.value)}><option value="all">全部状态</option><option value="available">可预览</option><option value="unavailable">文件不可用</option></select></label><details className="library-advanced"><summary>高级证据筛选</summary><select aria-label="证据筛选" value={evidence} onChange={(event) => setEvidence(event.target.value)}><option value="all">全部证据状态</option><option value="linked">已关联</option><option value="unbound">无绑定证据</option><option value="unparsed">旁证待解析</option><option value="incomplete">Runs 待恢复</option></select></details></div>
      <div className="library-selection-bar"><label><input type="checkbox" checked={followLatest} onChange={(event) => setFollowLatest(event.target.checked)} />跟随最新</label><span>已选择 {compareIds.length} / 2 段比较</span>{compareIds.length > 0 && <button type="button" onClick={() => { setCompareIds([]); setComparing(false); }}>清空比较选择</button>}<button type="button" disabled={!canCompare} onClick={() => { savedScroll.current = listScroll.current?.scrollTop || 0; setComparing(true); }}>比较所选视频</button>{notice && <span role="status">{notice}</span>}</div>
      {comparing && <Comparison entries={compareIds.map((id) => entries.find((item) => item.id === id) || { id, title: "所选视频已不可用", contexts: [], available: false })} measurements={measurements} onMeasured={onMeasured} onUnavailable={onUnavailable} onClose={closeComparison} />}<div className="library-body" style={comparing ? { display: "none" } : undefined}><section ref={listScroll} className="library-list-scroll" aria-label="浏览视频"><VideoLibraryRail entries={filtered} selectedId={selectedId} compareIds={compareIds} onSelect={onSelect} onCompare={onCompare} measurements={measurements} onMeasured={onMeasured} /></section><div className="library-preview-scroll">{!comparing && selected ? <Preview key={selected.id} entry={selected} entries={entries} measurements={measurements} onMeasured={onMeasured} onUnavailable={onUnavailable} renderContext={renderContext} onSelect={onSelect} /> : <p className="library-empty">选择视频开始预览。扫描结果将逐步显示。</p>}</div></div>
    </>}
    {view === "records" && <div className="library-records"><section><label>搜索生成记录<input type="search" value={recordQuery} onChange={(event) => setRecordQuery(event.target.value)} /></label>{recordItems.map((item) => <article key={item.workspace}><button type="button" onClick={() => setRecord({ workspace: item.workspace, attemptId: "" })}>{data.details[item.workspace]?.detail?.project?.title || item.run_id || item.workspace}<small>{item.workspace}</small></button>{(data.details[item.workspace]?.detail?.attempts || []).map((attempt, index) => <button type="button" key={attemptId(attempt, index)} onClick={() => setRecord({ workspace: item.workspace, attemptId: attemptId(attempt, index) })}>{attempt.target_shot_id || "Shot 未提供"} · {libraryLifecycle(attempt)}<small>{attempt.error_code || attemptId(attempt, index)}</small></button>)}{data.details[item.workspace]?.error && <p>{data.details[item.workspace].error}</p>}</article>)}</section><div className="library-record-detail">{recordDetail ? renderRecord(recordDetail, record.attemptId, (id) => setRecord({ ...record, attemptId: id })) : <p>选择工作区或生成记录，查看错误与 Shot 上下文。尚无视频的工作区也保留检查入口。</p>}</div></div>}
  </main></div>;
}
