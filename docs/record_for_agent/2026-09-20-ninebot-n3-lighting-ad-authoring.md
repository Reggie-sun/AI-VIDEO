---
record_kind: session_summary
topic_id: ninebot-n3-lighting-ad
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Ninebot N3 Lighting Ad Authoring Record

Date: 2026-09-20

## Purpose

为「浩口九号智能电动车」门店的九号 N3 系列电动车创建抖音竖屏 30 秒 AI 广告 authoring package，主打 ALC 全境光幕照明系统。本记录只覆盖 ecommerce authoring contract（input/1 + package/2）的建立与验证；不含任何媒体生成、Runtime 执行或质量验收。

## Current Truth Boundary

- 本片的 authoring contract 已闭合：`AdQCReport.ready=true` 只表示 Ecommerce authoring readiness，不证明 compositing、audio stream、watchability、P6、Final Acceptance 或投放效果。
- 尚未执行 runtime handoff export；该 export 需要 exact `DeliveryProfile`、reviewed `EcommerceVisualSystemProfile`、per-ad `EcommerceLayoutPlan` 与 `EcommerceProductionCompileProfile`，且需 per-ad visual review 先行。这四项目前都不存在。
- 未发生任何 Provider 调用、媒体生成、网络访问或付费动作；本地 ComfyUI 豁免在本阶段未被使用。
- `advertising_copy_graphics` capability gap 如实分类为 `REQUIRES_RUNTIME_CAPABILITY`，未被 prose 隐藏。

## Session Work And Decisions

- 素材：用户提供的 10 张门店实拍照片复制到 `artifacts/ninebot-n3-lighting-ad-20260920/assets/` 并语义化重命名（ALC 贴纸特写、N3 85C/N3 70/N85C 整车与铭牌、三张价格牌、一张抖音同行截图）。
- 抖音截图（`douyin-reference-screenshot.jpg`，含第三方 @MotoAge·电行 内容）仅列入 `references` 作风格参考，不作为 source asset。
- G0 Product Truth：7 条 allowed claims 全部绑定贴纸/价格牌事实与用户 attestation（用户确认照明卖点属于主推 N3 系列且可商用）。required disclaimers：「价格与优惠详情咨询当地门店」「性能数据来源于九号科技实验室」。
- 用户决策（经确认）：主推 N3 系列组合；照明 claim 全部可用；抖音 9:16 约 30 秒；CTA 为到店引导。
- 范围决策（记录在 `ad_strategy.proof_boundary`，非 unresolved）：N3 85C 存在两张价格牌（¥4199起/续航76km 与 ¥4299起/续航73km），本片只采用 ¥4199 起版本事实；N85C 仅作价格带展示，不绑定 ALC 照明 claim。
- 结构：5 beats（HOOK 0-3s / PRODUCT_INTRO 3-8s / DEMONSTRATION 8-16s / BENEFIT_PROOF 16-23s / CTA_CLOSE 23-30s），5 shots，talent-free，中文 VO + 音乐 + 两个 SFX，全部 generated source audio policy 为 MUTE（VO/music/SFX 由显式 P4 audio events 覆盖）。
- product name 定为「九号 N3 系列」以满足 product-name visible/audible gate（出现在 BRAND_END_CARD 与 VO）。

## Verification And Evidence

- `python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py --kind input --file artifacts/ninebot-n3-lighting-ad-20260920/ecommerce-input.json` → `{"diagnostics":[],"kind":"input","status":"valid"}`。
- `python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py --kind package --file artifacts/ninebot-n3-lighting-ad-20260920/ecommerce-package.json --source-input-file .../ecommerce-input.json` → `{"diagnostics":[],"kind":"package","status":"valid"}`。
- package identity：`source_input_hash=582605d817fa9411c69a46e92dff77cd59a4c29c99793c688e085b953736fffd`，`package_id=2dee026943d33e04b86cdb23037c58cd9e38dc9decba0b5b36cb071b40ce90de`。
- package 由 `artifacts/ninebot-n3-lighting-ad-20260920/build_package.py` 生成，hash 算法与 validator 的 canonical JSON（sort_keys、紧凑分隔符、UTF-8）一致。
- 校验过程中修复的 contract 问题（均为 authoring 层，非 Runtime）：`product_surface` 不接受 null；claim_ledger `used_at` 必须引用真实存在的 ID；product name 必须出现于 PRODUCT_LABEL/BRAND_END_CARD 或 VO；beat↔audio event 需双向一致（demo 段拆出独立 `audio-sfx-light-hit-demo`）；ready package 的 `unresolved_items` 必须为空；package `product_truth` 必须与 source input 逐字节一致（改为直接注入 input 内容）。

## Remaining Risks Or Next Work

- 下一步是 per-ad visual review，然后按现有 M0-M7 路径创建四个 visual contract identity 并执行 runtime handoff export；再进入本地生成与 Per-Shot Post-Media Gate。本片尚未做任何媒体生成。
- N3 85C 两张价格牌的版本差异未获用户解释；若后续要同时使用两个价格，需用户确认版本关系。
- N85C 是否同样具备 ALC 照明未确认；当前 claim 绑定只覆盖 N3 系列。
- `advertising_copy_graphics`（HEADLINE/价格卡/CTA/end card 等商业图文）尚无 Runtime 执行面，handoff 后需按既有 gap 路径处理。

## Agent Guardrails

- 本记录只证明 authoring contract valid；不得据此声称成片质量、Runtime 支持或投放效果。
- 任何后续生成都必须走既有 Provider Gate 与 Per-Shot Post-Media Gate；本片 price/disclaimer 小字是必需元素，不得在视觉执行中省略。
