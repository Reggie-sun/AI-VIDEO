# V11 Authoring Contract

## Goal

把 v10 从品牌短片重构为 30 秒竖屏 conversion-oriented development preview。优先解决前 3 秒钩子、产品第一次出现、使用可信度、社交利益、Hero Shot、CTA 与声音动态；不把媒体候选升级为投流、P6 或 Final Acceptance 事实。

## Product Truth

- Formal product: `青颜 氯化羟铝抑汗净味喷雾`，`60ml`。
- Allowed copy: `抑汗｜净味`、`清爽舒适`。
- Lifestyle copy: `近距离，更从容`、`点击了解青颜`；它们不表述额外产品功效。
- Forbidden: `24H`、根除、永久、绝对、临床/医学保证、未获证据支持的比例或效果时长。
- 包装侧面使用说明在当前源图中不可可靠辨读。因此画面只呈现用户明确要求的腋下皮肤区域示范，不写使用距离、次数、等待时间或其他操作参数。

## Timeline

| Beat | Frames | Time | Purpose |
| --- | ---: | --- | --- |
| Hook | 36 | 0.000-1.500 | 单一、极短痛点；衣料声在 0.2 秒内进入 |
| Product intro | 48 | 1.500-3.500 | 人物拿起产品；exact packshot 同屏；`青颜 / 抑汗｜净味` |
| Demonstration | 72 | 3.500-6.500 | 近景对准腋下皮肤区域；透明细雾；一次喷雾声 |
| Result | 60 | 6.500-9.000 | 动作和表情松弛；`清爽舒适` |
| Social proof | 64 | 9.000-11.667 | 阿婆自然靠近，人物不再回避 |
| Short dialogue | 96 | 11.667-15.667 | 保留原生真实问答并压缩到 4 秒 |
| Walk together | 96 | 15.667-19.667 | 并肩离开；`近距离社交，更从容` |
| Product hero | 128 | 19.667-25.000 | exact packshot + 正式产品名 + `抑汗｜净味` |
| CTA | 120 | 25.000-30.000 | exact packshot + `近距离，更从容` + `点击了解青颜` |

Total: exactly `720` frames at `24fps`.

## Retired Paths

- v10 `01_problem_open_cap_spray.mp4` 的喷衣服动作不进入 v11 demonstration；只允许使用其喷前拿起/开盖片段，并以品牌图形覆盖原黄色 haze。
- v8 `04-golden-fluid.png` 与 v10 黄色液体/烟雾利益卡不进入 v11。
- v10 25-30 秒的高电平结尾语音与炸响 chime 不进入 v11。
- v10 final、source media 与历史 review evidence 保持只读，不覆盖。

## Dialogue Truth

现有 accepted native dialogue 只有：`姑娘，喷的什么？`、`青颜抑汗净味喷雾，清爽舒适。`、`难怪这么自在。`。本版截取前 4 秒并显示与原声一致的两句字幕：`姑娘，喷的什么？`、`青颜抑汗净味喷雾`。不伪造用户建议但素材中不存在的口型或台词。

## Visual Source Boundary

- Hook source: built-in `imagegen` still edit，保留同一人物、服装、姿态与室内，只增加白色上衣腋下清晰但克制的真实湿痕，让痛点由画面直接建立。
- Product demonstration source: built-in `imagegen` 三关键帧序列，保留同一人物、服装与室内，依次呈现未喷、按压时的弥散近透明细雾、喷后雾气消散；通过 deterministic crossfade 形成可核验的 72-frame demonstration。
- 该关键帧序列是 authoring evidence，不是实拍、完整物理运动、包装用法核验或 Production Provider qualification。
- Product hero/CTA only use `assets/product-packshot.jpg` exact bytes。
- 苗家元素只承担人物与美术风格，不暗示民族秘方或产品来源。

## Audio Contract

- 0.2 秒内进入轻衣料声；产品开盖、喷雾、状态转亮与 CTA 各有低强度 SFX。
- 对白段 BGM ducking，对白始终在音乐上方。
- 输出 `BGM + SFX` 和 `no-BGM + SFX` 两版。
- Primary BGM master target: integrated loudness near `-14 LUFS`、`LRA <= 10 LU`、True Peak `<= -1.0 dBTP`；最终以实测为准。no-BGM 版是保留对白与 SFX 的 edit/review stem，允许因有意留白而具有更高 LRA。
- `bgm-tech-house.mp3` 与 bundled SFX 来自本机 `video-shotcraft` asset library。用于本 development preview；发布前仍须确认音乐/音效授权 provenance。

## Gate

成片必须验证：exact SHA-256、1080x1920、24fps、720 video frames、完整音视频 decode、响度、LRA、True Peak、silence/freeze、边界 contact sheet、project-local video analysis 与独立 reviewer。任何技术 PASS 都不替代用户完整观看/试听 verdict。
