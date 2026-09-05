import React, { useEffect, useRef, useState } from "react";
import { requestLibraryPreview } from "./library-preview.js";

export function durationLabel(measurement) {
  return Number.isFinite(measurement?.duration) ? `${measurement.duration.toFixed(3)} 秒` : "实测时长未提供";
}

export function entryTitle(entry) { return entry?.title || `多个详情上下文 · ${entry?.sha256?.slice(0, 12) || "未提供"}`; }

function VideoCard({ entry, selected, checked, onSelect, onCompare, measurement, onMeasured }) {
  const ref = useRef(null);
  useEffect(() => {
    let controller;
    const observer = new IntersectionObserver(([item]) => {
      if (!item.isIntersecting) { controller?.abort(); controller = null; }
      if (item.isIntersecting && !controller && entry.url) {
        controller = new AbortController();
        const request = controller;
        requestLibraryPreview(entry, controller.signal).then((result) => {
          if (result && !request.signal.aborted) onMeasured(entry.id, result);
        });
      }
    });
    observer.observe(ref.current);
    return () => { observer.disconnect(); controller?.abort(); };
  }, [entry.id, entry.url, onMeasured]);
  return <article ref={ref} className={`library-card${selected ? " is-selected" : ""}`}>
    <button className="library-card-select" type="button" aria-pressed={selected} onClick={() => onSelect(entry.id)}>
      <div className="library-thumbnail">{measurement?.poster ? <img src={measurement.poster} alt={`${entryTitle(entry)} 的视频缩略图`} /> : <span>{measurement?.failed || !entry.url ? "预览图暂不可用" : "正在读取预览图…"}</span>}<span className="library-duration">{durationLabel(measurement)}</span></div>
      <strong>{entryTitle(entry)}</strong><span className="library-card-model">{entry.model || "模型未提供"}</span>
      <span>{entry.available ? "已获取 · 可预览" : "文件不可用"}{entry.ambiguous ? " · 多个详情上下文" : ""}</span>
      <small>{entry.startedAt ? `${entry.timeKind === "file" ? "文件时间 · " : ""}${new Date(entry.startedAt).toLocaleString("zh-CN", { hour12: false })}` : "时间未提供"}</small>
    </button>
    <label className="library-compare-check"><input type="checkbox" checked={checked} disabled={!entry.available && !checked} onChange={() => onCompare(entry.id)} />选择比较</label>
  </article>;
}

export function VideoLibraryRail({ entries = [], selectedId, compareIds = [], onSelect, onCompare, measurements = {}, onMeasured }) {
  const [page, setPage] = useState(0);
  const pageSize = 12;
  const last = Math.max(0, Math.ceil(entries.length / pageSize) - 1);
  const current = Math.min(page, last);
  return <>
    <div className="library-card-grid" aria-label="视频列表">
      {entries.slice(current * pageSize, (current + 1) * pageSize).map((entry) => <VideoCard key={entry.id} entry={entry} selected={entry.id === selectedId} checked={compareIds.includes(entry.id)} onSelect={onSelect} onCompare={onCompare} measurement={measurements[entry.id]} onMeasured={onMeasured} />)}
    </div>
    {!entries.length && <p className="library-empty">已加载范围内没有符合筛选的视频；扫描未完成时，结果仍会增加。</p>}
    <nav className="library-pagination" aria-label="视频分页"><button type="button" disabled={current === 0} onClick={() => setPage(current - 1)}>上一页</button><span>{current + 1} / {last + 1}</span><button type="button" disabled={current === last} onClick={() => setPage(current + 1)}>下一页</button></nav>
  </>;
}
