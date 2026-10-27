---
record_kind: architecture_implementation
topic_id: shot-reference-compositional-risk
learning_eligibility: ineligible
---

# Shot Reference Risk Assessment

Date: 2026-10-27

## Assessment

现有系统已有一套可用的 Director → Canvas → VideoPlanner → neutral requirement → Router/compiler → QA feedback 链。
`reference_planning.py` 依据 typed facets、events、anchors 和 selections 决定参考职责，不按时长配图；
`reference_strategy.py` 精选已校验素材，身份/owner/bytes、Registry、selected capability 与 committer 保持原 owner。
readiness 在 `_asset_readiness.py` 检查角色、revision/content hash，Registry 在 `registry.py` 检查路径/bytes；
QA 验收仍由原 receipts/Manifest lifecycle 及逐镜 Gate 决定。

实质缺口是旧规则将 contact、physics、high-speed、complex-camera 任一标签直接升级为必需连续视频，
又只给泛泛预演建议。简单动作会被无故阻断；审看状态数也容易被误读成需要生成/提交的图片数。
已有 QA 建议能按 failed intent paths 定位，但需要先比较实际输入与输出，避免动作失败一律加图。

## Implemented Changes

在原 `ShotReferencePlan` 扩展派生报告，规则版本为 `shot-reference-rules/2`：

- motion 分为 `none / recommended / previs_priority / required`，由组合约束而非单个标签决定。
- 新增 `sustained_contact / support_transfer` 正交 facts；显式 `motion_reference_policy=required` 支持 Director 的必要控制决定。
  默认 `auto` 从序列化省略；旧字段、旧缺省 intent seal 形状保持，没有迁移/覆盖历史。
- 稳定对白、简单触碰可以零新增图片且不用白模；高速/物理/复杂摄影单维度仅建议 motion。
  持续接触与支撑转换、因果接触受力叠加高速或多人遮挡仍要求连续参考；静态姿态不替代它。
- `whitebox_decision` 给出无需制作、可选静态布局、先复用运动素材再评估连续 proxy/playblast 的具体理由。
  `reuse_quality=NOT_EVALUATED` 防止把已有或选中素材当作已验证可用。
- 报告分开 review states、未绑定图片职责、无可复用素材时的候选图数、minimum/higher-control 方案、
  planned inputs 与 compiled actual bindings；完整 selected variant 从原 capability 直接投影。
- 失败建议要求对照 exact MP4/QA 区间、reference bytes、native roles/order 和实际 prompt，区分覆盖不足、
  属性冲突、能力边界、文字、动作/导演设计及剪辑源时序；保留 passing requirements，UNKNOWN 只走 recovery。
- 更新现有 open-video、Storyboard specialist、Seedance authoring、Blender routing/blockout/previs 交接，
  去除白模“完全控制”保证式表述。没有安装新 Skill、创建第二 Registry/Router/Planner 或素材状态库。

完整规则与十类组合需求的收益/成本/风险对照见 [Reference Planning](../shot-reference-planning.md)。
计划见 [Implementation Plan](../superpowers/plans/2026-10-27-shot-reference-risk-assessment.md)。

## Upstream And Provider Findings

只读检出 Scenario 上游 commit `72b763c162266948f06f299b8aecfdf9f74a4779`，未安装或复制第二套执行流程。
研究 [multi-reference](https://github.com/scenario-labs/skills/blob/72b763c162266948f06f299b8aecfdf9f74a4779/skills/scenario-multi-reference/SKILL.md)、
[storyboard](https://github.com/scenario-labs/skills/blob/72b763c162266948f06f299b8aecfdf9f74a4779/skills/scenario-seedance-storyboard/SKILL.md)、
[blockout](https://github.com/scenario-labs/skills/blob/72b763c162266948f06f299b8aecfdf9f74a4779/skills/dcc/blender/scenario-blender-blockout/SKILL.md) 与
[previs](https://github.com/scenario-labs/skills/blob/72b763c162266948f06f299b8aecfdf9f74a4779/skills/dcc/blender/scenario-blender-previs-storyboard/SKILL.md)。
适用方法是明确每图主要职责和不应迁移属性、逐状态复核、区分审看 animatic 与 motion guide，以及最小可编辑几何。
不继承自动安装、Scenario collection/model_run、固定关键帧配方、默认高级场景密度，或“首尾图/白模保证动作”的表述。

当前源码 `seedance_capabilities.py` 区分 T2V、I2V/首尾与 R2V：2.0 R2V 上限9图/3视频、2.5 R2V 上限30图/10视频，
I2V 要 first frame、可 last frame，普通 reference 槽为零。官网 [2.5 overview](https://seed.bytedance.com/en/seedance2_5)
和 [launch guidance](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)
描述多模态与更长叙事能力；这不是逐时刻关键帧保证，也不能覆盖实际渠道限制。
H3 的 `metaso_h3.py` / `minimax_h3_max.py` 同样将 frame 与 multimodal 变体分开；R2V 声明9图/3视频，
视频 FPS、时长、总数及图像兼容性须由 exact variant/Profile/Router 校验。没有因官网容量升级渠道能力。
本轮没有 live session/capability submit 测试，当前账号/渠道真实可执行性仍须请求时核验。

## Historical Evidence And Limits

只读 native `code_mapper` 调查原请求/QA/素材；Parent 回看代表性 exact 抽帧并核对 QA SHA。
历史记录是线索，未重新签发任何 PASS/FAIL 或改变 accepted state。

| Case | Exact Evidence | Observation And Attribution Limit |
| --- | --- | --- |
| 失帧六图 MC03–05 | `outputs/shizhen-episode01/macro-opening-video-20261027/MC03-05/reference-input-plan.json`、`qa/post-media-gate.json`；对应 `runs/shizhen-macro-opening-20261027/MC03-05/state/video-generation/requests/` | actual Seedance2.0 VIP R2V 六张 native `reference`、无视频；输出 SHA `43584ba80ad0fc3beaaadfd8cc55c2748f4f3169b667a61d0655787e2e2b5528` 重新核验。t=0 已开门，QA 记录下楼变上楼/推门变拉门。多变量混杂，不能断言“六张太多/太少”是根因 |
| 失帧首尾修复 | 同路径 `MC03-05-repair-v2/reference-input-plan.json`、`qa/post-media-gate.json`、`qa/frame-index.json` 与 corresponding request | actual I2V first+last 两图，closed-door 中间图 review-only。输出 SHA `aecf88b4f06a005e5db32b11138dcc9b3db3700ab08c993187263e2ed21038c5` 重验。早揭示修复，但 QA 仍判楼梯/反复开门/接触 FAIL；8.5s、9s 抽帧可见门角变化与手把关系变化，静帧不能独立证明持续受力 |
| 失帧新状态包 | [macro reference record](2026-10-27-shizhen-macro-reference-preparation.md) | 七张干净图分下楼到达、接触持续推门两组；记录当时仅静态审查，本任务未核验该包的后续视频。不能标成已验证 motion |
| 界蚀 H3 Max | `runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-20261020-001/camera-corrected/` 的 resolved/native/submit/fetch/review-round9 | actual 9图+1 Blender whitebox 视频。输出 SHA `b3fea442735a2ad0a41c795c548c05e1a27c11a804b50e740775e417e918203b` 在 fetch/QA 一致，但原 MP4 当前缺失，不能 fresh rehash；21张历史抽帧可见腰部多余手/物体。镜像跟手/身份布局分别为 QA 记录，不冒充本轮完整动态观察 |
| 界蚀 motion source | 同链 Registry 的 `jieshi-uploadedstyle-camera-motion-guide-20261020-001`；[H3 record](2026-10-20-jieshi-3d-anime-minimax-test.md) | 历史5s/120-frame白模确实入请求，有当时检查；现 MP4 已缺失，只余 blend/audits，不能宣称目前可直接复用或其成功控制 H3 |
| Blender→Seedance Mini 正例 | [white-model transfer](2026-09-17-blender-mcp-white-model-seedance-mini-materialization-blocker.md)、`runs/seedance-blender-white-model-r2v-20260917-001/SUMMARY.md` | 单人物固定机位抬右臂/转身，source 与机器人 transfer 当时 Gate PASS；另一个方向错误的 source 曾 FAIL。支持先验 motion 源再使用，不证明多人/人体/所有白模通用有效 |
| 清颜广告 | `runs/qingyan-seedance2-reference-ugc-30s-20260828-001/shot-02/evidence/resolved-request.json` 及当时 gate | actual 两张产品图、零视频、2.0/15s/720p；QA 记载重复瓶盒。原 MP4/抽帧当前缺失，只能确认请求/记录，不能独立验证受力或把 floating-box 归因于缺 motion |

这些是不同目标/版本/模式的实际案例，不是控制变量实验。已验收前镜只证明自己的 exact 动作，
不是后镜的自动 motion qualification。无法由上述案例推出最优图数、白模普遍必要性或本次策略改善生成成功率。

## Verification

新增测试先出现10项预期失败，覆盖缺失风险报告与新 facts；实现后精准/邻近 tests 164 passed。
覆盖长短稳定镜头零新增图、简单接触不阻断、耦合风险缺 motion 阻断、选择视频的真实能力/数量限制、
review-only 不能上传、普通 reference 不能冒充 endpoint、独立身份 bytes 冲突、默认序列化及修订失效，
并通过真实 Canvas authoring/committer/loader/Planner/compiler seam，fake submit/fetch 均零。

- 七组直接关联诊断回归：**787 passed / 439.48s**，由 policy 原 argv 合并去重，启用原 no-network pytest guard。
  JUnit：`.agent/harness/runs/reference-risk-diagnostic-related-20261027.junit.xml`；这是诊断回归，不冒充 Harness full。
- `python -m scripts.architecture_gate check --base-ref HEAD`：PASS，0 errors / warnings / info。
- focused Harness：generation-feedback 组在900秒硬上限停止，receipt 为
  `.agent/harness/runs/reference-risk-focused-20261027/receipt.json`，状态 `failed` / `timed_out`。
  原检查收集626项、进度记录616项；对照同 argv 的 collect-only 确定10项未结算尾部和两个 FAIL 的 node IDs。
  单独补跑尾部及两项失败：**10 passed / 2 failed / 42.45s**，没有重跑整组或提高 timeout。
  JUnit：`.agent/harness/runs/reference-risk-feedback-tail-20261027.junit.xml`。
- 两项失败均是 `tests/test_generation_runtime_repair.py` 的
  `test_cross_provider_canvas_reopen_after_paid_intent_uses_consumed_lineage` 与
  `test_runtime_repair_requires_runtime_failure_evidence`。前者缺 Seedance compiler/4 当前文本 QA，
  后者错误消息预期不符。在 clean `git archive 5c8a9877199945e8da6aa322f0ad96791256cd72` 中独立复现同样两项失败，
  JUnit：`.agent/harness/runs/reference-risk-baseline-runtime-20261027.junit.xml`。未修复无关 baseline。
- related/full Harness 在未修改的 `AGENTS.md` 文档预算处停止；clean HEAD 导出同样复现。
  current/HEAD blob 均为 `28b9eb4bb6c84053a984dca68a50ae4f1fcaf412`。原 checkpoint receipts 位于
  `.agent/harness/runs/reference-risk-related-20261027/receipt.json` 与 `reference-risk-full-20261027/receipt.json`。
  最终仅文档收尾后的串行 exact staged receipts 为 `.agent/harness/runs/reference-risk-final-related-serial-20261027/receipt.json`
  与 `.agent/harness/runs/reference-risk-final-full-v2-20261027/receipt.json`；全量 pytest 未由 Harness 执行，不能称完整回归通过。

上述行为验证后的四份源码保持相同 SHA-256；后续收尾只更新文档/Skill 文字：

| Source Under `src/ai_video/production/` | SHA-256 |
| --- | --- |
| `reference_planning.py` | `2574646982b5461a8aab782f96e9817c55a7806d18fa44be1048a476b47451a7` |
| `reference_planning_contracts.py` | `363a94b0080580fdf2425e7cdc5b0f8acfaf6c1807d66f8fa486d3ea7a2e6b6b` |
| `reference_strategy.py` | `7e16edfb467fc31413dc37e2f996dd540b13d8d1e3d9cd1ebaf0cc6c7d48292a` |
| `video_reference_controls.py` | `88a016bfc81f9a436793c18c1b4159d11dd40beb0cfbc344c2a26fc3a0274d03` |

## Review And Learning Boundary

Parent 唯一 writer；调查 agent 仅只读。Risk Gate 为 `NATIVE_REVIEW_NOT_REQUIRED`：候选是上表源码、
派生报告/受限输入决策与 advisory 交接；没有凭据、权限、持久状态或验收写入变更，787项关联验证覆盖主要决策与失败路径。
既有 full 阻断与 timeout 不被静态独立审查代签关闭；本次不声明 full qualification 或媒体质量收益。
本记录使用 `record-ai-video-session`。`distill-ai-video-learning` 评估为 `no_candidate`：
本轮没有新媒体实验，历史案例未隔离参考策略变量，不能从工程测试声称生成质量收益或自动采用经验 Learning Claim。
本任务对现有 Skill 的必要交接修改来自用户明确实施授权，不是待确认经验 claim 的自动 adoption。

没有付费视频/图片/音乐调用或新媒体生成，费用为0；没有 UNKNOWN 重试、Production mutation 或历史验收改写。
publication 仅为本任务 owned paths 的工程 checkpoint；最终 commit 与远端 SHA 以交付时 Git 回读为准，不是发布质量 PASS。
