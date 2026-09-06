# S01 Attempt 02 Post-Media Gate

## Identity

Verdict: **FAIL**. S02 blocked; no activation or accepted continuity source.
Request: `cdf6a55c1d3586fbad30e5649306ef38f99d924afec645144d4daf5f9e96df9c`.
MP4 SHA-256: `49e585e89585449627431e3fe7395d64c1fa4bd42c9d400a3863fdde06fcb5f8`.
4,248,601 bytes; exact path recorded in `video-analysis-summary.json`.
Provider: Vidu `viduq3-pro`, I2V, native audio true, one submit accepted.

## Evidence

Exact fetched MP4 immediately analyzed with project-local `video_analyze`:
0.5-second interval, nine frames at 0.0 through 4.0 seconds, Whisper base,
scene detection. Codex visually inspected all nine returned images. This is
Agent review of MCP evidence, not human acceptance or automatic semantic scoring.
Summary preserves metadata/transcription/frame timestamps; embedded base64 images
are omitted from the summary and can be re-extracted from the exact retained MP4.

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Exact registered first frame drives I2V | PASS | Audited POST decoded PNG matches `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`, 2,064,319 bytes; initial composition matches |
| 9:16, 1080p raster | PASS | MCP measures 1080×1920, H.264, 24fps, 97 frames, 4.042s; no claim of native model internal raster |
| Real anatomical LEFT hand raises | FAIL | Left hand stays on knee through 4s; right arm holding phone rises between 1.5–3s |
| RIGHT hand phone remains on lap | FAIL | Phone is visibly carried upward in right hand |
| Seven others retain reflections | NOT_EVALUATED | Seven present initially; camera changes and right-edge cropping prevent full-duration proof |
| Lin Yan body/hand absent from glass throughout | NOT_EVALUATED | No obvious matching body in sampled frames; required left-hand event never occurs, sparse samples cannot prove all frames |
| Locked camera/focal framing | FAIL | Left-side carriage becomes visible and window/person scale and framing shift from 0 to 2s |
| No generated text/digits | FAIL | White name text at 0.5s; burned-in broadcast subtitle at 1–2s |
| Hover ~2cm before glass | FAIL | Required left hand never approaches glass; right hand instead holds phone |
| Identity and required badge detail | NOT_EVALUATED | Clothing/face visually similar; badge remains blank/unreadable |
| Native audio present | PASS | AAC stereo 48kHz, ~132kbps |
| Exact broadcast completed within 3s | NOT_EVALUATED | ASR 0–2.56s: “林燕,請在終點站下車”; homophonic name spelling is not proof of wrong pronunciation, nor enough for exact perceptual acceptance |
| Mouth still/no unintended speech, ambience and mix quality | NOT_EVALUATED | No full audio/perceptual review; stream presence and ASR are insufficient |
| Final narrative subtitle | NOT_EVALUATED | No final composition; generated broadcast subtitles are not the required narrative caption |

## Stop Boundary

Known Provider success and fetch success. One authorized submit consumed; no second
submit, blind retry or S02. Original failed attempt remains intact. This attempt
changed prompt constraints and native-audio selection together, so it cannot
isolate whether audio caused the burned-in captions or action change.
