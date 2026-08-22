export const CONTINUITY_DIMENSIONS = [
  ["identity", "主体身份一致"],
  ["camera_axis", "镜头轴线一致"],
  ["framing", "景别与构图一致"],
  ["motion_direction", "运动方向一致"],
  ["entrance", "入画状态符合约束"],
  ["exit", "出画状态符合约束"],
  ["unexpected_reentry", "是否出现不符合约束的重新入画"],
];

const REVIEW_VALUES = ["PASS", "FAIL", "NOT_SURE"];

export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

async function sha256(value) {
  const bytes = new TextEncoder().encode(canonicalJson(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function createHumanReviewDecision(reviewRequest, values, rationale) {
  if (!reviewRequest?.content_hash || !reviewRequest?.required_reviewer) {
    throw new Error("review request is unavailable");
  }
  if (!rationale?.trim()) throw new Error("rationale is required");
  const semantic = {
    review_request_content_hash: reviewRequest.content_hash,
    reviewer_identity: reviewRequest.required_reviewer,
    ...Object.fromEntries(CONTINUITY_DIMENSIONS.map(([key]) => {
      const value = values?.[key];
      if (!REVIEW_VALUES.includes(value)) throw new Error(`invalid ${key}`);
      return [key, value];
    })),
    rationale: rationale.trim(),
  };
  return {
    ...semantic,
    content_hash: await sha256({ schema: "human-continuity-review-decision/1", ...semantic }),
  };
}

export async function validateHumanReviewDecision(decision) {
  if (!decision || typeof decision !== "object") return false;
  const { content_hash: contentHash, ...semantic } = decision;
  if (!/^[0-9a-f]{64}$/.test(contentHash || "")) return false;
  if (!semantic.rationale?.trim() || !semantic.reviewer_identity?.name?.trim() || !semantic.reviewer_identity?.version?.trim()) return false;
  if (CONTINUITY_DIMENSIONS.some(([key]) => !REVIEW_VALUES.includes(semantic[key]))) return false;
  return contentHash === await sha256({ schema: "human-continuity-review-decision/1", ...semantic });
}

export function projectionMatchesTarget(projection, workspace, attemptId) {
  return Boolean(
    projection
    && projection.workspace === workspace
    && projection.attempt_id === attemptId
    && projection.review_request?.attempt_id === attemptId
  );
}
