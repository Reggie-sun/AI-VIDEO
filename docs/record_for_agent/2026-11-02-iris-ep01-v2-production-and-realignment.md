---
record_kind: session_summary
topic_id: iris-ep01-v2-production-and-realignment
learning_eligibility: ineligible
---

# IRIS EP01 v2《Looked Outside》製作與方向修正記錄

Date: 2026-11-02（America/New_York，UTC−5）

## Supersession Notice — 2026-11-04

本記錄把「EP01 不再付費生成」「以 c1 為底收尾」寫作現行方向，並以 v2 時期的人物與歌曲（`IRIS-01-v2.wav`）為 EP01 的素材；這些已被 2026-11-03 起使用者「做成完整版 2–3 分钟」與 2026-11-04 換人物、換歌（Suno T4，4:22）、重做分鏡取代：EP01 現按 `outputs/ai-city-takeover/ep01/plan-full-version.md` 的 12 階段做 4:22 完整版，人物為 canon v4，舊主角的人物鏡頭不再沿用（該 plan「不沿用」一節）。目前的檢查點見 [2026-11-04-iris-ep01-v3-full-animatic-checkpoint.md](2026-11-04-iris-ep01-v3-full-animatic-checkpoint.md)。

仍然有效的是 v2 時期的歷史事實（15 次送出的 Gate 判定與 SHA、費用鏈、證據邊界、未追蹤狀態）；561 積分「待確認」等未結算項本次沒有重新核對。被取代不等於已授權付費：新的 Seedance 或數字人提交仍須逐條 `preview_approval`、連續性報告、lint、一次性 permit 與逐鏡 Gate。本記錄沒有加 `retrieval: retired`，因為上述歷史事實仍可檢索。

## Purpose

記下 IRIS EP01 v2 由 Claude 會話全權製作的實際狀態：歌曲 v2 → 分鏡 v2.1 與參考包認可 → v2 付費生成 → 審看片 c1 → v3 表演修訂 → 審看片 c2 → 使用者否定 c2 並要求「回到原作做法」→ spec 草稿 → 交接。讓接手的 Agent 分清「已發生並核對的事」與「草稿、待確認、未驗證」。

這是交接邊界的事後重建，不是會話當下的第一手記錄。被記錄的會話約自 00:20 起、07:45 前後結束（主會話回報；`outputs/ai-city-takeover/logs/ledger.md` 最早一筆 00:25，spec 草稿檔最後修改在 08:06:52），交接前沒有做 record／learning 評估。本記錄由 `memory-keeper` 於約 08:15–09:00 依檔案與離線量測補寫，沒有呼叫付費或遠端 Provider。

`handoff/2026-11-02-iris-ep01-v2-session.md`（35,222 bytes，SHA-256 `c4bafe2f5c6a2b67f390e5cd10ea61993eb3a3eb053f95de9470cc8733a3964d`）只更新到第 12 節「進度更新 6」（06:21），使用者已要求不再更新；其後的事實以 `logs/`、`qa/`、`gen/` 為準。之後的 c3 工作（`ep01/v2/comp/`、`ep01/v2/qa/sync/`、`motion-kit/tools/sync_check.py`）屬另一個會話，不在本記錄內。

## Current Runtime Truth

- **沒有任何成片獲認可。** c1、c2 都是審看片，不是 Final Acceptance；沒有 P6、沒有發布、沒有 commit／push。
- **全部未追蹤。** `git ls-files outputs/ai-city-takeover/ep01` 為 0 筆，整個 `ep01/` 與 spec 草稿都是 untracked；2026-11-02 的 7 個 commit 與 IRIS 無關。`.gitignore` 排除 `*.mp4`、`*.png`，所以 15 支生成片、c1／c2 與關鍵幀不會被一般的 `git add` 納入，位元組只在本機（`ep01/` 約 5.1 GB），跨機器的身份只剩 SHA 與 JSON 證據。
- **拼接 Gate 沒跑。** `verify-assembly` 為 `NOT_RUN`：motion-kit 合成沒有 canonical `ResolvedTimeline` 與 HyperFrames render report（舊 spec `2026-10-30-ev-motion-douyin-pipeline.md` §3.7 的 Phase 1.5 未做），所以 c1、c2 的接點沒有經 Harness 驗證，只有開發側觀察（`qa/film-c1/assembly-review.json`、`qa/film-c2/assembly-review.json`，`authority: development_only`）。
- **使用者目前的判斷。** c1 被批評睜眼銜接弱、人物與唱歌表現弱；c2 針對這些意見重做五鏡，卻被判「节奏变快了,这个还不如上一版」。`logs/decisions.md`「c2 審看與方向」記錄的方向是回到原作做法、EP01 以 c1 為底收尾、不再付費生成（該段是 Agent 對使用者選項回覆的整理，見 Direction Change And Draft Spec）。做法寫在 spec 草稿，草稿未批准。
- **c3 在被記錄的會話結束時沒有動工。**

### Core Artifacts

路徑自 `outputs/ai-city-takeover/ep01/v2/` 起，除非標明 repo 路徑。SHA 由本次重算，與主會話提供的值全部相符。

| 產物 | 路徑 | SHA-256 | 狀態 |
| --- | --- | --- | --- |
| 歌曲 v2 | `song/mix/IRIS-01-v2.wav` | `d7e2107d8597fbc71176d9e472fdce9f6b0dfa86274011e325a89f208f6bcd97` | 30.504 s、48 kHz 雙聲道；使用者認可為歌曲（「可以，往下做分鏡」），不是成片認可 |
| 歌曲 bed | `song/bed-01/music__20261102_004125.mp3` | `f45c385ef6ec3c5ef817cce72ba6c9d6e5f6fbb21849e80ed8b794d137f08973` | 純伴奏加保留的 take 3 副歌 |
| c1 渲染檔 | `renders/EP01-film-c1.mp4` | `72d8b671dd49eeecc219775e6fc19211fa6ad843d6d91033b01375918b3bfc76` | 審看片 |
| c1 交付檔 | `renders/IRIS-EP01-Looked-Outside-v2-c1.mp4` | `fe6f8a7ac8b14eec3ed4ffccf8e0140f1d5b73188a100f1097aa432844ad30ac` | 審看片 |
| c2 渲染檔 | `renders/EP01-film-c2.mp4` | `b98c994ba03a6e3d1f41268903f0e1b3687de227cbf87944f61185e1be7a77e6` | 審看片；使用者判不如 c1 |
| c2 交付檔 | `renders/IRIS-EP01-Looked-Outside-v2-c2.mp4` | `58b9e653cfa74a19c597c3855af441e5a63d2a970b4b38559a843dc1a7149568` | 審看片 |
| 方法 spec 草稿 | `docs/superpowers/specs/2026-11-02-iris-ev-method-realignment.md`（repo 路徑） | `b1eb8b5cad7a9137d07ff3b1ab3c727f24b51d3249424aa4b41448bc0ee8b339` | 草稿，未批准、未 commit |

四支成片本次實測：h264 1920×1080 yuv420p、30 fps、915 幀、視訊 30.5 s，AAC 48 kHz 雙聲道；容器長度渲染檔 30.522 s、交付檔 30.528 s。響度（ffmpeg ebur128，`peak=true`）：兩支渲染檔 −14.2 LUFS、true peak −1.3 dBFS；兩支交付檔 −14.2 LUFS、true peak −1.0 dBFS。成片聲音只有母帶歌曲，生成片自帶音軌全部靜音。

## Session Work And Decisions

時間為當日本地時間。使用者原話逐字摘自 `outputs/ai-city-takeover/logs/decisions.md`（當日共 19 條）。

| 階段 | 時間 | 做了什麼 | 使用者原話 |
| --- | --- | --- | --- |
| 接手 | 00:20 前 | 先前「分工並行 (Recommended)」被取代；EP01 改由 Claude 全權負責。Codex 的 ACE-Step 候選 r4、A01-v2、C-v1、四段新聞圖形、storyboard 原樣保留，只作審查對象與備選素材 | 「你别管codex,我觉得他没做好」 |
| 歌曲 v2 | 00:25–01:08 | ElevenLabs Music `music_v2`（`elevenlabs-direct` MCP）三輪：take 1、2 念白段無人聲而退回，take 3（`adAwLxlOTRPdVH4Pq0x6`）副歌兩遍完整；再局部重生成純伴奏並保留 take 3 副歌（`pQ32FmBFhBW3qmGDofjz`）；念白用 ElevenLabs TTS（Stella，`BqljjWyTnrioXPCNkCd4`，`eleven_v4`）；混成 `IRIS-01-v2.wav` | 「我希望全自动别要我点击」「主歌改半唱半念，再试 (Recommended)」「保留第 3 版副歌，其餘補念白 (Recommended)」「A · Stella」「可以，往下做分鏡」 |
| 分鏡與參考包 | 01:12–01:52 | 10 張關鍵幀（Codex CLI `image_gen`）、分鏡 v2.1（`board.md`，SHA `da739a8451f16d66285542a1107c332777dcff3154985555db09ee4c4b9d91b6`）、動態分鏡 a1–a9、`preview-approval.json`（12 項） | 「認可，開始生成」：授權即夢 7 個 unit（S1、S3、S5、S7、S8a、S8b、S9a），上限約 2,500，每鏡已知失敗最多重做 1 次 |
| v2 付費生成 | 02:05–03:57 | S3、S5（FAIL）、S5r、S7、S1、S9a；S8a（FAIL）→ S8ar（FAIL）；S8b 參考上傳失敗 → S8b2（FAIL）→ S8br（FAIL）。每支出片先過 Gate 再送下一支 | 「用第一版 (Recommended)」「認可，生成 S8b (Recommended)」「認可修復參考，重做一次 (Recommended)」「用 S8b2 (Recommended)」 |
| 成片 c1 | 04:01–04:04 | motion-kit＋HyperFrames 合成並渲染；S2 沿用 Codex 時期的 A01-v2，S4、S6、S9b 為靜幀加 motion-kit | 「2s这里没有睁眼的过程是为什么,衔接很弱.后面人物表现一直很弱,唱歌也是」 |
| v3 表演修訂 | 05:12–06:49 | 6 張表演靜幀（K1c、P5、P7、P8a、P8b、P8c）、預覽頁 `review/v3-preview.html`、`preview-approval-v3.json`（13 項）與 `preview-approval-v3-S1.json`（`identity_waivers: ["IRIS"]`）；S1v3、S8av3、S8bv3（上傳失敗）→ S8bv3b、S5v3、S7v3 | 「S1 睁眼＋副歌＋S5/S7 反應 (Recommended)」「冷靜但活著 (Recommended)」「認可，S1 用原生首尾幀 (Recommended)」「用 S8av3，晚 2 幀 (Recommended)」「用 S8bv3b (Recommended)」 |
| 成片 c2 | 約 06:50–06:58 | 換入 S1v3、S5v3、S7v3、S8av3、S8bv3b；S1／S2 剪點由 2.867 s 後移到 3.367 s；S7 斷線移到 y=820、戳記限在安全區 | 「节奏变快了,这个还不如上一版」「我们需要讨论下怎么做这个视频,我感觉走远了」「回到原作做法 (Recommended)」「照這樣改 (Recommended)」「先把specs写好,作者是怎么做的,我们要怎么做」 |
| spec 與交接 | 約 07:00 起 | 寫 spec 草稿（檔案最後修改 08:06:52）；主會話回報經兩輪獨立審查（審查報告不在倉庫內，本記錄未核對）；c3 未動工 | 「给prompt.我开新的session」 |

## Paid And External Effects

**即夢 Seedance 2.0 VIP 1080p**（canonical `submit_once` 加一次性 permit；帳本 `gen/ledger.json`、`gen/ledger-v3.json`）：

| 範圍 | 計費次數 | 積分 | 確認狀態 |
| --- | --- | --- | --- |
| v2 | 10 | 1,815（6×198＋3×165＋132） | 已確認：UI 餘額 67,645 → 65,830 |
| v3 已確認 | 2（S1v3 198、S8av3 165） | 363 | 已確認：65,830 → 65,467（06:18:40 讀數） |
| v3 待確認 | 3（S8bv3b 165、S5v3 198、S7v3 198） | 預計 561 | **待確認**：沒有後續讀數，預期餘額約 64,906 |
| 合計 | 15 | 約 2,739 | 其中 561 待確認 |

- **2 次參考上傳失敗，`known_no_effect`，不計費**：S8b（03:34，`gen/S8b/project/state/paid-provider/submits/343681b7e8df10195c6a6eae135f799919a2d366cbae4e8b4047b813047d02e2.json`）與 S8bv3（06:17，`gen/S8bv3/project/state/paid-provider/submits/9f5a0c11c5e9ea6f3d3facbcfcea30df546169cf58122901caccfb99cfb72c05.json`）。兩份收據的 `external_effect_id` 都是 `null`。餘額鏈佐證：S8b 前後都是 66,127；S8bv3 之後的 65,467 恰等於 65,830 − 198 − 165。其後的 S8b2、S8bv3b 是請求逐項比對相同的新 attempt。
- **ceiling 不等於花費。** v2 的「2,500 用完」是 10 次送出 × operator ceiling 250，實際扣 1,815。v3 的 ceiling 是 10 次／1,850，已用 5 次計費送出。
- **`observed_balance` 是 UI 讀數，可能過期。** S7、S1、S9a 的 `node-created.json` 讀到 67,447，比前一個讀數 67,249 還高，不符合單調扣款，應是頁面未更新的舊值；只有符合連續扣款鏈的讀數才能當證據。
- **ElevenLabs**：當日 1,726 credits（帳號 1,162 → 2,888）：Music take 1＋2 共 762、take 3 為 381、局部重生成加 TTS 共 583。Voice Isolator 分離副歌約 7.4 s，讀數 2,888 → 2,888，結算**待確認**。
- **Codex 階段即夢 594 積分**（A01 兩版與 C，2026-10-30）屬更早會話，不在上表。
- **Codex CLI `image_gen`**（`motion-kit/tools/codex_plate.py`）：16 張關鍵幀與表演靜幀（01:12–01:31 十張、05:12–05:15 六張）。v3 六張在 `logs/ledger.md` 與 `logs/runs.md` 標為訂閱額度、不計積分；前十張沒有單獨的 ledger 或 runs 列，同一工具，費用性質依此推定，未另行驗證。
- **遠端狀態**：每個 unit 用 CDP 在即夢 IRIS 畫布（project `829df260-5a63-4f0d-8265-8353dc693b3b`）新增空白影片節點，共 16 個不同節點（S8b、S8b2 共用一個），建立時 `generation_POSTs` 為 0。每次送出前，參考圖與乾聲會上傳到即夢；沒有任何發布或對外分享。

## Per-Shot Gate Results

15 次計費送出各有一份 `qa/gate-<unit>/post-media-gate.json`，每份記載的 MP4 路徑與 SHA 都與磁碟位元組相符。15 次送出與 Gate 檔的時間順序已核對：每份 Gate 檔的 mtime 都早於下一次送出的 `intent_at`，沒有整批生成後補查。

| unit | 時長／積分 | Gate | 判定重點 | 處置與成片 |
| --- | --- | --- | --- | --- |
| S3 | 6 s／198 | PASS | 走道前推到紅門縫 | c1、c2 |
| S5 | 6 s／198 | FAIL | `camera`：推近末段加速，與封存的靜態機位不符 | 不用；唯一一次修復為 S5r |
| S5r | 6 s／198 | PASS | 固定機位 | c1 |
| S7 | 6 s／198 | PASS | | c1 |
| S1 | 6 s／198 | PASS | 只閉眼 | c1 |
| S9a | 6 s／198 | PASS | 原生首尾幀 K4 → K9e | c1、c2 |
| S8a | 5 s／165 | FAIL | `lip-sync`：開唱前 0.2 s 張嘴露齒、唱完雙唇只合到一條縫，兩項都在成片窗口外；窗口內開口在 ±1 幀內 | 使用者選用（窗口 clip 0.467–4.167 s），c1 |
| S8ar | 5 s／165 | FAIL | `lip-sync`：「I」「outside」開口晚 4–8 幀 | 不用 |
| S8b | 4 s／0 | 無 MP4 | 參考上傳失敗，`known_no_effect` | 另開 S8b2 |
| S8b2 | 4 s／132 | FAIL | `lip-sync`：「outside」晚 4–8 幀；參考 3.40 s 起無聲，閉嘴在約 3.73 s，超出 3 幀容許約 7 幀 | 使用者選用（clip 0.367–3.70 s），c1 |
| S8br | 5 s／165 | FAIL | `lip-sync`：約 2.2 s 後閉嘴，後半句「I just looked outside」沒唱 | 不用 |
| S1v3 | 6 s／198 | PASS | 眼瞼約 2.4 s 抬起、2.83 s 半睜、約 3.3 s 全睜 | c2 |
| S8av3 | 5 s／165 | FAIL | `onsets`：「I just」開口晚 4–5 幀（標準 ±2）；`pause-20.57-20.73` 收口晚約 0.13 s；`performance` PASS | 使用者選用，入點 0.5333，c2 |
| S8bv3 | — | 無 MP4 | 參考上傳失敗，`known_no_effect` | 另開 S8bv3b |
| S8bv3b | 5 s／165（待確認） | FAIL | `onsets`：「outside」沒重新張嘴；`pauses-and-closing`：兩處停頓沒收嘴，約 25.70 s 前未閉合；`performance`：望向城市在剪點之後 | 使用者選用，入點 0.5667，c2 |
| S5v3 | 6 s／198（待確認） | PASS | 約 1.2 s 皺眉、1.5–1.8 s 鎖定窗外 | c2 |
| S7v3 | 6 s／198（待確認） | PASS | 眼睛跟薄片再回鏡頭 | c2 |

15 支 MP4 的 SHA-256（皆已與 Gate 檔及磁碟位元組核對）：

```text
S3      4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7
S5      ce189514d1189865c8cecc1a42d4d5e2b12dc83a26d5f2f44a5f71c2c1b93c16
S5r     3f2224254e9453161301f7796dbf1a022d2dbfdaf15080d19ebe1a3f13f559dc
S7      1921cdec15b928919c99454ccafb0411916d21bfcc2780688904471d103ee9b7
S1      3e0b6ca44ab1c88889d8d1b7fd997c69d633dd9105182f670f0c901ed6d8f72b
S9a     9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728
S8a     8631894f86f4bedd10bdc8b7f41402e8236405a43499a0a032da6f5bcf21eda7
S8ar    474fc1db7ff5cd98921fd06f9005a13cc9ca264a7999ef60b83039e612dd1704
S8b2    098b41979918ca42aed75934cf9b99783da5ddd08868563c27f9b4852075c148
S8br    1baeab8a189278bd9e3221e282ce5dcef11ee46197fcff1dad90d467a5f11373
S1v3    4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5
S8av3   20e7642b073ab84910c820d75b3021fd5a0a2207b991f5a67edd485b42e3952f
S8bv3b  83576dce4c71fe88cdda4e2f93679e9a58f6cd564214dbc681f04bd69443a4b4
S5v3    a819d930a95a9c2cb876b272bbfbb766665338a8c8296d3e5e0fd7d484a26734
S7v3    3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21
```

### Lip-Sync Attempts

六支對嘴片全部 Gate FAIL，其中 S8a 第一版、S8b2、S8av3、S8bv3b 是使用者當次決定放進成片（`qa/gate-S8a|S8b2|S8av3|S8bv3b/user-decision.json`），Gate 判定都不變。判定標準由 Agent 起草，隨 board v2.1（`board.md`「S8a 對嘴測試」，含 ±2 幀與「仍 FAIL 就改用不對嘴的覆蓋」備案）經使用者認可，付費前依實測乾聲時間軸修訂並封存於 `s8a-lipsync-amendment.md`（SHA `48757062f2b754358827cecaf699ccd1097d18881a42431be899af273ec8009f`），v3 兩鏡的標準另封存於同檔「v3 表演重做」段。備案曾列入使用者的選項（`qa/gate-S8a/user-decision.json` 的 `alternatives`），使用者選第一版，S8b 因此是在 S8a Gate 仍為 FAIL、經使用者當次決定後才送出。

| 嘗試 | 乾聲參考 SHA-256 | 相對前一版的改動 | 結果 |
| --- | --- | --- | --- |
| S8a | `c70ec5a59777795a6ac608e17803be6b94ee24842d68801718cf6226c3241dfe`（0.2 s 前置靜音） | 首次 | 窗口內開口準，窗口外兩項不合格 |
| S8ar | `7a86f6695d11ac7a0a443cbb9c88528cbede5f1ac222943f59012120753b155e` | 唯一變數：去掉前置靜音（prompt 只隨參考改說法） | 開口晚 4–8 幀 |
| S8b2 | `8b391077d80ef5b967afb5163ee2896a839f7efd0fe137064ddb7ccc61a4b16b`（無前置靜音） | 與上傳失敗的 S8b 同請求 | 句尾晚 |
| S8br | `9ba9442d9d7c516f41251e410c8c8540cd0bd339d4923b08f0405e1a5326318a`（0.2 s 前置靜音） | 唯一變數：加前置靜音 | 約 2.2 s 後閉嘴不唱 |
| S8av3 | 同 S8a 的參考位元組 | 新增表演靜幀 P8a、prompt 改寫具體的戲 | 一個開口與停頓不合格；表演 PASS |
| S8bv3b | 同 S8br 的參考位元組 | 新增 P8b、P8c、prompt 改寫 | 停頓、「outside」、閉嘴不合格；表演放開 |

**這六次不是受控比較**：每次改動不只一個變數（前置靜音、窗口切點、prompt、表演靜幀同時動），判定標準隨輪次另行封存，每個條件只有一次抽樣，同一鏡的版本是同一條產物鏈。不能從這六次推出對嘴方法的因果結論。已核對的一個測量事實：副歌第一個「I」依 `song/isolation/S8a-vocal-ref-timeline.json`（30 fps RMS，首個 onset frame 6）約從 18.60 s 開唱，而 `timing/words.json` 記 18.912 s，早約 0.31 s，所以以 `words.json` 判唱段時間不可靠。

## Review Films c1 And c2

| | c1 | c2 |
| --- | --- | --- |
| S1／S2 | S1（閉眼）0–2.867 s，S2 2.867–4.80 s | S1v3（睜眼）0–3.367 s，S2 3.367–4.80 s |
| S5 | S5r | S5v3，入點 1.0 |
| S7 | S7 | S7v3，入點 1.4；斷線移到 y=820；戳記 2 個 |
| S8a | S8a 第一版，入點 0.4667 | S8av3，入點 0.5333（使用者選的晚 2 幀） |
| S8b | S8b2，入點 0.3667 | S8bv3b，入點 0.5667 |
| 同 | S2＝`outputs/ai-city-takeover/ep01/shots/A01-v2.mp4`（SHA `850b3807757e570dc59c2a6af96fcf930d8689322408e11f1be81db2c5adae1c`，Codex 時期）、S3、S9a；S4、S6、S9b 為靜幀加 motion-kit | 同 c1 |
| `qa.py` | 10 個剪點 ±0 幀、12 個圖形時機 ±1 幀內，無閃爍、頻閃、跳幀或離群幀 | 相同 |
| 使用者意見 | 睜眼銜接弱，人物與唱歌表現弱 | 節奏變快，不如上一版 |

- **`qa.py` 全過不是節奏判定。** c2 全部技術項通過仍被使用者否定。`qa/film-c*/report.json` 的 `motion_per_bar` 本次直接重算：c1 合計 35.677、c2 合計 31.612；第 1、2、3 小節上升（0.906→1.987、1.990→2.743、2.959→3.266），第 6–10 與 14 小節下降（例如第 8、9、10 小節 3.108→2.103、5.792→1.706、3.387→2.018），副歌第 11–13 小節小幅上升，第 4、5、15、16 小節不變。這個指標升降並存，不能單獨解釋「节奏变快」，使用者的感受與它的對應沒有被驗證；c2 同時改了五鏡內容、S1／S2 剪點與 S7 圖形位置，成因沒有被隔離。
- **音畫是使用者的**：Agent 不能聽音。c1 拼接記錄的 `audio` 欄是 `NOT_EVALUATED`，c2 的寫明對嘴聽感歸使用者；`audio_understand` 沒有出現在任何 Gate 或拼接記錄中。對嘴觀感、S8b 結尾、接點上的聲音只有使用者能判，而使用者的意見針對節奏與表演，沒有留下對聲音或對嘴的明確接受或否決。
- **c1、c2 無法由 `comp/` 目前內容重現。** `ep01/v2/comp/` 未追蹤，且 08:32 之後已被 c3 工作改動；c1、c2 只能靠成片 SHA 與 `qa/film-c*/report.json` 識別。

## Direction Change And Draft Spec

`docs/superpowers/specs/2026-11-02-iris-ev-method-realignment.md`（729 行）自述「狀態：草案，待使用者審閱」。使用者的選項回覆「回到原作做法 (Recommended)」「照這樣改 (Recommended)」支持**方向**（圖形與排版為主、人物為輔；對嘴照作者方法，不再為對嘴整鏡重生成；EP01 以 c1 為底收尾，不再付費生成），**不等於批准 spec 全文**。`decisions.md` 的這段方向文字是 Agent 對選項回覆的整理，選項問題原文不在倉庫內，使用者逐字確定的只有那五句原話。第 6 節五項待決，全部未批准：

| 編號 | 待決 | 備註 |
| --- | --- | --- |
| D1 | 對嘴 prompt 能否用引號寫出確切英文歌詞 | 與現行「prompt 純中文」規則衝突（`docs/canvas-continuous-production.md#prompt-language-and-character-identity`），未決前該規則照舊 |
| D2 | 下一集前做對嘴方法試驗：對照組（S8a 第一版）加 A、B、C 三種，各事先登記 2 支，共 6 支 4 秒片 | 約 800 積分以內；A、B、C 需要 D1，C 需要 D3 |
| D3 | 試驗是否含即夢 Seedance 2.5 | 先出 480p |
| D4 | 每集付費上限 | 建議 3–5 支主鏡加最多 2 支修復，約 1,400 積分 |
| D5 | 唱的鏡頭的逐鏡檢查改成「Agent 量、使用者判」 | 修訂現行 Gate 做法，須使用者同意才生效 |

草稿第 3.2 節「我們偏在哪」是**本會話的有界觀察**，不是通用規則，也沒有被受控實驗隔離：EP01 跳過原定的對嘴試驗而直接以副歌當試驗場；對嘴 prompt 是中文劇本式長描述，沒有引用歌詞（S8a 的 prompt 為純中文 423 字，`gen/S8a/pre-submit-lint.json`）；S8b 系列的參考從第一遍「outside」尾音中間起唱；Agent 自己逐幀判對嘴；EP01 合成裡沒有跟著音軌動的 punch／impact；c2 改 S2 長度前沒有量節奏。草稿 §2 的作者做法來自作者公開頁面（claudia.gallery），本專案未實測，作者用的是 Seedance 2.5 720p，本專案用即夢 Seedance 2.0 VIP 1080p，行為不保證相同；本次也沒有重新抓取這些頁面。

本次對草稿數字的核對：6 支對嘴片共 957 積分（165×5＋132）、v3 共 924、c1 副歌四小節動態 0.84／1.78／0.84／1.63（其中兩小節是全片最低）、第 1 小節 0.91→1.99、S2 由 1.93 s 縮到 1.43 s，皆與檔案相符。**一處不符，請主會話修正草稿（本次未改）：**

- 草稿 §3.1、§4.5 寫「這次分離取自成片混音，念白『cached.』延續到約 18.8 s，所以 18.6–18.8 s 可能混有念白」。實測 Voice Isolator 的輸入 `song/isolation/chorus-18.6-26.0-bed.wav` 與 bed mp3（`song/bed-01/music__20261102_004125.mp3`）18.6–26.0 s 片段的相關係數為 0.99999994（lag 0），與成片混音同段只有 0.961（lag −96 samples）、電平也不同；`gen/S8a/source-selections.json` 的 `derived_from` 同樣指向 bed。所以乾聲參考是從不含 Stella 念白的 bed 分離的，草稿「念白殘留在參考裡」的前提不成立，「從混入念白之前的音軌重新分離」在這個意義上 EP01 已經是這樣做的。念白尾巴確實存在於成片混音：`song/mix/vo-stem.wav` 在 18.30–18.60 s 平均 −22.5 dB、18.60–18.80 s 平均 −24.8 dB，18.80 s 之後約 −81 dB，這影響的是成片母帶的重疊，不是參考乾聲。

## Verification And Evidence

| 項目 | 方法 | 結果 |
| --- | --- | --- |
| spec、四支成片 | `sha256sum` | 與主會話提供的值全部相符 |
| 15 支生成 MP4 | 重算 SHA 比對 Gate 的 `artifact_sha256` 與路徑 | 15／15 相符 |
| 預覽認可 | 重算五份認可檔全部 `preview_artifacts` | 36／37 相符；不符的是 `preview-approval-S8b.json` 列的 `review/S8b-preview.html`（見 Evidence Boundaries） |
| 帳本 | 讀 `gen/ledger.json`、`gen/ledger-v3.json` | v2 共 11 筆（10 submitted、1 `known_no_effect`）；v3 共 6 筆（5＋1），與 `logs/ledger.md` 一致 |
| 餘額鏈 | 17 份 `node-created.json` 的 `observed_balance` | v2 1,815 與 v3 前兩筆 363 相符；S7、S1、S9a 三個讀數過期（見上） |
| 送出與 Gate 順序 | `intent_at` 對 Gate 檔 mtime | 14 對（有 MP4 的送出與其下一次送出）全部 Gate 在前 |
| 成片規格與響度 | `ffprobe`、`ffmpeg ebur128` | 如 Core Artifacts |
| 每小節動態 | 直接讀兩份 `report.json` | 如 Review Films |
| 乾聲來源 | 互相關與電平比對 | 如 Direction Change And Draft Spec |
| Git 狀態 | `git status`、`git ls-files`、`git log --since` | 全部未追蹤，無 IRIS commit |
| 記憶檢索 | `experience` scope 一次檢索（索引 fresh） | 沒有關於「參考乾聲驅動對嘴」的既有 Learning Claim |

**沒有驗證**：Gate 判定內容（沒有重看影格、沒有重跑 `lipsync_review.py`，只核對 MP4 身份與時間順序）；`motion-kit` 與 `gen/`、`qa/` 腳本的程式正確性與測試；兩輪 spec 獨立審查的內容；草稿引用的外部頁面；任何費用結算；人類以正常速度帶聲音觀看的結果。

## Evidence Boundaries

- **Agent Gate 不是人類接受。** 15 份 Gate 的 `authority` 都是 `Agent per-shot gate on the exact fetched MP4`，且全由主會話自行裁決，早於獨立角色 `shot-gate-reviewer`（commit `b0cb4dec`，07:41:55，晚於最後一份 Gate 的 06:49）。每份 Gate 的 `not_evaluated` 都列「human 1.0x viewing」。
- **FAIL 加使用者選用，不是 PASS。** 四次使用者處置都只是對 FAIL 判定的當次決定，Gate 判定不變。
- **v3 的表演 PASS 不等於使用者認可表演。** S1v3、S5v3、S7v3 的 PASS 與 S8av3、S8bv3b 的 `performance` 判定只是 Agent 的觀察；使用者沒有對 v3 表演給出結論（c2 的意見是節奏與方向）。草稿稱「表演改善有效」也出自 Agent。
- **技術 PASS 不是節奏或觀感判定。** `qa.py` 檢查剪點、圖形時機、閃爍、頻閃、離群幀與規格。
- **預覽認可的輸入覆蓋不完整（以現行標準看）。** 第一輪 `preview-approval.json`（12 項）不含身份圖 `CF-ID7b-a.png`（`e19d9473c40c19d4834554055298351e1bdea3f856a6de76b057b575fcb563ea`）與 S8a／S8ar 的乾聲參考。逐 unit 比對 `source-selections.json` 與各 unit 的 `preview-approval.json`：S5、S5r、S7、S1 各有 1 個輸入（ID7b），S8a、S8ar 各有 2 個（ID7b、乾聲）不在認可的 `preview_artifacts` 內；S3、S9a 與 S8b 之後的各 unit 全部涵蓋。這六次送出時的 prepare 沒有逐項比對；「每個 resolved input SHA 必須屬於認可集合」這條檢查在會話中途才出現在工作區（handoff 第 3 節稱 peer session 剛加入、尚未 commit，S8b 起的認可檔就都列全），並於 commit `20e71ba3` 落地（見 [fresh-generation-reference-gaps](2026-11-02-fresh-generation-reference-gaps.md)）。這不改變已發生的付費，也不表示使用者沒有認可整包（「認可，開始生成」），但這六次送出不符合現行的 exact input binding。ID7b 是先前會話定稿的身份參考（`decisions.md` 2026-10-30 使用者選「固定，只重出 ID7」；[T01 記錄](2026-10-30-iris-t01-readable-takeover.md)記 ID7b 已定稿）；ID7b 本身是否有單獨的使用者認可，本次沒有找到明確紀錄。S8a、S8ar 的乾聲參考在送出前未見交使用者試聽的預覽頁：認可頁 `index.html`（01:49）早於乾聲分離（02:31），第一個播放分離乾聲的預覽頁是 S8b 的 `review/S8b-preview.html`。
- **被覆寫的認可頁面。** `preview-approval-S8b.json` 記的 `review/S8b-preview.html` SHA 是 `8295c08c88d3f526dbee4b8191b191e92a2d098deea2d1fc74f78d432ec41eb3`，該頁在 03:44 為修復預覽改寫，現在的位元組是 `preview-approval-S8br.json` 記的 `4f8021a22ca4f5573b4da0a0e3662665fbf6536492a4ac8116b1bbc4fe3895ca`。第一次 S8b 認可時使用者看到的頁面無法逐位元組重現；認可檔列的輸入媒體（K8b、ID7b、乾聲）都相符。
- **`director-coverage.json` 不能當 c2 的證據。** c2 拼接記錄寫「S1／S2 時長已同步為 3.367／1.433」，但本次讀取時該檔已是 2.867／1.933（mtime 08:32:56，與進行中的 c3 工作時間一致；SHA `3eb70a235d9adc8487af2f8249936a523464ee1df53b2fbebc74e556d9fd9bad`，與五份預覽認可的 `coverage_hash` 相同）。
- **費用層次分開：** ceiling（operator 預設上限）、UI `observed_balance`（讀數）、帳單（未取得）是三件事；561 與 Voice Isolator 一律標「待確認」。
- **外部來源與本會話觀察分開：** 草稿 §2 是外部頁面的轉述；§3 是本專案觀察；§4–§5 是提議。

## Superseded Or Displaced Prior Claims

下列舊記錄（多為 Codex 會話所寫，皆未追蹤）依使用者決定保持原樣，**沒有被加上 supersession notice**，所以獨立閱讀時仍會呈現舊的待辦；請以本表為準。歷史測量與證據本身仍有效。

| 舊記錄 | 被取代的現行宣稱 | 取代它的證據 |
| --- | --- | --- |
| [2026-10-31-iris-bgm-and-sung-source-repair.md](2026-10-31-iris-bgm-and-sung-source-repair.md) | 「當前候選」是 ACE-Step r4 `IRIS-01-Music-and-Hook-preview.wav`（SHA `9e007d2a…`），音樂品質與真唱感待試聽 | 使用者「你别管codex…」與「可以，往下做分鏡」：EP01 的歌改為 `IRIS-01-v2.wav`（`d7e2107d…`），r4 只作備選 |
| [2026-10-31-iris-local-lyrics-guided-repair.md](2026-10-31-iris-local-lyrics-guided-repair.md)、[2026-10-30-ace-step-local-iris-audition.md](2026-10-30-ace-step-local-iris-audition.md)、[2026-10-31-iris-google-audio-listening.md](2026-10-31-iris-google-audio-listening.md) | 同一條 ACE-Step 歌曲候選鏈（G、r4）的待試聽狀態與 Gemini 聽音觀察，指向的已不是 EP01 的歌 | 同上 |
| [2026-10-30-iris-ep01-patchright-and-source-progress.md](2026-10-30-iris-ep01-patchright-and-source-progress.md)、[2026-10-30-captioned-music-preview-continuation.md](2026-10-30-captioned-music-preview-continuation.md)、[2026-10-30-suno-native-xdotool-restart.md](2026-10-30-suno-native-xdotool-restart.md) | 「等 Suno 人工驗證取得真實歌曲」「整片缺歌曲、B 演唱／對嘴」的 Remaining Work，以及經 `CompositionSpec → ResolvedTimeline → HyperFrames` 合成的計畫 | 歌曲不再走 Suno；v2 由 motion-kit 加 HyperFrames CLI 直接合成，沒有 canonical `ResolvedTimeline`；S2 沿用 A01-v2（`850b3807…`）。Suno 舊請求的 `NOT_CONFIRMED` 狀態**沒有**被本會話改判或解決 |
| [2026-10-30-iris-t01-readable-takeover.md](2026-10-30-iris-t01-readable-takeover.md) | 「EP01 等待其歌曲」的下一步 | 同上；T01 dev7 候選本身的結論不變 |
| `outputs/ai-city-takeover/logs/status.md`（非 record） | 2026-10-30 的「歌曲阻塞…不能繼續付費視頻」「EP01 延後」 | 本記錄 |

相關但不被取代的規則來源：[drift-root-cause-rules-and-gate](2026-11-02-drift-root-cause-rules-and-gate.md)（預覽認可門禁）、[preview-approval-and-identity-waiver-gate](2026-10-30-preview-approval-and-identity-waiver-gate.md)（`identity_waivers`）。

## Remaining Risks Or Next Work

- **待確認費用**：即夢 561 積分（S8bv3b、S5v3、S7v3）與 ElevenLabs Voice Isolator 約 7.4 s。要確認須讀下一個餘額並套回扣款鏈，不要用單一 UI 讀數。
- **全部未提交、只存本機**：`ep01/`、`motion-kit/` 的新檔與修改（`runtime.js` 的 image-sequence 底片與序列化渲染佇列等）、spec 草稿、`logs/` 改動。媒體位元組被 `.gitignore` 排除。
- **沒有獨立審查**：`motion-kit/src/runtime.js`、`ep01/v2/comp/`、`gen/unit.py`、`gen/operator.py`、`qa/*.py` 的 code-reviewer／verifier 因額度中斷沒有結果（出自 handoff 第 11 節，本次未另行核對）；15 份 Gate 全是自審。沒有任何 Harness focused／related／full receipt。commit 前必須補。
- **spec 草稿**：D1–D5 待使用者決定；上述乾聲來源不符待修正；c3（草稿 §5）細節也只是草稿。
- **舊記錄與日誌未對帳**：見上表，需主會話決定是否授權補 notice，或更新 `logs/status.md`。
- **聲音與對嘴觀感**：沒有使用者對 c1／c2 聲音或對嘴的明確接受或否決。
- **EP01 不再付費生成**是 `decisions.md` 記錄的最新方向；任何新的付費影片生成都需要使用者新的授權，D2 試驗也一樣。

## Agent Guardrails

- 不把 c1、c2、任何 Gate PASS、`qa.py` 全過當成 Final Acceptance、發布或使用者認可；不把「FAIL 加使用者選用」寫成 PASS。
- 沒有使用者新的明確決定，不對 EP01 做新的付費影片生成，也不整鏡重生成來修對嘴；草稿的 D1–D5 在批准前都不是規則，`prompt` 純中文規則照舊。
- 未結算的費用一律標「待確認」；餘額讀數要套回連續扣款鏈再用。
- 要重現 c1、c2，用成片 SHA；不要假設 `comp/`、`director-coverage.json` 的目前內容等於當時狀態。
- 預覽認可要列全每一個 resolved input 的 SHA，且不要原地改寫已被認可的預覽頁面（另存新版本）。
- 不要對工作區做 `git clean` 或覆寫 `outputs/ai-city-takeover/ep01/`；被 `.gitignore` 排除的媒體未見其他備份。
- Codex 時期的產出原樣保留，不刪不改。
- 對嘴與表演的觀察只是本會話的有界經驗，不外推成 Provider 或模型的一般結論。

## Learning Assessment

`record-ai-video-session`：recorded（事後重建）。`distill-ai-video-learning`：**no_candidate**，不建立 Learning Claim、不修改 Skill／Policy／Gate、不標 `ADOPTED`。

- 檢索 `experience` scope，沒有關於「參考乾聲驅動對嘴」的既有 Learning Claim 可更新。即夢「參考上傳失敗 → `KNOWN_NO_EFFECT` → 新 attempt」在專案歷史上至少有六次上傳階段先例與既定處理（例如 [jieshi-jimeng-mini-upload-stop](2026-10-26-jieshi-jimeng-mini-upload-stop.md)、[yanshengyuan-three-film-first-shot-checkpoint](2026-10-25-yanshengyuan-three-film-first-shot-checkpoint.md)），本次兩次是同型再現，沒有新規則。
- 六支對嘴片雖有精確身份，但不是受控比較（見 Lip-Sync Attempts）。前置靜音的效果互相矛盾：S8ar 去掉、S8br 加上，兩者都未過；有前置靜音的 S8a 在窗口內三個開口都準，S8av3、S8bv3b 各準 2 個、錯 1 個，S8br 後半句沒唱；無前置靜音的 S8b2 準 2 個、錯 1 個，S8ar 的「I」「outside」都晚。命中數互有高低，看不出前置靜音的單獨效果。最多是 `CONTESTED`，達不到 admission，也不值得為此留一個空殼候選。
- v3 表演改善只有 Agent 的 Gate PASS，使用者沒有結論；prompt 與參考靜幀同時改動，無法歸因。c2 節奏變快是單例，五項改動並存且沒有對照量測。
- 尚缺的是草稿 D2 那種受控且重複的試驗：判定標準與窗口事先登記、參考乾聲核對零延遲、每種方法至少兩次抽樣、以使用者看疊歌審看片作為人類證據層。D2 未批准、未執行。若日後執行，請以 `media_experiment`、`learning_eligibility: eligible` 與 Evidence Index 記錄；本記錄標 `ineligible` 的原因是上述混淆，不是證據不存在。
