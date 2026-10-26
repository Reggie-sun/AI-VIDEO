# Two Passengers Cold Open Production Plan

## Goal And Scope

执行用户已认可的Rhythm Revision 02，制作约22秒、可随表演在20–28秒内调整的《两位》冷开场；最终交付新开场、片名与完整S01的连续审看版。视频固定Jimeng / `seedance_2.5`、1080p、16:9，最终24fps；不重生成S01，不改原终场。

## Binding Inputs And Owners

创作依据为`docs/superpowers/artifacts/drama/shizhen-episode-01/cold-open-preparation/rhythm-revision-02/director-revision.md`与同目录v4 coverage。Parent独占新`outputs/shizhen-episode01/cold-open-execution-20261026/`及该run的`cold-open-execution/`，既有Project/Registry/Manifest变更只经原committer。其他窗口的广告、Suno旧runner／ledger及历史STOP不属于本任务。

## Invariants And Bounds

前一夜→翌夜的03:17规则、普通同事关系、无第二位保留记忆者、世界改写、S01原片／字幕／原声身份全部保留。原始37秒稿与22秒revision不覆盖。图片初始单元为首态整幅、后态整幅及罗敏近景各一次，known-outcome不合格最多追加一次对应修订；unknown停止。视频先完成前态动态素材逐项Gate，再后态，再平常回答；初始各一次，共三次新增logical Shot提交，原S01／S02累计历史完整读取后封存新有限额度，不因新root归零。known failure仅有具体单变量诊断才准备有限新单元；unknown不重投。

音乐优先核验已有候选是否实际匹配本cue；确需本cue新素材时只准备一次Suno v6（一对候选）的独立新授权单元，保留全部旧计数、UNKNOWN与账号边界，不购买积分。金额／积分只用现有sealed内部bound与实际读回，不凭估价授权或绕Gate。费用最终据实报告。

## Milestones

1. **Art and source preparation.** 用内置imagegen从已查看的S01材质／光照依据建立两人同框首态，核验完整空间与CG人物，再准备后态和近景；原图exact保存，沿generated_source入口导入，不冒充human import或qualified Provider。读取当前原项目、画布、账号、原消费与新节点，冻结源SHA。
2. **Three bounded dynamic components.** 沿现有qualification／orchestrator及committer准备新Shot，封存人物表演、对白、声音与raw/assembly职责。前态结束于车厢遮满，后态从相容遮挡揭出一人，第三段听见“一位”并自然回答。每次exact preview核对参考顺序、open/close、轴线、native prompt、lint、quota／budget／egress与one-use permit；每个MP4后显式project-local video-analysis，所有required findings PASS才下一镜，证据不足先补同bytes证据。
3. **Music and composition.** 沿现有Music Director／Suno adapter准备“缺席的应答”，选择实际可用乐句。前后动态片段只在相容满幅车身处CUT；准确时间、片名、最终声音归Composition/ResolvedTimeline/HyperFrames。音乐在平常回答之后或片名进入、S01前退出；S01完整原音显式进P4，不direct mux，不第二timeline。
4. **Exact film review and preservation.** 核对消失并非走开／上车，人物／空间／道具／声音连续，空位先读清，平常回答成立，数字与标题正确，S01首字、动作、完整原音及既有字幕未损。正常速度审看并交用户；新原片认可后自动字幕和连续拼接。未有人类认可前不以技术PASS冒充最终接受；完整工程验证与owned-path commit/push按film-first执行，保留真实阻断与所有历史。

## Evidence Boundary

所有执行脚本是调用现有owner的task-local caller，不新增Provider、renderer或通用框架。原生音频/最终混音、抽帧/原速声画、生成成功/质量/人工认可分别记录。缺能力先据当前输入确认最小缺口，不为本片扩建工程；Gate停在具体证据而非虚构PASS。

## User Revision: One Complete Seedance Call

2026-10-26用户明确“可以直接用seedance 2.5一次完成.这个模型最多30s一次生成”。前两段已提交，均保留完整原片、计数与证据；停止原定第三个短回答组件。将尚未消费的第三次冷开场单元 `CO-A3` 改为一条约22秒完整剧情：开画报两位→生活关心→同机位货车完全遮挡→原位只剩罗敏→同侧近景电话核对→平常回答一位。一次生成可以包含两个摄影镜头，不强行一镜到底，不凑满30秒；无模型生成的片名/时钟和背景配乐。准确时间、约3–4秒片名、配乐选句及完整S01仍经P4完成，总目标约25–26秒。

原冷开场3次logical-call上限及每次1500/合计4500内部CRD不增加；22秒所需原生权益及真实quote在提交前核验。同期其他窗口S03单次已核验为paid accepted，独立单元1500；`operator-bound-cross-window.json`保留原9次bound的SHA，六次旧史+S03一次+冷开场三次合计10次、内部总上界11000，均不是市场报价。未知结果停止，不因换whole-event重置已用计数或permit。

## Exact Media Editorial Repair

CO-A1与CO-A2的exact raw Gate为analyzer PASS。用户要求的一次22秒整段CO-A3已实际生成，89帧/真实音频观察完成剧情，但高峥开画缺少参考挎包，原raw identity为FAIL；电话声/棚雨的独立判读仍有证据缺口，不倒签raw PASS。保留此完整原片和原判决，不再生成。采用已合格的双人首段与遮挡后态，加整段版中实际胸上近景的电话回答，修复包的前后状态并压掉长等待；这是P4明确的素材选段，不声称一次原片全部合格。四轮对白均选原生音轨，不挪句、变速、重配或制作音轨假来源。

P4最小必要修复仅限`_composition_visual.py`：被捕获video仍各有一条exact同源、同区间、0gain/no-fade/no-duck对白轨，允许无对白/旁白的STATIC_IMAGE片名及额外BGM/SFX/ambience；同源窗口、字幕归属、连续区间和Production activation fence不变。以现有focused/source-audio/admission测试和实际HyperFrames渲染验证。Risk Gate：局部可回滚，未改变凭据/授权/持久化/激活；主要失败路径有精准负向测试，Parent自审，`NATIVE_REVIEW_NOT_REQUIRED`。完整工程验证与commit/push仍待用户认可成片，不能先阻塞交片。
