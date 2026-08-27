# Ecommerce Source-Audio Gate Routing Record

Date: 2026-08-28

## Purpose

本文记录 Ecommerce sequential generation 的 source-audio Gate 修正。触发原因是 Qingyan
Seedance Mini complete-ad experiment 在用户要求完整有声广告时仍使用了
`generate_audio=false`，并把声音统一推迟到 P4；该路线忽略了 Seedance 可提供同步原声以及
逐 Shot `SourceAudioPolicy` 已能表达 `KEEP`、`MUTE`、`REPLACE` 与
`TRIM_THEN_MIX` 的事实。

本次完成的是 Agent control-plane 与 authoring validator 修正，不是 generated-audio extraction、
P4 mixer 扩展、Provider live proof、candidate activation、P6 或 Final Acceptance。

## Current Gate Truth

Agent-controlled sequential generation 现在必须在每次 Provider submit 前先解析当前 Shot 的
`SourceAudioPolicy`，再与已经选择的 Provider exact output capability 绑定：

- `source_type=GENERATED` 且 `policy=KEEP` 或 `TRIM_THEN_MIX`：request 必须声明
  `native_audio=true`；Seedance adapter 对应 `generate_audio=true`。Capability 不支持、request
  identity 不符或被改成 `false` 时，submit 前 STOP，不得静音降级、换 Provider 或用未来 P4
  配音冒充同一路线。
- `policy=MUTE` 或 `REPLACE`：raw-MP4 Gate 只验证 exact request/source route，以及仍需的
  dialogue、VO、BGM、SFX、ambience 已有显式 P4 coverage requirements。最终是否真正静音或
  替换，只能在 P4 render 后的 final-composition audio Gate 判断；不能因此阻断下一 Shot。
- `source_type=NONE`：只允许 empty `MUTE` route。
- `source_type=NATIVE`：KEEP/TRIM 需要 exact existing source-audio identity，不能偷换成 Provider
  新生成音轨。

`GENERATED + KEEP/TRIM_THEN_MIX` 的 raw MP4 还必须逐项检查 audio stream parity、decoded audio、
audibility、画面/动作同步、required dialogue/recommendation、speaker/lip-sync binding、重复广告词
与非预期静音。有音轨本身不等于 audio PASS。

## Authoring And Runtime Boundary

`.agents/skills/ecommerce-ad-workflow/scripts/contract_gates.py` 现在 fail closed 地拒绝：

- `source_type=NONE` 却声明非 empty `MUTE` route；
- `p6_measurement_required` 与 `measurement_requirement` 不一致；
- `TRIM_THEN_MIX` 缺少 finite non-negative trim start；
- 非 trim policy 夹带 trim；
- 有 lead-in noise risk 却 KEEP，或缺少 measurement requirement。

该 validator 只证明 `package/2` authoring intent 自洽。当前 package schema 没有 first-class exact
Provider request 或 generated-audio asset binding，因此 `PACKAGE_READY` 不证明
`native_audio=true` 已进入 request，也不证明 embedded audio 已进入 P4。Exact request binding 与
submit STOP 仍属于 Agent Per-Shot Gate。

若最终 canonical composition 需要保留 generated source audio，必须先建立 exact generated audio
asset，并进入 `CompositionSpec -> ResolvedTimeline -> HyperFrames`。当前缺少该 ingestion capability
时必须报告 `REQUIRES_RUNTIME_CAPABILITY`并停止 final-composition/delivery claim；不得移除 source
`muted`、direct mux 或建立第二条 timeline。

## Verification And Evidence

Implementation commit：

```text
f7583eb fix: route ecommerce source audio gates
```

Red phase 的 focused suite 先真实得到 `5 failed, 83 passed`，证明旧 validator 接受矛盾 route，
playbook 也没有 Provider native-audio branch。修正及独立 review follow-up 后：

```text
python -m pytest -p no:cacheprovider tests/test_ecommerce_ad_workflow_skill.py -q
94 passed
```

兼容性检查重新验证既有 v12 package：

```text
artifacts/qingyan-miao-ad-20260827-v12/ecommerce-package.json
status=valid, diagnostics=[]
```

额外验证：

- `python -m scripts.docs_contract_gate check`：PASS。
- `python -m scripts.agent_harness policy-audit`：没有 unmapped、unverified 或 unreferenced owned path。
- `python -m scripts.architecture_gate check`：PASS；输出的 warnings 属于本 task 未修改的既有
  production modules，不是本次 delta。
- `reviewer_xhigh` 首轮 `reject`，指出 raw/final Gate 混淆、package closure 过度声明、无版本迁移的
  P6 收紧与 non-finite trim；修正后 scoped re-review 为 `accept`、无 blocking issue。

本次没有 Provider、network、credential、media generation、activation 或 publication effect。

## Remaining Risk And Next Work

- Per-Shot source-audio routing 当前是 Agent control-plane contract，不是新的 Product Runtime API。
  关键词型 contract test 可防止规则被无意删除，但不能替代未来 executable request-binding tests。
- Seedance raw MP4 即使通过 audio Gate，当前 P4 仍会静音 visual source；generated-audio extraction、
  canonical asset registration、trim/mix 与 dependency/replay/recovery 仍是独立 future Runtime slice。
- 新的 paid Seedance submit 仍需 task-scoped authorization、exact preview、finite budget、cloud-egress、
  durable intent 与 one-use permit；本次 Gate 修正不授权生成。

## Agent Guardrails

- 不得再把 Seedance 或其他支持 native audio 的 Provider 统一路由为静音输出。
- `GENERATED + KEEP/TRIM_THEN_MIX` 必须先证明 exact request 使用 native audio，再允许 submit。
- `MUTE/REPLACE` 的 final verdict 属于 post-P4 final-composition Gate，不得在 raw Shot 阶段伪造。
- `MP4 contains AAC`、raw Shot audio PASS、P4 mixed audio 与 Final Acceptance 是不同 proof layers。
- 不得用 direct mux、移除 `muted`、Provider fallback 或第二 timeline 绕过 canonical owners。
