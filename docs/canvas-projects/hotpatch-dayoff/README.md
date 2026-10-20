# A Little Warmth After Work

## Creative Brief

中文片名《今天，腰先下班》。目标是原创生活化商业短片：前三秒用“一条长得离谱的待办纸卷占住沙发”制造可理解的视觉问题，随后由伴侣腾出休息位置、真实贴片细节及人物主动休息完成暖意。夸张作用于待办事项，不表示产品治疗、即时消除不适或改变身体功能。

当前用户要求见 [creative-input.txt](../../superpowers/artifacts/ecommerce/hotpatch-dayoff/creative-input.txt)，Director 覆盖见 [director-coverage.json](../../superpowers/artifacts/ecommerce/hotpatch-dayoff/director-coverage.json)。24 秒、9:16、四个剪辑段落是导演选择；三个生成镜头各有职责，真实包装收尾属于独立受控商品画面。首次覆盖文件是对用户创作文字的转录，未把商品图中的广告文案自动当作商品事实。

## Reference Analysis

用户指定的两条竞品视频分别实测 68.300 秒、720×1280、30fps，以及 65.922 秒、540×960、30fps，均有 AAC 音轨。已显式调用 project-local `video-analysis.video_analyze`，逐条观察开头及全片分布帧；不是逐帧观看，也没有平台留存数据或本轮真人听音证据。

共同可见机制：

- 0 秒就展示另一人替女子贴腰贴，先交付动作和用途，再作解释，理解成本低。
- 约 4–9 秒的手部按压与贴片近景让观众看见接触、面积和使用部位；日常家居与衣物提供生活感。
- 多人、多件衣服的重复展示扩大生活代入感，但中后段存在重复按压、反复讲解的空间，原创片应以新的动作和关系变化推进。
- 第二条片四角持续营销贴纸较多；本片用明确的文字层级和空间避让保持人物与商品可读。

上述只是视觉机制分析，不能声称参考片留存、转化或传播效果已实测。原片仅用于风格分析，不作为本片剪辑素材，不上传到视频 Provider。源文件 SHA 和分析范围保存在任务素材目录的 `source-identities.json` 及 project-local MCP 观察中。

## Product Truth

三张图分别提供贴片结构、生活使用示意和橙色包装。正式画面采用图中可读名称“护腰贴”；商品身份以包装图中央橙盒为准，蓝色“护腰”和白色人物线条必须保持。未知品牌字样不重造，不新增认证、功效、温度、持续时长、品牌年限、价格或销量。

三条原始图片路径遗漏了 `~tplv` 中的 `~`；本轮按完整基名唯一匹配实际文件，已实际看图、测 SHA，未改名用户文件。用户提供素材用于本次创作，不等于已核实外部发布权。

人物休息由自己的决定和伴侣照顾引发；不使用疼痛到痊愈的前后对比。尚未取得说明书，不能从竞品直接贴肤的画面推断本产品适用方式。商品段先表现贴片形态与离型纸手部细节，实际动作与材质仍须真实视频证据。

## Creative Review

按 `open-video` creative-completion practice 使用一个 read-only Native Codex `reviewer_high` 检查概念，提出 CC-01（贴片本体缺少可见落点）及 CC-02（真人镜头包装身份未锁定），均为 non_blocking。Parent 在当前 coverage 中增加贴片/离型纸细节并锁定中央橙盒；概念检查不代替实际成片审查。

## Execution Boundary

当前选择由用户最新明确指令确定为 METASO / `MiniMax-H3`，仅通过 canonical `CanvasProductionService`、Planner、Router、`VideoGenerationService` 和 `ProductionStateCommitter` 执行；不使用 Seedance 或 MiniMax 官方接口替代。凭据仅由运行时读取用户指定私密文件中的 exact `METASO_API_KEY` 字段，不保存其值。

用户允许最多三个 5–8 秒视频提交、零自动重抽，以及最多四次 Gemini 音频分析。每镜按自己的 exact 输入、动态白模、原生声音和逐项 Gate 验证。完整后镜只能在前镜真实 MP4 已逐项通过后推进；未知结果停止，不重试或重新发放许可。

任务素材与 canonical Production 根位于 repository 内忽略目录 `runs/hotpatch-dayoff-20261020-001/`。这里只保存创作意图与分析入口；它不拥有可变执行状态、Provider 消费计数、质量 PASS、activation 或交付状态。实际输出时序与最终渲染仍归 `ResolvedTimeline` 和 HyperFrames。

## Acceptance

必须保持完整用户目标：原创、直观、夸张服务内容、无虚构功效、前三秒吸引、真人和产品质感、自然动作反馈、视听节奏与实际 MP4 成片。工程通过、参考图、白模、Provider 返回、抽帧或单镜通过均不能替代全片正常速度听看和用户最终审美认可。未取得的证明保留 `NOT_EVALUATED`，不预测商业传播结果。

## Current Media Checkpoint

2026-10-20：METASO / `MiniMax-H3` 已提交一次并取得首镜，未提交第二镜；Gemini 音频分析实际使用一次。首镜五项画面要求通过显式评估，原生声音因持续流水和喷溅声与客厅情境不符而 `FAIL`，已由 canonical committer 关闭失败，保留原 request、fetch、消费及评估链。严格 generated-video probe 也拒绝原输出契约匹配；实测 768×1344、24fps、175 帧，不能把下载成功称为 Production qualification。

用户指出慢动作感并明确剪辑职责后，按其反馈把首镜处理为 3 秒静音节奏预览：原 0–120 帧映射至输出 0–24 帧，原 120–175 帧映射至输出 24–72 帧。`CompositionSpec` → `ResolvedTimeline` → HyperFrames 完成实际渲染，未 direct mux、未重抽；保留纸卷动作与末段人物对视，不以剪辑抹掉原片声音失败。

预览路径为 `runs/hotpatch-dayoff-20261020-001/opening-render-checked/output/opening-3s.mp4`，SHA-256 `99fe8efd53d345174fc0938ce0d0e320ac9249c56834653003dad9ca76e6e115`。HyperFrames lint/check 为零错误，实测 72 帧、768×1366、24fps、无音轨；已显式 MCP 抽取 12 帧检查可见动作。它使用 `bootstrap_repair_input` 的 sealed `/2` admission，保持 `UNBOUND`、`NOT_EVALUATED`、`development_preview`，未 Production activation、P6、Final Acceptance 或发布。它不是完整成片，替换声音、商品互动、后续镜头及全片真实听看仍未完成。

当前恢复条件是已有 Production owner 能对这份失败源的非生成修复输出执行完整新用途验收并保留旧失败，或获得适用的新有限生成修复授权；不得把失败源普通 import 后伪装成已通过素材，也不得在首镜 barrier 失败时提交下一镜。详见 [checkpoint record](../../record_for_agent/2026-10-20-hotpatch-dayoff-edit-preview.md)。

## User Feedback Revision — 2026-10-21

用户拒绝旧 3 秒预览的怪异观感及静音。当前另有正常速度的 2.25 秒局部动作/声音检查文件 `runs/hotpatch-dayoff-20261020-001/natural-sound-render-v2/output/opening-natural-with-sound.mp4`，SHA `9fc167e0d6adb0ff61c96ccec35c2d3b7cad1f7fa96e91575c9ef47b97bbcd17`。已实际渲染含 AAC 的 MP4，完整音轨模型观察识别纸张窸窣和翻页声；未取得人工听看或商业审美接受。

这段截取没有整镜末尾对视，不能替代完整 S01 或证明自然度问题已修复。新增 `/6` 正常速度 replacement-audio preview 能力仅支持独立 P4 非语音声音，仍是 UNBOUND/NOT_EVALUATED 与 `development_audio_preview`，不能 Production activation。视频提交仍为一次；Gemini 实际分析三次。自制声音版本被模型识别为吱响/擦拭后拒绝，现使用已核验 CC0 的实录纸声与低音量钢琴；来源和失败证据见同一 checkpoint record。完整片制作与旧 raw barrier 仍未完成。
