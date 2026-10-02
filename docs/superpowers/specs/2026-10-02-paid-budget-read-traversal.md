# Paid Budget Read Traversal Repair

## Goal And Evidence

在同一COCO/Nosha实际复现任务中消除已实测的历史预算验证指数重复，继续canonical质量反馈和有界生成，不省略任何预算/历史/字节校验。Source3fd251c6的单次standard loader只读partial cProfile在1385.133秒后由Parent停止诊断进程：`load_paid_provider_budget`14771次、execution binding7377次、总10.35亿函数调用，仍停在`verify_paid_provider_evidence`。该进程exit130，不是loader PASS；正在运行的第七technical进程未因此停止。原profile及CodeGraph/read-only mapping证据在`runs/coco-nosha-vidu-post-seventh-coverage-assessment-20261002-001/`。

## Scope And Single Owner

只在`src/ai_video/production/_paid_provider_project_reader.py`的既有reader owner内建立一次读取范围的budget DAG验证上下文：区分当前active ancestry和已经完整验证的节点，合并同一Manifest paid-evidence读取中active/Gate/reconciliation roots的历史前缀；public单budget或content-hash读取每次独立创建新上下文。不是global/object长寿命cache、第二ledger、状态写入或接受证据。相关focused tests、matrix、runtime baseline及本spec/plan同步；policy只追加新focused test的现有category/check route；不改Provider、committer/permit/clock/count/monetary policy、QA、Source inputs或公开schema/layout。

## Verification Contract

每次pointer访问仍resolve containment、nofollow读取当前raw bytes、核fileSHA/revision/contentHash，canonical内容身份校验先于任何复用。只对本读取范围内同一完整内容节点复用已完成的ceiling/quota ancestry验证，不缓存失败或未完成节点；当前active路径先于completed判断，保持cycle fail closed，content-hash派生重入共享相同ancestry，不能重置cycle guard。原extension metadata、完整prefix、first-derived snapshot、reservations/unsettled、target/prior binding、Gate授权、project/attempt/lineage/unknown检查都保持。Binding仍由原canonical loader重验，不增加全局binding/文件缓存。上下文不进入artifact/Manifest，不跨public call/项目/锁内重验边界，也不暴露可由caller注入的复用权限。

## Acceptance And Execution Recovery

标准committer/production fixture先RED复现shared-prefix重复验证，GREEN要求每个distinct budget node在一次读取范围仅完成一次历史验证；新call对已篡改的历史base/binding/derived bytes仍拒绝，pointer身份、cyclic `_seen`与同一次遍历间字节漂移仍拒绝。原paid/quota/ceiling/no-effect/production-reader相关测试及真实changed-path policy checks必须PASS，按repo T3对稳定exact snapshot双独立review；Kimi重复transport故障及既有消费保留，按SUBAGENTS native fallback，不拿旧review覆盖新Source。user禁止worktree，所以canonical Harness=null，direct检查如实命名。

旧technical进程已经import Source3fd reader，修改磁盘不会重载其Python代码；不声称该进程在新Source上执行。优先让其自然返回。若旧读取耗时继续阻滞，只有在held exact Gate未seal、canonical Manifest/evaluation/presentation chain证明反馈未提交，且安全停止该owned本地进程前后durable bytes相同的条件下，Parent可记录known zero-feedback-write interruption；保留analysis/profiling/进程证据和所有旧output，再以新Source的fresh standard loader重开同一MP4/QA并执行exact feedback。存在已写proof/Manifest、不一致或无法确认则不采用此恢复，禁止blind重复登记。此规则不取消/重复remote submit、不remint Provider permit，不将unknown当known。

## Self-Review

本修复来自当前实际read根因，保护历史完整性同时使真实媒体工作可继续；授权属任务内必要verification/recovery修复，无新增用户approval。空间仅限一个reader与可信行为证据，不泛化到所有models/cache。风险在memo误跨调用、未完成节点标verified或跳过pointer/历史边检查；测试和T3审查专门覆盖。完整系统AOCI治理仍dirty；压缩后fresh33-entry正文及host delivery确认完成，严格Challenge10/10，current_system_cognition_reliable仍false；不声称当前系统认知可靠，Source/CodeGraph/tests为事实。旧schema未完成尝试保留，不将本次成功回写历史。
