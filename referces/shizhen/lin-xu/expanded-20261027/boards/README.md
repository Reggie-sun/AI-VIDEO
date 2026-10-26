# Lin Xu Character Reference Board

用户提供角色开发板示例，明确这些资料最终作为模型输入，需要整合成多视图人物参考板。目标布局为等尺度正侧背全身、脸部角度和少量服装细节；保留独立单图，表情／持物另按用途准备。参考板只承担人物身份和外观参考，不自动作为视频首帧或单一场景画面。

本次没有返回可用合板图片。初始7图请求在工具本地参数校验阶段被拒绝（最多5个 `referenced_image_paths`），实际生图调用0；收敛到5个 exact bindings 后的一次有效请求发生网络连接异常，结果UNKNOWN，零重试。旧左90度／两项表情UNKNOWN不变；没有把失败的背面全身图作为输入。

`board-request-input-validation.json` 保留首次参数拒绝，`board-request.json` 保留新请求输入与未知状态；对应 `.prompt.txt` 文件保留原文。原始单图未变，未导入Production。后续恢复须先核验该次结果，不能将本目录视为已有合板或已通过模型输入验收。
