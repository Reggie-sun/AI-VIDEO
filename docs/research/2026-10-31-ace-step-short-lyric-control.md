# ACE-Step Short Lyric Control

Date: 2026-10-31. Status: advisory research; no new generation or quality acceptance.

## Execution Follow-up

主会话随后实测 C/D/E，直接 DiT、标准标签和 SFT 文本生成都未改善完整词证据；完整本地朗读参考配合 SFT cover 的 G 则得到两份基本匹配原词的无提示 ASR，WER约1.33%／0%。实际输入、原速25.175秒参考、30秒歌曲、次数和手机交付见 [guided repair record](../record_for_agent/2026-10-31-iris-local-lyrics-guided-repair.md)。这些是当前单例测量，不能把本页研究建议改标为通用歌词修复规则；听感与完整歌曲验收仍未完成。

## Scope And Observed Failure

目标固定：原76词的内容及顺序、30秒、英语女声、dark electroclash / minimal techno、126 BPM。不删词、不延长、不加速成品，也不通过给 ASR 注入原词制造完整性。

主会话已取得两份完整解码的30秒音频；无原词提示的 Whisper large-v3 对两份各识别约20个规范化词，不能确认完整原词可听。ASR 漏识别不单独证明音频中没有对应词，最终仍须正常速度试听。本笔记不把本次源代码检查当作真实音乐质量验证。

本次只读核对了既有 `runner.py`、`repair-runner.py`、两次 `consume.json` 和原歌词的行数/标签；未复制完整歌词。路径为 `outputs/ai-city-takeover/ep01/audio/ace-step-local-20261031/`。项目经验检索命中并重读 `docs/record_for_agent/2026-10-30-ace-step-local-iris-audition.md`，仅作为历史观察。

## Version And Wiring Findings

源码固定为 `ace-step/ACE-Step-1.5@ca1e85fe9430179831e6bc6be790c332190a3866`；本机 checkout HEAD 一致，所检 `inference.py`、`llm_inference.py`、`constrained_logits_processor.py` 无 working-tree 修改。当前模型为 `ACE-Step/Ace-Step1.5@19671f406d603126926c1b7e2adc169acbcade22` 内的2B turbo和1.7B LM。

- 两次实际参数都是 `duration=30.0`、`thinking=True`、所有 CoT 改写关闭、`use_constrained_decoding=True`、`audio_codes=""`、`batch_size=1`。源码没有按歌词前20词切片，也没有只取第一个 section 的逻辑。完整歌词进入 LM 和 DiT；既有 tokenizer 实测没有截断。
- 30秒对应 `int(30*5)=150` 个5Hz audio codes；codes阶段 token预算为目标码数加10。constrained decoder 到目标前阻止 EOS，到目标后强制 EOS。这个长度约束控制音频码数，不检查76词是否全部实现。[LM token预算](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/llm_inference.py#L238-L303)、[目标码数](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/constrained_logits_processor.py#L1285-L1299)、[EOS约束](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/constrained_logits_processor.py#L1595-L1629)
- LM hints 可以决定 target latent 长度；因此未来保留 LM 的实验应记录实际 audio-code count，而不只依赖最终 WAV 时长。现有 runner 没保存 `result.audios[i]["params"]["audio_codes"]`，现有日志也没有实际码数，不能断言此次实际恰为150，更不能把漏词归因于 code duration bug。[target latents](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/core/generation/handler/conditioning_target.py#L75-L85)、[返回 audio params](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/inference.py#L979-L982)
- `thinking=False` 且所有 CoT flags 为 False，会完整跳过 LM。可传 `llm_handler=None`、保留空 `audio_codes`，直接用 DiT 接收原歌词；这不是只关闭文案改写。[LM入口条件](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/inference.py#L647-L655)
- 两次显式 DiT seed 相同，但 runner 没有显式设置 LM 的全局采样随机态；源码 single 模式不消费传入的 seeds 列表。因此此前不是完全确定的单变量比较。[batch seed与single分支](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/llm_inference.py#L1344-L1362)、[single生成调用](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/llm_inference.py#L1602-L1626)

## Lyrics Layout Evidence

原输入有5个结构段，包括 Intro、Verse、Pre-Chorus、Chorus、Outro，部分标签包含多个表演描述。官方支持简短结构标签，并建议把复杂表演要求放 caption；过长复合标签可能被当歌词或造成条件冲突。官方同时建议每行约6–10音节、相应位置音节数接近。[标签指导](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/Tutorial.md#L429-L464)、[音节指导](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/Tutorial.md#L509-L526)

因此，标准标签和简洁短语换行有文档依据；“把每段全部合成一个很长的连续行能迫使快速唱完”没有所检官方证据，且可能偏离其短行建议。可以原词不变地重排行，但必须将其标为实验假设，不能称为已知修复。76词/30秒约152词每分钟，仅是密度计算，不是模型可完成性保证。

## Model Alternatives And Resource Boundaries

| Official repo_id | 明确能力证据 | 资源与限制 |
| --- | --- | --- |
| `ACE-Step/acestep-v15-turbo` | 当前2B、8步、无可调CFG | 当前已安装；不能靠增大 `guidance_scale` 获得 SFT 式控制 |
| `ACE-Step/acestep-v15-sft` | 官方称50步、支持CFG，语义解析与细节表达更好；音频清晰度可能略逊Turbo | HF文件树约4.79GB；同属2B。无已核实的本任务峰值显存 |
| `ACE-Step/acestep-v15-xl-sft` | 4B DiT、50步、支持CFG；官方宣称更高音质 | HF文件树约20GB；README称加载权重约9GB，建议20GB以上显存，12GB需offload+quantization；HF模型卡另列16GB+offload。与现有LM兼容 |

官方所检材料没有给出上述模型在“76词、30秒”上的完整词率/WER对照。SFT是更可调的后续实验路径；不能把 XL 的音质声明写成已证实的歌词 fidelity 修复。[固定模型说明](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/Tutorial.md#L214-L273)、[SFT文件树](https://huggingface.co/ACE-Step/acestep-v15-sft/tree/main)、[XL SFT文件树](https://huggingface.co/ACE-Step/acestep-v15-xl-sft/tree/main)、[XL模型卡](https://huggingface.co/ACE-Step/acestep-v15-xl-sft)

HF资料为检索日的移动页面，尚未为候选模型封存新revision。HF模型卡把约18.8GB标成bf16，但页面张量概览显示F32，文件树约20GB；与固定README的约9GB加载权重不是可直接等同的数字。新下载容量按文件树估算，实际dtype、显存峰值须主会话另核对，不能承诺当前空闲显存必定足够。

## Voice And Rhythm References

`reference_audio` 对音色、制作与表现风格起全局作用，时间维被汇总，不能把它当逐词节奏或精确声线锁定。`src_audio` 在 `cover` 中提供旋律/节奏/和声结构，可同时传原歌词，但不是逐字强制对齐；作者也解释 cover 常产生旋律变体。[固定官方参考说明](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/Tutorial.md#L712-L769)、[作者关于cover边界的回复](https://github.com/ace-step/ACE-Step-1.5/discussions/209)

如已有30秒、原词完整且节奏正确的可用女声导唱，cover可作为后续结构约束实验；目前未提供这种已验收源。不要把前两条缺完整词证据的产物当作已正确的节奏蓝本。此路还需核对源音频确切时长，因为 cover 使用源长度，不能靠设置 duration=30 截出合格成品。

## Minimal Experiment Order

1. **先做直接DiT对照**：沿用第二条 exact caption、原歌词及排版、seed、8步、30秒、126 BPM、单样本，只关闭 `thinking`；CoT保持关闭，audio_codes保持空。可不初始化LM。验证是否移除LM规划后覆盖有所改善，而不是同时重排歌词后猜原因。
2. **再做布局实验**：若仍不足，在相同直接DiT参数上只规范结构标签，把复杂演唱描述保留在caption；原词与顺序逐词一致，按语义短句/接近6–10音节换行，不把整段强行合成长行。保留新旧格式identity，不能宣称该排版已证明有效。
3. **再考虑SFT**：必要时先2B SFT及其官方50步/CFG设置，复用其余共享权重；它能试验语义遵循控制，额外下载少于XL。XL SFT是后续较大资源实验，不能先以模型更大推定漏词解决。已具备完整节奏导唱时，参考路线可单独评估，避免与模型更换同时发生。

每步先取得已知结果再决定下一步；正常速度真实音频中原词可听、顺序正确才是目标。使用同一无原词prompt ASR作比较辅助，加试听确认，不把 forced alignment 或原词提示ASR当成唱出了原词。执行次数、资源与交付由主会话管理。

## Verification Scope

完成3个精准外部检索query，随后只打开官方固定文档、源码、模型页面和相关作者讨论；只读核对本机既有执行快照。未安装、下载权重、生成音频、修改runtime/测试/Product state。仅新增本笔记；未运行代码测试，未stage、commit或push。研究不改变旧Suno未知结果，也不代表新音频已经修好。

## Human Music Rejection And Source Repair

用户后续试听 G 明确反馈「这个版本为什么bgm都没有，只有词语」；G 的词正确但歌曲音乐失败，强保留 TTS 的 cover 不能作为音乐成功经验。后续独立器乐与演唱片段源制作见 [R4 record](../record_for_agent/2026-10-31-iris-bgm-and-sung-source-repair.md)。当前仅有可试听完整源和技术证据，音乐质量／真唱／接缝／whisper 未人工验收，不提出通用参数结论。
