# QA · T01-dev4.mp4

- spec: {'size': [1920, 1080], 'fps': '30/1', 'frames': 300, 'pix_fmt': 'yuv420p', 'color': ['bt709', 'bt709', 'bt709', 'tv'], 'video_kbps': 79102, 'audio': {'codec': 'aac', 'rate': '48000', 'ch': 2}, 'duration': 10.022}
- verdicts: {'spec': False, 'sync': False, 'flash': True, 'pops': True, 'strobe': True, 'outliers': True}

| event | what | key | t | expected | detected | Δframes | pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s1_title | 片名 slam | B | 0.5 | 15 | 16 | 1 | PASS |
| s1_ptz1 | PTZ 變焦第一級 | B | 1.0 | 30 | 31 | 1 | PASS |
| s1_ptz2 | PTZ 變焦第二級 | B | 1.25 | 38 | 38 | 0 | PASS |
| s1_census | 片名退場 + 計數卡第一行 | B | 2.0 | 60 | 61 | 1 | PASS |
| s1_census2 | 計數卡第二行（人类驾驶 1） | B | 2.125 | 64 | 64 | 0 | PASS |
| cut_s2 | 切 S2 車內 | B | 4.0 | 120 | 120 | 0 | PASS |
| s2_disable | 保持手动 變灰 | B | 5.5 | 165 | 167 | 2 | FAIL |
| cut_s3_drop | DROP：切 S3 + 人类驾驶 0 | H | 6.0 | 180 | 180 | 0 | PASS |
| s3_box | 最後入相光軌被框 | B | 6.5 | 195 | 196 | 1 | PASS |
| s3_time | 03:48 小字 | B | 8.0 | 240 | 242 | 2 | FAIL |

- flash: max 0/s (limit 3), transitions 0, pops []
- strobe cells: []
- outlier frames: []
- motion per bar: [{'bar': 1, 't0': 0.0, 'motion': 1.476}, {'bar': 2, 't0': 2.0, 'motion': 1.935}, {'bar': 3, 't0': 4.0, 'motion': 1.678}, {'bar': 4, 't0': 6.0, 'motion': 1.493}, {'bar': 5, 't0': 8.0, 'motion': 0.965}]
