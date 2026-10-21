## Blender routing

按每 Shot 的空间、动作、接触与摄影目标及所选模型的输入能力，判断是否需要制作或复用白模；不使用白模无需申请例外。选用后执行[白模参考工作流](canvas-production-harness.md#per-shot-whitebox-reference)，核验参考并证明模型请求实际绑定了对应素材。

制作白模时先读 `scenario-blender-expert`；blockout/proxy几何/送视频模型渲染的playblast读 `scenario-blender-blockout`；staging/camera/shots读 `scenario-blender-previs-storyboard`，motion/timing/contact读 `scenario-blender-animation`，确需rig/IK/FK才读 `scenario-blender-rigging`。用最小proxy geometry表达目标，交付可编辑 `.blend` 和核验后的clean参考。原Shot画幅、镜头、时长及剧情优先于Skill默认值；动作guide须呈现连续动作，不能以定格storyboard冒充。

### Execution Channels

按任务选择执行通道，现有两个MCP职责互补，无需每次全部调用：

| Channel | Purpose | Selection |
| --- | --- | --- |
| `blender` MCP | 通过 `get_scene_info`、`get_viewport_screenshot`、`execute_blender_code` 检查及操作现有Blender会话 | 需要交互制作、视口观察或GUI操作时使用；先只读检查连接及版本，保留可复现脚本，不修改非本任务对象。 |
| Local headless Blender | 脚本建模、动画、批量渲染和重开核验 | 无需GUI的白模可直接使用，遵循expert的factory-startup、错误退出及版本检查；不要求先启动live MCP。 |
| `blender_agent_studio` MCP | `blender_version`、`blender_inspect_asset`、`blender_render_evidence` 提供版本、独立进程资产检查及标准视图证据 | 需要对应验证时调用；它不接管live场景编辑，也不代替exact参考视频及生成结果的QA。 |

`scenario-blender-*` Skills的制作方法按项目合同复用；其中 `scenario-blender` 的 `execute_python` 等专属工具不能直接当作现有 `blender` MCP调用。执行前核对当前工具schema，适用的本地 `bpy` 操作经上述通道执行；Scenario专属报价、生成和上传流程不作为白模前置条件，不因Skill存在而新增MCP或外部服务。

MCP工具可见不等于Blender实例已连接；连接失败须报告，未开始执行的普通本地任务可明确选择headless。写入或渲染请求timeout/UNKNOWN时先核对进程、文件及执行结果，不在另一通道盲重跑；不同时通过不同通道写同一资产。

Blender负责参考资产制作，不替代现有Provider、`ResolvedTimeline`或HyperFrames最终renderer。白模与工程检查不保证模型服从，仍须沿原逐镜Gate验收exact输出；不因存在白模能力而重做已验收素材或搭建新基础设施。
