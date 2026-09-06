# S01 Attempt 04 Post-Media Gate

## Identity And Verdict

**FAIL** — no activation, no accepted continuity source, S02 blocked.

Exact MP4 SHA-256 `934f7498223dc6545396b868c7c6d31ea7dbd3015a80d34f19950087bb697bec`,
3,517,773 bytes. Request `b66d3b87c97390eacddd01140785d1702d6f566e82881908123ac576700f55c3`.
落盘后立即调用 project-local `video_analyze`，0.5 秒间隔、9 帧、Whisper base、scene detection。
Codex 查看全部九帧；summary 保存 metadata/transcript/frame timestamps，省略 base64。
这是 Agent 对 MCP 原始证据的审查，不是 human acceptance。

| Required finding | Verdict | Evidence |
| --- | --- | --- |
| Registered first-frame I2V | PASS | 实际 POST 解码 PNG SHA `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`；t=0 沿用构图 |
| 1080p 9:16 raster | PASS | 1080×1920、H.264、24fps、97帧、4.042s；不证明模型内部原生 raster |
| Real anatomical LEFT hand raises by 3s | PASS | 0.5–1.5s 空左手从膝上抬起，之后悬停；不是图片渐变 |
| RIGHT phone hand stays on lap | PASS | 九个样本中右手与手机保持腿部位置 |
| Palm faces glass | FAIL | 1.5–4s 掌心朝向镜头，与要求相反 |
| Hover approx 2cm from glass | NOT_EVALUATED | 错误朝向且透视不足以量定2厘米 |
| Seven complete other reflections remain | FAIL | 初始七人；机位移动后最右人物进一步出框，不能保持完整七人 |
| No Lin Yan body/hand reflection throughout | NOT_EVALUATED | 九个稀疏样本不足以证明全时段身体／手镜像缺失 |
| Locked camera and framing | FAIL | 窗框、座位和人物的画面位置持续变化，出现角度／构图漂移 |
| No generated captions/text | FAIL | 1.5–3.5s 烧入“林…”错误姓名及“在终点站下车”白色字幕，字幕不是既定叙事句 |
| Identity/badge details | NOT_EVALUATED | 衣着大体保持，胸牌仍无可验收姓名 |
| Native audio stream | PASS | AAC、48kHz、stereo、约130kbps |
| Exact native broadcast in first 3s | NOT_EVALUATED | Whisper base 为“零雁在終點站下車”，0–4s粗粒度段；未证明准确姓名、请字及2.7s截止 |
| Mouth still / ambience / mix quality | NOT_EVALUATED | 采样画面未见明显说话，不足以代替完整听觉与口型验收 |
| Final narrative subtitle | NOT_EVALUATED | 尚未 canonical final composition；生成物字幕不能代替既定叙事字幕 |

## Comparison And Stop

相对 attempt03，本次实际使用 compiler2 prose 与 `is_rec=false`，仍出现烧入字幕、
掌心朝镜头及机位漂移。原生音轨和真实左手动作存在；不能宣称本次封装改进已解决质量问题。
两项请求表达同时变化且 seed 未固定，不推断某一参数的因果作用或整个模型的能力上限。
Provider outcome known：同一任务成功并 canonical fetched/validate；一次提交额度已消费，
没有再提交或推进 S02。下载使用已有 GET-only DNS 恢复，不是第二次生成。
