# Reference Replica Migration

## Scope

将 AI_daily `80abf28cf6558a72b622c1f034153e451f8a6ded` 的参考片复刻工具迁为 AI-VIDEO 的共享编辑工具。`8dcaf84` 提供录屏教程流程，`98ef686` 提供工具和范例，`80abf28` 固定口播对齐及共享边界的优先级。仅在迁移时通过 Git 读取来源。礼品卡范例保留历史输入、镜头表和交付配置，所有验证使用临时工程与离线数据。

## Ownership And Boundaries

| Surface | Owner 和放置位置 |
| --- | --- |
| 复刻流程与成片检查 | `.agents/skills/reference-replica/SKILL.md`。`.claude/skills/reference-replica` 使用相对 symlink。将工作规则写入 Skill，现有 matrix 和 skill routing 文档只登记适用边界和入口。 |
| Agentcut 原生剪辑 | `scripts/replica/` 持有时间重映射、轨道序列化、独立工程换轨与本地交付工具。Agentcut 项目持有 `layers.json`、场景与导出。`scripts/replica/agentcut-scenes/{news,tutorial}/` 提供两组组件及其完整相对导入。 |
| Production 剪辑 | `ProductionProject`、`ResolvedTimeline`、P4 `CaptionTrack`、HyperFrames 和 `ProductionStateCommitter` 按现有 matrix 管理。Agentcut 工具限显式独立的客户剪辑或参考复刻工程，拒绝写入 Production 工程。Production 需要采用外部素材时，走现有导入、校验和 composition 入口。 |
| 分段配音 | `scripts/replica/tts_run.py` 负责从已确认口播选择 exact `say`、组号和 MiniMax 参数。专用声音项目复用现有 standalone speech bootstrap 和 P4 API。MiniMax adapter、`ProductionStateCommitter.generate_voice_asset()`、Paid Provider Gate、Registry、credential supplier 分别持有当前职责。 |
| 听审和对齐 | 语义观察沿 [Audio Understanding](../../audio-understanding.md) 的 `audio_understand` 和可信 operator 接线。字词时序由本地 Whisper checkpoint 与 `align_lines.py` 产生，只用于 Agentcut。 |
| 本地媒体工具配置 | FFmpeg 与 FFprobe 用显式参数或 `PATH`，共用现有 FFmpeg 执行与探测约定。Agentcut 使用显式 projects root 或已登记的 `AGENTCUT_WORKSPACE`；录屏、交付和字体由调用者提供。 |
| 回归 | `examples/reference-replica/giftcard-jp/` 持有五份原始输入 JSON、镜头表和交付数据。`tests/test_replica_kit.py` 迁原 27 项 pytest；其余验收覆盖三份字节快照及实际 committer 的离线 transport 路径。`.agent/harness/policy.yaml` 持有选测。 |

## Resolved Conflicts

- Agentcut 独立剪辑符合 `AGENTS.md` 的渲染约束。其层文件只描述 Agentcut 项目。`ResolvedTimeline` 继续独占同一 Production 项目的时序，成片仍由 HyperFrames 输出，P6 和 Final Acceptance 继续经现有入口。
- AI_daily 的豆包 HTTP、凭据加载和手写计费账本替换为现有 MiniMax 语音入口。开发批处理固定使用测试用途授权。客户片执行须经可信 operator 提供实际许可、选中音色、exact preview 授权和预配置上限。本次使用 MiniMax 正式 metered gate，原有 count-only 开发批保持原用途与兼容性。配音工具按组号和 exact 合成参数导出稳定 attempt ID，同一声音项目承担累计预算与未知状态。提交前由 committer 持久化 intent，成功时只重开 canonical WAV，RUNNING、UNKNOWN、旧失败和产物缺失停止。字幕文字及段间隔可独立调整。MiniMax 当前支持的速率进入请求，历史表演指导作为编辑信息保留。
- 源流程的 `review.audio` 与单期发布目录由当前项目的审听入口取代。语义审听使用 `audio_understand` 的 exact SHA 预览和显式执行流程。本地词时序仅接受已存在的 checkpoint，保持无上下文提示对齐。客户交付只使用本地媒体操作。
- 路径和工程状态由调用者显式提供。范例拆条使用同一个临时 projects root 内的资产链接。源脚本的真实工程默认路径、破坏性刷新场景和同名覆盖缓存的做法改为显式路径、原子文件写入和版本化素材。
- 礼品卡轨道名、资源相对路径、旧镜头帧号、JSON 格式及历史数据均用于比对。交付部分改为由共享 `deliver` 读取配方，封面只从本轮打码复查已覆盖的素材选帧。

## Implementation And Acceptance

1. 在临时目录从 pinned commit 取原脚本、场景和范例，准备空 assets 及 `{}` 的主工程元数据。设置 `AGENTCUT_PROJECTS` 指向该临时目录，运行原 `build_layers.py parts`，为三份原始 `layers.json` 记录 SHA-256。将同样结构的另一份临时工程用于迁移后脚本，逐份执行字节比对。若需变更路径或命名，逐项核对字段及对画面、时序和字幕的影响。
2. 迁十个脚本和两套场景组件。共享构建保持 30 fps、旧新时间轴句锚、下一句起帧优先、原录屏有效源区间及拆条末句复用。录屏源文件经独立打码，红框必须绑定原页面的可见区间，交付 SRT 使用单独文件夹。Skill 持有完整口播确认、客户版式、打码与成片复查等工作规则。
3. 迁 27 项纯逻辑 pytest。用临时目录、fake transport 和仓库真实 canonical 入口验证配音 exact replay、pending/UNKNOWN、成功文件缺失、改稿只涉及改动段。录屏、审听、场景和交付的测试使用本地数据或已有依赖；线上账号、配音和客户成片观感留待实际制作时验证。
4. 注册精准 Harness category。对 exact staged snapshot 运行 `make harness-verify` 的 focused、related 两级，包含 task Architecture Gate 与 Claude adapter，验证 receipt。核对完整 diff，按本任务路径本地提交。用户本轮明确要求将提交留在本地。
