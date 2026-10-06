---
record_kind: session_summary
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Fanxiang Formal Edit And Impact Sound Record

Date: 2026-10-06

## Current Status

停止生成后，复用 B-03、Ba-02、attack、recoil 原始 bytes，通过既有 SourceUseEvidence /
CompositionSpec / ResolvedTimeline / P4 / HyperFrames / ProductionStateCommitter 完成正式剪辑与 render activation。
当前剪辑项目为 `runs/fanxiang-formal-edit-20261006-001/production-v5/`；
原 generation 项目、raw 历史与旧 recoil QA 未回写。

正式输出 `runs/fanxiang-formal-edit-20261006-001/fanxiang-defense-final.mp4`：
1344×768，24fps，300 frames，video/audio stream 各 12.500s，container 12.522s（AAC 尾包）。
6,104,860 bytes，SHA-256
`af37152c6acce2feaa9c64bb44d957d22e8cf7bb352397d384c3049a23f69c61`。
这是当前独立 editorial 项目真实激活的 render 输出；不证明原 raw generation 的 activation、
P6 或 human Final Acceptance。MP4 与 run receipts 为本机 ignored artifacts，没有上传媒体。

视觉剪辑判定 PASS；实际 1× 非静音播放完成，0 dropped frames。
当前模型不支持音频听辨，主观听感与完整 human Final Acceptance 仍为 NOT_EVALUATED。
画面可作为下一剧情单元的基线；完整声画放行仍需人工听音，本次未提交下一 Shot。

## Selected Windows

所有范围为 24fps、半开区间，保持自然速度；没有补帧、重复末帧、变速或保留未选垃圾段。

| Order | Source | Source Frames | Source Seconds | Used Duration | Final Seconds |
| --- | --- | --- | --- | --- | --- |
| 1 | B-03-final | [0,211) | 0–8.791667 | 8.791667s | 0–8.791667 |
| 2 | Ba-02 | [221,240) | 9.208333–10.000000 | 0.791667s | 8.791667–9.583333 |
| 3 | attack-take-01 | [9,35) | 0.375000–1.458333 | 1.083333s | 9.583333–10.666667 |
| 4 | recoil-take-01 | [77,107) | 3.208333–4.458333 | 1.250000s | 10.666667–11.916667 |
| 5 | B-03-final empty window | [348,362) | 14.500000–15.083333 | 0.583333s | 11.916667–12.500000 |

Source prefix：`runs/fanxiang-production-loop-20261005-001/`；
对应子目录为 `sequence-B-take-03-final`、`sequence-Ba-take-02`、
`sequence-B-attack-insert-take-01`、`sequence-B-recoil-insert-take-01`，文件均为 `output.mp4`。

原 attack/recoil 各 107frames/4.458333s 超过 nominal 请求4s的 output-contract failure 继续保留。
旧 recoil 误绑 attack rubric 的 NOT_EVALUATED 也继续保留。
当前用途另建 exact source-byte / parent-Shot / 窗口 / transform 绑定的 SourceUseEvidence，
使用 analyzer authority，五个窗口通过 assess_source_use；不伪造 human proof。

## Editing And Sound Decisions

主干止于破窗近景，排除后续伸颈动作：先播放那段再接 Ba-02 会重复接近状态。
还去掉主干切点前仅两帧的宽景，避免闪切。使用硬切：
破窗威胁→室内三人准备→键盘击中→下偏受击→连续撤回→空窗。
攻击与反应短窗保持用户已确认的原窗口，末尾空窗多用两个真实原生帧。

recoil 源画幅为1440×736，其他源与 delivery 为1344×768。
新增唯一必要产品接缝 `FixedTransform.video_fit=cover`，显式固定居中填满裁切；
当前 recoil 用途证据绑定该 transform。默认 `exact` 继续拒绝画幅不符，保留旧序列化/hash，
旧全幅证据不能资格化新裁切。没有修改 continuity、Router 或 Provider。

撞击 SFX 使用已安装 video-shotcraft 的 `hit-blow.mp3`（Impact of a blow），
现有 attribution 指向 Mixkit SFX 2150，使用 Mixkit Sound Effects Free License；
没有网络下载或新生成声音。转换为48kHz stereo PCM仅作输入准备，最终 placement/mix 仍归 P4。
SFX取0.5s，gain -1dB，尾部0.1s fade-out。
其文件前导到10%峰值为5681samples/118.354ms，因此track开始于502319samples/10.464979s，
重击对齐全片 frame254/10.583333s；接 recoil 在frame256/10.666667s。
最终 AAC 解码波形匹配落点比 authored transient 晚1024samples/21.333ms，小于一帧；
这是可执行同步证据，不是耳听判定。

保留 B-03 的3s以后原生声（含破窗声），gain -3dB；
开头原生scratch转写有疑似多余词句，排除前三秒，改用原 B-03 空窗14.5–15.0s环境底。
反击段也使用该环境底桥接：0.5s片段每0.45s交叠，gain -9dB、50ms交叉淡入淡出。
attack/recoil 的 raw audio 不直接使用；无新增 BGM、字幕或旁白。

## Verification And Evidence

Evidence prefix `R = runs/fanxiang-formal-edit-20261006-001/`。

| Evidence | Actual Result | Boundary |
| --- | --- | --- |
| `R/raw-preservation-check.json` | 四条原 MP4 SHA/size 与原 terminal 一致 | 不重写 raw bytes |
| `R/*-source-admission.json` | exact ffprobe/count_frames、原 terminal、bytes | imported existing-source admission，不是 generation activation |
| `R/source-use-assessments.json` | 五个当前用途 PASS | 仅当前窗口与固定 transform |
| `R/composition.json`、`R/timeline.json`、`R/render-state.json` | canonical render、activation、strict reader reopen 成功 | 当前 editorial 项目，不是旧 raw 的 qualification |
| `R/final-probe.json` | H264/AAC、300frames、48k stereo、12.5s | 技术媒体属性 |
| `R/final-playback-1x-v5.json`、`R/final-playback-summary-v5.json` | ended=true、rate=1、muted=false、300frames、0掉帧、约12.677s wall；waiting仅加载起点0s | 真实播放执行，不替代耳听 |
| `R/final-explicit-mcp-review-v5.json` | 显式 project-local video-analysis MCP 返回当前 exact MP4 review | 指标不裁决语义；speaking estimate不稳定，不作无人声证明 |
| `R/final-audio-sync.json` | waveform sync误差21.333ms，低于一帧 | 主观听感 NOT_EVALUATED |
| `R/playback-counter-final.jpg`、`R/final-adjudication.json` | 可读因果/轴线、无重复状态、采样未见字幕水印 PASS | Parent画面判定，无 human Final Acceptance |

focused composition/source-use/planning/HyperFrames tests：312 passed、3 skipped；
最终 source-use transform 防回归 checkpoint：100 passed。
Exact code Harness receipt：
`.agent/harness/runs/fanxiang-explicit-video-cover-20261006/receipt.json`。
13/13 checks PASS；verify-receipt确认fresh/snapshot/scope/policy/artifact integrity及workspace stable。
代码checkpoint：`ead7967`；仅上述最小产品接缝、相关测试与contract matrix，未夹带其他工作。
Documentation-only checkpoint receipt：
`.agent/harness/runs/fanxiang-formal-edit-record-20261006/receipt.json`；
其结果由最终交付列出，记录内容本身不宣称已运行尚未完成的文档检查。

保留此前失败/淘汰的 editorial versions：初版音频 mux末端短32samples，保持失败 Gate；
v2 的14.5s组合存在重复接近；v3 的12.625s组合有切点短宽景残留；
v4 清理后音效仍需前导补偿；v5为当前输出。全部属于同一修复链，未重置 Provider预算或生成历史。

受管 Kimi deep 只读 mapping：第一次 upstream502导致 STRUCTURED_OUTPUT_EXHAUSTED，未采纳结果；
有限缩小scope后的 `9c1ef4cc-1378-4a9c-82ed-e0a09c9fb367` PARSED。
`R/kimi-run-retry.json`、`R/kimi-report.json`、`R/kimi-parent-adjudication.json` 保留route和Parent裁决。
Mapping确认现有 SourceUse/Registry边界；所有关键 claims仍由当前源码/测试/真实render核实。
Kimi并非最终媒体验收或 implementation adversarial reviewer。

## Production Experience

**复杂接触动作单镜失败 → 拆成攻击插镜 + 结果反应镜 → 选短窗 → 剪辑建立因果。**

本次可复用的制作方法：只要求攻击插镜给出清晰接触，只要求反应镜给出结果与连续撤退，
用短自然窗口和同步撞击声建立因果；不要要求一条raw完整覆盖所有复杂接触、受力和撤离。
整体剪辑还必须排除重复状态、反应前姿态跳变及无用尾部。

这是本次场景的经验，不是已验证的跨模型通用规则。
自动 learning evaluation 为 `no_candidate`：当前正式编辑版本属于同一素材/剧情修复链，
没有形成隔离变量的 controlled comparison 或足够独立重复支持。
不创建 placeholder claim，不修改 Skill/Policy/Gate，不标 ADOPTED。

## Manual Work And Remaining Risks

选窗、切点、节奏、SFX选型/增益/同步位置、画面裁决，仍由 Codex Parent手工做创作决定；
task script只是调用已有产品owners，不是自动化 Director、自动最优剪辑或新runtime pipeline。
Timeline resolving、P4混音、HyperFrames导出与render activation 使用既有canonical owners。

必须人工正常速度听最终MP4，确认撞击音色/响度、环境循环是否可感、有没有多余人声，
并做整体剧情的 human Final Acceptance；本环境无法代签。
视频分析转写对非对白底噪给出不稳定估计，不能用转写或无issues证明听感。
本次没有提交下一剧情 Shot，没有新的 image/video/voice/SFX generation 或 Provider media POST。
Kimi mapping 属于独立受管推理调用，不是媒体生成。

AOCI维护探测因现有10个managed paths认知待对齐而停止，未扩展任务修改无关认知；
不宣称索引已全面对齐。RAG只用于advisory发现，不作为本次验收来源；
记录后没有额外重建全局RAG。所有local evidence需与MP4共同保留，单独Git记录不携带媒体bytes。
