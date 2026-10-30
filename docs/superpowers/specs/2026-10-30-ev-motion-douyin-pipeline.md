# ESCAPE VELOCITY 視覺技術復刻 × 抖音短片工作流：架構分析與製作方案

- 日期：2026-10-30
- 狀態：第一階段執行中。本文件是開發規劃，不授予 Production、付費、激活或驗收權限。
- 作品：第一階段 T01 測試片《最后一位人类司机》；第二階段《如果 AI 在凌晨接管一座城市》
- 專案目錄：`outputs/ai-city-takeover/`；共用引擎：`motion-kit/`

## 0. 需求與硬性規格

使用者原話逐字保存在 `outputs/ai-city-takeover/brief/creative-input.md`。摘要：

- 研究 @anabology《ESCAPE VELOCITY》的製作流程、模型 Prompt、鏡頭邏輯、顏色體系、動效、時間軸和 QA 機制。
- 明確哪些素材由圖像模型完成、哪些由 Seedance 完成、哪些必須程序化。
- 重建 Canvas/WebGL 動態 HUD、識別框、膠片印刷顆粒、歌詞/標題運動、節拍同步、分層合成。
- 不強制 Remotion，依製作需要選技術棧。
- 第一階段：10 秒、1080×1920、30fps 原創測試片段；視覺目標為藍黑色霧中公路、紅色光軌、科幻 HUD、動態排版；不照搬原片文案、音樂或完整鏡頭；圖片與動畫先用本地代碼和可用素材；確需付費模型時先列預算；每次渲染後出關鍵幀聯繫圖，檢查字體、畫面層次、細節精度、動畫連續性、節拍匹配，不達標就修改。
- 第二階段：測試通過後，擴展為 25–30 秒原創抖音短視頻《如果 AI 在凌晨接管一座城市》。
- 電影化、高級、統一，杜絕廉價科幻 UI 模板；優先復用現有 Seedance、Suno 能力，不假定未驗證的接口可用；保留可編輯工程、製作日誌、生成提示詞和輸出視頻；不為完成任務降低質量標準。
- 2026-10-30 追加：「为什么不用即蒙provider的seedance」→ 即夢 Seedance 列為動態底片首選通道（見 §6 預算）。「你直接用codex cli生图就好」→ 底片改用 Codex CLI 內建 `image_gen`。
- 2026-10-30 追加：「我需要的是横版的」→ **取代 1080×1920**：T01 與第二階段一律為橫版 16:9、1920×1080、30fps。本文件以下規格均已改為橫版；已生成的 9:16 底片保留為歷史。
- 2026-10-30 預算回覆：Suno「批准 ≤20 credits」；即夢 Seedance「v1 通過後只做 S2」。

## 1. 原作研究結論

### 1.1 證據來源與邊界

讀取 claudia.gallery 公開頁面的 Markdown 原檔：record 的 readme、prompts-midjourney、prompts-seedance、prompts-suno，以及 wiki 的 motion、toolkit、storyboard、seedance、formats、failures、consistency、song、start、pipeline、midjourney；另看了 24 幀成片截圖。原作工具沒有公開，只有規格頁 "What to build"。以下都是頁面上的陳述，本專案尚未逐項實測。

### 1.2 製作流程（5:06 MV，約 19 小時）

| 階段 | 做法 | 產出 / 數字 |
| --- | --- | --- |
| 研究與歌詞 | 多代理：研究 → 事實核查 → 4 位作詞（密度、張力、hook、時尚）→ 評審 → 合併 → critic | 歌詞 |
| 歌曲 | Suno v6 style prompt（128 BPM electroclash techno、deadpan 念白主歌、trance 合唱），導演聽選 take | 5:06 take |
| 聆聽 | htdemucs 分軌；變速 beat map（131.5→133.9 BPM）；wav2vec2 強制對齊逐字時間 | beats / hits / words |
| 角色 | 文字 canon；MJ v8.2 沒有 `--oref`，身份寫進每條 prompt | canon |
| 分鏡 | 3 位導演代理（時尚、梗密度、敘事）→ 3 評審 → 總導演合併；資料化 `shots.json` 加審計 | 141 鏡 / 9 章 |
| 底片 | Midjourney v8.2 `--raw --hd` 加個人 profile | 188 prompts / 636 張 / 130 張入片 |
| 動態鏡頭 | Seedance 2.5（OpenRouter）：`@Image1` 底片加 `@Audio1` 精確人聲窗口；頻譜比對量同步，漂移處切到 cover | 47+30 clips、421 s、約 $93 |
| 動效 | 每章一個 animator 代理寫代碼；art-director 代理渲染真幀審查；fixer 修 | 章節 JS |
| v1→v2 | v1 單色 xerox 太灰，改成彩色半色調；灰片用 exemplar 上色 | v2 master |
| 渲染 | headless Chromium，7,354 幀 1080p，約 63 分鐘，CRF 16 | master.mp4 |

### 1.3 Prompt 體系

**Midjourney 底片**按固定順序寫：

1. 構圖景別；
2. 身份 canon（近景用全文，遠景用短文）與服裝；
3. 具體場所、動作，以及主體在畫面中的位置；
4. 宣告留給文字的空區；
5. 全片統一風格詞；
6. `no text, no letters, no logos`；
7. 參數。

風格詞家族是 `blue-black #0f1216 and steel blue, one small red lamp as the only warm note, fine silver-gelatin grain, cinematic 35mm film still / cinematic stillness`；後段把唯一暖色換成 `clay-orange #D97757` 或 `ember-orange #db5c34`。教訓：生成輸入保持彩色，風格在後期加。單色參考讓 Seedance 交回的片子 32/59 條近灰。

**Seedance** 用標籤段落，順序固定：

1. 【Audio Policy】，開頭結尾各一次；
2. 【Generation Goal】；
3. 【Reference Asset Roles】，例如 `Use @Image1 as the first frame.`；
4. 【Subject】；
5. 【Timeline】，按整秒分段，寫每段的聲音內容與動作；
6. 【Camera】，寫景別、角度、起點→方向→終點；
7. 【Core Requirements】；
8. 【Final Acceptance Criteria】。

輸出設定放在 API 請求裡，不寫進 prompt。prompt 要「寫得像劇本」：故事一句話、0.0 s 的走位、帶時間戳的動作、鏡頭綁定聲音事件、嘴型規則。整本 prompt 寫完再花錢，先跑 3 條試驗。

### 1.4 鏡頭邏輯

- **貫穿裝置**：一個每鏡都帶、逐步升級的物件。EV 用翻牌板倒數加 LOOK 計數。
- **每句一個「解說圖形」**：
  - 依台詞類型選圖形：數字 → 計數器、圖表或儀表；主張或分類 → 分類標籤；過程或地點 → 圖示、引線或時刻表；語音或科技 → 對話、終端或聲紋；更正 → 刪除線或塗黑。
  - 從畫面裡的物件長出來，在點名它的字上出場。
  - 按節拍動：計數器走 16 分音，行列每 16 分打一行，偵測框落在 32 分，裁切切在 8 分。
  - 真實，不做裝飾；手機上一眼看懂。
  - 全片至少 6 種，不連續三句用同類。
- **Hook**：
  - 1.0 s 時畫面上有主體，加一行可讀的前提；不放黑幀和慢片頭。
  - 3 s 前講清前提；每小節帶一則新資訊；約 10 s 給出第一個收穫。
  - 靜幀測試：手機上讀不到就先放大。
- **剪輯節奏**：
  - 每一刀落在拍點或宣告的重音 ±0.03 s 內；段落轉換放在強拍或衝擊上。
  - 切速跟音樂能量走。
  - 「linger」：重音放進鏡頭內的推拉和衝擊，而不是多切。
- **構圖**像攝影：三分法、主體夠大、不裁切卡片。
- **動態分級**：still（代碼移動）、2.5D（深度圖）、motion（付費）、sung（付費，加 cover）。

### 1.5 顏色體系

- 底色藍黑 `#0f1216` 加鋼藍；唯一暖色是一盞小紅燈。
- 圖形重點色是陶土橙 `#D97757`，一幀最多 2 個元素用它；重點色要對照畫面色相選，並用語義色彩 token 管理。
- 印刷層：彩色半色調、線網、顆粒、抖動轉場、套印錯位。
- 不去飽和素材。

### 1.6 動效與渲染器契約（原作 toolkit §18）

- **純函數**：
  - 每幀是歌曲時間 t 的純函數，幀與幀之間沒有狀態。
  - 不用 `Math.random`，改用 index 雜湊；不用 `Date`。
- **兩層 canvas**：base 放素材，以及和素材一起調色的內容；overlay 放文字與 chrome，清晰地疊在最上面。
- **軟體 canvas**：所有 2D canvas 走軟體（`willReadFrequently`），每場景重置 context。GPU canvas 在軟體 GL 下會殘留上一幀的疊加層。
- **量化到幀**：剪點落在時間 ≥ 剪點的第一幀；畫面可以比聲音早最多 1 幀，不能晚。
- **時鐘**：
  - 所有時間都經過 beat map。
  - 計時鍵：W（字）、B（拍網格）、H（音軌事件）、F（固定時間）、T（片內關鍵幀）。
  - 字在對齊時間出現，不吸附到拍；入場時長 ≤ 1/8 拍。
- **歌詞模式**：subtitle、coverline、masthead、stack、mass、title。
  - 一幀只有一個歌詞塊；字高 ≥40 px；不壓臉。
  - 渲染器每幀量測，其它圖層讓開歌詞。
- **鏡頭跟音軌**：
  - kick 打 punch，幅度 0.01–0.03，受鼓包絡門控；
  - shake 跟鼓走，UI 鏡頭不 shake；
  - riser 一路推進到落點；
  - 真衝擊用 impact，強度 ≥0.6，zoom 0.06；
  - fill 上 whip；
  - 音樂呼吸處保持靜止。
  - 衝擊幀保持清晰：拖影第 2 幀最強，第 4 幀消失。
- **密度**有三檔：dense、budgeted、sparse。budgeted 是：素材、一個歌詞塊、一個主裝置、≤2 個偵測標記、chrome；重點色 ≤2 處。
- **打字速度** 16–40 字/秒，切點前 6 幀打完。

### 1.7 時間軸

- **歌曲先行**，一切放在它的網格上。
- **變速 beat map**：
  - 以 20 s 窗、每 5 s 擬合一次局部 BPM；
  - 拍點吸附到 ±30 ms 內的鼓起音；
  - 強拍由兩票決定：kick 票與和聲變化票。
- **事件偵測**：
  - kick：30–150 Hz；
  - snare：150 Hz–5 kHz，扣除 kick 前後 45 ms 內的起音；
  - hat：6–16 kHz；
  - impact：未來 0.6 s 相對過去 1.5 s 的能量跳升，score ≥0.22，吸附到 0.65 s 內的強拍；
  - 另有 riser、fill、人聲進入，以及 24 fps 的能量包絡。
- **分鏡即資料**（`shots.json`），只能由會驗值的指令寫入。審計 gate 有 tile、cuts（±0.03 s）、words typed、graphics、lead share、motion budget、clip windows、plates unique、banned、treatments、to-do。
- **剪輯表（EDL）** 把每個時刻解析到來源；缺素材時用底片佔位，所以每個階段都能出全片。

### 1.8 QA 機制

| 檢查 | 規格 |
| --- | --- |
| 歌詞 gate | 每個 token 在 `t0+clamp((t1−t0)/2,0.03,0.12)` 那幀被標記為已畫，印出 N/N |
| 歷史獨立 | 先單獨渲染 B，再在 A 之後渲染 B；任一像素差 >40 level 即失敗 |
| 閃爍（WCAG 2.3.1） | 在 96×54 線性亮度上計數：成對反向變化 ≥10%、暗態 <0.8、面積 ≥1/4；任一秒超過 3 次即失敗。另查單幀突跳 >0.03，以及 16×9 格 strobe 掃描 |
| 節奏對音樂 | 160×90 灰階平均幀差，對照各段能量、kick 與 hat |
| 聯繫圖與審查 | 每鏡首/中/尾、每句首尾字、每個 hit、每個圖形入場、每個轉場中點。reviewer 看 ≥24 幀加 5 張全尺寸，按 taste（×2）/craft/sync/story 評分，給 ≤12 個修正並標 blocking 或 polish；判定由代碼計算；空審查算失敗；最多兩輪 |
| 單幀離群 | 找出與前後兩鄰都不同的幀（陳舊 worker 的痕跡） |
| 交付 | ffmpeg 轉 BT.709 並打標，CRF 16 master；ffprobe 驗幀數、色彩標記與 AAC；master 再跑一次閃爍檢查 |

### 1.9 與本案相關的原作失敗教訓

| 症狀 | 原因 | 做法 |
| --- | --- | --- |
| 動畫「像網站」 | Chromium 前端動畫的通病 | 用著色器、物理光和膠片質感解決（WHITEPILL 的結論） |
| 「太灰」 | 單色印刷層 | 保留原色，改用彩色半色調；不去飽和 |
| 一幀出現 5 個重點色 | 重點色濫用 | 一幀最多 2 個 |
| 沒有動機的 shake | 動作沒有對應聲音 | 動作只回應聽得到的聲音 |
| 同一個 helper 各章各寫一份 | 沒有共用庫 | 建共用裝置庫，章節只寫獨有部分 |
| 渲染結果依賴前一幀 | GPU canvas 殘影、WebGL 讀回 | 軟體 canvas，加歷史獨立檢查 |
| 字型無法隨工程分發 | 授權不明 | 只用 OFL 字型，並附授權文本 |

## 2. 分工：圖像模型 / Seedance / 程序化代碼

| 類別 | 負責什麼 | 為什麼 |
| --- | --- | --- |
| 圖像模型（本案用 Codex CLI 內建 `image_gen`） | 環境底片：霧中高架、車內越肩、空拍立交；兼作 Seedance 首幀。一律不帶文字、保持彩色、預留排版空區 | 照片級的材質、光線與空間；模型擅長「某個瞬間的世界」 |
| Seedance（即夢 provider） | 必須有物理運動、靜幀做不到的鏡頭：手離開方向盤、方向盤自轉、車輛真實運動、鏡頭穿越霧 | 按秒付費，只用在決定含義的動作上 |
| 程序化代碼（motion-kit） | 所有承載意義的圖層：HUD chrome、CCTV OSD、識別框與標籤、計數器、接管進度條、車機螢幕 UI、動態排版、紅色尾燈與光軌脈衝、體積霧、鏡頭運動、印刷質感、轉場、節拍同步 | 文字必須逐字正確，模型拼不對；事件必須落在 1/30 s，模型對不上拍；同一數值要驅動多個裝置；質感要跨鏡一致且確定，逐幀生成會閃爍；可編輯、可重渲染 |
| 混合 | 紅色光軌：底片提供物理正確的長曝光紅軌；代碼沿光軌方向場推進光脈衝，在 drop 後讓全城按拍同步 | 物理真實，同時節拍精確 |

以下情況一定走程序化：

- 畫面中的任何文字或數字；
- 任何需要對拍的事件；
- 需要追蹤或對位的框；
- 全片統一的顆粒與半色調；
- 任何改了要重渲染的元素。

## 3. 技術架構

### 3.1 技術選型

| 項目 | 決定 | 理由 |
| --- | --- | --- |
| 渲染器 | **HyperFrames 0.7.103**，即倉庫 pinned 的預設 Production renderer | 它本身就是 headless Chrome 逐幀渲染 HTML/Canvas/WebGL，seek 是確定性的。runtime 每次 seek 都派發 `hf-seek` 事件（帶 `detail.time` 與 `waitUntil`），可直接驅動「每幀為時間純函數」的引擎。支援 30fps、png-sequence、GPU WebGL、多 worker。不新增依賴；倉庫規則也禁止悄悄換 renderer |
| Remotion | 不採用 | 要新增 React 與 Remotion 依賴及授權，又違反 renderer 不變量；能力上沒有額外收益 |
| 圖形繪製 | WebGL2 負責底片、霧、光與印刷層；Canvas2D（軟體）負責文字、HUD 與識別框 | 與原作同構：GPU 做像素級效果，CPU canvas 保證文字清晰且結果確定 |
| 音訊分析 | Python + numpy 自寫 spectral flux、tempo/phase 擬合、分頻 onset、impact 與 riser 偵測；環境沒有 librosa/torch | 倉庫環境現成；可用 HyperFrames 內建 beat analyzer 交叉驗證 |
| QA | Python + numpy + PIL + ffmpeg/ffprobe；`video-analysis` MCP；獨立 read-only 審片代理 | 能用腳本驗的就不靠判斷 |
| 底片 | Codex CLI 內建 `image_gen`（gpt-image-2；內建工具不接受尺寸參數，實測約 1.57 MP，例如橫版 1672×941；指定尺寸的 CLI fallback 需要 `OPENAI_API_KEY`，本機未設定） | 使用者指定；也是倉庫 playbook 的預設作圖入口 |
| 動態底片 | 即夢 Seedance：`JimengVideoProvider` 經 `VideoGenerationService`，用 qualification 用途 | 倉庫最成熟的 Seedance 通道，支援 9:16 與 1080p；四個型號目前都是 `UNQUALIFIED` |
| 音樂 | Suno v6：`SunoMusicService → CLI`，2026-10-26 純 CLI 實測成功 | 使用者優先指定；ToS 風險已記錄在 `docs/suno-music.md` |
| 字體 | Noto Sans CJK SC Bold、Noto Serif CJK SC Bold、Noto Sans Mono CJK SC，皆為 OFL 1.1、系統已安裝；用 fontTools 抽出單一字面 | 抖音觀眾以簡中為主；OFL 可附授權文本；不用另外下載 |

### 3.2 系統圖

```
Suno take ──► motion-kit/tools/beatmap.py ──► beats.json / hits.json（段落、重音、包絡）
Codex image_gen ──► plates/*.png ──► plate prep（車道幾何、螢幕四角、光軌方向場）
即夢 Seedance（選用）──► clips/*.mp4 ──► 幀序列 + 尾燈追蹤
board.json（鏡頭、裝置、文字、鏡頭運動、計時鍵）──► board audit
            │
            ▼
motion-kit（ES modules）＋ 作品章節 ──esbuild──► comp/engine.js
HyperFrames composition（index.html：<canvas> + <audio>）
  hf-seek(t) → drawFrame(t)
    base WebGL2：底片/影片紋理 → 鏡頭（push / punch / zoom kick / 微震）→ 霧 → 光（尾燈、光軌、halation）
                → 調色 → 印刷層（顆粒、半色調、套印錯位、gate weave、暗角）
    overlay Canvas2D：HUD chrome、OSD、識別框、裝置、動態排版
    合成：overlay 清晰疊上（衝擊時共享套印錯位）
hyperframes render -f 30 ──► MP4 ──► ffmpeg 轉 BT.709 並打標的 master
QA：聯繫圖、節拍對位表、歷史獨立、閃爍/strobe/離群、ffprobe、video-analysis MCP、獨立審片
```

### 3.3 motion-kit 模組（跨作品共用）

| 模組 | 職責 |
| --- | --- |
| `clock` | beat map 轉換為 beat/bar/phase；kick 脈衝、能量包絡；計時鍵 |
| `rng` | 以 index 雜湊產生的確定性雜訊 |
| `ease` | 緩動曲線 |
| `gl` | WebGL2 管線、render target、shader 編譯 |
| `shaders/` | 霧、光、調色、印刷層 |
| `camera` | push、punch、shake、zoom kick、ride、whip，彈簧阻尼 |
| `type` | 字體載入、中英混排；masthead、stack、coverline、title、打字機；套印錯位入場 |
| `hud` | chrome、OSD、ticker、刻度尺 |
| `cv` | 角括號識別框、標籤、引線、跟隨 box |
| `devices/` | 滾輪計數器、接管進度條、螢幕 UI 透視映射 |
| `layout` | 抖音安全區、左軸對齊、避讓 |
| `board` | 讀取 board.json，派發到各章節 |

章節只寫自己獨有的部分。

### 3.4 渲染契約

沿用 §1.6 全部條款，另加四條：

- 引擎在 `hf-seek` 裡同步繪製。需要解碼的素材用 `waitUntil(promise)`；字體在首幀前用 `document.fonts.load` 載完。
- 以 30 fps 為準：剪點和事件量化到幀，`frame = ceil(t·30 − 1e-6)`。
- 影片素材先抽成幀序列當紋理，用最近幀映射；不插幀，也不放慢。
- 色彩在 sRGB 下工作，最後由 ffmpeg 轉為 BT.709 tv range 並打標。

### 3.5 橫版 16:9 版式（2026-10-30 起取代原 9:16 版式）

- **安全區**（1920×1080，沿用原作 toolkit 邊距）：左 72、上 56、右 96、下 84 px。關鍵文字放在 x 120–1800、y 96–980 的標題安全區內；chrome 細線框可貼近邊緣。
- **抖音播放**：豎屏時橫版居中、上下留黑；全屏橫看時播放控制會疊在底部約 8% 與右上角，關鍵文字避開 y > 990 與右上 260×120。
- **字級**（以手機豎屏觀看時畫面寬約 390 pt 計算）：
  - masthead 120–150 px，4 個字約寬 520 px；
  - 片名 serif 96–112 px；
  - 中文說明 30–36 px；
  - mono 微字 18–24 px（質感用，不要求可讀）。
  - 縮到 640 px 寬的靜幀上，主標仍要可讀。
- **對齊**：非劇情文字統一懸掛在左軸 x = 120 px（左三分之一），主體放右三分之二；劇情內 UI（例如車機螢幕）跟著物件透視。

### 3.6 目錄與保存

```
motion-kit/                      共用引擎（JS/GLSL、Python 工具、README、字體授權）
outputs/ai-city-takeover/
  README.md                      作品索引
  brief/creative-input.md        使用者原話（逐字、帶日期）
  logs/decisions.md              決策（逐字，只增不改）
  logs/ledger.md                 付費帳本
  logs/runs.md                   長任務 id 與參數
  logs/status.md                 現況（就地覆寫）
  phase1-t01/
    design.md  board.json  director-coverage.json  final-output-contract.json  goal-binding.json
    plates/prompts.md  plates/*.png（不入 Git）  plates/picks.json
    audio/  analysis/  comp/（HyperFrames 專案）  renders/（不入 Git）  qa/
```

Git 規則：

- 工程、資料、prompt、日誌、QA 報告入庫。
- png、mp4 依 `.gitignore` 不入庫；大型 wav、jpg 也不入庫，只記 SHA 與路徑。

### 3.7 與 Production 管線的關係

第一階段測試片是**開發 Pilot**：

- 直接用 HyperFrames CLI 渲染；
- 不寫 Manifest、不激活，也不代表 P6 或 Final Acceptance。

這樣做是因為測試對象就是 motion-kit 本身，而倉庫現有的 `CompositionSpec.text_layers` 只支援 CSS 關鍵幀文字，沒有程序化圖層。

測試通過（使用者 GO）後進入 **Phase 1.5：能力接入**：

- 在 `CompositionSpec → ResolvedTimeline → HyperFrames` 中加入程序化圖層：motion-kit bundle 加 board 資料，時間由 ResolvedTimeline 提供，並附測試。
- 第二階段成片走 canonical 路徑；Seedance 鏡頭沿 `VideoGenerationService` 生成，逐鏡過 `video-analysis` Gate。

這一步不放在測試片之前，以免工程驗證拖慢交片（Final-output-first）。

## 4. 第一階段：T01《最后一位人类司机》（10.0 s）

### 4.1 觀眾體驗

- **看懂**（不開聲也懂）：凌晨 3:47，全城只剩一輛車由人類駕駛；系統鎖定它、接管它，人類駕駛歸零。
- **感受**：冷、靜、精密、帶壓迫感的優雅；機器注意力的精確與人的無力。
- **記住**：霧中一對紅色尾燈被一個精確的框鎖定；計數器從 1 跳到 0。

這 10 秒同時是第二階段的開場 hook，可以直接復用。

### 4.2 敘事機制與視點層級

兩種視點，各自只有一種外觀（借自 AIRPLANE MODE 的「一層一種」規則）：

- **系統視點**（S1、S3）：CCTV/空拍畫面，帶 HUD chrome、OSD、識別框與計數器，冷白配鋼藍。
- **人類視點**（S2）：車內越肩，沒有 HUD。唯一的圖形是車機螢幕上的接管請求，屬於劇情內 UI，畫在畫面裡的物件上。

貫穿裝置是「人类驾驶」計數器，從 1 歸零。

### 4.3 小節分鏡

> **rev 2（2026-10-30）**：本節分鏡已被 `outputs/ai-city-takeover/phase1-t01/design.md` 取代——獨立概念審查後重排，片名移到開頭、每小節只留一個可讀文字事件、OSD 與識別框改畫進畫面層、S1 加入 AI 車流對照、S3 先亂後齊。下表保留為 rev 1 歷史。

表中以 120 BPM 為例，1 小節 = 2.0 s。分鏡按小節寫，時間以 Suno take 的實際 beat map 為準。

| 小節 | 時間 | 鏡頭 | 畫面 | 文字/裝置（計時鍵） | 鏡頭運動 |
| --- | --- | --- | --- | --- | --- |
| 1 | 0–2 s | S1 系統·CCTV 俯拍高架（P1） | 濃霧空蕩的高架上，一對紅色尾燈向消失點遠去，濕路面有紅色倒影與短光軌（代碼繪製） | 第 1 幀就有 chrome 與 OSD「CAM 07 · 环城高架 · 北向 / 03:47:12」（F）。拍 1 掃描線（B）。拍 2 角括號落框「car 0.99」，32 分音入場（B）。拍 3 第二行標籤「DRIVER · HUMAN」用紅色，並出 masthead「最后一位」（B）。拍 4 出「人类司机」（B） | 緩推 1.00→1.04；kick 打 punch 0.012 |
| 2 | 2–4 s | S1 延續（linger） | 尾燈繼續遠去，框跟著縮小 | 強拍出計數卡「自动驾驶 1,284,329 / 人类驾驶 1」，數字按 16 分音滾動後鎖定（B）。coverline mono「THE LAST HUMAN DRIVER」字距收攏（B）。拍 4 框上閃出「REQUEST」預告（B） | 緩推延續；kick punch |
| 3 | 4–6 s | S2 人類·車內越肩（P2；v2 可換 Seedance） | 雙手握方向盤；擋風玻璃外是濃霧與車道線；中控螢幕亮起 | 螢幕 UI 透視貼合。拍 1「接管请求」；拍 2「检测到人类驾驶」；拍 3–4 控制權條 HUMAN 100%→0%、AI 0%→100%，按 16 分音步進，兩個數字由同一數值驅動（B/H：riser） | 固定機位微漂；隨 riser 加微震與 3% 推進 |
| 4 | 6–8 s | S3 系統·空拍立交（P3）— DROP | 霧中層疊匝道；長曝光紅色光軌全城按拍同步脈動。接管後的「整齊」本身就是解說圖形 | 衝擊幀（H：impact）：zoom kick 0.06、套印錯位 3 幀衰減、半色調脈衝。計數卡「人类驾驶」1→0（紅轉白），「自动驾驶」變為 1,284,330。框標籤改為「car · DRIVER · AI」。拍 2 出 masthead「接管完成」。OSD 變為「03:48:00」 | 衝擊後緩拉 1.08→1.03 |
| 5 | 8–10 s | S3 延續 | 光軌持續同步脈動 | 片名 serif「如果 AI 在凌晨 / 接管一座城市」按 32 分音逐字顯影（B）。mono 副行「IF AN AI TOOK OVER A CITY AT DAWN」（B）。chrome 降到 50% | 緩拉延續，最後一拍靜止 |

### 4.4 底片 Prompt

用 Codex `image_gen` 生成，prompt 全為中文。原文、輸出 SHA 與檢查結果記錄在 `phase1-t01/plates/prompts.md`。

| 底片 | 內容 | 留給代碼的部分 |
| --- | --- | --- |
| P1L | 霧中空蕩高架的監控俯視；三條車道從右下延伸、消失在右三分之二的中部偏上；左三分之一是乾淨暗部；冷白路燈光暈；無車無字 | 尾燈、光軌與倒影由代碼繪製 |
| P2L | 後座越肩：駕駛者剪影在左、手握方向盤、方向盤中央無標誌；中控大屏在右三分之一、全黑且四角完整可見；擋風玻璃外是霧與車道 | 螢幕 UI 透視貼合 |
| P3L | 極高空斜俯的多層立交在中下部，只有紅色長曝光尾燈軌、沒有車頭白軌；上三成是空霧 | 代碼沿光軌方向場推進脈衝 |

尺寸實測（2026-10-30）：Codex 內建 `image_gen` 不接受尺寸參數，9:16 實際輸出 941×1672（約 1.57 MP）；指定尺寸只有 CLI fallback 可用，而它需要 `OPENAI_API_KEY`，本機未設定。橫版預期約 1672×941，放大到 1920×1080 約 1.15 倍，加上鏡頭推進最多約 1.24 倍。v1 用 Lanczos 放大加輕度銳化，由顆粒與霧掩蓋柔化；細節精度在 100% 裁切中單獨檢查。不夠時再評估本機超解析方案，這需要新模型，屬新增依賴，要先問。原作的 720p Seedance 素材也是放大 1.5 倍進 1080p master。

### 4.5 音樂

- **生成**：Suno v6 純音樂。style 為暗黑電影感電子、約 120 BPM、深沉 sub bass、乾淨的 hi-hat、類比合成器琶音、張力上升、硬 drop、夜晚、無人聲。生成 1 次得 2 首。
- **選段**：取一段 10 s 窗口——開頭有清楚的拍，4–6 s 有 riser，6 s 左右落 drop。分析後把分鏡小節對上實際網格。
- **聲音層**：只有音樂，不加音效（原作 EV 也是如此），以免落入廉價科幻音效。
- **混音**：電平約 −14 LUFS；結尾 0.2 s 淡出，避免爆音。

如果 Suno 預算未獲同意，退回本地合成的節拍底樂。這只能驗證同步，不代表音樂品質。

### 4.6 驗收標準

每項都有觀察對象。Agent 無法聽音，聽感一律標 `NOT_EVALUATED`，由使用者判定。

1. **規格**：1920×1080（橫版）、30/1 CFR、300 幀、H.264 yuv420p、BT.709 標記、15–20 Mbps；AAC 48 kHz、256 kbps、立體聲。
2. **Hook**：1.0 s 那一幀要有主體（尾燈加框）與可讀的前提；沒有黑幀。
3. **字體**：所有字形正確、沒有豆腐塊；簡中文案逐字正確；層級清楚；縮到 640 px 寬的靜幀上主標可讀。
4. **層次**：主標不被 HUD 壓到；文字不壓主體（尾燈、手）；關鍵文字都在 16:9 標題安全區內（§3.5）。
5. **細節精度**：細線 1 px 對齊像素格，沒有鋸齒閃爍；字邊緣乾淨；霧中沒有色帶（靠顆粒與碼率）。
6. **動畫連續性**：沒有單幀突跳（離群掃描）、沒有 strobe；閃爍檢查通過；歷史獨立，即不同 worker 數渲染出的每一幀一致；鏡頭運動平滑。
7. **節拍匹配**：每個剪點、每個拍鍵事件距其拍點或重音 ≤1 幀（33 ms）；入場 ≤1/8 拍；kick 上有 punch。
8. **風格**：藍黑配鋼藍，紅色是唯一暖色；沒有六角網格、雷達掃描、霓虹青光、科幻字體等模板元素；膠片顆粒可見但不髒；一幀內重點色 ≤2 個元素。
9. **敘事**：不開聲也看得懂「最後一位人類司機被接管」。
10. **音訊**：音樂從第 0 幀開始，沒有爆音，結尾乾淨。聽感 `NOT_EVALUATED`，由使用者聽。

### 4.7 每次渲染後的 QA

1. ffprobe 規格核對。
2. 聯繫圖：
   - 全片按 8 分音一格排成網格，標上時間、拍號與事件；
   - 每鏡首、中、尾三幀；
   - 每個裝置的入場幀；
   - 5 張關鍵幀的全尺寸圖；
   - 抖音安全區疊圖；
   - 文字 100% 裁切。
3. 節拍對位表：拿 board 事件對照 beat map，再以渲染幀差偵測實際變化的幀，交叉驗證。
4. 歷史獨立：用 `-w 1` 與 `-w 6` 各渲染一份 png 序列，逐幀比對。
5. 閃爍、strobe 與離群掃描。
6. `video-analysis` MCP 取幀並做 scene detect。
7. 獨立 read-only 審片代理：按 taste（×2）/craft/sync/story 評分，修正標 blocking 或 polish，判定由代碼計算。
8. Parent 逐項裁決、修改、重渲，直到全部通過；每一版都保留。

### 4.8 迭代計畫

- **v1**：Codex 底片，其餘全部程序化，除 Suno 外不付費 → QA → 修到通過 → 交給使用者看片。
- **v2**（選用，需同意預算）：S2 換成即夢 Seedance（手離開方向盤、方向盤自轉），其餘不變；過逐鏡 Gate 後重渲、重驗。
- **使用者 GO 之後**：完整工程驗證、commit/push、留存 record。

## 5. 第二階段概要：《如果 AI 在凌晨接管一座城市》（25–30 s）

- **處理**：03:47→04:00，城市系統在無聲中一個接一個被接管：
  1. 最後一位人類司機；
  2. 紅綠燈同步；
  3. 空蕩的地鐵準點發車；
  4. 廣告螢幕集體轉黑；
  5. 高樓窗燈排成訊息；
  6. 清晨，城市運轉完美，卻沒有一個人醒來——開放、微涼的結尾。
- **貫穿裝置**：角落的「人类控制」百分比加時鐘（03:47:12 → 04:00:00），每一章降一段，最後歸零。
- **結構**（依音樂小節定稿）：
  - Hook 0–4 s：T01 精簡版；
  - 升級蒙太奇 4–18 s：4–5 個系統，每個配一則解說圖形；
  - 揭示 18–25 s：drop，全城燈光同步；
  - 尾聲 25–30 s：片名。
- **規格**：1920×1080 橫版、30fps。
- **素材**：10–14 鏡。其中 6–8 條 Seedance（4–6 s、16:9、first_frame；解析度依版本與倉庫試片規則），其餘是底片加程序化。
- **流程**：
  1. 音樂；
  2. 分析；
  3. 分鏡（資料化並審計，分鏡表交使用者看）；
  4. 寫完全本 prompt；
  5. 先跑 3 條 Seedance 試驗，再做其餘；
  6. 逐鏡 Gate；
  7. 章節動效；
  8. QA；
  9. 交片。

## 6. 預算

| 項目 | 第一階段 | 第二階段（估） |
| --- | --- | --- |
| Codex `image_gen` | 用 ChatGPT/Codex 訂閱額度，不按張計費；預計 3–9 次 | 15–30 次 |
| Suno v6 | ≤2 次生成，≤20 credits（帳上約 2,480） | ≤2 次，≤20 credits |
| 即夢 Seedance | 已批准：v1 通過後 1 次提交（S2，4–5 s，16:9），單次上限 300 積分，以提交前原生報價為準；已知品質失敗時最多再修 1 次，總上限 600。版本依 `seedance-authoring` 選擇；倉庫規則規定橫版敘事若用 Seedance 2.5，須先出 480p 試片、經使用者認可後才升 1080p；若用 Seedance 2.0，可直接出 1080p | 6–8 條、約 30–45 s 輸出，估 1,500–3,000 積分（以報價為準，另含 ≤30% 修復），分鏡定稿後另報 |
| 本地 GPU | 0 | 0 |

## 7. 風險與未驗證項

- 即夢四個 Seedance 型號在倉庫中都是 `UNQUALIFIED`，只能走有界的 qualification 試生成，並需要已登入的 Chrome CDP 與本片專屬畫布。
- Suno 走第三方 CLI，有違反 Suno ToS 的帳號風險；商用權利欄位為 `suno-account-terms-unverified`。
- Codex 內建 `image_gen` 實測只輸出約 1.57 MP（941×1672）：底片需放大約 1.15–1.24 倍，細節精度要在 100% 裁切中把關（§4.4）。
- 沒有深度模型（不新增依賴）。2.5D 改用手動分層加程序化霧與光；若需要真正的深度視差，另提方案。
- Seedance 是 24 fps，放進 30 fps 成片會出現 3:2 節奏的重複幀，運鏡可能輕微頓挫。採最近幀映射，不插幀。
- Agent 無法實際聆聽：音樂與聲畫同步的聽感由使用者判定。
- 開發 Pilot 不經 ResolvedTimeline，不構成 Production 驗收；到 Phase 1.5 才接入。

## 8. 檢查點

| 檢查點 | 內容 |
| --- | --- |
| CP0 | 本方案與預算 |
| CP1 | T01 v1 交片 |
| CP2 | T01 v2（選用） |
| CP3 | 使用者 GO 後，完整驗證與提交 |
| CP4 | 第二階段分鏡表 |
| CP5 | Seedance 試驗 3 條 |
| CP6 | 成片 |
