# Research: AI Native Audio vs Post-Production Practices

## Executive Conclusion

对约 5 分钟、由多个短 Shot 组成的竖屏连续剧，最可靠的做法是：**生成时保留 model-native audio，但把它作为可验收的 source audio，而不是默认 final mix**。逐 Shot 检查后，保留同步且干净的环境声和动作音；精确对白、跨 Shot 声场、音乐、响度与字幕仍由统一后期控制。

对《界蚀》S01，广播“林砚，请在终点站下车。”承担情节信息，字词和表演必须精确，而说话者不在画面内，没有可从原生对白获得的口型同步收益。因此应使用受控后期广播对白作为 final dialogue；Vidu Q3 或 Seedance 2.0 的原生地铁环境声只有通过逐项听审后才保留，并在后期压低、补齐或替换。字幕从最终对白时间线生成，不能依赖模型画面内文字。

## Evidence Boundary

- 本文只采用模型厂商、工具厂商或行业交付方的一手资料。检索到的二手教程和聚合 API 文档未作为结论依据。
- 公开的一手资料能证明产品能力和推荐工作流，但没有披露可审计的专业 AI 短剧成片中每条 final audio stem 的来源。因而“行业普遍完整保留原生混音”没有足够一手证据；本文的成片建议是基于模型限制与成熟后期流程作出的工程推论。
- 根据本仓库 `AGENTS.md`，本次不检索、推导或比较 Provider 当前单价。因此本文不判断“开启声音是否更贵”；该问题需要由既有 sealed runtime profile 和执行 Gate 处理，不能用临时网页价格替代。

## Model-Native Audio Capabilities

### Vidu Q3

- **同步音画能力（HIGH）**：Vidu 官方 Model Map 将 `viduq3-pro` 列为支持同步音视频输出、I2V、首尾帧和 1080p 的模型；Q3 官方页进一步声明可同时生成对话、旁白、音效和音乐，支持中文、英文、日文及多角色对话。[Vidu Model Map](https://platform.vidu.com/docs/model-map)；[Vidu Q3 官方页](https://www.vidu.com/zh/vidu-q3)
- **API 开关（HIGH）**：官方 I2V 文档定义 `audio=true` 为音视频直出，包含对白和音效；Q3 的默认值为 `true`。[Vidu Image-to-Video API](https://platform.vidu.com/docs/image-to-video)
- **分轨限制（HIGH）**：同一 API 文档说明 `audio_type` 的 `All` / `Speech_only` / `Sound-effect_only` 拆分当前只适用于 Q2、Q1 和 2.0 系列，**不适用于 Q3**；并注明 Q3 不支持 BGM 参数。这意味着 Q3 原生输出不能靠请求参数稳定取得“只留环境声、去掉对白”的独立 stem。[Vidu Image-to-Video API](https://platform.vidu.com/docs/image-to-video)

### Seedance 2.0

- **同步音画能力（HIGH）**：ByteDance Seed 官方发布说明 Seedance 2.0 使用双声道立体声，可联合生成对白、音效、背景音乐并与画面融合；官方也明确承认仍会偶发 audio distortion。[Seedance 2.0 Official Launch](https://seed.bytedance.com/en/blog/seedance-2-0-%E6%AD%A3%E5%BC%8F%E5%8F%91%E5%B8%83)
- **质量边界（HIGH）**：厂商自己把“偶发音频失真”列为待改进项，所以即使音轨存在、声道正确或大体同步，也不能推导对白字词、音色、无杂音和 final-mix 可用性。
- **API 文档边界（MEDIUM）**：火山方舟公开了 Seedance 2.0 系列提示词指南和视频生成 API 入口，但动态文档在本次检索中未返回可核对的 `generate_audio` 字段正文；本文据此只确认官方发布所述的能力，不转述二手文档中的默认值或参数细节。[火山方舟视频生成 API](https://www.volcengine.com/docs/82379/1520758?lang=zh)；[Seedance 2.0 提示词指南](https://www.volcengine.com/docs/82379/2222480?lang=zh)

## How First-Party Workflows Treat Generated Audio

### Native audio as a fast integrated source

- Google 把 Veo/Flow 的对白、音效和背景声称为 experimental，并说明结果可能变化。这是把原生声音用于快速获得同步素材的直接证据，同时也是逐条验收的理由。[Google Flow speech update](https://blog.google/innovation-and-ai/models-and-research/google-labs/flow-adds-speech-expands/)
- Runway 的官方教育课程把两个路径并列：后期添加 temp music 和 sound design，或使用 Gen-4.5 native audio 取得 integrated sound and dialogue。其语境是 30–60 秒 proof of concept，说明原生音频适合快速预演，但没有声称它天然完成专业 final mix。[Runway Education Curriculum](https://runwayml.com/assets/runway-education-curriculum-packet-dec-2025.pdf)

### Generated audio as editable layers

- Adobe 的官方 Firefly 教程不是把生成声音烘焙后直接交付，而是选择多个 SFX variation，将每个声音放到独立 timeline track，调整时点和音量，并可导出 individual tracks 到 Premiere Pro 或 Audition 继续编辑。这是“生成素材进入后期分层”的明确一手示例。[Adobe Firefly sound-effects workflow](https://www.adobe.com/learn/firefly/web/text-to-sound-effects)
- Runway 的 Workflows 提供 `Extract Audio` 和 `Add Audio`；`Add Audio` 会替换视频原音，官方列出的用途正是用 custom music、voiceover 或 sound design 替换 generated audio，以满足创意和品牌要求。[Runway Utility Nodes](https://help.runwayml.com/hc/en-us/articles/47184761711379-Using-Utility-Nodes-in-Workflows)

### Dialogue, effects, Foley and music converge only at final mix

- Avid 的专业电影声音课程明确把 dialogue、sound effects、Foley、music 视为各自独立的工作流，最后才进入 final mixing 和 mastering。[Avid Film Sound Workflow](https://www.avid.com/resource-center/film-sound-workflow-secrets)
- Blackmagic 的 Fairlight 指南说明：现场对白嘈杂、不清楚或表演不理想时使用 ADR；Foley 用来补脚步、衣物和物体交互；music 可对 dialogue 做 ducking；最终在 mix/master 阶段输出。这些原则同样适用于 AI 生成的 source audio。[DaVinci Resolve Fairlight](https://www.blackmagicdesign.com/uk/products/davinciresolve/fairlight/)
- Adobe 建议在剪辑完成或接近完成时，从可编辑 transcript 创建独立 caption track，再选择 burn-in、embedded 或 sidecar 输出。字幕应跟 final approved dialogue 对齐，而不是绑定某次生成音轨。[Adobe Premiere captions overview](https://helpx.adobe.com/premiere/desktop/add-text-images/insert-captions/about-captions.html)

## Comparison

| Route | Strength | Main risk in a 5-minute serial | Use for 《界蚀》 |
| --- | --- | --- | --- |
| Native audio only | 单 Shot 内音画天然同源，快速获得空间感和动作同步 | 对白错字/音色漂移、偶发失真、每 Shot 音乐与声场不连续；Q3 无原生分轨 | 仅可用于预演或所有音频项都通过 Gate 的简单 Shot，不作为全片默认 |
| Post-production only | 对白、声音身份、音乐主题、响度和字幕可精确统一 | 容易丢掉模型生成时自然形成的微小同步环境声，需人工补 Foley | 适合关键旁白、广播、画外音及需要跨 Shot 严格连续的声音 |
| Hybrid: native source + controlled final mix | 保留可用同步现场声，同时让关键对白和整集声场可控 | 需要逐 Shot 听审、拆分或整轨替换，流程稍多 | **推荐**：原生声先入库为 source，按 dialogue / ambience / Foley / music 四类判定后混音 |

## Recommended Workflow for a Serialized Vertical Drama

1. 在模型和当前 sealed request 支持时生成 native audio，并将原始 MP4 音轨与画面一起保存为 exact source evidence。
2. 对每个 Shot 分别验收：对白字词与角色声音、环境声合理性、动作同步、杂音/失真、音乐污染。音轨“存在”不等于通过。
3. 将可用成分路由到明确类别：`dialogue`、`ambience`、`Foley/SFX`、`music`。若模型只给 mixed track 且错误成分无法可靠分离，整轨替换，不能把污染带入成片。
4. 关键叙事对白由受控配音/ADR/TTS 产出；原生对白只有在文本、表演、身份和技术质量全部通过时才保留。画外对白尤其适合后期替换，因为没有破坏口型同步的代价。
5. 环境声可优先保留原生同步片段，但要用统一 room tone 跨 Shot 铺底，并对对白做 ducking；动作音缺失或不准时补 Foley。
6. 音乐按整集弧线统一设计。不要把各 Shot 随机生成的音乐直接串联；Q3 无 API 级音频拆分时，应在 prompt 中避免不需要的音乐，若仍出现则整轨替换。
7. 在 picture edit 接近锁定、final dialogue 已定后制作字幕；字幕作为独立 timeline track，经人工校对姓名、标点和时间，再按交付要求 burn-in 或输出 sidecar。

## S01 Decision

S01 前三秒的核心不是“有人开口”，而是观众必须准确听到广播点名林砚，并同时感到列车仍在运行。最佳分工是：

- `final dialogue`：后期生成/录制准确的“林砚，请在终点站下车。”，使用统一的站内广播声线、带宽限制和车厢反射；这条对白跨后续 Shot 复用时可以保持同一身份。
- `native ambience candidate`：保留模型给出的轮轨、车厢低频、空调和玻璃附近空间声，前提是无错误对白、无随机音乐、无失真且与画面连续。若 Q3 mixed track 含错误语音或音乐，整轨不用，改铺统一地铁 ambience。
- `Foley/SFX`：按画面补极轻的衣料移动和手靠近玻璃的细节，避免夸张触碰声，因为手停在玻璃前约 2 cm。
- `music`：由整集后期统一控制；S01 可只用极低的悬疑纹理，不能让每次 Provider 生成自行决定音乐。
- `caption`：在 final broadcast 锁定后，用独立字幕轨呈现“可这条地铁，没有终点站。”；它是叙事字幕，不应从原生广播 ASR 自动生成。

因此，修改后的制作要求应表达为：**原生声音优先采集并逐项验收；可用的同步环境声和动作声进入后期，关键对白、跨 Shot 声场、音乐、响度与字幕由统一合成流程决定最终版本。**

## Sources Consulted

- [Vidu Model Map](https://platform.vidu.com/docs/model-map)
- [Vidu Image-to-Video API](https://platform.vidu.com/docs/image-to-video)
- [Vidu Q3 官方页](https://www.vidu.com/zh/vidu-q3)
- [Seedance 2.0 Official Launch](https://seed.bytedance.com/en/blog/seedance-2-0-%E6%AD%A3%E5%BC%8F%E5%8F%91%E5%B8%83)
- [火山方舟视频生成 API](https://www.volcengine.com/docs/82379/1520758?lang=zh)
- [Google Flow speech update](https://blog.google/innovation-and-ai/models-and-research/google-labs/flow-adds-speech-expands/)
- [Runway Education Curriculum](https://runwayml.com/assets/runway-education-curriculum-packet-dec-2025.pdf)
- [Runway Utility Nodes](https://help.runwayml.com/hc/en-us/articles/47184761711379-Using-Utility-Nodes-in-Workflows)
- [Adobe Firefly sound-effects workflow](https://www.adobe.com/learn/firefly/web/text-to-sound-effects)
- [Avid Film Sound Workflow](https://www.avid.com/resource-center/film-sound-workflow-secrets)
- [DaVinci Resolve Fairlight](https://www.blackmagicdesign.com/uk/products/davinciresolve/fairlight/)
- [Adobe Premiere captions overview](https://helpx.adobe.com/premiere/desktop/add-text-images/insert-captions/about-captions.html)
