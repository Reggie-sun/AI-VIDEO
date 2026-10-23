# Seedance 2.5 Authoring Overlay

这是 authoring-only overlay。current AI-VIDEO capability/profile 与 selected adapter 仍是 exact
support、limits、modes 与 surface behavior 的 authority。

## Use This Dialect

- Complex multi-reference prompt 仍需要 explicit roles。分别分配 identity、scene、style、motion、
  camera、voice、ambience 与 edit-source jobs；reference 含有不需要的 salient properties 时添加
  `must_not_transfer`。
- 只有 exact selected surface 与 current evidence 支持时，才可使用 timestamp 或 interval language。
  继续遵守 event-density discipline；timestamp syntax 是 authoring aid，不保证每个 event 都会被精确渲染。
- 直接说明 edit operation，包括改变什么、保护什么。
- Append extension 从 accepted observed source endpoint 开始；prepend extension 结束时接入
  accepted observed source opening。说明新增 beat，不得根据 original prompt 重建 source state。
- 将 audio behavior、reference ceilings、duration、resolution、file format 与 surface syntax 视为
  current runtime facts；不得从 `2.5` label 推断。

## Specialized Direction

仅在本 overlay 已由 exact selected `2.5` profile 选中时，使用下列 Liyue 方法；不向 2.0
路由注入 2.5 语法、时长或模式，也不因外部方案建议而改选模型。

为每个实际素材注明身份/场景/动作/声音/待编辑来源等职责、有效区间、必须保留和不得继承的内容。
身份参考默认保留所指人物的可见造型，除非已批准缩小范围；不要把脸与服装在多人之间交叉绑定。
编辑明确对象、操作、区间与受保护内容；续写明确新增片段放在原片之前还是之后，并分别接原片
首态或末态。位置实质不明时只澄清这一项，不从含糊的“往前/往后”猜测。

先保留批准的故事、覆盖、台词、总时长和声音要求，再按当前 mode/profile 的可用控制适配。
时间段给动作、倾听、反应和呼吸留空间；减少竞争事件优先于强迫异常语速。参考示例只继承用户
要求的维度，不能把参考结构当作继承其角色、情节、品牌或配乐的授权。

Long Video、extension、video edit、Clay Renderer、transition 和 multi-grid 都只在当前
selected surface/profile 实际支持且任务已选择时使用；上游列表不是 support evidence。

以上为本地重新编写的 authoring advice，来源：
[Liyue SKILL](https://github.com/liyue-aigc/seedance-2-5-video-director/blob/ad0e68ba6ce24fb9ae9c67c9276061cef37663f1/SKILL.md)，
[MIT notice](../../open-video/licenses/seedance-2.5-director-MIT.txt)。

## Repair Bias

结果混合多个 references 时，将每个 asset 收窄为一个 job，并加强 `must_not_transfer`。Timing drift
时先简化 competing beats，再增加 timestamps。每个 retry proposal 只改变一个 authoring variable，
并将 diagnosis 绑定 exact observed output。

## Source Boundary

- Official model overview：<https://seed.bytedance.com/en/seedance2_5>
- Official launch guidance：<https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5>
- 执行前必须从 AI-VIDEO code、sealed profiles 与 selected surface 重新打开 current API/runtime facts。
- Community prompt recipes 可以作为 vocabulary，但不是 capability 或 quality 的证明。
