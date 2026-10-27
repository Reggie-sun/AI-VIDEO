# Lin Xu Reference Expansion

## Sources

用户明确要求根据已经生成确定的片段制作。本组实际绑定 S01 真人版第5秒和已获认可 S04 接点修正版第1/8秒的原帧，不使用早期 `linxu-v2` 或 D 版 CG 设定图。[source-evidence.json](source-evidence.json) 保留源 MP4 与提取帧 SHA、请求取帧时间和真实绑定标识；同目录其余抽帧仅作观察。

## Images

已交付 [人物参考板 PNG](boards/lin-xu-identity-board-v2.png)，3200×2048：正侧背全身、4个脸部角度、发型/衣领/袖口/鞋型细节。一次已知失败的背面服装结构修复已返回新版，按已核验单图固定排版导出。详见 [Reference Board](boards/README.md) 与 [核验记录](boards/board-verification-v2.json)；旧网络UNKNOWN保留，不从合板成功倒填关闭。

打开 [图片总览](index.html)，或直接查看 `images/` 中的原图。初批返回8张，均为1024×1536独立单图；其中7张为静态参考候选，旧背面1张衣服裁片不一致，仅供历史审看。后续新增同尺寸背面修正版，现有9张照片、8张静态候选。正面、左右45度、右90度、后脑肩背、全身正面与侧面已补出。全部人工接受仍为 `NOT_EVALUATED`。

保留成片中的五官、黑色蓬松碎发、黑灰翻领夹克与浅灰圆领T恤。裤鞋、完整背部与未被成片充分展示的比例属于补全设计，不能反过来改写原片事实。`06` 的横向肩背裁片与 `09` 的竖缝不一致；不得同时作为同款夹克的精确结构输入。

## Boundaries

最初远程合板请求连接异常、结果UNKNOWN；后续用已核验照片做本地文档排版，已导出上述参考板，未重复该远程请求。旧单图和旧UNKNOWN均保留。

本组用于人物身份、外观和比例参考，不继承原帧中的便利店、店员、骑手、光线、持物和姿态。总览只供审看，后续生成按用途选独立单图，不能把总览直接作为视频首帧。

初批内置 `image_gen.imagegen` 共调用11次、返回8张，左90度／焦急求证／压抑恐惧3项UNKNOWN，零自动重试；这一历史计数不改。随后远程合板1次UNKNOWN，另一次已知背面结构修复返回新版（`09-full-body-back-r2.png`），总计13次有效生图请求、9张已返回照片、4项UNKNOWN；最初7参考图的本地参数拒绝不计生图。右手手机仍未提交、表情专项未补齐；人物主参考板已完成静态检查，尚未获得人工接受或模型实际使用验收。金额/额度未暴露，UNKNOWN用量待确认。

## Provenance And Verification

[generation-manifest.json](generation-manifest.json) 保存逐图目标、提示词文件、exact输入绑定、输出SHA/尺寸、观察及失败状态；`prompts/` 保留完整提示词。[verification.json](verification.json) 核验8张本地副本、8张工具原始输出及源帧，全部图片可解码、SHA一致，没有图片被删除。

没有修改原视频、原 Registry/Manifest，没有执行 Production import/activation 或视频生成。图片原件与工具原始输出均保留；Git 仅保存说明、提示词和来源/核验记录，图片本体仍为本地媒体。
