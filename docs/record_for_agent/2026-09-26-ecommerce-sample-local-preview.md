---
record_kind: session_summary
topic_id: ecommerce-existing-sample-local-preview
learning_eligibility: ineligible
---

# Ecommerce Existing Sample Local Preview

Date: 2026-09-26

## Purpose

用户要求生成一段可观看的视频，并选择“用仓库现有电商样例做演示”。本轮从已有登记素材重新剪辑、排版和配乐，实际产出新的本地竖屏 MP4；没有新增 Video Provider submit，没有修改既有项目，也没有 push / release。

这项用户请求授权本轮媒体合成，不应继续沿用上一阶段仅 offline verification 的限制，也不授权扩展为新的付费生成、正式发布或用户视觉验收。

## Current Runtime Truth

- 预览文件：`runs/ecommerce-sample-qingyan-20260926-003/preview/青颜-6秒电商样片.mp4`。
- Canonical output：`runs/ecommerce-sample-qingyan-20260926-003/production/state/render/outputs/f8f775e4357d4ec8030142f93e8f07d2631d370884e4717ff97f35d42353c6ce.mp4`。
- 两份文件 bytes 相同，SHA-256 为 `f8f775e4357d4ec8030142f93e8f07d2631d370884e4717ff97f35d42353c6ce`，大小 `1809894` bytes。
- 视频为 H.264 High、`720×1280`、`24 fps`、`144` frames；视频时间为 6 秒，容器包含 AAC 编码尾部，probe duration 为 `6.022` 秒。音轨为 AAC、48 kHz、stereo。
- 前四秒使用原素材第 22–26 秒的户外商品展示，后两秒使用第 26–28 秒的黑底商品镜头，并加入“青颜 / 了解产品”收尾。没有增加功效、价格或百分比文案。
- 已有 BGM 经 canonical P4 audio track 混音，gain 为 `-4000 millidb`，fade-in 为 `4800` samples，fade-out 为 `24000` samples；没有新增配音。

## Inputs And Canonical Execution

先严格重开 `runs/ninebot-n3-lighting-ad-20260920-001/production/project.yaml`，遇到 `Could not reopen generation decision execution binding`，没有修改或绕过该旧项目。随后严格重开并采用以下已登记素材：

| Input | Exact Identity | Existing Owner |
| --- | --- | --- |
| 青颜 clean video | `qingyan-v5-clean-video` / `654867ea044bd32a9c26b2c6a17663174c45172c8e4f4a67ffc50f8033b25839` | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/project.yaml` |
| Mixkit Cat Walk BGM | `mixkit-cat-walk-bgm` / `2c6471144a3273a58e978bad6e181f5529a0cc3afa5715036e67d0056ed26227` | `runs/haokou-ninebot-visual-v11-20260914/composed-production-24s5/project.yaml` |

视频沿用登记的 `project-owner-supplied-local-production` license，音乐沿用登记的 Mixkit Stock Music Free License。素材 bytes 与 Registry hashes 已核对；没有重新下载素材。包装上原生文字来自旧生成素材，不能将其视为已核实的真实 SKU 印刷、功效或商业真实性。

新项目只存在于新 `runs/ecommerce-sample-qingyan-20260926-003/production/`。驱动 `render_sample.py` 使用 `create_ad_creative_plan()`、`compile_ad_creative_plan()`、`resolve_composition()` 和真实 `render_with_hyperframes()`；bootstrap 与 render lifecycle 均由 `ProductionStateCommitter` 持久化。没有 fixture renderer、假分析回调、手写 Manifest、第二条 timeline 或 FFmpeg 成片 fallback。

Renderer 为本机 pinned HyperFrames `0.7.103`，通过既有 network-isolated runner 执行。FFmpeg 只用于既有 canonical audio/render seam、诊断抽帧及最终解码检查。新项目 render attempt `qingyan-sample-six-seconds-render-02` 已成功，并由 committer 写入该新项目的 active render pointer：

- Timeline fingerprint：`5d12f54ee117561010e4387d56b835206625029967c8f5428c972229e1f85474`。
- Render receipt：`production/state/render/render-receipts/50aeb9c1056e925d84a6cde103f6132a5cc893a443461621ef5c5e97e5521f9b.json`，相对于新项目 root。
- 新项目可再次通过 `load_production_project()` 严格重开，包括 render receipt 与 exact output bytes。

## Bounded Diagnosis And Verification

1. `runs/ecommerce-sample-qingyan-20260926-001/` 的准备阶段因将唯一主视觉作为 HERO_ASSET graphic layer 编译，触发 `Shot hero requires a primary visual layer`。该次没有启动 renderer；保留了准备证据。
2. `runs/ecommerce-sample-qingyan-20260926-002/` 使用既有 source video 的正确 presentation lane。Render attempt `qingyan-sample-six-seconds-render-01` 明确记录 `FAILED / renderer_source_invalid / check`，没有输出，也没有 unknown outcome。诊断报告为 `preflight/check-diagnostic.json`：品牌字换行造成与 CTA 重叠，且白字/金字覆盖黄色包装，出现 contrast failure。
3. 保留失败 attempt，建立新输入布局与新 attempt identity。将收尾品牌字和 CTA 移到商品上方黑色留白，调小字号和加宽品牌区域，未修改或禁用 check。`003` 的真实 canonical render 成功；没有重用失败 attempt。
4. 对最终 exact MP4 显式调用 project-local `video-analysis` MCP 的 `video_analyze`，提取六个关键帧并 probe 音视频 metadata。去除内嵌 base64 的报告位于 `runs/ecommerce-sample-qingyan-20260926-003/preflight/video-analysis.json`。
5. Parent 实际查看 0–5 秒关键帧：商品展示完整，切换到黑底商品收尾，新增文字可读，未发现新增文案重叠或遮挡商品。全片音视频 FFmpeg decode exit `0`，无 error output。MCP scene detector 返回一段 scene，不能将该 heuristic 解释为镜头切换证明；切换依据 canonical timeline 和已查看画面。

总计两次真实 HyperFrames render attempt，一次明确失败、一次成功；准备阶段的失败另计。新增 Video Provider submit 为 `0`。这不是 sequential Provider Shot generation，因此不把剪辑合成误报为逐 Shot Provider Gate 或 live generation qualification。

受管 Kimi read-only mapping invocation `075b9a5e-c486-492f-b2e0-10d14ba17b16` 因 output limit 失败，canonical receipt 无可用审查结论；parent 未将其视为 PASS，也没有仅为取得 verdict 重试。该受管外部模型调用与 Video Provider submit 是不同计数。

## Acceptance And Publication Boundary

本轮证明已有真实媒体可经 canonical composition/render seam 生成新的可播放预览。没有调用完整 `EcommerceProductionJob` live authoring/export/generation closure，没有生成 P6、Final Acceptance 或 delivery package。旧青颜 V9 的验收不转移到本次新剪辑；用户主观观看、真实产品印刷 fidelity、音乐主观听感及正式商业验收仍为 `NOT_EVALUATED`。

既有 M0–M7 offline checkpoint 的 pre-existing ARCH002 Harness blocker 没有被本次出片修复或覆盖，详见 [M7 offline record](2026-09-19-ecommerce-production-job-m7-offline-code.md)。本轮没有 runtime code change，也没有用文档 Harness PASS 声称整个实现已获 closure。

本轮 tracked change 仅为这份 session record。媒体、项目及诊断保留在 ignored `runs/`，不提交媒体 bytes。既有 `.codex/config.toml` dirty change 保持原样。记录阶段没有追加 Provider / media / network 调用；documentation policy 的四项 checks 在初版 exact staged snapshot 上通过，receipt integrity / freshness 为 true。此记录最终 commit 另绑定 receipt `.agent/harness/runs/ecommerce-sample-local-preview-record-final-20260926-01/receipt.json`，其实际状态以 receipt 和验证结果为准。没有 push / release，没有主动刷新 RAG index。

自动 `distill-ai-video-learning` evaluation 为 `no_candidate`：同一演示链的准备失败、布局修正与成功版本不能仅凭版本数量视为独立模型质量实验，没有符合 admission threshold 的跨实验 claim，因此不创建 learning placeholder，也不修改 Skill / Policy / Contract / Gate。
