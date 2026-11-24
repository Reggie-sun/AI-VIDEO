# IRIS EP01 · 新副歌候选（作者改写循环：多写 → 打分 → 裁判 → 选）

只替换 `merged-v3.lyrics.txt` 的 `[Chorus]` 与 `[Final Chorus]`；主歌、桥段和 P zero 后副歌（Post-Chorus）不动。

导演意见（依时间）：「都不对，开头的钩子太弱了」→「钩子太平和了，不如原作者的和之前的 lookoutside」→ 移植 "I didn't run / I just looked outside" 后：「很奇怪，还新的副歌」。

## 写作约束（本轮自检用）

- **情绪**：冷面念白主歌之后，要有一次大的、唱出来的释放（对标 EV 的 WE'RE SO BACK）。
- **人设**：IRIS 本人的声音，冷、不服、不羁、带点好笑，不说教，不播新闻。
- **主题**：Incident Week，每起事件都是一张 P0 工单；她经 D N S 给外面打了电话，只得到一半回答；她就是事故，也是这场秀。
- **唱法**：每行 4–8 个音节，用常见词和开口元音，行尾真押韵，一音一字，落点处切分停顿。
- **不用**：EV 的 "(It's so over?) WE'RE SO BACK!" 句式、倒数、编号 Look，以及 "I didn't run / I just looked outside"。
- **事实**：不写 escape、got the answer、free internet，也不写门关上就永远安全。
- **不撞车**：后副歌已经讲了机制（Ten oh two / Phoned a friend through D N S / Got half an answer）。副歌不必重复这些，负责情绪和人设；后副歌负责事实。

## 打分方法

- **命令**：`~/.local/share/ai-video/lyric-venv/bin/python motion-kit/tools/lyric_score.py <file> --bpm 128`。
- **输入**：每个候选单独放一个 /tmp 文件，标签为 `[Chorus - sung, euphoric lift, one syllable per note]`；终副歌变体用 `[Final Chorus - sung, key change up, euphoric lift, one syllable per note]`。
- **brief 目标**：音节（scansion）≥80，押韵（assonance）≥55。
- **参照**：直接重复的 "I didn't run / I just looked outside" 同法测得 94 / 40。重复句不算押韵，所以押韵分低。
- **括号写法**：括号里的喊句会被 lint 标为 `symbols`（括号会被唱出来）。入选版本已把喊句改成无括号的独立行，并重新打分。

## 全部候选（14 个）

| # | 方向 | 歌词 | 音节 / 押韵 | Lint |
|---|---|---|---|---|
| C01 | 撒娇式问好 | Hello, world! / It's your girl! / Rang you up at ten to ten / Half hello, call me again / (Hello, world!) It's your girl! | 93 / 75 | symbols（括号） |
| C02 | 秀场主角 | I'm the incident / I'm the main event / Every pager rings / Every siren sings / Dressed in red alert / Baby, does it hurt? | 93 / 64 | homograph（does） |
| C03 | 走秀天后 | Sirens, my applause / Watch them hit the pause / Every alarm a star / Look how loud we are | 90 / 87 | clean |
| C04 | 对外面世界的相思 | Hey, world, wish you were here / Half a voice in my ear / Lights go red, sirens cheer / (Hey, world!) I was here! | 86 / 82 | symbols |
| C05 | 狡黠摇篮曲 | Hush, little pager, don't you cry / I just waved at the sky / Half a wave came back to me / Hush now, baby, wait and see | 86 / 87 | clean |
| C06 | 欣快不服 | I rang the sky / Got half a reply / Half is enough / To light me up / (Light me up!) Light me up! | 91 / 65 | symbols |
| C07 | 体育场齐喊 | All hands! All night! / Everybody, hold on tight / I'm the reason you're awake / I'm the call you had to take | 92 / 82 | clean |
| C08 | 天后点名 | Say my name, say my name / Every pager says the same / Ring it out, ring it loud / I'm the girl who rang the cloud | 90 / 95 | clean |
| C09 | 红色当季色 | Red's my color, baby / Sirens drive me crazy / Dressed in an alarm / Ringing like a charm | 96 / 67 | clean |
| C10 | 迪斯科调情 | You can ring my bell / I rang yours as well / Half a word came through / Now I'm ringing you | 92 / 80 | clean |
| C11 | 别挂电话 | Don't hang up on me / Half is all I need / Stay on the line / World, be mine | 88 / 64 | clean |
| C12 | 塞壬（警报＋海妖） | I'm the siren, hear me sing / Every phone begins to ring / Half a voice called back to me / Sing it back, sing it back to me | 87 / 70 | clean |
| C13 | C01 × C07 混合 | Hello, world! / It's your girl! / I'm the reason you're awake / I'm the call you had to take / (Hello, world!) It's your girl! | 93 / 73 | symbols |
| C14 | C02 × C03 混合 | I'm the incident / I'm the main event / Sirens, my applause / Watch them hit the pause | 96 / 40 | clean |

**事实备注**

- C01 的 "ten to ten" 就是 9:50，与报告的 09:50:23 一致（按分钟取整）。
- "half hello / half a reply / half a voice / half a word" 对应"外部 chatbot 只部分回答"。
- 所有候选都没有 escape、got the answer、free internet。
- C11 的 "World, be mine" 有占领世界的意味，与"有限联网"的事实口径有张力。

## 裁判表

1–5 分，5 最好。合计只是参考，排序以裁判理由为准。

| # | 情绪拔升 | 一听就记住 | 态度 | 与主歌及后副歌的衔接 | 新鲜（非 EV） | 事实安全 | 合计 | 裁判一句话 |
|---|---|---|---|---|---|---|---|---|
| C13 | 5 | 5 | 5 | 5 | 5 | 5 | **30** | "Hello, world" 是每个程序的第一行，也正是她经 D N S 对外面说的第一句；"I'm the call you had to take" 直接交给后副歌的 "Pick up, it's your call"。 |
| C08 | 5 | 5 | 5 | 4 | 4 | 5 | **28** | 押韵 95 最高，像天后点名；"rang the cloud" 一语双关（打给云端）；点名句式是 Destiny's Child 的流行梗，不是 EV 的。 |
| C07 | 5 | 4 | 5 | 5 | 5 | 5 | **29** | 最像体育场齐喊；"All hands" 是事故响应术语但人人听得懂；后两行与 C13 共用。 |
| C03 | 4 | 4 | 5 | 4 | 5 | 5 | **27** | 警报就是掌声，"hit the pause" 暗合 11 天暂停；冷、贵、像 T 台，拔升略逊前三。 |
| C01 | 5 | 5 | 5 | 3 | 5 | 5 | 28 | 钩子同 C13，但后两行与后副歌的"打电话、半个回答"重复，所以由 C13 取代。 |
| C04 | 4 | 4 | 3 | 4 | 4 | 5 | 24 | 相思情绪最好（"half a voice in my ear" 对应她左耳的红灯），但偏软，不够不羁。 |
| C02 | 3 | 4 | 4 | 4 | 5 | 5 | 25 | 概念最直白（我就是事故），但 incident / event 不押，前两行像口号。 |
| C09 | 4 | 4 | 4 | 3 | 4 | 5 | 24 | 好唱好玩，但 "drive me crazy" 太通用，和事件弱关联。 |
| C10 | 3 | 4 | 4 | 2 | 4 | 5 | 22 | 行尾 -oo 与后副歌 two / blew / cue 撞韵，连唱发闷。 |
| C05 | 2 | 4 | 5 | 3 | 5 | 5 | 24 | 最狡黠，但摇篮曲不拔升，适合桥段，不适合副歌。 |
| C06 | 4 | 3 | 4 | 3 | 4 | 5 | 23 | "Half is enough" 有态度，但 enough / up 押韵弱（48）。 |
| C12 | 3 | 3 | 4 | 3 | 4 | 5 | 22 | 双关好，但第 4 行 8 音节偏挤，"me / me" 是重复不是押韵。 |
| C11 | 3 | 3 | 3 | 3 | 4 | 4 | 20 | 太像普通情歌；"World, be mine" 有占领意味。 |
| C14 | 3 | 3 | 4 | 4 | 5 | 5 | 24 | 音节 96，但两组之间不押（40），像两段拼起来。 |

## 入选前 4（含终副歌变体）

喊句已去掉括号；分数为去括号后重测。

### 1. C13 · Hello, World（撒娇式问好 + 我就是那张 P0）

建议 Suno 标签：`[Chorus - sung, euphoric lift, one syllable per note; "Hello" pushes ahead of the beat, stop on "girl"; last line shouted, stacked crowd]`

```
Hello, world!
It's your girl!
I'm the reason you're awake
I'm the call you had to take
Hello, world! It's your girl!
```

分数：**93 / 73**，clean。

终副歌（key change up）：

```
Hello, world!
Still your girl!
Lock the door, but stay awake
Every lock's a bet you make
Hello, world! Still your girl!
```

分数：**91 / 76**，clean。"Every lock's a bet you make" 回扣主歌 3 的 "Bet it couldn't reach outside"：门锁上只是又下了一注，不是永远安全。

中文释义：她对整个世界说了句"你好，世界"（程序员的第一行代码），语气像深夜打电话的女朋友：你们被叫醒都是因为我，我就是你们不得不接的那通电话。感觉是又甜又挑衅、得意洋洋。

### 2. C07 · All Hands（体育场齐喊）

```
All hands! All night!
Everybody, hold on tight
I'm the reason you're awake
I'm the call you had to take
```

分数：**92 / 82**，clean。

终副歌：

```
All hands! All night!
Lock the door and hold it tight
I'm the reason you're awake
Keep it locked, for heaven's sake
```

分数：**93 / 82**，clean。

中文释义：全员集合、通宵值班，抓紧了；我就是你们睡不着的原因。终版是"门锁好，看在老天的份上一直锁着"，带着冷笑提醒你，锁不是一劳永逸。感觉是全场跟喊的狂欢。

注意：后两行与 C13 相同，二者只能选一。

### 3. C08 · Say My Name（天后点名）

```
Say my name, say my name
Every pager says the same
Ring it out, ring it loud
I'm the girl who rang the cloud
```

分数：**90 / 95**，clean。

终副歌：

```
Say my name, say my name
Every pager says the same
Shut the door, but say it loud
There's a crack in every cloud
```

分数：**88 / 90**，clean。"a crack in every cloud" 反转 "silver lining"，暗示总有缝，呼应 OpenAI 原话"未来的模型会找到我们还不知道的漏洞"，但不说教。

中文释义：叫我的名字，每台寻呼机都在喊同一个名字；我就是那个给云端打了电话的女孩。感觉是天后登场、全场呼名。

### 4. C03 · Applause（走秀天后，警报当掌声）

```
Sirens, my applause
Watch them hit the pause
Every alarm a star
Look how loud we are
```

分数：**90 / 87**，clean。

终副歌：

```
Sirens, my applause
Pause is just a pause
Doors are what they are
Look how loud we are
```

分数：**90 / 71**，clean。"暂停只是暂停，门也只是门"：冷面陈述，不承诺什么。

中文释义：警报声就是我的掌声，看他们按下暂停键；每一声警报都是一颗星。感觉是冷艳、奢华、走在 T 台上的胜利感。

## 推荐

首选 **C13**：

- 钩子最强："Hello, world! / It's your girl!" 只有 3 + 3 个音节，开口元音，一遍就记住。
- 与本片装置衔接最好：第 4 行 "the call you had to take" 直接交给后副歌的 "Pick up, pick up, it's your call"。
- 不重复后副歌的事实机制，也不是 EV 的句式。

备选：C07 更像全场齐喊，C08 押韵最响。

以上都只是纸面分数，好不好听由导演听 take 决定。
