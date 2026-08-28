const OUTCOMES = {
  succeeded: { key: "succeeded", label: "成功", tone: "ready", terminal: true },
  failed: { key: "failed", label: "失败", tone: "blocked", terminal: true },
  interrupted: { key: "interrupted", label: "已中断", tone: "interrupted", terminal: true },
  outcome_unknown: { key: "outcome_unknown", label: "结果未知", tone: "unknown", terminal: true },
  running: { key: "running", label: "进行中", tone: "gated", terminal: false },
};

export function attemptId(attempt, index) {
  return String(attempt?.attempt_id || attempt?.id || `attempt-${index + 1}`);
}

export function providerOf(attempt) {
  return attempt?.provider || {};
}

export function attemptOutcome(attempt) {
  const key = String(attempt?.status || "").toLowerCase();
  return OUTCOMES[key] || { key: key || "unrecorded", label: "状态未标注", tone: "gated", terminal: false };
}

export function generationTypeOf(attempt) {
  if (attempt?.generation_type) return attempt.generation_type;
  const mode = attempt?.mode || attempt?.provider?.mode;
  if (mode === "text_to_video") return "T2V";
  if (mode === "reference_to_video") return "R2V";
  if (mode === "image_to_video") {
    const roles = new Set((attempt?.input_bindings || []).map((item) => item.role));
    return roles.has("first_frame") && roles.has("last_frame") ? "FL2V" : "I2V";
  }
  return mode ? String(mode).toUpperCase() : "未标注";
}

export function shotForAttempt(detail, attempt) {
  const target = attempt?.target_shot_id || attempt?.shot_id;
  const snapshot = attempt?.shot_snapshot;
  const snapshotStatus = attempt?.shot_snapshot_status;
  if (
    snapshotStatus === "verified"
    && snapshot
    && snapshot.shot_id === target
    && snapshot.revision === attempt?.target_shot_revision
    && snapshot.content_hash === attempt?.target_shot_content_hash
  ) return snapshot;

  if (snapshotStatus !== undefined && snapshotStatus !== null) {
    return {
      ...(target ? { shot_id: target } : {}),
      ...(attempt?.target_shot_revision ? { revision: attempt.target_shot_revision } : {}),
      ...(attempt?.target_shot_content_hash ? { content_hash: attempt.target_shot_content_hash } : {}),
      snapshot_available: false,
    };
  }

  const shots = detail?.shots || [];
  return target
    ? shots.find((shot) => (shot.shot_id || shot.id) === target) || { shot_id: target }
    : {};
}

export function projectShotRows(detail) {
  const shots = Array.isArray(detail?.shots) ? detail.shots : [];
  const attempts = Array.isArray(detail?.attempts) ? detail.attempts : [];
  const shotIds = new Set(shots.map((shot) => shot?.shot_id || shot?.id).filter(Boolean));
  return {
    rows: shots.map((shot) => {
      const shotId = shot?.shot_id || shot?.id;
      return {
        shot,
        attempts: attempts.filter((attempt) => (attempt?.target_shot_id || attempt?.shot_id) === shotId),
      };
    }),
    unmatched: attempts.filter((attempt) => !shotIds.has(attempt?.target_shot_id || attempt?.shot_id)),
  };
}

export function outputState(attempt) {
  const outcome = attemptOutcome(attempt);
  if (attempt?.candidate_media) {
    return {
      key: "registered_candidate",
      label: "Candidate 已注册",
      tone: outcome.key === "succeeded" ? "ready" : outcome.tone,
    };
  }
  if (attempt?.fetched_media) {
    return {
      key: "fetched_evidence",
      label: "已获取视频，尚未成为 candidate",
      tone: outcome.tone,
    };
  }
  if (outcome.key === "failed" || outcome.key === "interrupted" || outcome.key === "outcome_unknown") {
    return {
      key: "missing_after_failure",
      label: outcome.key === "outcome_unknown"
        ? "结果未知，无已验证视频"
        : outcome.key === "interrupted"
          ? "已中断，未登记可播放视频"
          : "失败，未登记可播放视频",
      tone: outcome.tone,
    };
  }
  if (outcome.key === "succeeded") {
    return { key: "missing_after_success", label: "成功记录缺少已注册输出", tone: "gated" };
  }
  return { key: "pending", label: "等待可播放输出", tone: "gated" };
}
