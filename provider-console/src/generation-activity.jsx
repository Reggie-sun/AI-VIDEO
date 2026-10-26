import React from "react";
import { attemptId } from "./run-detail-contract.js";
import { libraryLifecycle } from "./library-contract.js";
import { ReferenceMedia } from "./reference-media.jsx";

export function generationActivity(details) {
  return details.flatMap((detail) => detail.status === "valid"
    ? (detail.attempts || []).map((attempt, index) => ({
      workspace: detail.workspace, attemptId: attemptId(attempt, index),
      title: detail.project?.title || detail.run_id || detail.workspace,
      shot: attempt.target_shot_id || "Shot 未提供", attempt,
    })) : []).sort((a, b) => (Date.parse(b.attempt.started_at) || 0) - (Date.parse(a.attempt.started_at) || 0));
}

export function recentActivity(items, preparations = []) {
  const preparing = preparations.filter((item) => item.kind === "local_preparation" && item.binding_status === "unbound_local_files")
    .map((preparation) => ({ kind: "local_preparation", preparation, title: preparation.run_id, shot: preparation.directory_name, updatedAt: preparation.updated_at }));
  return [...items.map((item) => ({ ...item, updatedAt: item.attempt.started_at })), ...preparing]
    .sort((a, b) => (Date.parse(b.updatedAt) || 0) - (Date.parse(a.updatedAt) || 0));
}

export function PreparationActivityDetail({ preparation }) {
  if (!preparation) return <p>这组准备材料已不在当前扫描范围，请刷新或选择其他记录。</p>;
  return <section className="shot-reference-section" aria-label="本地参考准备">
    <h2>{preparation.directory_name} · 本地参考准备</h2>
    <p>参考素材已落盘 · 未关联生成请求。目录名称仅用于定位，不代表已登记的 Shot 或模型执行状态。</p>
    <p>{preparation.source_directory}</p>
    <p>最近素材更新时间：{new Date(preparation.updated_at).toLocaleString("zh-CN", { hour12: false })}</p>
    <div className="shot-reference-grid">{(preparation.references || []).map((ref) => <article key={ref.relative_path}>
      <ReferenceMedia media={ref.media} label={ref.file_name} /><strong>{ref.file_name}</strong><small>本地准备素材 · 未验证用途绑定</small>
    </article>)}</div>
    {preparation.references_truncated && <p>部分素材超出扫描范围或暂不可读，当前展示不完整。</p>}
  </section>;
}

export function GenerationActivity({ details, preparations = [], preparationsTruncated = false, loading, stale, onSelect }) {
  const items = generationActivity(details);
  // Show live generation separately from attempts awaiting media review. A
  // persisted running/validate state does not mean a Provider is generating.
  const generating = items.filter(({ attempt }) => attempt.status === "running"
    && ["request", "submit_intent", "submitted", "polling", "fetch"].includes(attempt.phase));
  const recent = recentActivity(items, preparations);
  const visible = generating.length ? [...generating, ...recent.filter((item) => item.kind === "local_preparation").slice(0, 2)] : recent.slice(0, 4);
  return <section className="generation-activity" aria-label="当前 Shot 动态">
    <header><strong>当前 Shot 动态</strong><span role="status">{stale ? "更新未确认 · 保留的状态可能已过期" : loading ? "正在同步生成状态…" : generating.length ? `${generating.length} 个 Shot 执行中` : "已加载记录中没有生成中的 Shot"}{preparations.length > 0 && ` · ${preparations.length} 组本地参考准备`}</span></header>
    <div className="generation-activity-list">{visible.map((item) => <button type="button" key={item.preparation?.id || `${item.workspace}:${item.attemptId}`} onClick={() => onSelect(item)}>
      <strong>{item.shot} · {item.title}</strong>
      <span>{item.kind === "local_preparation" ? "本地参考准备 · 未关联生成请求" : libraryLifecycle(item.attempt)}</span>
      <small>{item.kind === "local_preparation" ? `${new Date(item.updatedAt).toLocaleString("zh-CN", { hour12: false })} · ${item.preparation.references.length} 张参考素材 · ${item.preparation.source_directory}` : `${item.attempt.started_at ? new Date(item.attempt.started_at).toLocaleString("zh-CN", { hour12: false }) : "时间未提供"} · ${item.workspace}`}</small>
    </button>)}</div>
    {!visible.length && <p>尚未读取到可验证的生成记录。未产出视频的 Shot 也会在这里显示。</p>}
    {preparationsTruncated && <p>本地参考准备扫描不完整：部分目录或素材超限、变更或不可读。</p>}
  </section>;
}
