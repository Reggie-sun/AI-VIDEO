---
record_kind: media_experiment
topic_id: shizhen-opening-title-study
learning_eligibility: ineligible
---

# Shizhen Opening Title Study

Date: 2026-10-26

## Purpose

核对现有 Motion / Kinetic 技能与四个开源技能是否具备影视片名能力，并在 focus-002 的正式片名段落上渲染、观看两部完整独立开场。评价标准是成片观看，不是设计稿或渲染退出码。

同日较早的 [方向与 3.5 秒字体测试](2026-10-26-shizhen-live-action-direction-and-type-study.md) 只验证局部字形，不宣称空间合成或开场完成。该限制仍然有效。本文是其后的整段开场比较，不改写那次测试的测量。

## Current Runtime Truth

比较基线是 focus-002：`outputs/shizhen-episode01/opening-narrative-integration-20261026/focus-002/失帧-两位-关键事件重剪-002.mp4`，SHA-256 `f3c03c289bb770b209a355ffad5c59f732168d10d30553f249882c382a19faa9`，19,099,748 bytes，18.416667s，442 帧，1920×1080，24fps，H.264/AAC 48kHz stereo。原片未覆盖。

两部候选沿同一 ResolvedTimeline 与 HyperFrames 0.7.103 渲染。消失事件、四句原对白、Suno B 音乐、A1 时钟与画面内「AI生成」标记保持。片名只出现在 CO-A3 尾段：本地帧 126 仍为透明，156 全显，保持到 191。没有 S01，没有正片衔接，没有新的付费生成。

| 候选 | 路径 | SHA-256 | bytes |
| --- | --- | --- | --- |
| 曝光 | `outputs/shizhen-episode01/opening-title-study-20261026/exposure/失帧-开场-曝光.mp4` | `86093fd9eea8421bb100885b47e8e8f96fc6f2e5cc472956ca34575de2f9a6a5` | 18,236,358 |
| 玻璃 | `outputs/shizhen-episode01/opening-title-study-20261026/inscription/失帧-开场-玻璃.mp4` | `db2ded12a4c7910729c82af46b4eab3197e533cd6f56c51a41371303b4165252` | 19,110,346 |

三部成片的音轨解码 MD5 同为 `3e8125f4fe3745cea49e5a175beef909`。Receipt 均写 `human_review: PENDING`、`publication: NOT_PUBLISHED`、`paid_generation_calls: 0`、`s01: OUT_OF_SCOPE_NOT_INCLUDED`。

## Session Work And Decisions

已安装的 `motion-art-direction`、`animation-principles`、`kinetic-typography` 面向普通动态图形与西文 kinetic type，不设计中文电影字形，本次不重复安装。

用户随后明确授权安装。四个技能现已写入 Codex 全局目录 `~/.codex/skills/`，没有放进 `~/.agents/skills/`、`~/.grok/skills/` 或本仓库 `.agents/skills/`。Codex 下一轮可以按 `SKILL.md` 调用；本会话的自动技能列表不包含它们。四份都未拿来改渲染器或重做样片：

- `extreme-motion-design` 是 Remotion reel/QA。它会成为第二渲染器，也不画中文片名。
- `bang-motion` 是 GSAP/Three 促销动画，其 title 配方是 lower third。
- `chinese-font-selector` 只在字库中选字体。本机已有 Noto Serif CJK SC 与 AR PL UMing。
- `davinci-resolve-fusion` 描述的是真实 Fusion 合成。免费版 DaVinci Resolve 21.1.1 现已装在 `/opt/resolve`，`/opt/resolve/libs/Fusion/fuscript` 存在。技能里的 `run-script.sh` 仍指向 macOS 路径；外部 `fuscript` 按该技能说明只对 Studio 有效。这次没有用它重做样片。

最小补足是本目录的 `glyphs.py`：用 PIL 与 numpy 从现成字形取轮廓，切一条竖向缺笔，再交给既有 HyperFrames 全画幅 SVG path。曝光版用非零填充让雨和路灯只从笔画里透出；玻璃版把同一类轮廓以墨色叠在画面上。没有新 Skill、没有 blend mode、没有第二 timeline、没有 Blender。

玻璃版曾用 AR PL UKai，定格上「帧」的「车」被看成「中」。该文件已替换。交付的玻璃版改用 UMing、等比置入，缺笔留在右半，避开「车」。

## Verification And Evidence

本记录作者观看了三部成片的接触表和定格，时间点为 15.50s（片名应尚未出现）、17.20s、18.20s，文件在 `outputs/shizhen-episode01/opening-title-study-20261026/qa/`。15.50s 的曝光定格没有片名。17.20s 与 18.20s 两部候选的片名都仍在，并保持到尾帧。

曝光：近黑遮罩上，「失」「帧」竖排于左侧雨玻璃。笔画是窗口，钠灯和雨在笔画内继续；字腔保持暗。人物仍可辨认，但整幅变暗。宋体骨架在这个尺寸上像放大的现成字，不像专门绘制的电影字。竖向缺笔被暗场淹没，不容易读成消失事件本身。运动是一次淡入后保持。

玻璃：画面亮度与表演保留。UMing「失帧」可辨认，右侧缺笔可见。字仍叠在照片上，0.7px 模糊没有变成湿玻璃、折射或裹光。

focus-002 定格是脸侧一对小号奶油色宋体，属于克制的标题卡。

这是 Agent 观看，不是用户验收。不得写成艺术 PASS、P6 或 Final Acceptance。

## Assessment

缺口分成四层：

- 字体艺术仍是主缺口。两版都借用宋体或明体结构再切一刀，没有原创「失」「帧」。
- 画面合成只在曝光版部分闭合：现有 path 节点的非零缠绕能让照片成为油墨。没有折射、位移或光边，实色墨不能变成湿玻璃。
- 工具控制不是这两部成片的阻塞。HyperFrames 已在原时间线上交出两部带原声的成片。免费版 Resolve 21.1.1 事后已安装，Fusion 在应用内；它没有参与这两部成片，也不替换 HyperFrames。Remotion 与 GSAP 会换掉渲染器，仍然不提供中文片名设计。
- 导演判断上，曝光的回应成立：第四句之后，留下的雨和灯写成片名，她没有看见。尾部大约 2.7 秒只够一次显现和停留。玻璃版保住表演，失去与画面的融合。

曝光改变了观看类别。玻璃版是更大的标题卡。两者都还不是完成的电影级字形。

## Remaining Risks Or Publication

用户审看前不接受任何一版。相关成片、研究脚本与本记录保持 local/uncommitted，未 push，未发布。Manifest 未改，没有 Production activation。

若继续，下一步只补字形绘制本身。上述四个技能已在 Codex 侧。免费版 Resolve 只作为本机合成工具，不接成第二时间线，也不要另起片名框架。

## Learning Evaluation

`no_candidate`。这是同一次开场上的两臂比较，用户尚未审看；不能把一次借用字体的窗口实验写成 Skill、Policy 或 Gate。`docs/record_for_agent/learning/` 中没有可更新的片名 claim。
