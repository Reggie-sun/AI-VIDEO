import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

const execute = promisify(execFile);
const SHA = /^[a-f0-9]{64}$/;
const COMMIT = /^[a-f0-9]{40}$/;
const safePath = (value) => typeof value === "string" && value.length < 1024
  && !value.includes("\\") && !value.includes("\0")
  && value.split("/").every((part) => part && part !== "." && part !== "..");
const fail = () => { throw new Error("MODULE_EVIDENCE_UNAVAILABLE"); };
const string = (value) => typeof value === "string" && value.length <= 4000 ? value : fail();
const state = (value, allowed) => allowed.includes(value) ? value : fail();
const array = (value, limit = 256) => Array.isArray(value) && value.length <= limit ? value : fail();
const digest = (value, pattern = SHA) => pattern.test(value) ? value : fail();
const boolean = (value) => typeof value === "boolean" ? value : fail();
const count = (value) => Number.isSafeInteger(value) && value >= 0 ? value : fail();
const relative = (value) => safePath(value) ? value : fail();
const applicability = (value, allowed) => ({ applicable: boolean(value?.applicable), state: state(value?.state, allowed) });

function artifact(value, withState = false) {
  if (!value || typeof value !== "object") fail();
  const result = { path: relative(value.path) };
  if (withState) result.state = state(value.state, ["verified", "unavailable"]);
  if (!withState || result.state === "verified") {
    result.sha256 = digest(value.sha256);
    result.bytes = count(value.bytes);
  }
  return result;
}

// This transport validates and allowlists the fixed local projector schema. It
// cannot turn a receipt, artifact or user report into Production qualification.
export function moduleEvidenceProjection(value) {
  if (value?.schema !== "ai-video-module-evidence/1" || value.source_kind !== "local_readonly") fail();
  const ids = new Set();
  const modules = array(value.modules, 64).map((entry) => {
    if (!/^[a-z][a-z0-9-]{0,63}$/.test(entry?.id) || ids.has(entry.id)) fail();
    ids.add(entry.id);
    return {
      id: entry.id,
      kind: state(entry.kind, ["engineering", "media", "creative"]),
      source: {
        state: state(entry.source?.state, ["present", "missing", "unavailable"]),
        files: array(entry.source?.files, 32).map((item) => artifact(item)),
        ...(entry.source?.missing_paths ? { missing_paths: array(entry.source.missing_paths, 32).map(relative) } : {}),
        ...(entry.source?.unavailable_paths ? { unavailable_paths: array(entry.source.unavailable_paths, 32).map(relative) } : {}),
      },
      engineering: {
        state: state(entry.engineering?.state, ["historical_pass", "failed", "no_result", "unavailable"]),
        ...(entry.engineering?.reason ? { reason: string(entry.engineering.reason) } : {}),
        evidence: array(entry.engineering?.evidence).map((item) => ({
          receipt_path: relative(item.receipt_path), receipt_sha256: digest(item.receipt_sha256),
          base_commit: digest(item.base_commit, COMMIT), head_commit: digest(item.head_commit, COMMIT),
          finished_at: string(item.finished_at), check_id: string(item.check_id),
          status: state(item.status, ["passed", "failed"]),
          anchor_match: state(item.anchor_match, ["match", "changed", "unknown"]),
          artifacts: array(item.artifacts, 8).map((item) => ({ ...artifact(item), kind: state(item.kind, ["stdout", "stderr", "junit"]) })),
        })),
      },
      media: applicability(entry.media, ["not_applicable", "not_evaluated", "bounded", "failed", "unavailable"]),
      human: applicability(entry.human, ["not_applicable", "not_evaluated", "bounded_acceptance", "recorded_only", "unavailable"]),
    };
  });
  const cases = array(value.cases, 8).map((entry) => ({
    id: string(entry.id), title: string(entry.title), description: string(entry.description),
    category: state(entry.category, ["raw_generation", "edited_preview", "production_example"]),
    artifact: artifact(entry.artifact, true),
    quality: {
      state: state(entry.quality?.state, ["failed", "bounded", "not_evaluated", "unavailable"]),
      pass: count(entry.quality?.pass), fail: count(entry.quality?.fail), not_evaluated: count(entry.quality?.not_evaluated),
    },
    human: { state: state(entry.human?.state, ["bounded_acceptance", "recorded_only", "not_evaluated", "unavailable"]), scope: string(entry.human.scope) },
    qualification: { state: state(entry.qualification?.state, ["not_established", "not_evaluated", "unavailable"]), scope: string(entry.qualification.scope) },
    activation: { state: state(entry.activation?.state, ["recorded", "not_evaluated", "unavailable"]), scope: string(entry.activation.scope) },
    proofs: array(entry.proofs, 16).map((item) => ({
      ...artifact(item, true), kind: state(item.kind, ["qa", "human", "record", "artifact"]),
      ...(item.artifact_sha256 ? { artifact_sha256: digest(item.artifact_sha256) } : {}),
    })),
  }));
  return {
    schema: value.schema, observed_at: string(value.observed_at), source_kind: value.source_kind,
    repository: { head: digest(value.repository?.head, COMMIT), dirty: boolean(value.repository?.dirty) },
    modules, cases,
    delivery: {
      state: state(value.delivery?.state, ["not_established_in_reviewed_cases", "unavailable"]),
      scope: state(value.delivery?.scope, ["selected_case_audit"]),
      autonomy: state(value.delivery?.autonomy, ["not_measured"]),
    },
  };
}

export function createPythonModuleEvidenceProjector(repoRoot, run = execute) {
  const python = process.env.AI_VIDEO_PYTHON || "python";
  return async () => {
    try {
      const { stdout } = await run(python, ["-m", "scripts.provider_console_evidence", "--repo-root", repoRoot], {
        cwd: repoRoot,
        env: {
          PATH: process.env.PATH, LANG: process.env.LANG || "C.UTF-8", LC_ALL: "C.UTF-8",
          PYTHONPATH: path.join(repoRoot, "src"),
        },
        maxBuffer: 8 * 1024 * 1024, timeout: 30000,
      });
      return moduleEvidenceProjection(JSON.parse(stdout));
    } catch { fail(); }
  };
}
