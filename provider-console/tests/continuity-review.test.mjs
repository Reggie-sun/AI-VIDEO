import assert from "node:assert/strict";
import test from "node:test";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import {
  CONTINUITY_DIMENSIONS,
  ContinuityReviewPanel,
  createHumanReviewDecision,
  projectionMatchesTarget,
  validateHumanReviewDecision,
} from "../src/continuity-review.js";

const request = {
  attempt_id: "attempt-1",
  source_shot_id: "shot-source",
  target_shot_id: "shot-target",
  target_shot_content_hash: "1".repeat(64),
  resolved_generation_hash: "2".repeat(64),
  artifact_sha256: "3".repeat(64),
  continuity_constraints_hash: "4".repeat(64),
  qa_policy_content_hash: "5".repeat(64),
  automatic_evaluator: { name: "continuity-cuda", version: "1" },
  required_reviewer: { name: "continuity-human", version: "1" },
  media_identity: `sha256:${"3".repeat(64)}`,
  content_hash: "6".repeat(64),
};

test("decision builder seals all seven values and rejects tampering", async () => {
  const values = Object.fromEntries(
    CONTINUITY_DIMENSIONS.map(([key], index) => [key, index === 2 ? "NOT_SURE" : "PASS"]),
  );

  const decision = await createHumanReviewDecision(request, values, "  Exact visual review.  ");

  assert.equal(decision.review_request_content_hash, request.content_hash);
  assert.deepEqual(decision.reviewer_identity, request.required_reviewer);
  assert.equal(decision.framing, "NOT_SURE");
  assert.equal(decision.rationale, "Exact visual review.");
  assert.equal(await validateHumanReviewDecision(decision), true);
  assert.equal(await validateHumanReviewDecision({ ...decision, identity: "FAIL" }), false);
  await assert.rejects(
    createHumanReviewDecision(request, { ...values, entrance: "MAYBE" }, "reason"),
    /invalid entrance/,
  );
  await assert.rejects(createHumanReviewDecision(request, values, "  "), /rationale/);
});

test("review panel renders seven locked dimensions, NOT_SURE, rationale, and export boundary", () => {
  const projection = {
    workspace: "demo/project.yaml",
    attempt_id: "attempt-1",
    review_request: request,
    media: { token: "continuity-token", sha256: request.artifact_sha256 },
    source_shot: { shot_id: "shot-source", intent: "Alice exits" },
    target_shot: { shot_id: "shot-target", intent: "Alice enters" },
    constraints: {
      camera_axis: "left to right",
      framing: "medium shot",
      lighting: "warm",
      color: "amber",
      motion_direction: "exit right",
      exit_state: "outside frame",
      entrance_state: "enter from left",
    },
  };

  const markup = renderToStaticMarkup(React.createElement(ContinuityReviewPanel, { projection }));

  assert.equal((markup.match(/type="radio"/g) || []).length, 21);
  for (const [, label] of CONTINUITY_DIMENSIONS) assert.match(markup, new RegExp(label));
  assert.match(markup, /是否出现不符合约束的重新入画/);
  assert.match(markup, /PASS · 未出现/);
  assert.match(markup, /FAIL · 已出现/);
  assert.match(markup, /NOT_SURE/);
  assert.match(markup, /Rationale（必填）/);
  assert.match(markup, /continuity-human@1/);
  assert.match(markup, new RegExp(request.content_hash));
  assert.match(markup, /<button[^>]*>导出人工 decision 文件<\/button>/);
  assert.equal(projectionMatchesTarget(projection, "demo/project.yaml", "attempt-1"), true);
  assert.equal(projectionMatchesTarget(projection, "demo/project.yaml", "attempt-2"), false);
});
