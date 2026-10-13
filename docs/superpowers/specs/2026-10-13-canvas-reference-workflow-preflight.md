# Canvas Reference Workflow Preflight

## Goal

把资产先行、逐镜接续的制作检查接入共享 Harness；在首镜付费前展示全部镜头的参考职责、
真实来源、未来状态依赖及准入证据缺项。用户已要求“写入harness，然后生成”。

## Contract

`canvas_reference_preflight` 与共享 CLI `preflight` 提供只读投影；`author` 同时返回该报告。
Source/Director/Registry/Manifest 仍是原 owner，不新增 lifecycle、receipt store、执行脚本或 timeline。
新项目先执行既有 author validation；resume 重开 immutable Director input，不能读取被修改的数据冒充已批准内容。
报告覆盖整个 selected sequence，保留原文、对白、摄影/声音表达、generation order 与 composition order。
每份引用标明职责、exact asset identity 和 provenance；未来提取的状态不得把 placeholder 当作已接受输出。
普通提取帧、Provider 返回尾帧与原始视频不是等价输入。源自同一 Provider 或有 synthetic 声明
不自动证明当前账号准入。报告始终将 Provider admission 与 actual quality acceptance 分开。
离线报告不得调用 Provider/MCP/credential supplier、创建 Production state、提取媒体或签 PASS。

## Scope And Boundaries

新模块只组装 report；shared CLI 在既有 service author validation 后暴露报告，不增加 service lifecycle 方法。
现有作者及 Registry validator 继续校验数据，resume 报告附带 canonical `position`。
既有 prepare/start/execute、paid guard、per-shot MCP、state extraction、trim/audio/HyperFrames 不改。
不为输出版权拒绝添加 blind retry，不把 accepted failed task 改作 known-no-effect。
不伪造 Seedream/trusted-original provenance；新 Provider 及视频参考 adapter 不能凭报告成为可用。

## Acceptance And Verification

测试共享 CLI 与真实 authoring fixture：完整后镜依赖、placeholder 标识、来源/职责、剪辑顺序、
immutable resume、零 runtime factory/写入/Provider effects，格式错误 fail closed。
运行相关 Canvas tests 及 exact staged Harness；工程结果不代签实测。
随后在当前《界蚀》数据和真实 STOP 上运行报告，只有材料链、canonical recovery 和有限单元齐备才提交。

## Self Review

这是可执行准备证据，不是“模型必过”门。未来参考未产生是正常依赖；准入未知不能伪装为禁止，
也不能伪装为 qualified。保留原零重抽单元；本修改不自行授予额外付费/新模型。
