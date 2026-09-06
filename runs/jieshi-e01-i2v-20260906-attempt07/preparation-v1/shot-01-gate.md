# S01 Attempt 07 Post-Media Gate

## Identity And Verdict

**FAIL** — broadcast timing; no activation, no S02.

MP4 `88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e`，3,350,152 bytes。
Request `593e3c56176d80fc97e3c1bba9c10f9ef4196206b1b4ddbb887fb947ec965c11`。
POST body `62fe2899d163bf9f970dbca14fb0613efb00995f984539b0613af134c8398139`。

Exact fetch后立即project-local `video_analyze`：9帧640px、0.5秒、Whisper medium、scene detection。随后执行EVIDENCE_REPAIR_FIRST：MCP dense extraction返回97个时间样本；MCP word_timestamps复核广播；ffmpeg顺序解码97帧为5份5×4 contact sheets（每格256px，最后3格黑色padding）。Agent查看全部5表及原9张大图。该视觉观察不等同human full-speed acceptance。

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first/last inputs | PASS | 原两张已批准PNG逐图POST hash/bytes校验，Registry和receipt不变 |
| 1080p 9:16 output | PASS | 实测1080×1920、24fps、97帧、4.042秒H264；不证明内部native raster |
| Real LEFT hand before3s | PASS | 0.5秒起抬空左手，约2秒达到目标姿态并保持；顺序帧为真实动作 |
| RIGHT phone hand on lap | PASS | 全部顺序帧中右手手机留在腿上 |
| Palm faces window at hover | PASS | 约2–4秒手背朝镜头、掌心朝玻璃 |
| Approx2cm hover gap | NOT_EVALUATED | 单机位无法可靠量定手与玻璃的深度间隙 |
| Seven other reflections retained | PASS | 全部顺序帧中七人构图保持，未见06中段新增边缘裁切；保留原输入的边缘范围 |
| No matching Lin Yan body/hand reflection | PASS | 9张大图与全部顺序帧可见范围内未出现对应人脸、身体或抬手镜像；为本分辨率的Agent视觉判定 |
| Locked camera/framing | PASS | 全部顺序帧中窗框、竖杆、座位和人物大小基本固定；无06明显推移/缩放 |
| No generated caption overlay | PASS | 全部97帧contact sheets及9张大图未见烧录字幕；不将其外推为模型保证 |
| Identity/badge details | NOT_EVALUATED | 人物外观保持，胸牌仍空白 |
| Native audio | PASS | AAC48kHz stereo约134kbps |
| Broadcast completes before3s | FAIL | Medium word_timestamps段落0.84–3.40秒，识别“林彥,請在終點站下車。”；ASR对齐支持超时判定，非人工听觉验收 |
| Mouth/ambience/mix quality | NOT_EVALUATED | 画面未见明显说话，尚无全速听觉/混音确认 |
| Final narrative subtitle | NOT_EVALUATED | 尚未canonical composition |

## Scope And Stop

仅camera_intent的stability/framing文字不同于06；替回旧值后compiled prompt完全相同，independent reviewer_xhigh verified。seed未固定，不据单次结果作因果保证。Provider known succeeded/fetched/validate，GET-only DNS恢复同一任务文件，POST总数1。额度已消费，不复用permit、不推进S02。
