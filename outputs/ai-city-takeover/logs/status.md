# Current Status

更新：2026-10-30。取代旧的“暂停于 dev2 / dev3 未渲染”状态；历史决定保留在 `decisions.md`。

- T01 已收尾为横版引擎测试候选 **dev7**，1920×1080、30fps、300 帧；不是正式 IRIS MV。审看：http://127.0.0.1:8767/phase1-t01/review/ 。
- dev6b 的一帧计数、两帧标签停留已修复：dev7 实际 f181–194 有清晰红1/HUMAN，f195 同步变白0/AI。导演在展示后回复「可以」，按T01测试片认可记录；Agent自身的完整原速观感及听感仍 `NOT_EVALUATED`，不伪称已替用户聆听。
- dev7 本地 QA：11/11 事件 ±1 帧、规格通过、未检出闪烁/突跳/strobe/离群帧。1 与4 workers 渲染所得 MP4 SHA 完全一致；音频与 dev6b 解码后相同。报告：`../phase1-t01/qa/dev7/report.md`、`render-regression.json`、`codex-independent-review.md`。
- 正常速度播放器自动化：300 帧、0 掉帧、无播放错误，10 张关键帧均加载；这是播放功能证据，不是人眼/人耳接受。报告：`browser-playback.json`。
- IRIS：CF 身份组、命名和 ID7b 已完成；动态身份一致性、真实对嘴仍待验证，不重复生成身份图。
- EP01：选题与歌词已获认可；一手事实核验见 `../ep01/fact-check.md`，可审阅导演草案见 `../ep01/storyboard-draft.md`。草案未获分镜/参考包认可，不构成 `preview_approval`。
- 歌曲阻塞：本次只读 Suno `list` 返回6首，最新仍是10/25，没有 IRIS EP01。导演此前选择在官网生成；真实歌曲、take 选择、逐字时间和最终 beat map 尚缺，不能伪造对嘴/字幕或继续付费视频。
- 工程验证缺口：Harness exact staged `focused` 已尝试，因本 Pilot 路径无精准模块映射退出2，未执行 suite、未创建 Harness receipt。记录：`../phase1-t01/qa/dev7/harness-focused-invocation.json`。未降级规则或冒称 full 回归。
- 本次新增付费消耗：**0**；Suno/Seedance 没有新生成请求。历史账本保持不变；CLI 余额只读为2470，不据此推断本任务历史扣费。
- 发布：仅本地候选。导演已认可T01；最新提交阻塞为另一会话尚未提交的共享门禁/fixture迁移（下方新节点取代早期policy审计阻塞），暂未 commit/push；没有上传或发布，没有推进 Production 生命周期。原有并行改动保留；仅取消本任务三个文件的临时暂存，其他会话当前的暂存保持。

下一步：按导演指示「还没生成，先完成测试片」及后续「可以」完成本任务工程检查；EP01 延后，取得 Suno 歌曲/链接后再分析真实时序，定稿参考包并走原有付费、逐镜和合成 Gate。Phase 1.5 的 Production 接入仍待测试片 GO，不把 Pilot 当成正式管线。

## Post-Acknowledgement Engineering Check

- 原共享 index 有另一会话的staged代码/规则，未修改或夹带；采用verification-only clone封存99个本任务路径。
- Full Harness 已实际运行，前三项scope/docs/agent_rules通过，policy_audit_check因基线已存在的dotenv_source.py、preview_approval.py及dotenv测试缺映射而失败，其余检查按Harness原规则停止。三文件与原HEAD的SHA一致，本任务未改它们。真实receipt副本：`../phase1-t01/qa/dev7/harness-full-20261030/receipt.json`；范围及基线对照：`full-verification-summary.json`。不将该副本证据冒称原共享index验证通过。
- 工具独立review发现的短音频窗口越界、QA失败退出码、可变参考图identity问题已修复；9项精准测试通过，独立复审0 open issues。证据`tool-boundary-tests.json`、`tool-code-review.md`；已认可dev7媒体未改。

## Clock Recheck And Proposed Mapping

- 新增7项运行时回归发现并修复带歌曲offset的拍点浮点边界；9项工具测试仍通过，独立复审未发现新增阻塞。
- 新源码重新build并单次渲染，MP4 SHA与已认可dev7完全一致；新QA依然11/11 ±1帧且全部技术项通过。新证据`../phase1-t01/qa/dev7/clock-boundary-recheck.json`与`../phase1-t01/qa/dev7-clock-recheck/report.json`；原source identity仅保留为历史。
- 当前工作树policy audit已通过，修正来自另一会话尚未提交的共享policy改动；本任务未写该文件、未改其暂存。准备了增量`proposed-harness-mapping.patch`（2个精准check和1个Pilot分类）及包含既有修正的`combined-policy-proposal.patch`，只在verification-only clone验证，不能冒充已应用。

## Latest Verification Stop

- 精准映射仅在独立验证副本试用，主工作树policy与index未改；focused的Node7项、工具9项及Harness324项全部通过。
- 关联检查先通过diff/docs/agent_rules/policy_audit、runtime boundary、Node/Python与task architecture；随后`agent_rule_invariants`中的旧`test_close_retains_exact_request_history_budget_and_replays_without_writes`失败（43 passed、1 failed）。因此依原Harness停止，未继续proposal full，未伪称全量通过。
- 同一失败测试在包含另一会话staged迁移的当前工作树上直接诊断为1 passed，证明修正尚在未提交上下文；诊断不是本任务immutable closure receipt。另一会话的preview-approval-focused-r3仍在运行，未接管或重写其共享policy/fixture。
- Python工具回归已从`motion-kit/tests/test_tool_boundaries.py`移到标准`tests/test_motionkit_tools.py`，以便full pytest真实收集；9项测试保持，通过新证据`tool-boundary-tests-r2.json`。Node测试单列check，未假称被pytest覆盖。
- 当前证据：`../phase1-t01/qa/dev7/mapping-proposal-result.json`、`mapping-proposal-focused-r3/receipt.json`、`mapping-proposal-related-r4/receipt.json`。增量映射补丁与合并预览已备好；需先由原会话提交共享门禁修正，再在无同文件冲突时接入本任务映射。
- 当前已认可MP4不变，正式MV与付费生成未推进。阻塞解决前不commit/push、不夹带他人的22个staged路径。
