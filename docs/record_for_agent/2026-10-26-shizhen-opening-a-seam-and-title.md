---
record_kind: session_summary
topic_id: shizhen-independent-opening-a-revision
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Standalone Opening A: Seam And Title Preview

## Scope And Result

仅独立开场，不含 S01。保留 focus-002 核心消失事件、四句对白和既有 Suno 音乐；用户最新指令将片名字体重新交回本任务。没有新增付费图片、视频或音乐生成。旧 A/B、focus-002 和原始素材未覆盖。

实际输出位于 `outputs/shizhen-episode01/opening-A-revision-20261026/`：

- `variant-R2/失帧-独立开场-接缝修订-R2.mp4`：17.375 秒、417 帧。
- `variant-R3/失帧-独立开场-空位片名-R3.mp4`：20.375 秒、489 帧、1920×1080、24fps；SHA-256 `587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc`。
- `index.html`：R3 主播放、事件版与旧 A 接点对比、三种片名设计比较。

这是局部修订预演，不是完整 A 版或最终成片通过。此前干街库存镜头不能证明与雨夜站台的空间联系，已从新预演退出；真正同街区宏观素材尚缺。

## Editorial And Art Decisions

核心素材 A1 源帧 8..191、A2 源帧 30..95 保留；A3 从源帧 336 改为 361，保留至 527。删除造成同构图人物姿态跳变的 25 帧，接入原片真实近景。原声同步裁剪，没有重配对白；旧 A3 钟牌叠层不再错误悬浮于近景。

R3 尾部复用 A3 源帧 288..359 的 3 秒同站台全景，作为对消失位置的编辑性回看。钟牌后期补为 03:17:18 至 03:17:21，与前文连续，不表达倒流或第二次异常。原音乐继续播放未循环的源区间，尾部淡出；保留源素材 AI 标识。

片名比较“留位”“题刻”“独立断切”三个方向，当前采用“留位”：非对称完整宋体字形保留雨夜动态图像，左侧空间逐渐退暗，右侧幸存者仍在画面中。字体使用系统 Noto Serif CJK SC Bold。该变化是编辑性视觉表达，不声称发生新的世界内灵异机制。暗面仍有平面设计感，艺术完成度须用户正常速度审片判断。

## Verification And Review

`qa/integrity.json` 核验 26 个保护路径，旧 A/B/focus 文件 hashes 不变；A1/A2 原生音轨规格相等。解码缩图比较显示新片前 250 帧与 focus 同区间平均 8bit 差值约 0.451，后续 167 帧对照 focus 275..441 约 0.696；这是重编码近似比较，不是像素或文件字节同一证明。

`qa/playback-R3.json` 记录独立 Chromium 正常速度完整播放，489 帧、0 掉帧、结束成功；真实页面切换控件已检查。共享 MCP 浏览器 profile 已占用，未关闭他人浏览器，改用独立 Chromium。技术播放成功不证明人类听感或艺术接受。

project-local video-analysis 已显式分析 exact R2/R3；结果分别为 `qa/video-analysis.json`、`qa/video-analysis-R3.json`。自动场景识别未准确识别全部实际切点，不采纳其结果作为连续性通过依据。人工模型逐帧观察 actual MP4 抽帧和播放截图，独立 native reviewer 复核 R3 SHA、接点、钟牌与文字构图，无新增 blocking finding；结论限局部画面与时间逻辑。

`qa/transcription.json` 本地 Whisper 检出四句对白；同音字和“嗯”的识别遗漏不被用于改写原声。`qa/review-R3/packet.json` 为绑定 full goal 的正式审片准备，整体仍为 NOT_EVALUATED，缺失宏观和真人目标不能用局部 PASS 覆盖。

## Unknown Audio Analysis

一次现有分析工具的远程音频分析返回 `transport_unknown` / `UNKNOWN`，retryable=false，停止且未重试。证据：`qa/final-R3-audio-result.json`、`qa/final-R3-audio/` 和 `qa/final-R3-audio-binding.json`。单次封存 reservation 上限为 USD 0.05，不是实际费用；实际结算待确认。视频/音乐生成调用为零，不能将其误报为所有远程操作费用均为零。完整听感仍未确认。

## Production Gaps And Handoff

`production-inputs/README.md`、`CO-WORLD.director.zh.txt`、`preparation.json` 与 `reference-manifest.json` 给出同一道路交通动线收束至站台的中文导演输入与真实源帧职责。`execute_ready=false`：没有新宏观视频，没有完整获认可的真人角色素材，没有新付费生成授权，也未封存可提交的模型模式与生产绑定。原素材仍有 CG 质感和 AI 标识，正式使用限制尚未完成核验。

读取已安装 `extreme-motion-design`、`bang-motion`、`chinese-font-selector`、`davinci-resolve-fusion`，仅复用适用设计与排版方法；没有安装 Resolve、替换 HyperFrames 或改写共享执行 owner。Fusion 未来可作为镜头级可选合成环境，不管理第二套整片时间线。

## Publication And Learning

当前为本地用户审片版本；依据项目 media-first 规则，尚未获得用户效果认可，不提前跑完整工程验证、commit 或 push。共享 dirty work 未 stage、覆盖或清理。此记录及任务输出为新增 owned paths。

自动学习评估：`no_candidate`。本次为同一素材链的有界修订，尚无独立跨实验质量证据，不升级全局规则、Skill 或 Gate。
