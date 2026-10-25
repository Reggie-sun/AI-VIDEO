# Authored Resolution Revision

## Goal And Scope

用户要求先写入480p试片认可后生成1080p正式版、重新审片的规则，再实际生成《失帧》S01高清版。规则已单独提交并推送5bf4cd7；同一已认可D首帧、三轮原文、四机位、16秒和纸先落空台面再提饭放稳的方案保持。只执行一个新视频单元，累计4→5，保留旧paid/media/QA/UNKNOWN，零自动resample；新结果不继承旧验收。

## Ownership And Contract

Parent拥有原supersession receipt/facade/reader、qualification与submit锁内接线及实际运行；bounded_worker仅拥有`generation_resolution_revision.py`及其纯测试。新增typed `ResolutionRevisionTarget`只允许adaptive输出的分辨率档位提高，保持其余output、creative intent、精确prompt、参考、provider/model、原raw QA不变；新same-ID goal保留全部旧要求。

沿旧`GenerationVisualSupersessionReceipt`追加`/3`，旧`/1`与`/2`字段缺省序列化和hash不变；完整JSON写前重验。旧exact fetched+paid+latest experience绑定原始评估，并以用户要求的规格改版关闭，不能伪造FAIL、all-NE或Human acceptance。只允许无FAIL的已知media，NE仍为NE。新qualification admissibility核对完整累计历史、used+1、同task/Shot、零resample，无unknown/intervention/runtime recovery。submit锁内严格重开原`/3`及旧QA/evidence/request/fetch/paid并核对当前目标；不改变Product qualification，不走direct transport或新建project归零。

## Execution And Verification

先完成必要公开closure/replay/negative和pure/locked guard测试，兼容旧visual/coverage/quality路径；actual完整历史的离线副本经同一prepare/start/submit锁入口取证，零permit/POST。一名native reviewer_xhigh按权限与持久化Risk Gate审查，初审加最多两次复审，保留此前独立任务review历史与findings。

正规顺序：封存有限单元和当前输入→原004 supersede→新goal/Project与同语义Shot metadata revision（避免复用旧generation identity）→原budget extension→prepare→start005→原quota extension4→5→一次submit→poll→fetch→explicit project-local MCP。原raw rubric保持时，decision只识别被严格output-target约束的same-ID新goal提案，执行仍须完整编译predicate及锁内`/3`核验，NE不签PASS。当前native只读1080p16秒first-frame报价1024CRD；内部单次上限1500、累计3500，仅为operator upper bound，真实结算另记。

exact MP4重新核验实际尺寸/时长/帧时间戳、D人物、四机位、完整纸饭接触、对白/口型与声音；新片待用户播放时保留NOT_EVALUATED，不推进下一剧情Shot。先交1080原片，用户认可后沿共享字幕/ResolvedTimeline/HyperFrames制作并验收字幕，不为本次媒体生成提前扩跑完整工程套件。无公开发布或Production activation。
