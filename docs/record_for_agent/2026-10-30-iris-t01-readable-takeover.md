---
record_kind: session_summary
topic_id: iris-t01-readable-takeover
learning_eligibility: ineligible
evidence_index_version: "1"
---

# IRIS T01 Readable Takeover Record

Date: 2026-10-30

## Supersession Notice — 2026-10-30 EP01 Continuation

本文的 T01 测试及历史工程结果保留。下方关于 EP01 尚无参考包、没有后续镜头认可或零 paid submit 的状态，已由用户后续三图认可及真实执行取代；当前状态见 [EP01 接线与源片记录](2026-10-30-iris-ep01-patchright-and-source-progress.md)。旧 policy/full 验证缺口未在该制作分支修复，不再把它当作停止视频开发的理由。

## Purpose

接续用户指定的 Claude 会话，完成已有横版 T01 引擎测试候选的独立复核及有界修复。用户最新决定「还没生成，先完成测试片」，当前不继续 EP01 正式媒体。

## Current Runtime Truth

- 既有工程是 HyperFrames + motion-kit 的开发 Pilot，尚未接入 `CompositionSpec → ResolvedTimeline`；本次不更换 renderer、不宣称 Production 接入或验收完成。
- IRIS 女性 CF 身份、角色名、ID7b 已由上次会话生成并定稿；本次核对，不重复生成、不将既有工作记为本次新增。
- T01 dev6b 的独立观察显示：红1仅一帧，HUMAN仅两帧，且HUMAN晚于全局归零出现；静帧存在不证明原速可读。
- dev7 保留6.0s空拍drop，实际 f181–194 清晰保留红1/HUMAN，f195（6.5s）同帧翻白0/AI，最后光轨同时完成入相。此为父会话对局部时序偏好的裁决，不是新的用户硬时点。

## Exact Media

| Artifact | SHA-256 |
| --- | --- |
| `outputs/ai-city-takeover/phase1-t01/renders/T01-dev7.mp4` | `5e4601b0824b2cb82a42c9041178b0d3f06827f1d66de4e14755bf83b47a3697` |
| `outputs/ai-city-takeover/phase1-t01/review/T01-dev7-review.mp4` | `f14a007a5ae6570336adc1edfb1b89d382247e00485be83f9f3c1e11e1009165` |

原片：1920×1080、30/1、300帧、视频10.0s；AAC 48kHz stereo。封装时长含AAC尾部为10.022s，不据此增加视频帧或重定时。审看片为单独转码 identity，BT.709、H.264、AAC；不冒充原片相同bytes。

## Verification And Evidence

证据目录：`outputs/ai-city-takeover/phase1-t01/qa/dev7/`。

- `report.json` / `report.md`：11/11事件落在±1帧内；规格、闪烁、突跳、strobe、离群检查通过；每镜、八分音、安全区、390px和100%文字联系图已生成。
- `render-regression.json`：4-worker与1-worker的300帧全部一致，两个MP4本身SHA相同；dev6b/dev7导引音频469个解码帧相同。S1/S2有损编码并非逐像素相同；480×270 RGB的平均绝对差0.690/255，差异统计不单独签无回归。
- `codex-independent-review.md`：独立者核对f180–195，确认14帧可见前态及同帧翻转；逐帧有界修复PASS，完整声画PARTIAL。显式调用project-local `video-analysis.video_review`，自动issues=[]不替代语义或听感。该工具漏检旧片两处切镜，因此未把自动scene_count当完整性证据。
- `browser-playback.json`：独立本地浏览器以1×跑完300帧，0掉帧、无video/page错误，10张关键帧均加载；初次favicon 404已记录并在页面中改为data favicon，不影响媒体请求。没有把播放结束当作人眼观看或聆听。
- `source-and-media-sha256.json`：绑定当前参与的源码、数据、bundle及媒体。
- `harness-focused-invocation.json`：先前替代index尝试因Harness清理Git环境而无有效scope；随后真实exact staged snapshot树`075d5f8d3f4c27bc0bd010a9324f48e05f0b8806`，`focused`因Pilot路径缺精准映射退出2，未执行suite、未生成Harness receipt。没有扩跑full或修改policy求PASS。仅本次临时暂存的三个owned文件已取消暂存；最终读回存在其他会话新增的暂存，全部保留。

## Scope And Next Work

审看入口 `http://127.0.0.1:8767/phase1-t01/review/`，页面、视频及报告HTTP读回均为200；`xdg-open`返回3，未声称已替用户打开浏览器。T01 是带临时导引节拍的引擎测试候选，完整正常速度声画观感及人工接受 `NOT_EVALUATED`。正式Suno配乐、IRIS对嘴、真实平台转码、Phase1.5 Production接入均未验证。

本次顺带补齐EP01一手来源`outputs/ai-city-takeover/ep01/fact-check.md`和待歌曲的`storyboard-draft.md`，未改已认可歌词正文、未生成参考包、无`preview_approval`、无paid submit。03:47为IRIS虚构品牌时间，11天限相关最强研究工作，网页缓存与另一项CPU cache受控红队测试分开，不将两事件串成同一逃逸。

本次Suno/Seedance新增付费生成0次、消耗0；仅只读查询曲库和余额。用户已明确先完成测试片，EP01等待其歌曲。没有上传、激活、P6、Final Acceptance或发布；依成片优先规则等待用户观看后再完整验证及commit/push，本次本地修改未提交、未推送。

## Learning Assessment

`no_candidate`：本次是同一Pilot素材链的局部修复和确定性技术检查，没有新的可归纳模型质量实验；不把多版本、worker复测或多层证据计为独立媒体经验。不新增Learning Claim，不修改Skill/Policy/Gate。

## Subsequent User Acknowledgement

同日展示dev7后，导演回复「可以」，按T01测试片认可处理。它没有证明Agent已亲自完整听看，也不授权EP01付费镜头或Production Final Acceptance。用户认可后继续完整工程验证；原索引已有另一会话的staged source/policy/test改动，采用verification-only独立clone验证本任务snapshot，保留原索引。通过前不提交，不把clone receipt冒称原索引证据。

## Full Verification Attempt

用户认可后创建verification-only clone（非开发worktree），只封存本任务99路径，真实full Harness运行的前三项检查通过，在policy_audit_check失败后按原Harness停止。失败是基线`dotenv_source.py`、`preview_approval.py`、`test_production_dotenv_source.py`映射缺口，三者均与原HEAD字节相同、任务staged delta为空。详见`outputs/ai-city-takeover/phase1-t01/qa/dev7/full-verification-summary.json`及`harness-full-20261030/receipt.json`。未改另一会话拥有的policy，不夹带其staged工作；因此仍未commit/push。此receipt绑定首次verification snapshot，不证明后续tools修复已通过full。

## Tool Boundary Repairs

独立工程review进一步确认短音频STFT越界读取、QA失败仍返回0、参考图事后哈希三个边界问题；已在`motion-kit/tools/{beatmap,qa,codex_plate}.py`有界修复，新增`motion-kit/tests/test_tool_boundaries.py`，9项直接精准测试通过。独立复审为APPROVE（四文件、0 open issues）。测试仅mock生图调用，没有新媒体或Provider提交；dev7 exact MP4及其原有参与源码identity均未变。证据`qa/dev7/tool-boundary-tests.json`及`tool-code-review.md`。

最终停点：T01已获用户认可，工具修复已完成精准验证；full发布检查被基线policy映射缺口阻断，保持未commit/push，不修改另一会话的policy或暂存区。此为明确工程阻塞，不是新的媒体缺陷，也不授权扩大EP01工作。学习评估继续`no_candidate`，不把本工具回归测试写成普遍模型质量经验。

## Clock Boundary Continuation

后续“继续”时当前policy审计已通过，但修正属于另一会话的暂存、未commit。为本任务准备增量精准check映射，未写共享policy。新增Node运行时测试发现offset相减浮点误差使0.6s拍点丢脉冲，修复后7项通过；原9项工具测试也通过。独立代码复审APPROVE。

由于clock.js及bundle参与bytes改变，未复用旧软件证据：重新build/render到新路径并生成新联系图及QA。新MP4 SHA仍为5e4601b0824b2cb82a42c9041178b0d3f06827f1d66de4e14755bf83b47a3697，与已认可dev7完全相同；新QA11/11通过。软件identity另存`qa/dev7/clock-recheck-source-and-media-sha256.json`。原软件identity保留为历史，不倒填旧PASS。

## Latest Mapping Proposal Verification

增量精准映射仅在verification clone中试用，Main policy/index未改。首轮coverage声明遗漏与后续测试发现方式问题已在候选中纠正；失败receipt保留。最终Python工具测试移到标准`tests/test_motionkit_tools.py`，full_tests保持原默认argv并真实收集它；独立Node suite另设check。

proposal focused-r3全部通过：Node7、工具9、Harness324；仅补丁文档的空白格式修正后，related-r4的diff/docs/agent_rules/policy_audit、runtime boundary、Node/Python与task architecture通过，在agent_rule_invariants中因旧unsubmitted fixture失败而停止（43 passed、1 failed），没有继续full。该fixture在当前含另一会话staged门禁迁移的working tree直接诊断通过（1 passed），不是本任务冻结closure证据。

最新阻塞取代早期policy audit缺口：共享门禁迁移的另一会话尚未提交，且仍拥有policy与相关fixtures。未擅自修改其文件/暂存或将其工作混入本任务提交。可复核材料在`outputs/ai-city-takeover/phase1-t01/qa/dev7/mapping-proposal-result.json`、`mapping-proposal-focused-r3/receipt.json`、`mapping-proposal-related-r4/receipt.json`及proposed/combined patch；补丁尚未应用Main。按AGENTS同文件归属规则，等待该分支正式提交后接入本任务映射并继续验证，或由用户明确解决共享文件归属。当前仍无commit/push、无付费请求、无新Production状态。

本次record完成后经验评估仍为`no_candidate`：确定性工程回归、同一测试片的bytes一致性重验，不泛化为新媒体能力结论，不创建Learning Claim。
