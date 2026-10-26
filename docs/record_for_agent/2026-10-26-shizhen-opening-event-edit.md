---
record_kind: media_experiment
topic_id: shizhen-standalone-opening-event-edit
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Lost Frames Standalone Event Edit

Date: 2026-10-26

## Scope
用户最新明确只做开场，与S01无关。宏观到微观、真人摄影质感、保留原Shot和原Suno B、重新建立电影视听语言的目标继续有效。当前交付是关键事件的局部重剪预演和完整开场生产输入，不是已实现宏观真人开场。另窗口拥有`opening-reconstruction-20261026`及唯一审看页面；本窗口只写`opening-narrative-integration-20261026`、对应新run、计划和本记录。

## Actual Output
`outputs/shizhen-episode01/opening-narrative-integration-20261026/focus-002/失帧-两位-关键事件重剪-002.mp4`

SHA256 `f3c03c289bb770b209a355ffad5c59f732168d10d30553f249882c382a19faa9`；19,099,748 bytes；1920×1080；24fps；442帧/18.416667秒；H264/AAC48k stereo。

原素材窗口为A1 start8/count184、A2 start30/count66、A3 start336/count192。四句原生对白保留；每个窗口的画面、原声音轨严格对应，不变速。原Suno B在15.75秒进入，采用原曲0–2.667秒、-10dB和短淡入淡出。片名在回答后进入动态雨玻璃左侧负空间；不再用C的白色人形轮廓、静态大字卡或S01衔接。A3全源历史FAIL没有被改成PASS。

旧001在A2取源48帧，导致7.625→7.667秒站棚大面积单帧跳出，判为失败并保留。002取源30帧，恢复完整遮挡切点及车尾逐渐揭开；后态03:17:11延续至A3全景，并推进03:17:12，原生近景切镜后时钟离画。001、旧C和此前衔接实验均留存，不覆盖、不在当前入口作为主片。

## Verification
以下路径均相对`outputs/shizhen-episode01/opening-narrative-integration-20261026/`：

- `focus-002/render-receipt.json`：HyperFrames 0.7.103 lint/check均无错误；Composition→ResolvedTimeline→HyperFrames唯一渲染路径。未改共享runtime或第二时间线。
- `qa/focus-002-mcp.json`：exact MP4项目本地video-analysis，37张0.5秒间隔帧。逐帧核对了遮挡、空位、钟表、近景与片名。
- `qa/browser-playback-002.json`：实际Chrome 148播放18.624秒，rate1、unmuted、ended、442帧回调、零掉帧、无pageerror。因共享MCP浏览器profile被占用，使用已安装Playwright及独立临时browser，未终止别人的浏览器。此证据不证明人类听过。
- `qa/focus-002-audio-result.json`：一次盲音频理解HTTP200，模型识别全部四句对白，描述女声平静、对话自然，背景雨与水滴；未描述音乐或货车声，不能用它签音乐主题或接点听感。模型时间戳是估计，不覆盖ResolvedTimeline时序。
- `qa/focus-002-protected-inputs.json`：20项原资产/manifest保护hash重新核对一致。三条native audio span gain0、无淡入淡出，来源与画面窗口一致。
- `goal-binding.json`：24项原始用户意图保留，包括最新opening-only；binding验证通过。有重复固定机位的advisory提示，前后同构图为比较空位而保留；技术验证不代表艺术完成。
- 独立只读视觉复核由已有`opening_review`上下文完成，见另一窗口的`outputs/shizhen-episode01/opening-reconstruction-20261026/qa/standalone-review/002/verdict.json`：可作为关键事件预演展示，不签整片艺术PASS。

## Artistic Judgment
C先展示剪影和“缺席”概念，未先建立人物关系；当前重剪把关照、遮挡和“一位”的平常回答还给画面，异常通过前后关系成立。001的剪点缺陷已修复，10.417秒A2→A3仍有轻微头肩手姿态差，不声称完全连续。真人质感、同街宏观摄影和原创电影字体仍未实现；片名清晰且克制不足以满足最终艺术目标。当前没有人类完整声画验收。

三条视觉方向及取舍、三部参考作品的创作者来源和研究限制见`director-review.md`；完整同街城市引入和候车事件的中文Seedance 2.5输入见`production-inputs.md`。未使用参考作品素材进片，未将无声stock预演冒充完整对白成片。

## Cost And Publication
新增视频、图像、音乐生成次数均0。执行1次Gemini音频理解QA，outcome成功，真实费用待结算；封存USD0.05为operator内部上限，不是报价或实际消费。不重试已消费unit。

当前仅本地文件，无Production activation，无公开发布，无用户最终认可；未commit/push。遵循成片优先，等待用户审片后才做完整工程验证及Git checkpoint。未stage或改写他人dirty文件。RAG索引未刷新。

## Learning Evaluation
`distill-ai-video-learning`: `no_candidate`。这是一条源素材上的连续剪辑修复链，技术、模型与独立复核不是多个独立实验；且最终艺术和人工听感未验收，不能提炼成通用风格或模型能力结论。
