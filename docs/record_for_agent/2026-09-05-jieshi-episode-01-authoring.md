---
record_kind: session_summary
topic_id: jieshi-episode-01-authoring
learning_eligibility: ineligible
---

# Jieshi Episode 01 Authoring

## Current Generation Checkpoint — 2026-09-05

本节取代下方历史的“没有 MP4 / submit 为 0 / Ark 入库是唯一下一步”状态。
用户要求先解决 Seedance，随后允许 2.5 修复及 Vidu q3-pro 配合；并非要求真人素材。
实际选择先用 Seedance 2.0 T2V 生成原创虚构人物，经现有 canonical workflow 完成一次
submit、poll、fetch，无图片上传，无 Ark 人像入库，无 gate 放宽。
这证明本次 T2V 通路可用，不证明旧 I2V inline reference 路径已解除限制。

生产准备脚本位于 `runs/jieshi-e01-seedance20-20260905-001/`：
`prepare_first_shot.py`、`prepare_request.py`、`live_first_shot.py`。
复用 `ProductionStateCommitter`、真实 `ProductionProject`、`VideoPlanner`、
readiness、Shot Router、Seedance compiler/resolver、`VideoGenerationService`；
没有 fixture、直接 HTTP submit 或第二个 state writer。首镜 project 为
`production-s01-v1`，其余 Episode authoring 保留，尚未制作完整 300 秒。

首轮模型 `doubao-seedance-2-0-260128`，attempt
`jieshi-e01-s01-seedance20-t2v-attempt-v1`，resolved hash
`4cd2d90868975d3e362b5f06cdad31f3b83cc3c2e996fa4e224e6807d0b67817`。
实际 MP4：
`runs/jieshi-e01-seedance20-20260905-001/production-s01-v1/state/video-generation/fetch/files/537bc0ef25630d1b07364501482ca67baca27772331d6eaf3c1788a34f05729e.mp4`。
SHA-256 与文件名一致，1931391 bytes，1080×1920，H.264 High，24 fps，
97 frames / 4042 ms，无音轨。返回 `usage.completion_tokens=196425`，
按 51 micro-CNY/token 实际结算 `10017675` micro-CNY，约 10.02 CNY。
原 15 CNY ledger 剩余 `4982325` micro-CNY，不得将其当成新 15 元额度。

## First Shot Gate — FAIL

已显式调用 project-local `video-analysis.video_analyze` 对 exact MP4 分析，
每 0.5 秒抽帧，共检查 9 帧；原始证据保存在该 run 的
`preparation/shot-01-video-analysis.json`，逐项判据在
`preparation/shot-01-post-media-gate.json`。

- Visual FAIL：林砚背部、手机和抬起的手仍出现在倒影里，开场核心异常不成立；
  七名他人倒影和女孩远处位置也没有满足源分镜。
- Technical FAIL：旧请求为 `exact_seconds=4`，要求 96 frames / 4000 ms，
  实测 97 frames / 4042 ms；未通过改写请求或裁切原始证据将其改判 PASS。
- 非血腥虚构画面判据 PASS，但不能抵消上述失败。

素材状态 `fetched_unactivated`；没有 candidate activation、下一 Shot submit、
P6、Final Acceptance 或 human acceptance。广播与硬字幕仍需既有 P4 合成。

## Seedance 2.5 Repair And Budget Boundary

用户授权在 2.0 效果不好时选 2.5。候选为 `doubao-seedance-2-5-260628` T2V，
1080p；现有 `provider_selected` timing 可保留真实源帧数，源长度由模型选择
4–30 秒，成片 S01 仍为 3 秒。不能声称确定返回 4 秒或复用旧请求/permit。
此方案未修改 Product 的 timing contract，也未新增 nominal_seconds capability。

可审查的 typed request、Planner proposed 结果、exact capability、输出要求、
提示草稿和费用计算位于该 run 的 `preparation/seedance25-repair-v1/`。
request hash：`69f44bd3a96a2fc5adb6e215978d912d6a0c88105181462c66722dcc7c19c2ac`。
预算保持 `budget_authorized=false`，仅完成静态能力检查，未形成可执行的 paid preview。
新增一次修复建议上限 85 CNY；这是为最长源长度预留，实际依返回用量结算。
原支出加新增上限为 95.017675 CNY；追加预算尚未获明确确认。
`paid_provider.reserve_paid_provider_budget` 要求原 ledger ceiling/policy 恒等，
没有向上调整 API；不得为躲避原额度另建项目。预算获批后仍需明确新 scope、
canonical graph/Router/compiled request、fresh exact preview、intent、permit 和全量媒体重验。

官方事实已从当前公开页面核对：
[虚拟人像库](https://docs.volcengine.com/docs/82379/2223965?lang=zh) 说明本账号
Seedance 生成的视频可作为受信素材；本次尚未实际验证后续 edit/extend 接受情况。
[模型价格](https://docs.volcengine.com/docs/82379/1544106?lang=zh) 在当前日期给出
2.5 1080p 无输入视频单价 77 CNY/百万 token，活动价 72 折，即 55.44。
按 30 秒加一帧裕量估算 80.943786 CNY，取 85 元上限。授权后需重新核对时效。

## Execution Verification Boundary

Focused tests：`tests/test_production_seedance.py` 与
`tests/test_production_video_pre_generation.py` 共 132 passed。
native `reviewer_xhigh` 对单次 T2V 执行路径结论为 accept with concerns；
其非 JSON HTTP 错误审计包装问题已修正并离线验证，未追加 paid call。

Harness `.agent/harness/runs/jieshi-e01-seedance-t2v-execution-20260905/receipt.json`
为 FAILED，不能作为验收凭据：全量测试 4316 passed、2 failed、4 skipped；
两处为 `tests/test_mcp_transcribe.py` 依赖的 `whisper` 在 `.venv` 中缺失，
已由 parent 与只读 code_mapper 用 import-spec check 核实，未安装依赖或修改无关代码。
另有验证期间 HEAD 变化，虽三份任务脚本的 cached patch hash 未变，receipt 仍不稳定。
当前三份脚本保持 staged，尚无 fresh passing Harness receipt，代码提交/完成验收受阻。
本记录仅 checkpoint 当前事实，不将这次真实生成等同于脚本全量验证通过。

`record-ai-video-session` 更新同一记录，`distill-ai-video-learning` 评估为
`no_candidate`：一次失败视频的不同证据层不是多个独立实验。
新的 focused experience RAG 查询返回 `[]`，伴随 stale shard 异步刷新提示；
未以此推断无历史问题，未前台重建。未 push/release，未修改其他 writer 的文件。

## Historical Generation Preparation Checkpoint

用户随后明确要求“生成”；本次实际调用一次built-in `image_gen.imagegen`制作开场首帧，
保存原始输出与prompt到 `runs/jieshi-e01-seedance20-20260905-001/preparation/`。
候选图为 `shot-01-first-frame-v1.png`，941×1672、2064319bytes，SHA-256
`4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。
未上采样，不声明原图1080p。Agent视觉检查可见林砚本人、七个他人倒影及林砚倒影缺席；
这不是human acceptance、Production import、Ark Active observation或媒体验收。
图片生成时的exact创作源另存 `source-authoring.proposed.json`，SHA与旧commit `05b6367`一致；
新修正不重写其provenance。当前proposal另修复姓名替换误伤的P4技术用语并升为revision3，
SHA-256 `d0a373ce062564cc5ca64f075db38cbdc1f295063a27dbbeacaf982ca12de921`。

真实执行阻断：`SeedanceAssetMaterializationReceipt`要求human观察Ark Console中exact素材为Active；
`SeedanceSyntheticImageAuthorizer`和`SeedanceSyntheticImageReferenceResolver.validate_submit`
会在POST前拒绝写实person-like inline引用。仓库只有already-materialized receipt import/resolver，
没有自动Ark Assets上传action。Parent通过codegraph/current source检查，native `code_mapper`
独立复核；其引用的历史整体live状态不作为本次结论，以上结论取自当前执行代码。
对应focused tests实际为3 passed、120 deselected。没有降低gate或静默改为T2V。

经injected supplier只检查 `secret_store:ARK_API_KEY` presence为true，未回显或保存secret，
没有用其发起请求；presence不证明账号权限或余额。未封装当前pricing/budget/egress/permit，
官方文档本轮web读取失败，搜索摘要未用于构造计费事实。
Seedance submit/poll/fetch数量均为0，没有MP4；精确缺项见 `submit-readiness.json`。
本次生成的图片保留在run目录，未伪造Manifest/Registry或asset URL。

主线程继续拥有创作和execution准备；code_mapper只读、没有writer overlap。
当前commit-range Harness receipt预定为
`.agent/harness/runs/jieshi-e01-preparation-20260905/receipt.json`，实际状态以receipt为准。
同主题更新record；Learning evaluation仍为`no_candidate`：一次首帧生成与静态gate检查
不足以形成跨实验结论。下文“没有图片生成”等属于更早authoring阶段的历史状态。

## Historical Model Selection Update

2026-09-05用户最新指令“用seedance2.0吧”取代初版2.5选择。
当前目标为标准版 `doubao-seedance-2-0-260128`，capability
`seedance-2-0-260128-image_to_video`，1080p、9:16、1080×1920、24fps。
下方初版2.5选择与review/receipt均保留为历史，不证明更新后的执行状态。

本次仅修改原创作包的模型目标、画幅参数、源约束及派生hash，没有修改Runtime路径或契约。
由主线程完成这一有界文档调整；没有新增subagent或Provider调用。
现有capability的canonical SHA-256：
`10a7f345de52722d419b0a41f6cf514e3f0a32bc1027e67d09bfd99ca00f3a29`。
当前proposal SHA-256：
`433434377d96a14fa3dc4efce4428acfa1b599d3c81db6afedfd26a2ddf459e8`。
65个计划生成素材均为4–9秒，符合本地capability的4–15秒范围。
实际运行Director validator与verification.md内只读检查：16beats、52shots、300秒、
69个typed artifact及hash通过；逐项对比前版story/cast/scenes/beats/ordered_shots完全一致。
输入素材仍未绑定，不能把静态参数支持当作账号权限、实测清晰度或执行就绪。

当前模型版本的commit-range Harness receipt预定为
`.agent/harness/runs/jieshi-e01-seedance20-20260905/receipt.json`，实际结果以receipt为准。
record-ai-video-session评估为更新同一主题记录；distill-ai-video-learning为`no_candidate`，
没有新增独立媒体实验或现有Learning Claim变更证据。

## Purpose

为《界蚀》第一集《不存在的终点站》完成用户要求的300秒创作包：
剧情节拍、Scene、Shot、台词、动作、镜头与生成提示信息。
用户后续允许Seedance 2.0或2.5并要求更高清，本轮选定Seedance 2.5原生1080p档，
目标9:16、1080×1920、24fps。没有请求或交付已生成MP4的虚假状态。

## Artifact Owner

主创作包目录：`docs/superpowers/artifacts/drama/jieshi-episode-01/`。

- `creative-input.md`：用户brief与模型、清晰度补充。
- `director-coverage.json`：现有open-video schema v3，16个beat，300秒。
- `episode-01.proposed.json`：详细创作提案的唯一内容源，52个剪辑Shot、66个素材component。
- `episode-01.md`：由提案整理的人读全分镜与逐镜提示。
- `creative-artifacts.json`：69个现有Pydantic模型的派生快照，绑定源JSON SHA-256。
- `verification.md`：验证范围、结果、可复现命令与未验证媒体边界。

不存在新的Episode Runtime类。复用既有ProductionBrief、Story、Character、Scene、
Storyboard、Shot字段；B-D0固定2–3镜的fixture acceptance不适用于本集，未复用其PASS。
本包未materialize ProductionProject，也未调用load_production_project、Manifest或Registry writer。

## Decisions

- 先执行retrieve-ai-video-memory，再完成open-video Director coverage并通过validator；
  semantic continuity参考hell-grind-aigc-skill，Seedance表达仅使用2.5 overlay。
- RAG返回tagged stale experience fragments；未作为本次能力或验收事实，也未前台重建。
  当前模型结构和profile从代码重新核对；主线程另用codegraph查看Shot的关系。
- Exact authoring target：`doubao-seedance-2-5-260628` /
  `seedance-2-5-260628-image_to_video` / `seedance-2026-08-19`。
  I2V使用adaptive比例，1080×1920是首帧/成片目标，实际输出尺寸必须实测。
  未创建带pricing/egress的执行profile，也未读取credential。
- 三秒钩子保留用户广播与字幕原句；最后十五秒固定母亲遗忘、监控缺席和J-000提示。
  预见是七秒后的可干预错误分支。两次使用之后，林砚的工作群记录与工牌先后清空。
- 独立审读发现并修正首镜动作提示遗漏、先上车不能回应先下车规则、
  P2局部身体漏登记、C/D门混淆、手机/布袋状态及跨素材短口型等问题。
  修正保留原时长；普通乘客明确先从相邻既有车门下车，两位主角才离车。
- 用户随后要求不用字母当姓名。正文、台词标注和prompt现用林砚、苏遥、周伯祥、
  陈立、许雯、郭向东、沈嘉程、何静、周惠、赵晨；广播保留声源名称。
  稳定character_id/speaker_id仅供机器关联。苏遥姓名只作制作标注，本集不新增身份揭露。
  已逐镜对照改名前暂存版本：镜头顺序、时长、角色ID、逐字台词与生成目标均未改变。

## Verification

实际运行Director validator：`passed`，16个coverage units、300秒。
实际运行现有模型与canonical hash验证：69个artifact通过；17个Storyboard分组，52个Shot。
实际检查逐镜连续时间、角色/Scene闭包、source SHA、台词窗口、24fps素材裁切、
首镜逐字广播/字幕、最后十五秒与监控中的LY缺席，结果通过。

Native `reviewer_high`完成独立审读与同tier scoped re-review，最终 `accept`，
无剩余Blocking issues；主线程直接复核重要修正，并重验派生hash与focused checks。
改名前复核的proposal SHA-256（保留历史）：
`48ec205ef97e4df55744dec3f80d4fc77a2cdc2e59920a53c26278aa87ddab3f`。
姓名修改后的proposal SHA-256：
`6f1bdb6d8f0f42cb3a9f3d41ffc1db2206f991330dfdbcac17d14c8b790143ee`。
该姓名修改另经同一native reviewer_high scoped re-review，结果为`accept`，无阻断。

65个候选生成素材最少计划源时长337秒，加1个末帧复用，剪辑恰好300秒。
这不是已发生调用数，不包含首帧准备和重试，也不是预算reservation。

最终exact-snapshot Harness receipt：
`.agent/harness/runs/jieshi-e01-authoring-names-20260905/receipt.json`。
实际状态、freshness与artifact integrity以该receipt和本次最终交付为准，本文不预写结果。

## Learning Evaluation

按distill-ai-video-learning自动评估为 `no_candidate`。
本轮没有两个独立真实实验、受控多arm比较或更新既有学习claim的媒体证据，
不创建占位Learning Claim，不修改Skill、Provider Policy、Preflight或Gate。

## Remaining Boundaries

本轮没有Provider submit/poll/fetch、图片或视频生成、音频生成、上传、发布、P6或Final Acceptance。
首帧均为待准备需求，prompt是未绑定实际asset的草稿。
实际制作前仍需exact参考素材、连续性binding、当前profile、有限budget/egress/intent/permit、
现有合成能力确认、逐Shot video-analysis以及全速人工观看。
静态authoring验证和review不能证明清晰度、口型、连续性体验、抖音审核或观众留存。

当前checkout其他writer的变更保持原状，未纳入本任务stage/commit。
