---
record_kind: architecture_implementation
topic_id: visual-font-genre-separation
learning_eligibility: ineligible
---

# Font Research And Genre Gates

## Scope

用户否定九号广告字体并要求上网找字体，随后明确“电视剧和广告的字体gate得分开”。
本轮下载候选字体并制作真实字形对比，同时分离两类视觉 authoring 与报告入口。
没有重渲染成片、安装系统字体、新增字体 runtime dependency 或改变 Production 字体 owner。

## Font Evidence

原商业图形使用通用 `sans-serif`，本机 `fc-match sans-serif:lang=zh-cn:weight=medium`
得到 Noto Sans CJK SC Regular。只调整字重不构成精确选定字体。

候选一为 [MiSans](https://hyperos.mi.com/font/zh/download/)，从官方
`https://hyperos.mi.com/font-download/MiSans.zip` 下载；候选二为
[得意黑](https://github.com/atelier-anchor/smiley-sans) v2.0.1，从作者 release 下载。
两者原始许可分别保存在 `runs/ninebot-font-study-20260914/MiSans-LICENSE.pdf`
与 `SmileySans-LICENSE.txt`，字体文件 SHA256 见同目录 `font-provenance.json`。
用户随后明确选择“得意黑标题 + MiSans 小字”，已写入九号广告专属方向；
短标题用得意黑，说明、CTA与门店名用MiSans，尚未替换既有MP4或renderer字体。
得意黑作者列举视频标题用途，同时不推荐正文；不把该方案作为电视剧对白默认字体。

真实字体通过本地 `@font-face` 加载，独立 headless Chrome 实际输出
`comparison.html` 与 `comparison-full.png`；`document.fonts.check` 为 true，
`fc-query` 确认广告文案字符无缺字，详见 `font-verification.json`。
该样张证明字体选型预览，不证明 canonical HyperFrames 已接入这些字体。

## Implementation

代码提交 `546f134`：`VisualDirection.content_kind` 可明确为 advertising/drama；
factory 将类型放入 requirement ID，原 contract hash 与 SEMANTIC exact identity
校验因此拒绝跨类型证据，即使文案完全相同。两个 config 保存独立审美方向。
广告关注标题、品牌、CTA与条件说明；电视剧关注对白连续阅读、表演避让与题材画风，
片名展示字与对白分开。字节、抽帧与观看证据仍共用；原 CAPTION Gate 保持不变。

新私有 prepare CLI 必须提供匹配的 `--content-kind`，缺失/冲突在媒体操作前拒绝；
报告保存并显示类型，reopen 验证类型与 requirement namespace。旧 check、Python
未分类 direction 的序列化及旧合同 hash 保持兼容，不改历史 policy 或 packet。
详细兼容规则由 [Visual Quality Gate](../visual-quality-gate.md) 维护。

## Verification

新增5项测试先失败；实现后完整视觉组合41 passed，补充CLI成功及删标签再封存
回归后6项类型聚焦测试通过。独立 `reviewer_xhigh` 审查 `546f134` 为 accept，
确认双向跨类型拒绝及旧序列化/hash兼容，无阻断项。
固定 `546f134^..546f134` 的正式 Harness 9/9 passed，包含Production review
653 passed、final-output/no-regression 52 passed、视觉42 passed。Receipt为
`.agent/harness/runs/genre-visual-gate-546f134-20260914/receipt.json`；在该提交的干净
detached checkout 验证scope、snapshot、policy、artifact hashes、freshness与cleanup
全部为true；完整目录逐文件核对bytes后归档，保存 `receipt-verification.json`。
现有九号 MP4通过新 advertising CLI 提取5帧，报告位于字体研究目录
`advertising-gate/`，保持 NOT_EVALUATED，不制造人类审美或Production验收。
用户选定字体后另建 `selected-font-gate/`，绑定新字体方向与同一旧MP4，
1s标题字形与得意黑样张不符，显式评审字体FAIL，check退出1。Gate校验和裁决
评审证据，不自行识别字体；未改旧影片、旧QA或旧报告。这个受控新方向不适用于电视剧。

## Learning And Publication

按 `record-ai-video-session` 记录，`distill-ai-video-learning` 评估为 no_candidate：
字体研究和离线合同检查不构成多个独立媒体质量实验，不自动采用新的字体白名单。
RAG返回stale advisory fragments，未等待刷新或据其声明当前runtime能力。
其他会话 dirty/staged 内容保留，无Provider submit、push/release或Production activation。
