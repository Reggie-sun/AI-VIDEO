---
record_kind: architecture_implementation
topic_id: jimeng-model-family-routing-qualification
learning_eligibility: ineligible
---

# Jimeng Model Family And Routing Qualification

Date: 2026-10-22

## Verified Scope

同一个 `JimengVideoProvider` 类、`JimengBrowserTransport` 与 Browser Worker 新增 `seedance_2.0_vip`、`seedance_2.0_fast_vip`，保留 `seedance_2.5`、`seedance_2.0_mini`。型号由 exact profile 显式选择，未知别名拒绝，Provider 不选择 Shot 或降级输出。各型号限制由 `jimeng_models.py` 声明；没有新增 Provider、任务生命周期、预算 owner、恢复入口或素材登记体系。

所有四个型号均为 **UNQUALIFIED**。新 `VideoCapabilityVariant.production_qualification` 进入 capability fingerprint，正式 Router 对未获资格型号返回 `BLOCKED_CAPABILITY / MODEL_UNQUALIFIED`。这只是静态准入声明，没有自动晋级或 profile 放行开关。未声明字段的旧 capability 保持旧序列化和 hash；旧 2.5 profile 的字节 identity 保持兼容。现有历史查询与 UNKNOWN 恢复不依赖新任务路由资格。

| Model | Native ID | Declared duration | Declared resolutions | Production status |
| --- | --- | --- | --- | --- |
| Seedance 2.5 | `seedance_2.5` | 4–30 秒 | 480p / 720p / 1080p | `UNQUALIFIED` |
| Seedance 2.0 Mini | `seedance_2.0_mini` | 4–15 秒 | 720p | `UNQUALIFIED` |
| Seedance 2.0 | `seedance_2.0_vip` | 4–15 秒 | 720p / 1080p / 4k | `UNQUALIFIED` |
| Seedance 2.0 Fast | `seedance_2.0_fast_vip` | 4–15 秒 | 720p | `UNQUALIFIED` |

独立限制和当前有界 mode 4 映射见 [Provider contract](../jimeng-provider.md#selected-models)。本次还修复 2.5 已有的约束遗漏：图片最小/最大尺寸和比例、视频尺寸与最短时长、音频 15 MiB 和最短时长，以及所有型号的 native UTF-16 prompt 长度检查。保持已有较窄图片/视频字节上限，不修改生成规格、不截断 Prompt、不跳过或重排素材。

## Evidence Levels

| Evidence level | Observation | Limit |
| --- | --- | --- |
| 真实网页只读 native config / reference constraints | 当前登录页面的 `videoGenerationConfigStore` 和 `referenceConstraints` 返回四型号原生 ID、时长、分辨率、素材数量、字节、几何与时长限制 | 单次当前配置快照，不是服务稳定性或生成证据 |
| 真实网页只读参数 validator | 四型号、全部声明分辨率的八组三模态 placeholder 参数均 `valid` | 没有上传实际素材；不证明编码或真实生成组合可用 |
| 真实网页只读商业客户端 | 四型号各 720p / 5 秒 / 图片参考的 `quoteActions` 为 available，`getActionState` 为 allowed | 仅当时账号准入；不是 paid permit、真实收费或服务端硬上限 |
| 源码与 Mock | 共用 native action、mode 4、模型名、素材 index/type、输入视频计费时长映射；Fake transport、故障和重开验证 | 不将 Mock 标为真实生成或恢复 PASS |

直接 `generation_specs` 只读请求当时失败；实际数据来自网页已经初始化的 native stores，不把失败请求说成成功接口证据。脱敏配置投影已纳入 `tests/fixtures/generated_video/jimeng-native-models-20261022.json`，不包含账号、Cookie、Token、URL 或完整网页响应。

本轮上传、生成 POST、充值、购买均为 **0**。当前原生权限、fresh quote、operator credit bound、Paid Gate、一次性 permit、dispatch 持久化、UNKNOWN 及预算预留机制继续保留。历史成功资源的证据边界沿 [reliability record](2026-10-21-jimeng-reliability-qualification.md)，不据历史成功给本轮型号晋级。

## Tests And Independent Review

Jimeng 专项从 97 增至 **193 项**，新增 96 个参数化案例。覆盖四型号声明、独立 profile、分辨率/时长/别名拒绝、原生三模态参数和 material index、模型不替换、UTF-16 Prompt/几何/总时长超限、资格 hash 防篡改与正式路由拒绝，并将已有标准项目 Paid / State / UNKNOWN / concurrent recovery / Reader reopen 测试扩展到四型号。生命周期 Mock 显式构造测试用 `QUALIFIED` snapshot；真实 Provider 始终声明 `UNQUALIFIED`，测试不构成资格授权。

exact staged tree `237dc0fa1eb40cf5d3bec971e4d76ffc035c49cd`，base `15732cdc2707c002ff9cf17a129f770800f14e63` 的 Harness 为 **PASS**：累计执行 2,239 项、零失败，包括 runtime boundary 2、voice routing 47、Provider/Paid 1,177（含 Jimeng 193）、Vidu 191、neutral requirement 450、Shot Router 372。`seedance_local_video_tests` 按现有 covering check 规则跳过。文档、规则、policy audit 和 Architecture Gate 通过；保留既有大型契约模块两条增长 warning（Router reason enum +1 LOC、video capability +7 LOC），未为形式统一扩建模块或调整 baseline。前序全仓 12 项基线失败没有由本次 scoped PASS 消除，本轮没有运行完整全仓套件。

一名只读 Native `/root/final_review`、实际 profile `reviewer_xhigh`，新模型任务第 1 轮，绑定上述 tree 和 11 个文件 hash；finding set 为空。Reviewer 报告另运行 45 项模型/资格/边界测试通过，没有浏览器或付费调用。Parent 核对暂存树不变。审查不是平台运行或视觉/音频验收。

Receipt：`.agent/harness/runs/jimeng-model-family-20261022/receipt.json`；本地审查与 tree/hash 索引：`.codex/tmp/jimeng-models-20261022/candidate.json`、`review.json`；这些忽略目录不随 Git 发布。

## Workspace And Publication Boundary

提交前发现 `shot_router.py`、`_shot_router_contracts.py` 出现暂存之外的并发改动：新增 `execution_purpose="qualification"` 的放行路径。它们不属于上述冻结快照，未纳入本任务测试或独立审查，Parent 没有覆盖或暂存；已向用户确认归属和处理方式。

该时点 `verify-receipt` 的 integrity、snapshot_matches、complete_completion_proof、coverage 均成立，但本地 `scope_worktree_clean=false`，因此 `fresh=false`。不能把上述快照 PASS 外推到叠加这些改动后的当前工作区。Parent 没有继续写入冲突文件；按既有明确交付授权，仅提交原来已冻结的 11 个 owned paths/index，未将新增路径纳入。代码 commit **`52f6543a4113f342e6049db396bb7e2191b168e7`** 的 Git tree 与上述测试、审查的 tree 完全一致，已 push 到远端 `main` 并核对 SHA；两处本地叠加文件在提交前后的 SHA-256 均未变化。归属确认只决定是否继续纳入新入口，不作为原冻结快照的发布授权来源。

本记录是随后独立的文档 checkpoint；文档 Harness receipt 为 `.agent/harness/runs/jimeng-model-family-record-20261022/receipt.json`。最终交付只覆盖已发布 commit 的明确 scope，包含 `qualification_preview_input.py`、`test_jimeng_qualification_trial.py` 等其他新增本地文件的工作区版本没有由本轮证明，也没有被暂存或发布。

## Production Qualification Judgment

四型号的**参数映射与只读准入已验证到所述范围**，正式生产为 **NO-GO / UNQUALIFIED**。没有新增真实生成，不宣称 2.0 / Fast 已可稳定生产；2.5 历史 Probe 和 Mini 历史资源也不证明正式 Provider 的完整成功链。新资格限制保证正常正式路由不能选择这些型号，不代表已验证未来独立浏览器实例并发或任意网页版本。

后续真实资格验证必须获得新的有界付费授权，并保留原生权限、fresh quote、预算/permit、唯一 State owner；逐型号、逐有界规格取得正式 Provider 成功提交、精确任务查询、结果下载、画布保存、标准 Reader 重开及实际费用协调证据。进程/浏览器中断、响应丢失和登录过期的真实恢复仍沿前序记录列为证据缺口；无 dispatch 的 UNKNOWN 保持阻断和预留，不重交。创作声画验收仍归 Director / Shot QA，本 Provider 不承担。

Automatic learning evaluation：`no_candidate`。本轮为一次配置快照和确定性工程验证，没有独立真实媒体实验支持跨实验质量规则；未新增 Learning Claim、Skill/Policy/Gate 或全局 memory 改动。
