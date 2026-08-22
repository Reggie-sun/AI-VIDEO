import assert from "node:assert/strict";
import test from "node:test";

import {
  CONTINUITY_DIMENSIONS,
  createHumanReviewDecision,
  projectionMatchesTarget,
  validateHumanReviewDecision,
} from "../src/continuity-review-contract.js";

const request = {
  attempt_id: "attempt-1",
  required_reviewer: { name: "continuity-human", version: "1" },
  content_hash: "6".repeat(64),
};

test("dependency-free decision contract seals seven values and rejects tampering", async () => {
  const values = Object.fromEntries(
    CONTINUITY_DIMENSIONS.map(([key], index) => [key, index === 2 ? "NOT_SURE" : "PASS"]),
  );
  const decision = await createHumanReviewDecision(request, values, " Exact review. ");

  assert.equal(decision.review_request_content_hash, request.content_hash);
  assert.deepEqual(decision.reviewer_identity, request.required_reviewer);
  assert.equal(decision.framing, "NOT_SURE");
  assert.equal(decision.rationale, "Exact review.");
  assert.equal(await validateHumanReviewDecision(decision), true);
  assert.equal(await validateHumanReviewDecision({ ...decision, identity: "FAIL" }), false);
  await assert.rejects(createHumanReviewDecision(request, { ...values, exit: "MAYBE" }, "reason"), /invalid exit/);
  await assert.rejects(createHumanReviewDecision(request, values, "  "), /rationale/);
});

test("projection target contract rejects stale workspace or attempt", () => {
  const projection = {
    workspace: "demo/project.yaml",
    attempt_id: "attempt-1",
    review_request: { attempt_id: "attempt-1" },
  };
  assert.equal(projectionMatchesTarget(projection, "demo/project.yaml", "attempt-1"), true);
  assert.equal(projectionMatchesTarget(projection, "demo/project.yaml", "attempt-2"), false);
  assert.equal(projectionMatchesTarget(projection, "other/project.yaml", "attempt-1"), false);
});
