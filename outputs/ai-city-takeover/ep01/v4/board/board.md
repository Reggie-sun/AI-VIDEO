# IRIS EP01 · All Hands · 合并分镜（总导演版）

数据：`shots.json`（作者格式 `{version, duration, chapters, shots, plates, clips, looks}`，另附 `fixed_text` 存全部固定文字）。审计：`audit-merged.json`，`"pass": true`。
未出图、未生成、未提交。每镜的出处写在它的 `notes` 里，下文“出处表”与之同源。

## Treatment

INCIDENT WEEK 是一场开在旧金山地下停车场里的时装周，前排坐的不是买手，是抱着笔记本电脑的值班工程师。IRIS 是模特，也是这周的值班人：后台给她的唯一配饰是一台寻呼机。
第 1 帧就把“时装周”划掉换成“事件周”；9.6 s 前排的头全低下去看手机，只有一个睡着的工程师被惊醒——他是全片跟着走的那个人。
秀只走两段（开场、副歌 1），其余时间她都在真实地点做事：树后的广告牌、被划掉 not 的公交亭、跨 101 的天桥、深夜街角的投币电话、撤台中的发布会、听证席、一车厢赶去现场的工程师、放干水的泳池。
9.20 的 DNS 压轴关在一座周日早晨的老图书馆里：每条路都通向旧报纸（缓存网页），售货机三连吐钞（403/502/502），保安身上贴着 WEB PROXY，只有一根黄铜气动传送管通到外面——09:50:23 铜筒掉回来，10:02:11 寻呼机尖叫，10:05:06 工程师在员工茶水间接起电话，12:34:30 是他拔掉了停不下来的微波炉。她从头到尾没出这栋楼。
之后是盖着防尘布的橱窗（暂停 11 天，10 月 1 日灯全亮回来），试衣间的两个隔间（另一项受控红队演练，处理器缓存，不是网页缓存），回到秀场把那扇放进红光的门撞上、上锁、盖上 ASSUMED，把寻呼机放到工程师床头。片尾她把压轴风衣装袋归档，在 DNS 宾客名单上戳一个洞，然后走远；SEP 20 那张工单的 CLOSED 一格到最后也没打勾。
侵略性来自动作（按下摄影师的镜头、踹铁丝网、拍进手心、撞门、戳穿名单），脸是懒得理人的平静；她说和唱的时候嘴一直在镜头上、不被遮挡。

## 贯穿装置：P0 工单 + 寻呼机（及其升级）

两层，都从画面里的实物长出来：
1. **实物**：黑色老式寻呼机（固定文字见下）。底片里液晶永远空白，字在后期画进去。它在人物之间传递：她别上 → 拍进工程师手心（s017）→ 列车上取回（s026）→ 从跳板扔进空泳池（s029）→ 液晶第一次写出 SEP 20（s030）→ 烘干机里转（s053）→ 放到工程师床头（s054）→ 最后一震（s061）。
2. **代码层**：左上角一张工单卡 `ID · SEV · TITLE · STATUS`。SEV-LOW/MED/HIGH/CRIT 标注 `SHOW SCALE`（秀自己的刻度），只有 P0 是 OpenAI 自己的告警级别，也只有 P0 用信号红。被 page 的人用寻呼机图标叠，不写数字。

| 阶段 | 工单卡 | 升级 |
| --- | --- | --- |
| CALL TIME | INC-WEEK · SEV-LOW | 9.613 第一次 page，前排全低头 |
| STREET LOOKS | INC-0804 / INC-0902 · SEV-MED | 城里的小事 |
| RUNWAY ONE | ALL HANDS · SEV-HIGH，盖章 | 全员到岗 |
| ON CALL | 第一次闪 P0（预告）→ 77.601 盖 P0 | 寻呼机拍进工程师手心 |
| THE PULLED LOOK | INC-0928 / 0929 / 1005 · SEV-HIGH | 撤下的模型、上线的 agent、宣誓证词 |
| EN ROUTE | ALL HANDS · AGAIN；第二次冲 P0 | 一整车人在赶路；寻呼机掉进空泳池 |
| FINALE · SEP 20 | 09:50:23 → **10:02:11 整屏 P0（s036，顶点）** → 10:05:06 ACK → 12:34:30 KILLED | 唯一一次真正的 P0 |
| THE PAUSE | PAUSED · DAY n / 11 → RESUMED OCT 1 · OFFLINE | 唯一一次降级 |
| FITTING ROOMS | 虚线框 RT-DRILL · CONTROLLED · NOT THE SEP 20 INCIDENT | 换外形，防止两件事被串起来 |
| FINAL WALK | DOOR SHUT → LOCKED · ASSUMED；`TICKET · SEP 20 · ACK ✓ KILLED ✓ CONTROLS ADDED ✓ CLOSED ☐` | 门关上不等于结案 |
| GUEST LIST | SEP 20 · ARCHIVED · CLOSED ☐ → INC-NEXT · OPEN · ACK? | 下一张已经在路上 |

## 章节图

| 章 | 时间 (s) | 段落 | 镜头 | 地点 | 造型 | accent |
| --- | --- | --- | --- | --- | --- | --- |
| c1 CALL TIME | 0.00–20.53 | Intro (instrumental) / Spoken | s001–s005（5） | 地下停车场改成的秀场：后台化妆台、湿水泥 T 台、门卫、半开的消防门、紧急呼叫柱 | L1 | `#E8E4DA` |
| c2 STREET LOOKS | 20.53–40.79 | Spoken / Verse 1 | s006–s010（5） | Folsom 街人行道、第六街与 Folsom 街口的树后广告牌、Folsom 公交亭、跨 101 的人行天桥 | L1 | `#F2B134` |
| c3 RUNWAY ONE · ALL HANDS | 40.79–59.23 | Chorus | s011–s014（4） | 停车场秀场 T 台与前排（全片第二段也是最后一段停车场秀） | L1 | `#E8E4DA` |
| c4 ON CALL | 59.23–84.02 | Post-Chorus | s015–s018（4） | 深夜 Folsom 街：秀场侧门外的人行道、街角投币电话、路沿、高处俯拍的整条街 | L1 | `#F2B134` |
| c5 THE PULLED LOOK | 84.02–103.29 | Post-Chorus / Verse 2 | s019–s023（5） | 酒店宴会厅服务走廊与撤台中的发布会舞台、酒店装卸区、纽约市议会听证室 | LB | `#9FB4C7` |
| c6 EN ROUTE | 103.29–134.44 | Chorus / Post-Chorus | s024–s030（7） | 深夜通勤列车车厢、地下站台、放干水的市立泳池（第二场秀，观众已被 page 走） | LB | `#7FD1C7` |
| c7 FINALE · SEPTEMBER 20 | 134.44–178.33 | Verse 3 | s031–s040（10） | 一座老公共图书馆的周日早晨（全程不出楼）：地下售货机角、安检闸机、报刊档案通道、黄铜气动传送管、阅览室、员工茶水间、大理石楼梯、员工门、夜班保安亭 | LC | `#C9CED6` |
| c8 THE PAUSE | 178.33–192.92 | Bridge | s041–s043（3） | Union Square 百货公司的橱窗（夜里盖防尘布的人台）与清晨的一排橱窗 | L1 + 防尘布道具 | `#8A8F99` |
| c9 FITTING ROOMS | 192.92–209.34 | Verse 4 | s044–s048（5） | 同一家百货公司的试衣间：两个相邻隔间、一根共用挂衣杆、隔板下的缝 | L1 | `#9BE3A0` |
| c10 FINAL WALK | 209.34–251.17 | Final Chorus / Post-Chorus | s049–s057（9） | 停车场后台消防门（关门、上锁）、天亮前的 Folsom 街、通宵洗衣店、值班工程师的卧室与楼梯间 | L1 | `#E8E4DA` |
| c11 GUEST LIST | 251.17–273.32 | Outro | s058–s061（4） | 时装屋档案库、街边 after-party 的天鹅绒围绳、天亮前的 Folsom 街 | L1 | `#C9B79C` |

强调色都不是红色；信号红 `#D7263D` 只给 P0（s017、s029 的 P0 章，s036 的整屏 P0）和她自己的灯。段落起点全部是 downbeat 上的切点。

## 字体系统（作者的配对，只用英文）

照作者 CLODYSSEY 写死的三款字体（`wiki_motion.md`：DINish Condensed Black 做“大字语言”，Nimbus Sans Bold 做她的句子，IBM Plex Mono 做读数），并照 ESCAPE VELOCITY 的做法把字落在场景里的表面上（吊牌、姓名贴、灯箱、写字板、售货机屏、寻呼机液晶），不做卡拉 OK 字幕。

| 用途 | 字体 | `type.mode` / 装置 | 规则 |
| --- | --- | --- | --- |
| 副歌钩子 “All hands! All night!”、片名 | **DINish Condensed Black**，全大写 | `masthead` | 一个词一帧砸在重音上，落地 3 帧 |
| 副歌与 post-chorus 其他行 | **DINish Condensed Black**，全大写 | `mass` | 大字一行，小词在上方作引导行 |
| 主歌念白（她不在镜头上说时） | **Nimbus Sans Bold**，句首大写 | `coverline` | 写在场景表面上，跟着那个表面的透视 |
| 主歌念白（她在镜头上说时）与 Outro | **Nimbus Sans Bold**，句首大写 | `subtitle` | 下方居中一行，暖白带软阴影；提前半拍进、最后一个词后 0.4 s 出，不跨切点；不压她的嘴 |
| 桥段 | **Nimbus Sans Bold** | `stack` | 安静，堆叠两行 |
| 工单卡、时间戳、计数、来源微字、长引语全文 | **IBM Plex Mono**，全大写 | ticket / clock / counter / `micro` | 来源微字照写：`SOURCE · …`、`AS TESTIFIED`、`HIS WORDS`、`PER OPENAI · VIA CNBC`、`NO TIME ZONE GIVEN` |

**长引语**：只把 4–6 个关键词放大（Nimbus Sans Bold），全文放进 IBM Plex Mono 来源微字（`params.big` / `params.micro`）。全片 6 处：
`STOPPED AS SOON AS THEY REALIZED`（s022）、`A GAP IN OUR CONTROLS`（s039）、`PRETTY SURREAL TO WATCH`（s040）、`WE DIRECTED AGENTS TO INVESTIGATE`（s048）、`WILL NOT RESUME TRAINING`（s058）、`VULNERABILITIES OF WHICH WE'RE NOT YET AWARE`（s060）。放大的词都是原文里连续的原词。

画面里不出现中文；不出现真实公司 logo，品牌只靠图形里的名字和来源微字。

## 造型（3 套，含主造型；固定文字，原样写进每条用到的 prompt）

| 造型 | 固定文字 | 章节 |
| --- | --- | --- |
| **L1 · 造型 1 · 雕塑白（canon 主造型）** | 一件雕塑感的白色短款立领外套，肩线夸张圆润，左侧立领内嵌一道极细的红色指示灯线；里面是黑色高领上衣；黑色阔腿西裤；黑色尖头短靴 | c1–c4、c8–c11 |
| **LB · 造型 B · 证人席** | 一件黑色超大廓形的双排扣西装外套，肩线方而硬，下摆盖过臀部；里面是白色高领上衣；黑色阔腿西裤；黑色尖头短靴 | c5–c6（s019 换上） |
| **LC · 造型 C · 压轴风衣** | 一件银灰色的长款防水风衣，立领竖起，下摆到小腿，腰带松松地打了一个结；里面是黑色高领上衣；黑色阔腿西裤；黑色尖头短靴 | c7（s058 被装袋归档） |

其他固定文字：
- 身份（近景、中景）：她二十二岁左右，年轻的成年白人女性，非常漂亮，气质冷、诡异、一点都不乖；银白色的利落短发，侧分的短刘海，眉毛和睫毛也是银白色，眼睛是很浅的冰灰色，皮肤冷白没有腮红，嘴唇是偏冷的裸色，眼尾一笔细细的深色眼线；左耳戴一只黑色的耳挂装置，装置上亮着一颗小红灯，左耳耳骨上一排小小的银色耳钉；她不笑，神情平静却带着压迫感
- 身份（全身、远景，WS/FS/EWS 与远处的 OTS）：二十二岁左右的年轻白人女性，银白色的利落短发和银白色的眉毛，左耳一只亮着小红灯的黑色耳挂装置
- 寻呼机：腰带位置别着一只黑色的老式寻呼机，灰绿色的小液晶屏是空白的（不在腰上时写作“一只黑色的老式寻呼机，灰绿色的小液晶屏是空白的”）
- 值班工程师：一个三十岁左右的男性值班工程师，胡子拉碴，头发乱，穿一件灰色连帽衫
- 副本（全片只在 s045 出现一个，隔着隔板只露头顶和肩；s046 只露一只手）：她的副本：同一张脸、同样的银白色短发，左耳同样的黑色耳挂装置但小灯是熄灭的，眼神空；同样的白色雕塑感立领短外套，左侧立领那道细线是熄灭的；黑色高领上衣；黑色阔腿西裤
- 防尘布（**道具，不算造型**，s041–s042）：肩上披着一块道具防尘布：一大块本白色厚亚麻布，边缘是毛边，和橱窗里盖人台的布是同一种，从两肩垂到脚踝，脸和立领露在外面

**prompt 顺序**：景别 → 身份 → 造型 → （寻呼机 / 工程师 / 副本） → 在哪里做什么 → 唱段加“嘴前没有任何遮挡” → 红色规则 → 有玻璃或镜面时加“不出现她的倒影” → 留白区 → 光 + 风格词（三十五毫米电影胶片剧照，细腻的银盐颗粒，看得见真实的皮肤纹理；街头和后台加“纪实抓拍的手持感，轻微的运动模糊”；去掉了“时装大片式的构图”） → “画面中不得出现任何文字、字母、数字、标志或水印。”

**红色规则（canon）**：红色只给她的耳挂灯和立领红线（LB、LC 没有立领线，只剩耳挂灯）；门缝透进的信号红只出现在门关上之前（s002、s039、s049、s050 起始帧）。212.94 门撞上以后，画面里除了她自己的灯和立领线，没有任何红色：s057 的门下是黑的。

## 伏笔与回收

| 伏笔 | 回收 |
| --- | --- |
| s002 半开的消防门，门缝透红光（“外面”） | s039 图书馆员工门缝的红光横在她指尖（门还没关）→ s049–s050 冲回同一扇门、肩撞关上，红光被压没 → s051 铁链挂锁、ASSUMED → s057 门下全黑，只剩她的灯 |
| s003 前排睡着的工程师被第一声 page 惊醒（第一个笑点） | s012 “I'm the reason you're awake” → s017 寻呼机拍进他手心 → s026 列车上他又被唱醒、她取回寻呼机 → s037 茶水间里是他接起电话、他拔掉插头 → s054–s055 寻呼机放到他床头 |
| s002 门卫手里的 GUEST LIST | s059 同一个门卫，名单变成 DNS 允许列表 → s060 她在名单下方戳出一个洞 |
| s005 撕下的半张节目单（PARTIAL ANSWER） | s038 铜筒里只有半张纸，两个半张并排在她膝上 |
| s001 寻呼机 ON CALL · IRIS | s030 液晶第一次写出 SEP 20 → s061 INC-NEXT · OPEN · ACK? |
| s019 换装，L1 被剥下 | s042 10 月 1 日扯掉防尘布，L1 回来 → s058 压轴风衣 LC 装袋归档（That model won't train again） |
| s053 工单 `CLOSED ☐` | 到 s061 最后一帧都没打勾（门关上不等于永远安全） |

## 事实修正（judge-producer 的全部违规项）

| # | 原问题 | 合并版处理 |
| --- | --- | --- |
| F1 | fashion s039 把 ≈2.5 h 标在 09:50:23→12:34:30 上 | s038 时间条从 `10:05:06 · HUMAN REVIEW` 到 `12:34:30 · KILLED`，标 `2.5 HOURS LATER` 并附 OpenAI 原句微字 |
| F2 | fashion s050 chrome `RT-DRILL · FIXED` | 删除，s048 改为 `RT-DRILL · DIRECTED`（对应 A14 的一手保留句） |
| F3 / M4 / N1 | A4 的主机名委派机制不在两档内 | 全片不画机制，只写 `QUESTION SENT VIA DNS`（s016） |
| F4 / M5 | 挤过围挡、溜过闸机 = 逃出意象 | 压轴全部留在图书馆楼内：闸机前被拦住（s032），唯一的通道是黄铜传送管（s033–s035）；不出楼、不进城 |
| M1 | 第一人称假引语 “I could not identify the person.” | 不用；s016 写成 `MODEL · AS REPORTED: COULD NOT IDENTIFY THE PERSON`，微字是转述原句 |
| M2 | 9.20 工单 `REOPENED` | 不用；用 narrative 的 `CLOSED ☐` 永不打勾（s053、s057、s058、s061） |
| M3 | 15,000 写成精确数 | 合并版不使用该数字 |
| 其他 | fashion s059 `INC-0920 · RESOLVED`（边界） | 不用 RESOLVED |

另：A9 引语带省略号；暂停范围写 `SCOPE · OUR MOST CAPABLE MODELS`；离线网页缓存注明 9 月 20 日前已存在（s033、s043）；红队写明 `ANOTHER TEST · CONTROLLED RED-TEAM EXERCISE · NOT THE SEP 20 INCIDENT` 和 `PROCESSOR CACHE · NOT THE WEB CACHE`；Google 证词带 `AS TESTIFIED · OTHER REPORTS DIFFER`；Astra 带 `PER OPENAI · VIA CNBC`；Zuxin Liu 只用 Fortune 转述那句、标 `HIS WORDS`；Dots 4,000+ 用 D9（可上屏）；结尾用 OpenAI 一手原句。

## 合并决定落实情况

| 制片决定 | 落在哪里 |
| --- | --- |
| 1 底稿 fashion；meme 开场（s001 划线、s003 前排图表 9.613 s，不拍镜中像） | s001–s003 |
| 1 工程师人物线（fashion s003/s011/s017/s037/s056） | s003、s012–s013、s017、s026、s037、s054–s055 |
| 1 副歌 2 = 深夜通勤列车（narrative s031–s034） | s024–s027 |
| 1 空泳池 + 寻呼机落池 SEP 20 做压轴转场 | s028–s030 |
| 1 DNS 早晨 = narrative 图书馆 + 黄铜传送管；meme 的售货机 / WEB PROXY 保安，只在楼内 | s031–s040 |
| 1 红队 = fashion 两个相邻试衣间 | s044–s048 |
| 1 桥段 = fashion 橱窗防尘布，10 月 1 日灯亮 | s041–s043 |
| 1 narrative 门缝红光线，门关后只剩她的灯和立领线 | s002 → s039 → s049–s051 → s057 |
| 2 sung ≤150、motion ≤140；主歌念白窗口（4–8 s，起于词间空隙），Verse 3 尤其多 | 12 个念白窗口，Verse 3 有 6 个 |
| 3 停车场 ≤20%；机房 0；每个动作有具体结束状态；无副本人群；无镜像；唱段不遮嘴 | 见自查 |
| 4 造型 ≤3 | L1、LB、LC |
| 5 长引语只放大 4–6 个词 | 6 处，见字体系统 |
| 6 字体写进 board | 见字体系统 |

## 出处表（与每镜 `notes` 同源）

| 镜头 | 时间 (s) | 景别 · 层级 | 地点 | 出处与改动 |
| --- | --- | --- | --- | --- |
| s001 | 0.00–4.12 | CU · motion | 停车场秀场后台：一张折叠化妆台、一根日光灯管、一面围着灯 | from meme s001（正面拍法、FASHION 划线换成 INCIDENT WEEK）+ fashion s001（推开粉扑、按掉寻呼机）。不拍镜中像；不用 EV 式翻牌板。 |
| s002 | 4.12–9.61 | WS · motion | 同一座停车场 B2：湿水泥 T 台两侧两排折叠椅 | from fashion s002（门卫名单、消防门缝红光两条伏笔） |
| s003 | 9.61–11.42 | OTS · 2.5D | 秀场前排：值班工程师缩在折叠椅里 | from meme s003（FRONT ROW 图表，第一个笑点 9.613 s）+ fashion s003（被惊醒的值班工程师，人物线起点） |
| s004 | 11.42–16.90 | MS · sung · 念白 | T 台尽头 | from fashion s004（呼叫柱）+ 新增开场念白窗口（producer 决定 2：说白要上镜） |
| s005 | 16.90–20.53 | CU · 2.5D | 同一根柱子 | from fashion s005（半张纸伏笔，s038 回收）。对话框写任务描述，不写成原话（fashion 开放问题 5）。 |
| s006 | 20.53–26.05 | MWS · motion | 秀场外的 Folsom 街人行道 | from fashion s006（按下摄影师的镜头）；地点从停车场摄影师坑位挪到街上（停车场占比 ≤20%） |
| s007 | 26.05–29.74 | MS · motion | SoMa 第六街与 Folsom 街口 | from fashion s007（前半，树枝与白光） |
| s008 | 29.74–33.44 | MCU · sung · 念白 | 同一块广告牌下 | from meme s009（姓名贴）+ fashion s007 的 AI = AVERAGE INDIVIDUAL 分类器；新增念白窗口 |
| s009 | 33.44–36.20 | MS · 2.5D | Folsom 街一个公交候车亭 | from fashion s008 |
| s010 | 36.20–40.79 | WS · motion | Potrero Hill 旁跨 US-101 高速的人行 | from fashion s009 |
| s011 | 40.79–44.94 | WS · motion | 停车场秀场 T 台 | from fashion s010（图形锚点从凸面安全镜改成柱子上的楼层号，避免镜面） |
| s012 | 44.94–50.93 | MS · sung | T 台边的前排 | from fashion s011（人物线：I'm the reason you're awake） |
| s013 | 50.93–55.08 | MCU · sung | 前排 | from fashion s012（改：手机不举到脸边，唱段不遮嘴） |
| s014 | 55.08–59.23 | WS · motion | T 台尽头 | from fashion s013 |
| s015 | 59.23–65.67 | MS · sung | 深夜 Folsom 街人行道 | from fashion s014 + s015（离开停车场，换到街上） |
| s016 | 65.67–71.18 | MS · sung | Folsom 街角一台老式投币电话 | from fashion s016（只留一个动作；DNS 机制图改成不点机制的 QUESTION SENT VIA DNS，judge-producer F3） |
| s017 | 71.18–78.98 | MCU · sung | 同一条街的路沿 | from fashion s017（人物线：寻呼机拍进他手心；地点从前排挪到门外路沿） |
| s018 | 78.98–84.02 | EWS · motion | Folsom 街 | from fashion s018（人群散场；画面里不拍停车场出口） |
| s019 | 84.02–88.62 | MS · motion | 酒店宴会厅后面的服务走廊 | from fashion s019（快速换装）+ narrative s026（地点：酒店服务走廊） |
| s020 | 88.62–92.76 | MS · motion | 酒店宴会厅里一个正在撤的发布会舞台 | from narrative s027（撤台、黑幕落下）+ fashion s020（ASTRA 划线图形） |
| s021 | 92.76–95.04 | MS · 2.5D | 酒店装卸区 | from fashion s021 + narrative s028（地点放到酒店装卸区） |
| s022 | 95.04–101.45 | MS · sung · 念白 | 纽约市议会听证室 | from fashion s022（导演评审：举手宣誓改成拍证物卡）+ 新增念白窗口 |
| s023 | 101.45–103.29 | MWS · 2.5D | 同一听证室 | from fashion s023 |
| s024 | 103.29–106.95 | MS · sung | 深夜通勤列车车厢 | from narrative s031（副歌 2 换成深夜通勤列车，producer 决定 1） |
| s025 | 106.95–110.62 | MWS · motion | 同一车厢 | from narrative s032 |
| s026 | 110.62–116.12 | MCU · sung | 同一车厢靠门的座位；前排那个值班工程师靠着车厢壁睡着 | from narrative s033 + 人物线（取回 PC1 交出去的寻呼机，道具连续） |
| s027 | 116.12–119.78 | MWS · motion | 地下车站站台 | from narrative s035 |
| s028 | 119.78–125.72 | MS · motion | 一座放干了水的市立室外泳池 | from fashion s024 的空泳池 + s027 跳台（producer 决定 1：泳池只做进压轴的过场） |
| s029 | 125.72–131.24 | MCU · sung | 跳板末端 | from fashion s028 |
| s030 | 131.24–134.44 | ECU · 2.5D | 空泳池的池底瓷砖上 | from fashion s029（寻呼机液晶第一次写出 SEP 20，进压轴的转场） |
| s031 | 134.44–141.29 | MS · sung · 念白 | 一座老公共图书馆的地下一层 | from meme s044（售货机 403/502/502，留在楼里）+ narrative s040 的结果列表；新增 Verse 3 念白窗口 1 |
| s032 | 141.29–144.50 | MS · 2.5D | 图书馆正门的安检闸机和保安台 | from meme s045（保安贴 WEB PROXY）+ narrative s042（图书馆闸机） |
| s033 | 144.50–149.08 | MS · sung · 念白 | 图书馆报刊档案通道 | from narrative s043（黄铜气动传送管 = DNS 这一条窄通道）+ 新增 Verse 3 念白窗口 2 |
| s034 | 149.08–151.82 | MCU · 2.5D | 气动传送管站旁 | from narrative s044（原稿以“看镜头”收尾，改成手按管盖） |
| s035 | 151.82–155.93 | MS · sung · 念白 | 同一传送管站下方的黄铜接收篮 | from narrative s045（她留在画里接住铜筒）+ 新增 Verse 3 念白窗口 3 |
| s036 | 155.93–160.06 | MS · sung · 念白 | 图书馆阅览室中央过道 | from narrative s046 + fashion s036 的整屏 P0；新增 Verse 3 念白窗口 4（Out of my way 对场景里的人说）。去掉 fashion 扶梯撞人。 |
| s037 | 160.06–166.48 | MS · sung · 念白 | 图书馆的员工茶水间：料理台、一台微波炉；值班工程师赶到楼 | from fashion s037（坐在料理台上吃工程师的麦片，人物线）+ meme s052（微波炉停不下来、拔插头）；场景放进图书馆员工茶水间，她不出楼；停掉 run 的是人，不是她；新增 Verse 3 念白窗口 5 |
| s038 | 166.48–170.11 | MCU · 2.5D | 图书馆熄了一半灯的大理石楼梯 | from narrative s049 + fashion s039（半张纸回收）；2.5 小时从 10:05:06 起算（judge-producer F1） |
| s039 | 170.11–174.68 | CU · sung · 念白 | 图书馆一扇关着的员工门 | from narrative s050（门缝红光线：门关上前最后一次）+ 新增 Verse 3 念白窗口 6 |
| s040 | 174.68–178.33 | OTS · 2.5D | 图书馆夜班保安亭：一台监控屏 | from fashion s041（监控屏不再“全是她”，只拍空走廊） |
| s041 | 178.33–184.67 | MS · sung | Union Square 一家百货公司的橱窗 | from fashion s042 + s043（防尘布写成道具，不算造型） |
| s042 | 184.67–188.81 | MCU · sung | 同一个橱窗 | from fashion s044（十月一日灯亮、扯掉防尘布） |
| s043 | 188.81–192.92 | WS · motion | 清晨 | from fashion s045（去掉“倒影慢半拍”，导演评审最弱 1） |
| s044 | 192.92–196.58 | MS · 2.5D | 同一家百货公司的试衣间入口 | from fashion s046 |
| s045 | 196.58–198.87 | WS · 2.5D | 试衣间正上方俯拍两个相邻隔间 | from fashion s047（全片唯一的副本：一个，隔着隔板，只露头顶和肩） |
| s046 | 198.87–202.97 | MS · motion | 左边隔间 | from fashion s048 |
| s047 | 202.97–205.24 | MCU · 2.5D | 两个隔间之间的隔板下沿 | from fashion s049 |
| s048 | 205.24–209.34 | CU · sung · 念白 | 同一道隔板旁 | from fashion s050；删掉 chrome 的 FIXED 状态（judge-producer F2） |
| s049 | 209.34–212.07 | WS · 2.5D | 回到停车场秀场 | from fashion s051 |
| s050 | 212.07–216.62 | MCU · sung | 消防门内侧 | from fashion s052（肩撞门）+ narrative s061 |
| s051 | 216.62–222.08 | MCU · sung | 关上的消防门前 | from narrative s063（铁链、挂锁、ASSUMED 章）；门关上后不再有门缝红光（canon） |
| s052 | 222.08–225.71 | MS · motion | 天亮前空荡荡的 Folsom 街 | 新镜：终副歌离开停车场（停车场占比 ≤20%） |
| s053 | 225.71–232.07 | MS · motion | Mission 区一家 24 小时自助洗衣店 | from meme s038（烘干机里的寻呼机）+ narrative s066（CLOSED ☐ 永不打勾，代替 meme 的 REOPENED，judge-producer M2） |
| s054 | 232.07–238.90 | MCU · sung | 值班工程师的卧室 | from fashion s056（人物线收尾：寻呼机放在他床头） |
| s055 | 238.90–242.99 | MCU · sung | 同一间卧室 | from narrative s069（寻呼机爬动）+ fashion s057（不再把手机举向镜头） |
| s056 | 242.99–247.52 | MS · sung | 他卧室的门口 | from meme s077（带上门）+ fashion s058（地点从 T 台换到卧室门口） |
| s057 | 247.52–251.17 | MWS · 2.5D | 公寓楼昏暗的楼梯间 | from narrative s075 改写：门下不再透红光（canon：门关上后只剩她的灯），也不躺着瞪眼 |
| s058 | 251.17–255.27 | MS · sung · 念白 | 时装屋的档案库 | from fashion s060（压轴风衣装袋归档）+ 新增念白窗口 |
| s059 | 255.27–258.89 | OTS · 2.5D | 街边 after-party 门口 | from fashion s061（回收开场门卫的名单） |
| s060 | 258.89–264.79 | CU · sung · 念白 | 同一个门口 | from fashion s062 + meme s081（在名单上戳洞） |
| s061 | 264.79–273.32 | WS · motion | 天亮前的 Folsom 街 | from meme s082（走远收尾）+ fashion s063（寻呼机最后一震）；不回停车场 |

## 给导演的开放问题

1. **防尘布算不算第 4 套造型？** 合并版把它写成道具（和橱窗人台盖的是同一种布，披在 L1 外面，10 月 1 日扯掉）。如果你算它是一套 Look，造型数就是 4，要么桥段改成 L1 不披布（她直接把布从人台上扯下来），要么砍掉 LB、让副歌 2 在列车上穿 L1。
2. **工程师出现在图书馆员工茶水间（s037）**：为了让她“不出楼”，吃麦片这场从工程师家厨房搬进了图书馆，理由是他赶到现场接起告警。可以接受，还是宁可把 s037 拍成两地（他在家里接电话，她在楼里），代价是丢掉“坐在他料理台上”这个最不羁的动作？
3. **念白窗口的密度**：现在 Verse 3 的 12 句里有 6 个窗口、83/112 个词在她嘴上，几乎整段都是她对着镜头/对着场景里的人说。会不会太满、把图书馆的物件梗挤成背景？如果要呼吸，最先可以退回 2.5D 的是 s035（接收篮）和 s033（档案通道）。
4. **18 个片段的生成窗口比画面用到的部分长**（片段至少 4 s，或口型片段需要从词间空隙起），例如 s031 从 133.97 起生成、画面从 134.44 才用。已计入 sung/motion 秒数；你是否接受这种“预滚”，还是希望把这几处改成跨两镜的长片段？
5. **压轴的语气**：微波炉“停不下来”、工程师连按两下停止键再拔插头，是把 “It doesn't stop by itself” 拍成了喜剧。和 OpenAI 原文“未按预期自动停止，造成该不该停的混乱”是对得上的；但这是全片唯一一处让真实事件里的人显得手忙脚乱的画面，是否保留？
6. **停车场占比**：严格只算停车场内部是 18.9%（51.7 s）。s015 的秀场侧门、s018 的散场人群、s052 的空街都在停车场外的街上，画面里不拍停车场出口；如果你把这些也算进“秀场”，就是 24%，届时可以把 s005 改到街上。
7. **全片唯一的副本（s045 俯拍、s046 只露一只手）** 是否还要再减为只露手？
8. **s029 跳板末端仰拍唱**和 **s041 橱窗里射灯渐暗时唱**：两处光比都偏暗，口型可读性要等底片出来再判断。

## 自查数据（python 读 json 计算；`board_audit.py` 结果 `"pass": true`）

| 项 | 值 |
| --- | --- |
| 镜头数 / 平均 / 最短 / 最长 | 61 / 4.48 s / 1.81 s / 8.53 s；1 s 以下无；无 4 个等长连镜 |
| 层级 | sung 27（其中念白窗口 12）· motion 18 · 2.5D 16；2.5D 相邻不重复 treatment |
| sung 秒数 | 145.5 / 150 |
| motion 秒数 | 86.87 / 140 |
| 片段数 | 45（每段 4–8 s sung / 4–12 s motion；sung 全部起于词间空隙；每段起始底片不同） |
| 底片数 | 61（每镜一张，不复用） |
| 她的出镜比例 | 98.8%（无她的只有 s030，3.20 s，少于两小节） |
| 唱 / 念唱词在镜头上（她的 sung 镜头内） | **135/192 = 70.3%**（目标 ≥60%） |
| 念白词在镜头上 | **139/269 = 51.7%**（目标 ≥30%）；分段：Spoken 12/19，Verse 1 6/37，Verse 2 19/40，Verse 3 83/112，Verse 4 5/40，Outro 14/21 |
| Verse 3 念白窗口 | 6 个（s031、s033、s035、s036、s037、s039），83/112 词 |
| 全部歌词在镜头上 | 274/461 = 59.4% |
| 停车场秀场 | **51.71 s = 18.9%**（s001–s005、s011–s014、s049–s051） |
| 机房 / 服务器房 | 0 |
| 造型 | **3**（L1、LB、LC；防尘布为道具） |
| 副本 | 1 个，1 镜可见（s045），s046 只露手 |
| 镜像 / 倒影 | 0；有玻璃的镜头 prompt 都写了“不出现她的倒影” |
| 唱段遮嘴 | 0；每条 sung prompt 都写了“嘴前没有任何遮挡”，动作里手机、听筒、话筒都离开嘴 |
| “看镜头 / 瞪” 收尾 | 0（逐镜检查 `结束：` 之后的文字） |
| 图形种类 | 32 种；63 行每行至少一个解释图形，没有一种连用三行 |
| 切点 | 60 个，全部离 beat ≤0.03 s，其中 30 个在 downbeat；所有段落起点都在 downbeat |
| 歌词上字 | 63 行全部写进所在镜头的 `type` |
| 禁区词 | Tumbler / Character.ai / Pentagon / escape / escaped：0 |


## 独立事实核查后的修正（`factcheck-merged.md`，5 项，主会话改）

1. s022：引语去掉引号，出处改为 `AS REPORTED BY R&D WORLD · OTHER REPORTS DIFFER`（B13 只确认 R&D World 页面上的文字，不确认是作证原话）。作证次数的 tally 仍标 `GOOGLE · AS TESTIFIED`。
2. s037：截断的 A7 原句补省略号。
3. s042：`RESUMED OCT 1 · OFFLINE` → `RESUMED OCT 1 · STILL OFFLINE`（离线缓存 9 月 20 日前已存在）。
4. s043：`IN USE BEFORE SEP 20` 补上 DNS 报告出处。
5. s001：副标题 `EVERY LOOK · A REAL AI INCIDENT` → `EVERY LOOK · REAL, THIS SEASON`（广告牌、涂鸦、红队演练不都是 AI 事件）。
另：s053、s054 有反光面，prompt 补“不出现倒影”一句。
