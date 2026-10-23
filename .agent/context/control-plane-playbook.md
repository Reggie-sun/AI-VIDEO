# AI-VIDEO Control-Plane Playbook

按 concern 读取的 advisory reference；不拥有 Product state/Provider/验收。规则检查已迁入
[agent-rules.yaml](../harness/agent-rules.yaml)，argv 与 changed-path routing 只由 policy 独占。

## Task Context Loading

源码/tests/runtime 是事实；matrix 确定 surface owner，policy 确定 checks，baseline/roadmap 分别维护当前状态/方向。
只读匹配 Skill/active spec/plan；T8/LatentSync 主机操作另读 [runtime](t8-latentsync-local-runtime.md)。
不整目录加载，不把 history/handoff/`.workflow/` 当作当前事实。

## 1. Creative Skill Routing And Preflight

### Creative Completion

新创作、实质重剪及字幕/图形/配乐设计，执行前与交付前使用 `open-video` 的
[Creative Completion Practice](../../.agents/skills/open-video/references/creative-completion.md)。
保持完整目标、exact 成片独立观看与有界修复；忠实复刻不等于创作性重剪，纯复制已验收 bytes 沿原交付路径核验。

### Final-output-first Repair Preflight

用户成片目标 → Final-output / No-regression → Shot 完整要求 → 局部指标。固定 original bytes、完整目标和
baseline review，拒绝已知违规方案（含 preview），新片重做全部适用 proof；技术 PASS/成本不豁免。
Runtime seam 见 [matrix](../../docs/agent-primary-contract-matrix.md#final-output-first--no-regression)。
任意 Agent shell/media 操作仍须遵从；Python Gate 不拦截所有 shell。

### Agent-Side Image Generation Provider Preference

作图/修图默认优先 Codex Generated Image（`image_gen.imagegen`），读取 `imagegen`。
参考/QA/import见[工作流](../../docs/canvas-production-harness.md#agent-image-authoring-workflow)；先有界试图，验后由唯一 committer接入。
其他已授权入口须显式选择；timeout/unknown停止，不自动fallback/retry，不假称节点执行或完整剧情PASS。
保留原图/evidence；不保存session/browser/signed URL/private diagnostics，不把工具output dir当artifact root。

### Creative Skill Preflight Gate

创作前读匹配Skill并声明；live/paid preview/permit/POST前报告semantic open/close state、continuity、
actual reference/terminal handoff、axis/action/camera endpoint、prompt适配/lint；缺失停止。
逐镜验[白模](../../docs/canvas-production-harness.md#per-shot-whitebox-reference)及连续镜preflight；纯state/assets/schema/dependency/execution不触发创作。

#### Raw Creative Input Director Strategy Gate

请求分来源保留、新创作/已授权优化（design）、已知失败 repair；边界归 [`open-video` Step 1](../../.agents/skills/open-video/SKILL.md)。
原文/reference保语义，适配附diff；缺artifact不优化、不编造证据；repair保全目标/已满足项，实质改写沿human gate。
画风/参考用[当前稿](../../docs/canvas-production-harness.md#current-inputs)，禁历史追加。
仅 design 的未批准 raw input 作为 `DIRECTOR_PREFLIGHT_REQUEST` 入 `open-video`。
prompt presence、时长阈值、`VIDEO_EXTEND` 不代替 design 判断；封存 verbatim inventory。
核对 raw→inventory→coverage，执行 [validator](../../.agents/skills/open-video/scripts/validate_director_coverage.py)，FAIL 停止；选 single_take/multi_shot，保留 rationale/user evidence。
Provider capability 归 current profile；结构 PASS 不证明语义/质量。内部字段不机械拼入 native prompt；canonical/paid/media gates 不变。

### Skill Selection

依赖顺序：memory（命中 trigger 时）→ ecommerce/Director → semantic continuity → selected Provider authoring
→ deterministic composition。只用 matching concerns，实际读取各 Skill；schema/操作/限制不在此复制。连续画布先读[制作方法](../../docs/canvas-continuous-production.md)，默认480p。

- `ecommerce-ad-workflow`：仅 ecommerce/SKU/product advertising；不接管 AI comic/drama。
- `ad-creative`：广告创意策略、Hook、形式、文案与受控变体的 advisory 专项；先消费已核实商品事实，建议回到现有 ecommerce authoring owner，不处理投放账号或执行。剧情广告仍归广告语义，可按需借用下方 craft。
- `drama-authoring`：剧情/分集/剧本与人物场景道具制作设定；遵 accepted Drama contract，输出同一 Story/Scene/Character/Shot 语义与 Director 交接，不签媒体验收。
- `open-video`：concept/script/raw input/ordered coverage；不安装运行外部 engine 或生成/judge/stitch。
  需要细化调度、表演或动作时按需读其 `references/professional-specialists.md`，不为五库齐用而重复编剧/分镜；2.5 专项仍只由 selected Seedance 2.5 overlay 加载。
- `hell-grind-aigc-skill`：semantic Shot/state/continuity、prompt、diagnosis；不建立第二 schema/ledger。
- `h3-video`：approved Shot + requirement + selected MiniMax H3；不选择 Provider/改 intent/运行上游 runtime。
- `seedance-authoring` MUST use：approved Shot + requirement + selected Seedance，先 shared knowledge 再一个 exact
  version overlay；unknown/mixed selection 停止。semantic intent -> seedance-authoring: prompt/reference expression。
- Non-Seedance guidance 用 `higgsfield`；deterministic motion/graphics/pacing 用 `video-shotcraft`。
- `higgsfield-seedance`、`higgsfield-seedance-2-5`、`higgsfield-seedance-vfx` 与 `higgsfield-troubleshoot` 的
  Seedance branch 已 retired，MUST NOT direct-dispatch；仅 selected seedance-authoring 后可读取 advisory excerpt。

所有 External Skills 只作 advisory，不选 active Provider/renderer，不读 credential、不运行 engine/submit/fetch/retry、
不写 Project/Registry/Manifest/P6/receipt、不给 Final Acceptance、不重算 `ResolvedTimeline`；runtime_skill_calls=0。
Capability/model/profile/settings claims 重新核对 selected adapter、sealed profile、tests 与当前 runtime。

## 2. Module Boundaries And Focused Owners

只读取 [contract matrix](../../docs/agent-primary-contract-matrix.md) 与源码；这里不复制 surface catalog。

## 3. Provider Credential And Paid Execution Details

只经 injected supplier 的 exact Secret Service lookup；key 不回显、不持久化。失败/locked/rotated 停止，
不搜 repo/history 或替代 source。以下是 reference metadata，不能证明 access、余额或 authorization：

| Provider | Reference | Exact attributes（另含 `application ai-video`） |
| --- | --- | --- |
| Seedance | `ARK_API_KEY` | `provider seedance`、`credential ARK_API_KEY` |
| Vidu | `VIDU_API_KEY` | `provider vidu`、`credential VIDU_API_KEY` |
| MiniMax Speech | `MINIMAX_SPEECH_API_KEY` | `provider minimax-speech`、同名 credential |
| MiniMax Speech CN | `MINIMAX_SPEECH_CN_API_KEY` | `provider minimax-speech`、同名 credential；仅 `https://api.minimaxi.com` |

不使用 `SEEDANCE_API_KEY` 或跨 Provider fallback；CN 不复制旧引用。细节见
[Vidu](../../docs/vidu-provider.md)、[Speech](../../docs/minimax-speech.md)。
Paid scope/count 与 local exemption 只由 `AGENTS.md` 决定；每 submit 保留 remaining count、exact preview、
reservation、egress、durable intent、one-use permit。Local video 仍经 `VideoGenerationService`，禁止裸 transport/submit。
现有 paid owner 已在 durability/consume/POST 前重验 actual clock；KNOWN_NO_EFFECT 与 unknown 不混淆、不复用 permit。

### Operator Ceiling Renewal

仅 current Vidu 内部定额 upper bound 可在用户授权新 attempt、known outcome 且剩余 quota>0 时续期。
不可推用于 Seedance 市场报价。创建新 immutable profile，保留旧上限/币种/配置/总预算/count，真实决定时间，
最短可行有效期且最多六小时；留 old/new hash、授权、scope、remaining count 和 reaffirmation evidence。
旧 profile 不覆盖，不用于旧 submit fetch/recovery；重走 readiness/router/compiler/preview/budget/new intent/permit。
续期不是官方报价，不增额度、不重置消费，不重试 unknown。同 scope 的有限预算扩展按 constitution 记录 predecessor。

## 4. Verification, Pilot And Delivery Details

按 `AGENTS.md` 选择最小充分验证，记录对象、命令、结果与限制；不为 receipt 扩跑整组。
完整验证：`make harness-inspect` → exact staged snapshot 或 commit range 的 `make harness-verify` / `make harness-verify-range` → `make harness-receipt`，核验 scope/policy/artifact hashes/freshness。
耗时不相称时重评、停止冗余检查，保留中断/未验证项；仅新改动/失败/未决风险使证据失效时补验，不因提交/记录重跑。Harness routing、coverage、unknown-path fallback及receipt验真保持；局部通过不得冒充完整PASS，运行中snapshot drift/读取失败停余项。
`agent_rules_check` 验 references/links/budgets；`agent_rule_invariants` 与原 suites 验迁移 invariant。
Harness 不生成媒体或读 secret；CI 自产证据；remote enforcement 必须当前 server evidence。
真实批量媒体前先完成约 30–60 秒、4–8 连续 Shots 的代表性 Pilot，包含任务主要 media/audio/captions/composition，
人实际观看给 GO/NO-GO；NO-GO 不扩量。Reference asset 不自动成为 Final Shot Visual，跨非连续 Shot 复用须导演理由和人工 review。

### Empirical Uncertainty Triage

区分 deterministic 与 model-quality uncertainty；后者主导且有安全、有界、已授权或 local exemption、可负担、
可归因的最小实验时先取证。先核对 exact inputs、remaining budget、outcome、identity/seam、GPU/依赖和归因设计。
缺 prerequisite 先完成最小补齐；用户明确先做 contract 则遵从。纯确定性任务不生成媒体。
记录 triage 时说明 `next_empirical_question`、`cheapest_valid_experiment` 与 `blocking_prerequisite`。
实验隔离于 active truth，PASS/FAIL 不授权 qualification、activation、P6/acceptance，不改变 frozen rubric。
制作前先绑定用户原 source、目标片段与声画 AC；自编技术样例仅证明其测试对象，不能替代原剧本验收。能力已满足时直接制作，只有当前输入或 runtime 证据证明缺口才修改共享工程。

### HyperFrames Caption Source Readiness

升级 pinned renderer 前重新打开 exact bundled/generic font tables并同步 same-name preflight；alias、OS fallback、
`@font-face local()` 或 disabled lint 不放行。必须运行 `tests/test_production_hyperframes.py` 的
`test_p4_source_rejects_caption_font_outside_pinned_renderer_contract` 与
`test_p4_production_renderer_gate_renders_resolved_audio_and_captions`，后者需 actual pinned binary/browser 与 exact
Production source lint/render。离线结构断言不等于 actual render/glyph coverage，不改变 timeline/committer/caption/P6 owner。

## 5. Repository-Specific Don't Repeat This

resume、atomic state、path containment、standard loader、precise invalidation、canonical P4 audio/timeline 的
确定性行为由 migrated tests 与原 policy suites 验证。真实 incident 放 `.agent/bug-memory/`；不放假想风险或操作手册。
Generated-video delivery 只报告真实 fetched/validated bytes及实际 lifecycle，fake/smoke/preflight 不冒充质量或 activation。

### Generic Video Context Tool Selection

普通 overview 选实际注册名 `video-mcp` 的 `process_video`；exact-media/QA/Gate 选 project-local `video-analysis`。
Host install `/home/reggie/vscode_folder/MCP/VideoMCP`，executable `/home/reggie/.local/share/video-mcp/venv/bin/video-mcp`；
启动 cwd 固定 install dir 避免 repo `.env`，使用前核对当前配置。带音轨会自动 Whisper，只在本地模型已可用且允许转写时用；
否则用支持 `transcribe_audio=false` 的原服务。不要下载模型/上传/fallback。
外部缓存不是 exact bytes freshness，`max_frames` 不为硬 ceiling；核验图片可解码、数量/时间戳与 error/placeholder，
`isError=false` 不保证 usable evidence。结果仅 advisory，不转换为 QA/GenerationAnalysis/P6 receipt。

### Per-Shot Post-Media Gate

顺序：resolve SourceAudioPolicy + selected capability → exact request → generate once → fixed MP4 SHA-256 →
显式video-analysis验scene/lip-sync/continuity及声音（[audio_understand](../../docs/audio-understanding.md)）；逐项PASS才下一Shot。
Gate input：shot_id/path/hash/intent/rubric/required IDs/Shot2+前序 accepted end-state；output 每 requirement 的
PASS/FAIL/NOT_EVALUATED + evidence ref + reason，不用 score 或 advisory hook 代替。FAIL / NOT_EVALUATED 时 STOP。

- GENERATED + KEEP/TRIM_THEN_MIX：request `native_audio=true`，Seedance `generate_audio=true`；不支持即 submit 前停，
  不静音/换 Provider。Exact MP4 检查 decoded audio、audibility、sync、对白/推荐语义、speaker/lip-sync、重复词/意外静音。
- MUTE/REPLACE：source 不计 final coverage，明确 P4 dialogue/VO/BGM/SFX/ambience requirements；raw Shot 只验声明，
  render 后才证明实际静音/替换。NONE 仅 empty MUTE；NATIVE KEEP/TRIM 绑定 existing audio，不能偷换成新生成音轨。
- Raw audio PASS 不证明进入成片；KEEP/TRIM exact asset 仍经 CompositionSpec → ResolvedTimeline → HyperFrames。
  缺 seam 报 REQUIRES_RUNTIME_CAPABILITY 并停 final delivery，不倒改已关闭 raw barrier，不 direct mux/移除 muted。
- 只有 required findings 全 PASS 推进；MCP/error/missing/stale/identity drift 无法判断均 NOT_EVALUATED。
- 失败后持久化 current-attempt STOP，绝不允许提交下一 Shot；local loopback + outcome-known + unmet scope 执行
  LOCAL_BOUNDED_REPAIR_LOOP，先封存有限的 task-scoped attempt count、elapsed-time 与 GPU budget，每次诊断一个可归因变量。
  建 new exact identity / intent / one-use permit，保留 durable intent，只重做 same Shot 并完整重验，禁复用/重铸旧 permit。
- evidence-only NOT_EVALUATED 先 EVIDENCE_REPAIR_FIRST；无 media failure 不重生成。预算耗尽先核对 outcome/计数，
  有据扩展有限单元但不无限执行；无新变量/同类不可隔离/evidence持续失败/scope或paid状态变化报告 blocker。
  新 exact identity 不授权扩大 Provider/egress；Remote / paid retry 保留全部授权/Gates，unknown 立即停止。
- MCP raw evidence/Agent verdict 不写 Manifest/Registry/activation/P6/Final Acceptance，Production 必须另经 existing review/committer。

Final-composition audio Gate 在 P4 render 后独立检查 exact trim/mix、MUTE/REPLACE 无泄漏及 replacement coverage、
intentional silence；只决定 final-media 是否可进入 P6，不提交下一 Shot或重复 Provider generation。

## 6. Agent Experience Memory Routing

检索 scope、fresh/stale、exit code、derived-index queue 与 no-network 行为只由
[retrieve-ai-video-memory](../../.agents/skills/retrieve-ai-video-memory/SKILL.md) 维护。
结果保留 authority；不降低 admission、不重复查询、不前台 rebuild、不下载/假 embedding/fallback，不接入 Product state。

### Experience Learning And Confirmation

[distill-ai-video-learning](../../.agents/skills/distill-ai-video-learning/SKILL.md) 独占 Learning Claim/admission/
confirmation/adoption；[record-ai-video-session](../../.agents/skills/record-ai-video-session/SKILL.md) 独占 record/ACK。
两者仅 Development Governance，不复制字段/阈值，不放宽 advisory_learning authority。

## 7. Durable Session Record Gate

按 record Skill 主动评估 stable substantial checkpoint，含 repo 外 effects，无 hook 不免除；record 后 automatic
learning evaluation。Trivial/unfinished 明确 no_record；无合格学习 evidence 为 no_candidate，不制造批准步骤。

## Agent Workflow Operations

### Workflow Selection
Native Codex 默认 primary；settled bounded task 直接实施与 focused verification，不因 documentation、configuration、Harness 或多文件强制 full workflow。重大未决 architecture/contract 才先设计，必要时 research；authorized written spec 自动使用 `superpowers:writing-plans`。Spec/Plan 默认 Parent self-review；paid/credential/recovery/QA 的严格 gates 保留，review 按下文 Risk Gate，不自动双审。

### Cognition Tools
结构关系使用 CodeGraph；职责/语义确有缺口才加 AOCI，简单局部任务禁止机械调用。源码/LSP/tests/runtime 与 canonical contracts 是事实，AOCI 永远 advisory；不符时修正索引，不能覆盖源码。正式认知归 `aoci.txt`、`aoci.meta.txt`、`aoci.code.txt`，语义由模型基于当前 source/contract evidence 编写；状态、维护顺序和安全停点遵从项目 MCP 的 `aoci_rules`、实时 Guide、工具返回及官方文档。稳定后按官方流程维护，不把未对齐索引称为完整认知。

### Constructing An Immutable Review Target

使用 exact commit/tree 或 staged tree hash，绑定 diff、source byte hashes、spec/plan 和验证结果。
仅 staged 清单+时间不能证明 immutable bytes；原生 reviewer 绑定 exact target，read-only，不 nested delegation。

### Implementation Review
以相关局部验证为前提，按 `/home/reggie/.codex/SUBAGENTS.md` 的低频 Risk Gate 判断；需要的最终 Harness 留到候选稳定后。
T3、Spec/Plan 存在、diff 大小或 agent 可用都不自动触发；未触发由 Codex Parent 正常完成。
触发时只增加一名 native adversarial read-only reviewer，Parent 是 orchestrator/fixer/adjudicator；
不叠加 Kimi 或第二 reviewer。最低充分 package 绑定 exact snapshot、适用 Spec/Plan、AC 与 verification。
Native profile/权限/执行证据按 SUBAGENTS.md 核验，不伪造 external/Docker 资格；PARSED/exit0/LGTM 不代替验收，不探测/重试 Kimi。

### Adjudication

Native review → Parent 调查/裁决 → confirmed blocker 修复 → 受影响局部验证 → 必要 native re-review。
Parent 用 source、contracts、tests/Harness 和 runtime evidence 关闭 findings，不投票或为争取共识反复调用。
Semantic fix 绑定新 target；isolated boundary 用 targeted re-review，广域语义变更用 full re-review。
有限轮次、升级与接手由 SUBAGENTS.md 独占；旧 findings/失败与轮次保留，不得自动第四轮或叠加 reviewer。
没有 unresolved blocker 才具 completion eligibility，Parent 拥有最终决定；不得降低 AC 以消除 findings。
旧 Spec/Plan 的双审默认已失效；保留历史，不冒称新 snapshot 已审。
