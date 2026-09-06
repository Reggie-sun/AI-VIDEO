# S01 Attempt 05 Post-Media Gate

## Identity And Verdict

**FAIL** — S02 blocked; no activation or accepted continuity source.

Exact MP4 `292aae3a02357a96e129879af07b19ff6340c37f801d8bc7833d82fa7b2588cb`, 3,689,055 bytes.
Request `83680c436cf3694be09a2982e1ac8d110ef5aafe2b5bdc41fd39e1a812649f68`.
实际 POST body SHA256 `3210c156ec733ba127efa2c6ad2b22b42b9410ef43c9a67bfcfeccf895756aee`。
落盘后立即调用 project-local `video_analyze`，0.5秒间隔9帧、Whisper base、scene detection；Agent查看全部9帧。

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first/last frame conditioning | PASS | POST逐张验证首帧4134d691…30fb和末帧059bb2b2…1330；canonical receipt/Registry/request相符 |
| 1080p 9:16 raster | PASS | 实测1080×1920 H264、24fps、97帧、4.042秒；metadata内部标签含720p，不据此推断模型内部原生分辨率 |
| Real anatomical LEFT hand raises and settles by 3s | FAIL | 1.5秒开始抬空左手；3秒仍弯指且掌心偏向镜头，3.5–4秒才转向目标姿态；真实动作存在，时间要求未满足 |
| RIGHT phone hand stays on lap | PASS | 9帧中右手手机均保持腿部位置 |
| Palm faces glass at target hover | PASS | 3.5–4秒可见手背，手掌朝向窗；相对attempt04改善，不消除动作迟到FAIL |
| Hover approx 2cm from glass | NOT_EVALUATED | 单机位透视不足以量定2厘米，无法证明最终稳定悬停间隙 |
| Seven complete other reflections remain | NOT_EVALUATED | 9帧中同组七人仍可辨认且右端未见明显新增裁切；不声称全时段完整性已证实 |
| No Lin Yan body/hand reflection throughout | NOT_EVALUATED | 样本未见新增对应手镜像；稀疏帧不足以证明全时段无倒影 |
| Locked camera and framing | PASS | 9帧中窗框与背景排列基本保持，未见attempt04的大幅构图漂移；仅该观察精度 |
| No generated captions/text throughout | NOT_EVALUATED | 9帧未见烧入字幕；未进行全97帧文字检查，不能把采样结果外推为全片证明 |
| Identity/badge details | NOT_EVALUATED | 人物服装保持，胸牌仍空白，无可验收姓名 |
| Native audio stream | PASS | AAC、48kHz、stereo、约136kbps |
| Exact native broadcast in first 3s | NOT_EVALUATED | Whisper base仅识别“请选中原写”，0–2秒；不将不可靠ASR等同真实台词，但指定广播尚未证实 |
| Mouth still / ambience / mix quality | NOT_EVALUATED | 样本无明显口型说话，不代替全速音画/混音验收 |
| Final narrative subtitle | NOT_EVALUATED | 尚未canonical final composition |

## Stop And Comparison

本次真实使用首尾两张图片和 `/start-end2video`，末尾掌向与采样构图改善；动作迟到、广播未证实，仍未达标。
无字幕样本与旧first-frame-only烧字记录属于不同输入/endpoint，且本次尚无全片文字PASS；不能推断末帧导致去字幕或native audio路线已稳定成功。

Provider结果known succeeded，canonical fetched/validate。首次下载被public HTTPS guard阻断后，沿既有GET-only DNS恢复取得同一任务文件；总POST=1。当前封存的一次提交额度已消费，禁止复用permit或自动新增额度。
