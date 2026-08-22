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

function formatTime(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? text(value) : parsed.toLocaleString("zh-CN", { hour12: false });
}

function workspaceLabel(item) {
  if (!item?.workspace) return "未知工作区";
  const prefix = `${item.run_id}/`;
  const suffix = item.workspace.startsWith(prefix) ? item.workspace.slice(prefix.length) : item.workspace;
  return suffix === "project.yaml" || suffix === "manifest.json" ? item.run_id : `${item.run_id} · ${suffix.replace(/\/project\.yaml$/, "")}`;
}

function mediaUrl(media) {
  const token = media?.token || media?.media_token;
  return token ? `/api/runs/media/${encodeURIComponent(token)}` : null;
}

function attemptId(attempt, index) {
  return text(attempt?.attempt_id || attempt?.id, `attempt-${index + 1}`);
}

function providerOf(attempt) {
  return attempt?.provider || {};
}

function outputOf(attempt) {
  return attempt?.effective_output || attempt?.output || {};
}

function shotFor(detail, attempt) {
  const shots = detail?.shots || [];
  const target = attempt?.target_shot_id || attempt?.shot_id;
  if (target) return shots.find((shot) => (shot.shot_id || shot.id) === target) || { shot_id: target };
  return {};
}

function projectOf(detail) {
  return detail?.project || {};
}

function toneFor(attempt) {
  const value = `${attempt?.status || ""} ${attempt?.phase || ""}`.toLowerCase();
  if (/fail|error|reject|unknown/.test(value)) return "blocked";
  if (/active|complete|succeed|ready|deliver/.test(value)) return "ready";
  return "gated";
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

function AttemptRail({ catalog, workspace, attempts, selectedId, loading, onWorkspace, onRefresh, onSelect }) {
  return (
    <aside className="lane-rail" aria-label="真实生成尝试">
      <header className="lane-rail-header"><h2>Provider 记录</h2><p>来自已选 runs 工作区</p></header>
      <WorkspaceSelector catalog={catalog} selected={workspace} loading={loading} onSelect={onWorkspace} onRefresh={onRefresh} />
      <div className="lane-list" aria-label="真实 video generation attempts">
        {attempts.map((attempt, index) => {
          const id = attemptId(attempt, index);
          const provider = providerOf(attempt);
          const selected = id === selectedId;
          const tone = toneFor(attempt);
          return (
            <button key={id} type="button" aria-pressed={selected} className={`lane-option${selected ? " is-selected" : ""}`} onClick={() => onSelect(id)}>
              <span className="lane-option-top"><strong>{provider.name || attempt.provider_name || provider.kind || attempt.provider_kind || "未标注 Provider"}</strong><span className={`provider-badge provider-badge--${tone}`}>{provider.execution_kind || attempt.execution_kind || "记录"}</span><span className={`lane-radio${selected ? " is-checked" : ""}`} /></span>
              <span className="lane-option-sub">{attempt.phase || attempt.status || "状态未标注"} · {id.slice(0, 12)}</span>
            </button>
          );
        })}
        {!loading && !attempts.length && <div className="rail-empty"><Info size={18} /><span>这个工作区没有 video generation attempt。</span></div>}
      </div>
      <div className="lane-rail-note"><Info size={17} /><p>只读查看真实记录。<br />不提交、不重试、不自动回退。</p></div>
      <div className="local-status"><span className="local-dot" /><span>本地 runs 数据源<br />只读连接</span></div>
    </aside>
  );
}

function ShotSummary({ detail, attempt }) {
  const project = projectOf(detail);
  const shot = shotFor(detail, attempt);
  const preview = mediaUrl(attempt?.first_frame_media || attempt?.first_frame || attempt?.input_media);
  return (
    <header className="shot-summary">
      <div className="summary-project">
        {preview ? <img src={preview} alt="已注册首帧" /> : <div className="summary-placeholder"><ImageSquare size={24} /></div>}
        <div><span>项目</span><strong>{project.title || project.name || project.project_id || detail?.run_id || "未命名项目"}</strong></div>
      </div>
      <div className="summary-field"><span>镜头</span><strong>{shot.shot_id || shot.id || attempt?.target_shot_id || "—"}</strong></div>
      <div className="summary-field summary-field--wide"><span>类型</span><strong>{shot.visual_strategy || attempt?.mode || "Video Generation"}</strong></div>
      <div className="summary-field"><span>状态</span><strong>{attempt?.status || attempt?.phase || detail?.status || "—"}</strong></div>
      <div className="summary-field summary-field--updated"><span>更新时间</span><strong>{formatTime(attempt?.finished_at || attempt?.started_at || detail?.updated_at)}</strong></div>
    </header>
  );
}

function Fact({ label, value }) {
  return <div><dt>{label}</dt><dd>{text(value)}</dd></div>;
}

function MediaCard({ attempt }) {
  const input = attempt?.first_frame_media || attempt?.first_frame || attempt?.input_media;
  const output = attempt?.candidate_media || attempt?.output_media || attempt?.video_media;
  const inputUrl = mediaUrl(input);
  const outputUrl = mediaUrl(output);
  const media = output || input;
  const url = outputUrl || inputUrl;
  if (!url) return <div className="media-empty"><ImageSquare size={24} /><p>该 attempt 没有可预览的已注册媒体。</p></div>;
  const isVideo = (media?.mime_type || "").startsWith("video/") || Boolean(outputUrl);
  return (
    <div className="asset-card asset-card--real">
      {isVideo ? <video src={url} controls preload="metadata" aria-label="已注册生成视频" /> : <img src={url} alt="已注册输入素材" />}
      <div className="asset-details">
        <p>素材：<code>{media.asset_id || "已注册媒体"}</code></p>
        <p>{media.mime_type || "MIME 未标注"} · {media.bytes ? `${media.bytes.toLocaleString("zh-CN")} bytes` : "大小未标注"}</p>
        <p>{[media.width, media.height].every(Boolean) ? `${media.width} × ${media.height}` : "尺寸未标注"}</p>
        <p className="asset-ok"><CheckCircle size={15} weight="fill" />Registry bytes 已 strict reopen</p>
      </div>
    </div>
  );
}

function DetailPane({ detail, attempt, onEvidence }) {
  const provider = providerOf(attempt);
  const output = outputOf(attempt);
  const shot = shotFor(detail, attempt);
  const tone = toneFor(attempt);
  const title = provider.name || attempt?.provider_name || provider.kind || attempt?.provider_kind || "Provider attempt";
  const evidence = attempt?.evidence || attempt?.request_evidence || {};
  const duration = shot.duration_seconds || shot.duration_policy?.seconds;
  return (
    <>
      <section className="details-grid">
        <div className="readiness-pane">
          <header className="lane-heading">
            <div><h1>{title}</h1><span className={`provider-badge provider-badge--${tone}`}>{provider.execution_kind || attempt?.execution_kind || "只读"}</span></div>
            <p>{attemptId(attempt, 0)} · 来自 canonical Production/Legacy reader</p>
            <span className="manual-note">真实 runs 记录 · 不自动回退 <Info size={17} /></span>
          </header>
          <div className="readiness-copy"><h2>记录链</h2><p>以下字段来自严格 reopen 后的白名单投影，不代表新的执行授权。</p></div>
          <ol className="sequence-list">
            <li className="sequence-step"><div className="sequence-marker sequence-marker--ready"><StatusIcon tone="ready" size={24} /><span className="sequence-line" /></div><div className="sequence-content"><div className="sequence-title-row"><h4>1. 工作区已严格打开</h4><span className="ready-tag">只读</span></div><p className="step-description">{detail.workspace} · Manifest revision {text(detail.manifest_revision || detail.manifest?.revision)}</p></div></li>
            <li className="sequence-step"><div className="sequence-marker sequence-marker--ready"><StatusIcon tone="ready" size={24} /><span className="sequence-line" /></div><div className="sequence-content"><div className="sequence-title-row"><h4>2. 镜头与请求已绑定</h4><span className="ready-tag">已验证</span></div><p className="step-description">Target Shot：{shot.shot_id || shot.id || attempt?.target_shot_id || "—"}</p><div className="bullet-facts"><span><i />{shot.intent || "未标注意图"}</span><span><i />{duration ? `${duration}s` : "时长未标注"}</span><span><i />{provider.mode || attempt?.mode || "模式未标注"}</span></div></div></li>
            <li className="sequence-step sequence-step--media"><div className="sequence-marker sequence-marker--ready"><StatusIcon tone="ready" size={24} /><span className="sequence-line" /></div><div className="sequence-content"><div className="sequence-title-row"><h4>3. 已注册媒体</h4><span className="ready-tag">本机</span></div><MediaCard attempt={attempt} /></div></li>
            <li className="sequence-step"><div className={`sequence-marker sequence-marker--${tone}`}><StatusIcon tone={tone} size={24} /></div><div className="sequence-content"><div className="sequence-title-row"><h4>4. Attempt 状态</h4><span className={`ready-tag ready-tag--${tone}`}>{attempt?.status || attempt?.phase || "已记录"}</span></div><p className="step-description">只展示已存在状态；控制台不会推进 lifecycle。</p><div className="intent-box is-ready"><Info size={20} /><div><strong>只读观察边界</strong><p>不写 Manifest、不创建 intent、不调用 Provider、不访问云端。</p></div></div></div></li>
          </ol>
        </div>
        <aside className="detail-aside">
          <section className="detail-section"><h3>Provider 身份</h3><dl className="identity-list"><Fact label="名称" value={provider.name || attempt?.provider_name} /><Fact label="Kind" value={provider.kind || attempt?.provider_kind} /><Fact label="Model" value={provider.model || attempt?.model} /><Fact label="Profile" value={provider.profile || attempt?.profile} /><Fact label="Capability" value={provider.capability || attempt?.capability} /></dl></section>
          <section className="detail-section"><h3>有效输出</h3><dl className="identity-list"><Fact label="分辨率" value={output.width && output.height ? `${output.width} × ${output.height}` : output.resolution} /><Fact label="帧数" value={output.frame_count || output.frames} /><Fact label="帧率" value={output.fps ? `${output.fps} fps` : undefined} /><Fact label="时长" value={output.duration_seconds ? `${output.duration_seconds}s` : undefined} /><Fact label="音频" value={output.native_audio === true ? "原生音频" : output.native_audio === false ? "无原生音频" : output.audio} /></dl></section>
          <section className="detail-section"><h3>Evidence</h3><dl className="identity-list"><Fact label="Request" value={evidence.path || evidence.request_pointer || attempt?.request_pointer} /><Fact label="Fingerprint" value={evidence.request_receipt_fingerprint || evidence.resolved_generation_hash} /><Fact label="File hash" value={evidence.file_sha256 || evidence.content_hash || attempt?.request_hash} /></dl><button type="button" className="evidence-button" onClick={onEvidence}>查看白名单证据 <ArrowSquareOut size={17} /></button></section>
        </aside>
      </section>
      <section className="action-bar">
        <div className="action-note">本机只读 · 无 Provider 调用 <Info size={16} /></div>
        <a className={`primary-action${mediaUrl(attempt?.candidate_media || attempt?.output_media || attempt?.video_media) ? "" : " is-disabled"}`} href={mediaUrl(attempt?.candidate_media || attempt?.output_media || attempt?.video_media) || undefined} target="_blank" rel="noreferrer" aria-disabled={!mediaUrl(attempt?.candidate_media || attempt?.output_media || attempt?.video_media)}><Play size={20} weight="fill" />查看已注册输出</a>
        <button type="button" className="secondary-action" onClick={onEvidence}>查看证据 <ArrowSquareOut size={18} /></button>
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
        <div className="dialog-body"><p className="dialog-status dialog-status--ready"><CheckCircle size={18} weight="fill" />来自 {detail.workspace} 的 strict reopen projection。</p><dl className="dialog-records"><Fact label="Request pointer" value={evidence.path || evidence.request_pointer} /><Fact label="File hash" value={evidence.file_sha256} /><Fact label="Request hash" value={evidence.request_input_hash || attempt?.request_hash} /><Fact label="Resolved hash" value={evidence.resolved_generation_hash || evidence.content_hash} /><Fact label="边界" value="不返回 prompt、Provider raw response、signed URL、secret 或 absolute path" /></dl></div>
        <footer><button type="button" onClick={onClose}>关闭</button></footer>
      </section>
    </div>
  );
}

export function App() {
  const [catalog, setCatalog] = useState([]);
  const [workspace, setWorkspace] = useState("");
  const [detail, setDetail] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const loadDetail = useCallback(async (key) => {
    const response = await fetch(`/api/runs/detail?workspace=${encodeURIComponent(key)}`, { cache: "no-store" });
    const body = await response.json();
    if (!response.ok || body?.status === "invalid" || body?.error) throw new Error(body?.error?.message || body?.message || "工作区 strict reopen 失败。");
    setWorkspace(key);
    setDetail(body);
    const attempts = body.attempts || body.video_generation_attempts || [];
    setSelectedId(attempts.length ? attemptId(attempts[0], 0) : "");
    return body;
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/runs", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.error?.message || "本地 runs 数据源不可用。");
      const items = body.workspaces || body.items || [];
      setCatalog(items);
      if (!items.length) { setWorkspace(""); setDetail(null); return; }
      let lastError;
      for (const item of items) {
        try { await loadDetail(item.workspace); return; } catch (cause) { lastError = cause; }
      }
      throw lastError || new Error("没有可严格打开的工作区。");
    } catch (cause) {
      setDetail(null);
      setError(cause instanceof Error ? cause.message : "本地 runs 数据源不可用。");
    } finally {
      setLoading(false);
    }
  }, [loadDetail]);

  const selectWorkspace = useCallback(async (key) => {
    setLoading(true);
    setError(null);
    try { await loadDetail(key); } catch (cause) { setDetail(null); setWorkspace(key); setError(cause instanceof Error ? cause.message : "工作区无法打开。"); } finally { setLoading(false); }
  }, [loadDetail]);

  useEffect(() => { refresh(); }, [refresh]);

  const attempts = detail?.attempts || detail?.video_generation_attempts || [];
  const attempt = useMemo(() => attempts.find((item, index) => attemptId(item, index) === selectedId) || attempts[0], [attempts, selectedId]);

  return (
    <div className="app-shell">
      <Sidebar />
      <AttemptRail catalog={catalog} workspace={workspace} attempts={attempts} selectedId={selectedId} loading={loading} onWorkspace={selectWorkspace} onRefresh={refresh} onSelect={setSelectedId} />
      <main className="provider-console">
        {loading && !detail ? <EmptyState title="正在读取 runs" detail="正在通过 canonical reader 打开本机工作区…" /> : error ? <EmptyState title="工作区不可用" detail={error} retry={refresh} /> : !detail ? <EmptyState title="没有 runs 工作区" detail="repository/runs 下没有可读取的 Production 或 Legacy 工作区。" retry={refresh} /> : !attempt ? <><ShotSummary detail={detail} /><EmptyState title="没有 Provider 生成记录" detail="这个真实工作区尚未记录 video generation attempt；控制台不会补造 demo lane。" /></> : <><ShotSummary detail={detail} attempt={attempt} /><DetailPane detail={detail} attempt={attempt} onEvidence={() => setEvidenceOpen(true)} /></>}
      </main>
      <EvidenceDialog open={evidenceOpen} detail={detail || {}} attempt={attempt || {}} onClose={() => setEvidenceOpen(false)} />
    </div>
  );
}

export default App;
