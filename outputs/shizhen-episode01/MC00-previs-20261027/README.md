# MC00 City Layout And Continuous Previs

## Scope

只为已认可的MC00路线制作本地空间与相机参考：屋檐滴雨近景、越过外转角揭示城市、沿同一主路缓弧下降、街面减速并交给钢索和市政工人。明确切入MC01；不把MC01–06或B6合成一个长镜头。不提交模型，不激活Production，不改变楼梯FAIL。

用户本轮追加“先不要开始生成视频,生成之前给我看referces”。当前阶段因此只交静态参考；Blender连续视频也未渲染。参考入口见[静态参考页](../../../referces/shizhen/macro-opening-20261027/MC00-city-layout-20261027/index.html)。后续动态预演和正式生成保持未执行，不把静态图认可推定为模型准入。

## Build Plan

使用Blender 5.2.1 headless、独立场景和最小体块。城市地理是新的导演设计，单位米、Z向上，主路沿Y轴，市政铁门沿X轴。屋檐建筑位于道路西侧，住宅在东侧较南处，站棚在住宅以北、市政入口以南；高层远景在北侧。尺度只是本次可复现设计，不是从单帧测量所得。

起幅建筑14×18×18米，旧住宅10×14×12米，四车道14米、路缘与人行道各自独立；站棚6米长、2米深、2.7米高；门宽8米、高3.4米；工人为1.76米静止proxy。工人黄色安全帽、深蓝工作服只指示来源造型，不能代替已生成工人的身份图。沿MC01实际第0帧保留左侧工人/控制盒/绞盘、右侧门/限位、右前方回转滑轮和双索关系。不得用早期单直索文字替代实际帧。

连续摄影按24fps、固定28mm、16:9设计，静态图1280×720。初版18秒的节点设计已修为20秒，预留末段右移与减速；不是模型时长合同，也未以加速适配15秒上限。起始2.5秒视线方向固定，让位置横移承担揭示。相机位置与方向使用同一份节点表，逐帧烘焙连续曲线。工作灯始终亮，门、工人与控制盒静止，不提前表演按停或异常。背景车辆和檐口水滴仅有动画设计，尚未渲染动态视频。

## Reference Roles

- `anchor/MC01-frame000.png`：exact已认可市政剪辑第0帧；负责设备拓扑、观察侧、工人服装、灯态及构图方向，不证明城市位置、工程尺寸或MC00动态。
- `anchor/B6-frame000.png`：保护文件第0帧，只观察站棚外形类型；不复制人物/事件到MC00，不证明新城市地理已获认可。
- 城市总图与相机轨迹：负责新设计中的位置、尺度、遮挡、观察侧，不是正式美术图。
- 连续clean MP4：负责相机运动和信息显露；无字幕、无隐藏切镜、无静帧延长。颜色、proxy、灯光与简化雨滴均需在最终生成中替换，不能原样继承。

## Reproduction

从仓库根目录执行：

```bash
blender -b --factory-startup --python-exit-code 1 -P outputs/shizhen-episode01/MC00-previs-20261027/build_previs.py -- --stills
blender -b --factory-startup --python-exit-code 1 -P outputs/shizhen-episode01/MC00-previs-20261027/audit_scene.py
python outputs/shizhen-episode01/MC00-previs-20261027/make_reference_review.py
```

源文件、轨迹采样、必要视图及最终exact媒体身份与观察结论见本目录后续verification。此处不授予真实视频submit、预算、permit或模型服从结论。

## Current Evidence Boundary

源文件`MC00-city-v2.blend`、`build_previs.py`、`camera-samples-v2.json`可重现同一空间和机位。`scene-audit-v2.json`重开保存的blend：480帧设计、28mm、一条摄影镜头标记；相机中心没有进入两处具名建筑包围盒，出索线同侧，起始2.5秒旋转速度为0。这些是设计采样，不能证明实际视频速度自然、建筑无动态扭曲、全程碰撞净空或遮挡次序。

首版静态诊断保留在`MC00-city-v1.blend`及`views-v1/`：近远注视目标造成首秒转头过快、末态滑轮出框、总图被摄影标记覆盖。v2分别改为normalized方向插值、末段右移及独立inspection渲染。native只读空间复核实际查看v2起幅/沿途/末态/总图；当前末态仍比MC01宽、门透视较平，只签同侧空间候选。住宅与站棚已有可见位置，但“依次显露”的连续遮挡效果尚未证明。

实际视频、MC00→MC01原速接点、声音、模型服从、人工接受全部`NOT_EVALUATED`。本轮新MP4、Provider submit、生图和付费调用均0。正式MC03楼梯FAIL仍阻止越过Gate提交后续正式镜头。B6与市政accepted源bytes保持不变。
