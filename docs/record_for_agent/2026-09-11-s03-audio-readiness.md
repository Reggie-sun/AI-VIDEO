---
record_kind: session_summary
topic_id: jieshi-s03-audio-readiness
learning_eligibility: ineligible
---

# S03 Audio Readiness

## Supersession Notice — Speech Batch Contract

2026-09-11 的后续[语音批量测试记录](2026-09-11-minimax-speech-batch-tests.md)已实现并离线验证 MiniMax Speech 免逐次用户授权、免用户金额预算的有限批次入口；下文预算配置/费用结算阻断为修改前历史。独立语音 run 的唯一真实执行为 `OUTCOME_UNKNOWN`，没有 WAV，仍未完成 S03 配音或恢复原视频 lifecycle。原 S03 Manifest 与历史 QA/verdict 保持不变。

## Execution Boundary Recheck

用户再次允许继续后，standard `load_production_project()` 已重开 S03 revision11/schema2.7；原 Manifest SHA 仍为 `c340d0a5ca174835a13f4dfc511f11fa725ee797a36ea11cc368e1203f274b27`。video attempt 是 RUNNING、paid phase 是 ACCEPTED；reservation 为 RESERVED、actual cost 未知，不能将此简称成 typed UNSETTLED。当前没有生成对白或创建新 Production bundle。

独立 reviewer_xhigh 与 parent 源码核对确认：`_state_commit_voice_activation.py::generate_voice_asset()` 在没有 Provider reported cost 时，将 measured units × configured unit price 作为 actual cost 结算。因此不能为满足“语音不需要预算配置”而填入历史零价，或把 operator ceiling 冒充 actual cost。用户无需再次授权、提供凭证或配置预算；当前是既有执行/结算契约的适配限制，不能宣称只完成参数配置即可提交。

新建具有独立身份、仅交付 WAV 的 voice project 可以由现有 bootstrap API 表达，但不能解释成原 S03 lifecycle 已恢复、清空原账本或已完成音视频集成；它也不能消除上述费用语义限制。原 root 的 voice admission 仍拒绝 RUNNING attempt。未采取复制 Manifest、直接 transport、generated-as-imported 或 direct mux 旁路。独立审查拒绝当前立即 submit，parent 验证了关键结算分支与 source 状态。本轮仅更新本记录，无 runtime/history/media mutation、commit/push。自动 learning evaluation 为 `no_candidate`。

## User Budget Direction

用户随后明确“语音不需要预算配置”。后续不得再把要求用户新增语音预算作为前置问答；operator preparation 已记录 `user_requires_separate_voice_budget=false`。这不是新增免费资格或账单证据，也不授权删除内部 permit、来源及恢复检查。本轮未调用 Provider。实际 voice 执行路径还须处理 source Manifest 中仍为 RUNNING 的 S03 video attempt：`begin_voice_generation()` 不允许在存在 unresolved attempt 的同一 Manifest 上开始新 voice attempt；不能将人审 sidecar 自动冒充该 lifecycle 已完成。此项需通过既有 owner 完成合法状态准备，不能直接调用 transport。

## Chinese Configuration Checkpoint

用户明确选择现有 MiniMax Speech 并授权配置后，已在唯一 owner `minimax_speech.py::_request_is_supported()` 增加 exact `Chinese` admission，保留 English、原 endpoint、sealed identity、预算、secret capability 和 durable one-use permit。下文 English-only 阻断属于修复前历史，不再是当前代码状态。

S03 operator preparation 保存于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s03-audio-v1/voice-selection.json`：`speech-2.8-hd`、`male-qn-jingying`、Chinese、P2、原文“什么？没报站啊。”、44,100 Hz mono PCM WAV、speed_milli=1000、Secret Service reference、task ceiling=1/used=0。它明确为 `PREPARED_NOT_SUBMITTED`，不是已激活 character revision、sealed Production request 或 permit。参数通过现有 `VoiceProviderParameters` 验证。官方语言和音色来源及入口用法见 [MiniMax Speech](../minimax-speech.md)。原 playbook 中遗漏的 Secret Service 定位条目已恢复，不保存密钥值。

新增回归先实际 RED：1 failed/31 passed，失败于中文 preview admission；单行 runtime 修复后 focused suite 32 passed。audio/ElevenLabs/MiniMax/voice-e2e 组合 159 passed。Native reviewer_xhigh 独立只读审查 verdict 为 accept，并验证语言 fingerprint、中文 UTF-8、无效 permit 时零 secret/transport calls。

其余 policy 要求的 ad-creative/composition/HyperFrames/generated-audio/captions/state-commit/state-recovery 组合实际 816 passed/3 skipped（329.52s）。与前述159项合计，composition/audio policy suites 为975 passed/3 skipped，结果来自当前已说明的 working tree，不是 isolated snapshot。最终 diff check 通过；S03 Manifest 仍为 revision11、SHA `c340d0a5ca174835a13f4dfc511f11fa725ee797a36ea11cc368e1203f274b27`。

实际 live 阻断为未找到当前适用的 Speech budget 配置。历史 `minimax-speech-replacement-20260819-001/call-1` 和 `call-2-combined` 的 paid gates 都属于 `minimax-coding-plan-quota`，per-call ceiling=0；不把它们转换为当前免费资格或新预算。当前一项 submit 尚未消费，没有读取密钥、生成音频、修改 Manifest 或重生 S03。用户禁止 commit/push 的约束保持。

Documentation contract 检查通过；runtime-skill/docs/Harness/hook 组合为 226 passed/1 failed，唯一失败是此前已存在的三个 unmapped paths：image_import_video_frame.py、paid_provider_no_effect_reconciliation.py 和对应 test。Repository Architecture Gate 返回 PASS 并带历史 WARN；不是 isolated task-delta receipt。没有 fresh passing exact-snapshot Harness，不把 working-tree 检查冒充该证明。自动 learning evaluation 为 no_candidate。

## Credential Discovery Correction

用户要求自行判断已有音频接入后，从历史 credential-location 记录找到 MiniMax Speech 的精确 Secret Service 引用：label `AI-VIDEO MiniMax Speech`，attributes 为 `application=ai-video`、`provider=minimax-speech`、`credential=MINIMAX_SPEECH_API_KEY`。本轮通过 `org.freedesktop.Secret.Service.SearchItems` 对这组属性做 metadata-only 查询，返回一个 unlocked item、零 locked items；没有 GetSecret、没有读取或输出密钥值，没有网络请求。

此前根据环境变量缺失推断“缺少凭证”不成立；当前 playbook 没有对应条目也不证明系统 keyring 中不存在。已发现的现有服务是 MiniMax Speech，不应因漏查直接切到 ElevenLabs。条目存在不证明远程凭证有效、余额或可用声线；当前已复现的本地阻断仍是 MiniMax adapter 的 English-only admission。后续应沿这个既有接入处理中文配音支持及真实 readiness，而不是要求用户再次提供密钥或另建音频系统。本次没有生成声音、修改 runtime 或推进 S04。

## Corrected Assessment

用户指出项目已有音频接入和模型原生声音后，本轮重新核对：不能从 MiniMax adapter 的 English 限制推断整个项目缺少中文音频入口，也不能把修改该 adapter 认定为唯一下一步。下方原 Next Boundary 的修改建议已被本节取代。

- `vidu_profile.py` 的 Q3 Pro I2V capability 支持 `native_audio_options=(False, True)`；`vidu.py::_payload()` 将该值写入请求 `audio`。S03 exact execution binding 选择了 false，因此当前无声是已提交路线的结果，不是模型不支持声音。开启声音需要新的生成请求，不能为旧 MP4 恢复不存在的音轨，也不保证保留当前表演。
- `elevenlabs.py::ElevenLabsVoiceProvider.preview()` 对当前测试工厂构造的 `language=zh`、陈立对白请求返回 timing_supported=true/output_supported=true，fake transport_calls=0。这只证明现有 adapter 没有相同语言阻断；不证明 live voice、凭证、额度或音质已就绪。
- 陈立 canonical artifact `production-s03-v1/creative/characters/jieshi-e01-character-P2-r1.yaml` 的 voice_profile 为 null。当前需要补齐具体配音素材/声音配置，不能把角色名称直接当可调用 voice_id。
- `generated_video_audio.py::_require_supported_target()` 只接受 Manifest 2.0–2.2；S03 当前为 2.7/revision11。现有原生音轨派生入口不能直接登记到这个目标，且 S03 source 本身无音轨。不能伪装普通音频导入或降级 Manifest 绕过。
- 历史本地 voice 脚本也存在：skyship voice-v4 使用 H3 T2VA 生成独立视听素材；5min rough-cut 使用 eSpeak。它们不是已经匹配陈立台词和音色的素材，旧实验脚本不自动成为当前 Production 入口。

本次仅完成已有路径核实，未修改代码、生成媒体或调用 Provider。保留当前 S03 画面时应优先明确并配置现有中文配音来源，之后通过既有 P4 合成和音画验收；不自动新增系统或重生画面。Learning evaluation 仍为 no_candidate。

## Current Result

用户在 S03 画面人审通过后询问声音并要求继续补音。本轮核对现有音频路径，尚未生成对白、环境声或带声 MP4；没有 Provider submit、Manifest mutation、代码修改、commit 或 push。

S03 source SHA-256 重新核对为 `d35624979e6dc6902c2e527bf5a99bcc47108de083f8e069de687e337c1a9268`。画面保留结论见 [S03 checkpoint](2026-09-11-s03-first-frame-preparation.md)；它不证明最终声音或口型通过。

## Verified Blocker

- `src/ai_video/production/minimax_speech.py::_request_is_supported()` 明确要求 `request.language == "English"`。使用现有 test factory 的 sealed request 和 fake transport 调用公开 `MiniMaxSpeechVoiceProvider.preview()`：English 的 timing/output_supported 均为 true；Chinese 和 zh 均为 false；transport_calls=0。该复现只证明本地 adapter 限制，不证明上游服务不支持中文，不构成真实 production preview。
- 当前《界蚀》制作目录未找到陈立的独立对白 WAV 或已配置的 voice profile。ElevenLabs adapter 存在，但本轮没有找到 S03 可直接消费的 production voice/credential-policy/budget 配置；未查询 secret 值，也未尝试替代 Provider。
- 历史 `drama-h3-t8-30s-preview-20260830-v45` 的 shot-03 对白为另一部短片的“你这次，会留下吗？”，不可当作陈立“什么？没报站啊。”的声音证据。
- P4 提供 canonical audio tracks/mixing，不能由此推断自动中文 dubbing/lip-sync 已就绪。既有 LatentSync checkout 的 Python 和主权重文件存在，本轮未运行模型、未验权重 hash、未证明 S03 侧脸/耳机动作上的 no-regression。

## Next Boundary

“以后 P4 补音”此前仅表达制作意图，未完成配音能力预检。当前最小后续范围是修正现有 MiniMax Speech 的中文 admission 并验证适用 voice、既有 policy/credential reference 和有限调用预算；不新增音频架构、不重生 S03 画面、不推进 S04。中文配音落盘后才可判断原口型是否可用，以及是否需要单独的口型修正实验。正式对白仍为“什么？没报站啊。”，时间窗 0.50–2.60s；最终环境声与音画质量仍 NOT_EVALUATED。

Agent Memory 返回 stale advisory fragments；本轮结论来自 current source 与上述 offline reproduction。自动 learning evaluation 为 `no_candidate`：没有新的独立媒体实验或可推广的质量证据。
