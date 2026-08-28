# Qingyan Seedance Mini Native-Audio Regeneration Gate Stop Record

Date: 2026-08-28

## Purpose

本文记录用户点名使用 `.agents/skills/seedance-authoring/SKILL.md` 重写脚本并再次生成后的 single-submit paid development experiment。目标是在不发送人物参考图的前提下，同时修正上次的苗族人物造型、腋下喷用与静音问题，并保留用户要求的因果顺序：可观察问题 -> 老人推荐 -> 交接 -> 少女喷用 -> 喷后效果。

本轮成功 fetch 一条 Seedance Mini 原生有声 MP4。苗服/银饰、双人交接与稳定镜头明显改善，但 required post-media Gate 仍有多项失败，因此该媒体没有进入 deterministic composition、generated-audio ingestion、candidate activation、P6、Final Acceptance 或 publication。

## Authoring And Runtime Selection

`seedance-authoring` 使用 exact Seedance `2.0 Mini` overlay，消费以下已选 runtime truth：

- Model: `doubao-seedance-2-0-mini-260615`
- Mode: `REFERENCE_TO_VIDEO`
- Surface: AI-VIDEO `SeedanceVideoProvider` through Volcengine Ark
- Output: `720p`, `9:16`, `15s`, `24fps`, `native_audio=true`
- Reference role: one `ordinary_non_character_image` product PNG；只传递瓶型与黄白配色，不传递背景、构图、人物、手部、服饰或场景
- Source audio route: `GENERATED + KEEP`；exact request 必须是 Seedance `generate_audio=true`

Authoring package、Shot Contract、prompt 和 Ecommerce input：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-002/authoring-package.md
runs/qingyan-seedance-mini-complete-ad-20260828-002/shot-contract.md
runs/qingyan-seedance-mini-complete-ad-20260828-002/prompt.txt
runs/qingyan-seedance-mini-complete-ad-20260828-002/ecommerce-input.json
```

Ecommerce input validator 返回 `status=valid`、`diagnostics=[]`。Prompt 经 linter 收敛到 `178 words`：

```text
Seedance Preflight — PASS
```

本轮没有预先伪造 `EcommerceAdProductionPackage`。`PHYSICAL_INTERACTION_REQUIRED` 必须等 exact media Gate；raw generated audio 即使通过，也仍缺少进入 `CompositionSpec -> ResolvedTimeline -> HyperFrames` 的 P4 ingestion capability。

## Paid Preflight And Provider Effects

Offline preflight 验证：

- `credential_present=true`，只通过 exact Secret Service reference `ARK_API_KEY` 注入；secret value 未写入 artifact、prompt、command argument、stdout、record 或 receipt
- `submit_posts=0`，preflight 无 network/Provider effect
- 外发 preview 只有 `1233`-byte prompt 与一张 `634379`-byte product-only PNG；没有人物 image/video reference
- `estimated_cost_upper_bound_cny=7.452`，finite ceiling `8 CNY`；该值是 pricing-derived runtime settlement，不是 Provider invoice 或已核实账单扣款

Live execution 使用 durable submit intent、one-use permit、唯一 committer 与 `VideoGenerationService`：

- Submit POST: `1`
- Query GET: `20`
- Download GET: `1`
- Retry / permit remint / Provider fallback / activation: `0 / 0 / 0 / 0`
- Audited payload: `generate_audio=true`

人物 reference egress 旧路径仍保持退役。一次 product-only submit 成功不证明 Ark 以后不会拒绝其他输入，也不授权恢复人物参考图外发。

## Exact Live Output

Raw fetched media：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-002/output/seedance-mini-native-audio-story-15s.mp4
SHA-256 5c893fe313ccd34de2f3a5148a680d9b91a11e1783c0f2a8ba9fd2e4960afdc1
11,487,915 bytes; 15.104s
H.264 High; 720x1280; 24fps; 361 frames
AAC LC; 32kHz; stereo; 129688bps
```

Sanitized request/audit、fetched identity 与完整 Gate：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-002/evidence/preflight-report.json
runs/qingyan-seedance-mini-complete-ad-20260828-002/evidence/live-report.json
runs/qingyan-seedance-mini-complete-ad-20260828-002/evidence/post-media-gate.md
```

该 MP4 是 local-only rejected development artifact，未 activation、未接入 v12/v13、未发布。

## Post-Media Gate

exact MP4 落盘并固定 SHA-256 后，立即调用 project-local `video-analysis` 的 `video_analyze`、`video_review`、`video_transcribe`、`video_extract_frames` 与 `video_scene_detect`。MCP 测得 `has_audio=true`、`20` 个 sampled frames、`unique_frame_ratio=1.0`；另以 `6fps` / `12fps` dense contact sheets 检查问题、推荐/交接与喷用/效果窗口。

关键 verdict：

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| `PROBLEM_HOOK_VISUAL` | `FAIL` | 开头有拉开臂口与不适表演，但衣物没有可观察的湿斑、变深或黏连；问题动作存在，问题本身不够可见。 |
| `PROBLEM_HOOK_AUDIO` | `NOT_EVALUATED` | 音轨在对白前已有连续可解码信号，但当前 MCP 不分类布料摩擦/呼气，本环境不能试听；不能用“有波形”冒充语义 PASS。 |
| `CHARACTER_STYLE` | `PASS` | 两人均为写实苗族造型，靛蓝刺绣服饰、银项圈/胸饰与老人银头饰跨镜头保留；没有动漫 fallback。 |
| `RECOMMENDATION_ORDER` | `FAIL` | 少女约 `5.25s–5.50s` 已开始伸手/共持，而三套 Whisper 都把对白放到约 `6.46s–6.60s`；推荐尚未说完就开始交接。三套转写还一致出现 `清眼眼` / `轻言言` / `轻延延`，没有得到 exact `青颜`。 |
| `HANDOFF_CAUSALITY` | `PASS` | 老人 sole holder -> 少女伸手 -> 短暂共持 -> 少女接稳 -> 老人空手释放，因果明确。 |
| `SPRAY_ORDER` | `FAIL` | 交接、开盖和抬臂顺序正确，但 `spray-burst-12fps.jpg` 显示喷嘴低于腋下，雾束水平穿过胸前/躯干，仍未直接喷到腋下。 |
| `RESULT_ORDER` | `FAIL` | 少女在首次可见雾束前已经出现放松微笑；更强的后续笑容不能修复“效果只在喷后出现”的 open-state 错误。 |
| `CAMERA_AND_TRANSITIONS` | `PASS` | 三个 clean hard cuts，有动机且稳定；无怪异推拉摇移、闪白、溶解、变形、freeze 或 static end card。 |
| `AUDIO_STREAM_PARITY` | `PASS` | exact request 为 `generate_audio=true`，MP4 有覆盖全片的 decodable AAC；mean `-21.5dB`、max `-1.1dB`。 |
| `AUDIO_SYNC_AND_BINDING` | `NOT_EVALUATED` | 老人是可见 speaker，但 precise lip sync、首秒 cloth/breath、cap click 和 spray sound 的语义与同步没有可审计证据。 |
| `NO_REPEATED_SLOGAN` | `PASS` | 只检测到一个 speech segment，没有结尾重复口号；该 segment 内品牌词的重复音节已在 exact dialogue Gate 失败，不改变本项对“是否重复口号”的判定。 |

Overall Gate 为 `FAIL`。完整 requirement-level evidence 以 run 内 `post-media-gate.md` 为准。

## Assessment

这次证明三个窄事实：

1. product-only Seedance Mini 可以生成稳定写实苗族双人广告造型，不需要动漫路线或人物 reference egress。
2. `generate_audio=true` 能在当前受控 adapter path 返回 AAC 原生有声 MP4。
3. 一个 15 秒单元可以改善推荐、交接、开盖、抬臂、喷雾、效果与动态收口的宏观覆盖。

但它仍不是用户要的完整广告。核心因果的细粒度时序、喷雾空间目标和品牌对白准确性都失败；配字、加片尾或直接 mux 只会掩盖 failure，不会修复它。Raw source-audio PASS 与 P4 final audio 仍是不同 proof layer。

## Remaining Risk And Next Work

本次 permit 已消费、预算已结算，任何新 Seedance submit 都需要新的 exact preview、finite ceiling、durable intent 与 one-use permit；不得 blind retry。

若未来继续实验，优先级应是：

1. 将“推荐完成”与“伸手交接”进一步分离，避免对白和动作并发；
2. 不再依赖宽松的自然语言 `underarm`，使用更强的空间构图或独立 source-generation strategy 证明喷嘴到腋下的几何关系；
3. 原生广告对白需要 human audition 与 exact transcript Gate；品牌词无法稳定时，应把对话与画面生成拆成可审计路线，而不是接受近音字或重复音节；
4. 当前 P4 仍不能 ingest embedded generated audio，最终 composition 继续是 `REQUIRES_RUNTIME_CAPABILITY`。

这些都是后续候选方向，不构成新的 Provider、P4 slice 或实现授权。

## Agent Guardrails

- `Ark task succeeded`、`AAC exists`、`CHARACTER_STYLE=PASS` 都不能覆盖 `SPRAY_ORDER=FAIL` 或 exact dialogue failure。
- 不得把该 raw MP4 标为完整广告、accepted candidate、P6、Final Acceptance、published 或广告效果 evidence。
- 不得自动重提、扩预算、切换 Provider、恢复人物 reference egress、fallback 到动漫、direct mux 原生音轨或移除 HyperFrames source `muted`。
- Product-only route 只证明本次 exact product asset 与 prompt 的 bounded egress；不证明服务端 classifier 永不拒绝。
- Human normal-speed sound/visual verdict、P4 final composition、P6、Final Acceptance 与 publication 均未完成。
