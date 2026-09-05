---
record_kind: research_note
topic_id: jieshi-native-audio-post-production-workflow
learning_eligibility: ineligible
---

# Jieshi Native Audio Workflow Research Record

Date: 2026-09-06

## Purpose

记录《界蚀》第一集在 model-native audio 与后期声音制作之间的制作取舍。完整的一手资料、比较表和 S01 建议见
`docs/research/2026-09-06-ai-native-audio-vs-post-production-practices.md`。

## Verified Decision

公开的一手资料支持 hybrid workflow：生成时可取得与动作同步的原生声音，但对白、环境声、Foley、音乐仍以可编辑层进入最终混音。模型音轨存在或大体同步，不等于关键字词、声音身份、无失真或跨 Shot 连续性通过。

S01 的广播“林砚，请在终点站下车。”承担不可替代的情节信息，并且是画外声，没有必须保留原生口型同步的收益。因此当前建议是：

- `final dialogue` 使用受控后期广播对白；
- Provider 原生音轨只作为 source evidence，逐项验收可用的地铁 ambience 与动作声；
- mixed track 中若含错误对白、随机音乐或无法可靠分离的失真，整轨替换；
- 音乐、响度和跨 Shot room tone 由最终音频编排统一控制；
- 字幕绑定 final dialogue / narrative timeline，不从某次生成音轨自动定稿。

## Evidence Boundary

- Vidu Q3 与 Seedance 2.0 的官方材料证明原生音视频能力；Seedance 官方同时承认偶发 audio distortion。
- Vidu Q3 的 `audio_type` 不提供可依赖的对白/音效拆分，因此不能假定后期一定能从 Q3 mixed track 无损保留环境声。
- Runway、Adobe、Avid 与 Blackmagic 的一手材料均保留后期声音设计、分层编辑或最终混音路径。
- 本轮没有生成或分析媒体，没有调用 Provider，没有查询 credential、余额或动态报价，也没有形成 paid submit authorization、quality acceptance、P6 或 Final Acceptance。
- 本轮没有改写 episode creative artifacts；研究只给出供后续精确更新的制作政策文本。

## Verification

- Research artifact: `docs/research/2026-09-06-ai-native-audio-vs-post-production-practices.md`
- Research artifact SHA-256 before checkpoint: `3482f45ffe1b85732434e7e48d612d8b2589a348a8233b1996129107fff3d527`
- Validation: exact-path `git diff --check`

## Learning Evaluation

`no_candidate`。本记录汇总公开一手资料和既有制作边界，没有新增两次独立可审计的媒体实验或 controlled multi-arm comparison，不满足新 Learning Claim 的 admission threshold。

## Next Work

后续若采用该结论，应通过 creative artifact owner 将逐 Shot 声音政策表达为“原生声音优先采集并逐项验收；可用的同步环境声和动作声进入后期，关键对白、跨 Shot 声场、音乐、响度与字幕由统一合成流程决定最终版本”。这项研究本身不授权 Provider submit 或扩大 audio runtime。
