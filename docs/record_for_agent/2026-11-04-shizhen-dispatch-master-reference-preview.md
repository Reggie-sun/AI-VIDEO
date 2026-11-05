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

## K4 Repair

用户选择“修 K4 后再认可”。若直接在环境图里挪麦克风，会破坏 K1/K2 中麦克风的位置连续性，所以不改环境图，改为以 K1 为底图，让人物自己把麦克风连同底座拉到面前（`K4-rollcall-r2`）。本单元上限 2 次，实用 1 次，结果已知，r1 已被取代。观察结果：她坐在原位、不再探身，按键说话；目光偏向麦克风而非扬声器，键盘略向右挤。用户认可仍待定。

## Status

- 以上全部是静态候选，`human_preview_approval=PENDING`，未封存 `preview_approval`。
- 送入模型的图尚未选定：需先核对 Seedance 2.5 所选模式的图数上限。
- 未提交视频，未写 Registry、Manifest 或 Production 状态。
- 声音按用户指示暂不处理。
- 未决设计问题：约 26 秒的母带是连续镜头，如何同时覆盖 D1 中景与 D5 特写（运镜推近或剪辑放大）尚未经 `open-video` 定案。
- 验证范围：PNG 的 SHA 与尺寸已记录；审看页 13 张图经 8883 服务 HTTP 读取全部返回 200；无工程代码变更，因此未运行 Harness。

`record-ai-video-session`: recorded。`distill-ai-video-learning`: no_candidate。本次是单次静态参考准备，没有受控的多实验证据。

## Master Generation (Seedance 2.5, 480p, 30 s)

用户认可参考包与方案（"认可，开始生成"）。随后本地准备发现，当前运行时把 `reference_planning.structure=multi_shot` 的 `MULTI_SHOT_NATIVE_CONTROL_UNDECLARED` 当作阻断，用户改选"改一镜到底"。导演覆盖升为 `outputs/shizhen-episode01/opening-dispatch-20261029/director-coverage.v6.json`，分镜 `DISPATCH-SHOTBOARD.v5.md` 末尾新增 v6 一节。

- 调用器在单元目录下：`build_master.py`、`bootstrap_master.py`、`execute_master.py`、`jimeng_master.cjs`（沿用 scenes-v1 的模式，经 committer、`GenerationFeedbackOrchestrator`、`VideoGenerationService`、Paid Gate 与一次性 permit 执行）。
- 准备阶段陆续发现并修正以下问题，每次换新 root：
  - Scene 未登记全部 scene_reference 图；
  - 缺少显式 selections；
  - 画外转报员被列入 Shot Characters；
  - multi_shot 被规划器阻断；
  - `PERFORMANCE_BEATS_REQUIRED`；
  - anchor/event 的 purpose 未逐字出现在提示词中；
  - 编译器按 asset_id 字母序绑定图片，与提示词编号不符（由任务 lint 拦下）。
  
  每个被放弃的 root 都在 `M1/abandoned-root-*.json` 留有记录，生成请求均为 0。
- `continuity-supervisor` 共审查三轮。第一轮给出 7 个阻断项：PROP 外观冲突、J-cut 下有键盘声、28 秒超时、按键逻辑倒置、终点景别与口型冲突、K4 绑错事件、一镜到底未写回 owner。第二轮只剩 1 个：K2 缺鹅颈麦克风。第三轮无阻断。最终送模 5 张图（ENV-r1、identity-v1、K1、K2-r2、K4-r2），时长 30 秒；PROP 与 K3 只作预览。
- 提交：M1-r9、M1-r10 两次都在参考图上传时失败，状态为 `known_no_effect`（未提交生成、不扣费）。之后同样 5 张图经 canonical transport 上传全部成功；两次失败期间共享浏览器里另一个会话开着约 15 个即梦标签页，疑似资源争用，根因未证实。诊断见 `M1/r9-upload-failure-diagnosis.json`、`M1/r10-upload-failure-diagnosis.json`。M1-r11 作为最后一个有界单元，提交被受理，查询后成功并已取回。
- 成片：`runs/shizhen-opening-dispatch-20261104/M1-r11/state/video-generation/fetch/files/9a776d41….mp4`，24,348,614 字节，854×480，30.08 秒，721 帧，AAC 双声道。审看页为 `master-references-v1/review/index.html`。
- 逐镜 Gate（`shot-gate-reviewer` 子代理，经 project-local video-analysis MCP）判为 **FAIL**，记录在 `master-references-v1/qa/post-media-gate.json`：
  - camera FAIL：7.9–8.5 秒出现交叉溶接，不是一条连续镜头；
  - space FAIL：鹅颈麦克风在 8.5–24.3 秒消失；
  - action FAIL：没有可见的按键再松开；
  - identity、art PASS；
  - performance、sound NOT_EVALUATED：audio_understand 返回 `runtime_required`。
  
  Whisper 时间戳显示七段对白顺序完整，"暂无报告"在 29.86 秒结束。溶接后的构图接近 K2，K2 本身没有麦克风，这只是待验证的假设。
- 积分：报价 360 CRD，实际结算待确认。当前 attempt 已停止，没有自动重抽。

`distill-ai-video-learning`: no_candidate。本次是单次生成，加上一组准备期的程序门禁发现，没有受控的多实验对照。
