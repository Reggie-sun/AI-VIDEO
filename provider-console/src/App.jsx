import React, { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import {
  ArrowSquareOut,
  ArrowsClockwise,
  CaretUp,
  CheckCircle,
  Circle,
  FileText,
  FilmStrip,
  FolderSimple,
  Gear,
  ImageSquare,
  Info,
  Monitor,
  Play,
  Question,
  SlidersHorizontal,
  UserCircle,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import { ContinuityReviewPanel, projectionMatchesTarget } from "./continuity-review.js";
import {
  attemptId,
  attemptOutcome,
  generationTypeOf,
  outputState,
  providerOf,
  shotForAttempt,
} from "./run-detail-contract.js";
import {
  attachRunsMediaIndex,
  externalDisplayMetadata,
  externalGroupTitle,
  externalMediaUrl,
  externalStatus,
  groupMatchesEvidenceFilter,
  groupMatchesQuery,
  groupMatchesSource,
  preferredExternalGroup,
  preferredExternalLocation,
  readExternalCatalogResponse,
  sourceLabel,
} from "./external-media-contract.js";
import { AudibleVideo } from "./media-player.jsx";
import { useLibraryLiveUpdates } from "./library-live-updates.js";
import { createLatestRequestGuard, createWorkspaceSelectionGuard, libraryLiveStatus } from "./library-refresh-contract.js";
import { ExternalShotBreakdown, ProjectShotBreakdown } from "./shot-breakdown.jsx";
import { shotTiming } from "./shot-time-contract.js";
import { VideoLibraryRail } from "./video-library-rail.jsx";

const NAV_ITEMS = [
  ["projects", "项目", FolderSimple],
  ["shots", "镜头", FilmStrip],
  ["assets", "素材", ImageSquare],
  ["ark", "Ark", SlidersHorizontal],
  ["providers", "提供商控制台", Monitor],
  ["runs", "执行记录", ArrowsClockwise],
  ["evidence", "证据", FileText],
  ["settings", "设置", Gear],
];

function text(value, fallback = "—") {
  return value === undefined || value === null || value === "" ? fallback : String(value);
}

function requestsCanCommit(selectionGuard, selectionToken, requestGuard, requestToken) {
  return selectionGuard.canCommit(selectionToken) && requestGuard.canCommit(requestToken);
}

function formatTime(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? text(value) : parsed.toLocaleString("zh-CN", { hour12: false });
}

function mediaUrl(media) {
  const token = media?.token || media?.media_token;
  return token ? `/api/runs/media/${encodeURIComponent(token)}` : null;
}

function outputOf(attempt) {
  return attempt?.effective_output || attempt?.output || {};
}

const INPUT_ROLE_LABELS = {
  first_frame: "首帧",
  last_frame: "尾帧",
  reference: "参考图",
  reference_video: "参考视频",
  reference_audio: "参考音频",
};

function inputRoleLabel(binding) {
  const mimeType = binding?.media?.mime_type || binding?.mime_type || "";
  if (binding?.role === "reference" && mimeType.startsWith("video/")) return "参考视频";
  return INPUT_ROLE_LABELS[binding?.role] || text(binding?.role, "输入素材");
}

function projectOf(detail) {
  return detail?.project || {};
}

function StatusIcon({ tone, size = 18 }) {
  if (tone === "ready") return <CheckCircle size={size} weight="fill" />;
  if (tone === "blocked") return <WarningCircle size={size} weight="fill" />;
  return <Circle size={size} />;
}

function Sidebar() {
  return (
    <nav className="sidebar" aria-label="主导航">
      <div className="brand"><Play size={22} weight="fill" /><span>AI-VIDEO</span></div>
      <ul className="nav-list">
        {NAV_ITEMS.map(([id, label, Icon]) => (
          <li key={id}><button type="button" className={`nav-item${id === "providers" ? " is-active" : ""}`} aria-current={id === "providers" ? "page" : undefined}><Icon size={17} /><span>{label}</span></button></li>
        ))}
      </ul>
      <div className="sidebar-bottom">
        <button type="button" className="operator-button"><span className="operator-avatar">OP</span><span>操作员</span><CaretUp size={12} /></button>
        <button type="button" className="nav-item help-button"><Question size={18} /><span>帮助</span></button>
      </div>
    </nav>
  );
}

function ShotSummary({ detail, attempt }) {
  const project = projectOf(detail);
  const shot = shotForAttempt(detail, attempt);
  const outcome = attempt ? attemptOutcome(attempt) : null;
  const imageInputs = (attempt?.input_bindings || []).filter((item) => {
    const mimeType = item?.media?.mime_type || item?.mime_type || "";
    return mimeType.startsWith("image/");
  });
  const firstInput = imageInputs.find((item) => item.role === "first_frame")?.media
    || imageInputs[0]?.media;
  const preview = mediaUrl(attempt?.first_frame_media || firstInput || attempt?.first_frame || attempt?.input_media);
  return (
    <header className="shot-summary">
      <div className="summary-project">
        {preview ? <img src={preview} alt="已注册首帧" /> : <div className="summary-placeholder"><ImageSquare size={24} /></div>}
        <div><span>项目</span><strong>{project.title || project.name || project.project_id || detail?.run_id || "未命名项目"}</strong></div>
      </div>
      <div className="summary-field"><span>镜头</span><strong>{shot.shot_id || shot.id || attempt?.target_shot_id || "—"}</strong></div>
      <div className="summary-field summary-field--wide"><span>生成类型</span><strong>{attempt ? generationTypeOf(attempt) : (detail?.kind === "legacy" ? "Legacy" : "Production")}</strong></div>
      <div className={`summary-field summary-field--${outcome?.tone || "gated"}`}><span>结果</span><strong>{outcome ? `${outcome.label} · ${attempt?.status || "—"}` : (detail?.status || "—")}</strong></div>
      <div className="summary-field summary-field--updated"><span>更新时间</span><strong>{formatTime(attempt?.finished_at || attempt?.started_at || detail?.updated_at)}</strong></div>
    </header>
  );
}

function Fact({ label, value }) {
  return <div><dt>{label}</dt><dd>{text(value)}</dd></div>;
}

function formatDirective(directive) {
  const parameters = directive?.parameters || {};
  const values = Object.entries(parameters).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : text(value)}`);
  return values.length ? values.join(" · ") : "未记录参数";
}

function StoryboardList({ label, values }) {
  if (!values?.length) return null;
  return <div className="storyboard-list"><span>{label}</span><div>{values.map((value, index) => <code key={`${label}-${index}`}>{text(value)}</code>)}</div></div>;
}

function ShotStoryboard({ shot, attempt }) {
  const outcome = attemptOutcome(attempt);
  const snapshotAvailable = shot?.snapshot_available !== false;
  const timing = shotTiming(shot);
  const directives = shot?.motion_directives || [];
  return (
    <section className={`storyboard-card storyboard-card--${outcome.tone}`} aria-label="生成当时的 Shot 分镜脚本">
      <header className="storyboard-heading">
        <div><span>Shot Storyboard</span><h3>{shot?.shot_id || attempt?.target_shot_id || "未命名 Shot"}</h3></div>
        <div className="storyboard-badges"><span>{generationTypeOf(attempt)}</span><span>{shot?.visual_strategy || "策略未记录"}</span><span className={`storyboard-outcome storyboard-outcome--${outcome.tone}`}>{outcome.label}</span></div>
      </header>
      {!snapshotAvailable ? (
        <div className="storyboard-unavailable"><WarningCircle size={20} weight="fill" /><div><strong>历史 Shot snapshot 无法严格重开</strong><p>仅保留 sealed binding：revision {text(shot?.revision)} · content {text(shot?.content_hash).slice(0, 16)}。下方 Prompt 仍来自 exact request receipt；本页不会用当前 active Shot 冒充生成当时的分镜。</p></div></div>
      ) : (
        <>
          <dl className="storyboard-facts">
            <Fact label="Scene" value={shot?.scene_id} />
            <Fact label="Storyboard beat" value={shot?.storyboard_beat_id} />
            <Fact label="分镜策略" value={shot?.visual_strategy} />
            <Fact label={timing.label} value={timing.value} />
            <Fact label="Shot revision" value={shot?.revision} />
          </dl>
          <div className="storyboard-copy"><span>画面意图</span><p>{shot?.intent || "未记录画面意图"}</p></div>
          {(shot?.dialogue || shot?.narration) && <div className="storyboard-script-grid">
            <div><span>对白</span><p>{shot?.dialogue || "无"}</p></div>
            <div><span>旁白</span><p>{shot?.narration || "无"}</p></div>
          </div>}
          <StoryboardList label="Characters" values={shot?.character_ids} />
          <StoryboardList label="Continuity" values={shot?.continuity_constraints} />
          {directives.length > 0 && <div className="storyboard-directives"><span>Motion directives</span><div>{directives.map((directive, index) => <article key={`${directive.kind || "motion"}-${index}`}><strong>{directive.kind || "motion"}</strong><p>{formatDirective(directive)}</p></article>)}</div></div>}
          {shot?.generated_video_rationale && <div className="storyboard-rationale"><span>生成视频理由</span><p>{shot.generated_video_rationale}</p></div>}
          <p className="storyboard-schema-note">“分镜策略”与“生成类型”来自结构化 contract；当前 schema 没有独立景别字段，因此不会从 Prompt 猜测近景、广角或跟拍类型。</p>
        </>
      )}
    </section>
  );
}

function BindingMediaCard({ binding }) {
  const media = binding?.media;
  const url = mediaUrl(media);
  const label = inputRoleLabel(binding);
  const isVideo = (media?.mime_type || binding?.mime_type || "").startsWith("video/");
  return (
    <article className="binding-card">
      <header><span>{label}</span><code>{binding?.role || "input"}</code></header>
      {url ? (isVideo
        ? <AudibleVideo compact src={url} preload="metadata" aria-label={`${label} ${binding?.asset_id || ""}`} />
        : <img src={url} alt={`${label} ${binding?.asset_id || ""}`} />)
        : <div className="binding-media-empty"><ImageSquare size={22} /><span>已绑定，暂无浏览器预览</span></div>}
      <div className="binding-meta">
        <strong title={binding?.asset_id}>{binding?.asset_id || media?.asset_id || "已注册输入"}</strong>
        <span>{media?.mime_type || binding?.mime_type || "MIME 未标注"}</span>
      </div>
    </article>
  );
}

function OutputMediaCard({ media, state }) {
  const url = mediaUrl(media);
  if (!url) return <div className={`media-empty media-empty--${state.tone}`}><ImageSquare size={24} /><p>{state.label}</p></div>;
  const fetchedOnly = media?.source_kind === "fetched_evidence";
  return (
    <div className="asset-card asset-card--real">
      <AudibleVideo compact src={url} preload="metadata" aria-label={fetchedOnly ? "严格验证的 fetched 生成视频" : "已注册 candidate 生成视频"} />
      <div className="asset-details">
        <p>视频：<code>{media.asset_id || (fetchedOnly ? "fetched evidence" : "已注册 candidate")}</code></p>
        <p>{media.mime_type || "MIME 未标注"} · {media.bytes ? `${media.bytes.toLocaleString("zh-CN")} bytes` : "大小未标注"}</p>
        <p>{[media.width, media.height].every(Boolean) ? `${media.width} × ${media.height}` : "尺寸未标注"}</p>
        <p className={`asset-ok asset-ok--${state.tone}`}><StatusIcon tone={state.tone} size={15} />{state.label}</p>
        {fetchedOnly && <p className="asset-boundary">Exact fetch bytes；不表示 candidate、QA acceptance 或 activation。</p>}
      </div>
    </div>
  );
}

function ModeInputPanel({ attempt }) {
  const inputs = attempt?.input_bindings || [];
  const generationType = generationTypeOf(attempt);
  return (
    <div className="mode-input-panel">
      <div className="mode-input-heading"><span className="generation-badge">{generationType}</span><code>{attempt?.mode || providerOf(attempt).mode || "mode 未标注"}</code></div>
      <div className="prompt-panel"><span>Prompt</span><p>{attempt?.prompt_text || "该历史 request 没有可显示的 prompt。"}</p></div>
      {inputs.length
        ? <div className="binding-grid">{inputs.map((binding, index) => <BindingMediaCard key={`${binding.role || "input"}-${binding.asset_id || index}`} binding={binding} />)}</div>
        : <div className="text-only-input"><FileText size={20} /><span>{generationType === "T2V" ? "T2V 仅使用文本 Prompt，不需要图像输入。" : "该 request 没有 image/media binding。"}</span></div>}
      {attempt?.input_bindings_truncated && <p className="input-truncated-note">输入素材仅展示前 32 项。</p>}
    </div>
  );
}

function MediaCard({ attempt }) {
  const media = attempt?.candidate_media || attempt?.fetched_media || attempt?.output_media || attempt?.video_media;
  const state = outputState(attempt);
  return <div className="attempt-media"><ModeInputPanel attempt={attempt} /><div className="output-media"><span>生成视频</span><OutputMediaCard media={media} state={state} /></div></div>;
}

function WorkspaceMediaThumb({ item }) {
  const [failed, setFailed] = useState(false);
  const url = mediaUrl(item);
  const video = (item.mime_type || "").startsWith("video/");
  if (failed) return <div className="workspace-media-unavailable"><ImageSquare size={22} /><span>浏览器无法解码</span></div>;
  return video
    ? <AudibleVideo compact src={url} preload="none" aria-label={`已注册视频 ${item.asset_id || ""}`} onError={() => setFailed(true)} />
    : <img src={url} alt={`已注册图片 ${item.asset_id || ""}`} onError={() => setFailed(true)} />;
}

function WorkspaceMediaGrid({ media = [], limit = 12 }) {
  const visible = media.slice(0, limit);
  if (!visible.length) return <div className="workspace-media-empty"><ImageSquare size={22} /><span>没有可预览的 canonical Registry image/video。</span></div>;
  return (
    <div className="workspace-media-grid">
      {visible.map((item) => {
        return (
          <article className="workspace-media-item" key={item.token || item.asset_id}>
            <WorkspaceMediaThumb item={item} />
            <div><strong title={item.asset_id}>{item.asset_id || "已注册媒体"}</strong><span>{item.mime_type || "MIME 未标注"}{item.width && item.height ? ` · ${item.width} × ${item.height}` : ""}</span></div>
          </article>
        );
      })}
    </div>
  );
}

function WorkspaceOverview({ detail, projectShotsContent }) {
  const shots = detail?.shots || [];
  const operations = detail?.operation_summary || [];
  const media = detail?.workspace_media || [];
  const firstMediaUrl = mediaUrl(media[0]);
  return (
    <>
      <section className="workspace-overview">
        <header className="workspace-overview-heading">
          <div><CheckCircle size={28} weight="fill" /><div><h1>工作区已严格读取</h1><p>这里没有 video generation attempt，但 Project、Shots、Manifest operations 与已注册媒体仍可查看。</p></div></div>
          <span className="ready-tag">只读</span>
        </header>
        <div className="workspace-overview-stats">
          <div><span>工作区类型</span><strong>{text(detail?.kind)}</strong></div>
          <div><span>Manifest 版本</span><strong>{text(detail?.manifest?.revision)}</strong></div>
          <div><span>镜头</span><strong>{shots.length}</strong></div>
          <div><span>Registry 媒体</span><strong>{media.length}{detail?.workspace_media_truncated ? "+" : ""}</strong></div>
        </div>
        {projectShotsContent}
        <section className="workspace-overview-section">
          <h2>Manifest 操作</h2>
          <div className="operation-list">
            {operations.length ? operations.map((item) => <span key={item.operation}><code>{item.operation}</code><b>{item.count}</b></span>) : <p>该 Manifest 尚未记录 lifecycle operation。</p>}
          </div>
        </section>
        <section className="workspace-overview-section">
          <h2>Registry 已注册媒体</h2>
          <WorkspaceMediaGrid media={media} limit={32} />
          {detail?.workspace_media_truncated && <p className="workspace-media-note">仅展示前 32 个已验证 image/video；其余项目保持未加载。</p>}
        </section>
      </section>
      <section className="action-bar workspace-action-bar">
        <div className="action-note">已读取 · 未创建 Provider intent <Info size={16} /></div>
        <a className={`primary-action${firstMediaUrl ? "" : " is-disabled"}`} href={firstMediaUrl || undefined} target="_blank" rel="noreferrer" aria-disabled={!firstMediaUrl}><Play size={20} weight="fill" />查看首个已注册媒体</a>
        <div className="secondary-action workspace-read-state"><CheckCircle size={18} weight="fill" />{detail?.status === "valid" ? "Strict reopen 通过" : text(detail?.status)}</div>
      </section>
    </>
  );
}

function DetailPane({ detail, attempt, onEvidence, continuityContent, projectShotsContent }) {
  const provider = providerOf(attempt);
  const output = outputOf(attempt);
  const shot = shotForAttempt(detail, attempt);
  const outcome = attemptOutcome(attempt);
  const mediaState = outputState(attempt);
  const media = attempt?.candidate_media || attempt?.fetched_media || attempt?.output_media || attempt?.video_media;
  const tone = outcome.tone;
  const title = provider.name || attempt?.provider_name || provider.kind || attempt?.provider_kind || "Provider attempt";
  const evidence = attempt?.evidence || attempt?.request_evidence || {};
  return (
    <>
      <section className="details-grid">
        <div className="readiness-pane">
          <header className="lane-heading">
            <div><h1>{title}</h1><span className={`provider-badge provider-badge--${tone}`}>{outcome.label}</span></div>
            <p>{attemptId(attempt, 0)} · 来自 canonical Production/Legacy reader</p>
            <span className="manual-note">真实 runs 记录 · 不自动回退 <Info size={17} /></span>
          </header>
          <div className="readiness-copy"><h2>记录链</h2><p>以下字段来自严格 reopen 后的白名单投影，不代表新的执行授权。</p></div>
          <ol className="sequence-list">
            <li className="sequence-step"><div className="sequence-marker sequence-marker--ready"><StatusIcon tone="ready" size={24} /><span className="sequence-line" /></div><div className="sequence-content"><div className="sequence-title-row"><h4>1. 工作区已严格打开</h4><span className="ready-tag">只读</span></div><p className="step-description">{detail.workspace} · Manifest revision {text(detail.manifest_revision || detail.manifest?.revision)}</p></div></li>
            <li className="sequence-step sequence-step--storyboard"><div className={`sequence-marker sequence-marker--${shot.snapshot_available === false ? "gated" : "ready"}`}><StatusIcon tone={shot.snapshot_available === false ? "gated" : "ready"} size={24} /><span className="sequence-line" /></div><div className="sequence-content"><div className="sequence-title-row"><h4>2. 生成当时的 Shot 分镜</h4><span className={`ready-tag ready-tag--${shot.snapshot_available === false ? "gated" : "ready"}`}>{shot.snapshot_available === false ? "历史快照不可用" : "Exact snapshot"}</span></div><p className="step-description">Target Shot：{shot.shot_id || shot.id || attempt?.target_shot_id || "—"}</p><ShotStoryboard shot={shot} attempt={attempt} /></div></li>
            <li className="sequence-step sequence-step--media"><div className={`sequence-marker sequence-marker--${mediaState.tone}`}><StatusIcon tone={mediaState.tone} size={24} /><span className="sequence-line" /></div><div className="sequence-content"><div className="sequence-title-row"><h4>3. 实际提交 Prompt 与视频</h4><span className={`ready-tag ready-tag--${mediaState.tone}`}>{mediaState.label}</span></div><MediaCard attempt={attempt} /></div></li>
            <li className="sequence-step"><div className={`sequence-marker sequence-marker--${tone}`}><StatusIcon tone={tone} size={24} /></div><div className="sequence-content"><div className="sequence-title-row"><h4>4. Attempt lifecycle</h4><span className={`ready-tag ready-tag--${tone}`}>{outcome.label}</span></div><p className="step-description">Raw status：{attempt?.status || "—"} · phase：{attempt?.phase || "—"}{attempt?.error_code ? ` · error code：${attempt.error_code}` : ""}</p><div className={`intent-box intent-box--${tone}`}><Info size={20} /><div><strong>状态不等于质量验收</strong><p>“成功”只表示该 lifecycle 已成功结束；fetched video、candidate、QA acceptance 与 activation 会分别标注。控制台不会推进任何状态。</p></div></div></div></li>
          </ol>
          {continuityContent}
          {projectShotsContent}
        </div>
        <aside className="detail-aside">
          <section className="detail-section"><h3>Attempt lifecycle</h3><dl className="identity-list"><Fact label="结果" value={`${outcome.label} · ${attempt?.status || "—"}`} /><Fact label="Phase" value={attempt?.phase} /><Fact label="Error code" value={attempt?.error_code} /><Fact label="Started" value={formatTime(attempt?.started_at)} /><Fact label="Finished" value={formatTime(attempt?.finished_at)} /><Fact label="视频状态" value={mediaState.label} /></dl></section>
          <section className="detail-section"><h3>Provider 身份</h3><dl className="identity-list"><Fact label="生成类型" value={generationTypeOf(attempt)} /><Fact label="原始 mode" value={attempt?.mode || provider.mode} /><Fact label="名称" value={provider.name || attempt?.provider_name} /><Fact label="Kind" value={provider.kind || attempt?.provider_kind} /><Fact label="Model" value={provider.model || attempt?.model} /><Fact label="Profile" value={provider.profile || attempt?.profile} /><Fact label="Capability" value={provider.capability || attempt?.capability} /></dl></section>
          <section className="detail-section"><h3>请求输出规格</h3><dl className="identity-list"><Fact label="分辨率" value={output.width && output.height ? `${output.width} × ${output.height}` : output.resolution} /><Fact label="帧数" value={output.frame_count || output.frames} /><Fact label="帧率" value={output.fps ? `${output.fps} fps` : undefined} /><Fact label="时长" value={output.duration_seconds ? `${output.duration_seconds}s` : undefined} /><Fact label="音频" value={output.native_audio === true ? "原生音频" : output.native_audio === false ? "无原生音频" : output.audio} /></dl></section>
          <section className="detail-section"><h3>Evidence</h3><dl className="identity-list"><Fact label="Request" value={evidence.path || evidence.request_pointer || attempt?.request_pointer} /><Fact label="Fingerprint" value={evidence.request_receipt_fingerprint || evidence.resolved_generation_hash} /><Fact label="File hash" value={evidence.file_sha256 || evidence.content_hash || attempt?.request_hash} /></dl><button type="button" className="evidence-button" onClick={onEvidence}>查看白名单证据 <ArrowSquareOut size={17} /></button></section>
        </aside>
      </section>
      <section className="action-bar">
        <div className="action-note">本机只读 · 无 Provider 调用 <Info size={16} /></div>
        <a className={`primary-action${mediaUrl(media) ? "" : " is-disabled"}`} href={mediaUrl(media) || undefined} target="_blank" rel="noreferrer" aria-disabled={!mediaUrl(media)}><Play size={20} weight="fill" />查看可播放视频</a>
        <button type="button" className="secondary-action" onClick={onEvidence}>查看证据 <ArrowSquareOut size={18} /></button>
      </section>
    </>
  );
}

export function RunsAttemptView({
  detail,
  attempt,
  selectedAttemptId,
  onSelectAttempt,
  onEvidence,
  continuityContent,
}) {
  const projectShotsContent = (
    <ProjectShotBreakdown
      detail={detail}
      selectedAttemptId={selectedAttemptId}
      onSelectAttempt={onSelectAttempt}
    />
  );
  return (
    <>
      <ShotSummary detail={detail} attempt={attempt} />
      <DetailPane
        detail={detail}
        attempt={attempt}
        onEvidence={onEvidence}
        continuityContent={continuityContent}
        projectShotsContent={projectShotsContent}
      />
    </>
  );
}

export function RunsWorkspaceView({ detail, selectedAttemptId, onSelectAttempt }) {
  const projectShotsContent = (
    <ProjectShotBreakdown
      detail={detail}
      selectedAttemptId={selectedAttemptId}
      onSelectAttempt={onSelectAttempt}
    />
  );
  return (
    <>
      <ShotSummary detail={detail} />
      <WorkspaceOverview detail={detail} projectShotsContent={projectShotsContent} />
    </>
  );
}

function formatBytes(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) return "—";
  if (numeric >= 1024 ** 3) return `${(numeric / (1024 ** 3)).toFixed(2)} GiB`;
  if (numeric >= 1024 ** 2) return `${(numeric / (1024 ** 2)).toFixed(1)} MiB`;
  if (numeric >= 1024) return `${(numeric / 1024).toFixed(1)} KiB`;
  return `${numeric} bytes`;
}

function ExternalSummary({ group, sources }) {
  const location = preferredExternalLocation(group);
  const source = sources.find((item) => item.id === location?.source_id);
  const status = externalStatus(group);
  const metadata = externalDisplayMetadata(group);
  const compositionShotCount = group.composition?.ordered_shots?.length || 0;
  const typeLabel = compositionShotCount ? "Shot 信息" : metadata.generation_type ? "生成类型" : metadata.shot_type ? "Shot 类型" : "生成类型";
  const typeValue = compositionShotCount ? `同目录 Shot 计划 · ${compositionShotCount}` : (metadata.generation_type || metadata.shot_type || "NOT_EVALUATED");
  return (
    <header className="shot-summary external-summary">
      <div className="summary-project external-summary-title"><div><span>外部媒体</span><strong title={externalGroupTitle(group)}>{externalGroupTitle(group)}</strong></div></div>
      <div className="summary-field"><span>首选来源</span><strong>{sourceLabel(source, location?.source_label)}</strong></div>
      <div className="summary-field summary-field--wide"><span>{typeLabel}</span><strong>{typeValue}</strong></div>
      <div className={`summary-field summary-field--${status.tone}`}><span>生成状态</span><strong>{status.label}</strong></div>
      <div className="summary-field summary-field--updated"><span>文件时间</span><strong>{formatTime(group.modified_at || location?.modified_at)}</strong></div>
    </header>
  );
}

function ExternalMediaDetail({ group, sources }) {
  const url = externalMediaUrl(group);
  const status = externalStatus(group);
  const metadata = externalDisplayMetadata(group);
  const locations = group.locations || [];
  const evidenceRefs = group.evidence_refs || [];
  const hasBoundMetadata = metadata.source !== "none";
  const hasComposition = (group.composition?.ordered_shots?.length || 0) > 0;
  const hasExactShotEvidence = (group.shot_evidence?.length || 0) > 0;
  const hasRunsContext = metadata.source === "runs_exact_sha";
  return (
    <>
      <section className="external-detail-grid">
        <div className="external-detail-main">
          <header className="external-boundary-heading">
            <div><span>External Media Evidence</span><h1>同一视频的可验证信息</h1><p>按 exact SHA-256 合并重复文件；来源与 sidecar 证据保留，但不冒充 Production lifecycle。</p></div>
            <span className="external-proof-badge">NON-CANONICAL</span>
          </header>
          <div className="external-preview-wrap">
            {url ? <AudibleVideo src={url} preload="metadata" aria-label={`外部视频 ${externalGroupTitle(group)}`} /> : <div className="media-empty"><FilmStrip size={28} /><p>该文件当前无法安全预览。</p></div>}
          </div>
          <section className={`external-status-callout external-status-callout--${status.tone}`}>
            <StatusIcon tone={status.tone} size={21} />
            <div><strong>{status.label}</strong><p>{status.ambiguous ? "同一视频 bytes 关联到互相冲突的 exact evidence；不会选择最新记录或猜测语义。" : status.evaluated ? "状态来自受支持且经 exact identity 绑定的证据链；它不是 Manifest attempt、candidate 或质量验收。" : metadata.source === "runs_exact_sha" ? "Prompt、生成类型与可用的 Shot snapshot 来自 canonical Runs 的 exact SHA-256 + bytes 关联；External generation status 仍保持 NOT_EVALUATED。" : status.raw === "INCOMPLETE_RUNS_CONTEXT" ? "Runs context 正在加载、当前不可用或部分 workspace 无法严格重开；该视频没有已确认 match，但不能据此断言完全没有绑定。" : status.evidence_state === "incomplete" ? "已找到 exact-bound evidence ref，但 schema 或完整关联链不足，因此不会解释其中的 Prompt、Shot 或状态。" : "没有找到语义受支持且与 exact bytes 绑定的生成记录，因此不会把文件名或文件存在解释为 Prompt、Shot 或成功状态。"}</p></div>
          </section>
          <ExternalShotBreakdown group={group} />
          {!hasComposition && !hasExactShotEvidence && !hasRunsContext && <section className="external-storyboard-card">
            <header><div><span>Shot / Prompt</span><h2>{metadata.shot_id || "Shot 未绑定"}</h2></div><span>{metadata.generation_type || metadata.shot_type || "类型未评估"}</span></header>
            <div className="external-prompt"><span>Prompt</span><p>{metadata.prompt_text || "没有与该视频 exact path / SHA 直接绑定的 Prompt；不会从文件名或相邻文本猜测。"}</p></div>
            <dl className="external-storyboard-facts">
              <Fact label="Metadata binding" value={group.metadata_status || "not_evaluated"} />
              <Fact label="Evidence level" value={group.evidence_level || "non_canonical"} />
              <Fact label="Shot ID" value={metadata.shot_id || "NOT_EVALUATED"} />
              <Fact label="Shot type" value={metadata.shot_type || "NOT_EVALUATED"} />
              <Fact label="Generation type" value={metadata.generation_type || "NOT_EVALUATED"} />
            </dl>
            {!hasBoundMetadata && <p className="external-metadata-note"><WarningCircle size={16} weight="fill" />该视频只有文件级 identity；分镜、Prompt、类型和成功/失败均保持 `NOT_EVALUATED`。</p>}
          </section>}
          <section className="external-location-section">
            <header><div><span>SHA duplicate group</span><h2>{locations.length} 个物理位置</h2></div><code>{String(group.sha256 || "").slice(0, 16)}…</code></header>
            <div className="external-location-list">
              {locations.map((location) => {
                const source = sources.find((item) => item.id === location.source_id);
                const locationUrl = location.token ? `/api/external-media/media/${encodeURIComponent(location.token)}` : null;
                return (
                  <article key={`${location.source_id}:${location.relative_path}`}>
                    <div><strong>{sourceLabel(source, location.source_label)}</strong><span>{location.source_kind || source?.kind || "external"}</span></div>
                    <code title={location.relative_path}>{location.relative_path || location.file_name || "相对路径不可用"}</code>
                    <span>{formatBytes(location.bytes)} · {formatTime(location.modified_at)}</span>
                    {locationUrl ? <a href={locationUrl} target="_blank" rel="noreferrer">打开</a> : <span>不可预览</span>}
                  </article>
                );
              })}
            </div>
          </section>
        </div>
        <aside className="detail-aside external-detail-aside">
          <section className="detail-section"><h3>Exact file identity</h3><dl className="identity-list"><Fact label="SHA-256" value={group.sha256} /><Fact label="MIME" value={group.mime_type} /><Fact label="大小" value={formatBytes(group.bytes)} /><Fact label="物理副本" value={locations.length} /></dl></section>
          <section className="detail-section"><h3>判断边界</h3><p className={`evidence-state evidence-state--${status.tone}`}><span />{status.label}<br /><small>External evidence 不产生 candidate、P6、Final Acceptance 或 activation。</small></p></section>
          <section className="detail-section"><h3>Evidence refs</h3>{evidenceRefs.length ? <div className="external-evidence-list">{evidenceRefs.map((ref, index) => <code key={`${typeof ref === "string" ? ref : ref?.relative_path || "evidence"}-${index}`}>{typeof ref === "string" ? ref : [ref?.source_id, ref?.relative_path || ref?.kind].filter(Boolean).join(" · ") || "已绑定 JSON evidence"}</code>)}</div> : <p className="external-no-evidence">没有可公开的 exact-bound sidecar reference。</p>}</section>
          <section className="detail-section"><h3>Canonical Runs exact match</h3>{(group.run_bindings || []).length ? <div className="external-evidence-list">{group.run_bindings.map((binding, index) => <code key={`${binding.workspace || "runs"}-${binding.attempt_id || index}`}>{[binding.workspace, binding.attempt_id, binding.shot_snapshot_status].filter(Boolean).join(" · ")}</code>)}</div> : <p className="external-no-evidence">没有与 exact SHA-256 + bytes 匹配的 canonical Runs output。外部媒体库不会补造缺失 Production state。</p>}</section>
        </aside>
      </section>
      <section className="action-bar external-action-bar">
        <div className="action-note">只读外部证据 · SHA 去重 <Info size={16} /></div>
        <a className={`primary-action${url ? "" : " is-disabled"}`} href={url || undefined} target="_blank" rel="noreferrer" aria-disabled={!url}><Play size={20} weight="fill" />查看 exact 视频</a>
        <div className="secondary-action workspace-read-state"><Info size={18} />非 Production 状态</div>
      </section>
    </>
  );
}

function EmptyState({ title, detail, retry }) {
  return <section className="console-state"><WarningCircle size={36} /><h1>{title}</h1><p>{detail}</p>{retry && <button type="button" onClick={retry}><ArrowsClockwise size={17} />重新读取</button>}</section>;
}

function EvidenceDialog({ open, detail, attempt, onClose }) {
  const titleId = useId();
  const closeRef = useRef(null);
  const dialogRef = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const previous = document.activeElement;
    const keydown = (event) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") {
        const buttons = [...(dialogRef.current?.querySelectorAll("button") || [])];
        if (!buttons.length) return;
        if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault(); buttons.at(-1).focus(); }
        else if (!event.shiftKey && document.activeElement === buttons.at(-1)) { event.preventDefault(); buttons[0].focus(); }
      }
    };
    document.addEventListener("keydown", keydown);
    closeRef.current?.focus();
    return () => { document.removeEventListener("keydown", keydown); previous?.focus?.(); };
  }, [open, onClose]);
  if (!open) return null;
  const evidence = attempt?.evidence || attempt?.request_evidence || {};
  return (
    <div className="dialog-backdrop" onMouseDown={onClose}>
      <section ref={dialogRef} className="evidence-dialog" role="dialog" aria-modal="true" aria-labelledby={titleId} onMouseDown={(event) => event.stopPropagation()}>
        <header><div><span>只读白名单证据</span><h2 id={titleId}>{attemptId(attempt, 0)}</h2></div><button ref={closeRef} type="button" aria-label="关闭" onClick={onClose}><X size={18} /></button></header>
        <div className="dialog-body"><p className="dialog-status dialog-status--ready"><CheckCircle size={18} weight="fill" />来自 {detail.workspace} 的 strict reopen projection。</p><dl className="dialog-records"><Fact label="Request pointer" value={evidence.path || evidence.request_pointer} /><Fact label="File hash" value={evidence.file_sha256} /><Fact label="Request hash" value={evidence.request_input_hash || attempt?.request_hash} /><Fact label="Resolved hash" value={evidence.resolved_generation_hash || evidence.content_hash} /><Fact label="边界" value="显示 sealed prompt；不返回 negative prompt、Provider raw response、signed URL、secret 或 absolute path" /></dl></div>
        <footer><button type="button" onClick={onClose}>关闭</button></footer>
      </section>
    </div>
  );
}

export function App() {
  const [activeSurface, setActiveSurface] = useState("runs");
  const [catalog, setCatalog] = useState([]);
  const [workspace, setWorkspace] = useState("");
  const [detail, setDetail] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [continuityProjection, setContinuityProjection] = useState(null);
  const [continuityLoading, setContinuityLoading] = useState(false);
  const [continuityError, setContinuityError] = useState("");
  const [externalCatalog, setExternalCatalog] = useState(null);
  const [externalSelectedSha, setExternalSelectedSha] = useState("");
  const [selectedSource, setSelectedSource] = useState("all");
  const [externalQuery, setExternalQuery] = useState("");
  const [externalEvidenceFilter, setExternalEvidenceFilter] = useState("all");
  const [externalLoading, setExternalLoading] = useState(false);
  const [externalError, setExternalError] = useState("");
  const [runsMediaIndex, setRunsMediaIndex] = useState(null);
  const [runsContextLoading, setRunsContextLoading] = useState(false);
  const [runsContextError, setRunsContextError] = useState("");
  const continuityRequestEpoch = useRef(0);
  const workspaceRef = useRef("");
  const workspaceSelectionGuard = useRef(null);
  const detailRequestGuard = useRef(null);
  const runsContextRequestGuard = useRef(null);
  if (!workspaceSelectionGuard.current) workspaceSelectionGuard.current = createWorkspaceSelectionGuard();
  if (!detailRequestGuard.current) detailRequestGuard.current = createLatestRequestGuard();
  if (!runsContextRequestGuard.current) runsContextRequestGuard.current = createLatestRequestGuard();
  const runsRefreshInFlight = useRef(false);
  const runsRefreshQueued = useRef(false);
  const externalRefreshInFlight = useRef(false);
  const externalRefreshQueued = useRef(false);

  const loadDetail = useCallback(async (key, { preserveAttempt = false, selectionToken, requestToken } = {}) => {
    const response = await fetch(`/api/runs/detail?workspace=${encodeURIComponent(key)}`, { cache: "no-store" });
    const body = await response.json();
    if (!requestsCanCommit(workspaceSelectionGuard.current, selectionToken, detailRequestGuard.current, requestToken)) return null;
    if (!response.ok || body?.status === "invalid" || body?.error) {
      const message = body?.error?.message || body?.message || "工作区 strict reopen 失败。";
      const code = body?.error?.code;
      throw new Error(code ? `${message} · ${code}` : message);
    }
    workspaceRef.current = key;
    setWorkspace(key);
    setDetail(body);
    const attempts = body.attempts || body.video_generation_attempts || [];
    setSelectedId((current) => (
      preserveAttempt && attempts.some((item, index) => attemptId(item, index) === current)
        ? current
        : (attempts.length ? attemptId(attempts[0], 0) : "")
    ));
    return body;
  }, []);

  const refresh = useCallback(async () => {
    if (runsRefreshInFlight.current) {
      runsRefreshQueued.current = true;
      return;
    }
    runsRefreshInFlight.current = true;
    setLoading(true);
    let selectionToken = workspaceSelectionGuard.current.snapshot();
    let requestToken = detailRequestGuard.current.snapshot();
    try {
      do {
        selectionToken = workspaceSelectionGuard.current.snapshot();
        requestToken = detailRequestGuard.current.beginRequest();
        runsRefreshQueued.current = false;
        setError(null);
        try {
          const response = await fetch("/api/runs", { cache: "no-store" });
          const body = await response.json();
          if (!response.ok) throw new Error(body?.error?.message || "本地 runs 数据源不可用。");
          const items = body.workspaces || body.items || [];
          setCatalog(items);
          if (!workspaceSelectionGuard.current.canCommit(selectionToken)) continue;
          if (!items.length) {
            workspaceRef.current = "";
            setWorkspace("");
            setDetail(null);
            continue;
          }
          const current = workspaceRef.current;
          const ordered = current
            ? [...items.filter((item) => item.workspace === current), ...items.filter((item) => item.workspace !== current)]
            : items;
          let lastError;
          for (const item of ordered) {
            try {
              const loaded = await loadDetail(item.workspace, {
                preserveAttempt: item.workspace === current,
                selectionToken,
                requestToken,
              });
              if (!loaded) break;
              lastError = null;
              break;
            } catch (cause) {
              if (!workspaceSelectionGuard.current.canCommit(selectionToken)) break;
              lastError = cause;
            }
          }
          if (!workspaceSelectionGuard.current.canCommit(selectionToken)) continue;
          if (lastError) throw lastError;
        } catch (cause) {
          if (!workspaceSelectionGuard.current.canCommit(selectionToken)) continue;
          setDetail(null);
          setError(cause instanceof Error ? cause.message : "本地 runs 数据源不可用。");
        }
      } while (runsRefreshQueued.current);
    } finally {
      runsRefreshInFlight.current = false;
      if (requestsCanCommit(workspaceSelectionGuard.current, selectionToken, detailRequestGuard.current, requestToken)) setLoading(false);
    }
  }, [loadDetail]);

  const selectWorkspace = useCallback(async (key) => {
    const selectionToken = workspaceSelectionGuard.current.beginSelection();
    const requestToken = detailRequestGuard.current.beginRequest();
    workspaceRef.current = key;
    setLoading(true);
    setError(null);
    try {
      await loadDetail(key, { selectionToken, requestToken });
    } catch (cause) {
      if (!requestsCanCommit(workspaceSelectionGuard.current, selectionToken, detailRequestGuard.current, requestToken)) return;
      workspaceRef.current = key;
      setDetail(null);
      setWorkspace(key);
      setError(cause instanceof Error ? cause.message : "工作区无法打开。");
    } finally {
      if (requestsCanCommit(workspaceSelectionGuard.current, selectionToken, detailRequestGuard.current, requestToken)) setLoading(false);
    }
  }, [loadDetail]);

  useEffect(() => { refresh(); }, [refresh]);

  const attempts = detail?.attempts || detail?.video_generation_attempts || [];
  const attempt = useMemo(() => attempts.find((item, index) => attemptId(item, index) === selectedId) || attempts[0], [attempts, selectedId]);
  const continuityEligible = Boolean(
    attempt?.continuity_role && String(attempt?.phase || "").toLowerCase() === "validate"
  );

  const loadContinuityReview = useCallback(async () => {
    const epoch = ++continuityRequestEpoch.current;
    if (!continuityEligible || !workspace || !attempt) {
      setContinuityProjection(null);
      setContinuityError("");
      setContinuityLoading(false);
      return;
    }
    setContinuityLoading(true);
    setContinuityError("");
    setContinuityProjection(null);
    try {
      const id = attemptId(attempt, 0);
      const response = await fetch(
        `/api/runs/continuity-review?workspace=${encodeURIComponent(workspace)}&attempt=${encodeURIComponent(id)}`,
        { cache: "no-store" },
      );
      const body = await response.json();
      if (!response.ok || body?.error) throw new Error(body?.error?.message || "continuity review 投影不可用。");
      if (!projectionMatchesTarget(body, workspace, id)) throw new Error("continuity review 投影已过期。");
      if (epoch !== continuityRequestEpoch.current) return;
      setContinuityProjection(body);
    } catch (cause) {
      if (epoch !== continuityRequestEpoch.current) return;
      setContinuityProjection(null);
      setContinuityError(cause instanceof Error ? cause.message : "continuity review 投影不可用。");
    } finally {
      if (epoch === continuityRequestEpoch.current) setContinuityLoading(false);
    }
  }, [attempt, continuityEligible, workspace]);

  useEffect(() => { loadContinuityReview(); }, [loadContinuityReview]);

  const refreshExternal = useCallback(async () => {
    if (externalRefreshInFlight.current) {
      externalRefreshQueued.current = true;
      return;
    }
    externalRefreshInFlight.current = true;
    setExternalLoading(true);
    try {
      do {
        externalRefreshQueued.current = false;
        try {
          const response = await fetch("/api/external-media", { cache: "no-store" });
          const body = await readExternalCatalogResponse(response);
          const groups = body.groups || [];
          setExternalCatalog(body);
          setExternalError("");
          setExternalSelectedSha((current) => (
            groups.some((item) => item.sha256 === current)
              ? current
              : (preferredExternalGroup(groups)?.sha256 || "")
          ));
        } catch (cause) {
          setExternalError(cause instanceof Error ? cause.message : "外部媒体数据源不可用。");
        }
      } while (externalRefreshQueued.current);
    } finally {
      externalRefreshInFlight.current = false;
      setExternalLoading(false);
    }
  }, []);

  useEffect(() => { refreshExternal(); }, [refreshExternal]);
  const refreshRunsMediaIndex = useCallback(async () => {
    const requestToken = runsContextRequestGuard.current.beginRequest();
    setRunsMediaIndex(null);
    setRunsContextLoading(true);
    try {
      const response = await fetch("/api/runs/media-context-index", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok || body?.error) throw new Error(body?.error?.message || "Runs exact media context 当前不可用。");
      if (!runsContextRequestGuard.current.canCommit(requestToken)) return;
      setRunsMediaIndex(body);
      setRunsContextError(body?.boundary?.complete === true ? "" : `Runs context 部分可用：${body?.summary?.failed_workspace_count ?? "部分"} 个 workspace 无法严格重开；仅展示已确认的 exact match。`);
    } catch (cause) {
      if (!runsContextRequestGuard.current.canCommit(requestToken)) return;
      setRunsMediaIndex(null);
      setRunsContextError(cause instanceof Error ? cause.message : "Runs exact media context 当前不可用。");
    } finally {
      if (runsContextRequestGuard.current.canCommit(requestToken)) setRunsContextLoading(false);
    }
  }, []);
  useEffect(() => { refreshRunsMediaIndex(); }, [refreshRunsMediaIndex]);
  const refreshRunsAndContext = useCallback(async () => {
    await Promise.all([refresh(), refreshRunsMediaIndex()]);
  }, [refresh, refreshRunsMediaIndex]);
  const liveConnection = useLibraryLiveUpdates({ refreshRuns: refreshRunsAndContext, refreshExternal });
  const enrichedExternalCatalog = useMemo(
    () => attachRunsMediaIndex(externalCatalog, runsMediaIndex),
    [externalCatalog, runsMediaIndex],
  );

  const visibleExternalGroups = (enrichedExternalCatalog?.groups || [])
    .filter((group) => selectedSource !== "runs" && groupMatchesSource(group, selectedSource))
    .filter((group) => groupMatchesEvidenceFilter(group, externalEvidenceFilter))
    .filter((group) => groupMatchesQuery(group, externalQuery));
  const externalGroup = visibleExternalGroups.find((group) => group.sha256 === externalSelectedSha)
    || preferredExternalGroup(visibleExternalGroups);
  const refreshFailed = selectedSource === "runs"
    ? Boolean(error)
    : selectedSource === "all" ? Boolean(error || externalError) : Boolean(externalError);
  const liveStatus = libraryLiveStatus({
    connectionState: liveConnection.state,
    expectedSources: liveConnection.expectedSources,
    watchedSources: liveConnection.watchedSources,
    selectedSource,
    refreshFailed,
  });

  const selectSource = useCallback((sourceId) => {
    setSelectedSource(sourceId);
    setEvidenceOpen(false);
    if (sourceId === "runs" || sourceId === "all") {
      setActiveSurface("runs");
      return;
    }
    const groups = (enrichedExternalCatalog?.groups || [])
      .filter((group) => groupMatchesSource(group, sourceId))
      .filter((group) => groupMatchesEvidenceFilter(group, externalEvidenceFilter));
    setExternalSelectedSha(preferredExternalGroup(groups)?.sha256 || "");
    setActiveSurface("external");
  }, [enrichedExternalCatalog, externalEvidenceFilter]);

  const selectAttempt = useCallback((id) => {
    setSelectedId(id);
    setActiveSurface("runs");
    setEvidenceOpen(false);
  }, []);

  const selectExternal = useCallback((sha256) => {
    setExternalSelectedSha(sha256);
    setActiveSurface("external");
    setEvidenceOpen(false);
  }, []);

  const selectWorkspaceAndShowRuns = useCallback(async (key) => {
    setSelectedSource("runs");
    setActiveSurface("runs");
    await selectWorkspace(key);
  }, [selectWorkspace]);

  const refreshSelectedSource = useCallback(async () => {
    if (selectedSource === "runs") await refreshRunsAndContext();
    else if (selectedSource === "all") await Promise.all([refreshRunsAndContext(), refreshExternal()]);
    else await refreshExternal();
  }, [refreshExternal, refreshRunsAndContext, selectedSource]);

  const continuityContent = (
    <>
      {continuityEligible && continuityLoading && <section className="continuity-review-loading" aria-live="polite">正在严格打开 continuity review request…</section>}
      {continuityEligible && continuityError && <section className="continuity-review-error"><WarningCircle size={20} weight="fill" /><div><strong>Human continuity review 不可用</strong><p>{continuityError}</p><button type="button" onClick={loadContinuityReview}>重新读取</button></div></section>}
      {continuityProjection && <ContinuityReviewPanel key={continuityProjection.review_request.content_hash} projection={continuityProjection} />}
    </>
  );

  let runsContent;
  if (loading && !detail) runsContent = <EmptyState title="正在读取 runs" detail="正在通过 canonical reader 打开本机工作区…" />;
  else if (error) runsContent = <EmptyState title="工作区不可用" detail={error} retry={refresh} />;
  else if (!detail) runsContent = <EmptyState title="没有 runs 工作区" detail="repository/runs 下没有可读取的 Production 或 Legacy 工作区。" retry={refresh} />;
  else if (!attempt) runsContent = <RunsWorkspaceView detail={detail} selectedAttemptId={selectedId} onSelectAttempt={selectAttempt} />;
  else runsContent = <RunsAttemptView detail={detail} attempt={attempt} selectedAttemptId={selectedId} onSelectAttempt={selectAttempt} onEvidence={() => setEvidenceOpen(true)} continuityContent={continuityContent} />;

  let externalContent;
  if (externalLoading && !externalCatalog) externalContent = <EmptyState title="正在扫描外部视频" detail="正在计算 exact SHA 并读取直接绑定的 JSON evidence…" />;
  else if (externalError && !externalCatalog) externalContent = <EmptyState title="外部媒体不可用" detail={externalError} retry={refreshExternal} />;
  else if (!externalGroup && (externalCatalog?.groups || []).length > 0) externalContent = <EmptyState title="没有符合筛选的视频" detail="请调整视频来源、证据状态或搜索条件。" />;
  else if (!externalGroup) externalContent = <EmptyState title="没有外部视频" detail="当前 server allowlist 中没有可读取的常规视频文件。" retry={refreshExternal} />;
  else externalContent = <>{externalError && <section className="catalog-stale-warning" role="status"><WarningCircle size={18} weight="fill" /><div><strong>外部视频刷新失败，当前内容可能已过期</strong><p>{externalError}</p></div></section>}<ExternalSummary group={externalGroup} sources={enrichedExternalCatalog?.sources || []} /><ExternalMediaDetail group={externalGroup} sources={enrichedExternalCatalog?.sources || []} /></>;

  return (
    <div className="app-shell">
      <Sidebar />
      <VideoLibraryRail runsCatalog={catalog} workspace={workspace} attempts={attempts} selectedId={selectedId} runsLoading={loading} runsError={error} externalCatalog={enrichedExternalCatalog || {}} selectedSha={externalGroup?.sha256 || externalSelectedSha} selectedSource={selectedSource} query={externalQuery} evidenceFilter={externalEvidenceFilter} externalLoading={externalLoading} externalError={externalError} runsContextLoading={runsContextLoading} runsContextError={runsContextError} activeSurface={activeSurface} liveStatus={liveStatus} onWorkspace={selectWorkspaceAndShowRuns} onSelectAttempt={selectAttempt} onSelectExternal={selectExternal} onSource={selectSource} onQuery={setExternalQuery} onEvidenceFilter={setExternalEvidenceFilter} onRefresh={refreshSelectedSource} />
      <main className="provider-console">
        {activeSurface === "external" ? externalContent : runsContent}
      </main>
      <EvidenceDialog open={evidenceOpen} detail={detail || {}} attempt={attempt || {}} onClose={() => setEvidenceOpen(false)} />
    </div>
  );
}

export default App;
