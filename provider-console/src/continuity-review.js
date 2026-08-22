import React, { useMemo, useState } from "react";
import {
  CONTINUITY_DIMENSIONS,
  createHumanReviewDecision,
} from "./continuity-review-contract.js";

export {
  CONTINUITY_DIMENSIONS,
  canonicalJson,
  createHumanReviewDecision,
  projectionMatchesTarget,
  validateHumanReviewDecision,
} from "./continuity-review-contract.js";

const h = React.createElement;
const REVIEW_VALUES = ["PASS", "FAIL", "NOT_SURE"];

export function downloadHumanReviewDecision(decision, attemptId) {
  const blob = new Blob([`${JSON.stringify(decision, null, 2)}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `continuity-decision-${String(attemptId).replace(/[^A-Za-z0-9._-]/g, "-")}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function ShotCard({ label, shot, fallbackId }) {
  return h("article", { className: "continuity-shot-card" },
    h("span", null, label),
    h("strong", null, shot?.shot_id || fallbackId || "—"),
    h("p", null, shot?.intent || "未标注 Shot intent"),
  );
}

function DimensionField({ dimension, label, value, onChange }) {
  const displayValue = (option) => {
    if (dimension !== "unexpected_reentry") return option;
    if (option === "PASS") return "PASS · 未出现";
    if (option === "FAIL") return "FAIL · 已出现";
    return "NOT_SURE";
  };
  return h("fieldset", { className: "continuity-dimension" },
    h("legend", null, label),
    h("div", { className: "continuity-choice-row" }, ...REVIEW_VALUES.map((option) =>
      h("label", { key: option, className: value === option ? "is-selected" : "" },
        h("input", {
          type: "radio",
          name: `continuity-${dimension}`,
          value: option,
          checked: value === option,
          onChange: () => onChange(option),
        }),
        h("span", null, displayValue(option)),
      )
    )),
  );
}

export function ContinuityReviewPanel({ projection, onExport }) {
  const initialValues = useMemo(
    () => Object.fromEntries(CONTINUITY_DIMENSIONS.map(([key]) => [key, "NOT_SURE"])),
    [projection?.review_request?.content_hash],
  );
  const [values, setValues] = useState(initialValues);
  const [rationale, setRationale] = useState("");
  const [status, setStatus] = useState("");
  const request = projection?.review_request;
  const mediaToken = projection?.media?.token;
  const incomplete = Object.values(values).includes("NOT_SURE");

  async function submit(event) {
    event.preventDefault();
    setStatus("");
    try {
      const decision = await createHumanReviewDecision(request, values, rationale);
      if (onExport) await onExport(decision);
      else downloadHumanReviewDecision(decision, request.attempt_id);
      setStatus(incomplete
        ? "decision 文件已导出；含 NOT_SURE，不能形成完整 human evidence。"
        : "decision 文件已导出；尚未被 Product caller 接受，也未触发 activation。");
    } catch {
      setStatus("decision 文件无法导出，请检查 rationale 与所有维度。" );
    }
  }

  if (!request) return h("section", { className: "continuity-review-panel continuity-review-panel--empty" },
    h("h2", null, "Human continuity review 不可用"),
    h("p", null, "当前 attempt 没有可严格打开的 exact-bound review request。"),
  );

  return h("section", { className: "continuity-review-panel", "aria-labelledby": "continuity-review-title" },
    h("header", { className: "continuity-review-heading" },
      h("div", null,
        h("span", null, "只读 evidence authoring"),
        h("h2", { id: "continuity-review-title" }, "Human continuity review"),
        h("p", null, "这里只导出 decision 文件；不会写 Manifest、运行 evaluator 或批准 activation。"),
      ),
      h("span", { className: "continuity-lock-badge" }, "Exact-bound"),
    ),
    mediaToken
      ? h("video", { className: "continuity-video", src: `/api/runs/media/${encodeURIComponent(mediaToken)}`, controls: true, preload: "metadata", "aria-label": "待审 continuity fetched video" })
      : h("p", { className: "continuity-warning" }, "Exact fetched MP4 当前不可预览。"),
    h("div", { className: "continuity-shot-grid" },
      h(ShotCard, { label: "Source Shot", shot: projection.source_shot, fallbackId: request.source_shot_id }),
      h(ShotCard, { label: "Target Shot", shot: projection.target_shot, fallbackId: request.target_shot_id }),
    ),
    h("section", { className: "continuity-constraints" },
      h("h3", null, "Continuity constraints"),
      h("dl", null,
        ...["camera_axis", "framing", "lighting", "color", "motion_direction", "exit_state", "entrance_state"].flatMap((key) => [
          h("dt", { key: `${key}-label` }, key.replaceAll("_", " ")),
          h("dd", { key }, projection.constraints?.[key] || "—"),
        ]),
      ),
    ),
    h("form", { className: "continuity-review-form", onSubmit: submit },
      ...CONTINUITY_DIMENSIONS.map(([key, label]) => h(DimensionField, {
        key,
        dimension: key,
        label,
        value: values[key],
        onChange: (value) => setValues((current) => ({ ...current, [key]: value })),
      })),
      h("label", { className: "continuity-rationale" },
        h("span", null, "Rationale（必填）"),
        h("textarea", {
          value: rationale,
          required: true,
          rows: 5,
          onChange: (event) => setRationale(event.target.value),
          placeholder: "说明主体、轴线、构图与进出画判断依据。",
        }),
      ),
      h("div", { className: `continuity-completeness${incomplete ? " is-incomplete" : ""}` },
        incomplete ? "当前含 NOT_SURE：可导出，但 Product caller 将保持 VALIDATE。" : "七项均已明确判断。",
      ),
      h("button", { type: "submit", className: "continuity-export", disabled: !rationale.trim() }, "导出人工 decision 文件"),
      status && h("p", { className: "continuity-export-status", role: "status" }, status),
    ),
    h("details", { className: "continuity-bindings" },
      h("summary", null, "查看 locked bindings 与 hashes"),
      h("dl", null,
        h("dt", null, "Reviewer"), h("dd", null, `${request.required_reviewer.name}@${request.required_reviewer.version}`),
        h("dt", null, "Request hash"), h("dd", null, request.content_hash),
        h("dt", null, "Artifact SHA-256"), h("dd", null, request.artifact_sha256),
        h("dt", null, "Constraints hash"), h("dd", null, request.continuity_constraints_hash),
        h("dt", null, "QA policy hash"), h("dd", null, request.qa_policy_content_hash),
      ),
    ),
  );
}
