---
record_kind: media_experiment
topic_id: reusable-canvas-mecha-ant-production
learning_eligibility: eligible
evidence_index_version: "1"
---

# Mecha Ant Canvas Seedance 480p And MCP Gate

Date: 2026-10-11

## Goal And Current Outcome

用户选择现有机甲画布继续[spec](../superpowers/specs/2026-10-11-reusable-canvas-production-harness.md)，
保留《美丑》拒绝证据，并继续Seedance480p授权。一次实际生成取得完整15秒蚂蚁脱困单元的raw MP4。
它来自已读development样本《机魂觉醒》，不是holdout、完整机甲片或代表性Pilot。

已知视觉FAIL：受阻段显示主角完整头背和身体，是第三人称后方跟拍，违反封存的主角眼睛视点。
初次analyzer未实际听看声音/完整连续运动，保持NOT_EVALUATED；用户后续已确认声音，见下节独立human证据。
canonical experience仍为`EVIDENCE_GAP + QUALITY_FAILURE`，
`validate`实际被Gate拒绝，Manifest未变；没有activation、composition、render或下一Shot提交。
初始停点为`running`/phase`validate`；后续正常owner已显式abandon，见下节superseding证据，未更改原诊断。
完整spec尚未完成，AC-2完整资格仍PARTIAL，AC-7尚未验收。

后续修复入口已验证并发布；第二次机甲物理POST被HTTP403 / `AccountOverdueError`拒绝，
canonical `KNOWN_NO_EFFECT`、attempt failed、next action stop，没有新task ID或MP4。
当前任务累计3次物理POST（Beauty1、机甲原片1、修复1），本次追加单元已耗尽，未重复提交。
当前选定`doubao-seedance-2-0-fast-260128` / 480p仍受该计费拒绝阻断。用户随后明确“别用2.5太贵了”，
停止切换2.5的准备，本任务2.5提交数为0。用户购买的2.5资源包确实仍有余量，但不能抵扣2.0 Fast；
不把cash negative扩大解释为所有Seedance模型都不可用。详情与证据边界见下节，未估算市场费用。

## Source And Creative Decisions

证据根：`runs/canvas-mecha-seedance480-20261011-001/`。source node`node_fgfrmwy9ss`，
引用`node_pftt2pa76z`/resource`ea03ccdb-4eaa-4d93-9ea9-60a737931582`。
完整source inspection保留93nodes/118edges及未支持subject/audio/timeline字段；只明确选择可执行的蚂蚁单元，
不根据名称或坐标拼整片。原文、source版本和adaptation分别保留。

一张场景参考用于破瓶、沙土、叶石、黑色蚂蚁及二维手绘风格，不当first_frame或独立角色portrait。
平台预览WebP720×408，85136bytes，SHA`56f746591db43cc9b501ce1d9dd45bb02b4c7f9054261d86144029887eb61733`；
同像素RGB PNG564238bytes，SHA`2713555c702c7269139ddbb09f446bfbbd11b3a6907a87aa892d91b09e5be617`。
原1920×1088仅为平台元信息，没有冒充取回原图/原generator receipt。一次尝试更高分辨率URL返回403，
随后从实际DOM预览导出；这个只读素材GET不计视频POST。signed URL不进入本记录。

Director三个内部摄影段落：3秒建立顺时针围瓶困境，8秒主角第一人称碰撞/穿叶/绕石并坚持，
4秒一次越出外缘并带领同伴。它们在一次15秒native generation中完成，未把Provider上限当导演依据。
群体场景没有独立主角portrait，取消Agent误加的Character身份锁；完整动作、主观视点与跟随结果仍保留。
无对白源文不被改成新增对白；保留音效、无BGM/字幕。完整15项raw QA要求没有在看到结果后删改。

独立concept调用`773cb6b3-6175-4214-b6f1-cde38eeca1b3`，qualified deep route
`4f2d5dc8-4234-4665-b382-e82f1ad6cc00`，receipt为PARSED/exit0、5个actualRead、2个wire requests。
report SHA`3d69b8daa08f8dce932d1395bd0a1b8ad27913fcc9ea93026322a521e9154346`。
Parent确认并修正POV自相矛盾、重复脱圈、顺时针绑定及动作/分镜/正面音效检查；
864×496疑问由当前Seedance2.0 capability raster反证，不采用2.5的854×480。
补充复核`a1e60f57-5978-4a1c-8649-7070e33bbb41`读5份文件、2wire requests，
终态`STRUCTURED_OUTPUT_EXHAUSTED`/exit1，无可采纳报告、不当PASS，也未自动重试。
Parent逐项裁决与Director/goal-binding/native compiler检查独立成立，不冒称补充调用审过当前bytes。

## Paid Execution And Exact Artifact

现有generic data-configured caller只调用`CanvasProductionService`与既有owners。
用户指定`.env`的exact private supplier继续使用，credential仅内存、不输出、不复制。
human素材使用权原声明与本次明确来源选择分别封存；场景无人物，实际分类为ordinary non-character image。
新profile消费既有operator内部定额`50_000_000`microCNY，非市场价或账单。
新单元submit上限1、auto resample0，前序《美丑》实际1保持，任务累计上限/实际均2。
exact preview、source/Registry bytes、egress、预算、durable intent和one-use permit实际重验。

| Item | Actual evidence |
| --- | --- |
| Attempt | `canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7` |
| Model / mode | `doubao-seedance-2-0-fast-260128` / `reference_to_video` |
| Request | 15秒、480p16:9、24fps、`generate_audio=true`、1张PNG |
| Request input SHA | `5b5a91a92b281fe3cd0b2b8eb3a9fbe2e6a1177f439d0ff3da2dedb8b63c5e2e` |
| Resolved SHA | `628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19` |
| Prompt SHA | `b2f7e2890c3bb023f8b19f7af62224e200121cb4a523e844343d740098cc856c` |
| POST | HTTP200；757282bytes；bodySHA`4cde6e04c5847829965039780c8e54217df3e693e2d054759538c99ea5ca585e` |
| Paid receipt | `production/state/paid-provider/submits/9cc4e4f43c705bb5365ab4913180f1012beec060a2052f7dc2922a56826efe51.json` |
| Paid receipt file SHA | `ed2f500fd2643c91da3e4476be29944846189787e6e776c025a60eef2295086b` |
| Raw MP4 | `production/state/video-generation/fetch/files/265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36.mp4` |
| MP4 identity | SHA`265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36`；5976142bytes |
| Probe | 15.104秒容器；361帧；864×496/24fps/H264；AAC32000Hz/stereo |
| Calls | 1物理POST；7成功状态GET；fetch前1重查GET；1媒体download；0生成重试/下一Shot |

两次poll helper缺少显式transport，均在本地抛错而未发网络请求。核对constructor后仅补现有transport注入，
同task继续查询；未重新POST。fetch成功后的helper JSON序列化错误从committer重开真实fetch receipt修复，
没有重复fetch。开发telemetry与Production权威状态分开，错误/消费历史不清零。

## Per-Shot Evidence And Gate

exact MP4落盘后首先显式project-local`video_analyze`，0.5秒间隔取31帧，不转写/下载Whisper。
抽查视点范围0–15秒，主角背部明确可见；抽帧不等于完整正常速度观看/听辨。
scene detector在threshold0.4报告1scene，不用它否定实际可见切镜或代签摄影要求。
修复下节调用路径后，normal`service.evaluate()`再次实际调用同MCP，保存0/5/10/15秒帧及原response。
第5/10秒本地证据足以反证literal POV；不把局部反证升级为全部运动/声音判定。

canonical分析`canonical-mcp-analysis.json`，source`generation-evaluation-source.json`，
diagnosis`generation-media-diagnosis.json`；experience pointer：
`production/state/video-generation/experience/00efcfc58d26514cc8eda1b22d2bf43be0f22332f189d8012e6f18c0f3c4c425.json`。
experience fileSHA`316642e05f6bf2a580b24221983f5d3a3410df65a4fe8158a579c817d66fa7e4`。

- `pov`、`identity_state_camera`、`source_fidelity`、`reasonable_coverage`：FAIL，均包含被实际局部反证的视点义务。
- `closeups`：PASS，仅证明大幅近景存在，不代签镜头合理性。
- `audio/sfx/no_music`、完整运动/障碍/跟随等其余10项：NOT_EVALUATED；音轨存在不证明已听或音画同步。

`canonical-gate-blocked.json`记录validate抛出`production_project_invalid`，非retryable且Manifest revision不变。
正常evaluate replay只重开已保存source/analysis，diagnosis相同、无新MCP/Provider调用或Manifest write。
这里保留待补证的validate状态，未调用terminal abandonment，未settle费用或签人类验收。

### Human Audio Confirmation

用户对exact诊断MP4完整声音核对回复“音效符合要求，无配乐或对白”。
`human-audio-confirmation.json`绑定同MP4 SHA/size、实际request item与回复，作为独立`HUMAN_AUDIO`证据。
它补齐声音反馈，不推出用户完整视觉认可；也不把真实human observation改称analyzer调用、覆盖旧source中的
NOT_EVALUATED或签Production/P6/Final Acceptance。已知POV失败保持。

### Human Motion Confirmation

用户对同一exact诊断MP4回复“这些动作都能看清，过程连贯”。问题明确核对顺时针围瓶、受撞后继续、
穿叶绕石、脱圈带出同伴与动作连续，且预先披露第一人称FAIL不属于本次动作确认。
`human-motion-confirmation.json`保留actual reply/item、MP4 SHA/size与human身份；不代签POV、旧analyzer或最终接受。

## Known-Failure Closure And Shared Repair

上述human证据不属于POST前选定的旧analyzer-only authority。两次真实MCP分析与canonical replay不能
在同bytes上提供完整听辨/连续动作proof；继续同一抽样路线不能补齐formal gaps或改变POV pixels。
Parent记录这个明确补证耗尽理由，正常`ProductionStateCommitter.abandon_video_generation`关闭已知结果。
`known-failure-closure.json`与canonical `generation-quality-rejection/2` receipt保留原FAIL、10项NE及原QA：
Manifest26→27、attempt `failed`，closure hash`ce239bba1e96380c4e65d6282dd7849cebd5406aac861c5c9607e67e49ceca1c`。
原experience file SHA仍`316642e05f6bf2a580b24221983f5d3a3410df65a4fe8158a579c817d66fa7e4`，原MP4未改，
没有new attempt/POST、费用settlement或adoption。两次closure后的诊断metadata helper序列化失败，
仅按exact attempt读回真实receipt修复metadata，没有重新关闭或恢复未知结果。

readonly `canvas_repair_path` mapping证实底层已支持closed mixed failure后的manual intervention，
Canvas facade却只允许无attempt准备，或因multiple attempts一律阻断。新`prepare_repair` / `start_repair`
调用原orchestrator并保留same-task历史/消费；`canvas_recovery`只从已关闭前序的canonical binding读取无分支
唯一successor，不以日期/顺序猜版本，不新增writer/permit/自动retry。
最初RED复现缺入口；新7项回归实际验证normal committer/reader下的失败closure→explicit planner→successor，
完整后继submit/fetch/Gate/validate/activate→下一Shot，另验预算耗尽、task改名、unknown、fork、mixed closure和replay。
独立生成的scripted green MP4只防止测试错误复用old failed bytes，不证明真实POV或Provider效果。
两Canvas suites共同14项通过（追加mixed test后repair suite7项通过）；共享slice的exact Harness单独运行。

下一媒体候选`repair-prompt-v1/`只调整native prompt结构与观察者视野几何，保留reference/model/mode、
15秒480p、原文动作和声音。它是待独立concept审查及preflight的candidate；至此累计实际POST仍2，
没有新封套、permit或新片PASS。完整spec/holdout/final render/用户最终听看仍未完成。

### Prospective Proof And One Bounded Submission

上述candidate checkpoint现由`repair-prompt-v3/`的真实准备/提交结果取代，v1/v2证据保留。
同一Production根、Shot和task继续；实际native compiler前后比较仅`prompt_text`变化，
model/profile/mode/场景PNG/15秒480p/native audio保持，随机seed不可控单列。
新的表达删除序列化enum/default，按原3/8/4秒段落组织观察者视野：贴地视点、侧方蚂蚁腿、前方叶隙/石头，
不把主角背部放在主观段前方；原文行动/声音及一次脱圈保持，未采用参考图导致POV偏差的未经证实假设。

受管read-only concept调用`288df287-d04f-4c94-ba32-f3cc24fa9b1e`，deep qualified route，
seal`d4279170d6ffa3f388fa5db17d020887cffa59cc3f0f25f0d15cfde4463645a6`，
reportSHA`31392808185cb8f96f169bc6156df3b9627a31e7110edfb583d552cbb862d06b`。
actual5个Read、2个wire requests、exit0；Parent核对exact read bytes并裁决残余“跟随”措辞。
Kimi只审v1，v2/v3两行视点说明及exact原文substring的compiler修正由Parent检查，不冒称新bytes独立审过。
这不证明实际视频效果，也不替代implementation Risk Gate。

原QA把完整运动/听辨选给只能probe/sample的analyzer，后续human回答不能倒填旧source。
正常`activate_qa_policy`选择prospective policy v3 / final-output goal v2，保留15项raw hard observables与
18项final observables，13项连续运动/声音/复合要求选择fresh human proof，`pov`/`closeups`只选局部帧观察。
新QA SHA`e027a9395d90e7cf0e8c9d3d1404b8f3b1d3cec79327316d4a7a24bde9149c11`；
旧QA、quality-rejection、全部NE和失败媒体bytes保持。当前human authority没有新片finding。
既有planner实际返回`GENERATE_ONCE` / `intervention=None`：explicit goal revision保留旧失败，
不宣称canonical intervention已选中或修复成功。单变量比较另由actual compiled comparison核验。

Parent在当前任务有限预算/恢复授权内封存追加单元1次POST、0重抽、45分钟；
保留旧机甲1次消费、原ceiling1，显式扩展same-task ceiling到2，任务总物理ceiling2→3。
现有operator bound每call`50_000_000`microCNY保持，project ceiling`50_000_000`→`100_000_000`，
不是价格或账单；旧原片actual cost未知、reserved状态保持。
normal money extension hash`937fb1b05f4794d74547ac6b083ca64523d795c0e219f91fda5ed28e8ae6d570`，
quota extension hash`d6d092d9397c4eb683e430d75355ca98f6e41d15ef6dfa4ea850b0c1e928baff`，
新exact preview/authorization/egress、Director/goal-binding和pre-submit preflight均在POST前封存。
没有新Provider、credential来源、图像或模式切换。

| Item | Repair submission evidence |
| --- | --- |
| Attempt | `canvas-b632cd4c587aa7a8df7640c34bd99cfb57d9749c` |
| Resolved SHA | `e22c01f75a96be433ce1d3d7710c59c3fb95863e0d3689f1fc771b825796cc59` |
| Preview SHA | `fb3ac57c3604ec4fc8563476c9a8ac733385d75602078139eb3f8456096401a7` |
| Prompt SHA | `3adfc42f3c4aa2892be3de13b4bc7d72a1ab1a53165fbd7601501b3ce263a0e6` |
| POST | 2026-10-10T19:45:07Z；756131bytes；bodySHA`60f2c5eafc56678e77c8b185fa324df2c33d2fa82971a5551f8e8fd399c785c4` |
| Response | HTTP403 / `AccountOverdueError`；212bytes；responseSHA`7756484c317ee10bc504072ae30d41177ddb5ae80a27123077444368735758bf` |
| Canonical receipt | `production/state/paid-provider/submits/6f556558f90421f7e2b55ebe541c991751a0da4b0b19696734abfe53022a11f0.json` |
| Receipt file SHA | `37817c196e6316758cc7a892eb69fe4e45b285df5cf15cf147168547e42e32b6` |
| Reopen | Manifest33；attempt failed；paid phase known_no_effect；next action stop；external_effect_id null |
| Budget | active revision7，new reservation released / actual0；old reservation仍reserved / actual unknown |

本地结果保存为`repair-prompt-v3/submit-error.json`、`canonical-submit-failure-state.json`与
`canonical-paid-failure-summary.json`；读取正常owner失败状态没有再次POST或重铸permit。
辅助readonly metadata读取曾用错dataclass/Pydantic字段，修正后重开，未触发Production写入或Provider请求。
新片未生成，故新媒体Gate、POV效果、完整运动/声音、adoption及final render均NOT_EVALUATED，
原片human声音/动作反馈不转移为新片PASS。用户已收到账号侧恢复额度请求；余额和原因细项未取证。

用户随后表示仍有余额并确认查看的是火山方舟/火山引擎。Parent只读核对公开
[官方错误码](https://docs.volcengine.com/docs/ark/error-codes?lang=zh)：文档分别说明欠费及计费项未开通，
不能只凭error推定用户账户实际金额。当前adapter固定origin为`https://ark.cn-beijing.volces.com`；
当前已登录方舟首页经正常余额显示按钮实际显示negative余额，观测保存在
`repair-prompt-v3/account-console-observation.json`。这是当前console页面观察，与error相符；
尚未独立验证该登录账号与API key所属账号一致，未读取/reveal任何新credential、明细账单或实际生成费用，
未充值、开通服务或再提交视频。上句“余额未取证”只描述该只读核对前的历史停点。

### Resource Package Correction And Selected Model Constraint

用户提供调用汇总截图并说明购买了500万tokens的Seedance2.5资源包。2026-10-11约04:03 +08:00，
当前已登录资源包管理页只读核对该包为`生效中`，total `5000千tokens`，remaining
`3845.5999998773千tokens`（约384.56万tokens），region华北2（北京），有效期至2027-01-06。
选择字段的观测保存在`repair-prompt-v3/resource-package-observation.json`，不保存账号姓名或实例标识。
用量汇总、资源包余量与cash余额是不同观察，不能互相替代，也不据此推算账单。

[官方资源包规则](https://docs.volcengine.com/docs/ark/seedance-2-0-model-resource-pack-rules?lang=zh)
经实际页面核对：开通资格与抵扣分开，每次调用按具体模型结算，资源包只抵扣对应模型。
本任务三次实际POST分别是2.0、2.0 Fast、2.0 Fast，均不是2.5；这份2.5包不覆盖当前Fast请求。
因此先前将negative现金余额当作整个Seedance路线阻断的解释被限缩，保留原403/余额观测作为历史。
未遍历全部资源包页面，不能声称账户不存在任何2.0包；API key与console账号一致性仍NOT_EVALUATED。

Parent曾提出按已购资源包准备2.5，尚未提交或改变Production。用户最新明确拒绝2.5；当前选择保持
`doubao-seedance-2-0-fast-260128` / 480p。不为使用这份资源包切换模型，不查询价格、不充值或购买其他包，
没有新Video Provider POST、permit或预算扩展。2.0 Fast的known-no-effect失败及耗尽有限单元保持；
必须先解除所选API账户/模型的计费拒绝，再核对canonical恢复条件和新有限单元，不能盲目重试。

用户禁止2.5之前启动的受管只读model-reroute mapping已由Parent停止。invocation
`a9563bbe-9c45-4398-b614-653ac90ca074`的canonical receipt保留6次wire request、16次Read、
process `cancelled`及classification `OUTCOME_UNKNOWN`，没有terminal report，不采用partial输出或重试。
这是独立Kimi调查的结果状态，不改写上述Seedance physical POST的`KNOWN_NO_EFFECT`，
不构成恢复实现、required review、新model选择或媒体验收；封存inputs和历史消费保持。

### Published Repair Verification

MCP调用修复commit`40a26924a084e9b02390f0f255a2bbfba0117bef`已push并核对remote main SHA；
exact staged receipt`.agent/harness/runs/reusable-canvas-production-20261011-mecha/receipt.json`的11checks全部PASS。
共享repair commit`e11744514c0a47f6ec76c880722cad5be227a3e2`同样已push并核对remote SHA；
`.agent/harness/runs/reusable-canvas-repair-20261011/receipt.json`的9checks全部PASS，含114 Canvas、
275 Harness、44 invariant及2 runtime-boundary tests。staged tree`ebb3c94744e37cc4c63a9950ad8692b5b513a82b`，
receipt SHA`e91d5d34a6ce13544ad90144c5650b49852946c867310afdfa397db28202ad55`，commit前fresh验证通过。
两份staged receipt只证明各自snapshot；不把commit后的staged freshness当当前证明。

Implementation Risk Gate在上述native verification后裁决`KIMI_REVIEW_NOT_REQUIRED`，exact decision
保存在`repair-implementation-review-risk.json`。没有新增credential/Provider/permit/schema/state writer；
canonical current-attempt选择风险经closed lineage、same-task/history、fork/unknown拒绝、预算耗尽、
mixed closure、完整successor Gate/采用及replay覆盖，Parent未发现需adversarial review的实质剩余gap。
只读concept报告不被计为implementation review，也没有叠加额外reviewer。

## Shared MCP Invocation Repair

`ProjectAnalysisSession.__init__`原先把配置Python symlink`resolve(strict=True)`后作为executable调用。
配置venv能import`mcp`，真实resolved base Python不能；normal review因SDK缺失在MCP调用前失败。
修复先strict检查目标存在，再调用原配置路径的absolute形式；不安装SDK、不选新解释器、不fallback。
一个真实回归先红后绿，另一个保持missing executable拒绝；`test_generation_feedback_review.py`31项通过。
随后同bytes的真实MCP→evaluator→feedback与blocked validation/replay取证成功。

旧v2 source/authoring冻结21paths只有已发布spec/plan状态文字不同；本次新增共享QA调用修复在其外，
不能将旧工程receipt外推到这次代码或补签AC-2/AC-7。本次独立exact snapshot按policy验证。
Implementation Risk Gate：`KIMI_REVIEW_NOT_REQUIRED`，改变只保留已选executable路径；无新增secret/network/
Production authority或state writer，strict missing检查、public invocation seam回归与实际MCP都已验证。
concept审查不冒充code review，补充protocol失败也不构成已通过的required review。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mecha-provider-result | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/canvas-mecha-seedance480-20261011-001/fetch-result.json |
| mecha-pov-gate | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | ANALYZER | FAIL | POV_NOT_SATISFIED_WITH_EVIDENCE_GAPS | SAME_EVIDENCE_NEW_PROOF_LAYER | mecha-provider-result | runs/canvas-mecha-seedance480-20261011-001/generation-evaluation-source.json |
| mecha-human-audio | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | HUMAN_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | mecha-provider-result | runs/canvas-mecha-seedance480-20261011-001/human-audio-confirmation.json |
| mecha-human-motion | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | HUMAN_VIDEO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | mecha-provider-result | runs/canvas-mecha-seedance480-20261011-001/human-motion-confirmation.json |
| mecha-repair-account-rejection | provider-request:e22c01f75a96be433ce1d3d7710c59c3fb95863e0d3689f1fc771b825796cc59 | canvas-mecha-ant-unit-20261011 | canvas-b632cd4c587aa7a8df7640c34bd99cfb57d9749c | N/A | NO_ARTIFACT:ACCOUNT_OVERDUE | PROVIDER_RECEIPT | FAIL | ACCOUNT_OVERDUE | NEW_ATTEMPT | NONE | runs/canvas-mecha-seedance480-20261011-001/production/state/paid-provider/submits/6f556558f90421f7e2b55ebe541c991751a0da4b0b19696734abfe53022a11f0.json |

同一attempt只有一个独立单元；31帧、四个失败requirement、两次MCP及两层proof不增加独立实验数。

## Remaining Work And Record Outcome

原片声音/完整运动已获上述human确认；旧formal analyzer gaps保持，已通过明确补证耗尽closure封存。
保留已知POV失败，缺连续运动证据不靠重复生成补齐。新的视点表达单元已准备并被账号错误拒绝，
不是POV实测失败或成功。用户禁止2.5，当前Fast2.0计费拒绝解除后先核对closed known-no-effect状态和全部3次物理POST，
按原recovery/planning、exact preview/actual clock及下一有限单元执行；当前已消费permit/封套不能复用，
不另开Production根清零、不改成第三人称求PASS，也不自动重试。
最终还需真正holdout短剧情单元、canonical原声composition/HyperFrames和用户完整听看认可。
当前媒体可用于失败诊断，不能以candidate/preview名称结束作品目标或签AC-7。

使用`record-ai-video-session`记录真实稳定阻断和共享修复，并对工程/Beauty记录作直接supersession。
`distill-ai-video-learning`评估`no_candidate`：一次机甲POV失败与Beauty输入拒绝涉及不同model、素材及
观察层，未隔离共同变量；新修复没有媒体outcome，账号拒绝不能成为POV对照臂；SDK调用回归没有第二独立实验
或controlled multi-arm，不制造通用学习规则。learning outcome仍`no_candidate`。
资源包观察与官方抵扣规则补正不是第二次模型实测或受控POV对照，不改变该learning outcome。
record不改Skill/Policy/Gate，不重建RAG，也不为记录增加Provider/media或额外测试。
实现verification分别绑定上文MCP与repair receipts；收尾文档exact snapshot证据入口为
`.agent/harness/runs/reusable-canvas-account-blocker-20261011/receipt.json`，状态与scope以实际receipt核验为准。
资源包解释与用户禁止2.5的本次文档snapshot另验
`.agent/harness/runs/reusable-canvas-no-seedance25-20261011-v2/receipt.json`，不外推旧receipt到新bytes。
publication以实际main SHA为准；原11-check/1475-test receipt只保留原snapshot证明范围。
