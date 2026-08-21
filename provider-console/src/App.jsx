import React, { useEffect, useId, useMemo, useRef, useState } from "react";
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
  Lock,
  Monitor,
  Play,
  Prohibit,
  Question,
  SlidersHorizontal,
  UserCircle,
  WarningCircle,
  X,
} from "@phosphor-icons/react";

const ALICE_IMAGE = "/assets/alice-cafe-first-frame.png";

const LANES = [
  {
    id: "local-quality",
    name: "Local H3 T8",
    mode: "Quality",
    steps: "20 步",
    badge: "本地",
    tone: "ready",
    title: "Local H3 T8 — Quality · 20 步",
    runtime: "Local H3 T8",
    execution: "仅本地",
    boundary: "无云端访问",
    cta: "镜头 12 使用 Local H3",
  },
  {
    id: "local-turbo",
    name: "Local H3 T8",
    mode: "Turbo",
    steps: "6 步",
    badge: "本地",
    tone: "ready",
    title: "Local H3 T8 — Turbo · 6 步",
    runtime: "Local H3 T8",
    execution: "仅本地",
    boundary: "无云端访问",
    cta: "镜头 12 使用 Local H3 Turbo",
  },
  {
    id: "hailuo",
    name: "MiniMax Hailuo 2.3",
    mode: "云端",
    steps: "需付费授权",
    badge: "云端",
    tone: "gated",
    title: "MiniMax Hailuo 2.3",
    runtime: "MiniMax Hailuo 2.3",
    execution: "需付费授权",
    boundary: "需要云端 egress",
    cta: "当前通道不可执行",
  },
  {
    id: "seedance",
    name: "Seedance 2.0 Mini",
    mode: "云端",
    steps: "提交前阻塞",
    badge: "云端",
    tone: "blocked",
    title: "Seedance 2.0 Mini",
    runtime: "Seedance 2.0 Mini",
    execution: "提交前阻塞",
    boundary: "缺少 Ark 素材物化回执",
    cta: "当前通道不可执行",
  },
  {
    id: "minimax-h3",
    name: "MiniMax H3",
    mode: "云端",
    steps: "需付费授权",
    badge: "云端",
    tone: "gated",
    title: "MiniMax H3",
    runtime: "MiniMax H3",
    execution: "需付费授权",
    boundary: "需要云端 egress",
    cta: "当前通道不可执行",
  },
];

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

const GATE_ROWS = [
  ["hailuo", "MiniMax Hailuo 2.3", "需授权", "需付费授权并进行云端数据出境，不可离线执行。", "gated"],
  ["seedance", "Seedance 2.0 Mini", "提交前阻塞", "缺少 Ark 素材物化回执，请提供回执后再提交此通道。", "blocked"],
  ["minimax-h3", "MiniMax H3", "需授权", "需付费授权并进行云端数据出境，不可离线执行。", "gated"],
];

function StatusIcon({ tone, size = 18 }) {
  if (tone === "ready") return <CheckCircle size={size} weight="fill" />;
  if (tone === "blocked") return <Prohibit size={size} weight="fill" />;
  if (tone === "gated") return <WarningCircle size={size} weight="fill" />;
  return <Circle size={size} />;
}

function Sidebar() {
  return (
    <nav className="sidebar" aria-label="主导航">
      <div className="brand">
        <Play size={22} weight="fill" aria-hidden="true" />
        <span>AI-VIDEO</span>
      </div>
      <ul className="nav-list">
        {NAV_ITEMS.map(([id, label, Icon]) => (
          <li key={id}>
            <button
              type="button"
              className={`nav-item${id === "providers" ? " is-active" : ""}`}
              aria-current={id === "providers" ? "page" : undefined}
            >
              <Icon size={17} />
              <span>{label}</span>
            </button>
          </li>
        ))}
      </ul>
      <div className="sidebar-bottom">
        <button type="button" className="operator-button">
          <span className="operator-avatar">OP</span>
          <span>操作员</span>
          <CaretUp size={12} />
        </button>
        <button type="button" className="nav-item help-button">
          <Question size={18} />
          <span>帮助</span>
        </button>
      </div>
    </nav>
  );
}

function LaneRail({ selectedId, onSelect }) {
  return (
    <aside className="lane-rail" aria-label="提供商通道">
      <header className="lane-rail-header">
        <h2>提供商通道</h2>
        <p>为此镜头选择一个通道</p>
      </header>
      <div className="lane-list" aria-label="可用通道">
        {LANES.map((lane) => {
          const selected = lane.id === selectedId;
          return (
            <button
              key={lane.id}
              type="button"
              aria-pressed={selected}
              className={`lane-option${selected ? " is-selected" : ""}`}
              onClick={() => onSelect(lane.id)}
            >
              <span className="lane-option-top">
                <strong>{lane.name}</strong>
                <span className={`provider-badge provider-badge--${lane.tone}`}>{lane.badge}</span>
                {lane.tone === "blocked" ? (
                  <span className="lane-radio lane-radio--blocked" aria-hidden="true" />
                ) : (
                  <span className={`lane-radio${selected ? " is-checked" : ""}`} aria-hidden="true" />
                )}
              </span>
              <span className="lane-option-sub">{lane.mode} · {lane.steps}</span>
            </button>
          );
        })}
      </div>
      <div className="lane-rail-note">
        <Info size={17} />
        <p>当前仅选择了一个通道。<br />不自动回退。</p>
      </div>
      <div className="local-status">
        <span className="local-dot" />
        <span>本地环境<br />离线</span>
      </div>
    </aside>
  );
}

function ShotSummary() {
  return (
    <header className="shot-summary">
      <div className="summary-project">
        <img src={ALICE_IMAGE} alt="Alice Café 首帧" />
        <div><span>项目</span><strong>Alice Café</strong></div>
      </div>
      <div className="summary-field"><span>镜头</span><strong>12</strong></div>
      <div className="summary-field summary-field--wide"><span>类型</span><strong>Image-to-Video</strong></div>
      <div className="summary-field"><span>状态</span><strong>草稿</strong></div>
      <div className="summary-field summary-field--updated"><span>更新时间</span><strong>2026-08-21 09:42</strong></div>
    </header>
  );
}

function ReadyTag({ tone = "ready", children = "已就绪" }) {
  return <span className={`ready-tag ready-tag--${tone}`}>{children}</span>;
}

function SequenceStep({ index, title, tone = "ready", last = false, children }) {
  return (
    <li className="sequence-step">
      <div className={`sequence-marker sequence-marker--${tone}`}>
        <StatusIcon tone={tone} size={24} />
        {!last && <span className="sequence-line" aria-hidden="true" />}
      </div>
      <div className="sequence-content">
        <div className="sequence-title-row">
          <h4>{index}. {title}</h4>
          <ReadyTag tone={tone}>{tone === "ready" ? "已就绪" : "待操作"}</ReadyTag>
        </div>
        {children}
      </div>
    </li>
  );
}

function BulletFacts({ items }) {
  return (
    <div className="bullet-facts">
      {items.map((item) => <span key={item}><i />{item}</span>)}
    </div>
  );
}

function ReadinessSequence({ lane, intentReady }) {
  const isLocal = lane.tone === "ready";
  const blockedTone = lane.tone === "blocked" ? "blocked" : "gated";
  if (!isLocal) {
    return (
      <div className="blocked-panel">
        <StatusIcon tone={blockedTone} size={34} />
        <h3>{lane.title} 当前不可执行</h3>
        <p>{lane.boundary}。本原型不会发起云端调用，也不会自动切换到其它通道。</p>
      </div>
    );
  }

  return (
    <ol className="sequence-list">
      <SequenceStep index="1" title="输入绑定">
        <p className="step-description">首帧素材已绑定，可用。</p>
        <div className="asset-card">
          <img src={ALICE_IMAGE} alt="Alice Café 已绑定首帧" />
          <div className="asset-details">
            <p>素材：<code>alice_cafe_firstframe_v01.exr</code></p>
            <p>1280 × 720 · EXR</p>
            <p>采集时间：2026-08-20 14:37</p>
            <p className="asset-ok"><CheckCircle size={15} weight="fill" />本地 Registry：已绑定</p>
          </div>
        </div>
      </SequenceStep>
      <SequenceStep index="2" title="能力匹配">
        <p className="step-description">镜头需求与该通道的固定能力匹配。</p>
        <BulletFacts items={["1344 × 768", "124 帧", "24 fps", "原生音频", "Image-to-Video"]} />
      </SequenceStep>
      <SequenceStep index="3" title="本地运行时预检">
        <p className="step-description">本工作站可离线运行该通道。</p>
        <BulletFacts items={["GPU H3（80GB）可用", "T8 Tensor 并行", "磁盘与内存正常", "所有检查通过"]} />
        <p className="verified-time">验证时间：2026-08-21 09:35</p>
      </SequenceStep>
      <SequenceStep index="4" title="持久化意图" tone={intentReady ? "ready" : "pending"} last>
        <p className="step-description">点击“使用”后，由 ProductionStateCommitter 写入一次性意图。</p>
        <div className={`intent-box${intentReady ? " is-ready" : ""}`}>
          <Info size={20} />
          <div>
            <strong>{intentReady ? "原型意图已确认" : "尚未生成持久化意图。"}</strong>
            <p>{intentReady ? "仅更新本地原型状态；未调用 Provider、未写入 Production state。" : "使用后将写入一次性意图，并同时记录到本地证据。"}</p>
          </div>
        </div>
      </SequenceStep>
    </ol>
  );
}

function IdentityList({ lane }) {
  return (
    <dl className="identity-list">
      <div><dt>提供商</dt><dd>{lane.runtime}</dd></div>
      <div><dt>模式</dt><dd>{lane.mode}</dd></div>
      <div><dt>步数</dt><dd>{lane.id === "local-quality" ? "20（固定）" : lane.id === "local-turbo" ? "6（固定）" : "—"}</dd></div>
      <div><dt>执行位置</dt><dd>{lane.execution}</dd></div>
      <div><dt>边界</dt><dd>{lane.boundary}</dd></div>
    </dl>
  );
}

function DetailAside({ lane, onEvidence }) {
  const local = lane.tone === "ready";
  return (
    <aside className="detail-aside">
      <section className="detail-section">
        <h3>通道身份</h3>
        <IdentityList lane={lane} />
      </section>
      <section className="detail-section">
        <h3>固定能力</h3>
        <dl className="identity-list">
          <div><dt>分辨率</dt><dd>{local ? "1344 × 768" : "—"}</dd></div>
          <div><dt>帧数</dt><dd>{local ? "124" : "—"}</dd></div>
          <div><dt>帧率</dt><dd>{local ? "24 fps" : "—"}</dd></div>
          <div><dt>音频</dt><dd>{local ? "原生音频" : "—"}</dd></div>
          <div><dt>I/O</dt><dd>{local ? "Image-to-Video" : "—"}</dd></div>
        </dl>
      </section>
      <section className="detail-section">
        <h3>{local ? "本地边界" : "通道边界"}</h3>
        <p className={`evidence-state evidence-state--${local ? "ready" : lane.tone}`}>
          <span />{local ? "所有处理均在本机完成。" : lane.boundary}<br />
          <small>{local ? "不进行网络调用。" : "当前不可执行。"}</small>
        </p>
      </section>
      <section className="detail-section detail-section--evidence">
        <h3>离线证据状态</h3>
        <p className={`evidence-state evidence-state--${local ? "ready" : lane.tone}`}>
          <span />{local ? "必需证据均可提供。" : "当前通道缺少执行证据。"}<br />
          <small>{local ? "验证时间 2026-08-21 09:41" : "完成门禁后才可生成。"}</small>
        </p>
        <button type="button" className="evidence-button" onClick={onEvidence}>
          {local ? "查看证据" : "查看门禁说明"} <ArrowSquareOut size={17} />
        </button>
      </section>
    </aside>
  );
}

function GatesPanel({ open, onToggle }) {
  return (
    <section className={`gates-panel${open ? " is-open" : ""}`}>
      <button type="button" className="gates-toggle" aria-expanded={open} onClick={onToggle}>
        <span>其它通道门禁</span><CaretUp size={16} />
      </button>
      {open && (
        <div className="gate-rows">
          {GATE_ROWS.map(([id, name, state, description, tone]) => (
            <div className="gate-row" key={id}>
              <span className={`gate-dot gate-dot--${tone}`} />
              <strong>{name}</strong>
              <b className={`gate-state gate-state--${tone}`}>{state}</b>
              <p>{description}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function EvidenceDialog({ open, lane, onClose }) {
  const titleId = useId();
  const closeRef = useRef(null);
  const dialogRef = useRef(null);
  const local = lane.tone === "ready";
  useEffect(() => {
    if (!open) return undefined;
    const previousFocus = document.activeElement;
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = [...(dialogRef.current?.querySelectorAll("button") ?? [])].filter((item) => !item.disabled);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    closeRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previousFocus?.focus?.();
    };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="dialog-backdrop" onMouseDown={onClose}>
      <section ref={dialogRef} className="evidence-dialog" role="dialog" aria-modal="true" aria-labelledby={titleId} onMouseDown={(event) => event.stopPropagation()}>
        <header><div><span>离线证据</span><h2 id={titleId}>{lane.title}</h2></div><button ref={closeRef} type="button" aria-label="关闭" onClick={onClose}><X size={18} /></button></header>
        <div className="dialog-body">
          <p className={`dialog-status dialog-status--${local ? "ready" : lane.tone}`}>
            {local ? <CheckCircle size={18} weight="fill" /> : <StatusIcon tone={lane.tone} size={18} />}
            {local ? "该视图展示静态原型证据，不读取 Provider，不访问网络。" : "该通道仍受门禁约束，本原型不会提交、回退或调用 Provider。"}
          </p>
          <dl className="dialog-records">
            <div><dt>素材绑定</dt><dd>{local ? "alice_cafe_firstframe_v01.exr" : "未物化"}</dd></div>
            <div><dt>运行时</dt><dd>{lane.runtime}</dd></div>
            <div><dt>能力</dt><dd>{local ? "1344 × 768 · 124 帧 · 24 fps" : "门禁未完成，未获取"}</dd></div>
            <div><dt>证据边界</dt><dd>{local ? "本地原型 · passive/advisory" : lane.boundary}</dd></div>
          </dl>
        </div>
        <footer><button type="button" onClick={onClose}>关闭</button></footer>
      </section>
    </div>
  );
}

export function App() {
  const [selectedId, setSelectedId] = useState(LANES[0].id);
  const [gatesOpen, setGatesOpen] = useState(true);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [intentReady, setIntentReady] = useState(false);
  const lane = useMemo(() => LANES.find((item) => item.id === selectedId) ?? LANES[0], [selectedId]);

  const selectLane = (id) => {
    setSelectedId(id);
    setIntentReady(false);
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <LaneRail selectedId={selectedId} onSelect={selectLane} />
      <main className="provider-console">
        <ShotSummary />
        <section className="details-grid">
          <div className="readiness-pane">
            <header className="lane-heading">
              <div><h1>{lane.title}</h1><span className={`provider-badge provider-badge--${lane.tone}`}>{lane.badge}</span></div>
              <p>{lane.tone === "ready" ? "镜头 12 的所选通道" : "当前仅供查看，不能执行"}</p>
              <span className="manual-note">手动选择 · 不自动回退 <Info size={17} /></span>
            </header>
            <div className="readiness-copy"><h2>就绪流程</h2><p>完成每个步骤以确认此通道可以安全执行该镜头。</p></div>
            <ReadinessSequence lane={lane} intentReady={intentReady} />
          </div>
          <DetailAside lane={lane} onEvidence={() => setEvidenceOpen(true)} />
        </section>
        <section className="action-bar">
          <div className="action-note">手动选择 · 不自动回退 <Info size={16} /></div>
          <button type="button" className="primary-action" disabled={lane.tone !== "ready"} onClick={() => setIntentReady(true)}>
            {lane.tone === "ready" ? <Play size={20} weight="fill" /> : lane.tone === "blocked" ? <Prohibit size={18} /> : <Lock size={18} />}
            {lane.cta}
          </button>
          <button type="button" className="secondary-action" onClick={() => setEvidenceOpen(true)}>查看证据 <ArrowSquareOut size={18} /></button>
        </section>
        <GatesPanel open={gatesOpen} onToggle={() => setGatesOpen((value) => !value)} />
      </main>
      <EvidenceDialog open={evidenceOpen} lane={lane} onClose={() => setEvidenceOpen(false)} />
    </div>
  );
}

export default App;
