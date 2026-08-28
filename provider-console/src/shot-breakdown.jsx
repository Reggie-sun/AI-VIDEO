import React from "react";
import { CheckCircle, FilmStrip, WarningCircle } from "@phosphor-icons/react";

import {
  attemptOutcome,
  generationTypeOf,
  outputState,
  projectShotRows,
  shotForAttempt,
} from "./run-detail-contract.js";
import { externalStatus, externalStoryboardShots } from "./external-media-contract.js";

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
          return (
            <article className="shot-breakdown__card" key={shotId}>
              <header><div><span>SHOT {shotIndex + 1}</span><h3>{shotId}</h3></div><b>{attempts.length} 个生成记录</b></header>
              <ScriptFields shot={shot} />
              <dl className="shot-breakdown__facts">
                <div><dt>分镜策略</dt><dd>{shot?.visual_strategy || "未标注"}</dd></div>
                <div><dt>时长</dt><dd>{shot?.duration_seconds ? `${shot.duration_seconds}s` : "未标注"}</dd></div>
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

export function ExternalShotBreakdown({ group }) {
  const status = externalStatus(group);
  const coLocatedDeclaration = group?.composition?.association_status === "co_located_declared_package";
  const shots = externalStoryboardShots(group);
  return (
    <section className="external-shot-breakdown">
      <header><div><FilmStrip size={22} /><div><span>SHOT EVIDENCE</span><h2>{coLocatedDeclaration ? "同目录声明的 Shot 分镜" : "该视频关联的 Shot 分镜"}</h2></div></div><b>{shots.length} Shots</b></header>
      {group?.composition && <p className="external-shot-breakdown__boundary">{coLocatedDeclaration ? "成片 SHA 已验证；Shot 计划来自同项目目录的 ecommerce package。缺少结构化 composition receipt，因此不证明这些 Shot 构成该 exact MP4，也不升级为 canonical timeline、candidate、QA、P6 或 Final Acceptance。" : "仅展示与该媒体绑定的外部 Shot 证据。"}</p>}
      {shots.length ? <div className="external-shot-breakdown__list">{shots.map((shot, index) => (
        <article key={`${shot.shot_id || "shot"}-${index}`}>
          <header><span>SHOT {index + 1}</span><h3>{shot.shot_id || "Shot 未命名"}</h3><b>{shot.reported_status || (status.evaluated ? status.raw : "NOT_EVALUATED")}</b></header>
          <div className="external-shot-breakdown__facts">
            <span>{shot.shot_type ? `Shot 类型 · ${shot.shot_type}` : shot.generation_type ? `生成类型 · ${shot.generation_type}` : "Shot 类型未绑定"}</span>
            {shot.duration_basis && <span>时长依据 · {shot.duration_basis}</span>}
            {shot.start_seconds !== undefined && shot.start_seconds !== null && <span>{shot.start_seconds}s – {shot.end_seconds}s</span>}
          </div>
          <div className="external-shot-breakdown__script"><span>{shot.purpose || shot.intent || shot.talent_action ? "分镜脚本" : shot.prompt_text ? "分镜脚本参考（来自 exact Prompt）" : "分镜脚本"}</span><p>{shot.purpose || shot.intent || shot.talent_action || shot.prompt_text || "没有与该视频绑定的 Shot 脚本"}</p></div>
          {shot.talent_action && <div className="external-shot-breakdown__script"><span>人物动作</span><p>{shot.talent_action}</p></div>}
          {shot.product_state && <div className="external-shot-breakdown__script"><span>产品状态</span><p>{shot.product_state}</p></div>}
          {shot.camera_intent && <div className="external-shot-breakdown__script"><span>镜头意图</span><p>{shot.camera_intent}</p></div>}
          {shot.visual_strategy_need && <div className="external-shot-breakdown__script"><span>视觉策略</span><p>{shot.visual_strategy_need}</p></div>}
          {shot.copy?.length > 0 && <div className="external-shot-breakdown__script"><span>画面文案</span><p>{shot.copy.join(" / ")}</p></div>}
          {shot.dialogue?.length > 0 && <div className="external-shot-breakdown__script"><span>对白 / 旁白</span><p>{shot.dialogue.join(" / ")}</p></div>}
          <div className="external-shot-breakdown__script"><span>Prompt</span><p>{shot.prompt_text || "没有可验证绑定的生成 Prompt"}</p></div>
        </article>
      ))}</div> : <div className="shot-breakdown__empty"><WarningCircle size={16} />该文件没有可验证的 Shot 绑定；不会从文件名或目录猜测脚本与 Prompt。</div>}
      {shots.length > 0 && <div className="external-shot-breakdown__verified"><CheckCircle size={15} weight="fill" />仅显示已绑定或明确声明的字段</div>}
    </section>
  );
}
