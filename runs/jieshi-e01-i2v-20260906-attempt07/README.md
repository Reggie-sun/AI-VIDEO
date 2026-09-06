# S01 Camera Constraint Repair

一次真实Vidu Q3 Pro首尾帧生成，4.042秒1080×1920，保留native audio。输入两图及动作、广播措辞均与06相同，仅修改camera_intent两段文字。

MP4：`production-s01-v7/state/video-generation/fetch/files/88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e.mp4`，3,350,152 bytes。

**Gate FAIL**：机位、约2秒完成的真实左手动作、可见范围无对应镜像及无烧字观察通过；广播word timing为0.84–3.40秒，超过前三秒要求。距离/胸牌/混音/最终字幕仍NOT_EVALUATED。见 `preparation-v1/shot-01-gate.md`。

已完成canonical bootstrap/Planner/readiness/Router/compiler/preview，native reviewer_xhigh提交前accept。唯一POST成功；下载经既有GET-only DNS恢复。已消费一次submit，无activation、无S02。

MCP初检后补充dense frames和word timing。5份 `preparation-v1/frame-sheets/` 是同一exact MP4顺序97帧的256px contact sheets，左上到右下连续，最后3格为padding；仅分析材料，不是修复视频。首个ffmpeg尝试不支持fps_mode，指定系统路径不存在，drawtext缺默认字体；使用实际conda ffmpeg的vsync0及无字体tile后成功，未安装依赖、未覆盖原MP4。
