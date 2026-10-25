---
record_kind: session_summary
topic_id: hotpatch-warmholiday-seedance20
learning_eligibility: ineligible
---

# Hotpatch Warm Holiday Seedance 2.0 Checkpoint

Date: 2026-10-24 (Asia/Hong_Kong)

## Current Scope

用户拒绝纸浪版本的剧情，要求先讨论，随后明确产品与问题开头同框、先看到贴片、夸张效果更强。批准《人还在上班，腰已经入住总统套房》后要求“seedance2.0就够了开始吧”，并按产品说明确认“按说明贴在衣物上”。本片目标由55秒调整为58秒：独立concept review发现7秒O3承载不足，Parent保留所有大动作、对白与HERO5秒，将O3增至10秒，仍在用户45–60秒范围。

新run：`runs/hotpatch-warmholiday-seedance20-20261024-001/`。执行计划：[Warm Holiday Plan](../superpowers/plans/2026-10-24-hotpatch-warmholiday-seedance20.md)。旧54秒纸浪run停止新生成，旧MP4、账本与画布保留，不用旧片凑时长。

同一新[即梦画布](https://jimeng.jianying.com/ai-tool/ai-canvas/b0d2c76f-5f9a-4fd1-9d9b-cfaf55221f37)保存六个节点，索引为`canvas-delivery-index.json`。exact模型为`seedance_2.0_vip`，没有改用Mini/Fast/2.5。当前仍UNQUALIFIED，仅沿正式qualification trial入口生成、下载和开发审片，没有Production activation或P6。

## Exact Generated Media

| Shot | Duration / bytes | SHA-256 | Current gate |
| --- | --- | --- | --- |
| O1 | 原片8.058秒 / 15,044,546 | `fd9a93740b9c46f5eb6917e61e3052a5ad6c87bce41bf0b7012045e69335ea26` | MCP观察、用户台词/原声确认、canonical六项PASS。第一秒隔衣贴片和被子同框，拉开到冷办公室/短袖同事，最后贴片纤维近景。 |
| F1 | 原片8.058秒 / 13,717,948 | `e57ae64e85b60593e8f32178dfcc342f4f3d255eb7d873d9d2ede71b7f078c76` | MCP观察、用户台词/原声确认、canonical六项PASS。绒毯山谷、人物下落、沙发接住压缩、双靠垫弹出、墙板合拢可见。 |
| O2 | 原片6.080秒 / 7,927,190 | `332785abd1240c167cb2ec5899b0d415065f91511e6a1a0e6d4c8d390c425f15` | 已MCP观察且用户确认台词/原声正常；产品特写隔衣细节仍缺证，未写all-PASS diagnosis，F2不得提交。 |

原声确认均来自用户对各自SHA相同副本的逐段回复“台词和原声正常，继续保留”，不代表完整片观感或混音验收。O1/F1的相机/手指表演有已披露的局部变化，未宣称逐字完美执行所有prompt偏好。Whisper对F1生成无意义文字和超过8秒的时间戳，不作为听感证据；未调用Gemini或`audio_understand`。

## Requested First-Three Preview

用户明确要求“你先把前三段拼接起来我看下”，已制作原片顺接观看副本：

`/home/reggie/电商/热敷贴/成片/给腰放个暖假-前三段22秒-原片顺接预览.mp4`

actual duration22.326440秒，SHA=`232282e51cf311292543a7263b6a141908879d26484e4f31eb479be76b52a287`。531帧解码图像按源顺序全部相同，962个原AAC packet payload按顺序全部相同，concat未报告非单调时间戳；两个容器接点为8.1、16.2秒。receipt：`first-three-raw-viewing-receipt.json`。

这是按用户要求提供的无重编码原片观看副本，没有新增字幕、配音、音乐或Production state，不是58秒完整成片，不以此推进O2 raw gate。第三段产品特写约在整段18秒处。

## O2 Product Detail Evidence Gap

Native reviewer第3次检查`O2-product-frame.png`与真实`input/04-patch.png`：两图均可见单片米黄长圆端外轮廓、中央略鼓矩形和较平两端，没有明确扣件、绑带或第二片；不能仅因分区/厚薄/透视差异认定换品。finding `O2-P01`为non_blocking外观不确定项，但较大外侧米色区域不能由单帧独立确认是衣物、背衬还是皮肤。

Parent决定`NEEDS_MORE_EVIDENCE`，不把声音确认或形状相似当成隔衣证明；已追加相邻1.75秒frame，仍需明确外缘连续衣纹/褶皱或其他可靠使用证据。如果确认裸肤或错误装置，须有界修复并检查exact新媒体；不能倒写原source PASS。当前无O2 all-PASS diagnosis、无F2 generation request/start/submit。

相关证据：`O2-product-review-adjudication.json`、`O2-human-audio-confirmation.json`、`O2-mcp-analysis.json`。用户此次明确要求查看当前三段，允许作为具体问题诊断展示，不构成作品完成。

## Prepared Successors And Bounds

六段时长为O1=8、F1=8、O2=6、F2=12、F3=9、O3=10秒，HERO=5秒。全部独立canonical trial roots，paid-free master仅拥有creative/Registry/QA，不复制Manifest或付费历史。三个已生成trial保留accepted/VALIDATE状态及各自真实receipt。

F2已通过唯一committer加入F1真实末帧`10-F1-terminal`作为场景参考，绑定F1 exact SHA/frame190；只继承关墙、沙发、人物坐姿、白袜与电话位置，不伪称首帧锁定或QA acceptance。四份素材已沿既有Provider上传owner预提交，`F2-prepared-materials.json`仅有约60分钟本地有效窗口，过期不得修改时间冒充有效。F3的`04-patch`轮廓职责、O3的`06-warmroom`幻想插镜职责已在各自Scene owner明确登记。未来F3应按已接受前序实际袜脚/鞋履状态处理连续性，不凭原稿虚构突然出现的鞋。

预算封套`operator-bound.json`保留6初始调用、0自动重试、500 CRD/次上限、总3000 CRD及6小时窗口；没有增加上限或重置计数。本片实际3次native生成：O1报价112、F1报价112、O2报价84，共报价308积分；正式账本结算尚未确认为已结算金额。旧54秒run三次paid invocation/两次实际生成是保留的predecessor，不与本新批准创意计数混淆。当前没有UNKNOWN或自动重试。

## Minimal Postproduction Work

已备`prepare_film.py`、`compose_film.py`、`render_film.py`，尚未运行完整capture/compose/render。六段原声计划独立保留到P4，HERO本地Kokoro“医健树护腰贴，给腰留点暖意。”已生成3.112667秒，loudnorm后48k mono PCM16；听感待最终用户确认，云语音调用0。CC0配乐按幻想段和收尾选段，ResolvedTimeline独占时序，HyperFrames0.7.103出片。

为解除真实出片阻断，最小共享修复仅在`ad_creative.py`保留base CompositionSpec2.2/2.3/2.4，旧2.0/2.1仍升级至2.2；不再无条件降为2.2导致replacement-audio preview失配。对应`tests/test_production_ad_creative.py`的focused compiler验证5 passed，既有replacement-audio resolver fixture1 passed，语法/导入与diff检查通过；没有完整Harness receipt。capture保留normal-speed map，P4 layer不复制map。

Parent按actual O1 AAC8.057007秒的证据，将P4 native轨裁到对应正常速度画面窗口，0dB及边缘5ms淡入淡出，避免AAC尾部跨镜；Registry保留完整原音轨，不能静音或用TTS替换原对白。新脚本的实际执行、画面版式和最终音轨保留仍待exact成片验证。

## Completion And Learning

当前HEAD=`dcbb93e`，index为空。保留所有foreign dirty；本任务最小源码/测试、计划、记录未commit/push，按film-first先交完整片并获用户认可，再运行相称完整验证与owned-path commit/push。publication=`NOT_PUBLISHED`，58秒成片、正常速度整体观感/最终听感、Production/P6/Final Acceptance尚未完成。

本记录按`record-ai-video-session`保存稳定的三段观看checkpoint。自动`distill-ai-video-learning`评估为`no_candidate`：不同动作/参考条件的三个镜头不是隔离变量对照；尚有产品隔衣缺证，单次schema修复测试不构成跨实验媒体规律。不创建占位claim，不修改Skill/Policy/Gate或全局memory。没有为记录运行新Provider、媒体、网络调用或额外测试。
