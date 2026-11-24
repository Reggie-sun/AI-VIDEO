# QA · IRIS EP01 v4 excerpt 026-059

Render: `outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v4-excerpt-026-059-v3.mp4`
Overall: **PASS**

## Spec
PASS · 1920x1080 · 24/1 fps · 796 frames · h264 yuv420p · colour bt709/bt709/bt709 · audio {'codec': 'aac', 'rate': '48000', 'channels': 2, 'bit_rate': '321407'}

## Sound (master, no loudness change)
PASS · offset against the master slice 0 samples (0.0 ms) · RMS difference -0.022 dB

## Cuts on beats (every cut within 0.03 s of a beat; the picture changes on that frame)

| cut | planned | nearest beat | planned-beat | frame | frame time | frame-beat | render changes on | result |
|---|---|---|---|---|---|---|---|---|
| s008 | 29.7448 | 29.7448 | +0.0000 | 89 | 29.7611 | +0.0163 | 89 | PASS |
| s009 | 31.1263 | 31.1263 | +0.0000 | 122 | 31.1361 | +0.0098 | 122 | PASS |
| s009:X09b | 35.2827 | 35.2827 | +0.0000 | 222 | 35.3028 | +0.0201 | 222 | PASS |
| s010 | 36.1999 | 36.1999 | +0.0000 | 244 | 36.2195 | +0.0196 | 244 | PASS |
| s010:X10b | 39.8454 | 39.8454 | +0.0000 | 331 | 39.8445 | -0.0009 | 331 | PASS |
| s011 | 40.7859 | 40.7859 | +0.0000 | 354 | 40.8028 | +0.0169 | 354 | PASS |
| s012 | 44.9422 | 44.9422 | +0.0000 | 453 | 44.9278 | -0.0144 | 453 | PASS |
| s012:X12b | 48.1698 | 48.1698 | +0.0000 | 531 | 48.1778 | +0.0080 | 531 | PASS |
| s013 | 50.933 | 50.933 | +0.0000 | 597 | 50.9278 | -0.0052 | 597 | PASS |
| s014 | 55.0777 | 55.0777 | +0.0000 | 697 | 55.0945 | +0.0168 | 697 | PASS |

Other frames whose change passes 80% of the smallest cut: [44, 111, 177, 232, 265, 309, 431, 575, 619, 664, 752, 785] (in-shot events, each on a beat: f181-182 the s009 rack to the lightbox at 33.437, f332 ALL slammed at 39.897, f355 the s011 rows snapping on, f433 EVERYBODY, at 44.077, f709 the s014 punch at 55.542, f786-788 the push to the pager at 58.726; checked on the contact sheet).

## Lyrics
PASS · **64/64** words of words.json inside 26.0528-59.2341 drawn on their onset frame, held 8 frames (or to their end / the excerpt end), none early. Source: the engine's own word log (snap.mjs --marks), every frame.

| line | word | onset (s) | onset frame | first frame drawn | frames on | result |
|---|---|---|---|---|---|---|
| 2 | Six | 25.991 | 0 | 0 | 89 | PASS |
| 2 | grand | 26.293 | 6 | 6 | 83 | PASS |
| 2 | a | 26.594 | 13 | 13 | 76 | PASS |
| 2 | month | 26.695 | 15 | 15 | 74 | PASS |
| 2 | for | 27.138 | 26 | 26 | 63 | PASS |
| 2 | a | 27.319 | 30 | 30 | 59 | PASS |
| 2 | billboard | 27.399 | 32 | 32 | 57 | PASS |
| 2 | behind | 28.083 | 49 | 49 | 40 | PASS |
| 2 | a | 28.465 | 58 | 58 | 31 | PASS |
| 2 | tree. | 28.546 | 60 | 60 | 29 | PASS |
| 3 | A | 29.313 | 78 | 78 | 84 | PASS |
| 3 | I: | 29.695 | 87 | 87 | 75 | PASS |
| 3 | Average | 30.238 | 100 | 100 | 62 | PASS |
| 3 | Individual. | 30.681 | 111 | 111 | 51 | PASS |
| 3 | That&#x27;s | 32.007 | 143 | 143 | 35 | PASS |
| 3 | me. | 32.289 | 150 | 150 | 28 | PASS |
| 4 | Bus | 32.934 | 165 | 165 | 57 | PASS |
| 4 | stop: | 33.094 | 169 | 169 | 53 | PASS |
| 4 | I&#x27;m | 33.595 | 181 | 181 | 41 | PASS |
| 4 | not | 33.655 | 182 | 182 | 40 | PASS |
| 4 | taking | 33.836 | 187 | 187 | 35 | PASS |
| 4 | your | 34.116 | 194 | 194 | 28 | PASS |
| 4 | job. | 34.297 | 198 | 198 | 24 | PASS |
| 4 | Someone | 34.758 | 209 | 209 | 35 | PASS |
| 4 | scratched | 35.158 | 219 | 219 | 25 | PASS |
| 4 | the | 35.599 | 229 | 229 | 15 | PASS |
| 4 | not. | 35.78 | 233 | 233 | 11 | PASS |
| 5 | Freeway: | 36.363 | 247 | 247 | 84 | PASS |
| 5 | S | 37.226 | 268 | 268 | 63 | PASS |
| 5 | F | 37.426 | 273 | 273 | 58 | PASS |
| 5 | hates | 37.527 | 275 | 275 | 56 | PASS |
| 5 | A | 37.868 | 284 | 284 | 47 | PASS |
| 5 | I | 38.048 | 288 | 288 | 43 | PASS |
| 5 | billboars. | 38.129 | 290 | 290 | 41 | PASS |
| 5 | The | 38.751 | 305 | 305 | 41 | PASS |
| 5 | D? | 38.931 | 309 | 309 | 37 | PASS |
| 5 | Forgot. | 39.674 | 327 | 327 | 19 | PASS |
| 6 | All | 39.897 | 332 | 332 | 99 | PASS |
| 6 | hands! | 40.861 | 355 | 355 | 76 | PASS |
| 6 | All | 42.247 | 389 | 389 | 42 | PASS |
| 6 | night! | 42.769 | 401 | 401 | 32 | PASS |
| 7 | Everybody, | 44.077 | 433 | 433 | 81 | PASS |
| 7 | hold | 45.625 | 470 | 470 | 44 | PASS |
| 7 | on | 46.047 | 480 | 480 | 34 | PASS |
| 7 | tight | 46.308 | 486 | 486 | 28 | PASS |
| 8 | I&#x27;m | 47.517 | 515 | 515 | 82 | PASS |
| 8 | the | 47.919 | 525 | 525 | 72 | PASS |
| 8 | reason | 48.181 | 531 | 531 | 66 | PASS |
| 8 | you&#x27;re | 49.307 | 558 | 558 | 39 | PASS |
| 8 | awake | 49.89 | 572 | 572 | 25 | PASS |
| 9 | I&#x27;m | 51.239 | 604 | 604 | 80 | PASS |
| 9 | the | 51.62 | 614 | 614 | 70 | PASS |
| 9 | call | 51.76 | 617 | 617 | 67 | PASS |
| 9 | you | 53.024 | 647 | 647 | 37 | PASS |
| 9 | had | 53.224 | 652 | 652 | 32 | PASS |
| 9 | to | 53.445 | 657 | 657 | 27 | PASS |
| 9 | take | 53.645 | 662 | 662 | 22 | PASS |
| 10 | All | 53.767 | 665 | 665 | 117 | PASS |
| 10 | hands! | 54.59 | 685 | 685 | 97 | PASS |
| 10 | All | 55.152 | 698 | 698 | 84 | PASS |
| 10 | night! | 55.513 | 707 | 707 | 75 | PASS |
| 11 | Ten | 58.726 | 784 | 784 | 12 | PASS |
| 11 | oh | 59.027 | 791 | 791 | 5 | PASS |
| 11 | two, | 59.187 | 795 | 795 | 1 | PASS |

## Flashes and single-frame jumps
PASS · worst cell 1.0 flashes in any second (limit 3, WCAG 2.3.1 general flash on a 4x4 grid) · single-frame jumps: 0

## No Chinese on screen
PASS · CJK in drawn strings: none · CJK glyphs in the shipped fonts: 0 (the fonts cannot draw Chinese)

## Red
PASS · 199 frames (every 4th), 157 with saturated red, 0 with more than 12 px (at 960x540) outside her matte or the P0 ALERT RAISED label. Worst frames: f0 0 px, f4 0 px, f8 0 px, f12 0 px, f16 0 px

Sheets: `qa/contact-every-6-frames.jpg`, `qa/red-outside-map.png`
