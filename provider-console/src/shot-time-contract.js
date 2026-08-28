function finiteSeconds(value, { allowZero = false } = {}) {
  const number = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(number) || number < 0 || (!allowZero && number === 0)) return null;
  return number;
}

function formatDuration(seconds) {
  const rounded = Math.round(seconds * 1_000) / 1_000;
  return `${Number.isInteger(rounded) ? rounded : rounded.toFixed(3).replace(/0+$/, "").replace(/\.$/, "")}s`;
}

export function formatShotTimecode(value) {
  const seconds = finiteSeconds(value, { allowZero: true });
  if (seconds === null) return "NOT_EVALUATED";
  const totalMilliseconds = Math.round(seconds * 1_000);
  const hours = Math.floor(totalMilliseconds / 3_600_000);
  const minutes = Math.floor((totalMilliseconds % 3_600_000) / 60_000);
  const wholeSeconds = Math.floor((totalMilliseconds % 60_000) / 1_000);
  const milliseconds = totalMilliseconds % 1_000;
  const prefix = hours ? `${String(hours).padStart(2, "0")}:` : "";
  return `${prefix}${String(minutes).padStart(2, "0")}:${String(wholeSeconds).padStart(2, "0")}.${String(milliseconds).padStart(3, "0")}`;
}

export function shotTiming(shot) {
  const start = finiteSeconds(shot?.start_seconds, { allowZero: true });
  const end = finiteSeconds(shot?.end_seconds);
  const explicitDuration = finiteSeconds(shot?.duration_seconds);
  if (start !== null && end !== null && end > start) {
    const rangeDuration = end - start;
    if (explicitDuration !== null && Math.abs(explicitDuration - rangeDuration) > 0.05) {
      return { evaluated: false, label: "时间", value: "NOT_EVALUATED" };
    }
    const duration = explicitDuration ?? rangeDuration;
    const label = shot?.timing_basis === "exact_output_clip" ? "视频内时间" : "声明时间";
    return {
      evaluated: true,
      label,
      value: `${formatShotTimecode(start)} – ${formatShotTimecode(end)} · ${formatDuration(duration)}`,
    };
  }

  const fixedDuration = explicitDuration ?? finiteSeconds(shot?.duration_policy?.seconds);
  if (fixedDuration !== null) {
    return {
      evaluated: true,
      label: shot?.timing_basis === "exact_output_clip" ? "视频时长" : "计划时长",
      value: `${formatDuration(fixedDuration)} · 成片位置 NOT_EVALUATED`,
    };
  }

  const minimum = finiteSeconds(shot?.duration_policy?.minimum_seconds);
  const maximum = finiteSeconds(shot?.duration_policy?.maximum_seconds);
  if (minimum !== null || maximum !== null) {
    const value = minimum !== null && maximum !== null
      ? `${formatDuration(minimum)} – ${formatDuration(maximum)}`
      : minimum !== null ? `≥ ${formatDuration(minimum)}` : `≤ ${formatDuration(maximum)}`;
    return { evaluated: true, label: "计划时长范围", value: `${value} · 成片位置 NOT_EVALUATED` };
  }

  return { evaluated: false, label: "时间", value: "NOT_EVALUATED" };
}
