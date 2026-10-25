---
record_kind: architecture_implementation
topic_id: shot-performance-prompt-fidelity-repair
learning_eligibility: ineligible
---

# Shot Performance And Prompt Fidelity Repair

Date: 2026-10-21

## Authorization And Scope

用户在[spec-only 交付](../superpowers/specs/2026-10-21-shot-performance-and-prompt-fidelity-repair.md)后明确要求“修复”，并追问是否只针对这个视频。后续[实施计划](../superpowers/plans/2026-10-21-shot-performance-and-prompt-fidelity-repair.md)落实跨项目、人数、景别和 beat 的共享能力；《界蚀》只保留为[已知失败证据](2026-10-21-jieshi-seedance-20-fast-comparison.md#human-feedback-and-module-diagnosis)。本记录不回写旧媒体裁决或宣称自然度已改善。

## Engineering Candidate

现有 QA 表达增加 optional `native_text_mapping`（`native-text-mapping/1`），以同一条 `native_text` 的索引绑定具体 intent 叶子，并由 QA 作者封存 canonical intent 的 `intent_sha256`；缺省不序列化。intent 变更后旧 QA 映射拒绝，runtime 不代更新。recipe 核验 selected QA 及 fragment 来源；v4 ordinary Seedance binding 从最终正文检查片段和逐人物/beat 职责，不继承被替换 prose 的文字覆盖声明。编译失败沿现有 typed result 展示 final text、缺失路径与 rejected coverage source。

fresh prepare 选择明确封存的 compiler/4；自动 prose v1/v2、legacy source-preservation flag v2 和 Shot-level preserved-source v3 保留独立契约。pre-submit 仍经原 compile helper，以已有 sealed request 的完整相等作为 replay evidence。fresh execution creation 复验当前最终输入；历史 reader 不追加义务。voice/continuity 继续经过原验证，不静音或换 route。

原 Canvas workflow 和 `seedance-authoring` 同步约束来源、背景生活状态、逐人物文字职责、全场参考局部观察及 exact 正常速度声画审查。静止和微表演不按关键词判错，字面覆盖不提供审美或媒体验收。矩阵和 baseline 已有其他 dirty changes，本轮未覆盖；操作细节写在其已委托的 workflow owner。

## Verification

- 新 fidelity 测试首次 RED 为现有 schema 拒绝新映射；完成后 15 项通过，覆盖三个不同 cast/场景及不同 beat、offscreen、合法静止、缺失/反向片段、父路径、source/request 绑定、旧契约、标准 prepare/start 无副作用和报告边界。
- 当前选测的 source、source-expression、performance-authoring、mixed-reference、feedback、execution、voice-integration、provider-wiring 共167项通过。
- input-control、requirement-semantics、execution-guards、authoring-skill 的选测中77项通过；一项 quota fixture 在本轮开始已 dirty 的 `_state_commit_video.py` / `paid_provider_submit_quota.py` 路径因缺 `active_paid_provider_budget` 抛错。隔离进程只换回这两段 HEAD 函数后同一测试通过；未写回、修复或覆盖上述文件，不将该结果伪报为整组 PASS。
- documentation contract、agent rules、policy audit 和 owned-path whitespace 检查通过。新测试登记到既有 Seedance suite；没有改动质量/授权 Gate 语义。
- CodeGraph 查询返回 `Source changed during indexing`；依当前源码与一名只读 native mapper 核对调用链，不将未完成的 graph 查询当作证明。

用户追问 AOCI 后，补读 Cognition Tools 并实际调用 `aoci_rules`、`aoci_overview`：MCP `0.1.0-rc14` 完整交付33条、约5645 tokens，index `f34aee87f334494bbb91f05a2939610e15072b283ace43f981dc88e8a0a0a9c1`。host delivery 已确认，但两次声明在字段 schema 层失败，严格认知验证未完成；工具同时报告 `dirty_or_stale` / `governance_aligned=false`。不重试语义答案、不声称完整可靠系统认知，不在共享源码仍变动时维护索引。AOCI 的 execution binding、唯一 committer 与 QA/media 职责用于辅助定位，所有修复仍逐项绑定当前 source/test evidence。此前未充分评估其用途的遗漏保留为本次工具选择事实。

2026-10-22 补验：原 Seedance suite125项通过。新增 `test_seedance_durable_fidelity.py` 经真实临时 Production author/commit/load/begin/receipt seam 验证四项：fresh 重封装 v2 写入前拒绝、合法 v2 request/binding 原 hash 重开、既有旧替换正文的原字节恢复及 pre-submit recompile、错误 binding pointer 拒绝。临时进程禁用新增 admission 方法时，fresh canonical begin 回归确实失败为 `DID NOT RAISE`；恢复方法后通过。该 fault-injection 只模拟先前缺口，没有写回工作区源码或触发 Provider。

这些是 focused 工程证据；没有完整 Harness receipt、真实 Provider/媒体效果证据或新的质量 verdict。

## Independent Review

Risk Gate：因 fresh/replay 与 durable authority 边界仍需独立语义核验，采用一名 `reviewer_xhigh` 原生只读 reviewer `/root/fidelity_review`，禁止 nested delegation。首轮候选 HEAD 为 `d5c7f04298101d3cc9b1162e1c53e1f7a8084ecb`，19个 owned 文件的 snapshot manifest SHA 为 `0337d1eeeb23e3b27fcd747a415b7ed8c8be0f2423afcba187906a4106c61e50`；reviewer 核验文件/spec/patch 无漂移，期间共享 HEAD 因其他工作推进到 `15732cdc`。

首轮 `SPF-001 / blocking_candidate` 为 `CONFIRMED`：只检查 `.create` 不能阻止重新封装的 v2 数据经 `.model_validate` 进入新 durable attempt。已将 shared fresh guard 移入 factory 与 `validate_current_project` 的共同 admission 边界；仅真实 Manifest-owned request/binding 证明旧请求身份，读取当前 generation 的 canonical request receipt，不遍历历史 binding。上面的四项真实临时项目用例验证拒绝与兼容两侧。

第二轮目标 HEAD `15732cdc2707c002ff9cf17a129f770800f14e63`，21个文件的 manifest SHA `8550f56f33ff4ec6fdf4c0d62c7794bbb4c20aa90b4739d0608b74a1e2e9d369`，reviewer 核验前后目标无漂移。确认 `SPF-002`：普通请求能借 compiler/3 或未知版本跳过 fresh guard；现要求 v3 必须有真实 preserved-source 并精确重编译，未知版本拒绝。确认 `SPF-003`：旧 QA 映射不能只绑定路径，必须封存当前 intent 值身份；已新增必填 intent 指纹，重封装 request/recipe 不能代替 QA 作者重新审查。新字段仍属于未发布的新 mapping/1，不迁移任何旧 schema/request。新增 stale-map 与 QA 重新封存两条标准 prepare 用例后17项 fidelity 测试通过；另新增 ordinary v3/unknown canonical begin 零写入拒绝及合法 source v3 exact recompile，用例总数7项。

修复后的 input-control、semantics、execution、provider-wiring、voice、source-prompt、performance-authoring 选测142项通过。兼容性扩测发现新 fresh guard 遮蔽原 source `ValueError`，已改为先复用原 `validate_preserved_source_request`；不改旧失败测试来放宽契约。最终15项受影响测试通过，包含7项 durable cases、v4 篡改 typed failure 和7项原 source failure cases；此前扩测其余76项通过。这些结果按测试对象分别报告，不累计重复执行数。

第三轮（默认最后一轮）继续同一 `reviewer_xhigh`：HEAD `15732cdc2707c002ff9cf17a129f770800f14e63`，21文件 manifest SHA `345b7274a2f08aefb57ea1a3ee6d4200fb04297a71c1b1a940c632b8f7b33034`，tracked patch SHA `59b611c1c31e5900486f2c445c52ec7c7e1e59fd66c4c08d81541bd9b7e46737`；临时审查材料位于 `/tmp/ai-video-shot-performance-fidelity-review-r3.json` 与同名 `.patch`。reviewer 实际做只读进程内复现和 source/test 审查，初末21文件/spec/patch/HEAD一致，finding set 为空，三个既有 blocker 的拒绝与兼容两侧均获核验。Parent 以对应 focused evidence 关闭该目标的 SPF-001/002/003；该时点未增第四轮或第二 reviewer，审查不代表真实媒体或完整 Harness 验收。

随后 Parent 交付前 hash 检查发现新的并发改动：`generation_execution.py` 的 `_validate_binding` 新增28行 qualification one-submit scope guard，本轮 helper 和 source 校验均未被改写；其余20文件、spec、HEAD仍匹配第三轮目标。该非本轮改动保留，不覆盖、不 stage。第三轮“无漂移”仅指 reviewer 的初末时点，不能冒称覆盖后来的完整文件。Parent 明确有限扩展1次针对该外来差异及其交互的复核：历史已消耗3轮，仍用同一只读 reviewer，不重审无变化文件，不自动第5轮；若继续漂移或出现未解决 blocker，则停止完成声明并报告实际剩余条件。扩展依据是第三轮后真实并发漂移，并非重复争取相同 findings 的认可。

有界第4轮 manifest SHA `eabcfd12583a5b87ed2e99017c1983c2dbde32fa995ca4cbc2782088e15727ef`，patch SHA `0ff576ec7138e5d6c46549d102090acb259a71abaa806e8142893bf1f1c0302e`。在该 source 时点重跑17项 fidelity 和7项 durable，共24项通过。随后另一项并发改动又在 `video_generation.py` 增加 qualification candidate promotion guard；本轮原 expected-request recompile hunk 保留。reviewer 初末均检测该文件预期 SHA `41bb270a117ff319f10e2354969bb8612c91c003d595c2d440851bf02a470d90` 与实际 `a788de5bcea55f85c5e4d329bf46b33e30a6d084dd48c491f763e6fbdce73ce2` 不符，按限定范围停止，新增 `SPF-004 / blocking_candidate`。Parent 判定 `CONFIRMED`：这是最终集成证据漂移，不将其写成本修复新发现的功能漏洞；当前组合的 required review 未完成，qualification delta 也未审结。不自动开始第5轮，不修改或回滚另一任务的代码。最小恢复条件是两份共享文件的 writer/交接稳定后，再按既有 Risk Gate 封存当前实际组合并明确剩余验证与审查；当前不得宣称完整工程修复完成。

## Media And Publication Boundary

本轮没有在用户项目新增 Provider POST、媒体或 Production mutation，费用为零；工程测试只在临时 fixture 中创建合成素材和状态。旧2.0失败、Fast `validate/EVIDENCE_GAP`、16项raw/38项FinalOutput、历史计数和媒体保留。自然表演和全场风格没有因代码接通而取得新 PASS。

完成前经现有 `ProductionStateCommitter._read_manifest` 只读核对：当前项目仍为 Project36、Manifest254，Fast attempt 仍 `running / validate`，有1份 experience、无 quality rejection。没有用旧文档状态代替当前磁盘状态。新试片仍须先沿原 owner 补齐同 bytes 的审片证据并解决现有 STOP，再封存当前 v4 作者输入、参考审查和有限预算/permit；不能把工程修复当作跳过这些前提的权利。

按已批准规格的先交片审片顺序，尚无新的真实试片及用户效果认可，完整工程 suite 与 commit/push 暂未执行；本记录为本地工程候选状态，非发布或 Shot/Final Acceptance。若进入真实验证，须先解决既有证据/状态前提，再重新封存当前输入和有限单元，仍为至多一条短镜头、一次 POST、零重抽。

当前范围为共享工程候选及其 focused 兼容性证据；SPF-004 使当前组合的最终集成复核仍未完成，不能报告修复完成。真实自然度改善、完整 Shot/成片与 publication 均未验证。23个本地文档链接路径检查无缺失，documentation contract、agent rules、policy audit 均通过；第三轮目标的 owned whitespace 已通过，最后全量hash检查实际发现上述并发漂移，不伪报为最终无漂移 PASS。没有完整 Harness receipt。矩阵、baseline、其他 staged/dirty 改动及历史媒体未被本轮覆盖。

`record-ai-video-session`：record。自动 `distill-ai-video-learning`：`no_candidate`；本轮为工程及作者流程修复，没有新增独立质量实验，不创建占位 Learning Claim，不修改全局 memory。
