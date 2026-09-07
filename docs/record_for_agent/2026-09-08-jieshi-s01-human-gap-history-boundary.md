---
record_kind: session_summary
topic_id: jieshi-s01-hand-repair-history-boundary
learning_eligibility: ineligible
---

# S01 Human Gap Finding And History Boundary

Date: 2026-09-08

## Scope And Result

承接用户“继续生成界蚀shot1”。保留原点名广播、原首帧、已批准修复末帧、Vidu
Q3 Pro及最多一次新提交。用户随后明确“手部出现明显变型”，并对exact旧片前3秒
手与玻璃的小间隙回答“看不清”。旧手部FAIL继续有效，间隙可读性现在也是human
FAIL；不把不可读解释成已测量物理接触或厘米距离。

## Exact Evidence

旧attempt09 MP4 SHA-256为
`7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302`，
3,476,468 bytes。本会话已重新核对SHA/bytes，并调用project-local video_probe：
1080×1920、24fps、97帧、4.042秒容器、H264/AAC。技术读取不代表质量PASS。

以下派生证据保存在`runs/jieshi-e01-i2v-20260907-attempt10/`，遵循现有runs忽略规则，
本地保留、不强制加入Git：

- `human-visual-review-attempt09-20260908.json`：原话、问题、actor与exact媒体身份；
  SHA-256 `f685ef8e6b2013bab0370b9cae1b9d3cb0f2e8ebb6bde1b38e40427a1ff10660`。
- `historical-human-supplement-20260908.json`：旧2.1 rubric下两项human FAIL；没有改写旧证据。
- `historical-diagnosis-after-visual-20260908.json`：`diagnose_exact_result`实跑只有
  QUALITY_FAILURE，失败项legacy-03/05/06/17，next_owner=shot_router，非Gate PASS。
- `historical-decision-inputs-after-visual-20260908.json`与
  `historical-decision-after-visual-20260908.json`：只向旧输入追加补充证据，纯Router
  历史重放为REASSESS_FEASIBILITY，理由是没有新的可测试intervention。旧profile、
  context与2.1 rubric未升级，不能将这个重放当作当前2.3的生成准备或执行许可。

## Current Execution Boundary

standard `load_production_project()`重开attempt10为Manifest revision 4、Project/Shot
revision 6，`active_qa_policy=None`。准备目录的2.3 acceptance不是canonical active QA。
常规`activate_qa_policy`入口已存在；它本身不能解决历史接入。

`_StateCommitVideoMixin._require_submit_execution_binding`
（`src/ai_video/production/_state_commit_video.py`）要求binding的evidence/experiences
与Manifest完整durable history精确相等，latest hash也必须一致；同Shot旧任务若无
production decision binding则拒绝。`record_generation_experience`
（`_state_commit_generation_feedback.py`）又要求已有exact durable attempt/binding，
所以不能把另一个project内的旧attempt09回溯评价写成v10的新经验。
`record_attempt_evaluation`同样要求durable binding。现有historical replay测试只
验证pure policy，不提供历史导入或新submit证明。

不能通过空history把受控repair变为first attempt，也不能伪造过去不存在的binding、
复制Manifest状态或放宽校验。下一步需要明确的历史证据兼容性设计/实现：验证旧
request、fetch、human/analyzer来源及rubric版本，由唯一committer持久接入，保留
失败和quota语义，再走当前QA/Planner/Router/compiler/preview/permit。
这涉及新的runtime兼容契约，当前媒体任务没有被静默扩大为核心Gate修改。

本轮没有Provider POST/poll/fetch、secret lookup、profile续期、reservation、permit、
candidate activation或S02；没有新MP4，单次修复额度未消费。没有修改核心代码。

## Learning Evaluation

`distill-ai-video-learning`：no_candidate。同一旧MP4的补充human proof不是新独立
模型实验，不能证明修复末帧会改善生成质量。RAG仅作为advisory discovery使用。
