# Caption Quality Gate Prior-Art Research Record

Date: 2026-08-28

## Purpose

本文记录一次针对成熟字幕/closed-caption production 与 QC 体系的一手资料调研，回答
AI-VIDEO 当前是否确实缺少字幕专项 Gate，以及外部成熟体系如何划分 technical validation、
media-context QC 与 editorial/perceptual review。

本记录是 advisory research checkpoint，不是 accepted architecture、runtime implementation、
P6 policy、Final Acceptance 或新 Provider/media authorization。完整调研与 primary-source links
位于 `docs/research/2026-08-28-caption-quality-gate-prior-art.md`。

## Verified External Pattern

W3C IMSC 1.3、IMSC HRM、EBU-TT-D、BBC、Netflix 与 FCC 的公开一手资料共同支持以下分层：

1. 一份结构化 timed-text artifact 持有 text、timing、style/layout、language 与关联媒体语义。
2. Pre-render validator/lint 处理 syntax/profile、timing bounds、regions/styles、glyph/font、
   duration、language 与 render-complexity 等确定性约束。
3. Standalone technical validation 不能证明 final presentation、readability 或 editorial quality；
   字幕仍需与 exact media 一起 preview/QC。
4. FCC 将 caption quality 分为 `accuracy`、`synchronicity`、`program completeness` 与
   `placement` 四个并列维度。Netflix 也将 Auto QC、Manual QC、waveform sync 与 localization
   operator review 分开，而不是用一个总分替代各 requirement。

BBC 官方 `ttml-validator` 明确声明 technical validation 不是对关联媒体的 presentation/editorial
验收；W3C IMSC HRM 也明确不约束 readability complexity。因此“字幕文件合法”不能升级为
“最终成片字幕合格”。

## AI-VIDEO Mapping

当前代码方向与成熟体系的 source-of-truth pattern 一致：

- `CaptionTrack` 持有 script/transcript、alignment、segment、language、style reference 与
  timing fingerprint；
- `ResolvedTimeline.caption_cues` 消费 canonical caption truth，并继续由同一个 timeline
  独占 sample/frame timing；
- selected renderer 只消费 resolved cues；burned-in pixels 不成为第二份 caption truth；
- 当前 `QaLayer.LAYOUT` 只覆盖 `caption_overflow`、safe area、layer collision 与 transition
  boundary，不能证明 authored text fidelity、full cue presence、audio/semantic sync、double-burn
  或 perceptual readability。

Prior-art-driven proposal 是：

```text
CaptionTrack
  -> deterministic caption lint
  -> ResolvedTimeline.caption_cues
  -> selected renderer
  -> exact final media bytes
  -> Caption Quality Gate
  -> existing P6 review / Final Acceptance ownership
```

这是待单独 architecture decision 的 candidate hypothesis。当前调研没有决定应新增 `QaLayer`、
扩展 `LAYOUT`，还是采用 typed caption sub-policy；也不改变 `ProductionStateCommitter`、
`ResolvedTimeline`、renderer 或 P6 的 canonical ownership。

## Proposed Requirement Groups

调研报告提出六个最小 finding groups，供后续 design 使用：

- `SOURCE_INTEGRITY`
- `TIMING_CONTRACT`
- `RENDER_COMPLETENESS`
- `LAYOUT_READABILITY`
- `AUDIO_SEMANTIC_SYNC`
- `UNINTENDED_TEXT`

每个 required finding 应独立记录 `PASS | FAIL | NOT_EVALUATED`、reason、coverage 与 exact
evidence identities。Aggregate Gate 只能在全部 required findings 为 `PASS` 时通过；OCR、ASR、
waveform、frame sampling 与 renderer telemetry 是 evidence，不拥有 canonical text 或 Production
verdict。Evidence missing、stale、identity mismatch、tool unsupported 或 incomplete coverage 必须
保留为 `NOT_EVALUATED`，不得自动升级为 `PASS`。

## Verification And Publication State

- Research note commit: `b9d972b` (`docs: research caption quality gate prior art`)。
- Exact commit-range Harness receipt:
  `.agent/harness/runs/20260828T110727857994Z/receipt.json`。
- Receipt verification: `passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`complete_completion_proof=true`。
- Harness selected `scope_diff_check`、`docs_contract_check`、`policy_audit_check` 与
  `product_runtime_skill_boundary_tests`; boundary tests reported `2 passed`。
- Research note SHA-256:
  `ba095f1e44ae3b6b4bd8ba38400faeead0132f2385938085f49e2fdec24a54d6`。
- Commit is local `main` only；未 push、未 release。

本轮没有修改 Product Runtime、Manifest、P6 policy、caption assets、media 或 Provider state；
没有执行 OCR、ASR、waveform/media analysis、live/paid Provider call 或 human final-media review。
工作区中其他 staged/dirty files 均保留，未纳入本任务 commit。

## Remaining Decision

若用户授权 implementation，下一步应先根据当前 code/tests/ownership 做 bounded architecture
mapping，明确：

1. caption Gate 的 single owner 与 exact insertion point；
2. pre-render deterministic lint 与 post-render exact-artifact evidence 的边界；
3. required finding schema、language/delivery policy 与 human escalation；
4. 要移除或替换的 old path，以及保持不变的 P6/Final Acceptance lifecycle；
5. schema compatibility、focused tests、Harness routing 与 rollback。

没有该独立 decision 与 implementation evidence 前，不得把研究建议描述成 current runtime truth。

## Agent Guardrails

- `CaptionTrack` valid 不等于 final pixels correct。
- `QaLayer.LAYOUT PASS` 不等于 caption accuracy、synchronicity 或 completeness PASS。
- OCR/ASR 未发现错误不等于 full cue coverage。
- Burned-in subtitle、commercial on-screen text 与 deliberate graphics 必须保留不同 semantic identity。
- Language-specific CPS/CPL、中文断句、kinetic typography 与双语字幕不能使用未经选择的 universal
  threshold。
- Caption Gate 不得自行 activation、repair、retry、Provider submit 或 Final Acceptance。
