---
record_kind: session_summary
topic_id: ninebot-visual-sample
learning_eligibility: ineligible
---

# Ninebot Visual Sample

## Delivery

用户要求“做个成品我看下”，本轮沿既有素材和 canonical HyperFrames 生成新成片：
`runs/haokou-ninebot-visual-v11-20260914/delivery/潜江市浩口9号电动车-视觉新版.mp4`。
SHA256 `5112ff05b0238daa527539e19045b61e9a8863014dd2b377bd20ea878c894aeb`，
35,514,333 bytes；H.264 1080×1920、24fps、588 frames，AAC 48kHz stereo，24.522s。
统一中等字重与文字层级，短句随镜头出现；复杂背景使用局部底衬。片尾沿用完整
车辆场景，8–10s 源段以 0.5x 扩展至4秒，端点仅一帧舍入，无长时静帧。
保留既有 Mixkit Cat Walk 音乐，无口播、无新远程 submit。未新增产品代码或依赖。

## Evidence And Repair

同轮 v9 延长片尾错误纳入深色仪表镜头，未交付；v10 修正片尾，但19s标题压脸，
已由新视觉报告工具记录 layout FAIL。v11 把锁车标题移到右上并加局部深底，
重新调用 committer / ResolvedTimeline / HyperFrames，不改旧 Manifest 或验收状态。
v10 prepare 的两次帧数断言发生在 bootstrap 前；修正为588帧后才正式导入。

v11 的 project-local `video_analyze` 实际执行，原始结果保存为 `mcp-analysis.json`。
整段音视频 FFmpeg 解码 exit 0；标准 `load_production_project()` 重新打开成功；
交付副本与 canonical render output SHA256 一致，见 `delivery-verification.json`。
报告工具抽取19帧；已检查关键修复帧和此前同源镜头，17.5/19s标题避让脸部，
24.4s完整车辆及门店信息可见。`review/packet.json`、`observations.json`、
`result.json` 绑定 exact MP4 和截图；整体保持 NOT_EVALUATED，等待用户全片观看。
没有人类审美通过、Production Final Acceptance、上传或投放声明。

## Record And Learning

本轮按 `record-ai-video-session` 记录，`distill-ai-video-learning` 为 no_candidate：
同源确定性修订链不构成独立模型实验。RAG 返回 stale advisory fragments，已重开
当前来源；未主动刷新索引或修改 Learning target。其他任务 dirty/staged 内容保留，
只提交本记录及旧交付记录的指向更新，不 push/release。
