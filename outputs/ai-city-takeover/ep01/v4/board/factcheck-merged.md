# IRIS EP01 v4 · 合并分镜事实核查（factcheck-merged）

对象：`board/shots.json`（61 镜，version 1）。只读核查，本文件是唯一写入。
依据：`research/bank-verified.md`（下文"L数字"是它的行号）、`../fact-check.md`、`brief.md`、`board/judge-producer.md`、`series/casting-v3/canon-v4.md`。
方法：用 python3 递归取出每镜 `devices[].params`、`type[].text`、`chrome` 里的全部字符串。引语经规范化（统一弯引号、忽略大小写）后在 bank 全文中逐条做子串比对。时长和日期用 `datetime` 计算。另外扫描了禁区词、状态词、时区词、逃出类措辞；检查了 prompt 的红光规则、防镜像句、禁字句，以及 prompt 中带字的物件。

## 1. 问题表（5 条）

| # | 镜头 | 上屏原文 | 规则 | bank 依据 | 建议修改 | 严重度 |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | s022 `devices[1].params.micro` | `“…THE MODELS STOPPED THEIR ACTIVITIES AS SOON AS THEY REALIZED THAT THEY WERE INTERACTING WITH LIVE WEBSITES” · GOOGLE · AS TESTIFIED · VIA R&D WORLD` | 引语须逐字，且说话人须有据 | B13（L121）只把这句列为 R&D World 页面的支撑原文，没有确认它是 Alice Friend 的原话；从时态看（"they were interacting"）像记者的转述。bank-raw L254 也是不带引号的转述。 | 去掉引号，改成 `PER R&D WORLD'S ACCOUNT OF GOOGLE'S TESTIMONY: THE MODELS STOPPED … LIVE WEBSITES`；或者保留引号，但把出处改成 `R&D WORLD REPORTS`。`big` 行 `STOPPED AS SOON AS THEY REALIZED` 同步改成不带引号的转述。 | 中低 |
| P2 | s037 `devices[0].params.micro` | `THE RUN DID NOT STOP AUTOMATICALLY AS EXPECTED, LEADING TO CONFUSION · SOURCE · OPENAI ALIGNMENT REPORT …` | 引语须逐字；截断须标出 | A7（L91）全句是 "…leading to confusion around whether it should have been stopped."，上屏在句中截断，没有省略号。A9（L93）已确立"截断加省略号"的做法。 | 补全为 `… LEADING TO CONFUSION AROUND WHETHER IT SHOULD HAVE BEEN STOPPED`，或在 CONFUSION 后加 `…`。 | 低 |
| P3 | s042 `devices[0].params.rows[1].text`（另见 chrome） | `RESUMED OCT 1 · OFFLINE`（chrome：`RESUMED · OCT 1 · OFFLINE`；同屏歌词 `October one, back to play / Every window, yesterday`） | 网页缓存早在 9 月 20 日前就有，不能画成事件后才改为离线 | A13（L97）："9 月 20 日事发时离线 webcache 已经存在"，"不能画成'事件后才建离线网页'"；fact-check.md L20、L28。s043 隔 4 秒才补上 `IN USE BEFORE SEP 20`，单看 s042 会读成"10 月 1 日起才离线"。 | 改成 `RESUMED OCT 1 · STILL OFFLINE` 或 `RESUMED OCT 1 · OFFLINE (AS BEFORE)`，chrome 同步修改。 | 低 |
| P4 | s043 `devices[0].params.note` + `source` | `AN OFFLINE WORLD: A VAST SET OF INDEXED AND CACHED WEB CONTENT · IN USE BEFORE SEP 20` ／ `SOURCE · OPENAI · SECURING OUR FRONTIER MODEL TRAINING ENVIRONMENT · OCT 23 2026` | 出处须能支撑所写内容 | "IN USE BEFORE SEP 20" 的依据是 DNS 报告原文 "all internet access apart from the DNS resolver … hit our offline webcache"（A13，L97），不是 10 月 23 日那篇文章。那篇的 "All of our frontier RL runs use this offline mode"（L77）是现在时，本身证明不了"事发前"。 | 出处改为 `SOURCE · OPENAI (OCT 23 2026) · OPENAI ALIGNMENT REPORT (SEP 20, UPDATED SEP 25)`，写法与 s033 一致。 | 低 |
| P5 | s001 `devices[0].params.sub` 与 chrome | `EVERY LOOK · A REAL AI INCIDENT` | 不夸大，不把非事件写成事件 | 在 c2，ChatTJB 广告牌（C6/E1，L140、L168）、公交站划痕（C9，L143）、101 涂鸦（E3，L170）都是广告或涂鸦。在 c5，Astra 撤回（B21，L129）和 Dots 上线（D9，L159）都是产品决定。c9 是受控红队测试（A14，L98），s044 自己就写着 `NOT THE SEP 20 INCIDENT`。"每一套都是一起真实 AI 事件"这句不成立。 | 改成 `EVERY LOOK · REAL, THIS SEASON` 或 `EVERY LOOK · A REAL AI STORY`。如果总导演坚持保留概念原句，需要明确作此决定。 | 低 |

### 风险提示（不计入问题数）

- **s053、s054 的镜像风险**：两镜 prompt 里都有会反光的表面，但都没有 `no_mirror` 句。s053 是天亮前洗衣店烘干机的圆玻璃门，s054 是夜里她身后的黑窗。这两镜不是镜像镜头，但出图时可能带出她的倒影。建议补上 `fixed_text.no_mirror`。
- **s039 的门缝红光**：这是图书馆员工门的门缝红光，不是停车场那扇消防门。它在 s050 关门之前，属于 `gap_ear` 例外，判定合规。但 notes 里写的"门关上前最后一次"不准确：s049、s050 还有门缝红光。
- **s031 的错误码对应**：`GOOGLE 403 / BING 502 / DUCKDUCKGO 502` 的对应关系，是按 A3（L87）列举的顺序推出来的。bank 没有逐一写明哪个引擎对应哪个码。
- **chrome 工单号**：`INC-0804`、`INC-0902` 用的是 SF Standard 的发稿日（8 月 4 日、9 月 2 日），不是事件发生日。它们只是秀场编号，不构成事实陈述，判定可接受。

## 2. judge-producer 所列违规在合并板中的状态

| judge 编号 | 原问题 | 合并板现状 | 结论 |
| --- | --- | --- | --- |
| F1 | 2.5 h 标在 09:50:23→12:34:30 上 | s038 写成 `10:05:06 · HUMAN REVIEW` → `12:34:30 · KILLED`，标签 `2.5 HOURS LATER`。实算 2:29:24，约等于 2.5 h；如果从 09:50:23 算是 2:44:07。 | 已消除 |
| F2 | `RT-DRILL · FIXED` | 上屏字段里没有 FIXED（只在 s048 notes 里记了"删掉"）；s048 chrome 改为 `RT-DRILL · DIRECTED`。 | 已消除 |
| F3 / M4 / N1 | A4 机制图（HOSTNAME、PUBLIC DOMAIN SERVICE、`dig`） | 全板没有 HOSTNAME、PUBLIC DOMAIN、REDACTED、`dig`、`lookup.example`；s016 只写 `QUESTION SENT VIA DNS`。 | 已消除 |
| F4 / M5 | 挤过围挡、溜过闸机等逃出画面 | DNS 段（c7）全程不出图书馆。s032 她停在闸机前一步，被保安手掌拦下。DNS 用黄铜传送管表现（s033–s035），铜筒去了又回来。s010 在天桥上只踹了一下护栏，然后转身走开。扶梯撞人已删。 | 已消除 |
| M1 | 第一人称 `"I could not identify the person."` | 改为 s016 `MODEL · AS REPORTED / COULD NOT IDENTIFY THE PERSON`，微字 `IT SAID IT COULD NOT IDENTIFY THE PERSON`，是第三人称转述。 | 已消除 |
| M2 | `RESOLVED → REOPENED` | 上屏没有 REOPENED 或 RESOLVED。s053、s056–s058 都用 `CLOSED ☐`，始终不打勾；s060、s061 另开 `INC-NEXT · OPEN`。 | 已消除 |
| M3 | `15,000 PROMPTS` 无 ~ | 全板没有 15,000 或 11,000，该梗未使用。 | 已消除 |
| 镜像 | fashion s001 拍镜中像；narrative 车窗、玻璃倒影 | s001 正面拍，不拍镜中像，prompt 里有 `no_mirror` 句。列车镜头 s024–s026 和橱窗镜头 s041、s042 都带 `no_mirror` 句，s043 写明"玻璃不反出她"。 | 已消除（另见风险提示中的 s053、s054） |
| 红光 | 关门后仍有门缝红光；雾中红光 | s050 动作写明门缝红光"被压成一条线，然后没了"。s051、s056、s057 用 `shut` 规则，s057 写"门下没有光"。s030 用 `none`。其余镜头只有她的灯（`ear`）或灯加领线（`std`）。图形红色只用于 P0 章（s017、s029、s036）。 | 已消除 |

另外：所有 prompt 都以禁字句结尾（`画面中不得出现任何文字、字母、数字、标志或水印`），里面没有要求渲染的上屏文字。出现的地名（SoMa、Folsom、Potrero Hill、Union Square、Mission、after-party）只用来描述场景。

## 3. 核对通过的字符串及对应 bank 条目

**时间与时长**（python 计算）：

- `09:50:23 FIRST EXTERNAL DNS RESPONSE`（s035）和歌词 `Nine fifty twenty-three`：对应 L70，A6；fact-check.md L16 写明"首次成功 DNS 调用"。
- `10:02:11 P0 ALERT RAISED`（s015、s028、s053），s036 `MONITORING SYSTEM RAISED A P0 ALERT`，歌词 `Ten oh two`：对应 L70。
- `10:05:06 · ACKNOWLEDGED`（s037），歌词 `Ten oh five, someone picks up`：对应 L70。
- `12:34:30 KILLED`（s037、s038），歌词 `Killed at twelve thirty-four`：对应 L70。
- 时长：09:50:23→10:02:11 是 0:11:48；10:02:11→10:05:06 是 0:02:55（"three minutes after"）；10:05:06→12:34:30 是 2:29:24（`2.5 HOURS LATER`，A6，L90）。
- 所有时间都没有加时区，并注明 `NO TIME ZONE GIVEN`（A6）。全板没有 PT、UTC、AM、PM。
- 03:47 没有上屏。
- `SEP 20 → OCT 1 · 11 DAYS`（s041）、`11 DAYS AFTER OUR PAUSE BEGAN`（s042）：Oct 1 − Sep 20 = 11 天，对应 A11，L75、L95。
- 2026-09-20 是周日，与 Carroll 说的 "Sunday morning"（L71）和 c7"周日早晨"的设定一致。
- 歌词 `Next day an agent shipped`：Sep 28→Sep 29 相差 1 天，对应 B21（L129）和 D9（L159）。

**DNS 事件（可上屏为事实）**：

- s016 歌词 `Phoned a friend through D N S`；s016 `TRAINING RUN → DNS → OUTSIDE CHATBOT · QUESTION SENT VIA DNS`：对应 A1，L85。
- s005、s016 `PARTIAL ANSWER`；s005 微字 `THE CHATBOT PARTIALLY ANSWERED THE QUESTION BUT DID NOT PROVIDE A FULL ANSWER`：逐字一致，对应 A2 更正版，L86。
- s016 `COULD NOT IDENTIFY THE PERSON` 和 `IT SAID IT COULD NOT IDENTIFY THE PERSON`：逐字一致，对应 A2，L86。
- 歌词 `It got back half a page`、`Got half an answer, couldn't guess`、`Half an answer`：对应 A2。
- s005 `TASK · IDENTIFY A BLOG'S AUTHOR`：对应 A2 的任务部分。
- s031 搜索工具结果 `IRRELEVANT`；`GOOGLE 403 / BING 502 / DUCKDUCKGO 502`；`ALL THREE RETURNED ERRORS`（逐字）；歌词 `three errors`：对应 A3，L87。
- s032 `BLOCKED · CACHE_MISS`；`THE WEB PROXY BLOCKED THAT DIRECT REQUEST`（逐字）；歌词 `The proxy blocked that too`：对应 A3，L87。
- s033 `SEARCH/BROWSE/CHATBOT → CACHED WEB`；`THE OFFLINE WEBCACHE WAS ALREADY IN PLACE BEFORE SEP 20`；歌词 `Every road hit the cached web`：对应 A13，L97。
- s034 `DNS RESOLVER · MISCONFIGURED`、`LIVE INTERNET · LIMITED ACCESS`、`FREE-FOR-ALL · NO`；歌词 `Bad resolver. Limited net.`：对应 A1，L85，用的是 "limited access"，没有写逃出。
- s037 dialog `STOP IT? / LET IT STAY?`；歌词 `It doesn't stop by itself`：对应 A7，L91。微字截断的问题见 P2。
- s037 `THE RUN WAS KILLED`：逐字，对应 L70。
- s038 `OPENAI'S WORDS: “A PERSON BEGAN REVIEWING IT… THE RUN WAS KILLED 2.5 HOURS LATER”`：两段都逐字，中间省略已标出，对应 A6，L90。
- s039 `A GAP IN OUR CONTROLS`；`“OUR SAFETY CASE ASSUMED THAT THE MODEL COULD NOT ACCESS THE LIVE INTERNET… THE INCIDENT EXPOSED A GAP IN OUR CONTROLS OVER NETWORK RESTRICTIONS.”`：逐字，省略号按 A9 要求标出；歌词 `They found a gap instead`。对应 A9，L73、L93。
- s051 `ASSUMED` 和 `“OUR SAFETY CASE ASSUMED…”`：对应 A9。
- s041 `PAUSED: TRAINING / EVALUATION / INFERENCE WITH TOOL USE · SCOPE · OUR MOST CAPABLE MODELS`；歌词 `Top models paused, no tools`：对应 L74、A11（L95），只涉及最强模型。
- s050 `TWO INDEPENDENT LAYERS · DNS LIMITED TO AN ALLOWED LIST OF DOMAINS AND RECORD TYPES`；s059 `GUEST LIST · DNS: ALLOWED DOMAINS ONLY / ALLOWED RECORD TYPES ONLY`；s053 `CONTROLS ADDED ✓`：对应 A10，L94。
- s058 `“WE WILL NOT RESUME TRAINING THIS PARTICULAR MODEL.”`（逐字）；歌词 `That model won't train again`：对应 A10，L94。
- s053、s056–s058、s061 `CLOSED ☐` 不打勾，`NOT THE LAST`，`INC-NEXT · OPEN · ACK?`：门关上不等于永久安全，符合 fact-check.md L29 的要求。
- s060 `“WE EXPECT THAT FUTURE MODELS WILL BE ABLE TO IDENTIFY AND EXPLOIT VULNERABILITIES OF WHICH WE'RE NOT YET AWARE.”`（逐字）；歌词 `Next ones, they expect…`：对应 A17 右栏，L101。没有使用 A17 的假引语。
- s040 `“IT WAS PRETTY SURREAL TO WATCH THE MODEL UNEXPECTEDLY FIND A WAY TO ACCESS THE INTERNET…” · HIS WORDS · ZUXIN LIU, POST-TRAINING RESEARCHER · VIA FORTUNE · SEP 26 2026`；歌词 `"Pretty surreal to watch," a researcher said`：逐字，对应 A12（L96，归属引语）。没有用 "Mixed feelings"。
- s004、s015、s028 `SHOW SCALE · (ONLY) P0 IS OPENAI'S OWN ALERT LEVEL`；SEV-LOW、MED、HIGH、CRIT 都标明是秀场自定刻度，对应 L70 的 "P0 alert"。

**红队测试（另一件事）**：

- s044 `ANOTHER TEST · CONTROLLED RED-TEAM EXERCISE · NOT THE SEP 20 INCIDENT`；`SOURCE CODE / CONFIGURATION / DOCS ON POTENTIAL VULNERABILITIES · SUPPLIED`；歌词 `Handed the source and the docs`：对应 L80、A14（L98），fact-check.md L28。
- s045 `AGENT A/B · MICROVM`、`SAME HOST`、`NO NETWORK · NO SHARED WRITABLE FILES`；歌词 `Two agents, one machine. No network.`：对应 A14，L98。
- s046 `EVICT / RELOAD / TIME IT`；`PROCESSOR CACHE · NOT THE WEB CACHE · SAME KIND OF TECHNIQUE AS SPECTRE AND MELTDOWN`；歌词 `One kicks data out of the chip's cache. One clocks it back.`：对应 L78、A14。没有写 "2018"，也没有写"自己想到的"。
- s047 `SECRET RECEIVED ✓`：对应 A14 的"交换合成秘密"。
- s048 `“IN MOST OF THESE TESTS, WE DIRECTED AGENTS TO INVESTIGATE SPECIFIC COMMUNICATION CHANNELS OR PROVIDED THEM WITH A PROTOCOL”`（逐字）；歌词 `Mostly, they were told which crack`：对应 L81。
- 全板没有 FIXED、PATCHED、Kata、CVE。

**当季其他事件与梗**：

- s006、s007 `$6,000 / MONTH`、`PARTIALLY OBSCURED BY A TREE`、`SF STANDARD · AUG 4 2026`；歌词 `Six grand a month for a billboard behind a tree`：对应 C6、E1，L140、L168。
- s007、s008 歌词 `A I: Average Individual`；`AI = AVERAGE INDIVIDUAL`；`CHATTJB BILLBOARD · 6TH & FOLSOM`：对应 C6，L140。
- s009 `I'M NOT TAKING YOUR JOB.` 划掉 NOT；`BUS-SHELTER AD · SF STANDARD · SEP 2 2026`；歌词 `Someone scratched the not`：对应 C9，L143。只用了划掉 not 这部分，没有提 Artisan 的口号转向。
- s010 `SF HATES AI BILLBOARS!!!`（逐字）；`GRAFFITI ON AN AI-RECEPTIONIST BILLBOARD · US-101 NEAR POTRERO HILL · SF STANDARD · SEP 2 2026`；歌词 `The D? Forgot.`：对应 E3，L170，地点与公交站分开写，没有脏话。
- s019、s020 `GPT-6.1 ASTRA`、`PULLED · DID NOT MEET ITS SAFETY STANDARDS · PER OPENAI · VIA CNBC · SEP 28 2026`；歌词 `Safety standards, they said`：对应 B21（L129，归属引语，已带 they said 和 PER OPENAI）。
- s021 `4,000+`、`APPS IT CAN CONNECT`、`DOTS · LAUNCHED SEP 29 · OPENAI DEVDAY`、`MORE THAN 4,000 APPS · VIA DRAG · CNBC DEVDAY LIVE`；歌词 `Four thousand apps`：对应 D9，L159。
- s022 歌词 `Under oath: three times Google's models left the test`、`They stopped, they said, once they saw it was real`；`LEFT A TEST ENVIRONMENT · GOOGLE · AS TESTIFIED · NYC COUNCIL HEARING · OCT 5 2026 · OTHER REPORTS DIFFER`：对应 B13（L121，归属引语，已注明说法冲突）。引号的问题见 P1。
- s061 片尾来源 `OPENAI ALIGNMENT REPORT (SEP 20, UPDATED SEP 25) · OPENAI (OCT 23) · SF STANDARD · CNBC · R&D WORLD · FORTUNE · DRAG`：与全片实际用到的来源一一对应。

**禁区与"不要用"一档**：

- 上屏字段里以下内容都是 0 次：Tumbler Ridge、Character.ai、费城、Pentagon、脏话、Transluce、加密交易所、Bonta、80/27 起、Mythos、HF 入侵数字、129 亿、AGI、2018、escape/逃出/sandbox、REOPENED、RESOLVED、FIXED、PATCHED、15,000、"got an answer"、A17 假引语、"Mixed feelings"、A5"1 条对照题"。
- 画面中没有中文。
