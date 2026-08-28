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
- Extension 必须从 accepted observed source endpoint 开始并说明 next beat；不得根据 original prompt
  重建 endpoint。
- 将 audio behavior、reference ceilings、duration、resolution、file format 与 surface syntax 视为
  current runtime facts；不得从 `2.5` label 推断。

## Repair Bias

结果混合多个 references 时，将每个 asset 收窄为一个 job，并加强 `must_not_transfer`。Timing drift
时先简化 competing beats，再增加 timestamps。每个 retry proposal 只改变一个 authoring variable，
并将 diagnosis 绑定 exact observed output。

## Source Boundary

- Official model overview：<https://seed.bytedance.com/en/seedance2_5>
- Official launch guidance：<https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5>
- 执行前必须从 AI-VIDEO code、sealed profiles 与 selected surface 重新打开 current API/runtime facts。
- Community prompt recipes 可以作为 vocabulary，但不是 capability 或 quality 的证明。
