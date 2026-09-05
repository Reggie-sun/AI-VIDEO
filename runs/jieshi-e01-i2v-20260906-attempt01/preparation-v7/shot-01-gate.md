# S01 Post-Media Gate

## Identity

- Attempt: `jieshi-e01-s01-vidu-i2v-attempt01`.
- Exact request: `7db8e13b87b2cea7fe5f961ee8aeb633c98f2d4f68c922c3635018c77bd552cc`.
- Exact MP4: `../production-s01-v1/state/video-generation/fetch/files/b4b4def02532232b3c910999af483604bd677ed0bd9606a2b378951b81e27f8a.mp4`（相对 run 根目录）。
- SHA-256: `b4b4def02532232b3c910999af483604bd677ed0bd9606a2b378951b81e27f8a`；3,724,674 bytes。
- Source first frame: `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。
- Evidence: project-local `video-analysis.video_analyze`，0.5s / 9 frames；随后 `video_extract_frames`，1080px / 9 frames，实际 interval 0.449s。Agent 查看两组返回图片。摘要见 `video-analysis-summary.json`，可重开证据帧见 `gate-frames/index.json`。
- Verdict owner: Codex development per-Shot review。不是 Human full-speed acceptance，不创建 Production ReviewReceipt 或 FinalAcceptanceReceipt。

## Required Findings

| Requirement | Verdict | Exact Evidence |
| --- | --- | --- |
| exact first-frame input | PASS | 出站 payload 哈希和 PNG 字节/hash 已记录；0s 帧保持输入的本人、背景七人和窗口构图。 |
| 输出 9:16 / 1080p raster | PASS | MCP probe 1080×1920、H.264、24fps、97 frames、4.042s。 |
| 原生 1080p 生成来源 | NOT_EVALUATED | container 尺寸为1080p，但 AIGC ProduceID 内含 `720p`；不能仅由文件尺寸证明内部生成分辨率，也不能据此断言经过放大。 |
| 林砚本人坐窗边且七人有倒影 | PASS | 两组采样中本人保持实体、七名背景倒影可见。 |
| 全程唯独林砚无脸、身体或手的对应倒影 | FAIL | 0.898s 和1.0s玻璃右下出现对应悬浮手影；违反全程缺席，即使后段手影消失也不能通过。 |
| 解剖左手真实连续抬起，非图片渐变 | PASS | 0–2.5s左手由膝部依次抬起并展开；右手仍持手机，存在真实动作中间姿态。 |
| 左手朝玻璃，在3秒内停于约2cm处 | NOT_EVALUATED | 手抬起后掌心朝镜头；单目证据不能确认与玻璃的2cm距离或正确接近方向。 |
| 右手黑手机不换手 | PASS | 采样中黑手机始终由右手持于腿部。 |
| 固定机位与场景几何 | FAIL | 画面拉远并重构视角：0s下缘截断前脚，后段双脚完整；窗框、坐姿相对构图持续变化。 |
| 无模型生成字幕/时间戳/片头 | FAIL | 0.449s/0.5s胸腿前方有白色异常数字，类似`0:0::7`。 |
| 身份、服装、工牌连续性 | NOT_EVALUATED | 服装基本延续，但输入工牌从起点就无可读头像姓名，和后续S37变化要求未闭合；未宣称完整人物验收。 |
| 前3秒广播逐字及指定字幕 | NOT_EVALUATED | 此提交按旧无声源素材策略执行；MP4无音轨、尚未后期制作，不能视为S01成片交付。新的原生声音优先规则作用于后续请求。 |

## Decision

`FAIL — STOP_CURRENT_ATTEMPT_AND_BLOCK_S02`。没有 accepted continuity source；未激活视频，未提交S02。不得凭文件下载成功、实际抬手或最终无手影把 required FAIL/NOT_EVALUATED 忽略。

唯一 generation submit 已消费。后续修复必须是新 exact attempt，并落实新的适用调用次数授权、intent/permit；不能复用本次 permit。下一次优先原生声音，同时修正短暂手影、多余文字和机位变化。此文件不授权追加调用。
