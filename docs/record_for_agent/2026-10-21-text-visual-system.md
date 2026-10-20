---
record_kind: architecture_implementation
topic_id: production-text-visual-system
learning_eligibility: ineligible
---
# Production Text Visual System

Date: 2026-10-21

## Purpose And Current Truth

把现有参数化文字叠加升级为 Director 可创作的文字层次、排版和独立运动，并复用成熟 ASS 字形能力。共享生产入口已接入；四组同素材对照经真实 Canvas Production 出片，用户在本地浏览器观看页打开后明确反馈“过关”。这是这组候选的视觉认可，不是所有类型作品、全片音频、自动设计模型或 P6 Final Acceptance 的普遍 qualification。

架构、API、部署及已知限制由 [authoring guide](../text-visual-system.md) 独占；候选开源项目的官方资料、维护状态、许可证与取舍见 [research](../research/2026-10-21-text-visual-engines.md)，任务范围见 [plan](../superpowers/plans/2026-10-21-text-visual-system.md)。

## Implementation And Authority

- `pysubs2==1.8.0`、系统 libass 0.17.1 与 exact embedded fonts 处理 schema-v2 字幕字形；透明 PNG 状态仍由 pinned HyperFrames 0.7.103 合成。`fonttools==4.67.0` 检查字体身份与 glyph coverage。原 schema-v1 仍可用，未隐式换引擎。
- `TextDesign` 提供自由意图、层次、文字 runs、vector paths 与 keyframes；通用标题走 `CompositionSpec.text_layers`，广告仍走既有 AdCreativePlan。两者共用 GraphicTreatment / resolver / compiler。新增空字段不进入旧序列化和指纹。
- `ResolvedTimeline` 继续独占 frame/sample timing，原 resolver 将词时间投影到帧；renderer 不猜 ASR 对齐。Registry、Manifest、ProductionStateCommitter、CAPTION / Review / Repair 均未新增平行 owner。
- 样片设计是本次明确创作，并非运行时内置广告或电影模板。Director 的创作判断与 renderer 的执行能力分别验收。

## Exact Media Evidence

观看页：`artifacts/text-visual-system-20261021/index.html`；本次预览地址 `http://127.0.0.1:8877/`。每组 `{case}-comparison.mp4` 左旧右新，`{case}-{before,after}.mp4` 为原尺寸成片。媒体保存在本地 artifact 目录，不夹带其他窗口的素材到代码提交。

`artifacts/text-visual-system-20261021/evidence.json` 记录 source SHA、原 production output path、timeline fingerprint 与 render wall time；下表时间包含既有 source/lint/check/render/verification/activation 流程，不是通用性能基准。

| Case | Before MP4 SHA-256 | After MP4 SHA-256 | Before / After seconds |
| --- | --- | --- | --- |
| dialogue | 6919b1c57e15cdca05f1c6e07522e61dcf3d3c661163a62e3a180897289446e1 | 440661d3c81c5386cdfcbc6f5b7815aa38b627ce6265e8266f233094fc11a439 | 13.87 / 13.92 |
| advert | 1dce2a44efd702fab83349f6691f4c76e62b1d0c2456f561bdefe48d6c78a964 | d78cd2c66eb23e5b17d1b763d1aca892caa6b110800855c20102ea0b8478f465 | 12.05 / 12.50 |
| title | fa2ccef2ee7ffdfa03b3e823d690778b734ffda9e4bf41ad953b17f7890d9161 | 4634b5549aab819c3ee666837260af8d8a7d0eaf611b34474260dcbc8bbf36e6 | 13.08 / 13.54 |
| word | 96c0e78a1ad5ae8b053d61d58417b4de616eb260c8e05093086f8d44aa872bc7 | 85ef2454b55cf0c376769ede24e727a6aae861404aa8a6fd67b145506be6f0b7 | 13.63 / 14.61 |

- 对白 / 逐词：7秒、768×1344、24fps；保留已有原生音频。`audio-preservation.json` 核验新旧解码 PCM 相同，SHA-256 `a1a02780dc79dd29d4d54920c37067003657f05c5122ef48da6695e6527b60d8`，各 336896 samples（包括 AAC 尾部），不是凭时长推断保真。
- 广告：6秒、768×1344、24fps；虚构 LUMA 概念和价格，均显式标示。双方共用同一微推运动背景，未关闭 static check。新版用衬线主标题、退后的品牌/副文、晚出现的价格、独立 mask reveal，未采用卡片底板或机械缩放。
- 电影标题：8秒、1344×768、24fps；使用现有表演素材，标题置于空沙发负空间，保留人物和动作。广告/标题对照均静音，未放大此前用户否定的原生声音。
- 每个新版 exact MP4 显式调用 project-local `video-analysis`，其有限帧分析记录在 `{case}-video-analysis.json`；Parent 查看采样帧。采样中未见乱码/人物遮挡/截断，不把采样或工具结果当完整正常速度听看的替代。逐词时间为人工编排，未声称声学逐词对齐通过。

Production 验证目录 `/tmp/ai-video-text-visual-20261021/final-r1/{case}/{before,after}/` 保留标准 public service 导入、author/approve、caption import、compose、真实 render、deliver 和 strict durable reopen 的 receipts / state。它们是 development capability evidence；没有新付费 submit、模型生成或 P6 acceptance。

## Verification

- 相关 composition、HyperFrames、caption quality、Review/Repair、Canvas authoring/assets 与新文字回归：444 passed、3 skipped（90.72秒）。
- 新文字契约与 native 字形局部测试：25 passed（包含审查后新增回归）。实际 host 需显式 `LD_PRELOAD=/lib/x86_64-linux-gnu/libfreetype.so.6` 解决 Conda FreeType / 系统 HarfBuzz 冲突；产品不硬编码自动 fallback。
- CSS parser extraction 后相关 source / 字形回归：227 passed、3 skipped（46.73秒），再次 strict reopen 八个 exact 产物成功。
- opt-in `tests/test_production_text_visual_render.py`：4 passed，115.57秒，是真实本地 public Production 链，不使用 fake runner。
- 观看页经 Chrome MCP 打开，四组 `<video>` 的 readyState=4、duration/dimensions 正确且无 media error。用户反馈“过关”。
- 独立只读 `reviewer_xhigh` round 1 绑定 source snapshot `ee51dc5845ebeb06a2e6e496d5cb1ff65351ca83b58e9b63c3e9024626e864e8`。四项 finding 均经 Parent 复现并裁决 CONFIRMED：TVR-001 修复字面量 ASS 控制；TVR-002 拒绝不支持的逐行定位（保留既有 null 序列化兼容）；TVR-003 public resolver/compiler 递归重验 typed copies；TVR-004 把损坏字体 parser 异常转换为受控校验错误。新增测试先复现失败再通过；round 2 候选 `213018f031070ce834d54686028afe752b23e386a3999f665521cd734d25c28a` 原触发均未再复现、finding set 为空；完整 target 和 closure 保存在 `artifacts/text-visual-system-20261021/independent-review.json`。复核后仅删除无用 local variable、补 optional 依赖的测试 availability guard 和补完文档，未改变 Production rendering semantics。后续 Architecture Gate 要求的 CSS parser extraction 与新增 policy 路由经同一 reviewer 第三轮定向复核：候选 `39739159c81d7f84b173bf5435dd8629489e93c1724ac8d0f3694aaa5b3b2e44` 的26文件在审查前后指纹一致，finding set 为空，四项原问题没有新增残留。

## Failed Checks And Attribution

早期静态广告背景被现有 static sweep 拒绝；更换为两臂共享的可见微推背景，保留检查。价格单位颜色早期对比度约4.09–4.35，调整颜色后再出片；这是设计决策缺陷。严格 JSON 数组重开与 data font URL 的既有声明 parser 不兼容已在 JSON 边界/审计处修复并测试；这是实现缺陷。上述均不能归咎于模型创意能力，也不能据本次样片推断模型在任意 brief 下会自动设计。

## Limits And Learning Evaluation

当前缺少自动主体跟踪，避让依据明确提供的保守几何；没有测长片内联字形/source 内存和多小时滚动字幕，也未验证所有中文禁则、复杂多语脚本或漫剧特效。部署须固定原生依赖构建，同 API version 不保证跨平台像素一致；字体 commercial rights 由 exact license 与实际资产来源承担。

本次有多臂对照，但不是隔离单一审美变量的模型能力实验。`distill-ai-video-learning` 结果为 `no_candidate`：没有足够可归因的跨实验结论需要升级 Skill/Policy/Gate；不制造 placeholder 或 adoption。Agent Memory 原查询返回 exit 3 / library-incompatible，按 owner 禁止同任务重试，当前判断基于 reopened 源码/媒体；未宣称 RAG 已刷新。本记录不改变历史失败素材 verdict。

修复后八个 exact 生产输出经过 strict source reconstruction/reopen，MP4 SHA 均未改变，记录在 `artifacts/text-visual-system-20261021/after-fixes-reopen.json`。

用户视觉认可与 native 独立审查已完成。最终 exact staged policy 结果沿 Harness receipt 独立存证，不以本记录预签 PASS；首轮 r1 在 scope_diff_check 发现新文件 EOF 多余空行后停止，未运行后续套件；r2 在 policy_audit_check 发现新增源码/测试未登记后停止，尚未运行 full tests。已将这些路径与测试加入现有 production_composition_audio 组，不删除旧检查、不降 Gate；这使后续新文字改动自动受现有工程验收覆盖。r3 的 task Architecture Gate 拒绝 `hyperframes.py` 的 +6 effective LOC 历史债增长，full tests 仍未运行。把本次涉及的 CSS normalization 移入 `_hyperframes_css.py`，外层保持 typed error 适配，未提高 baseline 或添加例外；r4 已通过 scope/docs/rules/policy/runtime-boundary/Architecture Gate，进入 full_tests 后因共享 HEAD 前进而由 Parent 中断；该轮 receipt `.agent/harness/runs/text-visual-system-20261021-final-r4/receipt.json` 为 failed，不能复用为完成证明。全量收集7301项，中断时约10%；其大量耗时在任务外 Agent Memory 多语语料校准（stderr 有实际 stack），没有全量 PASS。，publication 以对应 Git commit / remote SHA 为准。媒体文件按现有 `.gitignore` 保留本地，观看页与轻量证据随代码提交。其他窗口的 dirty/staged work 必须保持。


## Final Verification Scope

在用户质疑全量范围后，重新读取当前 owner：`fef0b39` 将验证规则改为按行为影响与风险选取，允许在耗时不相称时停止冗余检查并保留中断/未验证项。未修改 Harness routing/coverage/fallback 或伪造完整 receipt。Parent 不再重跑7301项全仓库测试；以 existing Harness 的 verification-only isolated checkout 冻结 staged bytes，对文字模型/字体/ASS、composition、HyperFrames source audit、caption、广告、QA/Review/Repair 以及 Canvas authoring/assets/render/production/recovery 做有界相关验证，并运行既有文档、规则、policy、Architecture 检查。结果沿 `artifacts/text-visual-system-20261021/scoped-verification.json` 与同目录日志记录；这些是 development test evidence，不是第二套 Product QA 或完整 Harness PASS。发布前核对所有 task-owned bytes 与已验证 snapshot，不夹带其他窗口变更。

最终 scoped 验证结果：520 passed、3 skipped（223.64秒）；scope diff、docs contract、agent rules、policy audit、task Architecture 全部通过。Architecture 只有一个非阻断 INFO：HyperFrames first-party fan-out=14；导入仍服务同一合成/source audit 职责，第三轮已复核抽取边界。发布前已对比 frozen snapshot 的所有35文件 hash，无 byte drift；后续只补最终文档/测试证据。完整 Harness 仍为 INTERRUPTED_NOT_PASSED，不把局部结果冒充完整 PASS。
