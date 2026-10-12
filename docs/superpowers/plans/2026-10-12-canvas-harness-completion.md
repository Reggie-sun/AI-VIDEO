# Canvas Harness Completion Plan

## Goal And Scope

沿现有 Reusable Canvas Production Harness 补齐数据入口、连续性交接与剪辑接点检查。
本轮只做工程与离线验证，新增付费视频提交为零；历史 Seedance 7/7 保持。
原 spec 的 AC-7 仍要求真实 exact 成片与用户完整听看，不能以本轮测试关闭。

## Ownership And Contracts

用户选择 A，将 `canvas_production.py` 及其前序 recovery group 和对应 tests 交本轮接手；
保留并整合全部前序修改，补通唯一 committer 的公开 retarget 入口后验证完整快照。
其他 Grok、旧 spec/plan/baseline/record 保留，不纳入本轮发布。
Native Codex 为唯一 writer，受管 Kimi 只读核对现有 sequence 接缝，不拥有验收。
当前 working tree / main，不创建 dedicated worktree。

来源保留模式自动封存原文与完整素材职责；Director 数据只整理来源与声明缺项。
生产顺序沿 Storyboard / sequence owner；显式 composition_order 只投影到 CompositionSpec，
不自算帧或采样，不复制 timeline。中间参考来自真实 accepted source，不能伪装为尾帧。
真实 holdout probe 发现重复 chip 与 tray-only 普通参考；在原 preserved-source owner 增加
显式 `/2`：相同 slot/asset 可重复表达，但 exact material role/bytes 必须一致；physical input 去重。
保留 `/1` 原有 strict semantics/serialization，`/2` 每份 tray-only 材料仍绑定原画布 resource。
原文普通图号的适配由显式 `reference_aliases` 声明原 tray slot，再用 native compiler index 改写；
原始 text parts 不改，alias 与 selected materials 同属 immutable Shot revision。
花园/零号档案已用于定位该缺口，转为 development，不再计为最终 holdout；再次冻结后另选两份。
逐镜 exact Gate 全 PASS 后才推进，unknown 不重试。Registry、Manifest、committer、graph、
ResolvedTimeline、HyperFrames、paid owners 不变。
中间状态的后镜必须在既有 selected generation QA inventory 中覆盖同一组 checks，
并消费真实后镜的 canonical generation observations；source-frame Gate 不能替后镜验收。
交接必须先有 approved state_reference 计划；缺计划在提取/MCP/Registry/Manifest 前阻断，
避免临时检查与后镜 QA requirements 脱节。来源拒绝使用 typed occurrence/field 诊断，
原对白/动作/摄影扩写仍拒绝，错误输出不回显原始数据或 traceback。
普通 nominal 输出的剪辑长度接通已有 `content_driven` duration policy，由采用视频及显式 trim
决定实际帧数；`seconds` 保留生成时长提示，min/max 仍约束实际时长。显式 `fixed` 不放宽。
冻结后的《逆行之舟》暴露 URI/history-material 图片引用未被承认的缺口；在原 source owners
接通 exact URI 的外部 image inventory 和显式本地 PNG 绑定，不生成图节点/连线，不丢失原 descriptor。
同一 URI 的实际 bytes 仍由 Registry 测量，引用不自动下载、不认定采用。该画布转为 development，
需要另一份未参与修复的 holdout；《益达竞速嘉年华》保留为独立数据验证候选。
原文 `图片N` 的显式 alias 与 `图N` 同样按原 tray slot 重编号，不猜标签的语义。

## Major Milestones

### M1: Reusable Data Entry And Preservation

新增 `canvas_project_data.py` 与 shared operator CLI，消费 source/selection/direction/本地素材选择；
通过原 inspection、authoring、Registry owner 生成内部身份。展示原文与技术适配 diff，
入口不得加载故事代码、凭据或自动提交。

### M2: Continuity And Edited Audio

在现有 application / sequence / image owners 内补齐实际输出参考准备，区分普通中间状态参考与
terminal conditioning。composition_order 保留所有 occurrence 的独立 Shot，支持插入镜头；
原生 WAV 只从 exact accepted attempt 登记。声音 trim 与视觉 trim 对应，错版本与错接点拒绝。
剪辑接点材料由 resolved timeline 派生，实际 required continuity findings 缺证或失败停止交付。
通过 composition owner 解析 content-driven 主视频区间；不填充缺失末帧，不复制 timing 规则。

### M3: Executable Verification And Holdouts

覆盖 accepted-source、直接接续、换场、插入、trim/native audio、missing/stale/unknown/replay 与
canonical graph 失效。冻结共享代码与规则后，再选择两份未参与设计的独立保留画布，
只通过数据入口验证；失败如实分类，不能把 development 机魂或 synthetic fixture 当真实 holdout。
离线 Provider / renderer proof 与真实声画 proof 分开。

### M4: Completion

更新可用示例、操作说明与 matrix，运行 exact owned staged Harness / fresh receipt，
按 SUBAGENTS.md Risk Gate 裁决适用独立审查；记录当前结果、AC 状态与最小后续实测单元。
按完整 owned paths 提交、push main、核验远端 SHA。

## Self-Review

AC-1/6 对应 M1；AC-3/4/5 对应 M2/M3；AC-2 对应冻结后的两份独立画布。
AC-7 本轮明确 NOT_EVALUATED。来源视觉接续确认不转移到新生成 7→2。
默认480p与既有 nominal_seconds 有界末帧规则保持；显式精确时长不放宽。
