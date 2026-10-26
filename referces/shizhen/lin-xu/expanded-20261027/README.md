# Lin Xu Reference Expansion

## Sources

用户明确要求根据已经生成确定的片段制作。本组实际绑定 S01 真人版第5秒和已获认可 S04 接点修正版第1/8秒的原帧，不使用早期 `linxu-v2` 或 D 版 CG 设定图。[source-evidence.json](source-evidence.json) 保留源 MP4 与提取帧 SHA、请求取帧时间和真实绑定标识；同目录其余抽帧仅作观察。

## Images

打开 [图片总览](index.html)，或直接查看 `images/` 中的原图。已返回8张，均为1024×1536独立单图；7张为静态参考候选，完整背面1张衣服裁片不一致，仅供审看、待修。正面、左右45度、右90度、后脑肩背、全身正面与侧面已补出。全部人工接受仍为 `NOT_EVALUATED`。

保留成片中的五官、黑色蓬松碎发、黑灰翻领夹克与浅灰圆领T恤。裤鞋、完整背部与未被成片充分展示的比例属于补全设计，不能反过来改写原片事实。`06` 的横向肩背裁片与 `09` 的竖缝不一致；不得同时作为同款夹克的精确结构输入。

## Boundaries

用户随后要求按角色开发板示例整合为模型参考输入，新增 [Reference Board](boards/README.md)；该次合板请求连接异常、结果UNKNOWN，当前没有合板图片。旧单图和旧UNKNOWN均保留。

本组用于人物身份、外观和比例参考，不继承原帧中的便利店、店员、骑手、光线、持物和姿态。总览只供审看，后续生成按用途选独立单图，不能把总览直接作为视频首帧。

内置 `image_gen.imagegen` 共调用11次，返回8张，左90度／焦急求证／压抑恐惧3项连接异常、结果未知；保留未知状态、零自动重试。右手手机未提交，背面修复未执行；当前为 `PARTIAL_NETWORK_BLOCKED`，没有宣称整组完成。金额/额度未暴露，未知调用是否产生用量待确认。

## Provenance And Verification

[generation-manifest.json](generation-manifest.json) 保存逐图目标、提示词文件、exact输入绑定、输出SHA/尺寸、观察及失败状态；`prompts/` 保留完整提示词。[verification.json](verification.json) 核验8张本地副本、8张工具原始输出及源帧，全部图片可解码、SHA一致，没有图片被删除。

没有修改原视频、原 Registry/Manifest，没有执行 Production import/activation 或视频生成。图片原件与工具原始输出均保留；Git 仅保存说明、提示词和来源/核验记录，图片本体仍为本地媒体。
