---
record_kind: media_experiment
topic_id: baidaizi-original-canvas
learning_eligibility: ineligible
---

# Baidaizi Original Canvas Seedance Record

Date: 2026-10-10

## Purpose And Exact Inputs

用户确认复刻《零号档案》2资产+重置片段画布中的「视频 10 (17)」，目标 node_bq6wajb5xe。
画布 ID 为 f0ed223b-090e-4ed6-b394-283f8b7dbd07；本次独立 attempt 为 baidaizi-seedance25-canvas-001。
工作证据目录为 `runs/baidaizi-canvas-seedance-20261010-001/`，下文 JSON 均相对此目录。

实际提交原场景、COCO、Nosha 三张 PNG 与原 COCO MP3（6.504s，208173 bytes），没有改成旧派生 WAV。
88 个原文本节点保持顺序，仅将图片 chip 映射为 API 图片序号并补场景图片指代；最终正文 6306 字符。
原文 15 秒与画布 UI 17 秒、COCO 脚步文字与轮式角色图之间的冲突原样保留，没有创作性改写。
模型 doubao-seedance-2-5-260628，17s、720p、16:9、generate_audio=true。
720p 来自历史输出测量，不冒充当前画布分辨率选项或历史请求证明。
源节点/resource 与历史保存的 served bytes 对应，不声称证明上传前原文件的字节身份。

正文 SHA256：e6b23e2d246e41f06b76602cffa4cc8b7ac5c41a045f747183957ceb12545f9d。
实际请求 body SHA256：5fd5f09f1c6715d7a9a817a4a25cc8849d0768e3e3c7d1406795d787380d2bc3。
源文件完整 SHA、绑定与映射见 canvas-input-packet.json、input-fidelity-check.json、final-api-input-review.json。

## Execution And Verification

最小接入口适配已提交并推送 ff3cbbdb5733de8b8f4720df97462a4a67ca450e：
已验证原 WAV/MP3 可与图片组合，保留 Registry、bytes/hash/duration、授权、egress、paid preview 与一次性 permit 检查；
显式 native prompt binding 本地长度边界支持原长正文，通用 compiler 边界不变。
Provider 原生音频 Data URL 依据 [官方 API 文档](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)，未增加网页上传流程。

Claude 在提交前审查 exact 输入，session 4eebf403-2aba-46f1-ab7c-418ce2c5bd03，未发现文本删改或素材错绑；不代表输出质量审查。
受管 Kimi 只读接入口映射 invocation 1a3b3095-bad6-44b1-a9fa-6c889a688648；Parent 审查裁决见 review-risk-decision.json。
实现 Harness receipt：`.agent/harness/runs/baidaizi-canvas-input-20261010-001/receipt.json`，fresh/passed；
其中 Provider tests 906 passed，相关 focused Seedance checks 已通过。工程证据不构成媒体验收。

最初 task-local driver 的 max_polls=180 被现有上限在任何 committer/permit/POST 前拒绝；live.log 保留零副作用失败。
仅改为现有允许值 120，exact API body 不变。submit-wire-observation.json 记录实际物理 POST 总数 1；没有付费重试。
generation-result.json 返回 evaluation_required=true。原始输出未剪辑、未改音、未 activation。

## Actual Output And Review Limits

输出：`runs/baidaizi-canvas-seedance-20261010-001/output.mp4`。
SHA256：9f43043970289bc43f84d884dda4340a8fc6eb185a4d2fc3962eb52fae00c01d。
24,537,613 bytes；17.056s；H264、1280×720、24fps、409 frames；AAC 32kHz stereo。
已显式调用 project-local video-analysis MCP probe 与 extract_frames，查看 0–17s 的 18 张逐秒帧。
保存 video-probe.json、frame-sampling.json、post-media-observations.json。抽帧不冒充连续审片或实际听音。

可见事件包括 A 被撞离平台、COCO 接近、C 附着 Nosha 头部、推车倾斜、果实滚动及 D 吃果实。
但 0s 的 A 可见三颗眼睛而原文要求四颗；16s 的 D 呈圆身、正面大口，而非三角软壳与腹部口器。
这些形态要求 FAIL，不能称逐项完全复刻。逐秒抽帧不足以判定精确接触、完整因果、一镜到底和表演自然度。
没有实际听辨或以 ASR 判定台词；完整对白、声线、音效同步及用户最终接受均 NOT_EVALUATED。
停止本 attempt，不追加生成。旧 H3 反击失败及其他旧素材的验收状态不因本次改变。

## Learning Evaluation

distill-ai-video-learning：no_candidate。本次是单次非受控的完整输入实验，尚无用户完整听看反馈，
不以它推断模型普遍自然、参考控制必然成功或再补 prompt 即能完全复刻；不创建泛化 learning claim。
工程能力已进入 runtime baseline；RAG 索引未刷新。
