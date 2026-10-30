# MC00 v4 Pre-generation Feasibility

范围：仅前期作者审查，不是视频或接点验收。

- 首帧：`first-frame-1920x1080.png`，SHA `349b3581b2681ae1724d496a05d30b7cf0650ab678ce03e214f3116ab10b5260`；来源为 Codex 生图 `codex-image/raw/first-frame-v2.png`（SHA `a425fb681a075a09b4c5279437278c9a0a6dc54340433d54f93cf82fe6713268`），仅 FFmpeg Lanczos 尺寸适配。
- 尾帧：已认可市政第0帧 `MC01-normal.png`，SHA `a2cef0e9ff42796e09e72105bb04ea336149b4551a20dc767ffdd3179910eeed`，唯一末态锚点（方案A）。
- 首帧湿墙与檐口约占左侧55%，主路、车流和市政作业区被墙遮挡；右侧仅见旧住宅屋顶、窗灯与远处高楼。向右绕过墙角后主路才出现，符合尾帧“主路在左、作业区在右”的布局。
- 首尾朝向一致：路线为右移揭示→沿主路右侧上空前进下降→人眼高度减速停稳，见 `route-design.json`。
- 景别从高处檐口近景变为地面中景，`same_subject_scale=False`；不以变焦跳转、隐藏切镜或静止尾段替代运动。
- 未证明：实际视差、建筑稳定、站棚形制、工人是否重复按停、声音与 MC01 接点，全部待 exact MP4 验证。
