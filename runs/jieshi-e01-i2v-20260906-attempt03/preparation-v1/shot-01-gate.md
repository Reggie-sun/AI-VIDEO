# S01 Attempt 03 Post-Media Gate

## Identity And Verdict

**FAIL** — no activation, no accepted continuity source, S02 blocked.
MP4 SHA-256 `0bf686d428e7af6e11b8f191bf389565e74ca31728ef1048d9942d674e42d42c`;
4,188,741 bytes. Request `4fefcd71bc735c6296f28fddd31cdb18c7dd0e127c253afc68e7b4260fd7631d`.
Exact MP4 immediately processed by project-local `video_analyze`, 0.5-second interval,
nine frames, Whisper base and scene detection. Codex inspected all nine MCP images.
`video-analysis-summary.json` retains metadata and transcript but omits image base64;
exact original MP4 remains on disk. Agent review is not human acceptance.

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first-frame I2V | PASS | Actual POST decoded PNG SHA `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`; 2,064,319 bytes; image composition present at t=0 |
| 1080p 9:16 raster | PASS | 1080×1920, H.264, 24fps, 97 frames, 4.042s; no claim of model internal native raster |
| Real anatomical LEFT hand raises by 3s | PASS | Empty window-side left arm lifts from knee at 1s and holds up at 1.5–3s; not an image dissolve |
| RIGHT phone hand stays on lap | PASS | Right hand and black phone remain on lap in all sampled frames |
| Palm faces glass | FAIL | At 1.5–3s palm faces camera, not the window behind it |
| Hover approx 2cm from glass | NOT_EVALUATED | Perspective does not establish exact gap; incorrect palm orientation remains visible |
| Seven complete other reflections remain | FAIL | Seven present initially; camera moves and crops the rightmost reflected passenger by 3–4s |
| No Lin Yan body/hand reflection throughout | NOT_EVALUATED | No obvious corresponding body/hand in nine samples; sparse frames cannot prove all-time absence |
| Locked camera and framing | FAIL | Progressive pullback/angle shift shows more left carriage and changes window boundaries/person framing |
| No generated captions/text | FAIL | Name-like white glyphs around 2s, broadcast subtitle “请在终点站下车” at 2.5–3.5s |
| Identity/badge details | NOT_EVALUATED | Outfit and face broadly persist; badge is unreadable/blank |
| Native audio stream | PASS | AAC stereo 48kHz, ~133kbps |
| Exact native broadcast in first 3s | NOT_EVALUATED | Whisper base segment 0–4s: “零雁請在中點站下車”; not enough to distinguish name homophones, pronunciation and exact endpoint |
| Mouth still / ambience / mix quality | NOT_EVALUATED | No full perceptual audio acceptance; ASR/stream alone insufficient |
| Final narrative subtitle | NOT_EVALUATED | No canonical final composition; burned-in broadcast captions are not intended narrative caption |

## Comparison And Stop

Compared with attempt02, left-hand selection and phone stability improved in this sample;
burned-in captions and camera movement persist. Prompt wording changed, seed not controlled;
this does not prove a particular phrase caused the improvement or native audio caused captions.
One authorized new POST consumed. Known Provider success/fetch success, no blind retry or S02.
