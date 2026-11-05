---
record_kind: session_summary
topic_id: shizhen-dispatch-master-reference-preview
learning_eligibility: ineligible
---

# Shizhen Dispatch Master Reference Preview

Date: 2026-11-04

## Request

用户先要求读取《失帧》宏观开场的相关文档与记录，再说"先别管声音,就说开场的referces给我看下"。随后同意由主会话为 v5 调度对讲版的记录台对白母带（D1 接报、D5 计数、点名尾段，见 `outputs/shizhen-episode01/opening-dispatch-20261029/DISPATCH-SHOTBOARD.v5.md`）制作参考包，并要求预览认可后再生成。中途又指示"生图修图的额度调高可以10次"。

## Work

- 单元目录：`outputs/shizhen-episode01/opening-dispatch-20261029/master-references-v1/`。审看页 `index.html`；来源、提示词 hash、输入 SHA 与逐张观察记录在 `generation-intent.json`；调用脚本为 `run_codex_image.sh`（Codex CLI 0.166.0 内置 image_gen，每次调用 1 张）。
- 锚点均为既有图：董文慧 identity-v1（`53075b37…`）、宏观同夜造型 `MC03-descent-side-v2.png`（灰褐连帽外套）、已认可市政第 0 帧 `MC01-normal.png`（风格）。
- 共调用 10 次，原上限 8 次、按用户指示上调到 10 次，结果全部已知，自动重试 0 次，视频调用 0 次；模型 ID 与结算金额工具未暴露。
- 当前选用：
  - 环境 `ENV-desk-room-r1`：v1 桌面满是水珠，判为 REJECTED。
  - 道具 `PROP-speaker-notebook-v1`。
  - 关键帧 K1 `K1-D1-listen-v1`。
  - 关键帧 K2 `K2-D1-typed-r2`：v1 空间漂移；r1 画幅为 3:2，已被 r2 取代。
  - 关键帧 K3 `K3-D5-tally-v1`。
  - 关键帧 K4 `K4-rollcall-r1`：表情已改为平静，但人物仍从显示器后探出。根因是场景布局把麦克风放在显示器左侧、座位在右侧，记为 CANDIDATE_WITH_ISSUES，待用户裁决。

## Status

- 以上全部是静态候选，`human_preview_approval=PENDING`，未封存 `preview_approval`。
- 送入模型的图尚未选定：需先核对 Seedance 2.5 所选模式的图数上限。
- 未提交视频，未写 Registry、Manifest 或 Production 状态。
- 声音按用户指示暂不处理。
- 未决设计问题：约 26 秒的母带是连续镜头，如何同时覆盖 D1 中景与 D5 特写（运镜推近或剪辑放大）尚未经 `open-video` 定案。
- 验证范围：PNG 的 SHA 与尺寸已记录；审看页 13 张图经 8883 服务 HTTP 读取全部返回 200；无工程代码变更，因此未运行 Harness。

`record-ai-video-session`: recorded。`distill-ai-video-learning`: no_candidate。本次是单次静态参考准备，没有受控的多实验证据。
