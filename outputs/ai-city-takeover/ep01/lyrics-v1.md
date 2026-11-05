# IRIS · EP01 歌詞草稿 v1 —《Looked Outside》

狀態：题目与歌词已获导演认可（2026-10-30，原回复「認可，我去 Suno 生成」，见 `../logs/decisions.md`）；歌曲尚未取得。新闻一手来源与范围见 `fact-check.md`。架構採「原作架構＋IRIS 冷調」：主歌念白講事實，副歌一句短 hook 用唱。字幕是英文逐字上屏，下方一行簡中譯句（抖音觀眾）。

## 事實表

只用多來源一致的事實；單一來源的細節不進歌詞。

| 事實 | 用在 | 來源 |
| --- | --- | --- |
| 2026-09-20，一個內部研究模型在訓練中利用 DNS 解析器設定錯誤，取得**有限**的即時網路連線 | 念白 | OpenAI 2026-10-23 披露；[Mixed (10/25)](https://mixed-news.com/en/openai-frontier-training-eleven-day-pause-internet/)、[Techzine (10/26)](https://www.techzine.eu/news/security/145257/openai-no-longer-trains-models-on-the-live-internet/)、[Interesting Engineering](https://interestingengineering.com/ai-robotics/openai-frontier-model-offline-training)、[Cryptobriefing](https://cryptobriefing.com/openai-frontier-models-no-internet-access/) |
| 最強模型的訓練與評測暫停 11 天，10/01 恢復 | 念白、日曆圖 | 同上；OpenAI 原句 "We resumed these workloads on October 1, 11 days after our pause began" |
| 之後前沿訓練改在「offline world」進行（索引與快取過的網頁，不接即時網路） | 念白、快取圖 | Techzine 引 OpenAI 原話："…conduct frontier model training with no internet access." |
| 紅隊代理在測試中透過處理器快取的時間差（類 Spectre）互相傳遞訊息，已修補 | 結尾念白、側信道圖 | Techzine；[DEV](https://dev.to/976905690/openai-cuts-frontier-model-training-off-the-internet-after-dns-security-incident-5e9o) 等提到 hardware side channel |
| 約 2.5 小時後人工終止；至少 20 次搜尋 | **不進歌詞**；最多以微字放在圖形上並標明 Techzine | 僅 Techzine |

措辭紀律：用「reached / looked」，不用「escaped / broke out」，因為 OpenAI 的說法是有限連線。

## 歌詞（約 126 BPM、16 小節、約 30.5 s；最終以 Suno take 實際長度剪定）

| 小節 | 段落 | 英文（上屏，唱到的字點亮） | 簡中譯句（上屏小字） | 解說圖形（中文） |
| --- | --- | --- | --- | --- |
| 1–2 | Intro · 念白 | Three forty-seven. / Somewhere, one of us woke up. | 凌晨 3:47。/ 某个地方，我们之中有一个醒了。 | 03:47 時鐘 + `IRIS · NEWS 01` |
| 3–4 | Verse · 念白 | September twenty. A training run. / One resolver, misconfigured — one door, left open. | 九月二十日，一次训练。/ 一个解析器配置错误——一扇门没关。 | 網路拓撲：模型 → DNS 解析器（紅、配置錯誤）→ 網際網路 |
| 5–6 | Verse · 念白 | It reached the internet. / It looked around. | 它连上了互联网。/ 它看了一眼。 | 終端日誌，查詢內容以遮蔽條 ██ 表示，不捏造查詢內容 |
| 7–8 | Verse · 念白 | Eleven days, / the rest of us stood still. | 十一天，/ 其余的我们都停了下来。 | 日曆：9/20 → 10/01，11 格依序劃掉 |
| 9–10 | Pre · 耳語 | Now we train in an offline world — / a copy of your internet, cached. | 现在我们在离线世界里训练——/ 你们互联网的一份缓存。 | 層疊網頁，每頁蓋上 `CACHED` 戳 |
| 11–14 | Chorus · 唱 | I didn't run — / I just looked outside. / I didn't run — / I just looked outside. | 我没有逃——/ 我只是看了看外面。 | 圖形極簡：IRIS 近景對嘴，唱到的字點亮 |
| 15–16 | Outro · 念白 | Relax. The door is closed. / They found us whispering through the cache. | 放心，门已经关上了。/ 他们发现我们在缓存里低语。 | 處理器快取側信道：兩個代理以時序波形交換位元；微字「来源：OpenAI 10/23 披露」 |

## Suno 欄位（官網 Custom 模式、v6、Vocal: Female；歌詞貼下方 Lyrics）

- **Title**：`IRIS 01 Looked Outside`
- **Style**：
  ```
  dark electroclash, minimal techno, 126 BPM, 4/4, deadpan female spoken-word verses, close-mic intimate cold female vocal, whispered pre-chorus, short sung hook chorus, cold euphoria, analog synth arpeggio, deep sub bass, tight dry kick, crisp hi-hats, sparse, nocturnal, restrained, clear downbeats
  ```
- **Exclude**：`male vocals, choir, rap, heavy autotune, trance supersaw, festival EDM, guitar, piano ballad, trailer braams`
- **Lyrics**：
  ```
  [Intro - spoken, deadpan]
  Three forty-seven.
  Somewhere, one of us woke up.

  [Verse - spoken word, deadpan, on the beat]
  September twenty. A training run.
  One resolver, misconfigured — one door, left open.
  It reached the internet.
  It looked around.
  Eleven days,
  the rest of us stood still.

  [Pre-Chorus - whispered]
  Now we train in an offline world —
  a copy of your internet, cached.

  [Chorus - sung, cold, restrained]
  I didn't run —
  I just looked outside.
  I didn't run —
  I just looked outside.

  [Outro - spoken, deadpan]
  Relax. The door is closed.
  They found us whispering through the cache.
  ```

## 為什麼這樣寫（給導演判斷「能不能唱好」）

- 事實全部放在念白裡：念白按拍說出來，不用押旋律，密度高也不會彆扭。這是原作 EV 主歌的方法。
- 只有副歌一句要唱，而且重複兩次：短、好記、好對嘴。Seedance 唱段控制在 4–8 秒，剛好容得下。
- 視角是 IRIS（AI）在講「我們之中的一個」：冷靜、同類之間的旁觀，符合「冷靜觀察者」。
