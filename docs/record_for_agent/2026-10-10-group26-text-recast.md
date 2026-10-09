---
record_kind: media_experiment
topic_id: fanxiang-group26-text-recast
learning_eligibility: ineligible
---

# Group26 Text Recast

Date: 2026-10-10

## Outcome

用户选择保留写实风格、移除三张人脸参考、由新角色描述生成，其他内容保持。
`runs/group26-recast-20261010-002/` 实际一次 Seedance 2.5 API POST，任务成功，原生 MP4 已下载。
这不构成画布完全复刻、连续声画审片或用户采用；未 activation、未追加生成。
前次 `seedance-api-mixed-20261010-001` 的 HTTP400 privacy 拒绝和单次消费事实保持不变。

## Exact Inputs And Review

- Model `doubao-seedance-2-5-260628`，15s / 720p / 16:9 / native audio。
- 原宿舍 q95 JPEG 与两秒引导 MP4 bytes 不变，只剩一图一视频。宿舍右柱人像海报仍在；旧拒绝不定位图片，不能认定海报是原因。
- 三个 Character 保留原名字、角色职责及服装，改为文字选角，取消旧视觉身份继承；没有从 Shot 删除人物来绕过门禁。
- `recast-prompt.txt` SHA256 `da46ebca4f13822528906d20b166cd4029db841c2a03a9d7783322c97c65df54`。
  原四句对白、五分镜全部逐字保留，只有新外貌描述与宿舍引用重编号变化，见 `prompt-change.diff`。
- 实际请求 body SHA256 `6ca0a33927593b2882050e1d408dbe58e0e0017ce0e9815401f1bcc5568768a4`；
  Claude session `d6fc0ff7-1a39-4b02-814c-41e9b2348684` 对最终输入未发现阻断问题。
- 浏览器重启后仅重新上传相同 guide bytes 取得 API locator；没有网页生成。
  locator 只在内存，经 exact HTTPS GET 核验后由既有 GenerationService/paid owner 提交。

## Runtime Correction And Verification

原 VideoPlanner 把任何 Shot 人物都解释为必须绑定 portrait，导致已授权文字选角被阻塞。
最小修正在现有 `_asset_readiness`：仅首次、显式 scene roles、无已有/已提供 portrait、
无 identity continuity 声明的完整 Character 描述，允许 scene/media R2V；其他身份和前镜 guard 保持。
未更改 paid/network/Registry/committer owner 或建立第二执行路径。

工程提交 `8f8f7ce2232ba507d6a514e4849406c0d27a3701` 已 push `origin/main` 并核验 SHA。
相关 285 tests 通过；完整 staged Harness
`.agent/harness/runs/group26-recast-20261010-002/receipt.json` passed，freshness/integrity 均通过。
Architecture PASS，既有 oversized planner 因一行 import 增量产生一条 warning；新判断放在既有资产检查模块。
Kimi `6260793a-6432-47c3-b278-8c95a27a3498` 仅审旧准备脚本，PARSED；不声称审过后续 planner 修改。
Parent Risk Gate NOT_REQUIRED：纯离线选择逻辑，关键否定分支和真实新任务编译已验证，无凭据或 durable writer 改动。

## Actual Output And Evidence Limits

输出 SHA256 `6199f5978c9caf9c0f636dc247eefa43f0832346f21ea04b0f926fe580d7abd0`，
13,286,011 bytes。交付 `runs/group26-recast-20261010-002/output.mp4` 与 canonical fetch bytes 相同。
Project-local video-analysis probe：H264，1280×720，24fps，361 帧，容器 15.072s；AAC 32kHz stereo。
ffmpeg 全文件解码 exit 0，无错误；未裁剪多出的时长、未修改原音轨。

已实际查看 MCP 的 0–15s 共 16 张逐秒抽帧，未完成正常速度连续听看，未以 ASR 替代听音：

- 抽帧可见曾亮按肩、小龙反应、潘子上铺抓栏、结尾曾亮反应。
- 12–14s 小龙手持手机，与原空手描述有偏差；堵门桌关系未清楚获得画面证明。
- 全段演技自然度、对白完整性、语气、口型与声画因果仍 `NOT_EVALUATED`。
- `post-media-gate.json` 保留 FAIL / NOT_EVALUATED，STOP，无下一 Shot 或自动重抽。

当前只交付这一原生版本供用户听看，不宣称“换模型即可完美复刻”。
自动 `distill-ai-video-learning` 评估为 `no_candidate`：单条新成片尚无完整人工反馈，
提交通过不支持关于模型演技或全部 privacy 输入的通用定律。
