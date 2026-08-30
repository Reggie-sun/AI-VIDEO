# V11 Final Development Gate

Date: 2026-08-27

## Exact Outputs

| Output | SHA-256 | Video | Audio |
| --- | --- | --- | --- |
| `final/青颜_苗家腋下止汗转化广告_30s_9x16_v11.mp4` | `e4b857cfb00e1300af90dfaea68d82e80c04a3577da70d356471427f90c6bf8e` | H.264, 1080x1920, 24fps, 720 frames | AAC, 48kHz, stereo |
| `final/青颜_苗家腋下止汗转化广告_30s_9x16_v11_no-bgm.mp4` | `8cc0564613c842cff01dde68f22deee9f0ca5b80c115b2bea39739863ce5e116` | H.264, 1080x1920, 24fps, 720 frames | AAC, 48kHz, stereo |

两版均完成 video/audio full decode，无 decoder error；video-stream MD5 相同为 `c61d926f5b55ec060556f5d977279451`。

## Requirement Findings

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| 0-1.5s 由画面建立汗湿痛点 | PASS | `visible-sweat-hook.png` 与 frames 0-35 显示白色上衣腋下湿痕；钩子字幕只负责问句 |
| 3.5s 前建立产品与核心利益 | PASS | frames 36-83 同屏人物拿起产品、exact packshot、`青颜 / 抑汗｜净味` |
| 明确喷向腋下皮肤区域 | PASS | frames 84-155 与 `demonstration-peak.png` 显示喷嘴朝向露出的非敏感腋下皮肤区域，而非衣物表面 |
| 喷雾近透明、无黄色 haze | PASS | start/spray/end 三关键帧序列；峰值为弥散、透光、无色细雾，无黄色喷出物 |
| 完整真实物理喷洒运动 | NOT_EVALUATED | demonstration 是 deterministic 三关键帧 dissolve，不是实拍或完整 video-provider 物理运动 |
| 使用后自然放松 | PASS | frames 156-215；`清爽舒适`，没有夸张兴奋表演 |
| 社交利益与短对白 | PASS | 9.000-11.667s 靠近；11.667-15.667s 四秒真实原声问答；15.667-19.667s 并肩离开 |
| Hero Shot 与 conversion CTA | PASS | 19.667-25.000s exact packshot + 正式产品名；25.000-30.000s `近距离，更从容 / 点击了解青颜` |
| Product Truth discipline | PASS | 只使用 `抑汗｜净味`、`清爽舒适`；无医疗、量化、绝对或时长承诺 |
| 包装使用说明逐字匹配 | NOT_EVALUATED | 当前 product source 的侧面说明不可可靠辨读；成片未新增距离、次数、等待时长 |
| Main mix loudness | PASS | `-14.6 LUFS` integrated，`5.2 LU` LRA，`-2.1 dBTP` True Peak |
| Smooth dialogue ducking | PASS | 11.25/11.55/15.75/16.05s 同源 300ms crossfade；边界 sample difference 为 `0.00109/0.00441/0.00544/0.00148` |
| Publication/music rights | NOT_EVALUATED | bundled BGM/SFX 可用于本地 development preview；投放前仍须确认完整 license provenance |
| Human full-speed watch/listen | NOT_EVALUATED | 技术检查与 independent review 不替代用户在正常速度下完整观看、试听 |

## Tool Evidence

- `ecommerce-ad-workflow` input validator: `status=valid`, no diagnostics.
- project-local `video-analysis` on the exact primary final: probe confirms 30.022s, 1080x1920, 24fps, 720 frames, AAC stereo; `video_review` returned no machine-detected issues.
- Whisper base detects the two intended speech regions at 11.34-12.70s and 13.26-15.66s；品牌/产品词存在普通话同音字 orthography ambiguity，因此只把它用作 speech timing evidence。
- Independent `reviewer_high` re-review verdict: `accept with concerns`; no blocking issues. Remaining concerns are the deterministic demonstration dissolve and lack of speaker/headphone audition.

## Overall Verdict

`ACCEPT_WITH_CONCERNS` as a local development preview.

This is not `PACKAGE_READY`, P6, Final Acceptance, publication-ready, or proof of conversion performance. The next acceptance layer is the user's full-speed visual and audio verdict; publication additionally requires readable official usage instructions and music/SFX rights confirmation.
