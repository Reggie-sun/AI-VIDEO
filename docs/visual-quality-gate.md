# Overall Visual Quality Gate

## Scope

字体、配色、排版、画风一致性与整体观感进入现有 `QaPolicy.final_output`，仍由
Review / Repair 和 `ProductionStateCommitter` 裁决并持久化。没有新增 QA layer、
评分平均值、renderer 或第二套交付状态。旧 policy 未声明视觉要求时不追溯修改历史。

## Authoring

新建开发报告必须显式区分 `advertising` 与 `drama`，不能共用一份字体审美方向：
[广告方向](../configs/visual-quality/advertising.json)关注商业标题、品牌、CTA和条件说明；
[电视剧方向](../configs/visual-quality/drama.json)关注对白连续阅读、稳定位置、表演避让与
题材画风，并将片名等展示字与对白字幕分开。两份文件是独立 authoring 起点，不是
自动分类器或普遍适用的字体白名单；仍需根据具体作品明确字体、字号和观看标准。

`VisualDirection.content_kind` 显式声明类型后，factory 生成
`visual.advertising.<dimension>` 或 `visual.drama.<dimension>` requirement IDs。
即使方向文案相同，contract hash 也不同；广告证据不能通过电视剧合同的原有
exact identity 校验。选对作品类型由 authoring caller 负责，Gate 不从 MP4 猜类型。
两类共用 bytes、抽帧引用与完整观看校验，仍使用唯一 SEMANTIC / Final Acceptance
owner；电视剧对白准确性和同步仍由原 CAPTION Gate 负责，本次没有替换它。

兼容：已有未分类 `VisualDirection` 在 Python API 中继续可读，缺省字段不序列化，
旧 requirement ID 和已封存 packet 保持可读；旧完整报告缺少接缝证据时，当前 `check` 不再宣称完整通过。新私有 `prepare` CLI 要求
`--content-kind` 且必须与方向文件一致；旧创建命令需补该参数及显式分类的方向文件，
不能依靠默认广告类型。此变更不增加或改变公共 `ai-video` CLI 命令。

`visual_quality.VisualDirection` 保存五项具体期望，`visual_requirements(direction)`
将其转换为普通 `FinalOutputRequirement`，合并进完整用户目标的 requirements；
不得替换或删掉原音频、动作、叙事等要求。新 `visual_dimension` 可选，缺省不序列化，
旧 contract/hash 保持原样；启用时五项必须齐全且维度唯一。

示例方向：[ninebot.json](../configs/visual-quality/ninebot.json)。这是一套可修改的
具体 authoring 示例，不是适用于所有片种的默认审美或对旧成片的追溯授权。
将 contract 纳入 policy 后，仍通过原 `activate_qa_policy()` 显式选择，遵守原目标
版本规则；本工具不自动替换已激活 QA。

## Evidence And Gate

视觉 finding 仍在 `measured_payload.final_output.findings` 中，每项包含原
requirement ID、verdict、observation，以及 `visual_frames`：timestamp_ms、
frame_sha256、render_output_sha256。原 request/contract/tool/timeline/graph 绑定继续有效。
同一 observation 的 `visual_frame_inventory` 封存 duration_ms 与完整抽帧引用；
引用必须命中清单，时间必须在片长内，清单不得混用其他 MP4 或重复时间点。
Production 验证 selected evaluator 的测量声明，不重新解码 MP4/JPEG，也不证明
截图像素真实性；本地报告则重验实际 MP4/JPEG bytes 与 packet inventory。
缺少帧引用、引用其他 MP4、空白观察或遗漏要求不产生 PASS。

全片观感要求 `HUMAN`、`viewing_speed_milli=1000` 和 `viewing_mode=full_playback`。
抽帧可为明确局部 FAIL 提供证据，但不证明完整播放、文字驻留时间或真实人类观看。
工程检查验证证据声明与 identity，不具有辨别评审者说真话的能力。
若一项有效 FAIL，整体 FAIL；否则缺项或未评审为 NOT_EVALUATED。原最终验收入口
重新读取并裁决语义证据，失败或未知不能进入 Final Acceptance。

## Local Report

完整作品的开发侧审片使用 `prepare --contract /path/to/final-output-contract.json`，
同时提供该作品的 `--direction`、`--content-kind`、`--timeline` 和 `--render-report`。
后两者必须是本次 canonical `ResolvedTimeline` 与绑定 exact MP4 的 HyperFrames 输出报告。
`--contract` 读取原
`FinalOutputContract`，保留 `goal_id`、`goal_version`、`user_goal` 与所有 requirements；
其中五项视觉要求必须与 direction 完全一致，差异在 probe/抽帧/建目录前拒绝。
叙事、表演、商品、声音等普通要求不会被视觉要求替换或过滤，任何有效 FAIL 都阻断
整体 PASS，缺项为 NOT_EVALUATED，仍使用同一个 `adjudicate_final_output`。

此模式产生 `visual-review-packet/4` 与 `review_scope=full_contract`。不传 contract
则保持旧 `/1` packet 和 `review_scope=visual_only`；已有 packet 与旧合同身份继续可读。
HTML 显示原目标和所有要求，非视觉项使用原 requirement ID。
`full_contract` 仅描述 caller 输入范围：工具不会自动理解叙事、听音频、验证合同穷尽原意，
也不拦截 Agent 直接发链接。原始 brief 到合同的覆盖和审片纪律见
[Creative Completion Practice](../.agents/skills/open-video/references/creative-completion.md)。

新目标承接入口先使用 `python -m scripts.creative_goal_binding --binding PATH` 做只读检查，
再给 `prepare` 同时传 `--contract PATH --goal-binding PATH`。封套要求 Director v4、三份
contained exact file references 与完整 intent bindings；无效输入或合同冲突在 probe/抽帧/
mkdir 前拒绝。它不改变公共 `ai-video` CLI。封套字段与创作闭环只由上方 reference 维护。

显式传 goal binding 时，`/4` 仍保留此前 `/3` 的封套快照机制：封套及三个依赖以预检已读的原始 bytes
保存于 `creative/`，保留相对引用，identity 纳入 `subject_hash`。即使外部输入后来变化/移动，
reopen/check 只消费封存 snapshot；缺文件、symlink、改 quote/映射/合同/hash 都拒绝。
JSON bytes SHA 与 `contract_hash` 分别验证文件和语义，不能互相替代。旧 packet 不静默升级，
`/1`、`/2` 的 `goal_chain=not_evaluated` 保留；`/3` 的 `verified` 也只证明结构完整。

`/4` 额外封存 timeline/report bytes 与逐接缝 inventory；每刀的画面采用窗口、源素材 hash、
附近音轨的 sample 位置、裁切和淡入淡出由同一 `ResolvedTimeline` 投影，不建立第二时间线。
即使 CompositionSpec 未显式写 transition 标签，实际相邻 Shot 切镜也必须检查；叠加图层不重复计刀。
每刀必须记录 `junction_findings`：剪辑决定及理由、画面观察、声音观察和实际观看方式。
`retain_with_reason` 允许保留当前接点；`trim` 表示仍需修剪，会阻断通过，不能用理由替代修复。
PASS 需要 exact inventory、实际 human 1x 完整听看和分别明确的声画观察；播放器结束、首尾帧绑定、
抽帧、波形或 ASR 均不能代签听感。已报告的画面或声音 FAIL 保留为修复项，不能因不具备 PASS 证据而抹成未知。
缺项、未听声音、旧回答或 MP4/timeline/report 改动均不通过；旧 `/2`、`/3` 缺接缝绑定时返回
`missing_junction_binding`，仍保留已有 FAIL，不可通过降级 packet 版本绕过。

JSON/HTML 保留 evaluator 原始 `findings`，另列原 owner
`adjudicate_final_output_details` 的 `effective_requirements` 和全局 `evidence_gaps`。
不合格 human/sample/身份证据的 raw PASS 不显示为已证明；有效 FAIL 仍优先，任何全局
incomplete 仍阻断整体 PASS。旧 aggregate API、Production schema 与 acceptance 条件不变。
`completion_summary` 列出 exact identity、实际声明的复核范围、待修/补证要求及用户反馈来源；
用户语义仍需 Parent 核对和披露，不由机器判断拒绝是否撤回，不新建 accepted 状态。
所有 packet 的 `production_acceptance` 仍为 `not_evaluated`。

以下私有开发工具读取现有 MP4，使用 ffprobe 与 ffmpeg 生成截图和 HTML；不写
Production Manifest、Registry、ReviewReceipt 或 FinalAcceptanceReceipt。

```bash
python -m scripts.visual_quality_report prepare \
  --video /absolute/path/video.mp4 \
  --content-kind advertising \
  --direction configs/visual-quality/ninebot.json \
  --output /absolute/path/new-review-folder \
  --timestamps-ms 1000 3000 6000 9000 15000 21000 24000 27000

python -m scripts.visual_quality_report check \
  --packet /absolute/path/new-review-folder \
  --answers /absolute/path/new-review-folder/observations.json
```

电视剧使用 `--content-kind drama --direction configs/visual-quality/drama.json`。
类型缺失或冲突在抽帧和创建报告目录前拒绝；改变类型需新合同、新 packet 和新评审。

先打开 `report.html` 看方向和截图，再复制 `observations.template.json` 填写实际
评审。帧引用必须来自 packet；未观察到的项目保持 not_evaluated，不能为了通过
填写 human 或 full_playback。`prepare` 成功退出 0 只表示材料已生成；`check`
只有相应范围的开发侧 PASS 退出 0，FAIL/NOT_EVALUATED 退出 1，输入无效退出 2。

每次 check 重验 MP4、截图和封存 packet，清除旧派生 result/report 后重建，
防止换片后旧 PASS 报告继续留下。报告是可重算的开发侧观察，不是受控 human
host，也不具备签发 Production 验收的权限。

## Assembly Harness Entry

拼接或修剪连续片后、交付前，运行以下现有 Harness CLI 入口。它复用 `junction_review.py`
从唯一 `ResolvedTimeline` 推导全部相邻Shot接点（包括未标transition的硬切），不新增时间线或验收状态。

```bash
python -m scripts.agent_harness prepare-assembly-review \
  --video /absolute/path/rendered.mp4 \
  --timeline /absolute/path/resolved-timeline.json \
  --render-report /absolute/path/render-receipt.json \
  --output /absolute/path/new-observations.json

python -m scripts.agent_harness verify-assembly \
  --video /absolute/path/rendered.mp4 \
  --timeline /absolute/path/resolved-timeline.json \
  --render-report /absolute/path/render-receipt.json \
  --answers /absolute/path/observations.json
```

`prepare-assembly-review` 只生成默认全部NOT_EVALUATED的待填模板，独占创建文件且不覆盖旧文件；
不能把该命令退出0当成验证通过。逐刀检查前后完整行动与回应，不能只看切点一帧；
`action_review` 明确记录 `repetition`（动作是否无意重复）、`state_continuity`（持物、接触支撑、
视线与动作阶段）、`pacing`（停顿、速度与反应时机）的 verdict/observation；有意重演须说明叙事理由。
同时保留原Gate的剪辑决定、画面、声音、实际观看速度与观察依据。重复动作、连续性或节奏项明确FAIL
即阻断，其他证据缺失不掩盖已见FAIL；仅抽帧或未听声音不能签接点PASS。改剪辑后重渲染，
新MP4、timeline、report和inventory均须重新绑定，旧记录不能直接用于新输出。

`verify-assembly` 退出0只表示exact当前绑定和全部逐刀声明满足开发侧Gate；FAIL或NOT_EVALUATED退出1，
无效输入/陈旧绑定退出2。输出绑定回答文件SHA、当前视频SHA及timeline/report原字节SHA；
运行中变化也拒绝。report必须匹配选中的实际renderer输出路径，复制到交付目录的同bytes副本由SHA另核对。
本地report未重复提供 `timeline_frames` 时，仍须由 `measured.duration_frames` 匹配时间线；显式矛盾拒绝。

这不是视觉模型，不能自动识别任意影片中的重复扫码，也不能证明填写者确实看过/听过；
继续沿原Gate验证正常速度人工观看及声音声明，不自动填human，不新设用户审批流程。
它不运行生成、解码/抽帧或远程分析，不写Production state，不授予QA接受、发布或下一镜提交。
用户明确要求先看时可交标明未验证的审看片，验证结果必须如实披露；未通过不得称“接点已验收”。
这项入口是Agent交付前的必做检查，Harness不拦截任意shell或文件复制。

`assembly_review_tests` 验证该CLI与旧接点owner的正反例；单镜或同Shot内部镜头仍需原速审看，
Shot级inventory不自动发现生成视频内部的所有摄影切镜。

## Regression Checks

`python -m pytest -p no:cacheprovider tests/test_production_visual_quality.py
tests/test_visual_quality_report.py -q` 验证逐项阻断、真实 committer/strict reopen、
旧序列化、实际 ffmpeg 抽帧、替换 MP4/截图、陈旧回答、HTML 转义与缺少全片观看。
Harness 的 `visual_quality_tests` 路由这些检查，相关 Review / Repair 回归继续执行。
`tests/test_junction_review_gate.py` 覆盖逐刀、隐式切镜、单片零接缝、声音失败保留与 stale/downgrade 阻断；
同样进入 `visual_quality_tests` 与 `creative_goal_binding_tests`。新封套与 `/4` 实际入口继续验证 Runtime 单向边界。
测试通过不代表某条成片已达到用户的审美要求。
