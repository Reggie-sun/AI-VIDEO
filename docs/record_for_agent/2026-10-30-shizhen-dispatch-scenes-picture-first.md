---
record_kind: session_summary
topic_id: shizhen-dispatch-scenes-picture-first
learning_eligibility: ineligible
---

# Shizhen Dispatch Montage: Picture-First Scene Shots

Date: 2026-10-30

## Request And Direction

用户否定两版独立 TTS（“語氣不對”“不像幀的人”），要求“先把画面做出来”“语言也做下直接用seedance出”。导演覆盖升为 v5（`outputs/shizhen-episode01/opening-dispatch-20261029/director-coverage.v5.json`，分镜 `DISPATCH-SHOTBOARD.v5.md`）：独立 Concept Check 判 v4（一次生成五地点六镜）带条件可做但风险高，改为记录台一条约 26 秒的对白母带（Seedance 2.5）提供全部对白与 D1/D5 画面，D2/D3/D4/D6 现场分开生成、不说话，剪辑时铺在母带对讲声下；D3 推近、D4 上摇回应“运镜太平缓”；字幕不由模型生成。

## Generation (Seedance 2.0 VIP, 1080p, Jimeng browser transport)

六次付费提交，全部 known outcome，无 unknown、无自动重试：

| Shot | Attempt | Credits | Gate |
| --- | --- | --- | --- |
| D2 楼梯 | D2 preview-001 | 198 | FAIL：人从上方楼梯一路走下，读成正常下楼 |
| D2 楼梯 | D2r1 (first_frame) | 198 | PASS（回来从右前景入画，advisory） |
| D3 急诊 | D3 preview-001 | 198 | PASS；偏差：护士未明确抬眼，开头插入特写+切点 |
| D4 七楼 | D4 preview-001 | 231 | FAIL：全景推近而非逐层上摇；无呼救声 |
| D4 七楼 | D4r1 (first_frame) | 231 | 画面 PASS；木板后“救命”两次均未生成，转为组装声音待办（未解决） |
| D6 站台 | D6 (first_last_frame, B6 f0) | 165 | PASS；接 B6 色调略冷，接点 NOT_EVALUATED |

积分按只读报价与余额差核对：69,410 → 68,189（实际结算以平台为准）。参考图由 Codex `image_gen` 生成 5 次（3 场景 + 2 首帧；一次因 stdin 未关闭在调用前等待超时，确认无图片后关闭 stdin 重跑），费用未暴露。每镜声音经 development operator 调用 `audio_understand`（gemini-3.8-flash）6 次，内部上限各 USD 0.05，实际待确认。

## Evidence

- 生成包与脚本：`outputs/shizhen-episode01/opening-dispatch-20261029/scenes-v1/`（build/bootstrap/execute/jimeng.cjs/review_audio，per-shot row/data/prompt/profile/operator-bound/prepare/submit/fetch）。
- 逐镜 Gate：`scenes-v1/qa/<shot>/post-media-gate.json`，含 contact sheet 与音频观察。
- Run roots：`runs/shizhen-opening-dispatch-20261030/{D2,D2r1,D3,D4,D4r1,D6}`；每个 Project provenance 封存 coverage v5，生成经新参考规划门禁（reference_planning + director_coverage）。
- 审看页：`outputs/shizhen-episode01/opening-dispatch-20261029/scenes-review-v1/index.html`（exact MP4 副本）。

## Findings

- 多模态单参考图无法锁住“离开方向”与“镜头起点”：两次 FAIL 都通过 first_frame 锁起态一次修复成功（单例，非规则）。
- 规划器要求每个 identity_continuity 人物有身份参考；只出现一次的群演改由场景参考承载（identity 留空、preservation=unspecified）。
- 运镜 composition event 的 visual_state/purpose 必须逐字出现在 authored prompt。
- 首尾帧同一资产会触发 lifecycle 输入身份唯一性校验；用像素一致的无损重编码作尾帧。

## Remaining

- 对白母带（记录台，Seedance 2.5，董文慧身份参考）尚未生成；D1/D5 画面随母带产生。
- D4 呼救声、D6 时钟走字、D6→B6 接点、字幕与组装（HyperFrames + verify-assembly）未做。
- 用户观看验收：NOT_EVALUATED。

`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate（first_frame 修复为单例，不足以成为规则）。
