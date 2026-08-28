import React, { useEffect, useId, useRef, useState } from "react";
import { CheckCircle, FilmStrip, WarningCircle, X } from "@phosphor-icons/react";

import {
  attemptOutcome,
  generationTypeOf,
  outputState,
  projectShotRows,
  shotForAttempt,
} from "./run-detail-contract.js";
import { externalReferenceUrl, externalStatus, externalStoryboardShots } from "./external-media-contract.js";
import { shotTiming } from "./shot-time-contract.js";

function attemptKey(attempt, index) {
  return attempt?.attempt_id || attempt?.id || `attempt-${index + 1}`;
}

function ScriptFields({ shot }) {
  return (
    <div className="shot-breakdown__script">
      <div><span>画面脚本</span><p>{shot?.intent || "未记录画面意图"}</p></div>
      <div><span>对白</span><p>{shot?.dialogue || "无"}</p></div>
      <div><span>旁白</span><p>{shot?.narration || "无"}</p></div>
    </div>
  );
}

function AttemptEvidence({ detail, attempt, selected, onSelect, index }) {
  const id = attemptKey(attempt, index);
  const shot = shotForAttempt(detail, attempt);
  const outcome = attemptOutcome(attempt);
  const media = outputState(attempt);
  return (
    <button type="button" className={`shot-attempt${selected ? " is-selected" : ""}`} onClick={() => onSelect?.(id)}>
      <span className="shot-attempt__top"><strong>{id}</strong><b className={`provider-badge provider-badge--${outcome.tone}`}>{outcome.label}</b></span>
      <span className="shot-attempt__meta">{generationTypeOf(attempt)} · phase {attempt?.phase || "—"} · {media.label}</span>
      {shot?.snapshot_available === false
        ? <span className="shot-attempt__warning"><WarningCircle size={14} weight="fill" />生成当时的 Shot snapshot 不可用</span>
        : <ScriptFields shot={shot} />}
      <span className="shot-attempt__prompt-label">实际提交 Prompt</span>
      <span className="shot-attempt__prompt">{attempt?.prompt_text || "该 attempt 没有可显示的 Prompt"}</span>
    </button>
  );
}

export function ProjectShotBreakdown({ detail, selectedAttemptId, onSelectAttempt }) {
  const { rows, unmatched } = projectShotRows(detail);
  return (
    <section className="shot-breakdown" aria-label="Project 全部 Shot 分镜与生成记录">
      <header className="shot-breakdown__heading">
        <div><FilmStrip size={24} /><div><span>PROJECT SHOTS</span><h2>全部 Shot 的脚本、Prompt 与生成结果</h2></div></div>
        <b>{rows.length} Shots</b>
      </header>
      <p className="shot-breakdown__boundary">按 Project 当前 Shot 顺序展示；每个生成记录仍使用其 exact-attempt snapshot。这里不是最终成片的 ResolvedTimeline。</p>
      <div className="shot-breakdown__list">
        {rows.map(({ shot, attempts }, shotIndex) => {
          const shotId = shot?.shot_id || shot?.id || `shot-${shotIndex + 1}`;
          const timing = shotTiming(shot);
          return (
            <article className="shot-breakdown__card" key={shotId}>
              <header><div><span>SHOT {shotIndex + 1}</span><h3>{shotId}</h3></div><b>{attempts.length} 个生成记录</b></header>
              <ScriptFields shot={shot} />
              <dl className="shot-breakdown__facts">
                <div><dt>分镜策略</dt><dd>{shot?.visual_strategy || "未标注"}</dd></div>
                <div><dt>{timing.label}</dt><dd>{timing.value}</dd></div>
                <div><dt>Revision</dt><dd>{shot?.revision || "—"}</dd></div>
              </dl>
              <div className="shot-breakdown__attempts">
                {attempts.length
                  ? attempts.map((attempt, index) => <AttemptEvidence key={attemptKey(attempt, index)} detail={detail} attempt={attempt} index={index} selected={attemptKey(attempt, index) === selectedAttemptId} onSelect={onSelectAttempt} />)
                  : <div className="shot-breakdown__empty"><WarningCircle size={16} />该 Shot 尚无 video generation attempt，因此没有 Prompt 或成功/失败记录。</div>}
              </div>
            </article>
          );
        })}
        {!rows.length && <div className="shot-breakdown__empty"><WarningCircle size={16} />该 Project 没有 Shot 记录。</div>}
      </div>
      {unmatched.length > 0 && <section className="shot-breakdown__unmatched"><h3>未关联到当前 Project Shot 的生成记录</h3>{unmatched.map((attempt, index) => <AttemptEvidence key={attemptKey(attempt, index)} detail={detail} attempt={attempt} index={index} selected={attemptKey(attempt, index) === selectedAttemptId} onSelect={onSelectAttempt} />)}</section>}
    </section>
  );
}

function verdictTone(value) {
  const normalized = String(value || "NOT_EVALUATED").toUpperCase();
  if (normalized.includes("FAIL") || normalized.includes("REJECT")) return "blocked";
  if (normalized === "PASS" || normalized.includes("SUCCEEDED") || normalized === "OUTPUT_RECORDED") return "ready";
  return "unknown";
}

function ResultLayers({ shot }) {
  const layers = [
    ["生成结果", shot.generation_result || shot.reported_status || "NOT_EVALUATED"],
    ["Technical Gate", shot.technical_gate || "NOT_EVALUATED"],
    ["Human Verdict", shot.human_verdict || "NOT_EVALUATED"],
  ];
  return <dl className="external-result-layers">{layers.map(([label, value]) => <div key={label}><dt>{label}</dt><dd className={`external-verdict external-verdict--${verdictTone(value)}`}>{String(value)}</dd></div>)}</dl>;
}

function ReferenceLightbox({ reference, url, onClose }) {
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
  return (
    <div className="reference-lightbox" onMouseDown={onClose}>
      <figure role="dialog" aria-modal="true" aria-labelledby={titleId} onMouseDown={(event) => event.stopPropagation()}>
        <button ref={closeRef} type="button" onClick={onClose} aria-label="关闭 Reference 图片预览"><X size={20} /></button>
        <img src={url} alt={`${reference.role || "reference"} ${reference.asset_id || ""}`} />
        <figcaption id={titleId}><strong>{reference.role || "reference"}</strong><span>{reference.asset_id || "未标注 asset"}</span><small>点击遮罩、关闭按钮或按 Esc 退出</small></figcaption>
      </figure>
    </div>
  );
}

function ReferenceInputs({ references = [], bindingStatus, bindingReason }) {
  const [selectedReference, setSelectedReference] = useState(null);
  const selectedUrl = externalReferenceUrl(selectedReference);
  if (!references.length) return (
    <div className="external-reference-empty">
      <WarningCircle size={15} />
      <span>{bindingStatus === "NOT_EVALUATED" ? `Reference binding · NOT_EVALUATED：${bindingReason || "缺少 exact input receipt"}` : "没有与该视频 exact request 绑定的 reference。"}</span>
    </div>
  );
  return (
    <section className="external-reference-section">
      <header><span>GENERATION REFERENCES</span><h4>对应的 Reference 输入</h4></header>
      <div className="external-reference-grid">{references.map((reference, index) => {
        const url = externalReferenceUrl(reference);
        const body = <><div className="external-reference-preview">{url ? <img src={url} alt={`${reference.role || "reference"} ${reference.asset_id || ""}`} loading="eager" /> : <FilmStrip size={24} />}</div><figcaption><strong>{reference.role || "reference"}</strong><span>{reference.asset_id || "未标注 asset"}</span><code>{String(reference.sha256 || "").slice(0, 16)}…</code></figcaption></>;
        return url
          ? <button type="button" onClick={() => setSelectedReference(reference)} aria-label={`预览 ${reference.role || "reference"} ${reference.asset_id || ""}`} key={`${reference.role || "reference"}-${reference.sha256 || index}`}>{body}</button>
          : <figure key={`${reference.role || "reference"}-${reference.sha256 || index}`}>{body}</figure>;
      })}</div>
      {selectedReference && selectedUrl && <ReferenceLightbox reference={selectedReference} url={selectedUrl} onClose={() => setSelectedReference(null)} />}
    </section>
  );
}

function EvidenceFindings({ findings = [] }) {
  if (!findings.length) return null;
  return (
    <section className="external-findings">
      <header><span>REQUIREMENT FINDINGS</span><h4>逐项判断证据</h4></header>
      <div>{findings.map((finding, index) => {
        const evidence = Array.isArray(finding.evidence) ? finding.evidence.join(" · ") : finding.evidence;
        return <article key={`${finding.requirement_id || "finding"}-${index}`}><b className={`external-verdict external-verdict--${verdictTone(finding.verdict)}`}>{finding.verdict || "NOT_EVALUATED"}</b><strong>{finding.requirement_id || "未命名 requirement"}</strong><p>{finding.reason || evidence || "没有可公开的 evidence 摘要"}</p>{finding.reason && evidence && <small>{evidence}</small>}</article>;
      })}</div>
    </section>
  );
}

function joinedLines(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join(" / ");
  return typeof value === "string" ? value : "";
}

function ShotTimeBadge({ shot }) {
  const timing = shotTiming(shot);
  return <span>{timing.label} · {timing.value}</span>;
}

export function ExternalShotBreakdown({ group }) {
  const status = externalStatus(group);
  const coLocatedDeclaration = group?.composition?.association_status === "co_located_declared_package";
  const exactExperimentEvidence = (group?.shot_evidence || []).length > 0;
  const shots = externalStoryboardShots(group);
  return (
    <section className="external-shot-breakdown">
      <header><div><FilmStrip size={22} /><div><span>SHOT EVIDENCE</span><h2>{coLocatedDeclaration ? "同目录声明的 Shot 分镜" : exactExperimentEvidence ? "视频、References、分镜与结果" : "该视频关联的 Shot 分镜"}</h2></div></div><b>{shots.length} Records</b></header>
      {(group?.composition || exactExperimentEvidence) && <p className="external-shot-breakdown__boundary">{coLocatedDeclaration ? "成片 SHA 已验证；Shot 计划与声明时间来自同项目目录的 ecommerce package。缺少结构化 composition receipt，因此不证明这些 Shot 构成该 exact MP4，也不升级为 canonical timeline、candidate、QA、P6 或 Final Acceptance。" : "以下信息由 exact MP4 bytes 与受支持的结构化 evidence 绑定；视频内时间只描述该 exact 单 Shot clip，不冒充最终成片的 ResolvedTimeline。只有具备 exact input receipt 的 Reference 才标为生成输入，缺少 upload receipt 时明确显示 NOT_EVALUATED。Technical Gate、Human Verdict 和 Production lifecycle 保持分层。"}</p>}
      {shots.length ? <div className="external-shot-breakdown__list">{shots.map((shot, index) => (
        <article key={`${shot.shot_id || "shot"}-${index}`}>
          <header><span>{shot.entity_kind === "experiment_arm" ? "ARM" : "SHOT"} {index + 1}</span><h3>{shot.shot_id || "记录未命名"}</h3><b>{shot.generation_result || shot.reported_status || (status.evaluated ? status.raw : "NOT_EVALUATED")}</b></header>
          <div className="external-shot-breakdown__facts">
            <ShotTimeBadge shot={shot} />
            <span>{shot.shot_type ? `Shot 类型 · ${shot.shot_type}` : shot.generation_type ? `生成类型 · ${shot.generation_type}` : "Shot 类型未绑定"}</span>
            {shot.provider_name && <span>Provider · {shot.provider_name}</span>}
            {shot.model_id && <span>Model · {shot.model_id}</span>}
            {shot.duration_basis && <span>时长依据 · {shot.duration_basis}</span>}
            {shot.frame_count && <span>{shot.frame_count} frames{shot.fps ? ` · ${shot.fps} fps` : ""}</span>}
          </div>
          {exactExperimentEvidence && <ResultLayers shot={shot} />}
          <div className="external-shot-breakdown__script"><span>{shot.purpose || shot.intent || shot.talent_action ? "分镜脚本" : shot.prompt_text ? "分镜脚本参考（来自 exact Prompt）" : "分镜脚本"}</span><p>{shot.purpose || shot.intent || shot.talent_action || shot.prompt_text || "没有与该视频绑定的 Shot 脚本"}</p></div>
          {shot.talent_action && <div className="external-shot-breakdown__script"><span>人物动作</span><p>{shot.talent_action}</p></div>}
          {shot.product_state && <div className="external-shot-breakdown__script"><span>产品状态</span><p>{shot.product_state}</p></div>}
          {shot.camera_intent && <div className="external-shot-breakdown__script"><span>镜头意图</span><p>{shot.camera_intent}</p></div>}
          {shot.visual_strategy_need && <div className="external-shot-breakdown__script"><span>视觉策略</span><p>{shot.visual_strategy_need}</p></div>}
          {shot.copy?.length > 0 && <div className="external-shot-breakdown__script"><span>画面文案</span><p>{shot.copy.join(" / ")}</p></div>}
          {(joinedLines(shot.dialogue) || joinedLines(shot.narration)) && <div className="external-shot-breakdown__script"><span>对白 / 旁白</span><p>{[joinedLines(shot.dialogue), joinedLines(shot.narration)].filter(Boolean).join(" / ")}</p></div>}
          {shot.continuity_constraints?.length > 0 && <div className="external-shot-breakdown__script"><span>连续性约束</span><p>{shot.continuity_constraints.join(" / ")}</p></div>}
          {exactExperimentEvidence && <ReferenceInputs references={shot.reference_inputs} bindingStatus={shot.reference_binding_status} bindingReason={shot.reference_binding_reason} />}
          <div className="external-shot-breakdown__script"><span>Prompt</span><p>{shot.prompt_text || "没有可验证绑定的生成 Prompt"}</p></div>
          {exactExperimentEvidence && <EvidenceFindings findings={shot.findings} />}
        </article>
      ))}</div> : <div className="shot-breakdown__empty"><WarningCircle size={16} />{group?.association_ambiguity ? "检测到互相冲突的 exact experiment evidence；为避免误关联，分镜、Prompt、References 与 verdict 均未投影。" : "该文件没有可验证的 Shot 绑定；不会从文件名或目录猜测脚本与 Prompt。"}</div>}
      {shots.length > 0 && <div className="external-shot-breakdown__verified"><CheckCircle size={15} weight="fill" />仅显示已绑定或明确声明的字段</div>}
    </section>
  );
}
