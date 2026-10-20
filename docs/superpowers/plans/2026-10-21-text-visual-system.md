# Text Visual System Implementation Plan

## Goal And Boundaries

以同素材可播放对照证明影视字幕、商业图文及电影标题的表达能力升级。Director / Story / Scene / Shot 继续决定创意；CompositionSpec / ResolvedTimeline 独占时序；HyperFrames 负责最终合成；Registry、ProductionStateCommitter、P6 CAPTION / Review / Repair 的权威不变。研究结果见 `docs/research/2026-10-21-text-visual-engines.md`。

## Design And Compatibility

- 字幕：以可验证嵌入字体、排版意图和已有 CaptionTrack 为输入，复用 pysubs2 与 libass 生成透明字形状态；字形作为 HyperFrames 源码内的 PNG 消费，不建立第二成片合成链。缺依赖、字形、版本或 exact font bytes 时停止，不隐式回退。
- 图文：GraphicTreatment 增加 opt-in TextDesign（自由组合文字 runs、向量路径、空间层次、自定义关键帧与缓动），由纯 compiler 投影到 HTML/SVG/CSS；保留无 design 的旧行为及其序列化。固定的是安全的绘图/运动 primitive，不是美术模板或 genre 枚举。
- 词级时序只在现有 resolver 从 CaptionWord 投影；不由 renderer 猜测。字幕源字、时间、字体与样式、图文意图均进入既有哈希和审计。新源码禁止任意 JS、网络和未声明输入。
- 原有不相关 dirty changes 不编辑、不 stage、不提交。已有 dirty matrix / baseline / 广告 skill 由其他 writer 拥有，本任务说明写独立文档，必要协调后再归并。

## Implementation Units

1. Parent：`text_design.py`、`text_design_html.py`、`text_fonts.py` 及 commercial/resolver/source 的必要接缝；测试覆盖参数边界、投影、旧哈希、源码审计、样式修复失效与逐词边界。
2. Native bounded worker：`subtitle_ass.py`、`tests/test_production_subtitle_ass.py`；只负责成熟 ASS 库和原生字形渲染，无 state / timeline / QA 权威。
3. Parent：已有 Production 加载/resolve/render 公共入口的实渲染验证，使用相同素材、相同字文和时长对比旧新；至少对白、广告层次动效、电影标题三类。封存 exact inputs、输出 hashes、性能实测与截图。独立只读审片，逐项区分 renderer / design / model creativity 缺口。

## Acceptance And Verification

先做出片所需局部测试与真实渲染，检查完整候选及具体运动边界；交给用户审片。当前任务明确要求测试、提交和最终仓库状态，稳定实现按当前 policy 验 exact owned staged snapshot，完成适用独立审查，再 commit / push main / 核验远端 SHA。视频样片是 development capability evidence，不签署真实剧情、广告效果或 P6 Final Acceptance。用户已于 2026-10-21 在观看页打开后反馈“过关”；仅记录本组视觉候选认可，不扩大到全题材或 P6 qualification。

使用 `make harness-inspect`（已执行）、受影响 tests 和最终 fresh receipt；未映射 owned path 沿 policy fail-safe，不改 baseline 藏问题。native renderer / font / source 不可用先报告真实原因并在授权内修复。

## Progress

- 现状：已读取源码、canonical ownership、QA/Repair 与政策；Agent Memory 查询 exit 3（library-incompatible，已按 skill 停止重试），依据当前代码推进。
- 选型：pysubs2 1.8.0 保持 Python 3.11；fontTools 校验字体 identity / glyph；libass 版本封存；HyperFrames 0.7.103 不更换。

- 实现：通用 `text_layers` 与广告 `commercial_graphics` 共用 contract/resolver/compiler；字幕 v2 接入 native glyph 状态；保留原有序列化和状态权威。
- 实片：对白、虚构商业图文、电影标题、逐词高亮共四组真实 public Production 对照已落盘，用户明确认可；修复后八个 exact 输出通过 strict source reconstruction/reopen，MP4 hashes 未变。
- 审查：round 1 三项 blocker 与一项 non-blocker 均 CONFIRMED；修复 literal ASS 控制、拒绝未实现的逐行定位、递归重验 typed copies，并转换损坏字体异常。native round 2 未再复现原触发，finding set 为空；最终 exact staged Harness 按 policy 执行后提交。

- 最终检查接缝：新增模块/测试登记现有 Harness composition 组；CSS source normalization 抽出 `_hyperframes_css.py`，避免扩大既有 God Module。保留每轮失败 receipt，不提高 architecture baseline。

- 验证范围调整：r4 full因共享HEAD变动中断；当前fef0b39 owner允许按行为风险选择并停止耗时不相称的冗余检查。改为冻结快照上的相关生产/字幕/QA/Repair/Canvas验证，保留full未完成，不声称完整Harness PASS。

- 最终：冻结快照上相关520 passed/3 skipped，文档/规则/policy/Architecture检查通过；四组真实渲染、8 exact输出重开、用户视觉认可及3轮native审查闭合。完整仓库套件保留中断状态。
