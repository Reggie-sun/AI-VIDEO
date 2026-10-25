# Music Direction

## Authority And Starting Point

Codex 在现有 Director 中承担 Music Director 职责。先读当前剧情/人物知识、ordered coverage、
声音方案及可用的 exact 画面与原声，再决定音乐。`production/music_direction.py` 是原音乐决策
的独立代码 owner；`suno_music.py` 只接收这些决定并适配 Suno，旧 imports 兼容。
本参考不拥有 Production state、Provider、音乐素材库、QA 分数或第二时间线。

先判断这段需要观众听见什么：人物未说出口的东西、观众暂时不能知道的信息、动作的重量、
场景自身的声音，还是一个值得保留的停顿。音乐可以反衬，也可以延迟释放，不能把角色尚未
知道的转折提前用和声或高潮泄露。画面内歌曲才需要角色在场演唱；普通配乐不默认写歌。

## Spotting And Musical Decisions

在原有声音方案中说明音乐为何进入、如何发展、何时退出、需要让出什么。先用事件锚点，
如“听完回答后”“手松开之后”“切到空椅时”，成片位置由实际表演与 `ResolvedTimeline` 决定。
一条音乐可以跨多个摄影镜头；换镜、换场不必换曲。一个镜头也可以从静默走向音乐再退回环境声。
不按生成片段长度机械分曲，不强迫画面追随生成歌曲的副歌或鼓点。

选需要的音乐维度并写出理由：主导音乐语言、乐器的叙事分工、旋律与和声密度、音区/织体、
脉冲与重音、发展与收束、空间质感、对白下的让位。拍速可以是自由速度、渐变或明确 BPM；
用 BPM 时说明拍号、计拍单位及半拍/倍拍意图。非必要不锁死调性、拍号、乐器数或结构。
“紧张”不自动等于不协和弦乐，“温暖”不自动等于钢琴，“电影感”不自动等于宏大管弦。

| Work | Creative questions, not presets |
| --- | --- |
| 电影 | 观众处在谁的视角？何时需要克制、反衬、长线铺陈或沉默？结尾是否故意悬置？ |
| 电视剧 | 主题在本集如何变化？跨场/跨集是否保留同一动机而改变和声、音区或配器？ |
| 漫剧 | 音乐是否帮助理解夸张动作与停顿？笑点前需要收住还是推动？避免每次反应都加重击。 |
| 广告 | 音乐如何支持商品动作、品牌记忆和文案可懂度？需要节奏驱动还是生活声的真实感？不默认 jingle。 |

主题先从已选 actual 音频辨认轮廓、节奏和音色，再考虑再陈述、变奏或暂不出现。人物、关系、
地点或全片均可有主题，也可没有；仅角色主题使用 `CHARACTER_THEME` 与 `character_id`。
其他主题使用合适的器乐角色，在 `continuity` 写明意图。文字描述不能保证同一旋律被保留。
需要真正延续时优先复用已选源的合适段落，或评估 selected tool 的 source/extend 能力；
新生成的相似风格不能冒充主题延续。源 identity、权利与采用关系沿既有 Registry/committer。

## Authoring And Suno Handoff

对于需要专业设计的 cue，由 Codex 作出选择后填写现有 `SceneMusicBrief` 的可选 `musical_design`：
`role`、`narrative_function`、`style`、`instrumentation`、`pulse`、`development`、`mix_intent`；
按需补 `continuity`、`vocal_direction`、`exclusions`、`listening_checks`。这些是音乐意图而非
控制谱或验收声明；没有指定 Provider/model，也没有硬编码视频类型、BPM、主副歌或秒数。
旧的无设计调用仍走兼容启发式，它只是简单起点，不能宣称已分析剧情并专业作曲。

`direct_music` 把发声设计投影到原 `MusicDirection`。显式设计优先于情绪关键词。
选择 `INTENTIONAL_SILENCE` 时不填发声设计，不制造静音音乐资产；对白/环境声是否保留沿原声音方案。
新结构与配器进入 generation identity，单纯移动编辑窗口不会触发新音乐请求。

选择 Suno 时使用独立 `suno` Skill 的实时命令发现和 prompting guide；不要复制另一套作曲器。
全局声音、配器分工、脉冲与发展进入 `tags`；不想出现的声音单独进入 `exclude`；
唱出的原文放 `lyrics`，器乐不塞伪歌词/时间码。字段超限先由导演删去次要矛盾，不能静默截断。
默认 v6 用于明确意图；只有需要可归因的探索才考虑 wild，mini 可作有授权的草稿选择。
不自动轮换模型、不固定 sliders、不把模型推荐当当前账号资格；资格与价格以执行时证据为准。

唱词只服务确实需要的片内歌、片头/片尾或歌曲段落；当前 `DIEGETIC_SONG` 执行接口仅代表片内歌，
其他歌曲用途先由现有作品声音方案确认，不能伪装成片内歌。中文区分普通话/粤语、声部与唱法，
按实际旋律容量缩短句子、明确呼吸与关键词；不统一限制每行字数，不套副歌模板。

Suno 网页的 Simple Mode 已宣称支持图/视频/音频、多源与局部编辑；当前适配器只接通文本生成。
它没有 source upload、replace-section、mashup 或自动 extend；独立 CLI 的 cover/extend/stems
也不等于本项目已封存这些操作。遇到缺失能力明确报告，可准备手动操作意图，不能伪造已执行。

## Listen In Context And Repair

先听候选，再放回 actual 画面、对白、环境声与拟音中听 exact 渲染；记录文件 SHA、所用源区间、
时间线/混音版本、观察到的事件及具体偏差。逐项对照 `qa_findings` 与本次 `listening_checks`：
情绪/潜台词是否合适、揭示是否过早、重音是否打断表演、对白是否可懂、动机是否延续、
进入退出/尾音是否自然、原声是否重复配乐或丢失、主动留白是否成立。先看目标，再听正常速度全段。

复用 [audio understanding](../../../../docs/audio-understanding.md) 的可用听音路线与既有 video-analysis/
成片 review。`audio_understand` 只返回可听观察，不看剧情、不提供音乐质量裁决；其默认 preview
没有听音证据，实际执行还需原 operator/permit。无真实音频输入或缺画面上下文保持
`NOT_EVALUATED`，不拿响度、ASR、频谱或背景声描述代签影视音乐匹配，更不虚构人工认可。

| Observed failure | Smallest useful intervention |
| --- | --- |
| 曲子合适但遮对白 | 先用现有 P4 gain/ducking/fade、调整进入位置；若音区/织体仍冲突，再改配器密度。 |
| 情绪提前揭底、发展太满 | 指出哪项表演被抢先解释；只改发展、和声张力或音乐进入点，保留已成立的音色/动机。 |
| 接点断裂、尾音截断 | 重开实际源区间，选择完整乐句与尾音，按现有轨道淡变/重叠；不重生整片。 |
| 新曲丢失主题 | 先对听 actual 前段；需要源约束时检查工具能力，不能只重复“same theme”并声称解决。 |
| 器乐出现哼唱/人声 | 核对 instrumental 与排除项；标明确切听到的位置，保留其他已满足项后准备单一变量修订。 |
| 唱词含混 | 核对实际错字/漏字，先改局部音节密度与咬字；接口不支持局部替换时如实说明。 |

每次修订说明失败证据、保留项、改哪一项、为何足够及复验问题。修订建议不自动触发付费操作。
未知提交先恢复原任务；已知结果仍需新请求的完整授权与既有 Gates。没有新假设不盲目重生，
也不为了展示“专业”固定提出三次 A/B。最终审听不能被干声验收替代。

## Sources And Adaptation

本参考为面向影视叙事重新编写的方法；适配了 MJorgin 与 Suno v6 Cookbook contributors 的
[Songwriter 与 references](https://github.com/MJorgin/suno-v6-cookbook/tree/c8e40ff0b10636a7719cbc88bc5f58443ad19907/agents/skills/suno-v6-songwriter)，
原作许可证 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，
[原许可声明](https://github.com/MJorgin/suno-v6-cookbook/blob/c8e40ff0b10636a7719cbc88bc5f58443ad19907/LICENSE)。
改动：取消固定七段输出、必选三实验、固定乐器数与歌曲结构，加入影视 spotting、音乐延续、
对白/原声及成片听感边界。上游未背书此适配；不导入其执行/安全总流程。

模型事实核对 [Suno v6 FAQ](https://help.suno.com/en/articles/13924481)；
参数语义见 [Creative Sliders](https://help.suno.com/en/articles/6141377)、
[Exclude](https://help.suno.com/en/articles/3161921)。具体措辞与音画效果仍是待真实媒体验证的创作假设。
CLI 的 composer 与 prompting guide 已有相近方法，继续由独立工具维护；研究与差异见
[assessment](../../../../docs/research/2026-10-26-suno-music-direction.md)。
