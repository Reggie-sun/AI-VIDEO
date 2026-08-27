# Qingyan V11 Conversion Structure And Sound Redesign Record

Date: 2026-08-27

## Purpose

本文记录用户完整观看 v10 后给出的 conversion-oriented human review，以及据此完成的 v11 本地
development preview。v11 不是对 v10 画质的继续微调，而是重做前 3 秒、产品 demonstration、社交利益、
Hero Shot、CTA 和 sound design。

本记录不把 v11 描述成 `PACKAGE_READY`、Production candidate、P6、Final Acceptance、publication-ready
或转化效果证据。媒体、composition script 与 review artifact 仍为 local-only、untracked；本轮只提交本记录
及直接需要的 v10 supersession notice。

## Human V10 Correction

用户对 exact v10 的核心判断是：AI 画面已基本过关，真正阻塞转化的是广告结构、产品可信度和声音设计。
当前文件复核支持该判断：

- v10 前 `5.875s` 重复腋下不适，产品随后才出现；
- `01_problem_open_cap_spray.mp4` 朝完整白色上衣覆盖的腋下喷，并带大片黄色 haze；
- 15.333-21.542s 使用三轮长对白；
- final five seconds 仍含 golden-fluid benefit card；
- v10 音频为 `-13.9 LUFS`、`24.6 LU LRA`、`-0.5 dBFS` True Peak，前半段与结尾存在显著电平落差。

这些事实不抹去 v10 的 local generation 和 technical Gate；它们说明技术可解码、Shot continuity 或总响度
本身不能替代电商结构、使用可信度、主观观看和转化验收。

## V11 Product Truth And Boundaries

v11 formal product 仍为 `青颜 氯化羟铝抑汗净味喷雾`、`60ml`。只使用以下核心 copy：

- `抑汗｜净味`
- `清爽舒适`
- lifestyle/CTA：`近距离，更从容`、`点击了解青颜`

没有使用 `24H`、根除、永久、绝对、医疗/临床保证或未经支持的量化效果。苗家服装、银饰和人物关系只
承担人物与视觉风格，不暗示民族秘方或虚构产品来源。

当前 `assets/product-packshot.jpg` 能可靠证明正面产品名、黄色盒/标签、白盖和 `60ml`，但侧面使用说明
不可可靠辨读。因此 v11 不写使用距离、次数、等待时间或其他包装操作参数；这也是不生成
`ecommerce-ad-workflow/package/2`、不声明 `PACKAGE_READY` 的明确理由。

项目 Agent Experience Memory preflight 对
`青颜 电商广告 v10 产品使用 透明喷雾 音频混音` 返回有效空结果 `[]`；没有把 missing retrieval 当成 runtime
truth，也没有刷新或重建 RAG index。

## Session Work And Decisions

新 authoring surface：

```text
artifacts/qingyan-miao-ad-20260827-v11/
```

timeline 精确为 `720` frames at `24fps`：

| Beat | Frames | Time |
| --- | ---: | --- |
| visible sweat hook | 36 | 0.000-1.500 |
| product intro | 48 | 1.500-3.500 |
| skin-area demonstration | 72 | 3.500-6.500 |
| restrained relief | 60 | 6.500-9.000 |
| social approach | 64 | 9.000-11.667 |
| native short dialogue | 96 | 11.667-15.667 |
| walk together | 96 | 15.667-19.667 |
| exact product hero | 128 | 19.667-25.000 |
| conversion CTA | 120 | 25.000-30.000 |

旧 v10 `01_problem_open_cap_spray.mp4` 只消费喷前拿起/开盖区间，其下部黄色 haze 被明确的黄色品牌面板覆盖；
旧喷衣服动作、v8 `04-golden-fluid.png` 和 v10 末尾高电平 voice/chime 均已退休，不进入 v11 final。

本轮使用 built-in `imagegen` 完成五次 scoped edit：一张初版 demonstration 被 independent review 否决后已
从 v11 artifact 目录移除；保留的四个输出是一张 visible-sweat hook，以及 demonstration 的
start / diffuse-colorless-spray / clean-end 三关键帧。最终 3 秒 demonstration 用 deterministic crossfade
表达未喷、一次弥散近透明细雾、雾气消散。它比单张白色直线束可信，但仍不是实拍或完整物理运动证据。

现有 accepted native dialogue 不含用户建议的新句“姑娘，今天这么自在？/ 用了青颜。”。为避免字幕与
口型不一致，v11 使用原声的真实前两句并压缩为四秒：`姑娘，喷的什么？`、`青颜抑汗净味喷雾`。

声音由连续低动态 BGM、0.05s 衣料钩子、开盖、一次 soft spray、状态转亮 SFX、四秒 native dialogue
和低强度 CTA sting 构成。BGM 在对白区间通过同源三段 300ms crossfade 平滑 duck，dialogue 另有 50ms
入场和 250ms 尾淡；另输出同画面的 no-BGM + SFX review stem。

## Exact Outputs And Verification

Primary master：

```text
artifacts/qingyan-miao-ad-20260827-v11/final/青颜_苗家腋下止汗转化广告_30s_9x16_v11.mp4
SHA-256 e4b857cfb00e1300af90dfaea68d82e80c04a3577da70d356471427f90c6bf8e
23,417,073 bytes; H.264 High; 1080x1920; 24fps; 720 frames;
AAC 48kHz stereo; container duration 30.022s
```

No-BGM review stem：

```text
artifacts/qingyan-miao-ad-20260827-v11/final/青颜_苗家腋下止汗转化广告_30s_9x16_v11_no-bgm.mp4
SHA-256 8cc0564613c842cff01dde68f22deee9f0ca5b80c115b2bea39739863ce5e116
22,705,018 bytes; same 720-frame video stream; AAC 48kHz stereo; 30.022s
```

两版 video-stream MD5 均为 `c61d926f5b55ec060556f5d977279451`，完整 audio/video decode 无 error。
Primary master 实测：

- integrated loudness: `-14.6 LUFS`
- loudness range: `5.2 LU`
- True Peak: `-2.1 dBTP`
- `silencedetect=-35dB:0.20s`: no detected main-master silence interval

11.25 / 11.55 / 15.75 / 16.05s 四个实际 ducking/fade 边界的 mono single-sample difference 分别为
`0.00109 / 0.00441 / 0.00544 / 0.00148`。独立 reviewer 对 100ms RMS 复核也确认 15.7-16.0s 为渐进
恢复，不是 gain step。

`ecommerce-ad-workflow` input validator 返回 `status=valid` 且无 diagnostics。project-local
`video-analysis` 对 exact primary final 重新运行：probe 绑定 30.022s、1080x1920、24fps、720 frames 和
AAC stereo；`video_review` 返回 `issues=[]`。Whisper base 在 11.34-12.70s、13.26-15.66s 检出两段
speech；品牌/产品同音字误写只作为 timing evidence，不作为 copy truth。

local final evidence：

```text
artifacts/qingyan-miao-ad-20260827-v11/review/final-gate.md
artifacts/qingyan-miao-ad-20260827-v11/review/contact-sheet-1fps.jpg
artifacts/qingyan-miao-ad-20260827-v11/review/contact-sheet-boundaries.jpg
artifacts/qingyan-miao-ad-20260827-v11/review/demonstration-sequence.jpg
artifacts/qingyan-miao-ad-20260827-v11/review/demonstration-peak.png
```

首次 `reviewer_high` verdict 为 `reject`，阻塞点是单张 demonstration 的白色直线束和阶跃 BGM ducking。
修复后按同 tier scoped re-review，verdict 为 `accept with concerns`、`Blocking issues: none`。这证明两个
具体 blocker 已闭合，不是 human Final Acceptance。

## Assessment

v11 已经把 v10 的“30 秒品牌小短片”结构压成更明确的 problem -> product -> demonstration -> social
benefit -> proof -> Hero -> CTA 路径。产品第一次出现由约 6 秒提前到 1.5 秒；痛点由湿痕画面直接建立；
黄色被限制在 packaging、关键词和品牌板式；产品正式名称与两个核心利益点在首次出现和 Hero Shot 中重复。

Primary 音频把 v10 的 `24.6 LU` LRA 收紧到 `5.2 LU`，并保留足够 True Peak 余量。技术证据支持其作为
local development preview 交给用户完整观看/试听，但不证明投放表现。

## Remaining Risks And Next Work

1. 用户必须以正常速度、实际扬声器或耳机完整观看/试听 primary final，重点判断 3.5-6.5s dissolve 是否自然、
   11.25-16.05s 对白 ducking 是否舒适；该 verdict 仍 pending。
2. demonstration 是三关键帧 authoring sequence，不是完整物理喷雾运动；若用户仍认为不可信，下一最小动作
   是只替换这 3 秒为新的真实短运动 Shot，保持其余 648 frames 不变。
3. 包装侧面使用说明需要更清晰的官方图或正式说明，才能逐字核对操作与关闭 package readiness。
4. `bgm-tech-house.mp3` 与 bundled SFX 的 publication license provenance 在正式投流前必须确认；本记录
   只支持 local development use。
5. 本轮没有 AI-VIDEO Provider、ComfyUI、paid submit、Production Manifest mutation、P6、release、push 或
   publication action。built-in `imagegen` effects 不得误记为 AI-VIDEO Provider qualification。
6. project RAG index 未刷新；Agent Experience Memory 的空结果仍是本轮 advisory retrieval truth。

## Agent Guardrails

- 不得把 `video_review issues=[]`、decode、响度、contact sheet 或 reviewer verdict 当成人类观看/试听结论。
- 不得把 exact packshot 出现等同于包装使用说明已核验。
- 不得再次把黄色雾、黄色液体、粉末或烟气作为产品喷出物。
- 不得将三关键帧 dissolve 描述为实拍、完整物理运动或包装用法证明。
- v10 生成与 technical Gate 继续作为历史 evidence；其 current-facing human verdict 已被 v11 修订取代。
- v11 artifacts 保持 local-only、untracked；记录 commit 不会发布媒体，也不产生 Production activation。
