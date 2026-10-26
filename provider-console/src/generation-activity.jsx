import React from "react";
import { attemptId } from "./run-detail-contract.js";
import { libraryLifecycle } from "./library-contract.js";

export function generationActivity(details) {
  return details.flatMap((detail) => detail.status === "valid"
    ? (detail.attempts || []).map((attempt, index) => ({
      workspace: detail.workspace, attemptId: attemptId(attempt, index),
      title: detail.project?.title || detail.run_id || detail.workspace,
      shot: attempt.target_shot_id || "Shot 未提供", attempt,
    })) : []).sort((a, b) => (Date.parse(b.attempt.started_at) || 0) - (Date.parse(a.attempt.started_at) || 0));
}

export function GenerationActivity({ details, loading, stale, onSelect }) {
  const items = generationActivity(details);
  // Show live generation separately from attempts awaiting media review. A
  // persisted running/validate state does not mean a Provider is generating.
  const generating = items.filter(({ attempt }) => attempt.status === "running"
    && ["request", "submit_intent", "submitted", "polling", "fetch"].includes(attempt.phase));
  const visible = generating.length ? generating : items.slice(0, 4);
  return <section className="generation-activity" aria-label="当前 Shot 动态">
    <header><strong>当前 Shot 动态</strong><span role="status">{stale ? "更新未确认 · 保留的状态可能已过期" : loading ? "正在同步生成状态…" : generating.length ? `${generating.length} 个 Shot 执行中` : "已加载记录中没有生成中的 Shot"}</span></header>
    <div className="generation-activity-list">{visible.map((item) => <button type="button" key={`${item.workspace}:${item.attemptId}`} onClick={() => onSelect(item)}>
      <strong>{item.shot} · {item.title}</strong>
      <span>{libraryLifecycle(item.attempt)}</span>
      <small>{item.attempt.started_at ? new Date(item.attempt.started_at).toLocaleString("zh-CN", { hour12: false }) : "时间未提供"} · {item.workspace}</small>
    </button>)}</div>
    {!visible.length && <p>尚未读取到可验证的生成记录。未产出视频的 Shot 也会在这里显示。</p>}
  </section>;
}
