---
record_kind: architecture_implementation
topic_id: jimeng-shot-prompt-timing
learning_eligibility: ineligible
---

# Jimeng Shot Prompt Timing Record

## Observed Failure

用户的即梦客厅戏「视频 9 (9)」实际请求 18 秒，服务器保存的提交提示词包含 9 个镜头，计划延续至 20.5 秒。同类输入曾在本地通过适配器解析与预览。这里证实的是输入冲突，受影响的实际对白和动作尚未逐项核验。

## Implementation

即梦适配器首次编译和调用预览时校验最终 Prompt 中编号镜头的显式输出区间。超界时报告行号、超界时间与请求时长，于素材上传前停止；提交重新校验预览。可复用的检查行为与语法见 [Jimeng Provider](../jimeng-provider.md#explicit-frame-conditioning)。历史任务沿已封存参数读取，现有结构化时序依旧归原计划和时间线。

## Verification And Evidence

[测试](../../tests/test_jimeng_authored_prompt.py)覆盖 18 秒请求与 20.5 秒时间码、中文画布与默认英文镜头模板、起点超界、等于时长的终点，以及对白和参考视频中的时间。回归覆盖首次编译、预览、提交前零上传及历史参数的精确解析。验证仅在本地执行，线上效果和实际成片质量未评估。
