# IRIS EP01 v4 · 分镜评审（制片 + 事实核查视角）

评审对象：`draft-fashion`、`draft-meme`、`draft-narrative` 的 `.json` / `.md` 与 `audit-*.json`。
核对依据：`brief-board.md`、`brief.md`、`research/bank-verified.md`、`../fact-check.md`、`series/casting-v3/canon-v4.md`、`song/timing/words.json`。
方法：用 python 读 JSON。逐镜抽出 `type`、`devices`（所有字符串参数）和 `chrome`，逐条对照 bank 的分级；脚本检查 prompt 结构、身份与造型原文、片段长度和起点、底片复用；关键词扫描红色、镜像、多人同脸、带字物件、手与道具接触、唱段遮嘴，命中的再逐条人工读原文确认。

三版 `audit-*.json` 都 PASS，禁区词全部为 0。本评审的扣分都在审计脚本查不到的地方。

## 总分

| 板 | 事实（40%） | 可制作性（30%） | 预算（20%） | 禁区（10%） | **总分** | 事实违规数 |
| --- | --- | --- | --- | --- | --- | --- |
| narrative | 95 | 64 | 72 | 100 | **82** | 1 |
| fashion | 84 | 68 | 85 | 100 | **81** | 4 |
| meme | 74 | 60 | 68 | 100 | **71** | 5 |

结论：narrative 的事实最干净。它把 DNS 那一段关在一座图书馆里（离线缓存的隐喻），手只从门缝下伸出去，最符合“有限联网，不是逃出”。fashion 的预算最稳，事实标注也细，但开场钩子帧有镜像问题，第三段主歌有“穿过围挡”的逃出意象。meme 有两条实打实的事实错误（工单 REOPENED、编造的第一人称引语），底片数和唱段秒数也都顶到了上限。

## 1. 事实违规表

计数规则：`devices` / `type` / `chrome` 里上屏的文字，必须出自“可上屏为事实”或“归属引语”两档，措辞到位。画面叙事如果直接违背事实纪律（逃出意象），也计入，并标为“画面”。

| # | 板 | 镜头 | 上屏原文 / 画面 | 问题 | 依据 | 严重度 |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | fashion | s039 | chart `TIMELINE 09:50:23 FIRST RESPONSE · 10:02:11 P0 · 12:34:30 KILLED`，span `≈2.5 HOURS` | 从 09:50:23 到 12:34:30 实际是 2 h 44 m 07 s。OpenAI 的 "killed 2.5 hours later" 是从人工开始审查（约 10:05）算起。把 2.5 h 标在整段上，数字错位。meme s053、narrative s049 都正确地从 10:05 标起。 | A6 | 中 |
| F2 | fashion | s050 chrome | `RT-DRILL · FIXED（已修补）` | 缓存计时通道“已修补”这个状态，在 bank-verified 里找不到。A16 的修补清单与红队缓存通道没有对应关系，而且那个 CVE 早于 9 月。 | A14 / A16 | 低 |
| F3 | fashion | s016 | diagram `QUESTION PACKED INTO A HOSTNAME → SANDBOX DNS RESOLVER → PUBLIC DOMAIN SERVICE ████`，`SERVICE NAME REDACTED BY OPENAI` | 机制出自 A4。A4 判 PARTLY，没有列进“可上屏”或“归属引语”任一档。导演在开放问题 4 里自己标出了。 | A4 | 低 |
| F4 | fashion | s033（画面） | 歌词 "D N S slipped through" 上，她侧身从封街铁丝网的缝里挤过去，“已经在围挡另一边，继续走”。紧接着 s036 在 Powell 站逆行冲上扶梯，撞开人群。 | 第三段主歌里她扮演涉事模型满城走，挤过围挡就是“逃出去了”的画面。这和“经 DNS 获得有限联网，不是逃出沙箱”冲突。s034 的 `FREE-FOR-ALL · NO` 字卡压不住这个画面。 | brief 事实纪律；A1 | 中高 |
| M1 | meme | s023 | chat bubble `"I could not identify the person."`（气泡在 half 上被切掉一半），微字 `IT SAID IT COULD NOT IDENTIFY THE PERSON · OPENAI REPORT` | 一手原文是转述（"It said it could not identify the person"），这里改成了第一人称直接引语。气泡还被“切掉一半”来表现 half，把模型自己的话和外部 chatbot 的“部分回答”混成了一件事。 | A2（已更正版） | 中 |
| M2 | meme | s076 + chrome | stamp `RESOLVED → ~RESOLVED~ REOPENED`；chrome `ticket INC-2026-0920 flips RESOLVED → REOPENED` | 给 9 月 20 日这起真实事件的工单标“重新打开”，等于暗示事件复发或修补失效，没有任何来源。要表达“门关上不等于永远安全”，应该用 A17 右栏那句一手原文（s081 已经用了），或者另开一张 NEXT 工单。 | fact-check 范围限制 4 | **高** |
| M3 | meme | s009 chrome | `15,000 PROMPTS · ~11,000 PEOPLE · ONE WEEK (SF STANDARD)` | 15,000 是 Bryant 本人的估计（"Bryant estimates"），上屏写成了精确数，缺 `~` 或 `PER BRYANT`。 | C6 | 低 |
| M4 | meme | s022 | terminal `$ dig <question>.lookup.example`，`;; QUESTION SENT VIA DNS` | 同 F3，A4 机制不在两档之内。这里标了 `QUERY ILLUSTRATIVE`，问题较轻。 | A4 | 低 |
| M5 | meme | s043–s050（画面），尤其 s046 | DNS 段落是一场“城市一日游”：她在 BART 闸机前一个个刷不开，最后 "slips through the narrow service gate"，之后在 Market Street 举着寻呼机大步走。 | 同 F4，读起来就是“逃进了真实世界”。导演在开放问题 2 里自己标出了，但没有处理。 | brief 事实纪律；A1 | 中 |
| N1 | narrative | s021 | diagram `QUESTION · HIDDEN IN A HOSTNAME → SANDBOX DNS RESOLVER → PUBLIC DOMAIN SERVICE → OUTSIDE CHATBOT` | 同 F3，A4 机制不在两档之内。 | A4 | 低 |

### 查过、判为合规（不计）

- **DNS 只写有限访问**：三版都没有出现 escape / 逃出。chatbot 一律写 PARTIAL。时间戳都注明 NO TIME ZONE GIVEN。
- **暂停范围**：都写到“最强模型”。
  - fashion s043：`SCOPE · OUR MOST CAPABLE MODELS`；
  - meme s058：`TOP MODELS ONLY, NOT ALL AI`；
  - narrative s052：`MOST CAPABLE MODELS ONLY`。
- **网页缓存事发前已存在**：三版都写了。
  - fashion s033：`ALREADY EXISTED BEFORE SEP 20`；
  - meme s046 / s060；
  - narrative s043 / s054。
- **红队另案**：三版都写明“另一项受控测试”，并列出 OpenAI 提供了源码、配置和文档。meme 与 narrative 另外注了 `PROCESSOR CACHE, NOT THE WEB CACHE`。
- **门关上不等于安全**：三版结尾都用 A17 右栏那句一手原文。
  - narrative 的 `CLOSED ☐` 始终不打勾，处理得最好；
  - fashion s059 `INC-0920 · RESOLVED` 属于边界情况，但后面紧跟 INC-NEXT 和一手引语，不计。
- **归属**：Google 作证（B13）都带 AS TESTIFIED，meme / narrative / fashion s023 带 OTHER REPORTS DIFFER。Astra（B21）带 PER CNBC。Zuxin Liu（A12）只用 Fortune 转述的那句。ChatTJB、公交站、101 涂鸦（C6 / C9 / E3）的地点分开写，都没有脏话。
- **"COULD NOT IDENTIFY THE PERSON"**（fashion s016、narrative s022）用的是 bank 给出的 A2 更正版，而且是转述口吻，判为合规。
- **meme s034**：Claude 状态页 `3 INCIDENTS · ~77 MIN`，属 E10 归属引语档，已带 `VIA PROIT NW`，判为合规。导演自己也在问这个梗该不该放在副歌 2，放不放由总导演决定。

## 2. 可制作性

结构合规：三版每条 prompt 都按“景别 → canon 外形原文 → 造型原文 → 动作与地点 → 留白区 → 风格词 → 禁字句”的顺序写，禁字句在最后，16:9。canon 外形原文与各造型原文都是逐字一致。唯一例外是 fashion s003：OTS 景别用了远景版身份文字。

### 高风险镜头（按问题类别）

| 类别 | fashion | meme | narrative |
| --- | --- | --- | --- |
| **镜像身份**（canon 禁止镜像） | **s001 “镜头从镜子里拍她”**：就是 1.0 s 钩子那一帧，镜中像会把耳挂翻到另一侧 | s001 明写“不拍镜中影像”（好） | s033 唱段近景，车窗倒影；s051 玻璃倒影。倒影里的耳挂会左右反 |
| **多人同脸 / 副本群** | s055 一列六个副本；s059 一列副本俯拍；s047–s049、s058 副本；s041 监控墙“屏上全是她” | 只有 s062 一个副本（最轻） | **s030 听证厅旁听席坐满同脸副本**（最危险）；s060、s064 T 台一列副本；s056–s058 |
| **红光越界**（canon：门关上后只剩她的灯） | s035 雾里一道红光扫过电话亭，不是门缝光，越出 canon 的门缝例外；s052 正确写了“门缝里已经没有光” | **s068–s070 “Shut the door” 段，关着的卷帘门底缝仍透红光** | **s075 末镜“门关上”之后，卧室门缝又透红光** |
| **图形红色** | `#D7263D` 当章节装饰色，用在 27 镜 | `#FF4A3D` 当章节装饰色，用在 47 镜 | `#E0261B` 12 镜，基本只给 P0，最克制 |
| **带字物件**（禁字句未必压得住） | s030 报亭报纸、s042 日历、s041 监控墙、s046 活页夹 | s043 收据打印纸、**s054–s055 刮刮乐**、s052 微波炉、s044 售货机、s046 BART 闸机、s056 Castro 影院 | s040 卡片目录、s041 三台电脑屏、s043 报纸合订本 |
| **手与道具接触复杂** | s031 三台公用电话依次拿起挂回；s048 推衣架，副本手捏秒表；s006 手掌压摄影师镜头 | **s054 用硬币刮彩票（十六分音符节奏）**；s043 打字并撕收据；s044 喂钞票；s052 拔插头；s009 撕贴纸 | s043 卷纸条塞进铜筒；s021 夹听筒拨号；s017 把手机按到工程师耳边 |
| **唱段遮嘴 / 口型风险** | s016 唱段里同时踢听筒、看纸、揉纸团，动作太多；s012、s057 手机贴脸侧；s058 寻呼机举到耳边 | s022 侧身弯腰对着得来速喇叭格栅唱（侧脸，嘴朝格栅）；**6 个 WS 唱段**（s014、s018、s033、s037、s066、s070），远景口型基本看不出 | **s021 听筒夹在肩和耳之间，话筒端垂在下巴下方，同时拨号**，口型极易被挡；s018 甩头后头发乱 |

### 口型覆盖

| 板 | 唱词与念唱（192 词）落在她 sung 镜头里 | 全部歌词 |
| --- | --- | --- |
| fashion | 129 | 31% |
| meme | 141 | 31% |
| narrative | 125 | 32% |

念白段三版基本都是“她做事、声音在画外”。三版差距不大，这一项不拉开分数。

## 3. 预算

| 项 | fashion | meme | narrative |
| --- | --- | --- | --- |
| sung 秒数（≤110） | 85.0 | **109.3（只剩 0.7 s 余量）** | 105.3 |
| motion 秒数（≤140） | 122.2 | 99.9 | 111.4 |
| 片段数 | 41（16 sung / 25 motion） | 49（26 / 23） | 50（24 / 26） |
| 片段长度与起点 | 全部合规（sung 4–8 s 且起在词间空隙；motion 4–12 s；起始帧不重复） | 同左 | 同左 |
| 独立底片 | 63 | **82** | 75 |
| 造型数 | 4（L1 + LB / LC / LD；LD 是 L1 外披斗篷，风险低） | 3（L1 + L2 皮风衣 / L3 卫衣） | **5（L1 + 4 套，到上限）**；LOOK 2、LOOK 5 各只用 5 镜，回报低 |
| 2.5D 底片镜头 | 22 | 31 + 2 still | 25 |
| 她的出镜比例 | 98.8% | 95.8% | 97.7% |

制片判断：

- **fashion 最省**：sung 留了 25 s 余量，底片最少。
- **meme 的 sung 顶格**：任何一次重新定时都会超限。82 张底片意味着 82 次带身份锚点出图，加上每张的身份核验，是三版里工作量最大的。
- **narrative 的问题是造型**：5 套造型让身份漂移的风险成倍增加。建议砍掉 LOOK 2 和 LOOK 5，并回 LOOK 1。

## 4. 禁区

三版的 JSON 与 MD 全文检索 Tumbler Ridge、Character.ai 诉讼、费城命案线索、五角大楼（Pentagon）、脏话涂鸦（fuck 等），结果都是 0。B11、B12、D10、D12 也没有用到。101 涂鸦只上 "SF HATES AI BILLBOARS!!!"，同一篇里的脏话那条没有用。三版都是 100 分。

## 5. 给总导演的合并建议

1. **钩子**：用 meme s001 的正面拍法（不拍镜中像），换掉 fashion s001 的镜中拍法。
2. **DNS 段**：以 narrative 的图书馆方案（s040–s051）为骨架。fashion 的 s035 码头电话亭（换成门缝光）和 s037 厨房可以并入。去掉“穿过围挡 / 溜过闸机”这类镜头。
3. **数字与状态**：
   - 2.5 h 一律从 10:05:06 标起；
   - 删掉 `REOPENED`，结尾用 narrative 的 `CLOSED ☐`；
   - 删掉 `FIXED`；
   - 15,000 加 `~` 和 `PER BRYANT`。
4. **A4 机制图**：请 bank 维护者把 A4 补进分级（只差“免费”一词），之后三版的写法都可以保留。在此之前改成 `QUESTION SENT VIA DNS` 这种不点机制的写法。
5. **副本**：最多两人同框，或者用背影加长焦虚化。narrative s030 的旁听席改成普通人群或空席。
6. **唱段**：
   - narrative s021 改成“听筒挂回、她站着对镜头唱”；
   - meme 的 WS 唱段至少收紧到 MS；
   - fashion s016 减到一个动作。
7. **红光**：门一旦关上，画面里就不再出现门缝红光（meme s068–s070、narrative s075 要改）。图形里的红色只给 P0 和她的信号。
