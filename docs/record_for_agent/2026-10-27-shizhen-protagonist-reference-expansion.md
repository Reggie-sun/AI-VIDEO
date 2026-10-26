---
record_kind: session_summary
topic_id: shizhen-protagonist-reference-expansion
learning_eligibility: ineligible
---

# Shizhen Protagonist Reference Expansion

> Current Board：后续已完成一次已知背面结构错误修复，并用7份核验照片本地固定排版交付3200×2048人物参考板。旧网络UNKNOWN保留；下文初批阻断是历史范围，当前主板证据见文末。

## Scope And Current Evidence

用户要求补充主角多维度参考，并明确以已生成确定的片段为准。以 S01 真人版与获认可 S04 接点修正版原帧为真实输入，未绑定早期 CG 设定图。归档位于 `referces/shizhen/lin-xu/expanded-20261027/`，逐帧 source SHA 和绑定列表由该目录 `source-evidence.json`、`generation-manifest.json` 独占。

内置 `image_gen.imagegen` 共11次调用、8张实际返回，左90度／焦急求证／压抑恐惧3次连接中断为 UNKNOWN，零自动重试。右手手机未提交，已知背面夹克裁片不一致的修复未执行。8张均已逐张查看；7张为静态候选，完整背面1张仅供审看。未展示的裤鞋和完整背部为补全设计，不是成片已确立事实。当前 `PARTIAL_NETWORK_BLOCKED`，费用未暴露，UNKNOWN用量待确认。

用户询问是否误删图片后，实际重开8张工作区副本和8张工具原始输出，均存在且 SHA 一致。`verification.json` 另验证图片解码与8张源帧；源视频未变。没有新增视频/音频调用、Registry/Manifest 写入、Production import/activation 或人类接受。

## Assessment

这是单组身份参考准备，不能从图片数、技术解码或主观静态检查看作通用模型效果、视频身份保持或人工接受。按 `record-ai-video-session` 记录此有界网络阻断检查点；`distill-ai-video-learning` 评估 `no_candidate`，没有可归因独立对照或新的人工接受证据。不修改 Skill、Policy 或 Gate。

## Reference Board Request

用户随后提供角色开发板示例，要求把素材整合为模型参考输入。新增 `expanded-20261027/boards/` 的输入／提示词记录：最初7图在工具本地参数校验被拒绝（最多5张，生图0次），改为5张后一次有效合板请求网络失败、结果UNKNOWN，零重试，未返回合板。旧8张图未变；未使用已知服装结构错误的09图，没有Production写入或新验收。合板保留UNKNOWN，不能把已有HTML总览当作新增合板成图。本次仍为 `no_candidate`。

## Delivered Reference Board

用户继续后，对09已知夹克裁片错误执行一次 `image_gen.imagegen` 修复，实际返回1024×1536背面新版，横向后育克存在、错误中间竖缝消除，头脚与站姿完整；旧09和全部UNKNOWN保留。新原图/副本SHA一致，receipt归 `boards/back-repair-001.json`。

随后以7份已核验照片制作固定HTML/CSS/SVG参考文档并本地Chrome渲染为 `boards/lin-xu-identity-board-v2.png`，3200×2048。没有再次请求未知合板，也未用模型重画整板；板含3全身、4脸部角度、4细节。首版图片面板发生排版挤压，已修正并重开最终PNG逐区检查，头脚/脸/标签完整、无面板重叠。输出SHA、局部显示窗口、原图SHA与实际核验归 `board-layout-v2.json`、`board-verification-v2.json`。完整背部/裤鞋为补全候选，袖口裁切源分辨率有限；人工接受/实际视频模型输入/服从/Production import未验。

初批11次+远程合板1次+已知错误修复1次，共13次有效生图请求，返回9张照片，4项UNKNOWN不重试；本地板渲染不计生图。费用未暴露，UNKNOWN用量待确认。主板已交付，表情和持手机专项仍未完成；未修改运行源码或Production状态。record/learning再评估 `no_candidate`：单一人物参考链及静态观察不能升级为跨镜模型一致性结论。
