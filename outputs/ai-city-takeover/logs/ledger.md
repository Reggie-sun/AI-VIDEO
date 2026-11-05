# Ledger（每次付費或額度呼叫一行）

| 時間 | 服務 | 用途 | 單元/請求 | 預估 | 實際 | 結果 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-30 15:3x | Suno v6（SunoMusicService → CLI） | T01/第二階段配樂 | request `7026512f-fb70-5e1b-9420-68039d73f70b` | 10 credits | 0 | 未提交：doctor `captcha_preflight: required: true`，依規則不自動求解；dry-run 已通過；改請使用者於官網生成 |
| 2026-10-30 18:4x | 即夢 Seedance（Codex 會話） | EP01 A01 第一版 | 見 `ep01/live-binding/` | — | 198 積分（餘額差） | 已取回；構圖偏離，`reject_video_generation` |
| 2026-10-30 19:0x | 即夢 Seedance（Codex 會話） | EP01 A01 第二版 | 見 `ep01/a01-repair-binding/` | — | 198 積分（餘額差） | 已取回；逐鏡 Gate PASS |
| 2026-10-30 19:3x | 即夢 Seedance（Codex 會話） | EP01 C 室內 | 見 `ep01/c-binding/` | — | 198 積分（餘額 68189→67595，三次合計 594） | 已取回；逐鏡 Gate PASS |
| 2026-10-31 05:3x | Google Gemini 音訊分析（Codex 會話） | 歌曲候選 r4 聆聽 | 見 `ep01/audio/iris-google-listening-20261031/` | 內部上限 USD 0.05 | 待結算 | 觀察可用 |
| 2026-11-02 00:25 | ElevenLabs Music v2（elevenlabs-direct MCP） | EP01 歌曲 take 1 | song_id `9IWJUxax8CJKmqQF9nBt` | ≤2 次 × 30 s | 兩次合計 762 credits（帳號 1,162→1,924） | 無人聲，退回 |
| 2026-11-02 00:28 | ElevenLabs Music v2（elevenlabs-direct MCP） | EP01 歌曲 take 2 | song_id `EEkHSCJRyecb1l5idA8y` | 同上（預算用完） | 見上列合計 | 只有副歌有人聲，念白段空白，退回 |
| 2026-11-02 00:33 | ElevenLabs Music v2（elevenlabs-direct MCP） | EP01 歌曲 take 3（半唱半念，新上限第 1 次） | song_id `adAwLxlOTRPdVH4Pq0x6` | ≤3 次 × 約 380 | 381 credits（帳號 1,924→2,305） | 副歌完整唱兩遍；前奏、主歌沒有人聲；耳語段和尾奏各缺一句 |
| 2026-11-02 00:41 | ElevenLabs Music v2 局部重生成 | EP01 純伴奏＋保留 take 3 副歌（新上限第 2 次） | song_id `pQ32FmBFhBW3qmGDofjz` | 約 380 | 與下列語音合計 583 credits（帳號 2,305→2,888） | 副歌以外無人聲，副歌兩遍保留 |
| 2026-11-02 00:43–00:52 | ElevenLabs TTS eleven_v4（elevenlabs-direct MCP） | IRIS 選聲試聽 3 段＋念白 4 段 | voice Stella `BqljjWyTnrioXPCNkCd4` | 約 400 | 見上列合計 | 75 字全在；本日 ElevenLabs 合計 1,726 credits（1,162→2,888） |
| 2026-11-02 02:05 | 即夢 Seedance 2.0 VIP 1080p（Claude 會話，canonical submit_once） | EP01 v2 S3 走道前推 6 s | `ep01/v2/gen/S3`，attempt `iris-v2-s3-source-001` | 上限 250 | 198 積分（餘額 67645→67447） | 已取回；逐鏡 Gate PASS |
| 2026-11-02 02:14 | 即夢 Seedance 2.0 VIP 1080p | EP01 v2 S5 窗前旁觀 6 s | `ep01/v2/gen/S5`，attempt `iris-v2-s5-source-001` | 上限 250 | 198 積分（67447→67249） | 已取回；逐鏡 Gate FAIL（鏡頭末段加速推近，未收穩） |
| 2026-11-02 02:29 | 即夢 Seedance 2.0 VIP 1080p | EP01 v2 S5r（S5 唯一一次有界修復：固定機位） | `ep01/v2/gen/S5r`，attempt `iris-v2-s5r-source-001` | 上限 250 | 198 積分 | 已取回；逐鏡 Gate PASS |
| 2026-11-02 02:32 | ElevenLabs Voice Isolator（elevenlabs-direct MCP） | S8a/S8b 副歌乾聲（歌曲 18.6–26.0 s，7.4 s） | 輸出 `song/isolation/chorus-18.6-26.0-isolated.mp3` | 約 7 s 音訊 | 讀數 2,888→2,888（未見變化，待確認） | 人聲完整，與歌曲時間差約 2 ms |
| 2026-11-02 02:37 | 即夢 Seedance 2.0 VIP 1080p | EP01 v2 S7 離線房間 6 s | `ep01/v2/gen/S7`，attempt `iris-v2-s7-source-001` | 上限 250 | 198 積分 | 已取回；逐鏡 Gate PASS |
| 2026-11-02 02:43 | 即夢 Seedance 2.0 VIP 1080p | EP01 v2 S1 閉眼微距 6 s | `ep01/v2/gen/S1`，attempt `iris-v2-s1-source-001` | 上限 250 | 198 積分 | 已取回；逐鏡 Gate PASS |
| 2026-11-02 02:47 | 即夢 Seedance 2.0 VIP 1080p（原生首尾幀） | EP01 v2 S9a 機櫃門關上 6 s | `ep01/v2/gen/S9a`，attempt `iris-v2-s9a-source-001` | 上限 250 | 198 積分（S5r 起四次合計 792，餘額 67249→66457） | 已取回；逐鏡 Gate PASS |
| 2026-11-02 02:57 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v2 S8a 對嘴測試 5 s | `ep01/v2/gen/S8a`，attempt `iris-v2-s8a-source-001` | 上限 250 | 165 積分（66457→66292） | 已取回；Gate FAIL（開唱前 0.2 s 張嘴、唱完留縫，皆在成片窗口外；窗口內開口時機在誤差內） |
| 2026-11-02 03:11 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v2 S8ar（S8a 唯一一次有界修復：參考從開唱起點開始） | `ep01/v2/gen/S8ar`，attempt `iris-v2-s8ar-source-001` | 上限 250 | 165 積分（66292→66127） | 已取回；Gate FAIL（「I」「outside」開口晚 4–8 幀）；使用者選用第一版 S8a |
| 2026-11-02 03:34 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v2 S8b 第二遍 4 s（使用者認可 S8b 參考包） | `ep01/v2/gen/S8b`，attempt `iris-v2-s8b-source-001` | 上限 250 | 0（參考上傳失敗，未送出生成；known_no_effect 收據） | 未生成；以相同請求另開 S8b2 |
| 2026-11-02 03:39 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v2 S8b2（同一請求的新 attempt） | `ep01/v2/gen/S8b2`，attempt `iris-v2-s8b2-source-001` | 上限 250 | 132 積分（66127→65995） | 已取回；Gate FAIL（句尾 outside 與閉嘴晚約 0.2 s） |
| 2026-11-02 03:5x | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v2 S8br（S8b 唯一一次有界修復：前置 0.2 s 靜音，使用者認可修復參考） | `ep01/v2/gen/S8br`，attempt `iris-v2-s8br-source-001` | 上限 250（用完 2,500） | 165 積分（65995→65830） | 已取回；Gate FAIL（約 2.2 s 後閉嘴不唱，「I just looked outside」沒唱）；不再付費，交使用者在 S8b2/S8br 間選 |
| 2026-11-02 05:0x–05:15 | Codex CLI 內建 image_gen（codex_plate.py） | v3 表演預覽靜幀 K1c、P5、P7、P8a、P8b、P8c | `ep01/v2/keyframes/prompts-v3-performance.md` | 訂閱額度 | 不計積分 | 6 張皆交付，使用者認可（「認可，S1 用原生首尾幀 (Recommended)」） |
| 2026-11-02 05:27 | 即夢 Seedance 2.0 VIP 1080p（原生首尾幀，免附身份圖） | EP01 v3 S1v3 睜眼 6 s（v3 上限 10 次／1,850 積分，`gen/ledger-v3.json`） | `ep01/v2/gen/S1v3`，attempt `iris-s1v3-source-001` | 上限 250 | 198 積分 | 已取回；逐鏡 Gate PASS |
| 2026-11-02 05:35 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v3 S8av3 副歌第一遍 5 s | `ep01/v2/gen/S8av3`，attempt `iris-s8av3-source-001` | 上限 250 | 165 積分（S1v3 起兩次合計 363，餘額 65830→65467，06:18 讀數） | 已取回；Gate FAIL（「I just」開口晚 4–5 幀）；使用者選用並把入點晚 2 幀 |
| 2026-11-02 06:17 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v3 S8bv3 副歌第二遍 5 s | `ep01/v2/gen/S8bv3`，attempt `iris-s8bv3-source-001` | 上限 250 | 0（參考上傳失敗，未送出生成；known_no_effect 收據） | 未生成；以相同請求另開 S8bv3b |
| 2026-11-02 06:19 | 即夢 Seedance 2.0 VIP 1080p（全模態＋副歌乾聲） | EP01 v3 S8bv3b（同一請求的新 attempt） | `ep01/v2/gen/S8bv3b`，attempt `iris-s8bv3b-source-001` | 上限 250 | 預計 165（餘額待讀） | 已取回；Gate FAIL（停頓與句尾閉嘴沒對上）；使用者選用 |
| 2026-11-02 06:36 | 即夢 Seedance 2.0 VIP 1080p（全模態） | EP01 v3 S5v3 看到紅窗 6 s | `ep01/v2/gen/S5v3`，attempt `iris-s5v3-source-001` | 上限 250 | 預計 198（餘額待讀） | 已取回；逐鏡 Gate PASS |
| 2026-11-02 06:43 | 即夢 Seedance 2.0 VIP 1080p（全模態） | EP01 v3 S7v3 眼睛跟薄片 6 s | `ep01/v2/gen/S7v3`，attempt `iris-s7v3-source-001` | 上限 250 | 預計 198（餘額待讀；v3 合計預計 924） | 已取回；逐鏡 Gate PASS |
| 2026-11-03 00:03 | 即夢餘額讀數（試驗建節點時） | 確認 v3 最後三筆 | S8bv3b、S5v3、S7v3 | 預計 561 | 561 積分（65,467→64,906，確認） | v3 五次合計 924 積分全部確認 |
| 2026-11-03 00:29 | 即夢 Seedance 2.0 VIP 1080p（全能參考，作者 EV 英文原句） | EP01 對嘴方法試驗 LSen1 5 s | `ep01/v2/gen/LSen1`，attempt `iris-lsen1-source-001`，帳本 `gen/ledger-trial.json`（上限 4 次／800） | 上限 250，預計 165 | 115 積分（64,906→64,791，00:58 讀數） | 已取回（SHA `93c52d27…`）；使用者「嘴没有对好」；依自帶音軌延遲放時同步到 20.53 s；使用者決定停止試驗，其餘 3 支不送 |
| 2026-11-03 05:42 | 即夢 數字人 大師模式（OmniHuman 1.5），K7＋上傳人聲 5 s，無動作描述 | EP01 副歌近景「真的在唱」試驗 OH-A（對照組） | `ep01/v2/trial/omnihuman/OH-A`，帳本 `trial/omnihuman/ledger.json`（上限 2 次／330，每次 165） | 網頁價格 30 | 30 積分（64,791→64,761，送出後精確讀數） | 生成中（任務卡：大師模式 5s 16:9 標準）；OH-B 等 OH-A 取回並核對規格後再送 |
| 2026-11-03 05:56 | 即夢 數字人 大師模式（OmniHuman 1.5），K7＋上傳人聲 5 s＋動作描述（認可原文） | EP01 副歌近景「真的在唱」試驗 OH-B | `ep01/v2/trial/omnihuman/OH-B`，帳本 `trial/omnihuman/ledger.json` | 網頁價格 30 | 30 積分（64,761→64,731，送出後精確讀數；試驗合計 60／330） | 生成中；填表時音頻需移除重傳一次才可生成（記於 OH-B 紀錄） |
| 2026-11-03T12:32Z | N1, N2, N3 (action shots, Seedance 2.0 VIP 首幀 5 s 1080p) | 3 submits × ceiling 165 | balance 64,731 → 64,236 = 495 confirmed | gen/ledger-action.json; approval trial/action/preview-approval.json |
| 2026-11-03T12:50Z | N4 (flipped first frame N4f, Seedance 2.0 VIP 首幀 5 s 1080p) | 1 submit × ceiling 165 | balance 64,236 → 64,071 = 165 confirmed; action shots total 660 / 660 | gen/ledger-action.json; amendment in trial/action/preview-approval.json |
| 2026-11-03T13:55Z | ST1, ST2, ST3, ST4, ST6 (story shots, Seedance 2.0 VIP 首幀 5 s 1080p; ST5 held: continuity FAIL) | 5 submits × ceiling 165 | balance 64,071 → 63,246 = 825 confirmed | gen/ledger-story.json; approval trial/story/preview-approval.json |
| 2026-11-04 | SC1, SC2, SC3 casting screen tests (即夢數字人大師模式 5 s) | 3 × price 30 | balance 63,296 → 63,206 = 90 confirmed | trial/screentest/ledger.json; approval trial/screentest/preview-approval.json |
| 2026-11-04 | SC4 casting screen test (即夢數字人大師模式 5 s; action text amended to positive phrasing, continuity re-review ready) | 1 × price 30 | balance 63,206 → 63,176 = 30 confirmed; screen tests total 120 / 120 | trial/screentest/ledger.json; approval trial/screentest/preview-approval.json (amendment SC4) |
| 2026-11-04 | casting v3 voice audition (ElevenLabs: 4 voice designs, 11 music_v2 chorus takes incl. re-rolls, 7 isolations, 1 STS test, 17 TTS) | — | ElevenLabs 5,692 credits (5,876 → 11,568 / 40,000) | series/voice-v3/README.md |
| 2026-11-04 | casting v3 character images (Codex image_gen, 12 plates) | — | no Jimeng credits | series/casting-v3/prompts.md, logs/runs.md |
| 2026-11-04 | Suno v6 (chirp-hawk) × 3 generations = 6 takes of "Looked Outside" (web UI driven in the user's logged-in Chrome; fields `ep01/v2/song-suno/fields.json`, lyrics v2.2) | 3 submits, each with a one-use intent (`song-suno/ui/submit-*`) | Suno credits 2,470 → 2,440 = 30 confirmed (10 per generation) | song-suno/takes/takes.json, structure.json |
| 2026-11-04 | Gemini audio listening (gemini-3.8-flash) × 1 on Suno take T1 (110 s window), sealed operator unit `song-suno/listen/T1/` | 1 call, internal ceiling USD 0.05 (not a price) | outcome EVIDENCE_GAP (invalid response shape), consumed; actual cost pending settlement | not retried; user chose T4 by ear |
| 2026-11-04 | Gemini audio listening × 2 on the T4 vocal stem (28 s windows: verse 1 27–55 s, chorus 1 60.5–88.5 s), sealed units `song-suno/listen/T4-verse1`, `T4-chorus1` | 2 calls, internal ceiling USD 0.05 each (not a price) | both returned observations; actual cost pending settlement | voice description used to match the lead's look |
