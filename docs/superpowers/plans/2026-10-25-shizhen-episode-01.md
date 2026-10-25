# Lost Frames Episode 01 Production Plan

## Goal And Scope

制作原创都市灵异悬疑3D动画《失帧》第一集《消失的十一秒》，三至五分钟，故事、表演、连续性优先。用户指定 Jimeng Provider / `seedance_2.5`。Parent 串行创作与制作，仅委派只读 readiness 和适用独立创作审读；不编辑其他窗口已有 dirty 文件，不建 worktree。

## Owners And Files

- `docs/superpowers/artifacts/drama/shizhen-episode-01/creative-input.txt`：用户本轮完整原文及型号补充，保留来源。
- 同目录 `screenplay.md`：Story、Scene、Character、自然对白与人物知识。
- 同目录 `production-design.md`：身份、场景、道具、声音和参考职责。
- 同目录 `director-coverage.json`：唯一 ordered coverage 与 v4意图清单；不是执行时间线。
- 同目录 `shot-prompts.md`：从 coverage 导出的 selected-model 表达，不另立分镜。
- `runs/shizhen-episode01-jimeng25-20261025-001/`：本任务实际参考、exact profiles、canonical projects/requests、成本、逐镜证据和审片输出；未生成时不伪造媒体状态。
- `docs/record_for_agent/2026-10-25-shizhen-episode01-jimeng25.md`：有持久价值的当前 checkpoint 与最小恢复条件。

## Contracts And Acceptance

不设置台词时间戳；片段预算可变，按完整动作和对白留余量。Director coverage 不替代 ResolvedTimeline。Provider及模型固定，未有当前证据不换型号、账号或渲染路线。模型 `UNQUALIFIED` 时只走已有 qualification trial / development preview，不伪装 Production、P6或最终验收。所有状态通过现有 committer 和 standard loader。

关键戏剧证据是：店员的真实服务；消失与他人的遗忘；录像改写；多地不同日同刻缺口；妹妹身份与非实时警告；明日创建时间；原始像素已有的林序面孔。异常必须改变人物判断。禁止幻灯片、重复慢镜、表演截断、怪物扑脸和说明性世界观旁白。

先完成约30–60秒、4–8个连续镜头的原剧情 Pilot。封存有限调用单元、exact输入与当前积分上限，逐镜一次，零自动重试；每镜 MP4 落盘后显式 project-local video-analysis 全项核验，缺声义/unknown先补证或停，不提交下一镜。Pilot由用户实际声画审片给GO/NO-GO，未经GO不批量扩到整集。

## Milestones

### 1. Authoring And Feasibility

完成上列原文、剧本、制作设定、coverage和各镜提示词。按raw→inventory→coverage→实际prompt核对，运行现有 Director validator。Parent 自审因果、反转、十一秒数学、日期和镜头容量；独立只读创作审读针对因果/可读性，不以纸面意见代替媒体。

### 2. Representative Pilot

只读核验当前实际浏览器profile/account/canvas、native配置和积分，按canonical owner创建本任务空闲节点与sealed profile。按所需职责生成并查看最小参考图，再由现有Registry入口导入。完成首段生活→消失→困惑的4–8镜，逐镜gate与exact终态交接。合成原速带声Pilot并交用户；无法生成时保留已完成创作与实际blocker，不交伪成片。

### 3. Episode And Exact Review

用户Pilot GO后，沿同一模型、身份、空间、声音和有限单元扩展。准确的监控时间、属性与修复信息走现有图形/CompositionSpec；ResolvedTimeline独占时序。生成→逐镜媒体gate→完整声画剪辑→exact MP4独立审片；修复基础问题后再交整集。未知结果不重试，不删已满足目标。

### 4. Verification And Publication

静态/结构结果仅说明所验对象；电影与Human验收单独报告。遵film-first：先交审片，用户认可效果后再跑完整工程验证，按owned paths commit/push并核验远端main SHA。若当前只有创作产物且无可审媒体，运行相称文档/结构检查，commit/push仍须遵守当前项目验证契约；阻断明确报告。外部公开发布没有本任务授权，不发布。

## Current Assessment

本计划为Parent自审的执行边界，不是已完成制作的证据。镜头数与生成预算由最终coverage和当前native能力确定，不用数量代替剧情容量。用户brief与型号要求优先于历史经验和模板。
