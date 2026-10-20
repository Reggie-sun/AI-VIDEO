---
record_kind: architecture_implementation
topic_id: seedance-prompt-length
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Seedance Prompt Length Guidance

Date: 2026-10-21

## Purpose And Source

用户明确要求 Seedance 的文本长度处理与官方口径一致，并补写“文字过长可能使信息分散，模型遗漏细节；
建议中文不超过500字、英文不超过1000词”。依据是本轮实际读取的火山方舟
[创建视频生成任务 API 文档](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)
的 `content.text` 说明；该文档给的是效果建议，没有据此确立2.0、2.0 Fast、2.5分别的硬上限。

## Change

`compile_remote_video_prompt` 保留其他调用方既有5000字符边界，新增显式可关闭的本地长度参数；
Seedance adapter 单独关闭它。`SeedanceNativePromptBinding` 去掉原65536字符的本地 authoring 上限，
仍要求非空文本、exact SHA及provider-bound identity，原recipe coverage和来源保留检查不变。
没有自动截断、摘要、删减表演或语言计数Gate；不声称Provider可接受无限长输入。

官方建议及信息分散风险写入现有 `seedance-authoring/references/authoring-common.md`，
运行边界与来源见 `docs/seedance-prompt-length.md`。其他Provider的实际官方限制不在本次修改范围内。
本变更由用户直接授权，不是自动学习采用；未修改Policy、预算、permit、Production state或媒体。

## Verification

先增加回归，旧实现得到7 FAIL、2 PASS：Seedance的中文/英文长文本在自动编译路径被拒，
超出65536字符的绑定文本被schema拒绝。修复后同一组9项通过。

进一步执行 `test_generation_provider_wiring`、`test_production_seedance_mixed_reference`、
`test_seedance_source_prompt`、`test_seedance_authoring_skill`、`test_generation_historical_replay`，
共121项通过。覆盖2.0、2.0 Fast、2.5的长Prompt经共同Router/feedback/compiler形成原生请求，
完整保留末尾动作/表演；其他remote Provider既有拒绝行为、原样文本及hash/recipe拒绝路径保持。
这些是离线工程证据，不证明Provider live接受长文本或视频观感改善。

Parent自审：局部文本长度处理与advisory指导调整，无授权、凭据、持久化或验收路径变更，
按当前Risk Gate不额外派独立reviewer。额外启动的大范围changed-path policy验证耗时过长，
用户明确要求收回到Prompt限制修改后已停止，不重跑；
`.agent/harness/runs/seedance-prompt-length-20261021/receipt.json`为未完成记录，
不声称完整Harness通过。上述121项相关测试已完成并通过。

## Boundaries

本轮没有Provider调用、付费生成或真实媒体测试；记录过程也没有新增这些效果。
官方建议和机械编译成功不保证表演、声音或观看吸引力，不能据此宣布导演升级或内容发布。
保留其他窗口dirty/staged工作以及此前尚待审片的METASO记录与媒体，只提交本任务明确路径。
Agent Memory检索返回fresh/stale混合advisory命中并排队后台维护，未等待或手工重建索引。

自动评估 `distill-ai-video-learning`：`no_candidate`。这是对照官方文档的用户指定工程修正，
缺少新的真实媒体实验，不创建通用审美或模型质量Learning Claim。
