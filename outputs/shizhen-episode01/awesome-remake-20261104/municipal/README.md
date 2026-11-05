# Municipal Offline Preflight

本目录是完整《失帧》awesome 重做版首镜的离线制作资料，不是成片。使用现有 `ProductionStateCommitter` 和 `scripts.jimeng_feedback_driver`，未导入或执行旧故事脚本。新 root：`runs/shizhen-awesome-remake-20261104/municipal/`。

已封存用户原话“那你再用这个做出来视频我看看”、现有导演 coverage 的内容 hash、用户看过的完整 storyboard-v2.png exact SHA。仅取第一、二格市政工人与设备关系作为软参考，不将宫格设为首帧；人物身份明确归 municipal-worker。参考包没有被声称为用户看过的独立干净首帧。

连续性：全新镜头，不拼旧片，无前镜接续；断电开关→绞盘仍转→钢缆连接铁门的因果是必须可见事实。轴线固定同一侧，低机位小幅右摇；六秒只是镜头时长，不承诺模型逐时间点控制。新原生雨声、机械声，无对白；调度新母带由后续制作处理。

离线 prepare：GENERATE_ONCE / executable=true。15 项 exact-input lint PASS，标准 project reader 重开成功，manifest revision 5，0 video attempt，未注入 transport/authorizer。此处 PASS 仅结构与输入绑定；模型表现、物理连续性、声画与用户观感全部 NOT_EVALUATED。

单次有限单元：最多 1 submit、0 retry，实际页面报价198 CRD，内部上限1500 CRD；上限不代表报价。仅 qualification，无正式激活资格。Live owner 还须按现有流程封存 paid preview、预算和一次性 permit，执行后逐镜 video-analysis 与用户审片，不得因本预检跳过。

风险：完整宫格会有其他格泄漏、分屏、编号复现风险；这次由明示排除约束作有界试验，代码接通不证明模型一定隔离。钢缆受力和开关断开均须动态视频核验。声明 continuous_physics，规划器对此给动作参考建议，不把静态宫格声称为动作轨迹证据。

`build.py` / `bootstrap.py` 已执行，禁止在 live 期间重跑：前者会改变封存输入，后者拒绝覆盖 root。`prepare.py` 只离线准备；`verify.py` 检查的是 submit 前状态，提交后不得用它伪造提交前证明。记录文件：`prepare-result.json`、`resolved-request.json`、`provider-preview.json`、`prompt-lint.json`。
