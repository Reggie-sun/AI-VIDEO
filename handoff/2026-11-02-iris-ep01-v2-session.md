# Handoff：IRIS EP01 v2《Looked Outside》製作會話（2026-11-02）

給下一個 Agent。本文件記錄這個會話到目前為止的一切：目標、使用者決定、規則、檔案、命令、每一鏡的狀態與花費、學到的模型行為、未完成事項。

- **資料來源**：每一項都盡量附上檔案路徑。數字以檔案為準，本文件只是索引。
- **使用者決定的原文**：在 `outputs/ai-city-takeover/logs/decisions.md`，逐字記錄。
- **回覆語言**：使用者要求一律用繁體中文回覆。path、command、API、schema 名保持原文。

---

## 0. 一句話現況（2026-11-02 05:20 本地時間，UTC−5；已過時，最新狀態看第 12 節最後一段）

**已交付**

- 成片 c1 已交使用者審看：`outputs/ai-city-takeover/ep01/v2/renders/IRIS-EP01-Looked-Outside-v2-c1.mp4`，審看頁 `ep01/v2/review/film.html`。

**使用者對 c1 的意見**

> 「2s这里没有睁眼的过程是为什么,衔接很弱.后面人物表现一直很弱,唱歌也是」

**使用者已選定的修訂**

- 範圍：「S1 睁眼＋副歌＋S5/S7 反應 (Recommended)」。
- 演唱方向：「冷靜但活著 (Recommended)」。
- 預算：5 鏡約 924 積分；每鏡最多修 1 次，上限約 1,850 積分。
- 順序：先給使用者看靜幀預覽，認可後才付費。

**目前進度**

- 6 張表演預覽靜幀已生成，存在 `ep01/v2/keyframes/raw/`：
  - **K1c**：S1 睜眼。
  - **P5**：S5 看到紅窗的反應。
  - **P7**：S7 眼睛跟著薄片轉。
  - **P8a**：S8a 正面在唱。
  - **P8b**：S8b 最後一句。
  - **P8c**：S8b 唱完望城市。
- 縮圖已輸出到 `ep01/v2/review/*.jpg`。
- 我已逐張看過：身份、構圖、力度都對。

**下一步**

1. 做預覽頁 `ep01/v2/review/v3-preview.html`。
2. 用 AskUserQuestion 請使用者認可。
3. 認可後封存 preview approval，再按第 6 節流程逐鏡付費生成。

**尚未 commit 任何東西。** 整個 `outputs/ai-city-takeover/ep01/v2/` 都是未追蹤檔案。

---

## 1. 專案目標與歷程

**使用者原始需求**（簡中，逐字）：

> 你是一支由技术导演、Motion Designer、AI 视频导演、音频工程师组成的制作团队。我要使用 Claude Code 复刻 @anabology 的 ESCAPE VELOCITY 的视觉制作技术，最终建立能够持续制作高质量抖音短视频的工作流。

原文在 `outputs/ai-city-takeover/brief/creative-input.md`。

**階段**

- **Phase 1**：T01 十秒測試片，存在 `outputs/ai-city-takeover/phase1-t01/`。
- **Phase 2**：IRIS 系列 EP01《Looked Outside》。
  - 橫版 1920×1080、30 fps、30.5 s。
  - 主角 IRIS：固定的寫實歐美女性 AI 角色，冷靜觀察者。
  - 形式：英文歌詞 MV，配簡中譯句。
  - 題材：AI 新聞，OpenAI 2026-10-23 披露的訓練事件。

**接手前的背景**

- 使用者說「你别管codex,我觉得他没做好」。從此 EP01 由 Claude 主會話全權負責。
- Codex 的舊產出只當候選或歷史，不刪、不改。
- 使用者要求全自動：「我希望全自动别要我点击」。

**規格與分鏡**

- 規格：`docs/superpowers/specs/2026-10-30-ev-motion-douyin-pipeline.md`。
  - §3.7 寫明：成片接 `CompositionSpec → ResolvedTimeline → HyperFrames` 屬 Phase 1.5，**目前尚未做**。
  - 所以 EP01 v2 是用 motion-kit 合成、HyperFrames CLI 直接渲染。
- 分鏡：`ep01/v2/board.md`，v2.1 版，使用者已認可。
- 導演 coverage：`ep01/v2/director-coverage.json`，由 `build_coverage.py` 產生，open-video v4 格式。

## 2. 使用者決定（時間序，原文見 decisions.md）

| 時間 | 原文 | 意義 |
| --- | --- | --- |
| 先前 | 「可以，往下做分鏡」 | 認可歌曲 v2 |
| 先前 | 「認可，開始生成」 | 認可分鏡 v2.1、動態分鏡與參考包；授權即夢 7 鏡付費生成，上限約 2,500 積分，每鏡最多修 1 次 |
| 11-02 | 「用第一版 (Recommended)」 | S8a 用第一版：兩版都沒過 Gate，第一版的不合格點在成片窗口外 |
| 11-02 | 「認可，生成 S8b (Recommended)」 | 認可 S8b 參考包（K8b、ID7b、副歌第二遍乾聲） |
| 11-02 | 「認可修復參考，重做一次 (Recommended)」 | S8b 有界修復，加 0.2 s 前置靜音 |
| 11-02 | 「用 S8b2 (Recommended)」 | S8b 用 S8b2 |
| 11-02 | 「2s这里没有睁眼的过程是为什么,衔接很弱.后面人物表现一直很弱,唱歌也是」 | 對成片 c1 的意見 |
| 11-02 | 「S1 睁眼＋副歌＋S5/S7 反應 (Recommended)」＋「冷靜但活著 (Recommended)」 | 重做 5 鏡，先看靜幀 |
| 11-02 | 「你得为这个session专门简历一个文档记录所有一切./home/reggie/vscode_folder/AI-VIDEO/handoff 方便下个agent继续」 | 本文件 |

**更早的長期約束**

- 「确需调用付费模型时先列出预算」。
- 不降低品質。
- 「保留 AI 标识，只禁止新增剧情字幕和图形」。
- 圖像與影片的 prompt 必須純中文。
- 不外傳、不發布。
- Suno 不解 captcha。

## 3. 必守規則（摘自 AGENTS.md 與本會話實作）

- **付費生成**
  - 只走 canonical `VideoGenerationService.submit_once`，搭配一次性 permit。
  - 結果 UNKNOWN 就停，不盲目重試。
  - 每鏡付費前要回報：連續性、交接、軸線／動作／機位、prompt 適配、lint 證據。
- **preview approval**
  - 劇情類付費生成前，使用者必須認可預覽並封存為 `preview_approval`。
  - **新規定**（peer session 剛加入 `src/ai_video/production/reference_authoring.py`，尚未 commit）：resolved request 裡每一個輸入（圖、音訊）的 sha256，都必須出現在被引用的 preview approval 的 `preview_artifacts` 裡，否則 prepare 會拋 `preview_approval[input_asset:...]`。
  - 身份圖 ID7b、對嘴乾聲也要列進去。
- **身份規則**
  - 有 IRIS 出場的鏡頭需要身份參考，所以只能用 multimodal 全模態。
  - 原生首幀、首尾幀模式帶不了身份圖，canonical 會擋。
  - 例外：使用者在 preview approval 的 `identity_waivers` 列入 `"IRIS"` 並認可。
  - S9a 沒有人，所以能用原生首尾幀。
- **逐鏡 Gate**
  - 每支 MP4 落盤後、下一鏡送出前，必須用 project-local `video-analysis` MCP（probe、review、extract_frames）逐項裁決並封存。
  - 封存位置：`ep01/v2/qa/gate-<unit>/post-media-gate.json`，寫入模式為 `x`，不可覆寫。
  - FAIL 只能由使用者改判。
- **Final-output-first**：先交片，使用者認可後才跑完整驗證，再 commit 與 push。push 到 `main`，不可 force push。
- **檔案範圍**
  - 只 commit 本任務路徑，用 `git add <specific-files>`。
  - **不碰 peer session ai-video-66 的檔案**：`src/ai_video/production/{preview_approval,reference_authoring,reference_planning_contracts}.py`、`canvas_authoring.py` 及其 tests 與 docs。
- **憑據**：只經注入的 supplier 取得，Agent 不讀 `.env`。
- **cwd**：保持在倉庫根，否則 OMC 會在子目錄生出 `.omc/`。
- **不要 commit 的檔案**：`refs/ev-frames-final.webp`。

## 4. 目錄地圖（`outputs/ai-city-takeover/`）

| 路徑 | 內容 |
| --- | --- |
| `logs/decisions.md` | 使用者決定逐字記錄 |
| `logs/ledger.md` | 每次付費或額度呼叫一行 |
| `logs/runs.md` | Codex 生圖 run 記錄 |
| `ep01/v2/board.md`、`director-coverage.json`、`build_coverage.py` | 分鏡 v2.1 與導演 coverage |
| `ep01/v2/preview-approval.json` | 分鏡 v2.1 的預覽認可，12 項；S3–S8ar 用這份 |
| `ep01/v2/preview-approval-S8b.json`、`preview-approval-S8br.json` | S8b、S8br 的預覽認可，含 ID7b 與乾聲 |
| `ep01/v2/s8a-lipsync-amendment.md` | S8a／S8ar／S8b／S8br 對嘴標準，皆在付費前封存，含修訂原因 |
| `ep01/v2/song/` | 歌曲 v2：`mix/IRIS-01-v2.wav` sha d7e2107d…，30.504 s；bed `bed-01/music__20261102_004125.mp3` sha f45c385e… |
| `ep01/v2/song/isolation/` | ElevenLabs 分離的副歌乾聲與 S8a／S8ar／S8b／S8br 參考 WAV，各附 `*-timeline.json`（RMS＋pYIN，30 fps） |
| `ep01/v2/timing/` | `words.json`：17 行逐字時間；`alignment.json` |
| `ep01/v2/keyframes/prompts.md`、`raw/` | 分鏡 v2.1 關鍵幀 K1a、K1b、K3、K4、K5、K5b、K7、K8b、K9b、K9e |
| `ep01/v2/keyframes/prompts-v3-performance.md` | **v3 表演預覽** prompt 本；成品 K1c、P5、P7、P8a、P8b、P8c 在 `raw/` |
| `ep01/v2/gen/unit.py` | 每鏡建 canonical 專案（draft／materialize），見第 6 節 |
| `ep01/v2/gen/operator.py` | 付費 operator：prepare／start／submit／poll／fetch，一個 unit 只能送一次 |
| `ep01/v2/gen/addnode.cjs` | 在 IRIS 即夢畫布新增一個空白影片節點（CDP，不生成） |
| `ep01/v2/gen/ledger.json` | v2 付費累計帳；`known_no_effect` 不計入上限 |
| `ep01/v2/gen/<unit>/` | 每鏡的 profile、draft、project（canonical 狀態與取回的 MP4）、bound、lint、intent、result |
| `ep01/v2/gen/_superseded/` | 改版前、從未送出的舊 draft（S7、S1 推近版，S9a 軟端點版） |
| `ep01/v2/qa/` | 逐鏡 Gate 與工具，見第 7 節 |
| `ep01/v2/comp/` | motion-kit 合成專案，見第 5 節 |
| `ep01/v2/renders/` | 動態分鏡 a5–a9、成片 b1／b2／b3／c1、交付檔；`renders/review/` 是對嘴審看小片 |
| `ep01/v2/review/` | 審看頁 `film.html`、`S8b-preview.html` 與縮圖 |

**本任務改過的 motion-kit 與工具**

- `motion-kit/src/runtime.js`：image-sequence 底片；渲染佇列，修正多 worker 單幀閃錯畫面。
- `motion-kit/src/lyrics.js`：新檔，逐字歌詞。
- `motion-kit/tests/lyrics.test.mjs`。
- `motion-kit/tools/fonts.py`：`--latin`。
- `motion-kit/tools/whisper_align.py`：新檔。
- `motion-kit/tools/qa.py`。
- `motion-kit/tools/codex_plate.py`：新增 `--edit-base`。

## 5. 合成與渲染（成片）

**流程**

1. `uv run python outputs/ai-city-takeover/ep01/v2/comp/build.py`：寫 data、plates、audio、fonts，並用 esbuild 打包。
2. `uv run python outputs/ai-city-takeover/ep01/v2/comp/seq.py`：
   - `SOURCES` 列出每鏡用哪支已過 Gate 或使用者選定的 MP4，以及入點。
   - 檢查 sha 後轉成 30 fps 的 JPG 序列，放在 `comp/seq/<shot>/`（gitignored）。
   - 寫出 `seq/sequences.json`。
3. `~/.local/share/ai-video/video-analysis-mcp/bin/python -I outputs/ai-city-takeover/ep01/v2/comp/tracks.py`：S3 紅門縫追蹤、S7 戳記位置，寫入 `data/tracks.json`。
4. 再跑一次 `build.py`，讓 esbuild 把 sequences 打包進去。
5. 渲染：`timeout 1500 npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v2/comp -o outputs/ai-city-takeover/ep01/v2/renders/<name>.mp4 -f 30 -w 4 --browser-gpu --quality high`，約 1–2 分鐘。
6. QA：`uv run python motion-kit/tools/qa.py --video <mp4> --comp outputs/ai-city-takeover/ep01/v2/comp --out outputs/ai-city-takeover/ep01/v2/qa/<name> --dur 30.5`。
7. 交付檔：`ffmpeg -i <render> -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 320k <delivery>.mp4`。

**剪點**（`comp/data/events.json`，由 `build.py` 從節拍與人聲起點算出）

| 鏡 | 起始時間 (s) |
| --- | --- |
| S2 | 2.8667 |
| S3 | 4.8 |
| S4 | 8.1333 |
| S5 | 11.4667 |
| S6 | 13.3667 |
| S7 | 14.8 |
| S8a | 18.8667 |
| S8b | 22.5667 |
| S9a | 25.9 |
| S9b | 28.3 |

**成片 c1 現況**

- 不付費的鏡：S2 沿用 A01-v2；S4、S6、S9b 用 K4／K9b 靜幀加 motion-kit。
- 生成鏡：S1、S3、S5r、S7、S8a（第一版）、S8b2、S9a。
- QA：10 個剪點 ±0 幀；12 個圖形時機在 ±1 幀內；無閃爍、頻閃、跳幀或離群幀。
- 響度：−14.2 LUFS，峰值 −1.3 dBFS。
- 檔案：渲染檔 `renders/EP01-film-c1.mp4` sha 72d8b671…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c1.mp4` sha fe6f8a7a…。
- 拼接審查記錄：`qa/film-c1/assembly-review.json`，僅開發側。
  - `verify-assembly` **未跑**：它需要 canonical ResolvedTimeline 與 HyperFrames render report，motion-kit 合成沒有這兩樣。
  - 所以 c1 是**未經 Harness 驗證接點的審看片**。

## 6. 付費生成流程（即夢 Seedance 2.0 VIP 1080p，canonical）

**一鏡的完整步驟**

1. 畫布節點：`node outputs/ai-city-takeover/ep01/v2/gen/addnode.cjs outputs/ai-city-takeover/ep01/v2/gen/<unit>`。
   - 用 CDP 連 Chrome profile `~/.local/share/ai-video/playwright-mcp/profile`，在 IRIS 畫布（project 829df260-5a63-4f0d-8265-8353dc693b3b）點左側「視頻」新增一個空白節點。
   - 寫出 `node-created.json`，其中也會讀到帳戶餘額。
2. profile：複製某個舊 unit 的 `profile.json`，改 `node_id`。
   - `duration_seconds` 與 `benefit_amount` 相同（4、5 或 6）。
   - `credit_upper_bound` 固定 250。
   - 首尾幀模式另加 `"input_mode": "first_last_frame"`。
3. 在 `gen/unit.py` 的 `SPECS` 加這一鏡的 spec：refs、prompt（純中文）、intent、performance、rules，選填 audio、dialogue、frame_roles、conditioning、preview_file。
4. `uv run python outputs/ai-city-takeover/ep01/v2/gen/unit.py draft <unit>`，再 `... materialize <unit> --profile <unit>/profile.json`。這步免費，只做 canonical bootstrap 與 prepare。
5. 寫 `<unit>/operator-bound.json`，欄位可照 S8br 的模板：
   - attempt_id、ceiling 250、3 小時窗口。
   - 修復鏡加 `repair_of`。
6. `uv run python outputs/ai-city-takeover/ep01/v2/gen/operator.py prepare <unit>`，產生 `prepared.json`（含 paid preview）。
7. 寫 `<unit>/pre-submit-lint.json`，`pass` 必須為 true；可照各 unit 的模板。檢查項：
   - 輸入的 sha 與順序。
   - 純中文、AI 標識、固定機位。
   - 預覽認可涵蓋所有輸入。
   - 預算。
8. 向使用者回報送出前檢查：連續性、交接、軸線、prompt、lint、預算。
9. `operator.py start <unit>`，再 `operator.py submit <unit>`。
10. 背景輪詢：`operator.py poll <unit>`，每 45 秒一次，直到 succeeded，通常 3–6 分鐘。
11. `operator.py fetch <unit>`。MP4 在 `<unit>/project/state/video-generation/fetch/files/<sha>.mp4`。
12. Gate：MCP `video_probe`、`video_review`、`video_extract_frames`。extract 結果太大時會存成檔案，用 `qa/gate_sheet.py` 解碼成 sheet。再用 `qa/frame_drift.py`、`qa/region_drift.py`、`qa/lipsync_review.py` 取證，最後封存 `qa/gate-<unit>/post-media-gate.json`。

**operator 內建保護**

- 一個 unit 只能送一次。
- `ledger.json` 累計上限：舊預算是 10 次、2,500 積分。
- 必須有 lint pass，且在時間窗口內。
- UNKNOWN 或 interrupted 就停。

**上傳失敗的處理**：結果是 `known_no_effect`，沒有扣費。若要重試，另開新的 unit 目錄（見 S8b → S8b2），同一請求要逐項比對。

## 7. 逐鏡狀態（v2，全部 1080p）

| unit | 時長 | 畫布節點 | 結果 | 成片使用 |
| --- | --- | --- | --- | --- |
| S3 | 6 s | node_1vxq33rs4d | PASS | 是，入點 2.0 s |
| S5 | 6 s | node_x7nx0de1et | FAIL（推近末段加速） | 否 |
| S5r | 6 s | node_g5dbxsad5y | PASS（固定機位） | 是，入點 1.0 s |
| S7 | 6 s | node_2dp6s93h3e | PASS | 是，入點 1.0 s |
| S1 | 6 s | node_84f31ceyn1 | PASS（只閉眼） | 是，入點 1.0 s；**將重做睜眼** |
| S9a | 6 s 原生首尾幀 K4→K9e | node_5jvcjw9pzq | PASS | 是，入點 0.16 s |
| S8a | 5 s，全模態＋乾聲 | node_g2c2vwv3d1 | FAIL（成片窗口外）→ 使用者選用 | 是，入點 0.4667 s；**將重做表演** |
| S8ar | 5 s | node_p8zbz56w2a | FAIL（開口晚 4–8 幀） | 否 |
| S8b | 4 s | node_pt1yxwtw3y | 上傳失敗，`known_no_effect`，未扣費 | 否 |
| S8b2 | 4 s | node_pt1yxwtw3y（同上） | FAIL（句尾晚約 0.2 s）→ 使用者選用 | 是，入點 0.3667 s；**將重做** |
| S8br | 5 s | node_wdy7ej2s5d | FAIL（約 2.2 s 後閉嘴不唱） | 否 |

- 各鏡 MP4 的 sha 見 `seq.py` 的 `SOURCES` 與各 gate JSON。
- 使用者的改判記錄：`qa/gate-S8a/user-decision.json`、`qa/gate-S8b2/user-decision.json`。

## 8. 花費（`logs/ledger.md` 為準）

**即夢**

| 項目 | 數量 | 積分 |
| --- | --- | --- |
| 6 秒片（198 / 支） | 6 支 | 1,188 |
| 5 秒片（165 / 支） | 3 支 | 495 |
| 4 秒片（132 / 支） | 1 支 | 132 |
| **合計** | 10 支 | **約 1,815** |

- 另有 1 次上傳失敗，未扣費。
- 餘額讀數：67,645 → 65,995（S8br 之前）；S8br 的 165 待讀數確認，預期約 65,830。
- 舊預算的 2,500 上限已用完。新一輪 5 鏡的預算（上限約 1,850）已由使用者選項認可，需要在 operator 另設新上限，例如 v3 ledger。

**ElevenLabs**

- 歌曲與配音合計 1,726 credits（帳號 1,162→2,888）。
- 副歌分離約 7 s，讀數未變，結算待確認。

## 9. 本會話學到的事（下一個 Agent 必讀）

**Seedance 2.0 全模態對嘴**

- 生成檔自己的歌聲是「重唱」，時間會漂。前半句可能早 0.2–0.4 s，或整段縮短：S8br 只唱 2 秒。
- 畫面的嘴大多跟參考音訊，偶爾跟自己的重唱。
- 三次試驗裡，**參考前加 0.2 s 靜音**的 S8a 第一版開口時機最準。代價是靜音段會保留首幀的張嘴姿勢，要剪掉。
- 判對嘴要看逐幀嘴型對照參考音軌：用 `qa/lipsync_review.py` 產生 `mouth-timeline.jpg`、`onsets.jpg`。暗像素自動量測太吵，不可靠。

**`words.json` 的唱段時間不可靠**

- 副歌第一個「I」實際從 18.60 s 開唱，比 words.json 早約 0.3 s。
- 「run」「outside」是拖長音。
- 要用分離乾聲的時間軸檔判斷。

**prompt 的教訓**

- 「極慢推近，末段收穩」會在最後 1 秒加速。要靜止就寫「三腳架完全固定」，S5r、S7、S1 都穩。
- **把動作壓到「只有呼吸眨眼、頭不動、冷靜克制、輕聲演唱」，會讓人物死板**。這是使用者對 c1 最大的不滿。v3 改成寫具體的戲：吸氣、眼神、反應、情緒推進。

**首尾幀與 canonical 規則**

- 原生首尾幀（S9a）很穩，但有 IRIS 的鏡頭受身份規則限制，見第 3 節。
- 首尾幀的 row 需要 `conditioning_compatibility`（FL2VA），寫法見 unit.py 的 S9a spec。

**合成與渲染**

- HyperFrames 多 worker 時，渲染必須序列化，否則會出現單幀錯底片。已在 `runtime.js` 修正，QA 的 outlier 檢查可以抓到這種問題。
- Seedance 輸出約 24 fps 的 VFR，合成時用最近幀映射到 30 fps，不插幀。

**即夢與 Chrome 環境**

- 即夢參考上傳可能偶發失敗，結果是 `known_no_effect`。
- 同一個 Chrome 開著其他會話的畫布，例如《反相之地》，可能有干擾。

**Codex 生圖**

- 用 `motion-kit/tools/codex_plate.py`，走 Codex CLI 內建 `image_gen`，約 1 分鐘一張，可並行 3 張。
- `--edit-base` 能在保留構圖的前提下只改表演。

## 10. 進行中的工作：表演修訂 v3

**已完成**

- prompt 本 `keyframes/prompts-v3-performance.md`。
- 6 張靜幀與縮圖 `review/{K1c,P5,P7,P8a,P8b,P8c}.jpg`。
- 我的檢查結果：
  - K1c 與 K1a 構圖一致，只是睜開眼，非常適合當首尾幀。
  - P5 皺眉凝視，反應明確。
  - P7 眼睛轉向左側的薄片。
  - P8a 正面張口唱、眼神鎖鏡頭。
  - P8b 半閉眼仰頭唱。
  - P8c 閉嘴望遠方。
  - 身份都一致。

**下一步（依序）**

1. **做預覽頁** `review/v3-preview.html`，內容包括：
   - 每鏡的起始圖與表演靜幀。
   - S1 的新剪接：眼睛在「woke」約 2.83 s 睜開，S1 延到約 3.2 s，S2 縮成約 3.2–4.8 s，片名跟著新剪點出現。
   - 每鏡做法、預算。
2. **用 AskUserQuestion 請使用者認可**，包含：
   - S1 是否同意 IRIS 的 `identity_waivers`，才能用原生首尾幀 K1a→K1c。這是巨特寫，只看得到眼睛，身份由首尾幀承擔。
   - 若不同意，S1 改用全模態：K1a、K1c、ID7b 三張軟參考。
3. **封存** `preview-approval-v3.json`：
   - 列出所有付費輸入的 sha：K1a、K1c、K5b、P5、K7、P7、A02、P8a、K8b、P8b、P8c、ID7b、S8a 乾聲 `S8a-vocal-ref-18.40-23.40.wav`（建議沿用第一版做法）、S8b 乾聲 `S8br-vocal-ref-22.00-27.00.wav`（帶 0.2 s 前置靜音）。
   - 若同意 waiver，加 `identity_waivers: ["IRIS"]`。
4. **operator 設新的 v3 上限**：10 次、1,850 積分。建議另開 `ledger-v3.json` 或在 operator 加參數，舊帳不得改寫。
5. **在 unit.py 加 v3 spec**，unit 名稱建議 S1v3、S5v3、S7v3、S8av3、S8bv3：
   - 表演靜幀作為額外 reference，duty 寫「只示范神情与投入程度，不是起始画面、不改变构图」。
   - planning 用 performance event（control `model_guidance`），或用 pose anchor。
   - prompt 要寫具體的戲，不要再壓動作。
6. **逐鏡生成與 Gate**，每鏡最多修 1 次。對嘴標準照 `s8a-lipsync-amendment.md` 的方法，在付費前另封存 v3 段。
7. **更新 `comp/seq.py` 的 SOURCES**；S1 剪點改動要同步 `comp/build.py` 的 events（cut_S2 = S1 新長度）與 `board.md` 或 coverage 說明。重算 seq、tracks、build、render、QA，交 c2 給使用者看。

## 11. 其他未完成與已知風險

**獨立審查**

- code-reviewer、verifier 兩個子代理因額度中斷，沒有結果。
- commit 前要重派：審 `runtime.js`、`comp/`、`gen/unit.py`、`operator.py`、`qa/*.py`，並核對 gate 與帳本。

**commit 前的步驟**

- 使用者認可成片後，跑 `record-ai-video-session`（寫入 `docs/record_for_agent/`），並評估 `distill-ai-video-learning`。
- Harness 分級驗證先跑 `focused`（Harness 只認 exact staged snapshot），commit 後 push 並核對 SHA。

**目前狀態**

- 什麼都沒 commit。
- S8br 餘額與 ElevenLabs 分離費用都待確認。
- `verify-assembly` 跑不了，接點只有開發側的觀察記錄。

**已知畫面差異**

- S5r 景別比 K5b 寬。
- S1 窗外光掠過很弱。
- S7 戳記只能閃現：薄片移動太快。
- 這三點 v3 重做時一併處理。

---

## 12. 進度更新（依序 1–4；最後一段是最新）

**使用者認可**

- v3 預覽頁：`ep01/v2/review/v3-preview.html`。
- 使用者原話：「認可，S1 用原生首尾幀 (Recommended)」，也就是 S1 同意免附 IRIS 身份圖。

**預覽認可檔**

- `ep01/v2/preview-approval-v3.json`：S5、S7、S8a、S8b，共 13 項輸入。
- `ep01/v2/preview-approval-v3-S1.json`：S1，含 `identity_waivers: ["IRIS"]`。

**v3 unit**

- 已建立並完成免費 prepare 的 unit 與畫布節點：

  | unit | 畫布節點 |
  | --- | --- |
  | S1v3 | node_d0a24kjfsf |
  | S5v3 | node_4bgjmfnzjj |
  | S7v3 | node_0hhpmypamh |
  | S8av3 | node_41076c7tr7 |
  | S8bv3 | node_dd7zc9e0h4 |

- spec 在 `gen/unit.py` 的「v3 performance redo」段。

**operator 與帳本**

- operator 支援每輪各自的帳本：bound 裡寫 `"ledger": "ledger-v3.json"`、`cumulative_submit_ceiling: 10`、`cumulative_operator_credit_ceiling: 1850`。
- 舊的 `gen/ledger.json` 不動。

**付費前已封存的標準**

- S8av3、S8bv3 的對嘴與表演標準：`s8a-lipsync-amendment.md` 的「v3 表演重做」段。
- S1v3、S5v3、S7v3 依各自 QA rules。

**送出狀態**

- S1v3 已送出（ledger-v3 第 1 次），結果待取回並過 Gate。
- 之後的順序：S8av3 → S8bv3 → S5v3 → S7v3，每鏡都過 Gate 才送下一鏡。
- 送出步驟照第 6 節，bound 要帶 ledger-v3 欄位，lint 可參考 `gen/S1v3/pre-submit-lint.json`。

**帳務**：S8br 的扣款已確認為 165 積分，餘額 65,830。

**unit.py 這輪的改動**

- 新增 `identity_waiver`：不附身份圖；planning 寫 `identity_waivers`；identity_continuity 為空；Character 記錄照樣帶入 Registry。
- preview 會帶入 approval 檔的 `identity_waivers`。
- 新增 `settle` 與 `stability` 覆寫，讓推近鏡頭可以寫「全程匀速」。

**之後要做的剪接**

- S1v3 出片後，找出睜眼瞬間，決定 S1 的入點，讓睜眼落在母帶約 2.83 s。
- S1／S2 剪點改到約 3.2 s，要同步改 `comp/build.py` 的 `cut["S2"]` 計算，以及 S2 的片名 slam。

### 進度更新 2

**S1v3 逐鏡檢查 PASS**（`qa/gate-S1v3/post-media-gate.json`）

- MP4 sha 4d37fe3d…。
- 眼瞼約 2.4 s 開始抬，2.83 s 半睜（「woke」），約 3.3 s 完全睜開並對焦。

**合成已改**

- `comp/seq.py` 的 S1 改用 S1v3，入點 0.0。
- `comp/build.py` 的 `cut["S2"]` 改為 `beat(1, 3)`，即 3.3437 s，量化後 3.3667 s。S1 變成 0–3.37 s，S2 變成 3.37–4.80 s。
- `director-coverage.json` 的 S1、S2 時長**尚未同步**，仍是 2.867／1.933；交付前要更新並註明是使用者意見帶來的剪接修改。

**S8av3**：已送出，ledger-v3 第 2 次，結果待取回並過 Gate。

**額度監看**

- 讀法：`ccam usage --json --source cache`。目前帳號 work2 的 5 小時用量 63%（05:34），週用量 22%。
- 背景監看設在 work2 5 小時用量 ≥85% 時通知。
- 其他帳號：main 週額度已滿，work、work3 的 5 小時額度已滿。
- 使用者要求：額度快用完時一定要更新本文件。

### 進度更新 3（額度快滿前的完整交接點，約 05:45）

**額度**（`ccam usage --json --source cache`）

- work2：5 小時 80%（10:10 本地時間重置），週 24%。
- main：週額度已滿。
- work、work3、work4：5 小時額度已滿。
- work5：0%，下一個帳號很可能是它。

**v3 進度**

| unit | 狀態 |
| --- | --- |
| S1v3 | PASS，已放進 `comp/seq.py`（入點 0.0），S2 剪點已改 |
| S8av3 | 已生成成功，取回中；背景工作執行 `operator.py fetch S8av3` |
| S8bv3、S5v3、S7v3 | bound、prepared、lint 都已就緒（`gen/<unit>/pre-submit-lint.json` pass），**尚未送出** |

**接手的 Agent 依序做**

1. 若 `gen/S8av3/fetch-result.json` 不存在，執行 `uv run python outputs/ai-city-takeover/ep01/v2/gen/operator.py fetch S8av3`。
   - 先看 project 的 attempt 狀態。若 attempt 已經是 fetched，就不要重複 fetch。
2. 對 S8av3 做逐鏡檢查：
   - MCP 執行 `video_probe`、`video_review`、`video_extract_frames`。
   - 用 `qa/gate_sheet.py` 產生 sheet。
   - 用 `qa/lipsync_review.py <mp4> outputs/ai-city-takeover/ep01/v2/song/isolation/S8a-vocal-ref-18.40-23.40.wav outputs/ai-city-takeover/ep01/v2/qa/gate-S8av3 --mouth 980,400,300,230 --onsets 0.85,2.33,3.50 --zero 18.40` 取得逐幀嘴型證據。嘴部裁切範圍依實際畫面調整。
   - 用 `qa/frame_drift.py` 確認推近勻速、不加速。
   - 依 `s8a-lipsync-amendment.md` 的「v3 表演重做」段裁決，封存到 `qa/gate-S8av3/post-media-gate.json`。
3. S8av3 若 PASS，依序送出並檢查 S8bv3 → S5v3 → S7v3。每鏡的步驟：
   - `operator.py start <unit>`，再 `operator.py submit <unit>`。
   - 背景輪詢 `operator.py poll <unit>`。
   - `operator.py fetch <unit>`，然後過 Gate。
   - S8bv3 的 lipsync_review 參數：參考 `S8br-vocal-ref-22.00-27.00.wav`，`--zero 22.00`，`--onsets 1.10,2.233,3.233,3.60`，`--mouth 300,330,320,240`。
   - FAIL 時每鏡可修 1 次。修改要可歸因；新輸入要先取得使用者的預覽認可。
4. 全部完成後，更新 `comp/seq.py` 的 SOURCES，填入各鏡 v3 MP4 與入點。各入點要讓動作對上歌：
   - S5：反應落在 'around' 約 11.53 s。
   - S7：眼睛跟薄片的動作落在 'offline world' 附近，回到鏡頭落在 'cached'。
   - S8a：入點 0.4667（片內 0 s 對應 18.40 s）。
   - S8b：入點 0.5667（片內 0 s 對應 22.00 s）。
5. 依第 5 節流程重算 seq、tracks、build、render，再跑 QA，交成片 c2 給使用者，並做拼接審查記錄。
6. 使用者認可後：
   - 重派獨立審查。code-reviewer 審 `runtime.js`、`comp/`、`gen/`、`qa/`；verifier 核對 gate 與帳本。
   - 跑 `record-ai-video-session`。
   - Harness 驗證：focused，接著 related。
   - commit 本任務路徑，push 到 main 並核對 SHA。

### 進度更新 4（05:50 本地時間；work2 5 小時用量已到 92%）

**先前段落的時間標記**

- 第 12 節原本標的「05:55／06:05／06:12」是錯的（寫入時檔案實際時間約 05:45），已改成序號。以 `date` 為準。

**額度**（`ccam usage --json --source cache`，05:48）

| 帳號 | 5 小時 | 週 | 備註 |
| --- | --- | --- | --- |
| work2（本會話） | 92% | 25% | 10:10 本地時間重置 |
| work5 | 0% | 0% | 唯一完全可用的帳號 |
| main | 0% | 100% | 週額度已滿，11-03 10:00 本地時間重置 |
| work | 100% | 45% | 06:10 本地時間重置 |
| work3 | 100% | 14% | 06:20 本地時間重置 |
| work4 | 100% | 14% | 08:10 本地時間重置 |

- 本會話是 ccam 啟動的：`CCAM_PROFILE=work2`、`CLAUDE_CONFIG_DIR=~/.local/share/ccam/profiles/work2`。
- 換帳號繼續：使用者可用 `/ccam:switch`。
- memory 規則「額度剩不到 10%（5 小時 ≥90%）先更新本文件」已寫入 work、work2、work3、work4、work5 五個 profile 的 memory。

**S8av3：已取回，逐鏡檢查進行中（尚未封存）**

- MP4：`gen/S8av3/project/state/video-generation/fetch/files/20e7642b073ab84910c820d75b3021fd5a0a2207b991f5a67edd485b42e3952f.mp4`
  - 5.062 s，121 幀。
  - `fetch-result.json` 已存在，**不要再 fetch**。
- MCP `video_review`：一直在唱，沒有標出問題。
- 證據都在 `qa/gate-S8av3/`：
  - `mcp-sheet.jpg`、`first-mid-last.jpg`、`quarter-second-sheet.jpg`
  - `mouth-timeline.jpg`、`onsets.jpg`、`dtw.json`
- 嘴型時間軸（片內時間）：
  - 0–0.2 s 閉嘴。
  - 約 0.27 s 開口。
  - 2.33 s 附近有一次收口。
  - 3.4 s 起張大唱長音。
  - 約 4.5 s 閉嘴。
- `dtw.json` 的偏移約 −0.15 到 +0.05 s。
- `frame_drift.py` 量到的比例變化（相對第 0 幀）：
  - 第 24 幀 +0.05%。
  - 第 48 幀 +2.14%。
  - 第 72 幀 +1.72%。
  - 第 96 幀 +2.25%。
  - 第 120 幀 +3.09%。
  - 第 48 幀之後 inlier 少（約 284/800），臉在動，數字不可靠。「推近是否勻速、不加速」要靠看 `quarter-second-sheet.jpg` 的背景與畫框判斷。
- **待做**：依 `s8a-lipsync-amendment.md` 的「v3 表演重做：S8av3」逐項裁決：
  - 開口時間：片內 0.85／2.33／3.50 s，容許 ±2 幀。
  - 20.57–20.73 的停頓有收口。
  - 頭與眉有可見的表演。
  - 推近勻速、結尾不加速。
  - 身份與牙齒正常。
  - 裁決封存到 `qa/gate-S8av3/post-media-gate.json`，格式照 `qa/gate-S1v3/post-media-gate.json`。

**帳本待補**（`logs/ledger.md`）

- S1v3：198 積分。
- S8av3：165 積分。
- 都是 ledger-v3 的第 1、2 次。餘額讀數待確認。

**之後**

- 照「進度更新 3」的第 3–6 步：S8bv3 → S5v3 → S7v3，接著合成 c2。

### 進度更新 5（05:58 本地時間；使用者要求「记录文档然后停下」，已停下）

**S8av3 逐鏡檢查：FAIL（已封存）**

- 記錄：`qa/gate-S8av3/post-media-gate.json`。
- 不合格的是對嘴：
  - **開口**：0.85 s（didn't）、3.50 s（outside）都準時。2.33 s（I just）的嘴在 2.333–2.433 收窄，2.467–2.50 才重新張開，晚了約 4–5 幀（標準 ±2 幀）。
  - **停頓**：母帶 20.57–20.73 的停頓裡，嘴一直張大到片內 2.267，2.30–2.333 才收小，收口落後約 0.13 s。
  - 逐幀證據：`qa/gate-S8av3/pause-2.10-2.67.jpg`。
- 合格的項目：
  - 表演：眼神一直鎖鏡頭，頭隨樂句明顯傾動，最後長音眉眼放開。比 c1 好很多。
  - 推近：背景完全不動，等於固定機位。沒有加速，但原本要的「極緩推近」也沒有出現。
  - 身份、牙齒、下巴都正常。

**給使用者看的審看片**（片段配母帶，正常速度）

- 依封存的入點 0.4667：`renders/review/S8av3-sealed-master-audio.mp4`
- 入點晚 2 幀（0.5333）：`renders/review/S8av3-slip2f-master-audio.mp4`
  - 修正：**沒有任何一個入點能讓三個開口都在 ±2 幀內**。「didn't」本來早約 1 幀，「I just」晚 4–5 幀，兩點相差約 5 幀。
  - 晚 2 幀後：「didn't」嘴早約 3 幀，「I just」晚約 2 幀。嘴比聲音早，觀感上比較不明顯。
  - 這改了封存的對應關係（片內 0 s = 母帶 18.40 s），只能由使用者決定，不算 PASS。
  - 逐幀證據：`qa/gate-S8av3/onset-0.67-1.03.jpg`、`onset-3.27-3.63.jpg`。
- 對照：c1 用的 S8a 第一版是 `renders/review/S8a-take1-film-window.mp4`。

**還沒做、等使用者決定的事**

- 用 AskUserQuestion 請使用者選一項（每項的花費和作法如下）：
  1. 接受 S8av3，用入點 0.5333 的滑移剪接。不另付費。
  2. 有界修復 1 次，約 165 積分。可歸因的改法是處理參考乾聲在 20.57–20.73 停頓裡的殘響，讓停頓更乾淨。但這會產生新的輸入 sha，**要先給使用者看預覽並封存新的 preview approval**。
     - 只改 prompt 不夠可歸因：S8av3 的 prompt 已經寫了「声音停顿时嘴型随之收小」。
  3. 不換，保留 c1 的 S8a 第一版。
- 依規則（只有全 PASS 才推進），在使用者決定之前，**不要送出 S8bv3**。
- 決定之後的順序照「進度更新 3」：S8bv3 → S5v3 → S7v3 → 合成 c2。

**帳本待補**（`logs/ledger.md`）

- S1v3 198 積分、S8av3 165 積分，都在 ledger-v3。
- 餘額讀數待確認。
- v3 目前已用 2 次，363 積分，上限 1,850。

**額度**：work2 的 5 小時用量約 93%（10:10 本地時間重置）。只有 work5 可用，使用者可用 `/ccam:switch` 接續。

### 進度更新 6（06:21 本地時間；帳號已由 ccam 換到 work5）

**S8av3：使用者已決定**

- 使用者原話：「用 S8av3，晚 2 幀 (Recommended)」。
- 記錄在 `qa/gate-S8av3/user-decision.json` 和 `logs/decisions.md`。
- `comp/seq.py` 的 S8a 已改成 S8av3，入點 0.5333。
- Gate 判定仍是 FAIL，不改。

**S8bv3：參考上傳失敗，沒有扣費**

- 收據 `gen/S8bv3/project/state/paid-provider/submits/9f5a0c11….json` 記錄 `known_no_effect`，ledger-v3 已標註。
- 餘額讀數 65,467 = 65,830 − 198 − 165，可以證明沒有扣費。
- 已用相同請求另開 **S8bv3b**：
  - 新畫布節點 node_08yj7ypyat。
  - spec 是 `SPECS["S8bv3b"] = {**SPECS["S8bv3"]}`。
  - 逐項比對過：模型、prompt、4 張圖、乾聲、時長都相同。
- S8bv3b 已在 06:19 送出（ledger-v3 第 4 筆，計費第 3 次）。
- 背景輪詢會把結果寫到 `gen/S8bv3b/poll.log`，成功後自動 fetch。

**S8bv3b 出片後要做的事**

- Gate 依 `s8a-lipsync-amendment.md` 的 S8bv3 標準。
- 對嘴取證參數：參考 `S8br-vocal-ref-22.00-27.00.wav`、`--zero 22.00`、`--onsets 1.10,2.233,3.233`。
- 嘴部框要用人臉偵測重新定，因為是 K8b 3/4 側面。

**其他**

- `logs/ledger.md` 已補上 S1v3、S8av3、S8bv3、S8bv3b。
- S5v3、S7v3 的 bound 在 13:28Z（08:28 本地時間）到期；過期要重寫 bound，再重新 prepare 和 lint。
