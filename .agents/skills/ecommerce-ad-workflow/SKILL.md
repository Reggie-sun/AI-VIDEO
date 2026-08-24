---
name: ecommerce-ad-workflow
description: Use when an ecommerce, SKU, product advertising, direct-response product video, or commercial product brief needs structured authoring; not for AI comic, episodic fiction, campaign publishing, or Provider execution.
---

# Ecommerce Ad Workflow

## Overview

把已获授权的商品资料转换为 `EcommerceAdProductionPackage`。Product Truth 先于创意；每项 claim、商品呈现、广告图文、audio cue、Shot 与 Runtime gap 都必须可追溯。输出是 authoring contract，不是媒体、Runtime state 或广告效果证明。

## Boundaries

- 只服务 ecommerce / product advertising；AI comic、episode、serial、cliffhanger 输入立即停止。
- 不抓取未授权页面，不读取 credential，不联网，不调用 Provider，不生成媒体，不写 Project、Registry、Manifest 或 activation。
- 不选择 renderer/timeline/Provider，也不把 `DIALOGUE_SUBTITLE` 当作 commercial graphics fallback。
- Valid package 不证明 compositing、typography、audio stream、watchability、P6、Final Acceptance、live-ready 或 advertising performance。

## Decision Sequence

按 G0→G7 顺序执行。每个阶段只读取列出的 reference；blocking finding 立即返回 exact gate、diagnostic code、evidence gap 与所需决定，不继续伪造 ready package。

| Gate | Required result | Read |
| --- | --- | --- |
| G0 Product Truth | SKU、asset rights、facts、allowed/prohibited claims与disclaimers闭合；医疗/治疗 claim 禁止 | [product-truth-and-claims.md](references/product-truth-and-claims.md) |
| G1 Strategy | audience、pain point、objective、angle、promise、proof与objection一致 | [audience-angle-and-proof.md](references/audience-angle-and-proof.md) |
| G2 Hook / Beats | 第一秒有 observable Hook；beats有因果和非机械 duration budget | [hooks.md](references/hooks.md), [ad-beat-sequences.md](references/ad-beat-sequences.md) |
| G3 Product Presentation | intro/demo/proof/hero/CTA均有 typed role、mode、source与capability classification | [product-presentation.md](references/product-presentation.md) |
| G4 Copy / Audio | commercial roles与captions分离；商品名可见/可听；audio coverage完整 | [advertising-copy-graphics.md](references/advertising-copy-graphics.md), [audio-pacing-and-coverage.md](references/audio-pacing-and-coverage.md) |
| G5 Storyboard / Shots | beat、Shot、presentation、copy和audio cue双向可追溯 | [ad-beat-sequences.md](references/ad-beat-sequences.md) |
| G6 Runtime Handoff | 只输出 proposals、requirements与classified gaps；保持现有 owners | [runtime-handoff.md](references/runtime-handoff.md) |
| G7 Ad QC | truth、Hook、placement、copy、audio、CTA与brand closure无 blocker | [ad-qc.md](references/ad-qc.md) |

完成 master package 后，只有需要受控 creative experiment 时才读取 [creative-variants.md](references/creative-variants.md)。外部方法来源与 license posture 见 [external-method-sources.md](references/external-method-sources.md)；不得由此安装、fork 或 vendor 外部 repo。

## Contract Workflow

1. 将用户提供的资料写成 `ecommerce-ad-workflow/input/1`；未知事实保持未知，不补写营销 copy。
2. 运行：

   ```bash
   python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py --kind input --file PATH
   ```

3. 仅在 G0–G7 闭合后生成 `ecommerce-ad-workflow/package/1`，并以 canonical input SHA-256 绑定 `source_input_hash`、以不含 `package_id` 的 canonical package identity 绑定 `package_id`。
4. 运行：

   ```bash
   python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py --kind package --file PATH
   ```

5. Exit `0` 只表示 authoring contract valid；exit `2` 返回稳定 contract diagnostics；exit `3` 表示 validator internal failure。任何非零结果都不得标为 `PACKAGE_READY`。

## Output Shape

交付 exact input/package paths、schema versions、validator JSON result、G0–G7 gate summary、claim/source lineage、Runtime capability classifications与 unresolved blocker。`runtime_handoff` 只能投影到现有 `ProductionBrief`、talent-as-`Character`、set-as-`Scene`、`Storyboard`、`Shot`、`AudioTrackSpec` 与 `CaptionTrack` requests；advertising graphics和physical interaction保持独立 capability requirements。

## Stop Conditions

rights/claim/source 缺失、医疗 claim、第一秒 Hook 缺失、商品名缺失、fake physical interaction、commercial copy 全部降级为 subtitle、非 intentional audio gap、dialogue binding不全、CTA/end card缺失、multi-variable variant、或 Runtime execution/acceptance字段出现时停止。返回 blocker，不调用 `open-video`、AI comic workflow、外部 ad system或任何执行 fallback。
