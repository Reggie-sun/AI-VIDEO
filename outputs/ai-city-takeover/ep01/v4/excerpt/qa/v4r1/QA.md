# QA · IRIS EP01 v4 excerpt 026-059

Render: `outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v4-excerpt-v4r1-036-051.mp4`
Overall: **PASS**

## Spec
PASS · 1920x1080 · 24/1 fps · 353 frames · h264 yuv420p · colour bt709/bt709/bt709 · audio {'codec': 'aac', 'rate': '48000', 'channels': 2, 'bit_rate': '321884'}

## Sound (master, no loudness change)
PASS · offset against the master slice 0 samples (0.0 ms) · RMS difference -0.013 dB

## Cuts on beats (every cut within 0.03 s of a beat; the picture changes on that frame)

| cut | planned | nearest beat | planned-beat | frame | frame time | frame-beat | render changes on | result |
|---|---|---|---|---|---|---|---|---|
| s010:X10b | 39.8454 | 39.8454 | +0.0000 | 87 | 39.8445 | -0.0009 | 87 | PASS |
| s011 | 40.7859 | 40.7859 | +0.0000 | 110 | 40.8028 | +0.0169 | 110 | PASS |
| s012a | 44.9422 | 44.9422 | +0.0000 | 209 | 44.9278 | -0.0144 | 209 | PASS |
| s012a:p012w1-engineer | 45.8594 | 45.8594 | +0.0000 | 231 | 45.8445 | -0.0149 | 231 | PASS |
| s012b | 46.7882 | 46.7882 | +0.0000 | 254 | 46.8028 | +0.0146 | 254 | PASS |

Other frames whose change passes 80% of the smallest cut: [21, 65, 287] (in-shot events, each on a beat: f181-182 the s009 rack to the lightbox at 33.437, f332 ALL slammed at 39.897, f355 the s011 rows snapping on, f433 EVERYBODY, at 44.077, f709 the s014 punch at 55.542, f786-788 the push to the pager at 58.726; checked on the contact sheet).

## Lyrics
PASS · **23/23** words of words.json inside 26.0528-59.2341 drawn on their onset frame, held 8 frames (or to their end / the excerpt end), none early. Source: the engine's own word log (snap.mjs --marks), every frame.

| line | word | onset (s) | onset frame | first frame drawn | frames on | result |
|---|---|---|---|---|---|---|
| 5 | Freeway: | 36.363 | 3 | 3 | 84 | PASS |
| 5 | S | 37.226 | 24 | 24 | 63 | PASS |
| 5 | F | 37.426 | 29 | 29 | 58 | PASS |
| 5 | hates | 37.527 | 31 | 31 | 56 | PASS |
| 5 | A | 37.868 | 40 | 40 | 47 | PASS |
| 5 | I | 38.048 | 44 | 44 | 43 | PASS |
| 5 | billboars. | 38.129 | 46 | 46 | 41 | PASS |
| 5 | The | 38.751 | 61 | 61 | 41 | PASS |
| 5 | D? | 38.931 | 65 | 65 | 37 | PASS |
| 5 | Forgot. | 39.674 | 83 | 83 | 19 | PASS |
| 6 | All | 39.897 | 88 | 88 | 99 | PASS |
| 6 | hands! | 40.861 | 111 | 111 | 76 | PASS |
| 6 | All | 42.247 | 145 | 145 | 42 | PASS |
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

## Flashes and single-frame jumps
PASS · worst cell 1.0 flashes in any second (limit 3, WCAG 2.3.1 general flash on a 4x4 grid) · single-frame jumps: 0

## No Chinese on screen
PASS · CJK in drawn strings: none · CJK glyphs in the shipped fonts: 0 (the fonts cannot draw Chinese)

## Red
PASS · 89 frames (every 4th), 47 with saturated red, 0 with more than 12 px (at 960x540) outside her matte or the P0 ALERT RAISED label. Worst frames: f0 0 px, f4 0 px, f8 0 px, f12 0 px, f16 0 px

Sheets: `qa/contact-every-6-frames.jpg`, `qa/red-outside-map.png`
