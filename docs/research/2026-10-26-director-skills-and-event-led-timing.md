# Director Skills And Event-Led Timing Assessment

Date: 2026-10-26

## Decision

三库各有可用的导演工艺，但没有可比的 exact 实片证据证明其中任何一库整体优于 AI-VIDEO。
不安装三套 Skill、不引入其生产工具或状态模型。本次仅在既有 `open-video` 增补一份可按需读取的
[Event-Led Timing](../../.agents/skills/open-video/references/event-led-timing.md)：
先决定触发、行动、对白、反应、注意交接与切镜理由，再选择当前模型可执行的镜长；内部节奏默认
用事件关系表达，只有有根据的同步点或固定要求才用精确时间。它是作者方法改进，尚无新的实片
证明自然度或成片效果提高。

DirectorSKILL 与 drama-skills 的来源版本与[10月24日审计](2026-10-24-five-drama-skills-source-audit.md)
相同；其走位/coverage 和剧情方法已分别进入 `open-video`、`drama-authoring`，这部分不重复建设。
无时码顺序对白也已由另一任务写入当前工作树；本次没有实现、提交或宣称拥有那批 Runtime 改动。

## Sources, Reading And Licenses

冻结公开 Git 快照后阅读实际文件，未运行安装器或上游生成服务。初始项目 HEAD 为
`1c53e615815c80e978c25c08217937d95bd946f4`，共享工作区同时存在他人的大量 dirty/untracked 工作。
外部源码调查由一名原生只读 `context_search_agent` 协助，Parent 核对关键来源、当前实现、历史媒体
和最终取舍；文本 forward check 另由一名原生只读 `test_analyzer` 执行。两者都不写文件、不签媒体验收。

| Repository / pinned revision | Implementation and dependencies | License / reuse decision |
| --- | --- | --- |
| [skill-movie · `69f6db670ecf305e84f199e418bddbf2c1d988fe`](https://github.com/snowfrost/skill-movie/tree/69f6db670ecf305e84f199e418bddbf2c1d988fe) | 78个 `SKILL.md` 的资料集合；导演/表演/动作/镜头/模型表达分散于多个 Skill，另有 schemas、Python 检查器及安装脚本。属于知识工作流与工具合集，不是一个已接入的自动导演器。 | 根目录无统一 LICENSE；[`seedance-20/LICENSE`](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/seedance-20/LICENSE) 和 [`longform-skill-distiller/LICENSE`](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/longform-skill-distiller/LICENSE) 分别为 MIT，仅覆盖对应授权范围。不复制未获明确许可的主体文本，不安装或 vendor 任何该仓文件；MIT 子包亦因重复职责而不引入。 |
| [DirectorSKILL · `c65ae0d14457053efb1e354c7e7f7e120d97fad1`](https://github.com/wuwangzhang1216/DirectorSKILL/tree/c65ae0d14457053efb1e354c7e7f7e120d97fad1) | 单个导演 Skill、references、模板及 evals；无生成执行器或产品运行时依赖。CI 的 Python/YAML/Markdown/link 检查是开发依赖，evals 是文本行为题库。 | [MIT](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/LICENSE)，copyright wangzhang-wu；本地改写保留来源及既有[许可副本](../../.agents/skills/open-video/licenses/DirectorSKILL-MIT.txt)。 |
| [drama-skills · `fdb7b7c58017e3eae64eca382c2a85ede368dab0`](https://github.com/zenstory-ai/drama-skills/tree/fdb7b7c58017e3eae64eca382c2a85ede368dab0) | 11个日常 Skill及1个维护 Skill；有真实 Python/JS 工具、项目/资产/分镜/生产状态、模型适配与 Remotion 编辑路径。时长估算和时序算术工具使用 Python标准库；完整工具链另需网络、凭据、ffmpeg/ffprobe、Remotion/React。 | [MIT](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/LICENSE)，copyright drama-skills contributors；局部改写保留既有[许可副本](../../.agents/skills/drama-authoring/licenses/zenstory-MIT.txt)。基准小说等另有版权/评估用途声明，不复制其内容。 |

这里的完整阅读范围是相关导演/表演/动作/连续性/模型 Prompt 的 Skill、其引用方法和直接实现依赖，
不是声称读完三个仓库全部文件。未将不相关商业/营销工具、全部导演风格变体、全部 eval 题目、
Dashboard UI 或基准小说逐字审计。没有把外部文档中的安装命令或执行要求当成本项目指令。

| Relevant slice read in full | Actual implementation / exclusion boundary |
| --- | --- |
| skill-movie | director-workflow、action-rhythm、performance-scene、cinematic-audiovisual、consistency/continuity、prompt-director/preflight、H3与Seedance相关Skill及其导演/动作/调度/声音/协议/证据references；`seedance-20` 的compiler、allocation、surface profiles、state/handoff/QC/retake/eval references。完整读 `scripts/{sequence_eval_check,continuity_chain_check,prompt_lint}.py`，其import均为stdlib；完整读5份schema（prompt-spec、generation-run、clip-contract、take-review、project-state）。未审计其余无关Skill、全部样例和迁移资料；不复制未许可部分。 |
| DirectorSKILL | `SKILL.md`、LICENSE、13份通用references（blocking/cinematic/continuity/editing/failure/genre/image/video adapters/lighting/product/production/prompt lexicon/sound）、8份核心asset templates、`evals/run.md`和3份CI workflows。57条eval只核对顶层/实例结构，未逐题执行；排除20个可选named-director profiles及其风格比较语料。 |
| drama-skills | write/storyboard/video-prompts/review/produce五个相关 `SKILL.md` 及stage contracts，表演/动作/摄影/声音/连续性/prompt grammar/generability/model profile/delivery references、Seedance2.0/2.5与H3方言、实验摘要。完整读 `duration_estimate.py`、legacy `motion_timing_check.py`及完整时序tests、`short-drama-produce/scripts/provider_adapters.py`与直接adapter contracts/provider references；另读根许可、Remotion manifest及依赖说明。未逐行审计其无关UI/生产应用、全部测试和素材。 |

## Independent Assessment

### skill-movie

最有价值的是把戏剧任务、转折、观众视点、人物权力与潜台词连到表演、镜头、光线和声音，
以及将动作组织成起势、运动、接触/回避、接收方反应、跟进/收势，反对所有阶段等长。
[导演入口](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/director-workflow-70/SKILL.md)
与[动作节奏](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/action-rhythm-editing/SKILL.md)
提供了细分词汇，但覆盖面广不等于在真实模型中执行更好。

[orchestration playbook](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/ai-video-prompt-director/references/orchestration-playbook.md)
区分有依据的精确宏观段、近似范围/比例与未计时因果顺序，这与本题相关；其主体未有统一许可，
不搬用文本、模板或规则。可合法阅读和比较不等于可以复制发布。

MIT 的 Seedance 子包有实质
[directing engine](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/seedance-20/references/directing-engine.md)、
[连续性交接](https://github.com/snowfrost/skill-movie/blob/69f6db670ecf305e84f199e418bddbf2c1d988fe/seedance-20/references/continuation-handoff.md)、
schema 与检查脚本。不过，其 `sequence-project-state`、canon、take history 会与 Project/Manifest/
Registry/receipt 重复；字段/字符串/链条检查仍不能判断自然表演。`Liu` 专属模板、强制风格名字
锚点、固定事件密度、老版本平台语法和每切长度也不是本项目通用事实。不采用第二控制面或整包安装。

另有可复核的交付缺口：该SHA的 `seedance-20/V6_SEQUENCE_PROMPT_COMPILER_MANIFEST.md`
声称序列检查47例通过，但脚本读取的 `evals/evals.json` 及所指 `tests/test_prompt_lint.py`
在快照中均不存在。Parent核对文件缺失，未执行上游脚本；不能重放该声明，也不能将其作为引入理由。

### DirectorSKILL

[blocking-and-staging](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/blocking-and-staging.md)
把人物走位、可见关系和信息揭示放在构图前；镜头需要说明存在理由，移动需要触发。
这比泛泛的“电影感、缓推、戏剧性”更有操作价值，但本地已经吸收这些方法，新增完整总导演入口会
造成重叠。继续使用既有专业参考，只补“按事件决定停留/切出”的时间决策交接。

[editing-and-assembly](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/editing-and-assembly.md)
包含有用的切镜动机，同时规定24fps、ASL、handles及盲裁头尾配方，甚至建议用运动模糊、插入镜、
叠化掩盖连续性缺口。本地不采用这些固定数值与遮错逻辑：剪辑可以表达批准的省略，不能让必需的
接触、因果或连续性证据消失后宣称成功。不能将[文本 evals](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/evals/run.md)
的覆盖或通过率当作视频质量证据。

其[Beat Sheet](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/assets/beat-sheet-template.md)
和[Shot Plan](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/assets/shot-plan-template.md)
要求秒数与时间码及ASL对齐，适合预算却不直接产生自然节奏；同仓
[Prompt Lexicon](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/prompt-lexicon.md)
允许不需精确分段时使用相对事件提示，反而更接近本次需求。取后者的方法，不迁移前者的第二时长表。

### drama-skills

本题增量最明确的是
[performance-action-timing](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-video-prompts/references/performance-action-timing.md)：
允许以触发、话音、动作前提、反应落点表达节奏；自然并行动作共享时间，顺序动作不能靠“同时”压缩。
容量不足先减少无必要竞争动作，仍不足就回导演改镜长/分镜，保留逐字对白；不靠赶词或截断补算术。
本次局部改写这些方法，并通过现有 owners 交接。

[duration_estimate.py](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-write/scripts/duration_estimate.py)
要求项目声明自己的估算参数，缺少参数不输出虚构秒数；它估算剧本时长，不是自动决定单镜节奏。
[旧时序 checker](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/tests/legacy/short-drama-video-prompts/scripts/motion_timing_check.py)
对显式区间做算术，把相对时序列为未测范围而非数值 PASS；这个证据边界值得保留，代码不需移植。
具体消费时仍有风险：其aggregate `status=pass`可同时带 `relative_plans`/`unmeasured_specs`，
必须看明细，不能把总PASS解释成相对节奏已获验证。本地继续用已有逐项QA，不导入该汇总语义。

其[模型实验摘要](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/evaluations/model-behavior-probes.md)
比纯理论建议更有分量：声明 H3 中文对白20次探索、反应写法多臂复测，并报告部分质量评分。
但原片、完整 prompts、逐项评分、精确 SKU/endpoint 等留在仓库外，不能在此独立重看片或复算；
部分盲评流程为模型评审，不能冒作人工验收。因此4.1可发声字/秒、“两处信号、1.5秒内反应”只属于
待复验的有限路线经验，不成为本项目通则，也不据评分宣称优于现有表演系统。

同摘要的9秒三切比较确实给出逐切关键帧组更接近目标切点/构图的测量，属于值得未来验证的参考设计；
但只有一组短场景、原媒体不在checkout，NCC/切点/台词完整不证明自然度或全片效果。现有参考owner
已经能表达首帧/身份/场景/视频职责，本次不扩大为新的容器生成能力或“无逐切关键帧不能生成”规则。

[H3 方言](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-video-prompts/references/minimax-h3.md)
将 Max 描述为不支持 full-reference，而本地后续已有官方国内 Max 参考输入实片记录。
型号、地区、日期与 surface 不同可能解释差异；旧中转平台限制不能覆盖当前 selected adapter。
同理，不照搬 Seedance 2.0 的镜号/时间写法、2.5的自动定长或 H3三/六字段到所有路线。

## Current Architecture And Actual Gap

| Current owner | Existing capability | Increment / boundary |
| --- | --- | --- |
| `open-video` / coverage v4 | Director决定单镜/多镜、目标、动作、可见变化和具体镜长；validator校验结构与总时长 | 缺的是相对节奏与精确计时的选择方法；不需要新 Director引擎。 |
| `SubjectAction` / `MotionEnvelope` / `Pacing` | `progression`、onset/peak/settle、cadence/tempo_class与shot duration已能表达动作过程和节奏 | 估算依据写既有作者说明；不加第二时间schema或自动字秒公式。 |
| `performance_direction` / `performance_authoring` | 逐人触发、相对阶段、视线/身体/声音表达及QA覆盖 | 完整填写/字面覆盖不证明表演自然；不能全员锁定或强制同一反应强度。 |
| `DialogueIntent(mode=conversation)` | 当前其他任务的未发布工作树支持无单句时窗的有序台词/说话人/反应义务 | 仅 Jimeng / `seedance_2.5` / 原生音频路线；尚不能泛化为H3或任意多人抢话。本地状态来源 `docs/untimed-conversation.md` 不随本次提交；实际使用须重开当前runtime，不以本文获得支持。 |
| Selected authoring / compiler | 表达已封存意图、原生语法、参考身份与scope；未适配模式typed reject | 模型适配不能改写剧情，也不能靠填假秒数、静音或fallback通过。 |
| `ResolvedTimeline` / HyperFrames | 唯一最终帧、sample、source trim、音视频编排 | 导演可依据实际表演提出编辑修订；生成/编辑仍是显式新revision和证据，不原地变更已封存truth。 |

Parent实际读取上述当前源码、相关tests及matrix；CodeGraph核对
`compile_remote_video_prompt` 的调用关系，回到源码确认Jimeng、Seedance、H3等共用与独立边界。
没有因外部方法存在而修改共享compiler、schema、预算、qualification、Runtime或production state。
当前职责清晰，无需为本地Markdown集成额外维护AOCI索引。

## Historical Media And User Experience

以下是现有真实生成，不是本次实验；重用同一输出、记录和抽帧不增加独立样本数。
最后两项为其他任务的本地未提交记录，未夹带发布：
`docs/record_for_agent/2026-10-21-jieshi-seedance-20-fast-comparison.md`、
`docs/record_for_agent/2026-10-25-shizhen-episode01-jimeng25.md`。

| Exact evidence | Observation and user feedback | Implication / limit |
| --- | --- | --- |
| [Seedance2.5温室](../record_for_agent/2026-09-05-seedance25-director-live-test.md)，MP4 `26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a` | 用户总体反馈“很成功”；多景别与叙事推进可见，但铜花触碰前已开，原媒体Gate仍FAIL，声音意图未听验。 | 自主coverage已有正向经验，外部模板未证明更好；因果状态仍须核查。 |
| [Seedance Mini温室](../record_for_agent/2026-09-05-seedance-mini-director-live-test.md)，MP4 `1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564` | 目标3/4/3/5秒的镜头段，实际切点约4.5–4.75、6.5–6.75、9.5–9.75秒；动作与绽放可见，声音意图仍NE。 | 模型没有机械遵守作者秒段；不同模型/时长/Prompt并非受控A/B，不能据此判Mini更好。 |
| [H3机器人参考](../record_for_agent/2026-10-17-generic-h3-robot-reference-pilot.md)，源MP4 `0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9` | 原要求3.5秒平举；3.5秒仍在抬、约4秒到水平，原生成源被拒绝。顶部后续另记带原声编辑版获用户完整1×接受。 | 参考视频不保证逐事件定时；成功的后期是另一artifact，不能改写原生成FAIL，也不能一概否定有声时间映射。 |
| 《界蚀》2.0/Fast本地对照记录 | 用户指出“不自然”；作者输入含多处头身/姿态锁定、各人subtle；外观/构图稳定不抵消僵硬，具体因果尚未隔离。 | 先纠正作者选择与交接，不把字段完整或模型名当自然度。 |
| 《失帧》顺序对白本地记录 | 无固定对白时码的首样被用户指出声画/动作不同步；后续用户认可表演方向，却拒绝人物美术。 | 自由节奏不自动解决speaker绑定、口型或审美；表演/美术/声音结论应分开，不能推成完整媒体验收。 |

本轮重新SHA-256核验前三条原片，均与记录一致；显式调用project-local `video_extract_frames`：
机器人提取0–5秒、0.5秒间隔11帧，实际查看0/2/3/3.5/4/5秒6帧；2.5温室提取10帧，实际查看
0/6.016/15.040/18.048/21.056/27.072秒6帧。3.5秒抬臂未完成和触碰前开花在局部样帧中可见。
这是12帧局部视觉复核，未重新取得完整正常速度观看或听验，不签自然度、音义、完整连续性或新Gate。
未读取旧unknown的音义任务来重试，也未修改任何历史计数/结论。

## Adopted Method And Changes

只改现有 `open-video/SKILL.md` 和 `professional-specialists.md` 的窄路由，并新增
`references/event-led-timing.md`。来源为MIT范围内的局部改写，链接沿既有许可副本；
skill-movie主体不进入本地Skill文本。无需新增依赖、外部Skill入口、状态表或生成适配器。

导演先决定“何事触发何反应、哪些阶段可并行、观众读懂后为何停/切”，再选择合法镜长。
coverage仍有具体预算、封存请求仍有确定设置；内部对白/动作不因预算存在就被平均分秒。
实际表演后可以沿原owner修订编辑切点，最终时间线仍是单一、确定的 `ResolvedTimeline`。
固定用户deadline保持，超载明确返回作者/能力缺口；这种弹性不授权动态超预算或改变已验收要求。

## Verification

现有 `tests/test_production_h3_prompt.py` 与 `tests/test_performance_direction.py` 在当前工作树实际
运行：**61 passed**。它们核验表达、兼容性及不支持模式的边界；本次未改这些代码或测试。

另做五个文本forward cases：自然咖啡对白、5秒单镜长对白/复杂动作、3.5秒硬deadline、H3必须抢话、
把迟到失败改称弹性。实际输出选择8秒作为第一案的暂定文本预算、保留无时码turns；第二案保留原句/
5秒/单镜并报告未测容量；后三案保留固定deadline、unsupported边界与原失败。
不把估时当实测，也没有自动静音/换route/拆固定单镜。
唯一有用建议 ETT-001 为估算依据的保存位置不够明确；Parent确认并补写到既有authoring notes，
不新增字段，不粘贴进native prompt。该forward exercise是文本行为证据，不是独立代码审查或影视质量PASS。

Harness、最终文件/链接核验及Git状态见[本任务记录](../record_for_agent/2026-10-26-director-timing-method.md)。
没有新增图片、视频、语音生成或付费理解；新增媒体调用0，新增生成费用0。

## Limits

未做新的同输入受控生成对照，故无法证明这份作者方法已改善影视质量；未将外部实验摘要升级为
Production qualification、activation、P6、Final Acceptance或通用模型定时保证。
本次是研究与advisory authoring集成，不替其他窗口完成其共享工程/媒体工作，不重新签历史验收。
Git push另受本地main中4个既有未推送提交及其full回归发布阻断限制；本次相关检查不覆盖或解除该阻断，
具体远端SHA、旧失败receipt及归档范围见本任务记录。
自动learning评估为`no_candidate`：本次是资料比较、旧片复核与文本改进，没有新独立可归因质量实验。
