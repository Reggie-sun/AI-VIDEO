#!/usr/bin/env python3
"""Assemble existing local measurements; retain alignment disagreements explicitly.

No generation, network, model download, or alteration of raw analysis inputs.
Run: python -I scripts/14_audio_timeline.py <analysis_root>
"""
import difflib
import json
import math
import re
import sys
from pathlib import Path


def norm(word):
    return re.sub(r"[^a-z0-9]", "", word.lower())


def main(root):
    root = Path(root)
    load = lambda name: json.loads((root / name).read_text())
    shots = load("work/shots.json")
    manifest = load("manifest.json")
    fps = manifest["source_video"]["video"]["fps"]
    nf = manifest["source_video"]["video"]["nb_frames_decoded"]
    duration = manifest["source_video"]["duration_s"]
    aligned = load("audio/lyrics_aligned.json")["words"]
    raw_asr = load("audio/whisper_large_v3_words.json")
    asr = [w for segment in raw_asr["segments"] for w in segment["words"]]
    matching = {}
    matcher = difflib.SequenceMatcher(None, [norm(w["word"]) for w in aligned],
                                    [norm(w["word"]) for w in asr], autojunk=False)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            matching[block.a + k] = block.b + k
    events, flags = [], []

    def event(eid, kind, start, end, evidence, confidence, **extra):
        a, b = max(0, start), min(duration, end)
        record = dict(event_id=eid, type=kind, start_s=a, end_s=b,
                      start_frame=min(nf - 1, max(0, math.floor(a * fps))),
                      end_frame=min(nf - 1, max(0, math.ceil(b * fps) - 1)),
                      origin="unknown", evidence=evidence, confidence=confidence, **extra)
        record["end_frame"] = max(record["start_frame"], record["end_frame"])
        record["shot_ids"] = [s["shot_id"] for s in shots
                              if s["start_frame"] <= record["end_frame"]
                              and s["end_frame"] >= record["start_frame"]]
        record["visual_event_ids"] = []
        events.append(record)
        return record

    for i, w in enumerate(aligned):
        candidate = asr[matching[i]] if i in matching else None
        issues = []
        if w["end_s"] - w["start_s"] > 2.5:
            issues.append("forced_alignment_word_longer_than_2.5s")
        if w["confidence"] < 0.5:
            issues.append("low_CTC_score_not_a_calibrated_probability")
        if candidate:
            delta = max(abs(w["start_s"] - candidate["start"]),
                        abs(w["end_s"] - candidate["end"]))
            if delta > 0.5:
                issues.append("ASR_alignment_disagreement_above_0.5s")
        else:
            issues.append("no_monotonic_exact_ASR_token_match")
        # Keep both measurements. Reject gross forced-alignment stretches rather
        # than mistaking them for continuous audible phonation.
        use_asr = candidate is not None and (w["end_s"] - w["start_s"] > 2.5)
        start, end = ((candidate["start"], candidate["end"]) if use_asr
                      else (w["start_s"], w["end_s"]))
        e = event(f"AW{i + 1:04d}", "vocal_word_candidate", start, end,
                  "Local MMS_FA known-lyric alignment cross-checked against local Whisper large-v3; not listening-confirmed",
                  min(w["confidence"], 0.45 if issues else 0.75),
                  text=w["word"], line_id=w["line_id"], section_tag=w["section_tag"],
                  evidence_level="inferred", timing_status="REVIEW_REQUIRED" if issues else "CROSS_CHECKED_ESTIMATE",
                  selected_timing_method="ASR_candidate" if use_asr else "forced_alignment_candidate",
                  forced_alignment=w, asr_candidate=candidate, uncertainties=issues)
        if issues:
            flags.append(dict(event_id=e["event_id"], issues=issues))
    used_asr = set(matching.values())
    for j, w in enumerate(asr):
        if j not in used_asr and w.get("p", 0) >= 0.7:
            event(f"AX{j + 1:04d}", "unmatched_ASR_word_candidate", w["start"], w["end"],
                  "Whisper token absent from monotonic match to published lyrics; could be ad-lib, alternate wording, or ASR error",
                  min(0.5, w["p"]), text=w["word"], evidence_level="inferred",
                  timing_status="REVIEW_REQUIRED", uncertainties=["Not listening-confirmed; source lyric field may omit ad-libs"])
    beats = load("audio/beats.json")
    hits = load("audio/hits.json")
    hit_times = [h["t"] for h in hits["hits"] if h["band"] == "kick"]
    supported = beats["beat_is_kick_supported"]
    for i, t in enumerate(beats["beats_s"]):
        # Edge extrapolation and interpolated unsupported beats remain distinct.
        nearest = min((abs(t - h) for h in hit_times), default=duration)
        event(f"AB{i + 1:04d}", "beat_candidate", t, t,
              "librosa DP grid; drum-stem kick support within 30ms" if supported[i]
              else "Interpolated/extrapolated DP grid without nearby measured kick; not a confirmed audible beat",
              0.75 if supported[i] else 0.25, evidence_level="inferred",
              kick_supported=supported[i], nearest_kick_distance_s=round(nearest, 4))
    for h in hits["hits"]:
        event("A" + h["hit_id"], "band_onset_candidate", h["t"], h["t"],
              hits["source"], 0.5, evidence_level="inferred", band=h["band"],
              strength=h["strength"],
              uncertainties=["Band flux does not establish instrument identity or separate added SFX from music"])
    # Sections use published lyric tags and candidate vocal starts, never claim
    # that these are the author's unpublished nine visual chapters.
    groups = []
    for e in events:
        if e["type"] != "vocal_word_candidate":
            continue
        if not groups or groups[-1]["label"] != e["section_tag"]:
            groups.append(dict(label=e["section_tag"], start_s=e["start_s"], first_word_event=e["event_id"]))
    sections = [dict(section_id="AS00", label="instrumental opening before first aligned vocal",
                     start_s=0, end_s=groups[0]["start_s"], evidence_level="inferred", confidence=0.5)]
    for i, group in enumerate(groups):
        sections.append(dict(section_id=f"AS{i+1:02d}", **group,
                             end_s=groups[i+1]["start_s"] if i+1 < len(groups) else duration,
                             evidence_level="inferred", confidence=0.5,
                             boundary_method="first forced-aligned lyric word; instrumental lead-in not precisely established"))
    events.sort(key=lambda e: (e["start_s"], e["event_id"]))
    timeline = dict(schema="ev-audio-timeline/v1", source_sha256=manifest["source_video"]["sha256"],
                    fps=fps, duration_s=duration, video_duration_s=nf/fps,
                    coverage=dict(measured_mix="complete", stem_measurements="complete",
                                  perceptual_listening="NOT_EVALUATED", sfx_origin_attribution="unknown"),
                    sections=sections, tempo=beats, loudness=load("audio/loudness.json"),
                    events=events, uncertainties=[
                        "Native model cannot ingest audio here; no claim of direct listening or perceptual SFX recognition",
                        "CTC/Whisper confidence scores are model scores, not calibrated correctness probabilities",
                        "Section boundaries are vocal/tag estimates, not musicological or author chapter boundaries",
                        "Downbeat phase assumes 4/4 and has not been listening-confirmed",
                        "Container/audio outlast decoded video by about 0.106s; audio tail retains seconds and clamps visual frame references",
                        "Additional tail ASR words We're so back are candidates beyond published lyrics; do not silently discard them",
                        "Numeric beat analysis and author-reported tempo may differ; preserve both rather than force a grid",
                    ])
    (root / "audio_timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1) + "\n")
    (root / "qa/audio_alignment_review.json").write_text(json.dumps(dict(
        schema="ev-audio-alignment-review/v1", words=len(aligned), matched_ASR_tokens=len(matching),
        flagged_words=flags, listening_status="NOT_EVALUATED"), ensure_ascii=False, indent=1)+"\n")
    print(f"audio events={len(events)} sections={len(sections)} flagged lyric words={len(flags)}")


if __name__ == "__main__":
    main(sys.argv[1])
