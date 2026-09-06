# S01 Attempt 09 Post-Media Gate

## Identity And Verdict

**FAIL — ACTION_ENDPOINT_TIMING / PALM_ORIENTATION. No activation, no S02.**

MP4 `7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302`，3,476,468 bytes。
Request `4aa13578f273965fe32ef02c82c90a1c9dbee9f8ea79cbbd0c92038f70c55911`。
POST body `966d267e4bf7525c7d54722d3a61ee0d21607a8b451345624693f21f5d0ac9e5`。

落盘后立即project-local video_analyze：9张640px、0.5秒间隔、Whisper medium及scene detection；Agent检查全部9图。另用video_transcribe(word_timestamps=true)复核，工具仅返回segment数组，不冒称逐字对齐或人工听觉验收。明确FAIL已有直接帧证据，不为扩大证据数量执行dense extraction。

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first/last inputs | PASS | exact已批准双图及POST hash/bytes一致 |
| 1080p 9:16 output | PASS | 实测1080×1920、24fps、97帧、4.042秒H264；不证明内部native raster |
| Real LEFT hand reaches endpoint by1.5s and holds | FAIL | 1.5秒仍在抬起途中；2–3秒掌心朝镜头，未达到末帧姿态；也未满足此前2秒到位标准 |
| RIGHT phone hand on lap | PASS | 9图中右手手机留在腿上 |
| Palm orientation remains toward glass during lift | FAIL | 2–3秒明确掌心朝镜头，末尾才转正，与sealed action相反 |
| Approx2cm hover gap | NOT_EVALUATED | 单机位深度证据不足 |
| Seven other reflections retained | PASS | 9图保留七人及原边缘范围 |
| No matching Lin Yan body/hand reflection | PASS | 9图可见范围未出现对应人脸/身体/手镜像，仅为抽样视觉观察 |
| Locked camera/framing | PASS | 9图窗框/座位/竖杆及人物大小基本固定 |
| No generated caption overlay | PASS | 9图未见烧录字幕，未穷尽97帧 |
| Identity/badge details | NOT_EVALUATED | 外观延续、胸牌仍空白 |
| Native audio | PASS | AAC48kHz stereo约133kbps |
| Broadcast completes before3s | PASS | Medium segment0–2.24秒，“林燕請在終點站下車”；2.2秒prompt余量目标未达到，但在episode0.1–2.7结束窗口内；姓名同音字不证明错读 |
| Mouth/ambience/mix quality | NOT_EVALUATED | 未人工全速审听；抽样嘴唇未见明显说话 |
| Final narrative subtitle | NOT_EVALUATED | 未canonical composition |

## Scope And Stop

仅subject_action.progression不同于08，其余prompt逐字一致；seed未固定，不声称因果保证。一次POST成功后GET-only DNS恢复同一文件，strict phase=validate；额度1已消费。停止本attempt，不激活、不复用permit、不提交S02。下一步需要改变动作约束方案并重新准备exact请求，不能把末帧正确当成前3秒已达标。
