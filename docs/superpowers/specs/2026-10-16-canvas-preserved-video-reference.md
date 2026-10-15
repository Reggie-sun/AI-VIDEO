# Canvas Preserved Video Reference

## Goal

让用户明确新增的本地白模视频沿既有 Canvas/Registry/Planner/H3 reference 模式进入一次 S01 修复，不改变原剧情或现有图片质量。

## Contracts

- 新输入保留原 text parts，新增有明确 provenance 的 video reference slot；旧 source snapshot、视频、QA和消费不覆盖。新白模属于用户新授权素材，不能伪称原剧本原有参考。
- 共享 source-expression owner 只扩展普通 video material 的 exact resource/asset/role/type/bytes lineage验证；subject、image、accepted-state replacement 的现有语义保持。视频只能是明确的 `video_reference`，不接受错类型/错hash/缺metadata/错slot/错来源。
- 同一原PNG bytes作为 appearance/scene reference，白模仅负责动作、布局、人数与摄影。R2V 不宣称 first-frame 强约束；原文及15项 QA保留，模糊暂不修，不能将白模材质用作最终质感标准。
- local reference资产准备不是新的最终renderer/timeline或Provider执行链。旧失败沿canonical abandonment封存NE和FAIL，新attempt最多一次METASO `MiniMax-H3` POST；S02不在本次新调用授权内。

## Verification

focused source/ref regression tests、exact Harness与Risk Gate；实际新输入编译、reference SHA/metadata/职责核对；白模自身画面与几何检查后提交；exact输出MP4必须显式MCP/原15项QA。UNKNOWN停止且不重抽。

## Self Review

任务内必要的窄输入适配已授权；不新增补充参考schema或旁路，不移除preserved-source验证。
