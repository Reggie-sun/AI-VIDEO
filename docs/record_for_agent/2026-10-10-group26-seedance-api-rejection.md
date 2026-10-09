---
record_kind: recovery_incident
topic_id: group26-seedance-api-mixed-reference
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Group26 Seedance API Submission

Date: 2026-10-10

## Follow-up — Authorized Text Recast

用户随后明确授权撤下三张人脸参考，以新角色文字描述保持写实风格。
[新一条独立请求](2026-10-10-group26-text-recast.md) 已成功生成；下文仅描述原五参考失败请求，
其 HTTP400、输入、消费及未验收事实不变。新输出也尚未获完整听看验收。

## Current Runtime Truth

用户要求执行后，Group26 已经通过 canonical `VideoGenerationService` 向火山方舟
实际提交一次，未通过网页点击生成。2026-10-09T17:33:26Z 开始唯一 POST；方舟返回
HTTP 400，error code 为 `InputImageSensitiveContentDetected.PrivacyInformation`。
没有生成视频、没有 Provider task success、没有重试、没有媒体或人工验收。
本地 paid owner 将拒绝记录为 `paid_provider_known_no_effect`；未查询账单，不以此声称已核对扣费。

该错误指向输入图片隐私内容检测，但保留的响应码不定位具体图片或区域，也不证明
虚构角色实际是真人。网页上传的 `done` / risk PASS 与生成 API 接受是不同证据。
不得重标素材、伪造 asset admission、静默删图或用同请求重复提交来绕过此结果。

## Exact Input And Review

Run：`runs/seedance-api-mixed-20261010-001/`；attempt：`group26-seedance25-api-001`。
模型 `doubao-seedance-2-5-260628`，R2V，15s，720p，16:9，`generate_audio=true`。
图片顺序为小龙、潘子、曾亮、宿舍，随后为原导览视频的获准 2s 适配版。
原文仅做四处素材标签映射，四句对白、五段分镜、堵门、仅手机照明及结尾分歧保留。
已批准的例外仍仅包括视频末尾补3帧、原音轨保留，以及宿舍同尺寸q95 JPEG。

- 原画布 prompt SHA：`e4e191fb84d767f4f37dc3031c016a7afd346c5b46fac67df459594bbc92ed88`。
- 实际 prompt SHA：`09b6e4e0b6a4fe7a5d5a933a31898459d1ba6459c26e167abf49e55ad34e9eee`。
- 实际请求 body SHA：`ee347146d871275d59e3c16fb316608ab01411053d400ed7df5bcffeae9b3fa7`。
- 最终输入投影、Claude结果及Parent裁决：`final-api-input-review.json`、
  `claude-final-input-review.json`、`review-approved.json`。
- 物理POST及错误：`submit-wire-observation.json`、`provider-rejection.json`、`generation-result.json`。
- 完整视频GET哈希核验：`reviewed-reference-readback.json`、`reference-readback.json`。
  签名地址只驻内存；上述文件仅保存地址哈希。

Claude 确认四处标签映射、参考顺序、原文和参数保留；其“校验已过期”判断把 UTC
与本地日期混淆。Parent 以 UTC 实钟裁定，提交前还重新完整GET核验。Claude 没有实际
看图听音，未将JSON比对当作审片。15s密集对白的风险保留，不擅自缩减原创作目标。

## Implementation And Verification

代码 checkpoint：`ba7e7d8`。现有 synthetic image resolver 支持原样 JPEG/PNG；新
mixed resolver 组合人类声明/来源/Registry绑定的图片与完整GET核验的视频，短期URL
失效即停。Standalone图片入口仍拒绝video。原文binding保留完整意图覆盖检查，支持
原样中文对白和“推近”的对应表达；不为检查器追加英文或改原prompt。
Credential supplier 使用用户明确指定来源；值不进入日志、prompt或receipt。

新项目通过已有 bootstrap、schema upgrade、dependency graph、QA owner 准备。
曾因本地Manifest 2.4缺少video capability在POST前停止；经canonical upgrade到2.7
后继续同一审查过的body，不是第二次付费重试。浏览器本地网络访问处于prompt状态，
地址经一次性nonce保护的本地表单传入；未修改浏览器全局权限。
新增run脚本是该任务的胶水，不声明为通用命令或已覆盖所有错误恢复的入口。

Focused mixed-reference tests：13 passed。完整exact staged Harness与fresh receipt通过：
`.agent/harness/runs/seedance-api-mixed-20261010-004/receipt.json`。
先前003因验证期间snapshot改变未通过，保留，不作为当前完成证明。
受管Kimi独立边界调查的receipt与Parent逐项裁决在同run的`kimi-run.json`、
`parent-boundary-adjudication.json`；Kimi没有审过后续中文表达小改动，不扩大其证据。
Parent在最终snapshot判断Risk Gate不触发额外Kimi final review；用户要求的Claude
最终提交输入审查已完成。工程通过不证明平台接受或模型复刻质量。

## Learning Evaluation

使用 `record-ai-video-session` 保存这次真实拒绝；`distill-ai-video-learning` 为
`no_candidate`。本次只有一组混合输入的一次提交，未隔离具体触发图片，也没有成片；
不形成表演、模型能力或“虚构声明能通过审核”的经验定律。RAG索引未主动重建。
