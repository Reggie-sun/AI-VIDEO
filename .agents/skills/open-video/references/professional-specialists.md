# Professional Specialists

## Route By The Missing Decision

Native Codex 使用本地专业方法补足当前决策，再由 `open-video` 汇总到同一故事与 coverage。
不要求每个任务经过所有模块，也不重新设计用户已选定的来源或已经批准的内容。

| Needed decision | Read / responsibility | Return |
| --- | --- | --- |
| 故事/分集、人物动机与知识、对白及戏剧因果 | [Drama authoring](../../drama-authoring/SKILL.md)；Zenstory 方法 | 原有 Story/Scene/Character/Shot 的语义和未决项 |
| 可见人物/场景/道具设定、开场空间依据 | [Production design](../../drama-authoring/references/production-design.md)；Shuohao 方法 | 一致性锚点与开场站位候选，不持有独立 active 站位 |
| 动态调度、观众注意力、摄影覆盖与剪接意图 | 下方 Blocking And Coverage；DirectorSKILL 方法 | 一份整场调度与 ordered coverage |
| 听说反应、情绪表现、动作接触与后果 | 下方 Performance And Action；Kangarooking 方法 | 既定事件的可观察表演，不改变剧情事实 |
| 对白/动作如何共享时间、何时停留或切出、镜头是否装得下 | [Event-Led Timing](event-led-timing.md) | 同一 Shot 的相对节奏、可执行时长选择与切点理由 |
| 广告受众、角度、Hook、商品如何进入表达 | [Ad creative](../../ad-creative/SKILL.md)；Marketing Skills 方法 | 回既有广告 authoring owner 的创意建议 |
| 音乐叙事、主题/场景配乐、延续、留白与听感修订 | [Music Direction](music-direction.md) | 同一声音方案与 `SceneMusicBrief.musical_design`；不另建导演或时间线 |
| 已批准 Shot 的 Seedance 表达 | [Seedance authoring](../../seedance-authoring/SKILL.md) | 预选版本/profile/mode 的 prompt/reference advice；Liyue 仅用于已选 2.5 overlay |

## Blocking And Coverage

空间可读性、镜头选择和节奏沿既有 [Directorial Choices](creative-completion.md#directorial-choices)，
本节补充制作设定向整场调度的交接，不另建一套导演检查表。

制作设定提供家具/门窗/道具锚点与开场候选；Director 接受后才成为同一 Scene/Shot 调度。
中途站起、穿过、交物、离开和相邻镜的衔接由这份完整调度继续表达。发现空间与剧情冲突，
修改对应原稿并复核受影响内容，不维护另一份有不同事实的 staging 表。

变更遮挡/揭示顺序若改变角色或观众何时知道关键信息，返回剧情作者核对，不能视为纯摄影优化。

续拍先重开前镜已接受的实际末态：角色位置、朝向、动作阶段、持物、视线与声音尾部。未拍到的
预期动作不能凭旧 Prompt 补认完成。同场可省略、换景可续接，按已批准的 cut/ellipsis/reset
语义解释变化；没有明确 reset 就不回到最初开场。镜头逐一成立后，再检查相邻剪接和整场。

## Performance And Action

先消费已批准的目标、潜台词、当前知识、情绪输入及用户指定强度。材料没有明确心理事实时，
可提出有依据的选择并标明 Director 补充；局部修复不能重新推测出不同动机、重写台词或更换机位。

把表演写成被触发的过程：说话前的准备，台词发生时的行为，以及听完/行动完成后的余波。
只选能让当前意图可读的眼神、重心、呼吸、面部或声音信号，不要求每个通道都有动作。
倾听者先具备听见/看见信息的条件，再产生回应；角色不能因为观众看到了某事就同步知道。
克制和夸张都由作品需要决定，既不默认落泪/大喊，也不把用户要求的强烈夸张缩成统一微表情。

动作戏写清目标、起势/轨迹、接触或施力、双方/物件的反应和终态。检视下一动作是否有上一动作
提供的支撑、惯性、距离与空档；交物须有持有、接触、承重转移和释放。需要时加入材质声与环境
反馈，不能为每个阶段硬加碎石、烟尘、破坏或镜头震动；无接触、安静收束和固定机位均可成立。
动作复杂度与可用时长共同判断，不固定每段 2–3 秒，也不强制每场铺垫下一轮。

原声与后期声音设计沿 [Directorial Choices](creative-completion.md#directorial-choices) 的声音方案，
不在此另建混音规则或时间线。

## Handoff And Repair

把关键事实、动作起止、说话人与逐字台词、听者反应、物件状态、情绪变化和下一镜义务，写回
当前 Story/Scene/Character/Shot/coverage 表达；本参考不是另一个 schema。

失败归因沿 [Failure Attribution](creative-completion.md#failure-attribution)；按上方职责表退回相应 owner。
合法的 cutaway、遮挡或转场可以服务既定省略，不能把未解释的动作/身份/因果错误遮住后宣布通过。

文本完整性、单帧正确或生成成功不证明自然动作、听感、连续性或全片质量；实际观察不足保持
`NOT_EVALUATED`。专业方法不创建 Production receipt，不执行 Provider 或改变已有验收权限。

## Sources And Adaptation

本地中文方法按明确职责重新编写，未导入上游总流程、工具、评分或风格强制模板。
具体来源和保留的许可声明如下；Liyue 许可副本仅规范末尾空行，条款与版权文字不变。

- DirectorSKILL `c65ae0d14457053efb1e354c7e7f7e120d97fad1`：
  [blocking](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/blocking-and-staging.md)、
  [editing](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/editing-and-assembly.md)；
  [MIT notice](../licenses/DirectorSKILL-MIT.txt)。既有 `creative-completion.md` 的归因与方法继续有效。
- Kangarooking `301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5`：
  [emotion](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/emotion-performance-director/SKILL.md)、
  [action](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/action-fight-prompt/SKILL.md)；
  [MIT notice](../licenses/kangarooking-MIT.txt)。固定秒数、每段反馈、变化运镜和默认克制均不作为普遍规则。
- Liyue `ad0e68ba6ce24fb9ae9c67c9276061cef37663f1` 的 2.5 适配归
  [selected 2.5 overlay](../../seedance-authoring/references/seedance-2.5.md)；
  [MIT notice](../licenses/seedance-2.5-director-MIT.txt)。不从仓库名称推定当前 profile 的能力。
