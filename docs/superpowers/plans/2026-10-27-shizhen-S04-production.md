# Shizhen S04 Production

## Current Edited Review

用户只指出3–4秒接点不连贯后，已在同一素材上完成柜台近景插镜修剪，交付 `失帧-第一集-S04-接点剪辑修正版-1080p-9.875秒-原声.mp4`，SHA `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`。采用既有CompositionSpec→ResolvedTimeline→HyperFrames，1080p/24fps/237帧，原声与画面同窗口0..3.5和3.625..10秒，不变速，两句完整。新增生成0、总次18；原raw Gate FAIL和旧音频UNKNOWN均保留。逐帧主接点核验及exact PCM验证完成；intentional crop有1条layout warning，Harness assembly和用户正常速度审看仍NOT_EVALUATED/PENDING，不虚称完整接受、不启动S05或累计拼接。明细与真实限制归 `S04-edit-005/delivery-receipt.json`及primary record。

## Current Execution Supersession

S04-001已fetch并交原声单镜，exact SHA `9ffd9ef405fbc683ba49dd6044c3653218d525bcbe5cb0e7342c77e6cfc8dbff`，1920×1080，容器实测10.08秒。当前Gate **FAIL**：约3.5秒切中景时，右手手机从贴近身体跳到再次向柜台伸出；不符合封存的“近身持有后降低”。声音/口型和清楚查看侧通道尚NOT_EVALUATED，不能用源音轨存在或第三镜听音认可来代签第四镜。保留原片供用户观看，停止后续镜头和自动重生成；本单元1次已用完，不拼接、不上字幕、不发布。单镜审看完成前工程完整验收及owned commit/push按成片优先边界待办。

用户已明确回答“听过，声画衔接认可”，绑定S03-005 exact SHA `51bf0aaea2deaa8f02fb2a8f3f4f2666a8cd6304e5f9f80f5598fd7eab87368f`。这份独立实际听音证据与当前project-local MCP及画面复核，经既有committer补录全部8项观察PASS；不改写旧音频分析UNKNOWN、费用或permit，不作Production activation/Final Acceptance。

用户追问“10s你为什么不用2.0”后，当前最终选择为 **Seedance 2.0 VIP / multimodal / 10秒 / 1080p / native audio KEEP**，4张实际参考已按顺序编译绑定。共享compiler仅放开此已注册型号的untimed conversation，仍拒绝neutral fallback、静音、独立voice route或未适配型号；没有给台词强加时间戳。旧2.5只读报价/空节点profile保留为未提交准备，不发生2.5视频调用。

S04 canonical root为 `trial-S04-v1`，task `shizhen-S04-qualification`，attempt `shizhen-S04-qualification-attempt-001`，已通过现有preview、budget/quota、durable intent和一次性permit提交并被接收。17次历史video保留，新增1次，合并有限上限18、自动重试0；2.0当前native quote为330credits，1500CRD只是内部guard，实际扣费待结算。真实结果取回前不称完成，先交单镜原声审看，用户认可前不拼接或上字幕。下文Hard Stop是已被上述新证据解除的历史状态。

## Goal And Entry

用户明确“开始shot 4”，扩展原前三镜范围至S04，不授权S05或发布。保持真人摄影和原剧情两句“……还没扫上？”“师傅？”，不添加对白时间戳。承接S03-005已俯身、右手持手机的实际末态，不重演惊跳和柜台下探看；新行动是检查侧通道、码暗下后降手、叫师傅及向画外骑手转移注意。

## Preparation And Route

用户复核后已实际补做侧通道检查中态和手机降低/转向画外骑手末态两图，现在是2张actual取帧加2张生成动作图，共4张planned参考。具体hash、输入与职责归S04目录的reference-evidence/source记录；静态参考不能证明连续动作，视频仍未提交。

当前草稿为约10秒完整行动/回应，两机位同侧服务查找对象。实际两图为S03-005末尾近景与4.5秒柜台物件/场景，后一图不能迁移更早的受惊表情、站姿或举手机姿态。目录 `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/S04/`。

2.0 VIP渠道当前支持10秒/1080p/多图，原生只读报价330credits；这不等于已扣费或完整可执行。当前common compiler仅接受2.5的无时间戳conversation，原S04不应通过强塞逐句时间戳来适配2.0；exact模型/模式仍未封存，恢复后先在既有能力owner选择兼容路线或完成必要适配，不隐式换Provider。

## Hard Stop And Finite Bounds

S03-005原声证据补充调用返回 `transport_unknown / UNKNOWN`，一次性permit已消费，不能重试、重铸permit或换root归零；原视频结果已fetch，未知的是本次声音分析。S03仍NOT_EVALUATED，未满足逐镜全PASS进入下一镜的条件。因此不得新建可执行S04请求或提交视频；保留草稿、源素材、17次全部已知video调用历史。

用户授权目标在恢复条件满足后最多新增1次S04 video：拟议合并上限17→18，零自动retry。当前未封存该video预算、未创建新video节点、root、请求或permit。音频分析内部upper bound为USD0.05，不是账单，真实扣费待确认。

## Resume Conditions And Verification

先由原声音证据owner恢复该次已消费调用的明确结果或取得可信的同bytes声音证据，按原S03要求完成证据修复，不重生成S03补证、不假造PASS。随后重新核对计数、exact参考/意图、版本与无时间戳对白能力、当前平台quote、budget/quota与新video permit，走ProductionStateCommitter和selected adapter生成一次S04。exact原声MP4落盘后显式MCP核验；用户审看片与QA/人工接受分开。用户认可前按当前交付边界不擅自拼接或制作字幕；合成若获授权，仍走CompositionSpec→ResolvedTimeline→HyperFrames及Harness逐接点检查。
