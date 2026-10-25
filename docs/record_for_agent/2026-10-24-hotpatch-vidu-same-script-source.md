---
record_kind: session_summary
topic_id: hotpatch-vidu-same-script-source
learning_eligibility: ineligible
---

# Hotpatch Vidu Same-Script Source Review

Date: 2026-10-24 (Asia/Hong_Kong)

## Supersession Notice — Sound Feedback And Watermark Edit

下文原片交付、后期未执行和听音待审描述是第一次原片检查点的历史状态。用户随后明确反馈“我感觉很奇怪为什么一种解说感觉”“为什么会一直在说话”，并要求修改 Provider Skill；exact source 的对白/留白样式因此为 **FAIL**，逐字台词准确性仍为 NOT_EVALUATED，未调用额外音频理解服务。用户另行授权在这份未接受的原片上仅添加商户动态水印并保存预设，不改变源 Gate、activation 或 P6；当前扩展结果见文末。

2026-10-24局部修订：用户要求“开头的颜色换成橙色,然后最后几秒纯音乐太奇怪了”。当时观看文件为 `/home/reggie/电商/热敷贴/成片/给腰放个暖假-Vidu-橙色开场-收尾修订.mp4`（45秒），声音调整与验收边界保留在对应末节。

2026-10-25最新局部修订：用户改为“第一个镜头换成棕色”。当前观看文件为 `/home/reggie/电商/热敷贴/成片/给腰放个暖假-Vidu-棕色开场-收尾修订.mp4`（45秒）；此前橙色版与47秒水印版完整保留，末段声音和动态水印沿用45秒修订版。

## User Scope And Actual Result

用户认可上一条47秒观看版后要求“可以,vidu再做一条”，随后指出原片末镜包装盒过大；用户澄清长8厘米、宽7厘米指“橙色包装盒”，不是贴片。用户最终决定“用vidu再做一下吧,这不管了,大小你记住就好”，不再修旧片，并进一步要求“vidu都不用该稿子就直接换个provider看下”。Parent按“不用改稿，只换Provider看效果”执行：沿用《给腰放个暖假》原47秒剧情、台词与商品回切，新增尺寸事实，不采用曾准备的“棉被山”新故事。

已实际生成并提供Vidu同稿对照原片：`/home/reggie/电商/热敷贴/成片/给腰放个暖假-Vidu同稿原片-47秒-待审看.mp4`。SHA=`a4307dd05faab06f45c8cd9bedab029613824e5070c2645b25f5af0e763a0c99`，27,989,900 bytes，复制后SHA与canonical source candidate完全相同，原AAC音轨、AIGC metadata与画面未改。此文件是用户要求的Provider效果对照/诊断展示，有明确缺陷，**不是已通过验收的广告定稿**。未添加后期水印、未运行后期render、未激活source、未发布。

## Canonical Execution Evidence

Run：`runs/hotpatch-vidu-ad-20261024-001/`。正式源project=`production-original-v3`，project/local task=`hotpatch-vidu-ad-20261024-001-original-v3`，attempt=`hotpatch-vidu-ad-20261024-001-original-v3-source-01`，remote task=`1011583092994904064`。全程只实际一次generation POST，HTTP200 accepted，后续显式query processing→success，再canonical fetch；无自动重试或第二次生成。服务为国内官方`https://api.vidu.cn/ent/v2/ad-one-click`，不是可指定底层Q3模型的接口。完成状态的官方task response报告本次1363 credits；没有将既有1000 CNY operator ceiling当实际价格或做汇率换算。

Exact request hash=`14e1c65be874918ce4d026e575dd163e40b36315f151a3bd8e3a3d46e57a2fd8`，preview fingerprint=`c90818b452237766c21f766788607c43c307acc7d5ae284d18d7ff29f087f8c6`，prompt字节SHA=`0087050ae0240fa272e3fd6ce088fce9c335cdc33b1f5367644256f1ccf86106`，1431字符含末尾换行，在官方2000字符内；47秒、9:16、中文、creative=true、submit limit1。引用顺序为02-carton→04-patch→13-O1-office→10-F1-terminal→12-F2-wide，每张图从明确source Project Registry验证bytes/size/hash，首图商品包装。原稿技术适配为将已经观看的editorial意图合并到whole-ad请求、重映射参考编号；未加新的剧情或台词，不宣称源Prompt完全相同、逐像素复现或受控A/B。

最早`production`与后续`production-size-v2`只是纯本地bootstrap/prepare，均unsubmitted、0 paid、0 credential/network；旧root和封存输入保留，不能把新Project当作消费清零。第三份正式选择只替换尚未提交的作者输入，`execute_ad.py`锁定original-v3，所有旧草案仍在。既有内部Vidu ceiling只保留数额、币种和trust并封新一小时窗口，授权来自当前用户与constitution，未继承九号车任务“没有上限”的旧授权。Profile和authoring lineage见`sealed-preparation-original-v3/`。

一次本地credential preflight失败源于进程缺失DBUS_SESSION_BUS_ADDRESS；没有发出Provider POST。验证同UID拥有的`/run/user/<uid>/bus`为Unix socket，恢复同一用户session bus后，原exact Secret Service supplier可读取；没有寻找其它credential source，key只留进程内存且未打印/持久化。见`pre-submit-credential-blocker.json`的后续supersession与`pre-submit-check.json`。

Source Project有一条未参与实际ad wire的Character identity prose沿用旧新演员描述，与原角色复现意图不一致；正式请求实际消费封存prompt与五张图。此未用metadata差异记录为nonblocking，不宣称已经清理，不能借实际参考正确掩盖canonical prose并不相同。

## Exact Media Findings

显式调用project-local `video-analysis.video_analyze`，绑定source SHA，每1秒共47帧，关闭ASR与audio understanding；Parent抽查全片分布帧并逐看23/24与42–46秒关键问题。输入是同一exact MP4，不使用tool success替代媒体验收。`vidu-original-mcp-analysis.json`保存去base64分析；其probe为1084×1914、24fps、1127帧、AAC48k mono，容器约47秒。Pinned ffprobe独立测得format47.018秒，MCP自带probe为47.040秒，保留两种原始测量，不伪造1080×1920或1128帧。

明确问题：23–24秒衣服被撩起，贴片直接贴在裸露腰部皮肤上，违反用户明确“按说明贴在衣物上”；开头0–1秒及16–17秒贴衣服不抵消后面的错误。42–46秒，原本搭肩盖腿的米白被子变成带纽扣门襟的无袖厚外套/马甲，服装/道具状态连续性失败；0秒灰裤与后续黑裤也有变化。套房与电话、真人小盒收尾及大体叙事有保留，但不能因整体相像而宣称完整原稿/关键动作均通过。盒子比旧大盒明显缩小，未声称实际镜头可精确计量8×7厘米，生成细字亦未宣称完全正确。

`wholead-post-source-gate.json`：identity/space-camera/truth FAIL，action/performance/sound保留NOT_EVALUATED；未填假五项PASS以放行后期。没有下一次submit。原声全轨可完整解码，RMS约-14.506669dBFS、peak约-0.565680dBFS，NaN/Inf为0；声音语义、说话人、全部台词、口型同步与听感待用户听审。没有调用Gemini或其它音频理解Provider，也没有挪用旧Jimeng听音PASS。

## Delivery And Unused Post Recipe

`vidu-original-delivery-receipt.json`绑定external观看副本、exact SHA、native audio unchanged、1363 task credits、诊断展示范围与NOT_PUBLISHED；`vidu-audio-technical-review.json`是音频技术证据。此次只换Provider看效果，原片保留全部声音与缺陷，不做后期遮掩，也不称为已验收commercial delivery。

bounded post worker核对Haokou真实历史后修正了自己“没有安全导入路线”的初始判断：没有通用自动video-import owner不等于禁止canonical bootstrap建立独立imported-video审片Project。新`wholead-post.py`沿既有bootstrap→load→CompositionSpec→ResolvedTimeline→HyperFrames配方，拟保留candidate原MP4、完整原声派生PCM和moving TextDesign水印，并将candidate receipt及导入provenance一起捕获进新Project。它仅通过AST/import静态检查，因实际source Gate FAIL没有运行prepare/compose/render，不声称runtime已验证，更不伪造qualification-preview capture或source activation。

## Previous Source-Audit Repair Closure

上一条47秒影片所需的HyperFrames source-audit一行修复与两例回归测试及主记录，已单独commit/push到main：`0734ee6be99a235f62a438bd3f87860b39248486`，`git ls-remote origin refs/heads/main`核对相同SHA；只提交三个owned paths，其余约80项dirty/index保留。相关模块204 PASS /3 skipped。

Exact staged Harness第一次在libass native dependency失败：system harfbuzz请求FT_Get_Transform但进程已载入不兼容FreeType，1042 PASS /18 skipped /1 failed；未隐藏或改测试。仅进程预载已安装system`/lib/x86_64-linux-gnu/libfreetype.so.6`后，失败case单独PASS，继而同一staged内容完整适用Harness PASS，receipt=`.agent/harness/runs/hotpatch-watermark-source-audit-native-env-20261024/receipt.json`。`make harness-receipt`核验fresh/integrity/coverage/complete_completion_proof均true后才commit，旧失败receipt保留。未修改全局native库或foreign source，不把此工程PASS当作本次Vidu媒体验收。

## Checkpoint And Learning

record-ai-video-session创建本次唯一Vidu主记录，distill-ai-video-learning评估no_candidate：只有一次whole-ad新实验，与旧Seedance多Shot的执行机制、reference conditioning和内部调度不同，未控制seed/内部模型，也尚无用户Vidu评价；不能从这些缺陷推成所有Vidu模型的一般规律或性能排名。未修改Skill/Policy/Gate、没有新增学习claim。用户要求“大小记住”已仅写入一条ad-hoc memory extension，未直接编辑MEMORY.md。

当前稳定边界是：原片已给用户作同稿Provider对照，已知缺陷已明示，source未接受、后期未运行、无新付费attempt。按照film-first保留此新制作记录待审片反馈后处理Git；不为记录新增Provider、媒体、网络或额外测试。

检查点复核只重开既有delivery receipt、source Gate、完成态积分记录与本地Git信息，确认上述SHA、27,989,900 bytes、1363 credits及FAIL/NOT_EVALUATED边界一致；未再次分析或处理MP4。主记录为本文件，旧连续性记录仅补直接supersession notice，不新增重复记录。自动学习复评仍为no_candidate；记录变更保持本地、未stage/commit，既有无关dirty与空index不动，未执行网络、Provider、媒体或额外测试。

## Vidu Authoring Correction

用户直接要求“给这个provider的skill修改下,下次不能这样”。新增本地原创 `.agents/skills/vidu-authoring/SKILL.md`，并在 `open-video`、control-plane creative routing 和 `docs/vidu-ad-provider.md` 接入。该 Skill 区分具体 Vidu 视频模型与 `ad-one-click` 整片服务：当前整片接口具备自动营销/TTS，但没有独立逐说话人、逐句窗口或无口播时段控制。角色对白、反应及动作留白属于原稿硬要求时，不把整片服务当作同 Provider 的等价替换；明确需要连续解说的稿件仍可使用。能力未知返回既有 strategy/capability owner，不猜模型、不加第二音频合同。

只换 Provider 必须保留原句、说话人、顺序和无口播段；声音覆盖不等于一直说话。实际成片出现额外解说按声音意图不符处理，不能用音轨存在/波形/ASR或旧片确认放行。用户自行听音的偏好保持。失败归因区分服务、原稿、模型和后期叠声，不声称本会话已听音或证明了服务内部实现，也不盲重抽或整轨静音。此为当前用户明确授权的 Skill 修订，不是自动 Learning Claim adoption。

`skill-creator/scripts/quick_validate.py` 当前通过，owned diff whitespace 检查通过；native `reviewer_high` 在离线三个场景逐项推演：对白加留白阻止不匹配服务、明确连续解说允许、额外解说反馈绑定 exact source 并停止盲试，无 findings。详见 run 下 `vidu-skill-forward-check.json` 与 `vidu-user-audio-feedback.json`。这些证明 Agent 指导与入口，不证明下一次模型实际音效、人声或媒体验收。没有新 Provider 调用。

## V Watermark Review Copy And Editable Preset

用户将水印路径修订为左上→下方中间→右上，文本“乐喜呵护商贸”；预设保存到 `/home/reggie/电商/热敷贴/预设/V字动态水印.json`，`name` 和 `text` 可编辑，轨迹、字号、颜色和透明度随同保存。实际本片封存 `watermark-v-preset.json`，SHA=`46d04d6f2051e6a61b2d387258c75e0c1752caf22bb54c5a9bcc018786299166`。新增纯作者模块 `production/watermark_preset.py` 将可编辑预设投影到既有 TextDesign，按当前文字嵌入字体，跨 Shot 延续全片轨迹；不会建立第二 timeline 或 renderer。4 项 focused tests 覆盖 V 轨迹、改名改字、跨切点连续和非法/越界输入，全部通过。

新审片 Project 的 bootstrap 输入捕获原 source receipt、未通过的 Gate 和用户仅编辑水印的授权，不冒充 source QA/activation。r1 composition 的 video time map 被同片音频 guard 拒绝；保留失败后改为原1127帧+实际末帧 PNG 延长2帧。r2 又由原 `1127/24` 浮点秒数经 CEILING 得1128帧，不能匹配1127帧 trim；保留 r2，r3 使用 content-driven 读回实际源 policy。最终 r3 单一 `ResolvedTimeline` 为1129帧、2,258,000 samples、1084×1914/24fps；原1127帧保持1×，只延长末帧2帧承接完整原声。原声作为 P4 global track，无新增旁白或音乐。

r3 render 在缓存 Chrome for Testing148 的 HyperFrames check 发生 `sweep_static`。读取 exact Haokou历史证据后，对同一 r3 source 仅换已安装 system Chrome149.0.7827.53，check 通过；file:// 没有注入 runtime 时 stage高度0并非真实 check serving 的结论。未修改 node_modules、共享 renderer 或降低检查。r4 使用同一 Project/spec/timeline，只换既有 browser_path 和新 staging；HyperFrames0.7.103 lint/check 均0 errors/0 warnings，实际渲染与 adapter 输出核验通过。所有失败 staging 与证据保留。

已交付观看副本 `/home/reggie/电商/热敷贴/成片/给腰放个暖假-Vidu-V字动态水印.mp4`，SHA=`490d45d8e1a02d998a90a99b218bed5eeae07bc93f5b5f4e95d98b6bee8b20ee`，65,198,684 bytes，47.041667秒。显式 project-local `video-analysis.video_analyze` 对 exact verified MP4 抽取0/11.75/23.5/35.25/47秒画面，关闭ASR/audio understanding；Parent看到水印沿V移动、无额外底板。原片的隔衣错误、服装连续性和解说样式问题保留，不称广告定稿。

音频技术核对：完整源解码2,256,896个48k stereo采样与P4 WAV前缀逐字节相等，尾部只加1104个静音采样。最终AAC相对源存在1024采样/21.333毫秒的编码起始对齐差，小于一帧；按adapter报告的priming对齐后相关系数0.999991、gain fit0.999562，全部原声覆盖，未声称AAC字节相同或已亲自听音。证据在 `watermark-v-edit-audio-preservation.json`。

交付receipt相对run为 `watermark-v-edit-delivery-receipt.json`，render为 `watermark-v-edit-render-r4.json`，MCP为 `watermark-v-edit-mcp-analysis.json`；source Gate unchanged、P6 NOT_EVALUATED、NOT_PUBLISHED。此次水印和Skill修订新增Provider调用0次、生成积分0。仅做必要局部检查与实际出片，水印视觉的人类审片仍待用户；不为此记录扩跑完整工程套件。自动学习复评no_candidate：一个whole-ad样本和同链局部导出不构成跨独立实验结论；Skill修改来自用户直接授权，不推导普遍模型质量或新增claim。

Skill 指导属于本次独立明确的文本修订请求，局部验证及只读场景审查完成后，仅4个 owned Skill/routing/doc 文件提交为 `31fe5b1f92462b83f5a075302c971f379f7d9dd3`，push到远端main并核验 `ls-remote` SHA一致；没有夹带水印模块、测试、记录或其它窗口 dirty。水印模块/测试及制作记录仍按film-first保留本地待用户实际审片后处理后续验证与提交；没有将审片待定包装为已完成工程发布。

检查点 `ai-video-record-53b17c606c95e06c` 复核了已有交付 receipt、Skill 场景记录、当前 HEAD 与空 index，以上状态一致；更新本主记录而不新增重复记录，保留全部无关 dirty。自动学习评估仍为 `no_candidate`，没有新增独立实验或需要修订的既有 claim。此次检查点未执行 Provider、媒体处理、网络或额外测试。

## Orange Opening And Ending Pacing Repair

当前用户只要求开头贴片橙色与末段音乐收尾修复，沿用原片、商户文字与全片V字路径，不重新设计剧情或重抽整片。原片前53帧（0–2.208333秒）是开头特写。Parent对固定原片做局部视频色彩派生：纸面纹理点LK跟踪/稳健仿射，独立手部轮廓跟踪，限制改色区域并处理指尖遮挡；保留源亮暗纹理，改变色相/饱和度，没有给整个画面加橙色滤镜。初版暖色阴影被误判为皮肤造成纸面灰色锯齿，后续修正折指轮廓和早期指尖接触；五个派生版本及明确predecessor/verdict留在run中，均是同一原片局部修复链，不是独立模型实验。只有r5进入新review Project；失败版本未交付成片。

r5 visual-only开场MP4 SHA=`b1798b1ca2eb725c6f4b9b53686019c23aa11505c3a66e929232ae5af9f302ce`，53帧、1084×1914、24fps、35,222,699 bytes。显式project-local MCP检查exact MP4的0/.4/.8/1.2/1.6/2.0秒帧，Parent另看原/改对照和边界细节。输入封存 `orange-ending-edit/edit-input-r5.json`，含原话、保留要求、原片/派生/推导收据/MCP身份和音频编辑样本表。不将局部改色检查写成整片表演、原声或source质量PASS。

原水印版的local Whisper辅助转写最后品牌语在37.28–40.06秒，随后约7秒仅音乐；转写同音字错误较多，只用作时间辅助，不代听音。新声音编排用原P4 PCM，不新增TTS或音频理解Provider：原声0–37.28秒保持，37.28–41.5秒放同源无口播音乐过渡，原37.28–40.10秒品牌句移到41.5–44.32秒真人手持产品末镜，随后0.68秒音乐并在最后0.5秒淡出。前段与品牌句在实际P4 premix逐字节等于原PCM相应区间；没有整轨静音或丢失前段对白/音效。最终local ASR辅助识别末句为41.52–44.28秒，保留human listening NOT_EVALUATED。

Native worker只拥有本次run内 `compose_edit.py` 与其新Project/prep/spec/timeline；Parent拥有局部颜色资产、输入封存、render及最终QA，未写共享Runtime。两处canonical严格检查按现有合同解决：本地预处理文件进入新Project的获取方式是IMPORTED，保留DERIVED SourceReference、原asset ancestry、tool/receipt/fingerprint；没有伪造Provider生成。原四段global P4 span不能满足REPLACE单span覆盖整个Shot的约束，因此两条visual MP4明确MUTE内嵌音频，四条独立P4原声span仍覆盖全片；未放宽guard或将最终声音静音。失败bootstrap留下的空自有目录核实后移除，已知失败说明保留，未删除完整orphan证据。

最终唯一ResolvedTimeline指纹=`4a258550d4b96852794863dd3f5231b303ba37bc786552366cb815d3b9527b9e`，1080帧/2,160,000 samples。前53帧使用r5，后1027帧连续使用原MP4的53–1079帧，均1×，全片45秒。两段V字TextDesign按全局路径跨零时长CUT连续；预设不改名、不改字。HyperFrames0.7.103 + system Chrome149实际render，lint/check均0 errors/0 warnings，adapter输出verification通过。Worker既有watermark/source-audio focused 19项及策略相关6项通过；未运行完整工程套件，不以这些测试代媒体验收。

交付 `/home/reggie/电商/热敷贴/成片/给腰放个暖假-Vidu-橙色开场-收尾修订.mp4`，SHA=`95200ea656cc0768ef750984d30ef52d7db3428af351800fdda99c9f36e3306d`，63,800,010 bytes；external副本与verified snapshot核对相同。显式MCP对exact成片检查元数据/抽帧，Parent另查1.208/2.167/2.208/41.5/43/44.958秒，确认开场橙色、原切点、V字水印及真人产品末镜。最终AAC相对P4为1024采样起始对齐差，对齐相关系数0.99999064，品牌语完整覆盖，混音尾部到0。技术证据不等于亲自听音或用户接受。

本轮证据统一在 `runs/hotpatch-vidu-ad-20261024-001/orange-ending-edit/`：`delivery-receipt.json`、`render-receipt-v1.json`、`final-mcp-analysis.json`、`final-detail-contact.png`、`final-audio-review.json`、`final-asr-auxiliary.json`。新Provider generation 0次/0积分，无新增Gemini/音频理解；原片隔衣使用、服装连续性与持续解说样式的旧失败仍保留，source未接受、P6 NOT_EVALUATED、NOT_PUBLISHED。新修订版供用户审看；film-first下run配方/本主记录与既有水印工程改动保留本地，未夹带无关dirty提交或为交片扩跑完整Harness。

稳定交片后按record-ai-video-session更新同一主记录；distill-ai-video-learning评估no_candidate：本次多个局部派生共享一个exact源与目标，没有跨独立实验的已隔离变量结论，不新增Learning Claim或修改Skill/Policy/Gate。

## Brown Opening Variant — 2026-10-25

用户只将第一个镜头贴片颜色改为棕色。沿用上一版53帧纸面/手部跟踪与遮挡matte，逐帧重建并核对matte像素计数相同，仅调整色相/饱和度/亮度为自然棕褐色（HSV H12/S160/V×0.72）。新开场派生SHA=`35a3761edcb8c719c42eaa0fec176201b09a95c6514de95423f017e451111bc8`，53帧，33,884,526 bytes；未重做动作或重新生成模型媒体。显式MCP检查exact开场0/.4/.8/1.2/1.6/2.0秒，Parent看接触/轮廓及纹理。当前请求使用既有局部编辑owner，未新增共享Runtime功能或测试工程。

独立review Project通过同一canonical bootstrap/strict loader/CompositionSpec/ResolvedTimeline与HyperFrames0.7.103导出，保留1080帧/45秒、同一原片53帧后的1027帧continuation、原四段P4编排及V字商户水印。与上一版相比，ResolvedTimeline audio_spans逐字段相同，P4 premix WAV全字节相同（SHA=`683957bcb2fdcd01fd73c0173f3999fc44f30c135fc0d90b25ab6bc2e844c495`），两个最终MP4全轨解码PCM也逐字节相同（SHA=`e44a02a27f45ed0aa1e6f1ee10dd393635eb8fc6611fac22195f08327cf27ac4`）；因此未重复ASR或音频理解，也不声明新的人工听音PASS。

实际lint/check均0 errors/0 warnings，adapter输出verification通过；project-local MCP绑定最终SHA检查0/11.2/22.4/33.6/44.8秒，确认棕色开场、水印和末镜。观看副本 `/home/reggie/电商/热敷贴/成片/给腰放个暖假-Vidu-棕色开场-收尾修订.mp4`，SHA=`818ab8729b3d2335e5d816c5fae050c22e01a20a3133759fdab3b93531ae2551`，63,634,624 bytes，复制后SHA核对一致。

本轮receipt相对repo：`runs/hotpatch-vidu-ad-20261024-001/brown-opening-edit-20261025/delivery-receipt.json`；同目录有`render-receipt-v1.json`、`final-mcp-analysis.json`、`audio-preservation-review.json`。新增Provider/生成调用0次、生成积分0；原source Gate及其已知失败保持，P6 NOT_EVALUATED、NOT_PUBLISHED，颜色观感待用户审片。旧文件/无关dirty/index保持，film-first下不为局部修片扩跑完整Harness或提前提交制作改动。

record-ai-video-session更新此同一主记录；自动distill-ai-video-learning评估no_candidate：这是同一原片链的单一颜色选择，不构成新的独立模型实验或通用改色能力结论。
