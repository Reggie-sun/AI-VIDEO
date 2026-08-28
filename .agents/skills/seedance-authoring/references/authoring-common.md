# Shared Seedance Authoring Knowledge

本文件保存可跨 version 使用的 authoring guidance，不定义 runtime capability、provider parameters、
asset identity、production validation 或 lifecycle state。

## Evidence Order

facts 冲突时，保留各自的 authority，不得混合：

1. Approved AI-VIDEO Character / Scene / Shot facts 拥有 creative intent。
2. Current AI-VIDEO capability/profile 与 selected adapter 拥有 executable support 和 surface
   semantics。
3. Official model guidance 可以影响 exact selected version 的 authoring language。
4. Community recipes 与 observed heuristics 始终是 advisory，必须明确标注。

不得将一次成功 lint、一个 upstream template 或一个 observed clip 升级为 current runtime 或
Production acceptance truth。

## Prompt Grammar

使用可观察的表达，并保持 chronology 清晰：

```text
subject 与 stable identity
-> visible action 与 state change
-> scene 与 spatial relations
-> 一个 primary camera treatment
-> lighting 与 visual treatment
-> 必要时加入 audible action / dialogue / ambience
-> constraints 与 protected properties
```

- 描述可见或可听的内容，不要用 mood label 取代 action。
- 每个 Shot 保留一个 primary camera intent，除非 approved Shot 明确包含 cut。
- 按 start state -> action -> resulting state 排列事件。Selected duration 无法清晰表达所有 beat
  时，降低 event density。
- 保留 approved names、appearance、wardrobe、objects、screen axis、direction 与 causal anchors，
  不得虚构缺失的 story facts。
- Audio 仅作为 authoring intent。Exact native-audio support 与 final mix ownership 仍属于 current
  AI-VIDEO runtime facts。

## Reference Role Map

每个输入 asset 在进入 prompt 前都必须有一个 primary semantic job：

| Role | Authoring meaning | Typical protection |
| --- | --- | --- |
| `first_frame` | I2V/FLF2V 的 exact visual start state。 | 除非 Shot 明确改变，否则保留被锚定的 identity、composition 与 starting state。 |
| `last_frame` | FLF2V 的 exact intended endpoint。 | 保留 endpoint identity/state；不得把它描述为 generic style image。 |
| `reference_image` | 不作为 start frame 的 identity、object、scene 或 style evidence。 | 只 transfer 被点名的 properties。 |
| `motion reference` | Action rhythm、camera path、physical motion 或 timing example。 | 未明确授权时不得 transfer identity、wardrobe、location 或 audio。 |
| `reference_video` | 用于 R2V、edit 或 extend 的 motion/style/source video。 | 明确 operation 与 protected source properties。 |
| `reference_audio` | Voice、dialogue、ambience、music 或 timing evidence。 | 只 transfer 被点名的 audio property；不得推断 visual identity。 |

对每个 asset 记录：

- `primary_role`：只能有一个 dominant job；
- `transfers`：允许 prompt 继承的 properties；
- `must_not_transfer`：必须排除的 properties；
- `target`：接收 transfer 的 approved subject、object、scene、action、camera 或 audio intent。

Reference 含有显著但不需要的 identity、wardrobe、location、composition、motion、text、branding
或 audio 时，必须提供 `must_not_transfer`。如果一个 asset 被要求承担冲突的 jobs，应拆分 intent
或返回 ambiguity，不得静默合并 roles。

## Mode-Specific Expression

- `T2V`：不得使用 implicit asset binding。
- `I2V`：说明 `first_frame` 锚定什么，并描述从该状态开始允许的变化。
- `FLF2V`：区分起点 `first_frame` 与终点 `last_frame`；不得把两者都称为 generic reference。
- `R2V`：在正文中说明每个 image、video 与 audio reference 的 job。
- `edit`：使用 direct operation wording，例如 replace、remove、preserve、recolor、relight 或
  restage，并给出 exact protected properties。
- `extend`：使用 direct operation wording；从 exact source output 的 accepted observed state
  开始，只描述 continuation beat。此前的 prompt 不是 actual source endpoint 的证据。

## Authoring Consistency Check

handoff 前确认：

- 每个 referenced asset 都存在于 input contract；
- first/last/reference roles 未被混淆；
- 每条 transfer 与 `must_not_transfer` rule 都可追溯到 approved intent；
- prompt chronology 不存在 impossible overlap 或 contradictory state；
- edit/extend 直接说明 operation；
- 未猜测 runtime limits、file formats、reference counts、mode tokens 或 node/API fields；
- 所有来自 community 的 heuristic 都标注为 advisory。

这只是 authoring check，不是 provider validator、continuity verdict、media lint、Harness receipt
或 Production acceptance gate。
