# Shot Continuity Motion Endpoint Candidate Record

Date: 2026-08-25

## Purpose

本文记录 rainy-station A2→A3 source failure 的 root-cause closure、一个新的独立
motion-compatible endpoint candidate，以及继续 fresh Production validation 前尚未关闭的
human approval gate。它不把 image generation success、自评或历史 endpoint A/B 提升为
canonical asset、Production evidence、source quality PASS、P6 或 activation。

## Root Cause And Repair Boundary

当前 short FL2VA route 的因果 evidence 已把主要问题收敛到原 A3 endpoint composition：

- 保持 model、seed、A2/A3、workflow 与 sampling 不变的 prompt-only A/B 没有恢复 tail motion；
- 只把 last frame 替换为 motion-compatible development frame 的 endpoint-only A/B 恢复了
  frames 105–119 的 tail motion，并消除了原终点吸附造成的 giant jump；
- 2026-08-25 v7 exact MP4 的 frames 107→108 direct visual review 再次观察到 hard-cut 式
  composition jump，且 frames 116–123 几乎静止。

因此本轮 repair 只允许替换 A3 endpoint bytes。A1、A2、A4、prompt、model、workflow、
124 frames、24 fps、20 steps、`res_multistep/simple`、Turbo off、native audio 与 output contract
保持不变。此前从 generated MP4 导出的 frame 96 仍只属于 development causal evidence，禁止直接
升级为 canonical Production asset。

相关历史 evidence：

- `docs/record_for_agent/2026-08-24-shot-continuity-e0a-development-experiment.md`
- `docs/record_for_agent/2026-08-25-shot-continuity-source-live-attempt.md`

## Independent Candidate

本轮通过一次 image generation call 生成一个独立 PNG candidate：

- external working path：
  `/home/reggie/.codex/generated_images/01a037c9-a74a-7e51-8209-d291ee001ef8/exec-bbb000f4-e8ba-41c7-91da-4e9c95df0643.png`；
- SHA-256：`347e1208215f2d2a4a0b37ec60dbed62daed19dd62ac2a776ab1b308f9fb9c1c`；
- PNG dimensions：`1659x948`；
- exact A2 anchor SHA-256：
  `c50517a17313402ef271694ea058d6c92b0b750c4b854e39858bdaf5d73c5768`；
- original rejected A3 SHA-256：
  `03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c`。

Direct image inspection显示该 candidate 保持同一人物、black bob、mustard-yellow raincoat、
red shoulder satchel、screen-right mid-stride、主体尺度、相机轴、level horizon 与 rainy-platform
透视；clock 没有继承旧 A3 的 sudden enlargement，柱列、轨道与背景也没有切换到另一套构图。
该观察只支持把它提交给 human review，不构成 creative approval 或 endpoint feasibility PASS。

Candidate 未复制进 repository、未导入 Asset Registry、未创建 Shot revision，也未修改 v7。

## Current Gate And Next Executable Step

现阶段必须由 human 对上述 exact PNG bytes 明确判断：

1. creative identity 与 scene intent 是否接受；
2. camera axis、screen direction、subject scale/FOV 是否连续；
3. 从 A2 到该 endpoint 的 displacement 是否在约 5.2 秒持续 lateral tracking 内可达；
4. 是否不存在 teleport、sudden zoom、stop pose 或 terminal composition reset。

在 human approval 之前，结果为 `NOT_EVALUATED`。Agent 自评、image generation success、旧 A3
approval 与 development frame 96 evidence 均不能替代该结论。

若 exact candidate 获批，下一步是在新的 fresh v8 root 中使用 truthful image-import receipt 导入它，
重建 Project/Registry/P0 closure，reseal source/M0 profiles，并以 endpoint bytes 作为唯一变量执行
zero-effect preflight。v7 已有失败 attempt，必须保持 immutable；不得在 v7 retry、mutation 或复用
旧 one-use authorization。

新的 local FL2VA submit 仍须冻结 exact v8 identities、one submit、no retry/fallback，并在 submit 后对
真实 MP4 分别执行 technical probe、source boundary/motion hard gate、automatic P6 与 human/P6 gate。

## Verification And Boundaries

- 已直接查看 exact A2 与新 candidate 原图；两者 dimensions 均为 `1659x948`。
- 已对 candidate bytes 计算 SHA-256。
- 本轮没有启动或调用 ComfyUI，没有 local FL2VA video submit/poll/fetch，没有 retry/fallback，
  也没有修改 Production Manifest、Project、Registry、profiles 或 activation state。
- 本轮发生一次 image generation tool call；其 billing/provider detail 未由工具暴露，因此不推断费用状态。
- `.codex/config.toml` 与 `artifacts/` 的 unrelated dirty state 保持未触碰。

## Agent Guardrails

- `candidate visually plausible` 不等于 `human approved`。
- `human endpoint approved` 不等于 `source video PASS`。
- 新 endpoint 必须进入 fresh bundle；不得覆盖旧 A3 bytes 或改写 v7 failure evidence。
- 下一次视频必须保持 single-variable attribution；不得同时改 prompt、seed、sampler、model 或 route。
- 任何 fetched MP4 仍必须通过 direct real-media review，不能由 Harness、SSIM 或 single-scene detector替代。
