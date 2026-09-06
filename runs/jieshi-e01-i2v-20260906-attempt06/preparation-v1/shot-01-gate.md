# S01 Attempt 06 Post-Media Gate

## Identity

**FAIL** — no activation, no accepted continuity source, S02 blocked.

MP4 SHA256 `041de54a023082c24cb2d4cced4ba8d068569aebdf3330496f40615eaa9ae2a4`，4,111,052 bytes。
Request `94120c86894dec85b0a4dfdd0dea81f7d17dd6a42d6e1690c976be6dd7638288`。
POST body SHA256 `cb0883b014a49665f8f8083ee9a64884a48ac8cccf2fe6a2306ba672b02fb670`。
落盘后立即调用project-local `video_analyze`，0.5秒间隔9帧、Whisper medium、scene detection；Agent检查全部9帧。

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first/last frame conditioning | PASS | POST精确核对同一首帧4134d691…30fb、末帧059bb2b2…1330及bytes，两份已批准receipt/Registry/request一致 |
| 1080p 9:16 raster | PASS | 实测1080×1920、H264、24fps、97帧、4.042秒；metadata内部含720p，不据此证明模型内部原生raster |
| Real LEFT hand reaches target before3s | PASS | 1.5秒开始抬空左手，2.5秒已伸指并转向目标掌向，3秒保持；未达本次prompt更早的2秒目标，但满足原前三秒验收要求 |
| RIGHT phone hand stays on lap | PASS | 九帧中手机仍在右手、保持腿部位置 |
| Palm faces glass at target | PASS | 2.5–4秒为手背朝镜头、掌心朝玻璃 |
| Approx2cm hovering gap | NOT_EVALUATED | 缺少可量定的深度/间隙证据 |
| Seven complete other reflections remain | FAIL | 中段构图变化使最右乘客进一步被画面边缘裁切 |
| No Lin Yan body/hand reflection throughout | NOT_EVALUATED | 样本未见对应镜像，不能以稀疏采样证明全时段缺失 |
| Locked camera and framing | FAIL | 0.5–3秒窗框、人物及腿部在画面中明显位移/缩放，末帧才回到端点构图 |
| No generated captions/text throughout | NOT_EVALUATED | 九帧未见烧入字幕；未完成全97帧文字检查 |
| Identity/badge details | NOT_EVALUATED | 人物外观大体保持、胸牌仍空白 |
| Native audio stream | PASS | AAC48kHz stereo约132kbps |
| Exact broadcast before3s | NOT_EVALUATED | Medium ASR在0–2.6秒识别“林燕,請在終點站下車”，与目标读音/句子相符且较05改善；无完整听觉证据，不把ASR或同音字当作最终对白验收 |
| Mouth still / ambience / mix quality | NOT_EVALUATED | 仅帧采样/ASR，无全速音画及混音确认 |
| Final narrative subtitle | NOT_EVALUATED | 尚未canonical composition |

## Stop

Provider known succeeded，canonical fetched/validate。第一次下载受public HTTPS guard阻断，GET-only DNS恢复取得同一文件，POST总数1。当前封存的一次提交额度已消费，不能复用permit或自动增加额度。

相对05，变化为提示词表达（动作时序和广播措辞），非fixed-seed single-phrase controlled comparison。改善与回退均是本次样本观察，不构成因果或全模型能力结论。
