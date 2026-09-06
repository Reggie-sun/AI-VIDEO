# S01 Attempt 08 Post-Media Gate

## Identity And Verdict

**FAIL overall — sealed action timing not met; no activation, no S02.**

2026-09-06 continuation correction：此前仅按before3s抬起判PASS，遗漏封存request-draft与compiled request明确要求第2秒前达到末帧姿态并保持。2秒图显示掌心朝镜头，约3秒才转正，因此action timing应FAIL；历史NOT_EVALUATED结论被本次纠正取代。未修改原MP4或请求。

Request `65958875804c478f4094e57f6f60ebe5dd976a930e92f9a0969d6a71b9272bc7`。
MP4 `cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e`，3,232,566 bytes。
POST body `7fcfbb100f8b4252942802bbc0dd9847af96cf1ba913daa4ca71645d0484ac56`。

Exact fetch后调用project-local video_analyze：9张640px图、0.5秒间隔、Whisper medium及scene detection。EVIDENCE_REPAIR_FIRST补充video_transcribe(word_timestamps=true)与video_extract_frames（97个时间样本）。另外ffmpeg顺序解码97帧为5份5×4 contact sheets；Agent检查全部5表及9张大图。该证据不是human full-speed acceptance。MCP转录响应仅返回segment时间，没有逐词数组，不应称为逐字对齐证明。

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first/last inputs | PASS | 两张已批准PNG经Registry/receipt及实际POST逐图hash/bytes校验 |
| 1080p 9:16 output | PASS | 1080×1920、24fps、97帧、4.042秒H264；不证明内部native raster |
| Real LEFT hand reaches endpoint before2s and holds | FAIL | 约1秒起抬空左手，2秒掌心仍朝镜头，接近3秒才转向玻璃；未达到封存动作时序，虽为真实连续动作 |
| RIGHT phone hand on lap | PASS | 顺序帧中右手手机留在腿上 |
| Palm faces window at hover | PASS | 约3–4秒手背朝镜头；2秒掌心朝镜头，之后有明显翻腕，动作自然度仍待全速审看 |
| Approx2cm hover gap | NOT_EVALUATED | 单机位没有足够深度证据确认约2cm间隙 |
| Seven other reflections retained | PASS | 顺序帧保留原图七人及边缘范围，未见新增裁切 |
| No matching Lin Yan body/hand reflection | PASS | 9张大图及顺序帧可见范围内未见对应身体、人脸或抬手镜像；限于本观察分辨率 |
| Locked camera/framing | PASS | 窗框、竖杆、座位及人物大小基本固定 |
| No generated caption overlay | PASS | 全部97帧contact sheets与9张大图未见烧录字幕 |
| Identity/badge details | NOT_EVALUATED | 外观延续已批准图片，胸牌空白；不推断不可见细节 |
| Native audio | PASS | AAC48kHz stereo约134kbps |
| Broadcast completes before3s | PASS | Medium ASR复核segment为0–2.14秒，“林燕,請在終點站下車”；同音姓名不能由ASR字形证明错读；这是自动分析层时间判定 |
| Mouth/ambience/mix quality | NOT_EVALUATED | 无全速听觉验收，尚不能证明字音、女声广播质感及混音自然度 |
| Final narrative subtitle | NOT_EVALUATED | 尚未canonical composition |

## Scope And Stop

唯一创作变量为广播起声/语速段落；相机、动作、句子内容、输入及输出参数沿用07。seed未固定，不从一次改善推导保证。单POST已消费，known succeeded/fetched/validate，首次下载DNS guard后GET-only恢复；无第二次生成。保留本候选，下一步先补full-speed人类审看及remaining required evidence，不能沿用07的通过项、静默放宽rubric、复用permit或提交S02。
