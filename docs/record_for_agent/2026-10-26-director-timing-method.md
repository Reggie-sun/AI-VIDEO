---
record_kind: research_note
topic_id: director-event-led-timing
learning_eligibility: ineligible
---

# Director Event-Led Timing Method Record

Date: 2026-10-26

## Scope And Result

用户要求研究 skill-movie、DirectorSKILL、drama-skills 的真实实现、依赖和许可，结合 Seedance/H3
历史媒体独立取舍并自主改进，明确不新增付费生成。完整比较、固定上游SHA、许可及阅读范围由
[研究报告](../research/2026-10-26-director-skills-and-event-led-timing.md)维护，本记录不重复其资料表。

本次仅补 `open-video` 的作者方法：先按触发、行动、对白、倾听/反应、后果及切镜理由决定节奏，
再选择可执行镜长；明确相对顺序、估算、固定deadline与最终剪辑时间的区别。既有字段已足够，
不新增Runtime schema、第二时间线、生成执行器或外部Skill安装。

自有文件为 `open-video/SKILL.md`、`references/professional-specialists.md`、新建
`references/event-led-timing.md`、上述研究和本记录，共5个路径。两个既有文件写前为clean，
Parent为唯一writer。共享compiler/schema、其他dirty/untracked工作与全部历史媒体保持各自归属。
MIT方法局部中文改写保留既有许可证；skill-movie无统一许可的主体未复制，两个MIT子包亦未引入。

## Verification Evidence

- 当前工作树的 `tests/test_production_h3_prompt.py`、`tests/test_performance_direction.py`：
  **61 passed**，核对已有表演表达、无时码对白的支持与拒绝边界，不归作本次新Runtime功能。
- Skill `quick_validate.py`、两份MIT副本与上游文本核对通过；最终相对链接、owned diff及snapshot
  检查沿本任务收尾验证。Parent没有以source coverage代替影片观感。
- 原生只读 `test_analyzer` `/root/timing_forward_check` 做5项文本forward exercise，实际给出自然
  咖啡对白的暂定8秒预算/无台词时窗、严格5秒长对白的未测容量缺口、保留3.5秒硬deadline、
  H3抢话unsupported及禁止将已知迟到改称弹性。`ETT-001`建议明确估算保存位置，Parent确认并
  补入既有authoring notes，未增加schema；原forward候选SHA为
  `3090fc2161e7839dfa0872a5c586e11f9e163fd98c5e5379a6275a7db490febc`，
  估算与未发布能力边界澄清后，最终guide SHA为
  `ad1f8a6aa3d52f16ea3d538d403e6c1d89d2b417e899231016b0b3060b3f969b`。
- exact staged Harness的结果、scope、policy和源码身份以以下receipts为准：
  `.agent/harness/runs/director-event-timing-focused-20261026-002/receipt.json`、
  `.agent/harness/runs/director-event-timing-related-20261026-001/receipt.json`。
  focused不充作功能完成，related不冒充全库回归或媒体质量。若因外来漂移需要新候选，保留旧receipt。
  两次focused均通过（各48项Skill、321项Harness与docs gate）；002包含source审计、许可/缺失eval
  说明及未提交引用边界。之后仅在本研究/记录补充Git发布阻断，最终scope由related receipt绑定。
  staged related 001的10个checks通过（423项测试），校验为fresh、full_regression_passed=false。
  commit后的当前身份另以 `.agent/harness/runs/director-event-timing-related-20261026-commit/receipt.json`
  做commit-range核验，避免把提交前staged scope在HEAD变化后仍称fresh。

最终链接检查同时针对working tree和精确Git index，避免把其他窗口尚未提交的文件当作发布依赖。
因此未提交的对白说明及两份用户反馈记录只注明本地来源，不新增指向远端不存在文件的链接，也不夹带
其工程实现。17条首轮上游permalink已与对应clone的固定SHA/实际路径核对，最终增加的引用继续同样核验。

本轮是纯advisory Skill与研究文档，非视频交片或Production release；按受影响模块及接口做相称检查，
不为文档运行全库媒体/工程套件。Risk Gate为 `NATIVE_REVIEW_NOT_REQUIRED`：无执行/权限/
持久化语义改动或重大后果验证缺口，Parent自审；source researcher和forward tester不冒作独立工程review。

## Media Boundary

重新核对2.5温室、Mini温室、H3机器人原片SHA，均与历史记录一致。显式调用project-local MCP
提取机器人11帧、2.5温室10帧，实际查看其中各6帧；局部确认3.5秒手臂未平举、铜花触碰前已开。
没有新完整1×声画审片、不改旧verdict；原H3源的FAIL与后来另一有声编辑版获用户接受分别保留。
《界蚀》的不自然反馈与《失帧》的表演/美术/声画反馈按原记录范围使用，不合并成全片PASS。

新增图片/视频/语音生成0、付费理解0、生成费用0；未submit、retry、remint、activate或改变历史budget、
UNKNOWN、qualification、P6或Final Acceptance。新方法尚无同输入新片对照，观感改善 `NOT_EVALUATED`。

## Publication And Learning

Git归档仅覆盖上述5个自有文件。核对远端 `main` 为
`2d17c49e0f22ce2ffb44a713b25c81ef7a546aa6`，本地初始HEAD `1c53e61`在它之后已有4个其他任务提交，
包含Harness实现 `5daa3d6`、其full失败记录 `136038a` 和广告方向实现/记录。既有
`.agent/harness/runs/harness-three-levels-full-20261025-r2/receipt.json` 为FAILED，
[原owner记录](2026-10-25-harness-three-level-verification.md)要求修复后fresh full PASS才发布。
本次未改其失败或取得新的全库PASS；直接push本地main会连带发布这4个提交，因此push为BLOCKED。
不force、不改写他人历史、不用新branch/合成commit绕过发布门槛。自有稳定改动可在相关验证后本地commit，
最终SHA以Git readback与交付消息为准；未进行Production发布或把其他窗口的工程/媒体归作本次成果。

`record-ai-video-session`：record。自动 `distill-ai-video-learning`：`no_candidate`；这是外部研究、
旧片的同一证据复核与文本方法集成，没有新增独立可归因质量实验，不创建占位claim，也不修改全局memory。
RAG初次检索返回带stale标签的last-good片段并自动排队刷新；关键内容均直接重开当前源，不等待或
手工重建索引，不声称整个RAG已更新。
