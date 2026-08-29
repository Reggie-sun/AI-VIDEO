import { ArrowsClockwise, CheckCircle, Info, WarningCircle } from "@phosphor-icons/react";

import { attemptId, attemptOutcome, generationTypeOf, outputState, providerOf } from "./run-detail-contract.js";
import {
  externalDisplayMetadata,
  externalEvidenceFilterOptions,
  externalGroupTitle,
  externalSourceOptions,
  externalStatus,
  groupMatchesEvidenceFilter,
  groupMatchesQuery,
  groupMatchesSource,
  preferredExternalLocation,
  sortExternalGroupsNewest,
  sourceLabel,
} from "./external-media-contract.js";
import {
  resolveVideoSourceSelection,
  videoSourceIsRefreshing,
  videoSourceSelectionValue,
} from "./video-library-source-contract.js";

function workspaceDirectory(item) {
  return item?.run_id || String(item?.workspace || "").split("/")[0] || "未知工作区";
}

function workspaceDetail(item) {
  const directory = workspaceDirectory(item);
  const prefix = `${directory}/`;
  return item?.workspace?.startsWith(prefix) ? item.workspace.slice(prefix.length) : (item?.workspace || "workspace 未标注");
}

function WorkspaceOption({ item, selected, disabled, onSelect }) {
  const kind = String(item?.kind || "workspace").toUpperCase();
  return (
    <button type="button" aria-pressed={selected} className={`lane-option${selected ? " is-selected" : ""}`} disabled={disabled} onClick={() => onSelect(item.workspace)}>
      <span className="lane-option-top"><strong>{workspaceDirectory(item)}</strong><span className="provider-badge provider-badge--unknown">{kind}</span><span className={`lane-radio${selected ? " is-checked" : ""}`} /></span>
      <span className="lane-option-sub">{workspaceDetail(item)}</span>
    </button>
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
  evidenceFilter = "linked",
  externalLoading,
  externalError,
  runsContextLoading,
  runsContextError,
  activeSurface,
  liveStatus,
  onWorkspace,
  onSelectAttempt,
  onSelectExternal,
  onSource,
  onQuery,
  onEvidenceFilter = () => {},
  onRefresh,
}) {
  const sources = externalCatalog?.sources || [];
  const groups = externalCatalog?.groups || [];
  const showRuns = selectedSource === "all" || selectedSource === "runs";
  const showExternal = selectedSource !== "runs";
  const sourceGroups = showExternal
    ? groups.filter((group) => groupMatchesSource(group, selectedSource))
    : [];
  const visible = sortExternalGroupsNewest(
    sourceGroups
      .filter((group) => groupMatchesEvidenceFilter(group, evidenceFilter))
      .filter((group) => groupMatchesQuery(group, query)),
    selectedSource,
  );
  const evidenceOptions = externalEvidenceFilterOptions(sourceGroups);
  const sourceOptions = externalSourceOptions(externalCatalog).slice(1);
  const selectedSourceValue = videoSourceSelectionValue(selectedSource);
  const currentWorkspace = runsCatalog.find((item) => item.workspace === workspace);
  const otherWorkspaces = runsCatalog.filter((item) => item.workspace !== workspace);
  const changeSource = (value) => {
    const selection = resolveVideoSourceSelection(value);
    onSource(selection.sourceId);
  };
  const refreshing = videoSourceIsRefreshing(selectedSource, runsLoading, externalLoading);
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
        <select id="video-source-select" name="video-source" value={selectedSourceValue} onChange={(event) => changeSource(event.target.value)} aria-label="选择视频来源">
          <option value="all">全部视频来源</option>
          <optgroup label="视频目录">
            <option value="runs">Runs</option>
            {sourceOptions.map((option) => <option key={option.id} value={option.id} disabled={option.disabled}>{option.label}</option>)}
          </optgroup>
        </select>
      </div>
      {showExternal && <label className="external-evidence-filter" htmlFor="external-evidence-filter"><span>证据状态</span><select id="external-evidence-filter" name="external-evidence-filter" value={evidenceFilter} onChange={(event) => onEvidenceFilter(event.target.value)}>{evidenceOptions.map((option) => <option key={option.id} value={option.id}>{option.label} ({option.count})</option>)}</select></label>}
      {showExternal && <label className="external-search" htmlFor="external-media-search"><span>筛选视频</span><input id="external-media-search" name="external-media-search" type="search" value={query} onChange={(event) => onQuery(event.target.value)} placeholder="文件名 / Shot / Prompt" /><small>{visible.length} / {sourceGroups.length} unique SHA</small></label>}
      {showExternal && runsContextLoading && <div className="runs-context-status" role="status">正在按 exact SHA + bytes 关联 Runs Prompt 与 Shot…</div>}
      {showExternal && runsContextError && <div className="rail-stale-warning" role="status"><WarningCircle size={16} weight="fill" /><span>{runsContextError}</span></div>}
      {showExternal && externalError && <div className="rail-stale-warning" role="status"><WarningCircle size={16} weight="fill" /><span>刷新失败；当前外部视频列表可能已过期。</span></div>}
      <div className="lane-list external-group-list" aria-label="视频与生成尝试列表">
        {selectedSource === "runs" && currentWorkspace && <><div className="rail-section-heading"><span>RUNS · 当前工作区</span><b>目录详情</b></div><WorkspaceOption item={currentWorkspace} selected={activeSurface === "runs"} disabled={runsLoading} onSelect={onWorkspace} /></>}
        {showRuns && <div className="rail-section-heading"><span>RUNS · 当前工作区记录</span><b>{attempts.length} attempts</b></div>}
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
        {selectedSource === "runs" && <div className="rail-section-heading"><span>RUNS · 其他工作区</span><b>{otherWorkspaces.length} directories</b></div>}
        {selectedSource === "runs" && otherWorkspaces.map((item) => <WorkspaceOption key={item.workspace} item={item} selected={false} disabled={runsLoading} onSelect={onWorkspace} />)}
        {showExternal && <div className="rail-section-heading"><span>EXTERNAL · SHA 去重</span><b>{visible.length} videos</b></div>}
        {showExternal && visible.map((group) => {
          const status = externalStatus(group);
          const metadata = externalDisplayMetadata(group);
          const selected = activeSurface === "external" && group.sha256 === selectedSha;
          const location = preferredExternalLocation(group);
          const compositionShotCount = group.composition?.ordered_shots?.length || 0;
          return (
            <button type="button" key={group.sha256} aria-pressed={selected} className={`external-group-card external-group-card--${status.tone}${selected ? " is-selected" : ""}`} onClick={() => onSelectExternal(group.sha256)}>
              <span className="external-group-top"><strong title={externalGroupTitle(group)}>{externalGroupTitle(group)}</strong><span className={`provider-badge provider-badge--${status.tone}`}>{status.badge}</span></span>
              <span className="external-group-source">{sourceLabel(sources.find((source) => source.id === location?.source_id), location?.source_label)} · {(group.locations || []).length} 个位置</span>
              <span className="external-group-meta">{compositionShotCount ? `${compositionShotCount} Shots · 同目录声明` : `${metadata.shot_id || "Shot 未绑定"} · ${metadata.generation_type || metadata.shot_type || "类型未绑定"}`}</span>
              <span className="lane-option-prompt" title={metadata.prompt_text}>{compositionShotCount ? `已展开同项目目录声明的 ${compositionShotCount} 个 Shot` : (metadata.prompt_text || "没有与 exact bytes 绑定的 Prompt")}</span>
            </button>
          );
        })}
        {showExternal && !externalLoading && !visible.length && <div className={`rail-empty${externalError ? " rail-empty--error" : ""}`}><WarningCircle size={18} weight="fill" /><span>{externalError || (sourceGroups.length ? "没有符合当前证据状态或搜索条件的视频。" : "该来源没有可读取的视频。")}</span></div>}
      </div>
      <div className="lane-rail-note"><Info size={17} /><p>只读查看真实记录。<br />不提交、不重试、不自动回退。</p></div>
      <div className="local-status"><span className={`local-dot${liveStatus === "reconnecting" || liveStatus === "partial" ? " local-dot--reconnecting" : liveStatus === "unavailable" || liveStatus === "stale" ? " local-dot--unavailable" : ""}`} /><span>{liveLabel}<br />Server allowlist · 不暴露绝对路径</span></div>
    </aside>
  );
}
