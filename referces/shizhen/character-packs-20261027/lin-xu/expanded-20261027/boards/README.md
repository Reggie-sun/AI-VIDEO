# Lin Xu Character Reference Board

## Current Board

[林序人物参考板 PNG](lin-xu-identity-board-v2.png) 已落盘，3200×2048，正侧背全身、4个脸部角度和4个局部细节。直接由7份已检查照片通过 [固定排版](lin-xu-identity-board-v2.html) 本地渲染导出；[来源布局](board-layout-v2.json) 保留图片SHA与显示窗口，[核验记录](board-verification-v2.json) 保留输出SHA、规格和观察。没有调用生成模型重画整板，也没有覆盖或关闭旧合板UNKNOWN。

原背面照片的中间竖缝与肩背图不一致。`back-repair-001.json` 记录一次对该已知错误的修复，已返回 `../images/09-full-body-back-r2.png`，横向后育克与肩背图一致；旧09保留供历史审看，新版进入本板。完整背部与裤鞋仍是未被成片充分展示的补全候选；袖口局部来自全身图裁切，细节分辨率有限。人物板为静态参考候选，不等于人工接受、Production import或实际模型服从。

## Historical Remote Request

用户提供角色开发板示例，明确这些资料最终作为模型输入，需要整合成多视图人物参考板。目标布局为等尺度正侧背全身、脸部角度和少量服装细节；保留独立单图，表情／持物另按用途准备。参考板只承担人物身份和外观参考，不自动作为视频首帧或单一场景画面。

该次远程请求没有返回合板图片。初始7图请求在工具本地参数校验阶段被拒绝（最多5个 `referenced_image_paths`），实际生图调用0；收敛到5个 exact bindings 后的一次有效请求发生网络连接异常，结果UNKNOWN，零重试。旧左90度／两项表情UNKNOWN不变；没有把失败的背面全身图作为输入。

`board-request-input-validation.json` 保留首次参数拒绝，`board-request.json` 保留该远程请求输入与未知状态；对应 `.prompt.txt` 文件保留原文。原始单图未变，未导入Production。旧请求恢复须先核验其结果；本地v2板不证明旧请求无效果或已通过模型输入验收。
