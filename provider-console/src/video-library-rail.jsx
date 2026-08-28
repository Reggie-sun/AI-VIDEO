import React from "react";
import { ArrowsClockwise, CheckCircle, Info, WarningCircle } from "@phosphor-icons/react";

import { attemptId, attemptOutcome, generationTypeOf, outputState, providerOf } from "./run-detail-contract.js";
import {
  externalGroupTitle,
  externalSourceOptions,
  externalStatus,
  groupMatchesQuery,
  groupMatchesSource,
  preferredExternalLocation,
  sourceLabel,
} from "./external-media-contract.js";

function workspaceLabel(item) {
  if (!item?.workspace) return "未知工作区";
  const prefix = `${item.run_id}/`;
  const suffix = item.workspace.startsWith(prefix) ? item.workspace.slice(prefix.length) : item.workspace;
  return suffix === "project.yaml" || suffix === "manifest.json" ? item.run_id : `${item.run_id} · ${suffix.replace(/\/project\.yaml$/, "")}`;
}

function WorkspaceSelector({ catalog, selected, loading, onSelect, onRefresh }) {
  return (
    <div className="workspace-picker">
      <label htmlFor="workspace-select">runs 工作区</label>
      <div>
        <select id="workspace-select" value={selected} disabled={loading || !catalog.length} onChange={(event) => onSelect(event.target.value)}>
          {!catalog.length && <option value="">暂无工作区</option>}
          {catalog.map((item) => <option key={item.workspace} value={item.workspace}>{workspaceLabel(item)}</option>)}
        </select>
        <button type="button" onClick={onRefresh} disabled={loading} aria-label="刷新 runs 工作区"><ArrowsClockwise size={16} className={loading ? "is-spinning" : ""} /></button>
      </div>
      <small title={selected}>{selected || "仅连接本机 repository/runs"}</small>
    </div>
  );
}

export function VideoLibraryRail({
  runsCatalog,
  workspace,
  attempts,
  selectedId,
  runsLoading,
  runsError,
  externalCatalog,
  selectedSha,
  selectedSource,
  query,
  externalLoading,
  externalError,
  activeSurface,
  liveStatus,
  onWorkspace,
  onSelectAttempt,
  onSelectExternal,
  onSource,
  onQuery,
  onRefresh,
}) {
  const sources = externalCatalog?.sources || [];
  const groups = externalCatalog?.groups || [];
  const showRuns = selectedSource === "all" || selectedSource === "runs";
  const showExternal = selectedSource !== "runs";
  const sourceGroups = showExternal
    ? groups.filter((group) => groupMatchesSource(group, selectedSource))
    : [];
  const visible = sourceGroups.filter((group) => groupMatchesQuery(group, query));
  const sourceOptions = [
    { id: "all", label: "全部视频来源", count: attempts.length + groups.length, disabled: false },
    { id: "runs", label: "Runs 工作区", count: attempts.length, disabled: false },
    ...externalSourceOptions(externalCatalog).slice(1),
  ];
  const refreshing = runsLoading || externalLoading;
  const liveLabel = liveStatus === "live"
    ? "实时更新已连接"
    : liveStatus === "reconnecting"
      ? "实时更新重连中"
      : liveStatus === "partial"
        ? "部分来源未实时监视 · 可手动刷新"
        : liveStatus === "stale"
          ? "最近刷新失败 · 当前列表可能已过期"
          : liveStatus === "unavailable" ? "实时更新不可用 · 可手动刷新" : "正在连接实时更新";
  return (
    <aside className="lane-rail external-rail" aria-label="全部视频来源与生成记录">
      <header className="lane-rail-header"><h2>视频生成记录</h2><p>Runs + 外部媒体 · exact evidence</p></header>
      <div className="external-source-filter">
        <div className="external-filter-heading"><label htmlFor="video-source-select">来源</label><button type="button" onClick={onRefresh} disabled={refreshing} aria-label="刷新当前视频来源"><ArrowsClockwise size={15} className={refreshing ? "is-spinning" : ""} /></button></div>
        <select id="video-source-select" name="video-source" value={selectedSource} onChange={(event) => onSource(event.target.value)} aria-label="选择视频来源">
          {sourceOptions.map((option) => <option key={option.id} value={option.id} disabled={option.disabled}>{option.label} · {option.disabled ? "不可用" : option.count}</option>)}
        </select>
      </div>
      {showRuns && <WorkspaceSelector catalog={runsCatalog} selected={workspace} loading={runsLoading} onSelect={onWorkspace} onRefresh={onRefresh} />}
      {showExternal && <label className="external-search" htmlFor="external-media-search"><span>筛选视频</span><input id="external-media-search" name="external-media-search" type="search" value={query} onChange={(event) => onQuery(event.target.value)} placeholder="文件名 / Shot / Prompt" /><small>{visible.length} / {sourceGroups.length} unique SHA</small></label>}
      {showExternal && externalError && <div className="rail-stale-warning" role="status"><WarningCircle size={16} weight="fill" /><span>刷新失败；当前外部视频列表可能已过期。</span></div>}
      <div className="lane-list external-group-list" aria-label="视频与生成尝试列表">
        {showRuns && <div className="rail-section-heading"><span>RUNS · 当前工作区</span><b>{attempts.length} attempts</b></div>}
        {showRuns && attempts.map((attempt, index) => {
          const id = attemptId(attempt, index);
          const provider = providerOf(attempt);
          const selected = activeSurface === "runs" && id === selectedId;
          const outcome = attemptOutcome(attempt);
          const mediaState = outputState(attempt);
          return (
            <button key={id} type="button" aria-pressed={selected} className={`lane-option lane-option--${outcome.tone}${selected ? " is-selected" : ""}`} onClick={() => onSelectAttempt(id)}>
              <span className="lane-option-top"><strong>{provider.name || attempt.provider_name || provider.kind || attempt.provider_kind || "未标注 Provider"}</strong><span className={`provider-badge provider-badge--${outcome.tone}`}>{outcome.label}</span><span className={`lane-radio${selected ? " is-checked" : ""}`} /></span>
              <span className="lane-option-sub">{attempt.target_shot_id || "Shot 未标注"} · {generationTypeOf(attempt)} · phase {attempt.phase || "—"}</span>
              <span className={`lane-option-media lane-option-media--${mediaState.tone}`}>{mediaState.label}</span>
              <span className="lane-option-prompt" title={attempt.prompt_text}>{attempt.prompt_text || "该 request 没有可显示的 prompt"}</span>
            </button>
          );
        })}
        {showRuns && !runsLoading && !attempts.length && (runsError
          ? <div className="rail-empty rail-empty--error"><WarningCircle size={18} weight="fill" /><span>该工作区未通过 strict reopen；右侧显示稳定错误码。</span></div>
          : <div className="rail-empty"><CheckCircle size={18} weight="fill" /><span>当前工作区没有 video generation attempt；右侧仍展示 Project 全部 Shots。</span></div>)}
        {showExternal && <div className="rail-section-heading"><span>EXTERNAL · SHA 去重</span><b>{visible.length} videos</b></div>}
        {showExternal && visible.map((group) => {
          const status = externalStatus(group);
          const selected = activeSurface === "external" && group.sha256 === selectedSha;
          const location = preferredExternalLocation(group);
          const compositionShotCount = group.composition?.ordered_shots?.length || 0;
          return (
            <button type="button" key={group.sha256} aria-pressed={selected} className={`external-group-card external-group-card--${status.tone}${selected ? " is-selected" : ""}`} onClick={() => onSelectExternal(group.sha256)}>
              <span className="external-group-top"><strong title={externalGroupTitle(group)}>{externalGroupTitle(group)}</strong><span className={`provider-badge provider-badge--${status.tone}`}>{status.evaluated ? status.raw : "N/E"}</span></span>
              <span className="external-group-source">{sourceLabel(sources.find((source) => source.id === location?.source_id), location?.source_label)} · {(group.locations || []).length} 个位置</span>
              <span className="external-group-meta">{compositionShotCount ? `${compositionShotCount} Shots · 同目录声明` : `${group.shot_id || "Shot 未绑定"} · ${group.generation_type || group.shot_type || "类型未绑定"}`}</span>
              <span className="lane-option-prompt" title={group.prompt_text}>{compositionShotCount ? `已展开同项目目录声明的 ${compositionShotCount} 个 Shot` : (group.prompt_text || "没有与 exact bytes 绑定的 Prompt")}</span>
            </button>
          );
        })}
        {showExternal && !externalLoading && !visible.length && <div className={`rail-empty${externalError ? " rail-empty--error" : ""}`}><WarningCircle size={18} weight="fill" /><span>{externalError || "该来源没有可读取的视频。"}</span></div>}
      </div>
      <div className="lane-rail-note"><Info size={17} /><p>只读查看真实记录。<br />不提交、不重试、不自动回退。</p></div>
      <div className="local-status"><span className={`local-dot${liveStatus === "reconnecting" || liveStatus === "partial" ? " local-dot--reconnecting" : liveStatus === "unavailable" || liveStatus === "stale" ? " local-dot--unavailable" : ""}`} /><span>{liveLabel}<br />Server allowlist · 不暴露绝对路径</span></div>
    </aside>
  );
}
