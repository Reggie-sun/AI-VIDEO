# Driver Selection Review

## Verdict

2026-11-05 只读调查。目标 bot `e86e4307-899b-4788-83c7-0466bbc9e3e7`、线程 `b6ae631e-7f11-4841-8244-6228716321b8` 的实际偏差可定位为：**调度层记录 Claude work5 额度受限，将该线程切换到 Codex，再由 Codex app-server 启动 gpt-6-astra / medium。** 这不是根据 bot 名字、事后默认配置或单独源码推断。

已证实的是调度层做出了额度接管决定并实际运行 Codex；**Claude 真实额度是否耗尽、额度判断是否过期、为什么候选最终选中 Codex，仍有历史证据缺口。c3 验收未通过，本报告不批准任何修复或验收。**

## Scope And Self Runtime

仅读取指定报告、目标及本线程白名单运行元数据、有关调度配置与实现。未修改配置、源码、状态或 Harness；未启动 Claude、插件、项目测试、hook、子代理或重跑。唯一主动写入产物为本报告。

本次调查自身运行不能由“Codex 执行｜High”名称推断，已直接核对：

- OMB thread：`6f5d637d-1092-485c-b8d3-39dccb2b00e1`；原生 SID：`01a1aaf9-3921-7df0-92d1-11523b44fb68`。
- `/home/reggie/.openmausbot/native/6f5d637d-1092-485c-b8d3-39dccb2b00e1.ndjson` 行7–8：`codex.app-server`，`gpt-6.1-sol`，`openai`；初始化响应 effort 为 medium，不能据此认定本轮实际 effort。
- 同日志行35：`turn/start` 显式 `effort=high`；`/home/reggie/.codex/sessions/2026/11/05/rollout-2026-11-05T01-10-22-01a1aaf9-3921-7df0-92d1-11523b44fb68.jsonl` 行10 `turn_context`：`gpt-6.1-sol / high`。本次实际模型与 effort 以此确认。

## Historical Evidence

以下均为本次直接读取；时间使用 UTC。通知只提取该任务的调度 activity，没有提取任务正文、对话正文或秘密。

| 时间 | 历史事实 | 引用位置 |
| --- | --- | --- |
| 09:03:40.849 | 目标线程创建；openedBy 指向 MausBot 的 `4384717f-33f1-4569-bfb3-449739f65fab` 线程 | `/home/reggie/.openmausbot/bots.json`，按目标 bot id 与 task.threadId 定位，`createdAt=1793869420849`、`openedBy`；这是当前保存的创建元数据，不是完整历史配置快照 |
| 09:03:40.942 | 同目标 bot/thread 的额度接管记录：from=`claude-3e4a5344-24ed-4475-91a8-6119dd8261ac / claude-opus-5-5 / high`；to=`codex / gpt-6-astra`，to 不含 effort | `/home/reggie/.openmausbot/limit-failovers.json` 行18–30，数组索引1；`at=1793869420942` |
| 09:03:40.945 | 同线程 activity：`recovery: Claude work5 hit its limit (resets 4:40 AM), so Codex took over.`，ok=true | `/home/reggie/.openmausbot/messages.db`，只读连接；messages 主键 `(thread_id=b6ae631e-7f11-4841-8244-6228716321b8, id=c221e302-3b72-44e1-9802-86333c67fde2)`，`at=1793869420945`、kind=activity、json.tool.name/ok |
| 09:03:40.960 | turn.started 的 provider 和 providerInstanceId 均为 codex | `/home/reggie/.openmausbot/events/b6ae631e-7f11-4841-8244-6228716321b8.ndjson` 行1 |
| 09:03:40.961 | Codex initialize 开始 | `/home/reggie/.openmausbot/native/b6ae631e-7f11-4841-8244-6228716321b8.ndjson` 行1 |
| 09:03:41.121 | thread/start 已指定 `model=gpt-6-astra, modelProvider=openai`，cwd 为目标私有任务目录 | 同 native 日志行7 |
| 09:03:43.464 | 响应确认 model、provider、medium 与 SID `01a1aaf3-1a4d-7a91-a13f-c29e6a6a7171` | 同 native 日志行9 |
| 09:03:43.591 | turn/start 未传 effort | 同 native 日志行29 |
| 本轮 turn | `turn_context` 再次确认 `gpt-6-astra / medium` | `/home/reggie/.codex/sessions/2026/11/05/rollout-2026-11-05T01-03-43-01a1aaf3-1a4d-7a91-a13f-c29e6a6a7171.jsonl` 行10 |

接管记录的 `resetsAt=1793882400988`，对应 12:40:00.988Z / Pacific time 04:40:00.988，与通知一致。该时间是调度层保存的预计重置时间，不是本次核验的供应商额度承诺。

当前 `bots.json` 中目标默认已为 `claude-5cbc8b72-f35e-4d67-bf0f-f992c2cd4a56 / claude-opus-5-5 / high`；目标旧线程仍有 `task.modelSelection={instanceId:codex, model:gpt-6-astra}` 和 Codex resume cursor。它们只证明当前默认与线程覆盖不同，不能倒推 09:03 的完整配置。历史 from 指向 work5，不能用事后号池实例替代解释。

## Implementation Correlation

以下为当前磁盘源码，用来解释历史记录对应的机制；未证明当时 Node 进程加载的完整构建与这些文件逐字节一致。历史因果结论主要依赖上面的同线程记录与实际运行，而非源码单独成立。

- `/home/reggie/OpenMausBot/server/index.ts:13876`：新 teammate 线程的 createTask 调用没有传 modelSelection；`server/store.ts:2189` 的 buildTask 只有收到不同于 bot 默认的显式选择才保存覆盖。正常新线程路径不是从派发者模型盲目继承。
- `server/store.ts:2037`：projectBotForTask 取 `task.modelSelection ?? bot.modelSelection`，解释为何旧线程 pin 可继续覆盖事后 bot 默认。
- `server/host/limit-takeover.ts:246`：heldAtStart 检查 engine/model hold 或 signed-out，存在备选时可在发送真实 turn 前拒绝原引擎；`server/index.ts:8466` 在 sendTurn 前调用。**符合“先切换后首个 Codex initialize”的时间顺序，但不能单凭顺序排除其他限额拒绝来源。**
- `server/index.ts:8593` 起选择备选；行8619–8631 保存 switchTaskModel、调用 carriedOn、写 activity、重新 startTurn。`server/host/limit-takeover.ts:216` 与行272–277 将同一接管写入 failover 和 recovery 通知。`server/index.ts:8803` 将 record 接到 LimitFailovers；`server/limit-failover.ts:109` 持久保存。
- `server/host/limit-takeover.ts:175` 的 backups 可从指定备选及其他合格订阅引擎中选择；行183只输出 instanceId/model，不携带 effort。历史 to 缺 effort、turn/start 未传 effort、实际 medium 三项相符。**这是 high 未随接管保留的机制解释，不证明历史候选最初有 high。**

## Confirmed Cause And Evidence Gaps

**已证原因：** 目标 Claude 选择被一次有明确时间、from/to 和线程绑定的额度接管覆盖，实际送到 Codex。不能归因为“名字错了”或“09:09 后配置错了”，也没有证据称本次通过了 Claude CLI 验收。

**假设，尚未证实：** 启动时采用已有 engine hold，直接在调用 Claude 前切换。当前实现和时间顺序支持此解释，但缺当时 hold 的产生记录和调度异常分支日志，不能升级为确定结论。

**待证项：**

1. 原 work5 的真实额度事件、采样时间和原始拒绝证据；不能把宿主通知当供应商事实，也不能推断换号池后可用。
2. 当时 engine/model hold、signed-out 状态与各备选 readiness、拒绝理由、顺序；无法确定 Codex 来自显式备用还是自动选择。当前配置不补足历史。
3. 当时加载构建、恢复设置与完整 candidate 决策轨迹；未核验历史部署映射。
4. c3 的 Claude init、原生 Read、自动 OMC hooks、真实 cleanup 输入根及共享副作用归属仍未验证。指定独立报告 `/home/reggie/.openmausbot/task-workspaces/3799c0ce-c96d-410f-b8ac-54f2ba3ef9bd/4384717f-33f1-4569-bfb3-449739f65fab/independent-runtime-verification.md:84` 起为参考报告，本次没有重新执行其全部文件系统采样。

## Minimal Recovery Proposal — Not Applied

1. 保留旧线程、SID、failover、通知和原始 c3 before/after，不重写历史、不清 pin、不删状态、不自动重跑旧任务。
2. 交独立审核后，由协调者核对目标当前默认及实际可用性；未来验收绑定 Claude driver 与期望模型，限定原生 Read 和既定 fixture。对“验证特定引擎能力”的任务，将跨引擎接管视为未评估并停止，不能由 Codex 结果继续签收；本报告不修改全局恢复策略。
3. 若现有调度入口不能在真实派发时保证引擎约束，则先标为阻断并审查最小约束方案，不能只改 bot 名称或默认模型。不要为本次恢复扩大成宿主重构，也不要关闭全团队恢复能力。
4. 获准进入下一阶段时，另开一次受控验收、另取新基线；先证实 Claude init、真实 SID/model/cwd 和原生工具，再核对自动 hook 与 cleanup 证据。偏离 driver 即停止且不冒充 c3 通过。

## Evidence Integrity And Delivery

读取期间散列（SHA256；当前可变文件的采样值，不承诺后续不变）：

| 文件 | SHA256 |
| --- | --- |
| `/home/reggie/.openmausbot/limit-failovers.json` | `107adcf3ca6a450a7472c80b111346a45df532c4b6e4c00e9c0af014af27d932` |
| 目标 native 日志 | `37d91d6228884535aecfbb34778e4102373020b7ad0ded69cfd8fc8a76446484` |
| `server/host/limit-takeover.ts` | `eb48be9f0b8a51346379e181ea6fa574b778a1d6489c69b3b08c26d0ef9eec1a` |
| `server/index.ts` | `fde2873b87cd7992fea6ebe892c705c0581a8eec13fe82a2e9b7ce1fd61ba553` |
| `server/store.ts` | `dbfdf5bfecc9f70584c73930b82fe379f622f2ec31c0760975fd4ce39c9d5c8e` |

未访问被拒绝的 assignment API 数据，也未通过 runtime.db 绕过该拒绝。messages.db 只查询目标线程元数据及指定 recovery activity；未提取任务正文。未使用其他 bot 的私有目录作为检索源；仅读取明确指定的共享报告。

这是宿主调度只读调查，非 AI-VIDEO 产品实现；报告本身作为此次交接记录，不另写项目 session、经验、规则或状态。不运行项目 Harness，不生成 receipt，不 commit/push。已检查本 bot 自动化列表：为空，无临时监控需停止。结论待独立审核，未自批。
