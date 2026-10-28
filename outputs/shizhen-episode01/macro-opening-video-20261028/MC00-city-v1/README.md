# MC00 Local Authoring Preparation

## Current Status

本目录仅为Parent委派的本地准备草稿。选定的技术目标为`seedance_2.5`、`first_last_frame`、20秒、480p、16:9、原生声音。没有创建run、平台节点、上传、quote、attempt、paid authorization或one-use permit；不能直接执行生成。

`row.json`保留rich camera intent及尚未审定的`conditioning_compatibility`，其空值是显式阻断，不是可执行的production request。禁止伪填全True、删除rich camera intent或改成其他模式绕过。Parent须通过现有owner裁决首尾尺度／路径等条件及实时profile后再作canonical准备。

## Source And Actual Inputs

- 首帧：`referces/shizhen/macro-opening-20261027/MC00-photoreal-20261027/02-eave-start-v1.png`，SHA `38af8b4fa48bba43acc98df2740367669290b3c257f1e2b7c917890dd7fb9b61`。
- 尾帧：`referces/shizhen/macro-opening-20261027/full-opening-references-20261027/MC01-normal.png`，SHA `a2cef0e9ff42796e09e72105bb04ea336149b4551a20dc767ffdd3179910eeed`，来自已认可市政片第0帧。

依据为修订`59e80dd`的MC00方案A，当前分镜字节hash保存在`data.json`。城市展开／下降图及本地连续预演只供作者审查，不进入本次mode3的actual inputs，不把mode3首尾帧与mode4多模态混为同一请求。

`data.images`中的node/resource名称仅为director-declared本地素材标签，不是平台已创建节点，也不授予平台或Production写权限。`reference-*-source.json`分别保留内置生图来源与exact市政视频第0帧派生依据；前者不冒充Seedance原生图，后者不冒充新builtin生图或把原片接受继承给新MC00。

## Files

- `native-prompt.zh.txt`：380字纯中文实际正文草稿，无首尾素材marker，无中间图虚假引用。
- `row.json`、`data.json`：符合现有Canvas准备形状的Shot、GenerationIntent、两帧素材、七类观察与原生正文片段映射；当前兼容性为空，整体projection应拒绝。
- `conditioning-review-pending.json`：不可自签的首尾尺度及可达性条件。
- `live-profile-required.json`：尚缺的实时account/project/node/benefit/quote及新attempt输入清单，不包含假值或新授权。
- `prepare_local.py`：只在本目录写准备材料；不创建run。
- `validate_preparation.py`：只读当前素材和task数据，用现有`prepare_canvas_png_assets`在内存核验，确认整体projection继续fail closed。

## Validation

从仓库根执行：

```bash
PYTHONPATH=src python outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v1/prepare_local.py
PYTHONPATH=src python outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v1/validate_preparation.py
```

离线结果归`offline-validation.json`，只证明图像来源／输入形状／intent结构及拒绝未审兼容性的行为，不证明真实路径、模型服从、声音、尾帧像素或接点通过。480p试片不能宣称1080p原片像素精确匹配；方案A最终须按exact声画检查位置、门速、车流／雨线、工人姿态与声音，接缝只处理MC00一侧，MC01及B6原片不改。

## Parent Integration Boundary

新scope拟最多1次submit，历史宏观6次known保持，旧下楼／推门paired上限7不挪作本镜头额度。1500CRD仅记录旧sealed operator per-call配置依据，不是本目录签发的新预算或平台quote。Parent须重新绑定当前真实profile、native mode config、quote、reservation、egress、durable intent和one-use permit。建议新root为`runs/shizhen-macro-opening-20261028/MC00-city-v1`，新身份不得从旧MC03脚本复制。

本子任务不执行bootstrap/start/submit。后续仍沿现有Canvas→GenerationFeedbackOrchestrator→ProductionStateCommitter／VideoGenerationService→JimengVideoProvider／JimengBrowserTransport，不新增执行器。旧MC03 FAIL保持，任何UNKNOWN停止，不重试、不换工具。Parent负责集成与最终verification、记录及commit。
