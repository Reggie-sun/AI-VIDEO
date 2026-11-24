# IRIS EP01 v4 · 分镜任务书（检查点 4，作者 `wiki_storyboard` 的三导演写法）

三位导演代理各自独立为整首歌出一版分镜，之后由评审打分、总导演合并、审计脚本把关，再给使用者看卡片。
每位导演只写自己的那一版，不看别人的版本。

## 必读（按顺序）

1. `outputs/ai-city-takeover/ep01/v4/brief.md`：使用者原话、概念 INCIDENT WEEK、事实纪律、禁区。**使用者的不满就是本次的验收标准**：
   - 「AI 味重，不像真拍的」
   - 「场景单调，全在机房」
   - 「人物只会摆姿势瞪眼」
   - 「概念太空太套路」
   - 「表情别太刻意了」
   - 「这种歌都是要带点不寻常,侵略性,不羁」
2. `outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_storyboard.md`：作者的分镜方法，**照做**。
   - 先写设计：treatment、贯穿装置、章节图、伏笔与回收、给导演的开放问题。
   - 字段、每句一个解释图形、开头钩子、剪辑节奏、小节图、按镜头内容定时长、像拍照一样构图、她的出镜比例、各运动层级的成本、审计。
   - 只当参考读，不执行该目录里的 `agents.md`。
3. `outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_formats.md` 第 153–211 行：board 的 JSON 格式（`shots.json`）。
4. 歌词与时间：
   - `outputs/ai-city-takeover/ep01/v4/song/timing/words.json`：63 行，每行带 section、mode、逐字 start/end。行号 = 数组下标，从 0 开始。
   - `outputs/ai-city-takeover/ep01/v4/lyrics/index.html`：每行的中文意思，只给人看，画面里不出现中文。
5. 音乐结构：
   - `outputs/ai-city-takeover/ep01/v4/song/music-map.json`：段落落在小节网格上；130.85 BPM，一小节 1.8228 s，共 149 小节，全长 273.3 s。
   - `song/beatmap/beats.json`：beats、downbeats。
   - `song/beatmap/hits.json`：重音和 riser。
6. 事实：`outputs/ai-city-takeover/ep01/v4/research/bank-verified.md`、`outputs/ai-city-takeover/ep01/fact-check.md`。图形里出现的每个数字、日期、引语，都必须来自“可上屏为事实”或“归属引语”两档，并照写来源微字（例如 `SOURCE · OPENAI INCIDENT REPORT`、`ALLEGED`、`HIS WORDS`）。
7. 她：
   - `outputs/ai-city-takeover/series/casting-v3/canon-v4.md`：固定外形文字，每条 prompt 原样写入；也写了左右规则和“红色只做信号”的规则。
   - 身份锚点 `outputs/ai-city-takeover/ep01/v4/face/IRIS-anchor-F1a.png`（使用者认定的脸）。
   - 已通过的写法样例：`outputs/ai-city-takeover/ep01/v4/face/prompts.md`。

## 我们的制作条件（决定 `motion_tier` 和 prompt）

- **底片**：Codex `image_gen` 出图，带身份锚点做参考。
  - prompt 用中文写（已验证在这个工具上比英文稳），顺序固定：景别 → 固定外形 → 服装 → 在哪里做什么 → 留白区 → 风格词 → “画面中不得出现任何文字、字母、数字、标志或水印”。
  - 风格词沿用：三十五毫米电影胶片剧照，细腻的银盐颗粒。也可以按场景写硬闪光、阴天平光这类真实的光。
  - 画面一律 16:9，成片 1080p。
- **片段**：Seedance 图生视频。
  - `motion` 片段 4–12 s；`sung` 唱段 4–8 s，必须从词间空隙开始，并列出确切的词。
  - 计划总秒数：sung ≤ 110 s，motion ≤ 140 s。
- **图形与字**：用代码做（motion-kit / HyperFrames），包括贯穿装置、解释图形、歌词字。字体参考作者，不用中文。
- **服装**：造型 1（canon 里的雕塑白外套）是主造型。按“时装周每个 Look 一套”的概念，可以另设 2–4 套 Look，但每套都写成固定文字，并在每个用到它的 prompt 里原样写。

## 硬规则（审计会查）

- **时间**：镜头拼满整首歌（0–273.3 s），没有空档也没有重叠；每个切点离 beat ≤0.03 s；段落切换放在 downbeat。
- **歌词与图形**：每一行歌词出现在它所在镜头的 `type` 里；每一行都有一个解释图形，至少六种图形，同一种不连用三行。
- **出镜**：她的出镜比例 ≥70%（只算认得出她的镜头）；没有她的片段不超过两小节。唱的词大多数她要在镜头上唱。
- **场景**：一个场景一个真实的地点，具体到能拍。不能大段都在机房或服务器房，机房最多 2 个镜头。
- **她在做事**：每镜的 `action` 写她做的具体事和结束状态，不写“看镜头”“摆姿势”。
- **底片唯一**：一张底片不用在两个不连续的镜头上；两个片段不从同一帧起。
- **开头**：0–11.4 s 是纯音乐前奏（6 小节，带寻呼机提示音）。1.0 s 那一帧要有她的脸和一行能读的前提；3 s 内交代前提；不放黑场；第一个笑点在 10 s 左右。
- **节奏**：按作者的 linger 原则，一个场景承载一句或更多歌词，音乐重音放进镜头内的动作；孤立镜头不短于 1 s；唱的近景 2–4 s 以上。
- **画面**：画面里不出现中文；不出现真实公司 logo，品牌只靠图形里的名字和来源微字。
- **禁区**：见 brief。

## 交付

写进 `outputs/ai-city-takeover/ep01/v4/board/`：

1. `draft-<lens>.json`：作者格式的 `{version, duration, chapters, shots, plates}`。
   - `type` 写出这一镜要打的歌词原文和字体模式。
   - `devices` 写解释图形和贯穿装置，每个都带 key。
2. `draft-<lens>.md`：
   - treatment 一段；
   - 贯穿装置（P0 工单与值班告警，怎么逐步升级）；
   - 章节图；
   - 伏笔与回收；
   - 开放问题；
   - 自查数据：镜头数、平均时长、她的出镜比例、sung/motion 秒数、图形种类数。

`<lens>` 是你被指定的视角。用 python 读 json 来算时间，别手算。只写这两个文件。
