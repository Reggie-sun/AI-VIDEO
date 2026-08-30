# V12 Final Gate

Date: 2026-08-27

## Exact Artifact

- Primary: `artifacts/qingyan-miao-ad-20260827-v12/final/青颜_苗家腋下止汗完整广告_30s_9x16_v12.mp4`
- SHA-256: `94c6b7fc92202f6c7e979bb94b31ecd58aab40e3652113f1e78d66c3535a16a4`
- No-BGM review: `artifacts/qingyan-miao-ad-20260827-v12/final/青颜_苗家腋下止汗完整广告_30s_9x16_v12_no-bgm.mp4`
- No-BGM SHA-256: `deb515e8e94a78f253889bf8fc72df31b2ff025dd3ac2604de865817577e75ff`

## Requirement-Level Verdicts

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| 开头同时建立问题、反应与声音 | `PASS` | frames `0-107` 显示抬臂检查、闻腋下与回避；首秒叠加衣物摩擦 SFX；`silencedetect=-42dB:0.35s` 无区段。 |
| 老人先推荐，少女后喷用 | `PASS` | 推荐位于 frames `108-173`，喷用从 frame `174` 开始；contact sheet 显示老人开口和少女倾听。 |
| 产品推荐只出现一次 | `PASS` | project `video-analysis` Whisper 只返回一段 speech：`姑娘 青岩一汉精尾喷屋 清爽舒適`；同音字误写只作 timing / repetition evidence。 |
| 喷用后才表现效果 | `PASS` | treatment 为 frames `174-317`；result 从 frame `318` 开始，显示放松微笑与收好产品。 |
| `11s` 无异常切镜或运镜 | `PASS` | frame `264` 位于连续 treatment frames `174-317` 内；`around-11s-4fps.jpg` 显示同一轴线和连续动作。 |
| `22s` 无异常切镜或转场 | `PASS` | frame `528` 位于连续 walk frames `409-583` 内；`around-22s-4fps.jpg` 显示同一同行镜头。 |
| 删除奇怪的两张静图收尾 | `PASS` | frames `584-719` 仅有一个 packshot composition；产品图持续缓慢推进；fresh `freezedetect=-50dB:1.0s` 无区段。 |
| 无冻结、无静音、技术规格正确 | `PASS` | H.264 `1080x1920`, `24fps`, `720` frames；AAC `48kHz` stereo；duration `30.022s`；MCP unique-frame ratio `1.0`、issues `[]`。 |
| 主混音安全余量 | `PASS` | `-15.6 LUFS`, `6.1 LU LRA`, `-2.4 dBTP`。 |
| 老人重构对白的自然度与逐字口型 | `NOT_EVALUATED` | 现有素材重构避免了新 Provider 提交；Whisper 和 timing 不能代替真人正常速度试听与口型判断。 |
| 人类整体节奏、转场与广告观感 | `NOT_EVALUATED` | 需要用户完整观看 exact primary master；本 Gate 不签发 P6 或 Final Acceptance。 |

## Review Evidence

- `review/contact-sheet-1fps.jpg`
- `review/opening-2fps.jpg`
- `review/around-11s-4fps.jpg`
- `review/around-22s-4fps.jpg`
- `review/treatment-result-boundary-3fps.jpg`
- `review/hero-2fps.jpg`
- `review/ffprobe.json`
- `review/ebur128.txt`
- `review/silencedetect.txt`
- `review/freezedetect.txt`

## Boundary

Verdict: `PASS_FOR_HUMAN_REVIEW`.

这证明 v12 的精确本地 development preview 满足本轮结构、切点、重复口播和技术要求；不证明重构对白的主观自然度、P6、Final Acceptance、publication-ready 或投放效果。
