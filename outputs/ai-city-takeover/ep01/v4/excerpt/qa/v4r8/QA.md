# QA · IRIS EP01 v4 excerpt 026-059

Render: `outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v4-excerpt-v4r8-036-059.mp4`
Overall: **PASS**

## Spec
PASS · 1920x1080 · 24/1 fps · 552 frames · h264 yuv420p · colour bt709/bt709/bt709 · audio {'codec': 'aac', 'rate': '48000', 'channels': 2, 'bit_rate': '321335'}

## Sound (master, no loudness change)
PASS · offset against the master slice 0 samples (0.0 ms) · RMS difference -0.016 dB

## Cuts on beats (every cut within 0.03 s of a beat; the picture changes on that frame)

| cut | planned | nearest beat | planned-beat | frame | frame time | frame-beat | render changes on | result |
|---|---|---|---|---|---|---|---|---|
| s010:X10b | 39.8454 | 39.8454 | +0.0000 | 87 | 39.8445 | -0.0009 | 87 | PASS |
| s011 | 40.7859 | 40.7859 | +0.0000 | 110 | 40.8028 | +0.0169 | 110 | PASS |
| s012a | 44.9422 | 44.9422 | +0.0000 | 209 | 44.9278 | -0.0144 | 209 | PASS |
| s012a:p012w1-engineer | 45.8594 | 45.8594 | +0.0000 | 231 | 45.8445 | -0.0149 | 231 | PASS |
| s012b | 46.7882 | 46.7882 | +0.0000 | 254 | 46.8028 | +0.0146 | 254 | PASS |
| s012c | 49.087 | 49.087 | +0.0000 | 309 | 49.0945 | +0.0075 | 309 | PASS |
| s012d | 50.4686 | 50.4686 | +0.0000 | 342 | 50.4695 | +0.0009 | 342 | PASS |
| s013a | 50.933 | 50.933 | +0.0000 | 353 | 50.9278 | -0.0052 | 353 | PASS |
| s013b | 52.3146 | 52.3146 | +0.0000 | 386 | 52.3028 | -0.0118 | 386 | PASS |
| s014a | 55.0777 | 55.0777 | +0.0000 | 453 | 55.0945 | +0.0168 | 453 | PASS |
| s014b | 57.3765 | 57.3765 | +0.0000 | 508 | 57.3861 | +0.0096 | 508 | PASS |
| s014c | 58.7697 | 58.7697 | +0.0000 | 541 | 58.7611 | -0.0086 | 541 | PASS |

Other frames whose change passes 80% of the smallest cut: [21, 65, 374] (in-shot events, each on a beat: f181-182 the s009 rack to the lightbox at 33.437, f332 ALL slammed at 39.897, f355 the s011 rows snapping on, f433 EVERYBODY, at 44.077, f709 the s014 punch at 55.542, f786-788 the push to the pager at 58.726; checked on the contact sheet).

## Lyrics
PASS · **37/37** words of words.json inside 26.0528-59.2341 drawn on their onset frame, held 8 frames (or to their end / the excerpt end), none early. Source: the engine's own word log (snap.mjs --marks), every frame.

| line | word | onset (s) | onset frame | first frame drawn | frames on | result |
|---|---|---|---|---|---|---|
| 5 | Freeway: | 36.363 | 3 | 3 | 99 | PASS |
| 5 | S | 37.226 | 24 | 24 | 78 | PASS |
| 5 | F | 37.426 | 29 | 29 | 73 | PASS |
| 5 | hates | 37.527 | 31 | 31 | 71 | PASS |
| 5 | A | 37.868 | 40 | 40 | 62 | PASS |
| 5 | I | 38.048 | 44 | 44 | 58 | PASS |
| 5 | billboars. | 38.129 | 46 | 46 | 56 | PASS |
| 5 | The | 38.751 | 61 | 61 | 41 | PASS |
| 5 | D? | 38.931 | 65 | 65 | 37 | PASS |
| 5 | Forgot. | 39.674 | 83 | 83 | 19 | PASS |
| 6 | All | 39.897 | 88 | 88 | 100 | PASS |
| 6 | hands! | 40.861 | 111 | 111 | 77 | PASS |
| 6 | All | 42.247 | 145 | 145 | 43 | PASS |
| 6 | night! | 42.769 | 157 | 157 | 32 | PASS |
| 7 | Everybody, | 44.077 | 189 | 189 | 65 | PASS |
| 7 | hold | 45.625 | 226 | 226 | 28 | PASS |
| 7 | on | 46.047 | 236 | 236 | 18 | PASS |
| 7 | tight | 46.308 | 242 | 242 | 12 | PASS |
| 8 | I&#x27;m | 47.517 | 271 | 271 | 82 | PASS |
| 8 | the | 47.919 | 281 | 281 | 72 | PASS |
| 8 | reason | 48.181 | 287 | 287 | 66 | PASS |
| 8 | you&#x27;re | 49.307 | 314 | 314 | 39 | PASS |
| 8 | awake | 49.89 | 328 | 328 | 25 | PASS |
| 9 | I&#x27;m | 51.239 | 360 | 360 | 81 | PASS |
| 9 | the | 51.62 | 370 | 370 | 71 | PASS |
| 9 | call | 51.76 | 373 | 373 | 68 | PASS |
| 9 | you | 53.024 | 403 | 403 | 38 | PASS |
| 9 | had | 53.224 | 408 | 408 | 33 | PASS |
| 9 | to | 53.445 | 413 | 413 | 28 | PASS |
| 9 | take | 53.645 | 418 | 418 | 23 | PASS |
| 10 | All | 53.767 | 421 | 421 | 122 | PASS |
| 10 | hands! | 54.59 | 441 | 441 | 102 | PASS |
| 10 | All | 55.152 | 454 | 454 | 89 | PASS |
| 10 | night! | 55.513 | 463 | 463 | 80 | PASS |
| 11 | Ten | 58.726 | 540 | 540 | 12 | PASS |
| 11 | oh | 59.027 | 547 | 547 | 5 | PASS |
| 11 | two, | 59.187 | 551 | 551 | 1 | PASS |

## Flashes and single-frame jumps
PASS · worst cell 1.0 flashes in any second (limit 3, WCAG 2.3.1 general flash on a 4x4 grid) · single-frame jumps: 0

## No Chinese on screen
PASS · CJK in drawn strings: none · CJK glyphs in the shipped fonts: 0 (the fonts cannot draw Chinese)

## Red
PASS · 138 frames (every 4th), 0 with saturated red, 0 with more than 12 px (at 960x540) outside her matte or the P0 ALERT RAISED label. Worst frames: f0 0 px, f4 0 px, f8 0 px, f12 0 px, f16 0 px

Sheets: `qa/contact-every-6-frames.jpg`, `qa/red-outside-map.png`
