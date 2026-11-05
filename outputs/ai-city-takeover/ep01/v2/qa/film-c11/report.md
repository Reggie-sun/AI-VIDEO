# QA · EP01-film-c11.mp4

- spec: {'size': [1920, 1080], 'fps': '30/1', 'frames': 915, 'pix_fmt': 'yuv420p', 'color': ['bt709', 'bt709', 'bt709', 'tv'], 'video_kbps': 64394, 'audio': {'codec': 'aac', 'rate': '48000', 'ch': 2}, 'duration': 30.522, 'video_duration': 30.5}
- verdicts: {'spec': True, 'sync': True, 'flash': True, 'frames_match_comp': True, 'pops': True, 'strobe': True, 'outliers': True}

| event | what | key | t | expected | detected | Δframes | pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cut_S2 | cut to S2 |  | 2.8667 | 86 | 86 | 0 | PASS |
| cut_S3 | cut to S3 |  | 4.8 | 144 | 144 | 0 | PASS |
| cut_S4 | cut to S4 |  | 8.1333 | 244 | 244 | 0 | PASS |
| cut_S5 | cut to S5 |  | 11.4667 | 344 | 344 | 0 | PASS |
| cut_S6 | cut to S6 |  | 13.3667 | 401 | 401 | 0 | PASS |
| cut_S7 | cut to S7 |  | 14.8 | 444 | 444 | 0 | PASS |
| cut_S8a | cut to S8a |  | 18.8667 | 566 | 566 | 0 | PASS |
| cut_S8b | cut to S8b |  | 22.5667 | 677 | 677 | 0 | PASS |
| cut_S9a | cut to S9a |  | 25.9 | 777 | 777 | 0 | PASS |
| cut_S9b | cut to S9b |  | 28.3 | 849 | 849 | 0 | PASS |
| cut_S3d | cut to S3d |  | 7.1 | 213 | 213 | 0 | PASS |
| cut_S4c | cut to S4c |  | 9.7333 | 292 | 292 | 0 | PASS |
| cut_S5d | cut to S5d |  | 12.1 | 363 | 363 | 0 | PASS |
| cut_S9h | cut to S9h |  | 29.1333 | 874 | 874 | 0 | PASS |
| cut_S9b2 | cut to S9b2 |  | 29.7333 | 892 | 892 | 0 | PASS |
| cut_S8e | cut to S8e |  | 21.3667 | 641 | 641 | 0 | PASS |
| cut_S8a2 | cut to S8a2 |  | 21.8667 | 656 | 656 | 0 | PASS |
| cut_S8b_x | cut to S8b_x |  | 24.0667 | 722 | 722 | 0 | PASS |
| cut_S8w | cut to S8w |  | 24.7333 | 742 | 742 | 0 | PASS |
| cut_S8b_x2 | cut to S8b_x2 |  | 25.1667 | 755 | 755 | 0 | PASS |
| chorus_impact | impact on the chorus entry hit (picture one frame early) |  | 19.0667 | 572 | 571 | -1 | PASS |
| s1_timecode | 03:47 lands on beat 1 |  | 0.5 | 15 | 15 | 0 | PASS |
| s2_title | title slams in with the cut |  | 2.8667 | 86 | 86 | 0 | PASS |
| s2_date | incident date OSD on 'September' |  | 3.8333 | 115 | 115 | 0 | PASS |
| s3_model | 研究模型 on 'training' |  | 5.0667 | 152 | 152 | 0 | PASS |
| s3_resolver | DNS 解析器 on 'resolver' |  | 6.1 | 183 | 184 | 1 | PASS |
| s3d_error | resolver node turns red on 'misconfigured' |  | 7.1667 | 215 | 214 | -1 | PASS |
| s4_reach | the probe breaches the glass on 'reached' |  | 9.8333 | 295 | 295 | 0 | PASS |
| s5d_count | the eleven-day count starts on 'Eleven' |  | 12.1667 | 365 | 365 | 0 | PASS |
| s5_window | far window lights on 'around' |  | 11.5333 | 346 | 347 | 1 | PASS |
| s6_pause | 最强模型训练 暂停 11 天 |  | 13.4 | 402 | 402 | 0 | PASS |
| s7_offline | 离线 with the cut |  | 14.8 | 444 | 444 | 0 | PASS |
| s9a_shut | door shut, 已修复 tag |  | 28.2 | 846 | 847 | 1 | PASS |
| s9b_redteam | 另一项红队测试 |  | 28.3333 | 850 | 851 | 1 | PASS |
| s9b_card | 03:48 card |  | 30.1 | 903 | 903 | 0 | PASS |
| k_still | STILL on 'still' |  | 14.0667 | 422 | 422 | 0 | PASS |
| k_offline | OFFLINE on 'offline' |  | 15.6667 | 470 | 470 | 0 | PASS |
| s9a_invert | white-ground inversion on the beat of 'The door' |  | 27.1667 | 815 | 815 | 0 | PASS |
| s9a_invert_end | back to the dark ground 1.5 beats later |  | 27.9 | 837 | 837 | 0 | PASS |
| k_closed | CLOSED on 'closed' (inverted ground) |  | 27.5333 | 826 | 826 | 0 | PASS |

- flash: max 1/s (limit 3), transitions 11, pops []
- strobe cells: []
- outlier frames: []
- motion per bar: [{'bar': 1, 't0': 0.035, 'motion': 2.142}, {'bar': 2, 't0': 1.916, 'motion': 3.409}, {'bar': 3, 't0': 3.82, 'motion': 2.825}, {'bar': 4, 't0': 5.724, 'motion': 2.76}, {'bar': 5, 't0': 7.628, 'motion': 1.815}, {'bar': 6, 't0': 9.532, 'motion': 2.989}, {'bar': 7, 't0': 11.436, 'motion': 3.61}, {'bar': 8, 't0': 13.351, 'motion': 2.453}, {'bar': 9, 't0': 15.255, 'motion': 2.084}, {'bar': 10, 't0': 17.16, 'motion': 2.932}, {'bar': 11, 't0': 19.064, 'motion': 3.33}, {'bar': 12, 't0': 20.979, 'motion': 4.936}, {'bar': 13, 't0': 22.872, 'motion': 3.13}, {'bar': 14, 't0': 24.776, 'motion': 3.928}, {'bar': 15, 't0': 26.68, 'motion': 7.802}, {'bar': 16, 't0': 28.584, 'motion': 3.006}]
