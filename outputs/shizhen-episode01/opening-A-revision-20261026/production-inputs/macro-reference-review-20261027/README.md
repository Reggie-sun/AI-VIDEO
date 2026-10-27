# Macro Opening Reference Review

## Existing Characters Reused

用户说明referces角色图已经有了后，直接复用character-packs-20261027中的董文慧身份底图；不重新造脸或补已有四视角。罗敏、高峥以已有雨站人物和B6实际入口为场次依据。闻素芬不出场。本轮早先灰褐外套母图仅保留历史，不替换原角色身份。

- [全部候选与失败审看](index.html)
- [独立审看板](index-board.png)
- [来源、用途、SHA、调用计数](preparation-report.json)
- [逐次状态图、实际引用与裁决](../../../../../referces/shizhen/macro-opening-20261027/state-attempts.json)

## Reference Task Mapping

| Shot | Current files | Status and gap |
| --- | --- | --- |
| MC01 | M01-v0、M01-r1、M01-r2 | 全部FAIL；门被要求向右但图仍残留左绞盘直连。未生成M02/M03 |
| MC02 | 尚无合格结构来源 | M03-D0/D1未生成，不能由失败设备扩图 |
| MC03 | L01-r1、L01-X | 静态候选；实际继承已有董文慧，浅凹已封闭；下行路径可定位，动态步速未验 |
| MC04 | L02、L02-O-r1 | 关门接触与向内半开候选；重复凹痕匹配仍欠清晰证据；L03因右手/把手悬空FAIL |
| MC05 | 无 | L03不合格，L04不继续延展 |
| MC06 | T01；原清单station-entry作T02；B6-exact-first-frame | 较远双人定位候选；真实动作接点、速度、时钟推进未评估 |

状态单图位于referces/shizhen/macro-opening-20261027，点击审看板中的图片可打开原图。干净单图无审看注释；T01保留原来源AI标识。第一版裂口、外开门、三版错误钢索及全开门悬空把手均明确保留为FAIL，不进入合格状态。

## Source Checks And Protected Work

原reference-manifest四张图片与三份去重原片全部可读、SHA匹配，四图均已查看。station-entry为两人在场；station-reveal是事后空位，不作MC06入口。清单入口来自原片第8帧，不冒充B6精确首帧。本轮另外从未改动B6抽取实际首帧，观察到时钟03:16:53；T01保留此状态作为静态模板，不能据此声称前置镜头的动态时钟或时间连续性已解决。

董文慧E02场次图的灰蓝外套、包、本与日光入口不作为本次楼梯动作输入；本场服装沿当前开场造型提案制作，身份始终绑定已有底图。角色包其他窗口更新了静态审看状态，原董文慧身份图SHA未变化，本轮未修改其文件。

## Bounded Attempts And Limits

共12次内置生图：1张早先未选母图、7次新状态尝试、4次已知质量修复。先两次修复，再在保留旧上限/消费后封存两次几何参考修复；无unknown、无自动重试、无新增付费Provider、视频或音乐调用，结算未暴露。几何参考为本地SVG布局示意，不是Blender或ControlNet执行证据；参考方法核对官方图像提示指南，不保证模型服从。

所有输入/输出SHA、实际参考顺序、提示词及已观察缺陷均保留。图包尚不完整，不是Production Registry、activation或验收状态；人物脸、门向局部成立不证明全开门接触或钢索力学成立。静态图不证明运动、声音、切点、节奏或完整成片通过。B6、片名字体、音乐、Registry和Manifest未改。
