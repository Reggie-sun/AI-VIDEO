# Seedance 2.0 Authoring Overlay

这是 authoring-only overlay。current AI-VIDEO capability/profile 与 selected adapter 仍是 exact
support、limits、modes 与 surface behavior 的 authority。

## Use This Dialect

- 优先使用清晰的 visual sequence，不要使用密集 timestamp choreography。Official 2.0 guidance
  提醒 precise timing 可能无法被可靠遵循；除非 exact selected surface 有更强控制的 current evidence，
  否则使用 relative beats。
- 将每个输入的 image/video/audio reference 绑定到一个 semantic job，并说明必须保持不变的内容。
  不得假设 reference ordering 本身就能表达该 job。
- 对 first/last-frame authoring，描述 start state、permitted transition 与 endpoint state。不得在两个
  endpoint 之间引入第二条 continuity story。
- 对 edit 或 extend，直接说明 operation，并保护必须保留的 source properties。只有 current runtime
  selection 已支持对应 profile 时才可使用。
- 将 native audio、reference ceilings、duration、resolution、file format 与 surface syntax 视为
  current runtime facts；不得从 `2.0` label 推断。

## Repair Bias

结果偏离 intent 时，优先减少 competing actions、澄清 reference job，或将脆弱的 clock-time wording
替换为有序 relative beats。每个 retry proposal 只改变一个 authoring variable，并与 exact
accepted/failed output evidence 比较。

## Source Boundary

- Official model overview：<https://seed.bytedance.com/en/seedance2_0>
- 执行前必须从 AI-VIDEO code、sealed profiles 与 selected surface 重新打开 current API/runtime facts。
- Community prompt recipes 可以作为 vocabulary，但不是 capability 或 quality 的证明。
