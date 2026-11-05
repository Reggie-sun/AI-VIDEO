# motion-kit

程序化動效層：HUD、識別框、膠片印刷質感、動態排版、節拍同步和分層合成，跑在倉庫既有的 HyperFrames renderer 上。方法來自 ESCAPE VELOCITY 的公開製作記錄（claudia.gallery），程式碼為本專案原創。設計與取捨見 `docs/superpowers/specs/2026-10-30-ev-motion-douyin-pipeline.md`。

狀態：開發 Pilot（T01 dev7）的本地技术检查与有界修复已验证，完整声画及用户观感尚未验收；尚未接入 `CompositionSpec → ResolvedTimeline` 的 Production 路徑（見 spec §3.7 的 Phase 1.5）。当前证据见 `outputs/ai-city-takeover/phase1-t01/qa/dev7/`；Harness 精准映射补丁已准备，仅在验证副本试用，尚未写入另一会话拥有的共享policy；不宣称主工作树回归通过。

## 契約

- **每幀是合成時間 t 的純函數**：
  - 不用 `Math.random`，改用 `math.js` 的 hash；不用 `Date`；幀與幀之間沒有狀態。
  - 驗證方式：1 個 worker 與 6 個 worker 渲染的 PNG 序列必須逐像素相同。T01 dev5 為 300/300。
- **時鐘**：
  - 所有音樂時間都經過 beat map（`clock.js`），從不假設單一 BPM。
  - 剪點量化到幀：`frame = ceil(t·fps − 1e-6)`。
  - 事件時間放在專案的 `data/events.json`（以 `[bar, beat, sub]` 表示），引擎與 QA 共用同一份。
- **畫布分工**：
  - **scene**（WebGL2，線性 HDR）：底片經攝影機、霧、光、emissive。
  - **feed**：畫面內訊號（OSD、識別框），在調色前合成，會吃到顆粒、暈光、色差和套印錯位。
  - **overlay**：只放可讀的敘事文字，清晰地疊在最上層。
  - **emit**：光筆畫，以 HDR 加入場景。
  - **ui**：劇情內螢幕，經 homography 貼到底片裡的螢幕上。
- **2D canvas 一律 `willReadFrequently`**（軟體繪製），每幀重置。

## 模組

| 檔案 | 職責 |
| --- | --- |
| `src/runtime.js` | `install(cfg)`：載入字體、底片和資料，接上 HyperFrames 的 `hf-seek` → `renderFrame(t)`；執行 scene、bloom、final 三道 pass |
| `src/clock.js` | `Clock`：`at(bar, beat, sub)`、`beat(t)`、`bar(t)`、`pulse(kind, t)`、`riser(t)`、`env(name, t)` |
| `src/shaders.js` | scene（Catmull-Rom 底片取樣、雙層霧、點光/倒影/車身暗影、光軌線段、螢幕 homography、車內掃光、窗外前進流）、bloom 鏈、final（ACES 調色、halation、加色半色調、顆粒、套印錯位、暗角、抖色；`uInvert` 亮度反轉，保留色相，預設 0） |
| `src/draw2d.js` | 字體載入、混排 `runs`、`slam` 入場、`wipeOut`、`rollNumber`、OSD、`detector`（延遲與抖動）、`chrome`、`carDialog`、`glowPath` |
| `src/gl.js` / `src/math.js` | WebGL2 工具；hash 雜訊、緩動、homography |
| `src/beatcam.js` | 鏡頭跟著音軌動（EV toolkit §18）：`trackZoom` 在宣告的段落內於 kick 上 punch（受鼓的包絡門控）、在宣告的 hit 上 impact，兩者取大不相加，畫面最多早聲音一幀；段落外與段落開始前的事件一律不動。`protectCentre` 放大時讓指定矩形（燒進畫面的平台標識、臉）留在畫面內 |
| `src/mouth.js` | 唱歌的靜圖（2D 動畫的換嘴型法）：依實測字詞時間，在只差嘴部或眼部的幾張底片間逐幀切換。每個字是一串 `[嘴型, 字內位置]`；嘴型比聲音早 `lead_frames` 幀，短於 `min_hold_frames` 的讓給下一個，停頓 ≥ `rest_gap_s` 就閉嘴；眨眼（半閉、閉、閉、半閉）只能落在閉嘴時（`checkBlinks` 檢查） |
| `src/lyrics.js` | 歌詞層：英文逐字點亮＋簡中翻譯；`stack` 為副歌逐詞堆疊版式；`accent: { color, keys: { 行號: 關鍵字 } }` 每句一個關鍵字用強調色（預設不開，行為不變） |
| `src/hud.js` | 全片持續 HUD（EV toolkit 的 G-TITLE-TAG、G-LOOK-COUNTER、G-AUDIO-SPECTRUM、G-TICKER、G-TIMECODE）：`hudRun` 小號等寬標籤列、`meterLevels`／`drawMeter` 由 clock 的頻段包絡與鼓的脈衝算出的小頻譜、`drawTicker` 兩條細線之間的跑馬燈、`timecode`（HH:MM:SS:FF）、`tagCard` 帶紅色邊條的小標籤卡 |
| `src/flap.js` | 翻牌（G-FLAP-BOARD）：`flapText` 以 hash 產生亂碼、逐字翻定，只在 tick 上換字（預設每秒 15 次＝30 fps 隔一幀，不會連兩幀都變，避開 qa.py 的 strobe 掃描）；`from` 讓沒變的字不翻；`flapDone` 翻定時間；`drawFlap` 每字一塊深色牌加中線 |
| `src/kinetic.js` | 大號窄體動態字 `kineticWord`（沒有窄體字面，水平壓縮繪製；落拍放大入場、切條退場）；段落交界的條狀遮罩 `stripRects`／`drawStrips`（剪點前細條掃過、剪點後橫條在數幀內收走，`post: 0` 只留細條） |
| `src/osd-charts.js` | OSD 語言的解釋圖表，只畫形狀、不編數字：`lineChart`（可從某點起轉紅）、`kneeSeries` 示意序列、`levelGauge` 分格儀表、`timelineBar` 逐日時間軸 |
| `tools/region_plates.py` | 做上面那些底片：把「只改了一個區域」的編輯圖用 ECC 對齊底圖（在區域外對齊），在羽化環上校色，經羽化形狀貼回底圖。區域外逐像素等於底圖，不符即停；輸出底片與 `<base>-regions.json`（輸入 SHA、變換、ECC、色偏） |
| `tools/codex_plate.py` | 用 Codex CLI 內建 `image_gen` 生成底片。prompt 從 prompt 本逐字讀出；可用 `--ref` 綁定身份參考；在倉庫外執行，並記錄 SHA 與 argv |
| `tools/fonts.py` | 從系統 OFL Noto CJK 抽出 SC 字面，按實際用字子集化，附授權 |
| `tools/snap_paths.py` | 把手繪粗路徑吸附或追蹤到底片的光軌脊線上 |
| `tools/guide_track.py` | 按 beat map 合成**臨時**導引節拍，只用於判斷同步，不作為配樂交付 |
| `tools/qa.py` | 每次渲染後的 QA，見下節 |
| `tools/sync_check.py` | 唱的 take 的同步檢查（EV toolkit §15、§63）：take 自帶音軌對送出的人聲窗口，量延遲（照抄／重唱）、逐 10 ms 相似度、分歧點、同步區段與包絡延遲分段，輸出 `sync.json`、診斷圖與疊歌審看片（`--review`）。數字決定放置與切點，準不準以人看疊歌片為準 |
| `tools/serve.py` | 只綁 loopback、支援 Range 的靜態伺服器，供審看頁拖動與逐幀 |

`qa.py` 包含：
- 規格核對；
- 事件對拍：預期幀與實際變化起點比對，誤差 ≤1 幀；
- WCAG 2.3.1 閃爍檢查、單幀突跳、strobe 格掃描、離群幀；
- 每小節運動量；
- 聯繫圖：8 分音全片、每鏡首中尾、390 px 可讀性、安全區、100% 文字裁切。

## 用法（以 T01 為例）

```bash
uv run python outputs/ai-city-takeover/phase1-t01/comp/build.py --guide      # 底片、資料、字體、esbuild、index.html
npx --no-install hyperframes render outputs/ai-city-takeover/phase1-t01/comp \
    -o outputs/ai-city-takeover/phase1-t01/renders/T01-devN.mp4 -f 30 -w 4 --browser-gpu --quality high
uv run python motion-kit/tools/qa.py --video <render.mp4> --comp outputs/ai-city-takeover/phase1-t01/comp \
    --out outputs/ai-city-takeover/phase1-t01/qa/devN
```

合成檔根節點需加 `data-no-timeline`（不用 GSAP），否則 HyperFrames 會等待 45 秒。專案設定不要用全域變數傳遞：HyperFrames 會隔離合成腳本的作用域，改由引擎 fetch `data/*.json` 讀取。

## 已知限制

- Codex 內建 `image_gen` 實測約 1.57 MP。底片放大約 1.15–1.24 倍，靠降噪、雙三次取樣與印刷顆粒處理。
- 無深度模型：2.5D 以手動幾何（車道模型、路徑、遮罩）加程序化霧與光實現。
- 字體只用系統 OFL Noto CJK（Sans、Serif、Mono），沒有 DIN 類窄體。

## Clock Boundary Regression

2026-10-30，增加7项Node回归，覆盖变速节拍、窗口与偏移、逐帧量化、事件起点、确定性噪声和透视映射。修复offset=2、event=2.6s时comp0.6s拍点因浮点误差丢脉冲的问题；`last`仍排除未来事件。可用`node --test motion-kit/tests/runtime.test.mjs`执行。新代码重新构建与渲染后，T01 dev7 MP4与已认可bytes的SHA完全相同；新软件identity见`qa/dev7/clock-recheck-source-and-media-sha256.json`，旧软件identity只保留为历史。
