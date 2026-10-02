# COCO / Nosha Local Feedback Read Recovery

## Goal And Evidence

继续同一实际出片任务的第七known fetched视频反馈，不等待已定位的Source3fd指数重复读取消耗数小时。Reader修复Source`c262073`已完成251 focused、12 exact direct checks、同target双独立审查及Parent acceptance；actual只读standard loader25.38秒、Manifest211不变。旧进程仍持有已import的旧reader，不能以磁盘更新假称其已加速。

独立source mapping及Parent源码复核表明：`record_feedback.py`的Gate seal在presentation callback内、`record_attempt_evaluation`前创建；其没有Provider call或activation。唯一durable feedback publication在原committer `record_generation_experience`：先immutable experience artifact，后atomic Manifest pointer；helper sidecar更晚。因此“任何Gate seal都禁止有据local-read recovery”将本地raw证据文件等同于已发布feedback，过重。本spec窄 supersede [reader spec](2026-10-02-paid-budget-read-traversal.md)仅有关“Gate必须未seal”的恢复条件，不降低未知结果、安全、付费、QA或canonical ownership。

## Scope And Recovery Contract

Parent sole writer，仅新增run-local恢复helper/tests及本spec/plan；无Product Source/schema/API变更，旧Gate/raw/media/消费/proof/preflight refusal不追改。只操作原exec session37177中owned PID4086143、已封Linux startticks40566028及exact `record_feedback.py --technical`命令、当前UID；以Linux pidfd固定这个进程实例并发送全部信号，API不可用则拒绝，不按数字PID发送signal、不管理其他进程。

首个signal之前必须exclusive create/fsync控制intent，并fsync其目录。两个并发invocations只能一个claim；unfinished/partial intent同样消费单次控制预算，后继不得再次signal。最终receipt通过own temporary file/fsync/atomic replace保存；这是任务恢复证据，不是Product Manifest写入。SIGSTOP及SIGINT前保守标记可能发生的阶段，异步异常仍须通过已绑定pidfd恢复被暂停的原进程；SIGINT尝试后异常一律unresolved，不误报零写成功或preflight refusal。

必须先暂停该owned进程，确认停止状态，再通过当前已reviewed Source的standard `load_production_project`完整核验current project/QA/attempt/fetch。当前attempt仍known paid accepted/fetched/running、没有experience或quality rejection；当前experience目录所有entries必须恰好对应Manifest已严格重开的旧pointers，不得有orphan、temp、symlink或未知entry。Gate seal可以存在，但必须匹配旧exactGate及MP4/QA/request；它仅是保留的raw前置证据，不当成durable feedback或接受。

冻结后canonical state、full ROOT及原unit全部durable文件/链接identity、bytes前后必须一致；仅在确认零feedback publication、零未决artifact后才SIGINT并恢复执行以交付中断，确认旧进程结束、再次standard load及完整bytes等价。任一前置失败时恢复原进程，不进行fresh feedback；停止后出现差异/已写pointer/orphan/缺证则标unresolved并停止，禁止重复登记或收养orphan。恢复helper只写自身run evidence，不直接写Product Manifest/experience/proof；MCP callback产生的process-local一次性proof随旧进程结束，不是Provider permit。

成功只证明known zero canonical feedback write interruption。随后独立fresh invocation仍通过原`review_generation_attempt`/controlled verifier/one-use evidence proof/committer，对同一MP4及QA重新technical记录；新analysis保留旧raw，不删旧seal或任何输出。唯一remote第七submit/fetch不重复，没有新Provider permit或付费效果；完成technical后按原analyzer/mixed abandon路径继续第八修复。若旧进程在暂停前已发布pointer，则此零写恢复拒绝，改为原owner strict replay核验，不重复record。

## Verification And Self-Review

用标准fetched fixture验证空pointer+无orphan才允许，已发布feedback、孤立/未知entry、staleGate/QA/media及state变化拒绝；所有tests只在tmp_path/fake transport和test-owned child，绝不控制actual任务PID。真实Linux signals覆盖成功中断、preflight拒绝后resume、SIGINT期间写入变动后的unresolved/禁止repeat、错误命令/startticks零signal、STOP/INT成功后立即异常、helper突然退出后的durable fence、并发claim及旧pidfd目标死亡后replacement不受signal。file/symlink同bytes换inode仍须inventory不同。helper immutable snapshot包含Source/spec/plan/tests/verification及旧Kimi失败fallback，T3双独立read-only审查后才真正执行。预算一次owned local recovery attempt、pause/read90秒上限、无自动retry；前次拒绝/诊断/审查消费保留，canonical Harness=null（无worktree）。Parent self-review：恢复判据使用actual canonical publication而非seal旁路，零写证明失败即恢复原进程；unknown不重试、所有remote消费保留，无用户额外approval。首轮双review的fence/PID/异步窗口blocking findings均CONFIRMED，修复后重验并对同一新target双re-review；不重置审查预算。
