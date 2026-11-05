# IRIS EP01 對嘴方法試驗（照 ESCAPE VELOCITY 做法）

- 日期：2026-11-02
- 狀態：草案，等使用者確認參考包預覽後才付費。
- 上游：`docs/superpowers/specs/2026-11-02-iris-ev-method-realignment.md` §4.5、§6 的 D1、D2。
- 使用者原話（`outputs/ai-city-takeover/logs/decisions.md`）：
  > 「对嘴也是根本对不上」
  > 「先做對嘴方法試驗（付費）(Recommended)」
  > 「作者怎么做我们怎么做」

## 1. 為什麼做

c3 副歌的對嘴使用者判定「根本对不上」。原因：

- 6 支對嘴片的 prompt 都是約 500 字的中文表演劇本，沒有引用歌詞。作者實測，這類 prompt 會讓模型自己「演」一遍、重唱。
- c3 依 take 自帶音軌的延遲放置。但上個 session 的逐幀紀錄顯示，這幾支即夢 take 的嘴跟著送出的參考走，不跟自帶音軌，所以 c3 的嘴又晚了 2–4 幀。

這次照作者 ESCAPE VELOCITY（以下稱 EV）的做法重做唱的片段，先在副歌第一遍做 4 支試驗，挑出在即夢上有效的寫法。

## 2. 作者怎麼做 → 我們怎麼做

出處：EV readme「Seedance 2.5, with the song inside the prompt」、prompts-seedance.md（含早期測試）、wiki seedance「Lip sync, measured」「Inputs」。

| 項目 | 作者（EV） | 我們 |
| --- | --- | --- |
| 模式 | 參考模式：底片當 @Image1、人聲窗口當 @Audio1（OpenRouter 帶首幀會丟掉音訊，所以不用首幀） | 即夢 Seedance 2.0 VIP 全能參考：`{{image:0}}`＝底片、`{{audio:1}}`＝人聲窗口，標記寫在正文裡 |
| 底片 | 這一鏡的 Midjourney 底片，彩色 | 第一遍副歌已認可的底片 A02（`ep01/reference-package/A02-v1.png`） |
| 人聲 | 這一鏡人聲的完整窗口，從字間空隙切；窗口從第一個字前約 0.3–0.7 s 開始，不在字中間結束 | 分離人聲 17.97–22.97 s（5 s）：「I」在 18.60 s，前面 0.63 s 空隙；結尾落在 22.97–23.09 s 的停頓 |
| Prompt | 「@Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in time: "…"」＋一句景別、人物、一個表演動作、光＋「Locked camera, no cuts, no head turns.」，約 90 字以內 | 同一結構與長度，引號內是窗口唱的英文原詞 |
| 長度 | 4–8 s，720p | 5 s，1080p（倉庫對 2.0 的預設） |
| 同步 | 程式比對片段音軌與送出的人聲，找漂移點；最後人看 | `motion-kit/tools/sync_check.py`＋**逐幀嘴型**＋正常速度疊歌審看片；嘴型另量，因為我們實測即夢的嘴不一定跟音軌 |
| 對不上 | 在漂移前最後一個八分音符剪，從那一格接 cover | 試驗挑出方法後，正式重做副歌時照做 |

唯一要使用者決定的差異是 prompt 語言：作者全英文；倉庫規則要求送出的 prompt 純中文（`docs/canvas-continuous-production.md#prompt-language-and-character-identity`），D1 只放寬到引號內的英文歌詞。所以試驗分兩組，同時驗證方法與語言。

## 3. 試驗單元（付費前封存，不因結果追加）

共用輸入：

| 輸入 | 檔案 | SHA-256 |
| --- | --- | --- |
| 底片 | `outputs/ai-city-takeover/ep01/reference-package/A02-v1.png` | 見預覽頁 |
| 人聲窗口 | `outputs/ai-city-takeover/ep01/v2/trial/lipsync-ev/window-17.97-22.97.wav` | `851ce8a54b3bf96f13a6c29355720d58dab6a6d4a658c33006519cd7dedda5d7` |

人聲窗口取自分離人聲 `song/isolation/chorus-18.6-26.0-isolated.mp3`。它是從不含 Stella 念白的 bed 分離的，與母帶時間差約 2 ms。窗口調到 −16 dBFS RMS、峰值 ≤ −1 dBFS，結尾 15 ms 淡出。

| 單元 | prompt | 次數 |
| --- | --- | --- |
| EV-en-1、EV-en-2 | 作者英文原句（下文 3.1） | 2 |
| EV-zh-1、EV-zh-2 | 中文直譯，引號內英文歌詞（下文 3.2） | 2 |

- 模型：即夢 `seedance_2.0_vip`，1080p，16:9，5 s，全能參考。
- 預算：每支預計 165 積分、operator 上限 250；4 支預計 660，累計上限 800（使用者核可的「約 800 積分以內」）。
- 同一組的 2 支是事先登記的重複，用來分辨方法差異與隨機差異，不是失敗後的重試；每支都是獨立單元，各自有上限與一次性 permit。

### 3.1 EV-en

```text
{{image:0}} sings {{audio:1}}. She lip-syncs to {{audio:1}} exactly, every word in time: "I didn't run — I just looked outside. I". Medium close-up of the woman from {{image:0}}, her dark hair slicked back into a low bun, a black ear hook on her left ear and a thin red light line on her left collar, standing on the rainy glass balcony at night and facing the camera, singing calmly with her eyes on the lens, her head tilting slightly on the long notes. Cold blue city light behind her. Locked camera, no cuts, no head turns. No on-screen text.
```

### 3.2 EV-zh

```text
{{image:0}}中的她演唱{{audio:1}}。她的口型严格对准{{audio:1}}，每个字都准时："I didn't run — I just looked outside. I"。中近景：{{image:0}}中的女人，深色头发向后梳成低发髻，左耳戴黑色耳挂，左领口一条细细的红色灯线，站在夜雨中的玻璃阳台上，面向镜头，冷静地唱，眼睛看着镜头，长音时头微微倾斜。背后是冷蓝色的城市灯光。镜头固定，不切镜，不转头。画面中没有任何文字。
```

與作者原句相比只多兩處：IRIS 的外型描述（EV 也寫她的髮型、耳機等），以及「No on-screen text」（作者後期把它列為必寫，因為引號裡的字可能被畫成畫面文字）。

## 4. 量測與判斷

每支落盤後：

1. `shot-gate-reviewer` 依第 5 節的封存項目做逐鏡檢查。
2. `sync_check.py` 比對片段音軌與人聲窗口：延遲、照抄或重唱、同步區段、分歧點。
3. 逐幀量嘴型開口：「I」18.60、「didn't」19.28、「run」19.50、「I」20.72、「just」20.91、「looked」21.41、「outside」21.91 s（實測人聲起點），記錄嘴比聲音早或晚幾幀。
4. 做正常速度的疊歌審看片，片段依參考對應放（片內 0 s＝歌曲 17.97 s）；若量到的音軌延遲與嘴型一致，另做一支依延遲放的版本。

4 支都完成後，交使用者並排看疊歌片挑方法。Agent 只量，不判對嘴觀感。

## 5. 逐鏡檢查與停止條件（付費前封存）

客觀項目，由 `shot-gate-reviewer` 判：

- 身份：同一張臉、後梳低髻、左耳黑色耳挂、左領紅線、炭黑高領大衣。
- 畫面：無變形、無多餘文字或介面（包括歌詞被畫成文字），平台 AI 標識保留。
- 鏡頭：固定，不切鏡。
- 唱：歌詞期間嘴在唱，無聲處閉合。

停止條件：

- 某支在客觀項目 FAIL，且原因來自共用輸入（例如底片或窗口），就停止，其餘單元不送，回報使用者。
- 原因只屬於該支的隨機表現，就記錄後續送下一支事先登記的單元。
- 對嘴準確度是試驗要量的變數，不是停止條件。
- 結果不明（UNKNOWN）一律停止，不重送。

## 6. 之後

- 使用者挑定方法後，用它重做副歌兩遍：第一遍可直接用試驗中勝出的 take；第二遍用 K8b 底片；分歧處照作者做 cover。
- S5 看見紅窗的反應改用作者的動作片段寫法重拍「冷靜但活著」的版本（不皺眉）。
- 這兩項另列預算，先做參考包預覽再付費。

## 7. 不變的規則

- 付費前交參考包預覽，使用者確認後封存 `preview_approval`。
- 付費前由 `continuity-supervisor` 出連續性報告。
- 每支落盤後由 `shot-gate-reviewer` 做逐鏡檢查。
- operator 上限、一次性 permit、canonical submit 照舊。
- D1 落地時同步修訂 `docs/canvas-continuous-production.md` 的 prompt 語言規則；EV-en 組需使用者另外同意。
