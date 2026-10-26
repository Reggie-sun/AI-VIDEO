import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { X } from "@phosphor-icons/react";
import { createPortal } from "react-dom";
import { AudibleVideo } from "./media-player.jsx";

export function ReferenceLightbox({ reference, url, onClose }) {
  const titleId = useId();
  const closeRef = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    const keydown = (event) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") { event.preventDefault(); closeRef.current?.focus(); }
    };
    document.addEventListener("keydown", keydown);
    closeRef.current?.focus();
    return () => { document.removeEventListener("keydown", keydown); previous?.focus?.(); };
  }, [onClose]);
  return createPortal(
    <div className="reference-lightbox" onMouseDown={onClose}>
      <figure role="dialog" aria-modal="true" aria-labelledby={titleId} onMouseDown={(event) => event.stopPropagation()}>
        <button ref={closeRef} type="button" onClick={onClose} aria-label="关闭 Reference 图片预览"><X size={20} /></button>
        <img src={url} alt={`${reference.role || "reference"} ${reference.asset_id || ""}`} />
        <figcaption id={titleId}><strong>{reference.role || "reference"}</strong><span>{reference.asset_id || "未标注 asset"}</span><small>点击遮罩、关闭按钮或按 Esc 退出</small></figcaption>
      </figure>
    </div>, document.body
  );
}


export function ReferenceMedia({ media, label = "参考素材", onError }) {
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);
  const token = media?.token || media?.media_token;
  const url = typeof token === "string" && /^[A-Za-z0-9_-]{6,128}$/.test(token)
    ? `/api/runs/media/${encodeURIComponent(token)}` : null;
  if (!url) return <p className="reference-unavailable">{label} · 暂无可验证预览</p>;
  if (media.mime_type?.startsWith("video/")) return <AudibleVideo compact src={url} preload="none" aria-label={label} onError={onError} />;
  if (!media.mime_type?.startsWith("image/")) return <p className="reference-unavailable">{label} · 此类型暂无预览</p>;
  return <>
    <button type="button" className="reference-image-button" aria-label={`放大 ${label}`} onClick={() => setOpen(true)}>
      <img src={url} alt={label} onError={onError} loading="lazy" />
    </button>
    {open && <ReferenceLightbox reference={{ role: label, asset_id: media.asset_id }} url={url} onClose={close} />}
  </>;
}

const SOURCE_LABELS = { character: "角色参考", scene: "场景参考", shot: "Shot 素材" };

export function AuthoredReferences({ shot }) {
  const references = shot?.authored_references || [];
  return <section className="shot-reference-section" aria-label="生成前创作参考">
    <h4>生成前创作参考与素材</h4>
    <p>当前创作版本 · revision {shot?.revision || "—"}，不代表已提交给模型</p>
    {references.length ? <div className="shot-reference-grid">{references.map((ref, i) => <article key={`${ref.source_kind}:${ref.source_id}:${ref.role}:${ref.asset_id}:${i}`}>
      <ReferenceMedia media={ref.media} label={ref.asset_id} />
      <strong>{ref.asset_id}</strong><small>{SOURCE_LABELS[ref.source_kind] || "创作素材"} · {ref.source_id} · {ref.role}</small>
    </article>)}</div> : <p>尚未登记此 Shot、角色或场景的参考素材</p>}
    {shot?.authored_references_truncated && <p>仅展示前 32 项创作素材</p>}
  </section>;
}

export function RequestReferences({ attempt }) {
  const inputs = attempt?.input_bindings || [];
  return <section className="shot-reference-section" aria-label="生成请求参考">
    <h4>本次生成请求参考</h4>
    <p>来自该 attempt 的请求绑定；是否已提交以执行阶段为准</p>
    {inputs.length ? <div className="shot-reference-grid">{inputs.map((ref, i) => <article key={`${ref.role}:${ref.asset_id}:${i}`}>
      <ReferenceMedia media={ref.media} label={ref.asset_id || ref.role} />
      <strong>{ref.asset_id || "未标注素材"}</strong><small>{ref.role}</small>
    </article>)}</div> : <p>{attempt?.mode === "text_to_video" ? "T2V 文本生成，无参考素材绑定" : "未记录可显示的请求参考素材"}</p>}
    {attempt?.input_bindings_truncated && <p>仅展示前 32 项请求素材</p>}
  </section>;
}
