# COCO / Nosha Causal Shot Repair

## Goal And Authority

继续用户已授权的 Vidu Q3 复现：只用三张已批准图片和原画布一次对白 WAV，正常速度呈现原剧情、角色、道具和可读因果链。用户允许分 Shot，无固定总长。当前任务授权包含必要的 task-level QA/coverage revision 和有限预算；不授权新增图片、其他 Provider、publish/release。

## Current Evidence

标准 `load_production_project` 重开 `runs/coco-nosha-vidu-voice-recovery-20260930-001/production-v2/project.yaml`：Manifest 104，QA `1177e77cb005559b3e657504e754a02d9eaaabb58c46258124f86f037d2b13e0`，两次 Vidu physical submit 均 fetched 后 quality rejected，2/4 consumed。原 H3 八次另行保留。两次只改 seed/profile 时间，不足以证明拆 Shot 无效或必须补四图。

## Requirement Decisions

| Selected requirement | Source / necessity | Prospective treatment |
| --- | --- | --- |
| `shot-output` | 正常速度来自 `creative-input.txt`；8/8/7秒、192帧是 Director v1 配置。两片8.042秒/193帧不证明动作速度异常。 | 保留1280×720/24fps和可解码媒体；改用现有 `VideoFlexibleOutputRequirement.nominal_seconds` 的唯一 timing matcher，允许一个终点帧。不得变速、冻结或删关键动作。 |
| `shot-identity` | 原文明确 A四眼/扇耳/六吸盘足/长尾，B湿囊/三鳍/无虫形，C六瓣吸盘体，D三眼柄/五足/三角软壳；COCO/Nosha和手机等身份不变。 | 按当前 Shot 的已封存出场范围检查，身份实错与遮挡缺证分开。背景未入镜不自动证明变形；不可把所有角色都必须在每镜清楚入镜作为额外门槛。 |
| `shot-action` | 原文 B侧撞A→坠落/翻滚/逃跑、A惊C→C扑附Nosha→失衡、Nosha→车→篮→果→D。 | 保留明确动作和关键触发/顺序/结果；正常速度观众能辨认谁触发什么。每个微接触逐帧无遮挡不是独立要求；明确要求的接触仍不能删。Nosha头部不在画面是看屏 `NOT_EVALUATED`，不能推断没有看屏。 |
| `shot-continuity` | 原文角色职责和唯一道具、同一空间/方向、事件连续；旧 `A尚未碰C` 是旧Shot2的接点。 | 新 coverage 重新封存接点，允许匹配切镜，承接已接受前镜真实末状态。不能省去刺激C、容器、推车和果篮的关键原因；不从未接受失败片造accepted terminal。 |
| `shot-muted-source` | 用户原声线/唯一一次对白；既有 SourceAudioPolicy 分配原WAV到P4。 | raw request仍 `native_audio=false`；raw音轨存在/缺失按真实技术证据记录。原声、单次对白、同步和最终混音只由P4/成片验证，不提前声称PASS。 |

原片两次 FAIL/rejection、旧 rubric、消费和原QA bytes不可改。新版本不是历史片重新验收，也不把模型随机失败归结为图片数量。

## Coverage Contract

进一步拆原 Shot1，保留同一 project/task/history，4个有序单元：

1. `fall-and-line` revision2，5 nominal秒：仅A/B平台侧撞→A吸盘脱离坠落→侧落/翻滚两圈→接触木碗后碗滚动→翻正开始逃跑；B沿平台滑出。D已藏在同一低架/木箱间，前段可见锚点明确分配至下一单元；COCO/Nosha可在背景，尚无对白。身份和明确动作不删。
2. `floor-and-line`，7 nominal秒：承接A落地逃跑，沿同一方向穿行；D在同一低架/木箱间必须短暂露出转动的三眼柄，保留原文翻滚逃跑后的前段可见锚点；COCO持唯一手机移动、避让A、抵达Nosha举屏；Nosha头部可见并看屏，C仍在脚边，D藏处维持。原5秒WAV只覆盖此单元一次，末镜引用此已接受前段锚点。
3. `contact-and-fruit`，8 nominal秒：保持原 A尾触容器→刺激C→C立即扑附头→Nosha即刻失衡→撞推车→车撞果篮→六瓣果滚出，不能定住展示。
4. `d-eats-fruit`，7 nominal秒：同果滚入同货架，D观察/移动/逐瓣咬食/咀嚼/吞咽，末状态仍有动作。

上述时长是生成与剪辑安排，不是用户固定成片长度。镜头1将碰撞、坠落从人物举屏中隔离，测试动作负载这一有依据的主要变量；三图、Provider/model、静音路线和原声轨保持。seed实际是否受控、profile时间续期等附带变化必须如实记录，不能宣称严格单变量质量证明。图片中的其他宠物形态不覆盖原文A/B/C/D身份。

## Owners And Compatibility

原 authoring/QA types封存 coverage、Shot、FinalOutput goal version2、QA policy version2；`ProductionStateCommitter.commit` 原子发布 project/graph，`activate_qa_policy` 发布QA。Registry图片/WAV bytes不变。`VideoPlanner`→feedback→Router→compiler→`VideoGenerationService`维持唯一执行链。用现有dependency transition helper重建所选target，不裸写Manifest或造state。前序末状态只作analysis evidence，不新增生成图像输入。

当前 pure compile 暴露共享 matcher 未接通 `content_driven` 与已有 `nominal_seconds` output，导致 compatible route 为 false。仅补此映射；不改变 schema、Provider capability、measurement tolerance、`fixed` 或 `voice_driven` 的限制。回归测试验证 content-driven 可匹配、错误秒数不可匹配、固定/voice-driven不可匹配，以及终点帧上限。此 necessary shared seam 属于本任务授权，纳入同一T3 review snapshot。

## Budget And Stop Conditions

先使用剩余2个slot，第一新单元最多1个physical submit；停止同prompt改seed的无据循环。若新片known FAIL，先评估真实修复变量。若镜头1/2通过且目标还需后续镜头，保留真实计数并经现有committer逐次有据扩展有限quota和operator upper bound；不得重置history/permit或用改名逃避上限。profile/preview/authorization/intent/one-use permit全部重新封存。Unknown outcome或未授权输入/Provider/egress停止。

每镜exact MP4必须显式调用project-local `video-analysis`并按selected required IDs判PASS/FAIL/NOT_EVALUATED；下一镜仅在全部required PASS后submit。证据不足先补证；required真实失败不降级。成片只走CompositionSpec/ResolvedTimeline/P4/HyperFrames，原WAV一次，完整观看/聆听未取得就保持NOT_EVALUATED。

本 development bundle 保持原有顶层 Shot，不声称其具有 Production component lineage 的自动 predecessor enforcement。task-local `task_gate.py` 在 prepare/execute 前只消费 committer 重开的 current-QA exact predecessor diagnosis 和 unchanged fetched bytes；不存在第二份持久PASS truth。逐镜脚本必须调用同一 consumer。反馈脚本支持 required 全PASS的持久反馈与 known QUALITY_FAILURE rejection 两条分支，activation仍为独立canonical action。0.5秒抽帧经既有任务专用MCP shim提供，验证实测interval/timestamps，不仅信Gate自填数量。

## Verification And Review

运行Director v4和creative-goal-binding验证、requirement semantic admission、canonical candidate load、exact native编译/preview、历史count/asset/rejection保持检查，以及相关已有timing/QA/feedback/project tests。风险T3只限本任务QA prospective contract，最终stable candidate绑定hash作双独立read-only review。Parent裁决，不以测试或review替代媒体验收。用户禁止worktree，使用direct policy checks并明确canonical detached Harness receipt为null。

## Self-Review

Parent核对：没有删原动作/身份、没有新的输入或Provider、没有倒填旧PASS；时长改变复用现有nominal contract，证据缺失保持NE。原文一镜到底/固定时间明确被当前用户覆盖；其余显式约束仍保留。声音人类听觉与最终同步能力缺口未被工程通过掩盖。

## Bounded Repair Amendment

首个拆分5秒片 `be14259bb64444e1c90e02828018f7ea1c80bec6c60b0bef4c304ddcbc210af9` 已经真实生成、显式MCP半秒11帧及0.1秒51帧检查：B侧撞先于A坠落、A碰碗先于碗运动均有改善；4.2–5秒未建立逃跑末状态，六吸盘足及意外入镜D形态保持NE。committer在Manifest129显式abandon保留QUALITY_FAILURE/EVIDENCE_GAP，不接受或追改该片。

下一有限单元仅使用剩余第4个Vidu slot，把隔离A/B单元延长至8 nominal秒；其余三镜、三图、原对白、角色/动作/终点要求不改。主要修复变量是该单元可用时间，不是再次盲改seed。新coverage/Shot/project及其QA coverage binding前瞻封存revision3；FinalOutput goal version3仅标识这次前瞻authoring contract，要求正文与version2逐字相同，不授权删动作、降低identity、reset消费/repair预算或重验旧失败为PASS。profile仅有限纯时间续期，金额/Provider/model/egress不扩张；seed等附带不受控差异如实保留。全部required通过仍是推进条件，失败后先取证，不能把这次样本当成证明补四图必要。

标准 disposable compile暴露旧QA的abandonment回执被history producer当作新QA执行例外，binding正确阻断。修复只在`GenerationFeedbackOrchestrator.for_project`按current selected QA筛选`abandoned_result`；旧experience、latest evidence、baseline与receipt完整保留，binding的QA equality guard不变。真实canonical fixture覆盖同QA继续修复与新QA不继承旧权限两支；新contract仍需通过原Router/QA/planning/paid guards，切换QA本身不授权重试或重置消费。

## Platform-Only Repair Amendment

第四次exact8秒MP4 `5f139f918f8802abe95321ff69731dae8c8298e2d32bc09d467a89749aa39e45` 已取回并经显式MCP17个半秒帧、81个0.1秒帧检查。A末尾开始左向逃跑，但B随A坠落，地面两次翻滚未成立；identity遮挡/足部结构缺证仍NE，不推断四足或必须新增四图。technical-first后analyzer的durable diagnosis保留QUALITY_FAILURE/EVIDENCE_GAP，committer终结候选；原FAIL/QA/receipt与4次physical消费均保留。

下一最小实验将第一单元进一步拆为平台5秒与地面5秒，随后原7/8/7秒三镜保持。平台只到B侧碰→A离开平台、B继续沿平台滑出；地面承接已接受末状态，侧落→翻滚两圈期间身体碰碗才使碗滚动→第二圈末顺势翻正并立即逃跑。不得新增“第二圈完后才碰碗”的顺序条件，不用失败帧作新的reference，不省略原对白或后段因果。平台镜保持此前有效5秒长度，主要诊断变量为动作范围/构图；去除第一镜中的地面和人物任务，不是删全片动作。模型随机性和新profile仍是混杂因素，不宣称严格单变量质量证明。

通过原authoring/QA owner形成revision4及五镜coverage；所有generation_requirements和FinalOutput正文逐字保留，goal version4仅标识前瞻contract。现有三图/WAV/Provider/egress不改。只封存一次新的platform submit：同TASK ceiling4→5、内部project operator上限12M→15M microunits、per-call3M不变；原4个reservation/permit/消费与预算lineage不可清除。原committer执行金额扩容与exact prior/target binding的quota entry，未通过标准loading/preview/submit guard不得提交。平台FAIL/NE阻断地面，known结果先补证、核对下一修复依据；unknown立即停止。之后镜头的有限预算仍须另行有据封存，不在本单元预发多次permit。

## Side-Route Repair Amendment

第五次platform-only5秒片 `b7830b76679dd7cf19c3941af868980966c28680453680336cac96e9a24bbd07` 的显式MCP11个半秒帧和51个0.1秒帧已建立A左前离台、B留在平台，仍未建立B侧腹冲量和随后沿平台出画；A正面仅呈现一对眼睛、足部爪趾样，原四眼与六吸盘足身份尚未建立，不误证全身只有四足。技术输出与静音PASS、动作/连续性FAIL、身份NE分别保留；不能把地面动作归到当前平台失败，也不能把样本当作必须补四图的证明。

下一单次实验只改变B相对A的开场位置及路线这一空间编排变量：B在A右侧近处，先向内侧腹碰A，再沿平台后侧滑出，避免从后追尾并停在前角。A仍活动并观察镜头，不自行走下平台；5秒、同三图、原A/B形态文本、正常速度和既有QA4/五镜coverage不变。空间路线修复不自动解决身份证据缺口，全部required仍须PASS。同TASK仅新增一次slot5→6，内部operator ceiling15M→18M、per-call3M不变；保留前五个reservation及所有历史。重新封存profile时间窗、exact preview/authorization、新REQUEST与one-use permit，由原committer执行预算和quota扩展。模型随机性仍是混杂因素，不宣称严格因果实验。若该次FAIL/NE，先补证和核对是否仍有不同、可归因的修复；不得自动重发同prompt或以预算耗尽本身要求用户回复继续。

## Authored Intervention Input Amendment

第六次disposable编译返回`REASSESS_FEASIBILITY`，未发生Provider效果：共同feedback仅自动生成resample，既有resample上限正确阻断；空间路线变化没有作为typed干预进入Router。Router原有`DecisionInputs.interventions`已经支持显式修复与完整history/actual-delta校验。

为接通该既有能力，`GenerationFeedbackOrchestrator.prepare`与`start`增加可选keyword-only `interventions: tuple[Intervention, ...] = ()`，在重新打开的当前context/history和自动干预之外加入caller封存提案。Router仍独占是否准入、候选选择、baseline比较与语义实验去重；不修改decision policy、resample limit、QA、失败历史、prediction或permit规则。显式提案不是授权、事实或已证明有效的修复。默认空值保留原行为。非法/陈旧证据、重复实验、known violations和未声明实际编译变化仍fail closed；`start`只将通过同一binding的新REQUEST交给committer，不submit或activate。

Parent self-review：这是共同producer的缺失输入接线，不另造Resolver/编译执行路径。初始提案误把当前Q3 seed视为uncontrolled，真实compiler正确拒绝未声明的seed变化；pure diagnostic测得实际delta为`provider_profile`、`prompt_text`、`seed`，seed为1496616717→1496616718。新提案须声明三项、保留全部其他compiled constants，不能声称严格单变量实验。semantic target hash只绑定空间prompt，附带seed推进/profile时间不作为新空间实验身份；当前profile仍由原binding/typed reaffirmation精确核验。不能借文字换名重发同一实验。只针对动作/连续性失败提出假设，身份NE仍阻断下一Shot。纳入本任务stable exact snapshot验证和适用独立审查，完成后继续原真实实验。

## Phase Checkpoint Amendment

两次未提交的disposable校验进程结束后没有最终收据；保留副本及中断记录，原因保持`NOT_EVALUATED`。真实ROOT仍为Manifest190、五次known failed/fetched，不存在第六次paid intent或physical marker。到期的05/06仅为未执行准备，不复用其preview或permit。

同一第六次空间修复在07窗口重新封存，operator per-call3M及五次真实消费保持不变，有限上限仍仅5→6、15M→18M。task-local wrapper分开`start`、`quota`、`submit`、`poll`、`fetch`；每阶段标准重开Project并调用原canonical service/committer。`submit_once`内部paid intent、permit和POST保持一个不可重启单元。只允许无paid/local副作用的exact `RUNNING/REQUEST`继续准备；submit intent、unknown、terminal、identity drift均停止。已接受提交只能同task GET/fetch，不能再POST或通过窗口续期重发。Parent self-review确认该调整只改变任务编排，不修改共享恢复契约、质量标准或预算owner。

## Known-Unsubmitted Recovery Amendment

07 exact snapshot的独立审查定位REQUEST窗口到期后无canonical关闭路径、graph commit后中断不可重入和analyzer可先封错误技术Gate三个问题。真实ROOT仍Manifest190、五次physical FAIL；07没有真实第六次effect。此处前瞻扩展恢复契约，不追改旧记录。

`ProductionStateCommitter.close_unsubmitted_video_generation`仅在standard reopen、exact REQUEST、无paid/local intent/receipt/status/fetch、无该attempt reservation、存在exact canonical `not_submitted` experience时将RUNNING关闭为FAILED/`video_generation_not_submitted`。保留request/binding/experience、graph及budget，existing error metadata记录typed actor/reason。CAS保护首次关闭，exact replay无写入；unknown/intent/错误证据拒绝。新generation identity的同TASK successor保留全部history和实际消费；已应用quota仅经这个verified closed ancestor继承原ceiling，不追加额度、不重放旧授权或permit。普通RUNNING/REQUEST、INTERRUPTED或unknown不能继承。

task-local新packet在graph mutation前检查fresh profile；重入仅复用canonical已成功提交且desired graph/states相等的checkpoint。analyzer必须先核对当前Gate/request/media/QA的durable technical source，缺失或错误时在seal/MCP前拒绝。Parent self-review：仅补未发生外部效果的生命周期收口，不将paid未知结果改成未提交；schema既有字段保持，新的specific error code与公开method前瞻添加。纳入T3 direct policy和同一稳定snapshot双独立review；通过后继续第六次真实实验及成片目标。

## Unapplied Quota Proposal Amendment

第二轮review的SIDEROUTE-04由standard-loader fixture复现：`start`后、`quota`前关闭的verified zero-effect REQUEST仅封存了较高ceiling提案，尚未应用extension。canonical quota owner计算历史已生效上限时，仅对此类已验证关闭且未获任何retained quota的高上限提案排除；保留其完整attempt/binding/experience与真实消费。已应用extension、普通FAILED、RUNNING、UNKNOWN、INTERRUPTED不能借此排除。后继仍须针对最新Manifest/base ledger及最后真实prior封存原5→6的exact extension；已应用额度仅只读继承。task wrapper每次quota阶段调用同一canonical owner，并按实际ledger判断应用或继承，不能按“存在关闭检查点”猜测额度已生效。Parent self-review确认不扩大ceiling或清零消费，采用pre-quota/post-quota两种关闭边界的完整submit guard测试及最终第三轮双独立review。

## Unapplied Prior Rejection Amendment

第三轮SIDEROUTE-05由canonical fixture实际复现：把未应用cap-2的verified closed请求用作prior，原实现会错误应用2→3，即实际cap-1跳到cap-3。排除未应用closed提案必须独立于entry自行选定的prior ceiling；所有verified closed且没有retained quota的提案均不作为已生效上限，ledger-applied ceiling及实际非关闭history继续保留。新负向测试要求扩展拒绝且全部字节无写入，既有合法扩展/完整submit guard保持。Parent确认这是有限授权计数的真实缺陷，保持前三轮与原预算，将同一review单元有限扩展一次（总上限4轮），只复审最终修复和同一unused第六次packet，非新任务/新实验或review计数重置。

## Supported Inertia Repair Amendment

第六次真实 MP4 `96e611dec19e82717ddd0cdb8cd3dcbbd4825aa7bf51e9d329c20f4814505da6` 经显式 project-local MCP 全段11个半秒帧、51个0.1秒帧补证后，侧接触先于A离台已有可读证据；A四琥珀眼、两扇膜及吸盘状足明显改善，不能沿用第五次的两眼结论。B却在4.6–4.9秒跟A从同一前角跌落，supported exit FAIL；精确六足总数、B腹褶持续收缩和手机保留仍未关闭。原QA4与本次FAIL/NE均保留，不接受或剪取失败片充当前序。

Parent发现上一修复把B右侧向内的滑行改接BACK-RIGHT退出，要求它改变原滑行方向；这只是导演候选，原文要求的是保持惯性沿平台后侧出画。下一有界假设改为宽平台上的右→左后侧通路，A靠前缘，B通路位于A接触侧但远离前缘，B侧腹接触使A向左前方失去支撑，B仍沿原左向惯性滑行并在后侧有连续木面支撑的位置退出画框。保留原文沿平台边缘的左向横移，只在本镜看平台、不追至地面；人物及同一手机留在画外原空间，下一镜仍须匹配。保留原A/B形态、正常速度、侧接触和各自明确结局，不要求每个微接触逐帧完全展示，也不将画外人物改判为通过。

这是known结果之后新的第七次空间修复单元，最多新增1 POST，同TASK真实消费6→7、operator ceiling18M→21M、per-call3M不变；不是第六次review单元的重命名或计数重置。旧四轮审查和六次物理消费完整保留。seed先按canonical编译实测核对，若现有编译器推进seed则如实声明actual delta，不为保持seed绕过Router或新建控制路径；不宣称严格单变量质量归因。只使用现有三图和原WAV，不新增参考帧/裁图或其他Provider。profile纯时间窗遵循当前ViduProfileReaffirmation至多60分钟；第六次已有同样窗口内完整guard/POST的真实证据，不为延长等待修改共享契约。只在本次quality closure与任务脚本准备完成后续封fresh窗口；过期且零副作用才走既有known-unsubmitted恢复，unknown不得续封重提。Operator Ceiling Renewal、exact preview/authorization、Budget Guard/egress、新identity/intent/one-use均保留。

Self-review：支持平台出口与侧撞均是原文动作，不是额外像素级门槛；左后侧通路修正了候选的惯性冲突，未删B动作或改变宠物职责。只读authoring复核的AUTHOR-01指出固定镜头会取消原文明确的左横移，Parent采纳并撤回固定镜头候选；AUTHOR-02指出若改Director camera treatment必须另封coverage/QA，当前方案保留原tracking及Shot4/QA4，通过typed GenerationIntent和Intervention表达同一已批准目标内的路线细化，不制造无必要的QA revision。宽后侧木面仍是待真实验证的布局假设。新的有限单元先纯canonical验证、适用独立review，再真实取证。若FAIL/NE，先同bytes补证再判断是否有可归因修复；无依据时停止该单元，不同prompt盲改seed、不默认必须补四图，不把测试/commit当成复现完成。

## Cold History Window Amendment

第七次准备的profile11仍未产生REAL attempt或POST。六次质量关闭后的同一canonical副本，money阶段实际耗时756.147秒；随后仍需compile、paid、preflight、start、quota、guard、独立审查及真实执行。每步都重验增长的历史evidence，不能省略标准loader、Budget Guard或execution binding来挤进60分钟。Parent据本次实际耗时修订上一60分钟假设：只将Vidu内部operator ceiling的纯时间reaffirmation最大窗口改为3小时，任务使用最短可行的有限窗口。该T3变更属于当前默认授权的时间窗口修复，先做source/test/canonical docs、direct policy verification和同一exact target双独立review，再真实取证。

唯一类型owner仍为 `vidu_profile.py::ViduProfileReaffirmation`；不增加schema字段、配置入口或Provider路径。旧/新profile所有非时间字段必须相同，决定时间和到期时间均须严格向后，窗口大于3小时仍拒绝；Provider preview/submit继续按实际clock拒绝过期或尚未生效的profile。旧proof和profile bytes/hash、原三图、QA4、seed计数、总预算、sameTASK quota及one-use/unknown-outcome规则均保留。这个内部上限窗口不产生官方市场报价或余额事实，不适用于其他Provider的真实pricing snapshot。

新的time02准备只替代未使用的profile11时钟，仍是同一第七次惯性实验、最多1个新POST、真实消费6和6→7/18M→21M边界；旧copy、时间证据及全部审查/消费保留。source/脚本准备完后才以真实UTC决定时间封fresh profile12，重新绑定preview/intent/permit和canonical副本验证。已知零效果的旧准备可显式关闭或保留为未提交副本证据，未知结果禁止续封重提。Self-review：扩大有限operator确认窗口解决已观察的历史校验运行成本，不放松媒体criteria、费用数值、调用次数或runtime expiry，不引入cache或绕过canonical校验；没有新增外部授权。

## Separate Verification And Execution Windows

旧profile11副本preflight实际910.171秒后因过期明确停止，零POST；money/compile/paid此前分别756.147/1562.381/577.115秒。把完整copy、review和REAL preparation重复串入同一窗口，会让已验证的准备再次被时钟耗尽。Parent在同任务默认授权内将纯验证与真实执行分为两个有限时间单元，不再要求同一profile覆盖两遍cold历史校验。

profile12副本须先完成全部八阶段，保留exact bytes、M202及零POST证据。随后仅在known zero-effect条件下，为同一未提交第七次实验创建fresh profile13/time03；实际baseline仍是第六次profile10，真实消费仍6，最大新POST仍1，三小时上限不再扩大。time03脚本仅变更preparation identity、profile引用和路径；其非时间profile、原三图、QA4/coverage、typed intent、预算/计数保护和物理payload必须逐项比较。通过canonical REAL money/graph/compiler准备fresh request后封fresh preview/authorization，禁止复用12的preview/permit或将12的copy称为13的同bytesreceipt。copy12验证只证明共同逻辑；新的exact source+time03 packet须双独立review，真实start/submit仍按当前项目和实际clock重新执行所有guard、durable intent与one-use。

Self-review：review前仅允许已授权committer的有限budget/graph准备，不启动付费intent或POST；final review仍在真实start/submit前。non-time或native payload差异超出上述声明、unknown effect、required review或clock未通过时停止，不能用参数等价掩盖新的语义变化。全部旧准备、轮次与消费保留，最终媒体Gate和实际出片目标不变。

## Measured Execution Window Amendment

2026-10-01 18:13 UTC新计时取代上文“上限不再扩大”的三小时假设。copy12 money/compile/paid/start/quota已分别耗时905.160/1740.261/526.121/1192.593/2545.227秒；guard从16:56:51开始，17:31:38才完成main前置流程，截至18:13仍在canonical guard。仅上述真实路径共同阶段的已测开销已超过180分钟，尚未计入独立review、service重开和durable paid intent写入。当前REAL仍M202、profile13未封存、无第七次POST。零POST等待器的17:56:58到期和额外30分钟等待均保留；Parent停止自动REAL准备，先修复有限窗口。

唯一source变化仍在 `ViduProfileReaffirmation._pure_dated_renewal`，最大内部operator窗口3→6小时。选择六小时为该次完整cold验证/审查/提交保留有限余量，不声称某函数是CPU热点、不引入cache或省略任何历史/当前性检查。所有非时间字段相同、strict later dates、actual-clock preview/submit、费用数值、per-call3M、sameTASK6→7、最大新1 POST、原三图/WAV/QA4及unknown/one-use保护不变；大于六小时仍拒绝。这不适用于官方市场报价或其他Provider。

保留source5ae8b2f三小时下已执行的copy12 receipts，明确它们是旧source、旧时间值的零效果共同逻辑证据，不能称新source/六小时profile13的同bytesreceipt。新source的六小时准入/超界/preview clock、feedback/history与production proof通过可执行验证；fresh REAL compiler/preview/authorization及exact parameter comparison再证明新dated参数实际接通。共同逻辑与native payload/intent/QA不变，最终同一source+fresh time03 target双独立审查裁决此组合证据是否充足，存在缺口则补证后再submit，不追改copy或旧source证据。

Self-review：本任务默认授权允许必要的有限时间窗修复；本次是实际阶段成本驱动的修订，非价格、调用次数、媒体criteria或外部范围变化。原三小时和等待器脚本保持历史bytes，使用新的six-hour helper封存真实UTC窗口；review前仍只有canonical snapshot/money/graph/compiler准备，没有paid intent/permit/POST。保留旧profile、所有消费/准备/审查历史。源码/任务参数的direct验证不冒充detached Harness receipt或媒体接受，工程完成后继续同一真实复现。
