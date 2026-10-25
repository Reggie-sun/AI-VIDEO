# Lost Frames EP01 — Music Pilot

## Actual Outcome

本轮真实生成未成功。只尝试一次 Suno `generate`，返回 `auth_expired`，没有 clip ID 或音乐文件。
CLI `jobs` 显示该 transaction 为 `rejected`；AI-VIDEO 保守保留 `submission_unknown`，没有改写旧回执。
后续真实请求全部停止，没有刷新登录、换 UUID、追加重试、验证码绕过或购买积分。

用户后续明确要求“预算不要设gate,告诉我到时候消耗多少就可以”，本实验不设置金额/积分门槛，
没有修改全局 Budget Guard；原始最多三次请求上限仍保留。实际尝试 1/3，确认成功 0。
只读账号查询显示 Pro、v6 可用、前后 `total_credits_left=2500`、`monthly_usage=0`，观察到积分变化 0。
没有独立账单结算回执，不把错误状态本身当作零副作用证明。

## Source And Watching Boundary

已有原片：`outputs/shizhen-episode01/失帧-第一集-S01-1080p高清版-Seedance2.5-16秒.mp4`，
SHA-256 `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，
51,142,682 bytes、1920×1080、16.065 秒、H.264 与原生 AAC。第一集已有的五个原片版本均属于首镜，
不能当作五个不同剧情场景；另有同一首镜的字幕审看导出与原声 WAV。
其余监控、店外雨棚、工作间、妹妹录像和身份揭示，目前在所核对的该项目目录内只有剧本/分镜。

本次显式调用 project-local `video_analyze`，禁用转写与 remote audio；检查了 0/4/8/12/14 秒实际帧。
画面显示便利店日常交流、饭团/垫纸与人物反应，没有本集后续灵异画面。自动 scene threshold=0.4
只报一个 scene，但样本已有不同构图，不能以该数字证明没有切镜。`r_frame_rate=60` 也不等于
实测恒定 60fps；ffprobe 的平均帧率为 `23100/961`，不在本轮重写或变速原片。

完整原声已按相同源解码成 48kHz stereo PCM16 WAV，另取四秒做当前 host 音频输入探针。
`filesystem.read_media_file` 实际返回：`audio content omitted because you do not support audio input`。
因此没有本轮模型听音证据；抽帧不证明连续观看、音画同步、对白或音乐质量。
旧 `audio_understand` 的 UNKNOWN 不重试，也未另行调用付费识音服务。

## Spotting Decisions

以下是导演根据原剧本作出的选择，未取得音乐或对应后续画面时属于创作提案。
事件锚点先于秒数；不把生成长度反过来约束表演，不将每镜等同一条配乐。

| Passage | Music decision | Why / what must remain audible | Actual proof |
| --- | --- | --- | --- |
| 首镜：热饭、垫纸、日常对白 | 不新增配乐；保留原声音方案 | 先让小程成为可信的普通人，不提前告诉观众他将消失；纸与饭团动作、对白应保留 | 有实际首镜、抽帧；本轮听音未完成 |
| 扫码声少一截、柜台空了 | 不用惊吓重击；让声音缺失本身成立 | 人物尚未解释异常，不能由音乐替他给出“怪物来了”的答案；不把所有环境声机械归零 | 只有剧本 |
| 监控呈现另一种顺序 | 选第一条候选的低密度部分，必要时不配 | 音乐陪伴求证，不抢走观众看见证据、理解另一种顺序的时间 | 只有剧本；Suno 请求失败 |
| 店外删去“我确定”、重新走进雨里 | 以雨声为前景，优先不新增音乐 | 让自我怀疑和日常行动并存，避免无依据的悲情升级 | 只有剧本 |
| 两个无关源都缺十一秒 | 第一条同一实际录音的动机再次进入、稍增压力 | 同一音乐身份应由复用同一源片段支持，不通过再抽一条“类似的曲子”假称连续 | 尚无录音，连续性未验证 |
| 林晚先听画外、轻声叫“哥”、警告未说完 | 先让对白和呼吸成立；音乐不在“哥”之前煽情，不用撞击抢危险线索 | 哥哥与录像不是实时通话；先听到她，再理解他的反应 | 只有剧本 |
| 林序看旧照片，说“四年了” | 第二条人物情绪主题候选，保持温度和未解决感 | 允许短暂的亲近，但不替人物哭、不做重逢高潮 | 只做离线准备，未提交 |
| 左袖、面孔、右手动作与最终明日时间 | 音乐退出，回到工作间真实声音；结尾不强加高潮 | 让身份与时间矛盾形成恐惧，不能用“怪物音效”代替视觉对照 | 只有剧本 |

## Request 01 — The Missing Space

用途：监控与修复台的跨场悬疑动机。已尝试，因认证错误停止。
模型 `v6` / `chirp-hawk`，纯器乐，不指定 BPM、长度或精确时间轴，sliders 未设置，无 Max Mode。
主导声音为中低音单簧管的相邻两音、薄层中提琴与少量模拟低音；不等长间隙与未解决尾音
服务“求证使现实更不可靠”。同一源内的动机反复只是一项待听音验证的要求，不是已完成事实。

请求 ID：`68ae0257-5b71-5871-8c49-10d03fc658f7`。
generation identity：`b386f921219eda58c767caa5c24cce938e5ede507db9c0749de0f5f31bfe00ca`。
完整 Prompt、排除项、配置、dry-run、一次性消费及错误见本地包 `request-01/`。
实际没有上传剧本全文、人物素材、图片、视频或音频；只交付封存的文字音乐设计给 CLI。

## Request 02 — An Unfinished Answer

用途：旧照片与哥哥的情绪变化，毡音钢琴与中提琴保留有限温度。
不把妹妹的危险写成煽情重逢；音乐应在台词与反应之后获得空间。
请求 ID：`a456e1a3-13c4-5130-9b8e-e6a2be438ea7`。
generation identity：`04b45809f45c38d75a7f5ec38dd5e700aa78ab9ec19926d18e6c0c82a037425c`。
仅 offline dry-run，未消费 one-use 标记、未提交。跨两条生成的“相邻两音”只是关联假设，
不能保证同旋律/调性；真正连续优先复用已选录音或有证据的 source-conditioned route。
第三次请求保留给有实际偏差证据的单一变量修订，不为凑次数自动生成第三种风格。

## Five Evidence Layers

| Layer | Current verdict | Evidence / missing condition |
| --- | --- | --- |
| 工程接入 | 账号读取 PASS；生成 FAIL；恢复观察 PASS | Pro/v6 读回；真实 generate auth_expired；原 transaction 查询/回执保留；没有重试 |
| 音频文件有效 | Suno NOT_EVALUATED；源原声 derivative 有效 | 无 Suno MP3/WAV；不能以首镜原声代替音乐产物 |
| 音乐创作质量 | NOT_EVALUATED | 没有实际生成音乐，不能从 Prompt 断言配器、动机或结构已成立 |
| 剧情/画面适配 | NOT_EVALUATED | 有创作理由，缺候选音乐与后续实际画面；首镜不加新配乐是选择，非听感通过 |
| 最终成片听感 | NOT_EVALUATED | 未渲染新的配乐成片，未取得本轮正常速度听看或人工认可 |

## Failure Attribution And Repair

1. 实际失败位于 Provider 的生成认证路径：`auth_expired`。读取账户和模型成功不证明生成端接受同一会话。
   根因尚未定位到具体 JWT、session 或端点，不读凭据推测；本轮未做登录/刷新或平台限制绕过。
2. 执行前依据 pinned CLI 源码证实其成功信封为 `data: Clip[]`，原项目只读对象形式，会误判成功
   为 UNKNOWN。已兼容数组并保留旧对象、malformed/空数组/未知拒绝路径；这是工程修复，尚未由本次
   成功生成实证，因为调用停在认证错误。
3. 独立只读审查 R1 找到 task-local summary 写入早于凭据检测；Parent 确认并复用原 `_envelope`
   先验证后持久化。fake title/error-code 机密样式测试不落敏感值，保持 UNKNOWN 且不重提。
   R2/R3 未发现未解决项；R3 还核对了实际 STOP 在新消费/调用前生效。
4. 没有音乐结果，不能把失败归为 Prompt、作曲质量、混音或 v6 不适合影视；也没有依据改词抽卡。

## Recovery And Production Readiness

本轮不具备“真实配乐生产验收完成”的证据。最小恢复条件是已有账户通过正常支持流程获得
可用于生成的有效认证；随后先核对这个确切 transaction 的 rejected/UNKNOWN 证据，经原 recovery
owner 处理，不能删回执或换 UUID 归零。本轮停止状态不能当作后续重试授权。
用户若正常使用官方界面制作音乐，返回原始文件与可追踪 clip 信息后，也可继续本地测量和审听，
但这不证明当前自动接入已修复。

无候选音乐时不伪造 AssetRecord，不将生成音乐伪装普通 IMPORTED 音频，不修改第一集 Registry、
Manifest 或 active pointers。没有 Production activation、P6、Final Acceptance 或音乐 publication。
跨电视剧、电影、漫剧与广告的通用性仍来自共享方法与接口；这次单例认证失败不证明泛化质量。

本地试听/证据入口：`outputs/shizhen-episode01/suno-v6-music-pilot-20261026/index.html`。
其中明确区分首镜原声、实际失败记录及未执行的音乐 Prompt，不显示不存在的生成音频。


## Official UI Recovery — Current Checkpoint

> 后续用户新增一次测试授权，纯CLI已真实生成并下载另一对Scene04候选；累计4次请求、20 credits。
> 旧3次及UNKNOWN不变。最新链路证据见docs/record_for_agent/2026-10-26-suno-cli-skill-preflight-repair.md
> 的Live CLI Recovery；本节“3次耗尽/纯CLI未恢复/盘满”仅保留当时历史状态。

2026-10-26：本节替代上文“只有一次请求/没有音乐”的当前状态，原失败历史保留。
第2次CLI请求经正常auth --refresh后仍auth_expired，无ID。旧ledger保持UNKNOWN，
CLI jobs为rejected/ids=[]。doctor外层success与captcha_preflight的pass只是查询成功，
detail仍为required:true，不能当作生成许可。--no-captcha不豁免平台验证。

用户要求自动操作原reggie/sunruijie42窗口。第3次由已登录官方Create界面单击提交成功，
没有出现需人工处理的challenge，未求解或搬运token。两个clip均complete：

- A：e61e327c-4e53-4e68-9e52-118e3ac0cb64，WAV183.56秒。
- B：6de433ab-dab5-4ca4-a0f5-7665a0d48c01，WAV174秒。

这是同次空位动机设计的两个候选，非两个独立实验。chirp-hawk(v6)，Lyrics空，Duration Auto，
Max Mode/Personalize Off；网页默认滑杆未改：Weirdness50%、Style Influence50%、Variety Normal。
Styles、Exclude、标题经网页复制读回与原意图逐字比对一致。CLI仅查询status并下载MP3/WAV，
四文件完整解码通过；WAV为48kHz双声道PCM16。请求3/3次耗尽，未追加。
余额2500→2490，monthly_usage0→10，实际消耗10 credits，未购买积分。

新证据在outputs/shizhen-episode01/suno-v6-music-pilot-20261026/manual-request-03/：
consume.json、ui-form-readback.json、status-download.json、credits-after.json、audio-validation.json。
后者含源clip、文件路径、字节数、SHA及解码结果，试听入口为上级index.html。
旧认证受阻ZIP只代表首次失败，本次因盘满没有新ZIP。

工程修复：SunoMusicService提交前只读doctor，分别核验jwt/studio_api/captcha要求；
required:true或检查不明时在generate与UNKNOWN写入之前拒绝，不用积分设置预算gate。
原submitted/UNKNOWN先走幂等分支。36项精准回归通过，JUnit位于
.agent/harness/runs/suno-captcha-preflight-repair-focused.xml（非完整Harness回执）。此前related因
其他任务改变HEAD而scope drift，不能报告相关回归整体通过。Parent自审：新前检仅拒绝
有障碍的新提交，主要失败路径有测试，无新凭据读取、Product写入或重试，不触发新独立审查；
旧三轮review不冒充审过新前检。

工程与文件有效性PASS；作曲/主题/声画/最终听感NOT_EVALUATED，当前无法实际听音。
不以元数据评音乐、不盲裁源区间或排名。S01不加新配乐；并行任务新产出S02待审素材，
本音乐实验未审听或混合；旧“后续无素材”仅为初检时间点。当前为外部生成候选，
不关联失败CLI事务，不伪造IMPORTED、Registry激活、P6或成片。canonical资产登记/混音尚未验证，
未证明独立专业影视配乐闭环生产就绪。学习评估no_candidate，无听音质量证据或独立受控对照。
磁盘普通用户可用空间0，commit/push受阻；未清理其他任务文件。

Returned clip metadata: tags are different English texts for A/B; negative_tags absent. UI readback does not prove model compliance; see manual-request-03/wav-download.json.
