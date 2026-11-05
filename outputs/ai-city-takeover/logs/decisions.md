# Decisions Log

規則：導演（使用者）原話逐字、帶日期與來源；後來的決定以新條目取代舊條目，不修改舊條目。Production 自己的決定另標「production」。

## 2026-10-30 · director · 初始需求
見 `../brief/creative-input.md`「初始需求」。要點：10 s 1080×1920 30fps 原創測試片 → 通過後 25–30 s《如果 AI 在凌晨接管一座城市》；不照搬原片；付費前先列預算；每次渲染後聯繫圖 QA；不降低質量。

## 2026-10-30 · director · 即夢 Seedance
「为什么不用即蒙provider的seedance」
→ production 決定：即夢 Seedance（`JimengVideoProvider`）列為動態底片首選通道；第一階段 v1 先以本地代碼驗證圖層系統，v2 以 Seedance 生成 S2（需預算同意）；第二階段動態鏡頭走即夢 Seedance。

## 2026-10-30 · director · 生圖入口
「你直接用codex cli生图就好」
→ production 決定：底片以 Codex CLI 內建 `image_gen`（gpt-image-2）生成，不用本地 FLUX / ChatGPT web MCP。

## 2026-10-30 · production · 技術棧
渲染器沿用倉庫 pinned 的 HyperFrames 0.7.103（`hf-seek` 驅動每幀純函數引擎），不採用 Remotion；字體用系統 OFL 的 Noto Sans/Serif/Mono CJK SC；音樂優先 Suno v6（需預算同意）。詳見 `docs/superpowers/specs/2026-10-30-ev-motion-douyin-pipeline.md`。

## 2026-10-30 · director · 預算（AskUserQuestion 回覆）
- Suno：「批准 Suno ≤20 credits (Recommended)」→ T01 配樂用 Suno v6，最多 2 次生成、≤20 credits。
- 即夢 Seedance：「v1 通過後只做 S2 (Recommended)」→ T01 v1 全本地；v1 通過 QA 後以即夢 Seedance 生成 S2（1 次提交、4–5 s、1080p 9:16、單次上限 300 積分；已知品質失敗最多再修 1 次，總上限 600）。

## 2026-10-30 · director · 畫幅（取代初始需求中的 1080×1920）
「我需要的是横版的」
→ production 決定：T01 與第二階段一律改為橫版 16:9，1920×1080，30fps 不變（使用者原指定 30fps）。已生成的 9:16 底片 P1-a/P2-a/P3-a 保留為歷史、不入橫版成片；橫版底片 P1L/P2L/P3L 重新生成。版式改用 16:9 標題安全區（原作規格：左 72、上 56、右 96、下 84 @1920×1080），抖音豎屏播放時橫版居中顯示，不再套用豎版按鈕區避讓。

## 2026-10-30 · director · 定位與長期方向（AskUserQuestion 回覆）
- 先前提問：「你是准备就做这个主题还是这个是跑通的,我们得讨论下」
- T01 定位：「先暫停，等主題討論完」→ 停止渲染與修改；dev3 修正（尾燈、識別框、光脈衝、events.json）已寫入但未渲染。
- 長期形態：「固定系列」→ 系列共享世界觀、視覺語法、片頭與 HUD 系統，持續出不同主題；T01 等同於定義系列的視覺語法。主題待討論。

## 2026-10-30 · director · 系列核心（AskUserQuestion 回覆）
「B 固定 AI 角色」→ 系列以一個原創 AI 角色為核心（身份 canon、服裝、標誌，可加固定聲線）；每集她/它在凌晨的城市做一件事，把一個 AI 話題用解說圖形講清楚。T01 保留視覺語法、內容重做；需先做角色設計與一致性測試。
- production 註記：AGENTS.md（2026-10-30 修訂）要求新創作付費影片生成前，參考包須交導演預覽並封存 `preview_approval`；觀感只由導演判斷。

## 2026-10-30 · director · 角色主軸（AskUserQuestion 回覆）
- 形態「寫實人形」；聲音「唱歌（歌詞 MV）」；題材「AI 新聞／熱點解說」；調性「冷靜觀察者」。
- 選角方向：「欧美」（性別未指定 → production：男／女／中性三方向各出定妝照，由導演看圖挑選）。
- 歌詞語言：「英文」。
- T01：「收尾為引擎測試 (Recommended)」→ 修完 dev3、跑完 QA，作為系列視覺語法與引擎的驗收片；角色與對嘴另在 T02 測試。

## 2026-10-30 · director · 選角（AskUserQuestion 回覆）
「CM 歐美男性」→ 系列角色定為 CM 方向：二十八九歲歐美男性，棱角鋒利、高顴骨、淺鬍渣、灰綠眼、灰金色後梳髮；黑色高領毛衣 + 深灰利落技術風短外套；右太陽穴一枚小紅色指示燈（系列唯一暖色標誌）。身份錨點候選：`series/casting/raw/CM-a.png`（SHA 見 casting/runs.md）。下一步：多角度身份參考組 → 導演確認後固定 canon。

## 2026-10-30 · director · 選角變更（取代「CM 歐美男性」）
先問「你觉得这个视频更适合男的还是女的」（production 答：依現設定男性略合適，但差距不大），導演隨後決定：「我更像让第一个女的当主角」「现在好修改吗」
→ 系列角色改為 CF 方向的第一張 `series/casting/raw/CF-a.png`。CM 身份參考組（series/identity/ID*-a）保留為歷史，不再作錨點。未產生付費素材，無需作廢付費結果。

## 2026-10-30 · director · 身份定稿與命名（AskUserQuestion 回覆）
- 「固定，只重出 ID7」→ CF 身份參考組 `series/identity-cf/raw/CF-ID1..ID6-a.png` 固定為系列 canon（含下裝：黑色修身直筒褲、黑色皮質短靴）；ID7（演唱表情）重出為更冷靜克制的版本。錨點 `series/casting/raw/CF-a.png`。
- 角色名：「IRIS」→ 系列角色與品牌名 IRIS。

## 2026-10-30 · director · 歌曲與字幕（AskUserQuestion 回覆）
- 先前提問（未選題）：「我考虑的是这种词语适合我这个背景吗,能唱好吗,我要换成和作者一个风格的吗,唱歌我还是准备用英文.一些字体你可以用中文」
- 歌曲：「原作架構＋IRIS 冷調 (Recommended)」→ 主歌 deadpan 念白講事實，副歌一句短 hook 用唱；陰暗 electroclash / minimal techno 約 126 BPM；冷而貼耳的英文女聲；副歌是「冷的快感」而非狂喜。
- 字幕：「英文歌詞＋中文譯句 (Recommended)」→ 唱的英文逐字上屏（唱到的字點亮），下方一行中文譯句；解說圖形用中文。
- production：EP01 題目未定；先以推薦題「AI 從訓練中連上網路（OpenAI 隔離事件）」查證並寫歌詞草稿供導演判斷，不構成選題決定。

## 2026-10-30 · director · EP01 選題與歌詞（AskUserQuestion 回覆）
「認可，我去 Suno 生成」→ EP01 題目：OpenAI 內部模型經 DNS 解析器設定錯誤取得有限網路連線、暫停 11 天（多來源查證）；歌詞 `ep01/lyrics-v1.md` 認可。導演將於 suno.com 以該檔欄位生成（CLI 仍需人機驗證）。

## 2026-10-30 · director · Current Scope

Codex 接续本会话后，导演回复：「还没生成，先完成测试片」。
→ 当前先收尾 T01 横版引擎测试片；EP01 歌曲与正式 MV 延后。T01 继续明确使用临时导引节拍，不把它标为正式 Suno 配乐，不新增歌曲或付费视频请求。dev7 与原速观感仍待导演观看，不把本回复当成成片审美认可。

## 2026-10-30 · director · T01 Dev7 Acknowledgement

在展示 dev7 审看入口、修复与验证范围以及临时导引音轨后，导演回复：「可以」。按测试片认可处理，继续工程验证及本任务提交；不把此回复扩展成 EP01 分镜、付费生成、Production Final Acceptance 或发布授权。

## 2026-11-02 · director · EP01 分工（AskUserQuestion 回覆，已被下一條取代）
Claude 會話因用量上限暫停約 3 小時，恢復後發現 Codex 已推進 EP01，於是詢問分工。導演回覆：「分工並行 (Recommended)」→ Claude 只做 motion-kit 歌詞字幕模組與歌曲節拍／逐字時間分析，Codex 繼續鏡頭與合成。

## 2026-11-02 · director · EP01 改由 Claude 全權負責（取代上一條）
「你别管codex,我觉得他没做好」
→ production 決定：
- EP01 改由 Claude 會話全權負責，不再與 Codex 分工。
- Codex 的產出不默認沿用，只作審查對象與備選素材，包括 ACE-Step 歌曲候選 r4、A01-v2、C-v1、4 段新聞圖形、storyboard/production-input。
- 這些檔案原樣保留，不刪、不改；已花費的 594 即夢積分照實保留在歷史中。
- 依原作方法「歌先行」重做：歌曲 → 節拍與逐字時間 → 按小節的分鏡 → 參考包預覽認可 → 即夢生成 → motion-kit 合成 → QA。

## 2026-11-02 · director · 歌曲生成方式（AskUserQuestion 回覆）
選項：Suno 網頁由導演按、ElevenLabs Music 全自動、兩邊都做。導演回覆：「我希望全自动别要我点击」
→ production 決定：
- 用 ElevenLabs Music（`music_v2`，經 project MCP `elevenlabs-direct`）全自動生成，不再請導演操作 Suno 網頁。
- 預算上限照選項所列：最多 2 次生成，每次約 30 秒。
- 生成前後各讀一次帳號 `character_count` 核對實扣；生成前讀數為 1,162 / 40,000。
- 第一次生成存檔以便局部重生成（inpainting）；局部瑕疵優先局部修，不整首重來。
- 歌詞、曲風、時長沿用已認可的 `ep01/lyrics-v1.md`，不改詞。

## 2026-11-02 · director · 歌曲修正方式（AskUserQuestion 回覆）
背景：ElevenLabs Music 生成兩次，念白和耳語段都沒有可辨識的人聲，只有唱的副歌有，兩次合計 762 credits。
導演回覆：「主歌改半唱半念，再試 (Recommended)」
→ production 決定：
- 主歌、前奏、尾奏改為冷感半唱半念（單音、平板）；耳語段改為氣聲輕唱；副歌照樣唱。歌詞一字不改。
- 新增上限最多 3 次，每次約 380 credits，合計約 1,150。
- 挑最好的一版，局部瑕疵用局部重生成修，局部重生成也計入這 3 次。

## 2026-11-02 · director · 歌曲方案（AskUserQuestion 回覆，聽過 take 3 後）
導演回覆：「保留第 3 版副歌，其餘補念白 (Recommended)」
→ production 決定：
- 保留 take 3（song_id `adAwLxlOTRPdVH4Pq0x6`）18.80–26.67 s 的副歌，即兩遍演唱。
- 其餘段落用局部重生成改為同一聲音的純伴奏，1 次，約 380 credits。
- IRIS 念白用 ElevenLabs 語音生成：同一把聲音，耳語段用氣聲，逐句對齊拍點，約 400 credits。
- 歌詞一字不改，總長 30.5 s。

## 2026-11-02 · director · IRIS 念白聲音（AskUserQuestion 回覆）
試聽頁 `ep01/v2/song/index.html` 有三個候選：Stella、Sarah、Sage。導演回覆：「A · Stella」
→ production 決定：IRIS 系列念白聲音定為 ElevenLabs「Stella Gu - Cold, Indifferent and Calm」（voice_id `BqljjWyTnrioXPCNkCd4`），模型 `eleven_v4`，stability 0.6，similarity 0.8。之後各集沿用，不另換聲音。

## 2026-11-02 · director · 歌曲 v2 認可（AskUserQuestion 回覆）
試聽 `ep01/v2/song/mix/IRIS-01-v2.wav`（SHA `d7e2107d…`，30.5 s，−14.1 LUFS）後，導演回覆：「可以，往下做分鏡」
→ production 決定：
- 此版定為 EP01 歌曲，之後的節拍、逐字時間和分鏡都以它為準。
- 只是歌曲認可，不代表成片認可。

## 2026-11-02 · director · EP01 參考包與動態分鏡認可（AskUserQuestion 回覆）
預覽：`ep01/v2/index.html`，包括動態分鏡 `renders/EP01-animatic-a9.mp4`、分鏡 v2.1 與逐鏡參考圖；概念審查的五項阻塞都已修正。
導演回覆：「認可，開始生成」
→ production 決定：
- 依 v2.1 付費生成即夢 Seedance 2.0 VIP 1080p 共 7 鏡：S1、S3、S5、S7、S8a、S8b、S9a。
- 預算上限約 2,500 積分（每鏡已知失敗最多重做 1 次）；另做一次約 7 秒的副歌人聲分離。
- S8a 最先做，依封存標準驗證對嘴；每鏡落盤後先過逐鏡 Gate，全部 PASS 才提交下一鏡。
- 認可封存為 `ep01/v2/preview-approval.json`。

## 2026-11-02 · user · S8a 對嘴版本

> 「用第一版 (Recommended)」

背景：S8a 第一版與有界修復版 S8ar 都未全過封存標準。第一版的兩個不合格點（開唱前 0.2 s 張嘴、唱完留縫）都在成片窗口 18.867–22.567 s 之外，窗口內開口時機在 ±1 幀內；S8ar 開口晚 4–8 幀。使用者選用第一版；S8b 照第一版做法（不留前置靜音，從前一句尾音起唱）生成。

## 2026-11-02 · user · S8b 參考包預覽

> 「認可，生成 S8b (Recommended)」

預覽頁：`ep01/v2/review/S8b-preview.html`（K8b 首幀、ID7b 身份圖、副歌第二遍乾聲 22.20–26.20 s 與同段母帶）；4 秒、約 132 積分；封存標準見 `ep01/v2/s8a-lipsync-amendment.md` S8b 段。

## 2026-11-02 · user · S8b 有界修復

> 「認可修復參考，重做一次 (Recommended)」

背景：S8b2 判 FAIL（句尾「outside」晚約 0.2 s、唱完晚約 0.2 s 閉嘴）。修復參考 `song/isolation/S8br-vocal-ref-22.00-27.00.wav` 與已認可的 S8b 乾聲逐樣本相同，只在前面多 0.2 s 靜音（S8a 第一版的做法），5 秒、約 165 積分。

## 2026-11-02 · user · S8b 版本

> 「用 S8b2 (Recommended)」

背景：S8b2 判 FAIL（句尾 outside 與閉嘴各晚約 0.2 s），有界修復 S8br 判 FAIL（約 2.2 s 後閉嘴，後半句沒唱）；已核准的 2,500 上限用完。使用者選用 S8b2。

## 2026-11-02 · user · 成片 c1 審看意見

> 「2s这里没有睁眼的过程是为什么,衔接很弱.后面人物表现一直很弱,唱歌也是」

## 2026-11-02 · user · 重做範圍與演唱方向

> 「S1 睁眼＋副歌＋S5/S7 反應 (Recommended)」
> 「冷靜但活著 (Recommended)」

範圍：S1（睜眼）、S5、S7、S8a、S8b 共 5 鏡，約 924 積分，每鏡最多修 1 次，上限約 1,850 積分；先給使用者看靜幀預覽，認可後才付費。演唱：保留冷靜觀察者，唱前換氣、眼神從遠處拉回鏡頭、頭隨樂句輕動、嘴型完整、鏡頭緩推，到「I just looked outside」情緒稍微放開。

## 2026-11-02 · user · v3 表演預覽

> 「認可，S1 用原生首尾幀 (Recommended)」

預覽頁 `ep01/v2/review/v3-preview.html`：S1 K1a→K1c（同意這一鏡免附 IRIS 身份圖，用原生首尾幀）、S5 K5b＋P5、S7 K7＋P7、S8a A02＋P8a＋S8a 乾聲（前置 0.2 s 靜音）、S8b K8b＋P8b＋P8c＋S8br 乾聲；5 鏡約 924 積分，每鏡最多修 1 次，上限約 1,850。

## 2026-11-02 · user · S8av3 逐鏡檢查 FAIL 的處置

> 「用 S8av3，晚 2 幀 (Recommended)」

S8av3 表演合格，但對嘴「I just」晚 4–5 幀（`qa/gate-S8av3/post-media-gate.json` FAIL）。使用者選擇放進成片並把入點從 0.4667 改為 0.5333：「didn't」嘴早約 3 幀、「I just」晚約 2 幀，不另付費。審看片 `ep01/v2/renders/review/S8av3-slip2f-master-audio.mp4`。Gate 判定不變，記錄於 `qa/gate-S8av3/user-decision.json`。

## 2026-11-02 · user · S8bv3b 逐鏡檢查 FAIL 的處置

> 「用 S8bv3b (Recommended)」

S8bv3b 表演放開（仰頭、半閉眼），但兩處停頓沒收嘴、「outside」沒重新張嘴、唱完到剪點仍留縫，望向城市在剪點之後（`qa/gate-S8bv3b/post-media-gate.json` FAIL）。使用者選擇放進成片，入點維持 0.5667，不另付費。審看片 `ep01/v2/renders/review/S8bv3b-film-window.mp4`。Gate 判定不變，記錄於 `qa/gate-S8bv3b/user-decision.json`。

## 2026-11-02 · user · c2 審看與方向

> 「节奏变快了,这个还不如上一版」
> 「我们需要讨论下怎么做这个视频,我感觉走远了」
> 「回到原作做法 (Recommended)」
> 「照這樣改 (Recommended)」
> 「先把specs写好,作者是怎么做的,我们要怎么做」

c2 節奏不如 c1；方向改為回到原作做法：圖形與排版為主、人物為輔，對嘴照作者方法，不再為對嘴整鏡重生成；EP01 以 c1 為底收尾，不再付費生成。做法寫成 `docs/superpowers/specs/2026-11-02-iris-ev-method-realignment.md`（草稿，經兩輪獨立審查）。

## 2026-11-02 · user · 交接

> 「给prompt.我开新的session」

本會話停在 spec 完成；c3 還沒動工。使用者先前要求不再更新 `handoff/` 交接文件，所以改給新 session 一段接續用的 prompt。

## 2026-11-02 · user · c3 副歌剪法與字幕時間（AskUserQuestion 回覆）

> 「B：切到睜開的眼 (Recommended)」
> 「B：切到窗前 (Recommended)」
> 「校正副歌四行 (Recommended)」

審看頁 `ep01/v2/review/c3-chorus.html`；量測工具 `motion-kit/tools/sync_check.py`，結果在 `ep01/v2/qa/sync/`。
- 第一遍：S8av3 依量到的延遲（−0.107 s）放置，唱「I didn't run —」；20.67 s 換行停頓處切到 S1v3 睜開的眼（片內 4.0 s 起），「I just looked outside」照樣上屏。
- 第二遍：S8b2 依量到的延遲（−0.133 s）放置，唱「I didn't run —」；24.07 s 換行處切到 S5v3 窗前看城市（片內 3.0 s 起），25.90 s 接 S9a。
- 副歌四行的上屏與逐字點亮改依分離人聲實測的起點（c1 起的 `words.json` 副歌時間來自低信心的 Whisper 對齊）。
- S8av3、S8b2 原本的逐鏡 Gate 判定（FAIL）不變；成片只用量到同步的那一行。

## 2026-11-02 · user · c3 審看意見與下一步（AskUserQuestion 回覆）

> 「要修改」
> 「人物表情为什么会皱眉,然后人物一点表现力没有」
> 「对嘴也是根本对不上」
> 「先做對嘴方法試驗（付費）(Recommended)」
> 「一起納入重做」

背景：c3（`renders/IRIS-EP01-Looked-Outside-v2-c3.mp4`，SHA `437fddcb…`）副歌依 take 自帶音軌的量測延遲放置；上個 session 的逐幀 Gate 紀錄顯示這幾支即夢 take 的嘴跟送出的參考、不跟自帶音軌，所以 c3 的嘴又晚了 2–4 幀。皺眉來自 S5v3 的表演指令（眉心收緊、一直盯住）與我在第二遍副歌復用它。
→ production 決定：
- 照 spec 2026-11-02 D1＋D2 做對嘴方法試驗：對嘴 prompt 可在引號中寫英文歌詞（其餘仍中文），改用作者的短格式；在副歌第一句「I didn't run」各方法做 2 支 4 秒，合計約 800 積分以內；使用者看疊歌片挑方法，再用它重做副歌。付費前仍先交參考包預覽並封存 `preview_approval`。
- S5 看見紅窗的反應也用新方法重拍一個「冷靜但活著」的版本，另列預算、先看預覽。
- D3（是否含 Seedance 2.5）、D4、D5 仍未批准。

## 2026-11-02 · user · 對嘴試驗參考包（AskUserQuestion 後回覆）

> 「作者怎么做我们怎么做」
> 「先给我看看」
> 「认可,其实原作者很多都是静图我们也可以这么做的,如果人物表现力做不好」

預覽頁 `ep01/v2/trial/lipsync-ev/preview.html`；計畫 `docs/superpowers/plans/2026-11-02-iris-ep01-lipsync-trial.md`。
→ production 決定：
- 照 ESCAPE VELOCITY 的做法送 4 支試驗片：作者英文原句 2 支（EV-en，這次試驗破例不遵「prompt 純中文」規則）、中文直譯加引號內英文歌詞 2 支（EV-zh，D1）；底片 A02、人聲窗口 17.97–22.97 s，即夢 Seedance 2.0 VIP 1080p、5 秒，預計 660 積分、累計上限 800。
- 認可封存為 `ep01/v2/trial/lipsync-ev/preview-approval.json`。
- 方向備案：人物表現力做不好時，照作者大量用靜圖（底片由程式移動的 still／2.5D）。

## 2026-11-02 · user · 對嘴試驗第 1 支後停止（AskUserQuestion 回覆）

> 「嘴没有对好,然后我记得原作者不是就是这样简单的放一个视频还有很多后期处理」
> 「先停，用 LSen1 的同步段＋靜圖後製」

背景：LSen1（作者英文原句，SHA `93c52d27…`）依參考對應放時嘴對不上；它的嘴主要跟片段自帶音軌走（自帶音軌第一句早 0.8 s），和作者說的一致。依自帶音軌延遲（−0.804 s）放時，同步到歌曲 20.53 s、20.61 s 起分歧（`trial/lipsync-ev/LSen1/sync/LSen1/`）。
→ production 決定：
- 試驗停止：LSzh1（已 start、未送出）、LSen2、LSzh2 都不送，不扣費。試驗帳本只有 LSen1 一次付費。
- 副歌照作者的後製做：第一遍用 LSen1 依自帶音軌延遲放，留到分歧前最後一個八分音符；其餘段落用已認可的靜圖由程式移動（still），加副歌的 punch／impact 與歌詞。

## 2026-11-02 · user · c4 審看（AskUserQuestion 後回覆）

> 「不认可,人物表情和对嘴都不好.干脆就用静图,嘴应该很少动,或者动图的时候给远景动作不要动嘴.歌我非常认可」

→ production 決定：
- c4 不認可。下一版人物一律用已認可的靜圖由程式移動（still），不再放對嘴或人物近景表演的影片；嘴幾乎不動。
- 若要用動態影片，只用遠景的身體動作、不動嘴（目前沒有這類素材，新生成要另外批准預算並先看預覽）。
- 歌曲 v2（`song/mix/IRIS-01-v2.wav`）使用者明確認可。
- 同一輪補充（附 c4 截圖三張）：
  > 「睁眼之后突然转到这个人也非常奇怪」（S1 睜眼 → S2 A01v2 垂眼）
  > 「这里倒是可以」（S7 S7v3，玻璃窗空間）
  > 「这里又跳会又显得很突兀」（S7 → S8a 跳回陽台、張嘴唱）
  → S7 保留；S1→S2 與 S7→副歌兩個接點要重做，不能「突然換人／跳回」。

## 2026-11-02 · production · c5 剪輯（不付費，只用已認可素材）

依上方使用者對 c4 的意見（open-video 接點與重複素材審查）：
- **S2**：A01-v2 陽台影片 → **P7 靜圖**（S1 那隻眼睛的主人，同一張臉、同樣的玻璃窗冷光，醒著看向頁面）。
- **S5**：S5v3（皺眉）→ **K5b 靜圖**（窗前平靜望外，遠窗紅燈與 DNS 查詢圖形照舊）。
- **S7**：S7v3 保留（使用者認可）。
- **副歌第一遍**（18.867–22.567 s）：**K7 近景一鏡到底**，與 S7 結尾同一空間、同樣看鏡頭，推近；不跳回陽台。
- **副歌第二遍**：22.567 s 唱「I didn't run」時才回到 S5 的窗前（**K5**，低頭看城市）；24.067 s「I just looked outside」接 **K5b 近景**，視線抬起望遠，鏡頭往她看的方向漂。
- 人物全部閉嘴靜圖，副歌仍有 kick punch 與進入 impact；字幕照舊上屏。c4 的副歌剪輯另存 `comp/chorus-c4.json`。
- 已知：K5 玻璃上有她淡淡的臉部倒影（畫面中央）；K7 的面板比 S7 結尾亮。是否怪由使用者判。
- c5 交付審看（未經 Harness verify-assembly，審看片）：render `renders/EP01-film-c5.mp4` b562a96d…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c5.mp4` 39cf28d3…；並排 `renders/review/c1-vs-c5.mp4` b9e9e19f…；QA 11/11 剪點、12/12 圖形時機、無閃爍；−14.2 LUFS／−1.0 dBFS；花費 0。逐接點紀錄 `qa/film-c5/assembly-review.json`。等待使用者審看。

## 2026-11-02 · user · c5 審看（AskUserQuestion，附 S8a K7 近景「I just looked outside」截圖）

> 「我觉得这是还是要动嘴,这样你可以就做图,然后拼起来变成动态图」

→ production 決定：c5 不定案。副歌正面近景（S8a，K7）要有嘴部動作；方法依使用者：做同一張臉的不同嘴型靜圖（只改嘴部，其餘像素不動），依實測字詞時間逐張接成動態圖，不用影片模型對嘴。
- 同一輪補充：「户在哦和看你还有没有更好的想法,总之这个唱歌这里放一个静图贴脸太奇怪了.是不是你后面还有层序每加导致的」（語音輸入，理解為「看你還有沒有更好的想法……是不是你後面還有程序沒加」）→ 是：c5 近景是不動的閉嘴靜圖，嘴型拼接尚未接入。追加：換嘴型（M7B/C/D/F）＋一次眨眼（E7H/E7C）；更好的備案（付費、需先查證）：專為「圖＋歌聲」對口型的模型（如即夢數字人）。
- c6 交付審看（未經 Harness verify-assembly，審看片）：S8a K7 改為換嘴型靜圖（M7B/C/D/F＋眨眼 E7H/E7C，Codex image_gen 各 1 次共 6 次，無重做；`comp/mouth.json`、`motion-kit/src/mouth.js`、`motion-kit/tools/region_plates.py`）；其餘同 c5。render `renders/EP01-film-c6.mp4` a9d51ff2…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c6.mp4` e26ad4cb…；副歌片段 `renders/review/c6-chorus-17.5-26.5.mp4` ed3f327f…；QA 全過；−14.2 LUFS／−1.0 dBFS。逐接點紀錄 `qa/film-c6/assembly-review.json`。等待使用者審看。

## 2026-11-02 · user · c6 審看（AskUserQuestion）

> 「查專門對口型模型」

→ production 決定：c6 不定案。先查證「一張圖＋歌聲 → 唱歌影片」的專用對口型模型（如即夢數字人）的唱歌效果、可用性、限制與費用（model-researcher 外部調研＋memory-keeper 專案經驗），再做參考預覽給使用者決定；任何生成都要付費，預覽與付費前照常走 preview_approval 與連續性報告。

## 2026-11-02 · user · c6 審看

> 「不行,太low了.我看了下这个对嘴,要不不用对的狠准,我们只需要让人物真的表现在唱歌就好」

→ production 決定：c6 的換嘴型靜圖不採用（定格感）。副歌近景的要求改為「人物真的在唱」：自然的開合、呼吸、表情與頭部動作，跟著樂句走；逐字對嘴精度放寬（仍以使用者看、聽判定）。需要真的唱歌的影片，靜圖路線到此為止；下一步依調研結果選模型，先給參考預覽與費用，使用者認可後才付費生成。

## 2026-11-02 · user · 數字人試驗預覽（AskUserQuestion）

> 「你寫程式自動操作」

→ production 決定：認可 `trial/omnihuman/preview.html` 的試驗（即夢數字人大師模式、1080P，K7＋17.97–22.97 s 人聲；A 不寫動作描述、B 寫純中文動作描述；2 次不重做，約 330 積分上限，單次網頁價格高於 165 就停下問），封存為 `trial/omnihuman/preview-approval.json`。授權替數字人頁新寫瀏覽器自動化：先唯讀確認入口、價格與規則，再照既有關卡（連續性報告、lint、一次性許可、帳本上限、結果不明即停）送出。
- 2026-11-03 05:42Z · production：數字人試驗 OH-A 送出。
  - 送出前：連續性報告 OH-A／OH-B 皆 ready（`trial/omnihuman/continuity-report.json`）；lint 通過；網頁價格 30（單次上限 165）；許可為一次性。
  - 實扣 30 積分（64,791→64,761，精確讀數）。入口審核放行，K7 寫實 AI 臉未被擋。
  - 任務卡：大師模式 5s 16:9 標準。
  - 照報告建議逐支送：OH-B 等 OH-A 取回、核對輸出規格（解析度、fps、標記）後再送。
  - 自動化：數字人的「角色」「上傳音頻」用的是 `showOpenFilePicker`，`gen/omnihuman.cjs` 以頁面內 SHA-256 驗證過的原檔回應選檔；生成按鈕以「最上層元素是生成按鈕」驗證後只點一次。
- 2026-11-03 06:27Z · production：數字人試驗結果。
  - OH-B 送出 30 積分（64,761→64,731）；試驗合計 60／330。
  - 逐鏡 Gate（shot-gate-reviewer，video-analysis MCP）：OH-A、OH-B 皆 **FAIL**（`trial/omnihuman/post-media-gate.json`）。
  - 共同問題：第二句中段嘴幾乎不動、凍臉、身分漂移（雀斑消失、臉型變圓）、入點垂眼、身體擺動。
  - OH-A 另有：機械手、光條。OH-B 另有：小幅搖鏡、漂移光點、4.03 s 牙齒碎裂。
  - 依預覽認可的放棄條件（兩支都有身分漂移）：這條路線停止，不送第三支。是否改判次要或改走其他路線，由使用者決定。

## 2026-11-03 · user · 數字人兩支審看（AskUserQuestion）

> 「现在嘴形对上了,背景也还可以,但是人物表演还差点.然后后面的程序装饰还差点,作者不是就是简单放个视频」

→ production 決定：
- 使用者當次裁決：數字人的嘴型與背景可以接受（Gate 的對應項由使用者改判，Gate 原判定不變）。路線繼續。
- 待改善：人物表演還差一點；後期程式化裝飾不足。照作者做法：影片簡單放進去，靠 motion-kit 的後期裝飾撐起畫面。
- 下一版 c7：副歌近景放數字人 take（OH-B；OH-A 有機械手），副歌加程式化裝飾；表演再強的新 take 需先給預覽、經使用者認可才付費。
- c7 交付審看（未經 Harness verify-assembly）：
  - 內容：S8a 換成數字人 OH-B（推近構圖、延遲 +0.025 s），副歌加程式裝飾（識別框「IRIS · 仍在沙盒內」、紅色探針「只看了一眼」、重拍印刷衝擊、IRIS 時鐘）。
  - 檔案：render `renders/EP01-film-c7.mp4` d94c8b33…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c7.mp4` ef43c5c5…；副歌片段 `renders/review/c7-chorus-17.5-26.5.mp4`。
  - 檢查：QA 全過（首次渲染進副歌閃白一格被判單格突跳，改三格遞減）；−14.2 LUFS／−1.0 dBFS。
  - 待使用者：審看 c7；表演更強的兩支新 take（OH-C／OH-D，預覽 `trial/omnihuman/preview-v2-inputs.json`）要不要做。

## 2026-11-03 · user · c7 審看（AskUserQuestion，附「只看了一眼」探針截圖兩張）

> 「这个表现力确实可以了,但是这个字体,我是真的看不懂.」

→ production 決定：
- 數字人 OH-B 的表現力使用者認可，不做 OH-C／OH-D 新 take，不再付費。
- 「只看了一眼」紅色探針（線＋字）看不懂，兩遍副歌都拿掉；第二遍只留 S5 遠窗亮起，不加文字。
- 識別框「IRIS · 仍在沙盒內」與時鐘保留，若也看不懂再拿掉。
- c8 交付審看（未經 Harness verify-assembly）：
  - 改動：拿掉「只看了一眼」探針；第二遍只留遠窗亮起；其餘同 c7。
  - 檔案：render `renders/EP01-film-c8.mp4` 236b36c0…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c8.mp4` 31eb8a7a…；副歌片段 `renders/review/c8-chorus-17.5-26.5.mp4`。
  - 檢查：QA 全過；−14.2 LUFS／−1.0 dBFS；花費 0。

## 2026-11-03 · user · c8 審看

> 「地址给我」→ 給出 c8 審看頁、副歌片段、整片網址。
> 「整体差不多了,还少点东西感觉」

→ production 判斷（對照 `docs/superpowers/specs/2026-10-30-ev-motion-douyin-pipeline.md` 與同系列 T01）：
- IRIS 整片沒有系列的 HUD 畫框（chrome）。作者規格的 budgeted 密度要求每鏡都有，T01 也每鏡都有。
- 規格中的「抖動轉場」也還沒做。
- 規格另寫明只用音樂、不加音效，所以不從聲音補。
- c9 加上這兩樣，都不加文字：
  - 畫框：四角框線＋中央刻度，inset 18 避開 AI 標識，lw 1.5、alpha 0.42；
  - 剪點：3 格印刷爆點。
- 共用元件 `motion-kit/src/draw2d.js` 的 `chrome()` 增加 `lw` 參數，預設 1 不變。
- 若使用者指的不是這個，另提兩處：結尾她沒有再出現；副歌第二遍是靜圖。

- c9 交付審看（未經 Harness verify-assembly）：
  - 檔案：render `renders/EP01-film-c9.mp4` a9aa3b8c…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c9.mp4` e73a8eb6…；並排 `renders/review/c8-vs-c9.mp4`。
  - 檢查：QA 全過；−14.2 LUFS／−1.0 dBFS；花費 0。

## 2026-11-03 · user · c9 審看（AskUserQuestion）

> 「都没问题,但是对比原作者还是太单调,元素太少,片段太少,内容太少,也不够高级还」

→ production 決定（c10，照作者 dense 密度與規格中尚未用上的手法；已認可的歌、表演、S7、識別框、畫框全部保留；花費 0）：
- 鏡頭 12 → 21。每個新鏡頭都對準它講的字：
  - 7.1 s 資訊圖「研究模型 → DNS 解析器 → 互聯網」；
  - 9.73 s 城市：破窗光點、探針、連線、「有限聯網」；
  - 12.1 s「11 天」滿版大字；
  - 副歌 21.37 s 眼睛特寫、24.73 s 遠窗特寫，切回時鏡頭運動接續；
  - 29.13 s 她的最後一眼（S7v3）。
- 副歌歌詞改用作者的 stack 版式（`motion-kit/src/lyrics.js` 新增，預設行為不變）。
- QA 修正：
  - 副歌不加剪點轉場；其他剪點的轉場改為單格，且不落在圖形登場前；
  - 城市鏡頭加破窗光點，檢查框縮到光點。
- c10 交付審看（未經 Harness verify-assembly）：
  - 檔案：render `renders/EP01-film-c10.mp4` afa95da9…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c10.mp4` 39b1349a…；並排 `renders/review/c9-vs-c10.mp4`、`renders/review/c1-vs-c10.mp4`。
  - 檢查：QA 全過；−14.2 LUFS／−1.0 dBFS。

## 2026-11-03 · user · 對照原作者逆向分析（AskUserQuestion）

> 使用者給出 `outputs/anabology-opus55-replica/escape_velocity_analysis/README.md`；選「對照 c10 出差距清單 (Recommended)」；清單 `ep01/v2/review/ev-gap-c10.md` 九項全選：「1–3 介面系統 (Recommended), 4–5 字型與圖表, 6–7 反白與轉場, 8–9 標籤與識別框」

→ production 決定（c11，花費 0，motion-kit 程式）：已認可的歌、表演（OH-B）、S7、鏡頭與剪點保留，加上：全片持續 HUD（計數 D+00/11、片名＋頻譜、事實跑馬燈、時碼）、翻牌（03:47、11 天、03:48）、紅色關鍵字、窄體動態關鍵字、解釋圖表（DNS 折線、聯網儀表、11 天時間軸）、「门已经关上了」反白、段落條狀遮罩、人物標籤卡、臉部識別框貫穿。新手法做成 motion-kit 共用元件。
- c11 交付審看（未經 Harness verify-assembly）：
  - 內容：九項全做，鏡頭、剪點、歌、OH-B、S7v3、原有圖形照 c10；新手法在 `motion-kit/src/hud.js`、`flap.js`、`kinetic.js`、`osd-charts.js`，`lyrics.js` 加強調色選項、final shader 加 `uInvert`（預設都不變），node 測試 42/42。反白 27.17–27.9 s（1.5 拍）。c10 的 main.js 留在 `comp/src/main-c10.js`，chorus.json 未改。
  - 檔案：render `renders/EP01-film-c11.mp4` c4600f8aace0d88070722c484e7b23a640cd3c0ca9e44e31d08966a71034db2e；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c11.mp4` 60527579a9772dbd5869a15cac167caf3270d150bc1286042c88a8330ac3e870；副歌片段 `renders/review/c11-chorus-17.5-26.5.mp4`；並排 `renders/review/c10-vs-c11.mp4`；審看頁 `review/film-c11.html`。
  - 檢查：QA 全過（剪點、事件含新增 5 個、閃爍、strobe、單幀突跳、離群幀）；途中修正：反白收回時間避開 S9b 剪點、副歌前細條改細改慢（原有 strobe 格）、03:48 翻牌提早翻定。−14.2 LUFS／−1.0 dBFS；花費 0。

## 2026-11-03 · user · c11 審看（AskUserQuestion）

> 「還不夠，繼續加」

→ c11 不定案，繼續增加內容；方向待使用者選（免費重用既有素材 vs 付費新人物鏡頭）。
- 方向：「兩條都做 (Recommended)」→ (1) c12：免費重用既有素材（舊 Seedance 鏡頭不靠嘴的片段、OH-A、未用靜圖）做插入鏡，加資訊圖與小視窗；(2) 3–4 個新人物遠景動作、不動嘴的鏡頭，先做參考預覽（靜幀）給使用者認可，認可後才付費生成（約 165 積分／支）。
- c12 交付審看（未經 Harness verify-assembly；免費重用那一半）：
  - 內容：c11 的 20 個剪點都在原幀，歌、OH-B、S7v3、介面系統、歌詞、AI生成 不變；加 7 個插入鏡（0.43–0.70 s，落在字或拍上）：I1 4.10 s S9a 機房寬鏡、I2 5.27 s K9b 晶片、I3 8.60 s S9a 紅色門縫、I4 15.03 s S3 走道、I5 16.90 s 第一版 S7 面板（只框面板）、I6 23.33 s S5r 側臉（副歌唯一插入，副歌切離共 1.47 s／7.03 s＝21%）、I7 26.23 s P8c；只用無唱歌嘴型、無皺眉的片刻，來源 SHA 與入出點在 `ep01/v2/comp/inserts.json`、`qa/film-c12/assembly-review.json`。資訊元素：S3 查詢紀錄面板、S3d／S6／S9b 小視窗（K4、第一版 S5、K9e）、S4c 城市示意圖＋探針點、S6 機櫃刻度標籤，不加新事實。c11 留在 `comp/src/main-c11.js`、`comp/chorus-c11.json`，可重建（events.json 與 c11 同 d879367b…）。`motion-kit/src/runtime.js` 加可選 `bitmaps`（預設不變）。
  - 檔案：render `renders/EP01-film-c12.mp4` ead978bb3891f452b808a7b7c7ebe4a89d75bcaaa880d5ec71145377b9b6e7ab；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c12.mp4` f1a7fba69b71c57a6306e28f18a6d335dd333cb97c1d70b94b208ea12eca3801；副歌片段 `renders/review/c12-chorus-17.5-26.5.mp4` bf97477f6321…；並排 `renders/review/c11-vs-c12.mp4` 509af8c797f9…；審看頁 `review/film-c12.html`。
  - 檢查：QA 全過（剪點 33/33、事件 20/20、閃爍最多 2 次／秒、strobe 0、單幀突跳 0、離群幀 0）；途中修正：插入鏡切點不加印刷爆點（切進 I5 亮面板那格判成單幀突跳）、I6 改 1.6 倍避免和 K5 像跳接、I5 改框只剩面板、I7 識別框避開 AI 標識。node 測試 42/42。ebur128 −14.2 LUFS／−1.0 dBFS；花費 0。

## 2026-11-03 · user · 新人物動作鏡頭預覽（AskUserQuestion）

> 「4 支都生成 (Recommended)」

→ 認可 `trial/action/preview.html`：N1–N4 首幀（keyframes/raw/N1–N4-a.png）＋純中文提示詞，Seedance 2.0 VIP 首幀生影片 5 s 1080p 無音頻，各 1 次不重做；單支上限 165、總上限 660 積分，原生報價超過即停下問。封存 `trial/action/preview-approval.json`。送出前照常：連續性報告、lint、一次性許可、帳本、逐鏡 Gate。
- 主會話補記：N1–N4 的影片請求只送首幀一張圖、不附身份參考圖，正是使用者看過並認可的預覽內容；在 `trial/action/preview-approval.json` 補 `identity_waivers: ["IRIS"]` 與依據，輸入未變。

## 2026-11-03 · N1–N3 生成與逐鏡檢查；N4 翻轉（AskUserQuestion）

- N1–N3 已送出，實扣 495（64,731→64,236）。逐鏡 Gate（qa/gate-N1..N3）：N1 PASS、N3 PASS；N2 FAIL（鏡頭推向頭部而非封存的「推近手」，其餘全過）。
- 使用者：N2 回「地址呢」（給出 `trial/action/takes.html`，N2 待決）；N4 選「用翻轉版送出 (Recommended)」→ 首幀改 N4f-a（水平翻轉，耳掛與紅線回到左側），向左橫移；提示詞不變；認可補記於 preview-approval.json amendments。
- N4 已送出（165，四支合計 660／660）。逐鏡 Gate（qa/gate-N4）FAIL：1.083 s 模型自行硬切成正面近景，之後站立不動、無橫移跟隨、領口紅線變整圈；僅 0–1.04 s 與首幀連續。預算已用完，不重做；N2、N4 的用法待使用者決定。

## 2026-11-03 · user · N2／N4 用法（AskUserQuestion）

> N2：「合成时裁向手 (Recommended)」；N4：「只用前 1 秒当插入镜 (Recommended)」

→ 使用者當次決定：N2 的「推近手」改由合成時的程式鏡頭達成（只用 1.0–3.5 s）；N4 只用硬切前 0–1.04 s 當 S7 內的插入鏡。據此做 c13（c12＋N1–N4，花費 0）。
- c13 交付審看（c12＋N1–N4；未經 Harness verify-assembly，NOT_RUN）：
  - 內容：c11 的 20 個剪點都在原幀，歌、OH-B、S7v3、介面系統、歌詞、AI生成 不變（N 鏡頭來源畫面沒有平台標識，和 OH-B 一樣由合成畫上）。N1（gate PASS）3.833–4.333 s「September」，來源 1.000–1.500 s，片名延續在畫面上，接 I1 機房寬鏡（4.333–4.800，原 I1 改從第 9 拍起）再接 S3：不和 S3 同構圖的空走道直接相接，S3 DNS 框仍在空走道；拿掉 I2，3.8–5.7 s 剪點 4→3。N4（gate FAIL，使用者「只用前 1 秒当插入镜」）16.900–17.667 s，來源 0.000–0.767 s（最多讀到來源第 20 格，不過第 25 格），取代 I5。N2（gate FAIL，使用者「合成时裁向手」）取代 S8b 的 K5 靜圖 22.567–24.067 s，來源 1.000–2.500 s，程式鏡頭 [820,500,1.1]→[620,600,1.6] 推向手，識別框（R9）改框手（臉滑出畫面）；拿掉 I6。N3（gate PASS）25.500–25.900 s，來源 2.000–2.400 s，只在 S9a 之前。副歌切離 1.33 s／7.03 s＝19%。c12 可重建（`comp/src/main-c12.js`、`comp/inserts-c12.json`、`comp/chorus-c12.json`，重算 events.json＝c12 的 1e3a3e4f…）。來源 SHA 與入出點在 `ep01/v2/qa/film-c13/assembly-review.json`、`review/film-c13.html`。
  - 檔案：render `renders/EP01-film-c13.mp4` 54e5528eeb3289001d755f2bbadfd2c3b9a1d2c9e2bdd1cfd2aba871d2355cc1；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c13.mp4` e14439127c2b73983a025a56db7ad72bbaaecc3c2bcfff1afec9ff1040c1db9a；副歌片段 `renders/review/c13-chorus-17.5-26.5.mp4` 148c43646419…；並排 `renders/review/c12-vs-c13.mp4` 80bc89884e35…；審看頁 `review/film-c13.html`。
  - 檢查：qa.py 全過（剪點 31/31、事件 20/20、閃爍最多 2 次／秒、strobe 0、單幀突跳 0、離群幀 0）；node 測試 42/42；ebur128 −14.2 LUFS／−1.0 dBFS。第 13 小節畫面動態 4.07→8.19（N2 推近＋雨）。花費：這版 0；四支鏡頭先前 660 積分。

## 2026-11-03 · user · c13 審看（AskUserQuestion）

> 「还不够，继续加」

→ c13 不定案，繼續增加內容；方向待使用者選。
- 使用者補充（拒絕選單後直接回覆）：「画面信息不够密, 故事内容太薄, 人物镜头太少太单调, captipon做的字体不行,参考作者,还有这个中文你直接不要了吧,看着很奇怪」
- 使用者：「费用你不用管」→ 本輪不再逐次詢問積分；付費生成新創作內容前仍先給參考預覽、取得認可（2026-10-30 使用者規則），帳本照常記錄實扣。
- 中文範圍：「只拿掉歌词的中文翻译」→ c14：去掉英文歌詞下的中文翻譯行，圖形標籤保留；字幕字型改照作者 lyric_headline（Helvetica 類粗體無襯線、左對齊、緊行距、關鍵字上色）；畫面資訊再加密（免費）。同時做故事／人物新鏡頭參考預覽（付費生成前先給使用者認可）。
- 使用者：「最后成片用即梦生成的我要1080p的,那个左上角的ai生成可以去掉的,我发现」→ 成片維持 1080p（即夢鏡頭與成片皆 1920×1080）。可見「AI生成」標識：改用即夢官方提供的無水印下載取得鏡頭（不自行裁切或塗抹平台標識），合成也不再畫自己的標識；檔案元數據的隱式 AI 標識保留；發佈時需在平台勾選 AI 生成內容聲明。此項取代先前「AI 標識須留在畫面內」的專案決定（使用者明確指令優先）；具體下載方式待在即夢頁面確認。

## 2026-11-03 · user · 故事人物鏡頭預覽（AskUserQuestion）

> 「6 支都生成 (Recommended)」

→ 認可 `trial/story/preview.html`：ST1–ST6 首幀＋純中文動作描述，Seedance 2.0 VIP 首幀 5 s 1080p，各 1 次；單支上限 165、帳本 6 次／990（使用者「费用你不用管」）；封存 `trial/story/preview-approval.json`。送出前照常：連續性報告、lint、一次性許可、逐鏡 Gate。
- 即夢「系统设置 → AI生成水印设置」：開關「导出内容去除AI生成水印」探查時已是開啟（主會話未更動；探查截圖 `ep01/v2/trial/watermark/`）。說明：開啟後導出內容不加「AI生成」明水印、保留「即梦AI」品牌水印，發佈時須自行用傳播平台標識功能聲明。實測：N1、N4 畫面四角皆無可見水印；舊鏡頭（如 S7v3）仍有左上「AI生成」。後續：合成不再畫自繪標識；舊鏡頭是否可重新導出為無水印版待測（不動已封存檔案）。
- c14 交付審看（c13＋三項改動；未經 Harness verify-assembly，NOT_RUN）：
  - 內容：剪輯與 c13 完全相同（31 個剪點在原幀，events.json 同 71a992e2…；歌、OH-B、S7v3、N1–N4、介面系統、圖形中文標籤、AI生成 不變）。① 拿掉每句歌詞下的中文翻譯。② 歌詞照作者 lyric_headline：Nimbus Sans Bold（URW base35，AGPL-3＋字型例外，授權檔 `comp/fonts/LICENSE-urw-base35.txt`，經 `motion-kit/tools/fonts.py --grotesk` 子集），一般句型、左對齊 x=76、行距 1.05、96 px（字高約 70 px）、關鍵字紅色，唸白與副歌同一樣式，逐字唱到才出現；`motion-kit/src/lyrics.js` 新增可選 `headline`（預設不變）。③ 畫面加密：左緣刻度尺、歌詞下段落標籤與句號、CUT 計數、識別框座標、S4／S5／S7／S9b 編號標註、S4c 探針座標、副歌沙盒小圖、S9a 門與解析器狀態；只重述片中已有事實。c13 可重建（`comp/src/main-c13.js`、`comp/inserts-c13.json`、`comp/chorus-c13.json`）。
  - 檔案：render `renders/EP01-film-c14.mp4` c76d2debd6eb68953d7043256da973445efe29d092ec5b2f42fbc6e389ff7a7b；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c14.mp4` 62a5ea7967f6e840c5210a03df2775a603ce7f2fcd03555f4b4373d0023b01c6；副歌片段 `renders/review/c14-chorus-17.5-26.5.mp4` 2dd1c50c2de2…；並排 `renders/review/c13-vs-c14.mp4` 395578e3b4f2…；審看頁 `review/film-c14.html`；`qa/film-c14/assembly-review.json`。
  - 檢查：qa.py 全過（剪點 31/31、事件 20/20、閃爍最多 2 次／秒、strobe 0、單幀突跳 0、離群幀 0）；node 測試 45/45；ebur128 −14.2 LUFS／−1.0 dBFS。花費 0。
- ST1–ST4、ST6 已送出（825，64,071→63,246）；ST5 連續性 not_ready（右側副本右耳耳掛、左側副本嘴唇可見），未送，待修首幀並重新認可。

## 2026-11-03 · user · c14 審看（直接回覆，附副歌眼睛特寫截圖）

> 「字体换了还有大小我觉得也不合适.然后这个[眼睛特写截图] 图片很奇怪,为什么突然晃一个眼睛过去.再就是这里没有加东西」
- 「这里」＝「就是这个眼睛镜头」→ 下一版：拿掉副歌「looked」的 K1b 眼睛插入（S8e），換成有內容的鏡頭；歌詞字號照作者實測（約 52 px 字高）縮小。
- ST5 修正首幀 ST5b（keyframes/raw/ST5b-a.png）：右側副本右耳已空、耳語者看不到嘴，但兩人領口紅線都在右領（背面視角應在左領）。未送、未給使用者認可；與 5 支逐鏡結果一起交使用者決定（再試或不用 ST5）。

## 2026-11-03 · user · 故事鏡頭用法（AskUserQuestion）

> 「只用合格的片段 (Recommended)」

→ 逐鏡 Gate（qa/gate-ST1..ST6）：ST2 PASS；ST1、ST3、ST4、ST6 FAIL，使用者當次決定只用各自的可用片段（ST1 0.5–2.5、ST3 0–2.5、ST4 0–2.0、ST6 2.5–5.0、ST2 1.0–3.5）；ST5 不用。c15：c14＋故事鏡頭；副歌「looked」的 K1b 眼睛插入換成 ST2 窺門；歌詞字號照作者縮小；合成不再畫「AI生成」。

## 2026-11-03 · user · 片長（AskUserQuestion）

> 「做成完整版 2–3 分钟」

→ 範圍擴大：EP01 從 30.5 s 擴成 2–3 分鐘完整版。需延長歌曲（新歌段落須給使用者試聽認可）、擴寫故事與分鏡（約 70–90 鏡）、大量新人物鏡頭（付費，使用者「费用你不用管」，仍先給參考預覽）。c15 照做，作為完整版前 30 秒與視覺系統的基礎。下一步：先出完整版大綱（結構、歌詞、故事段落、鏡頭量）給使用者認可。
- 完整版大綱與歌詞草稿 `ep01/lyrics-v2-full.md` → 使用者：「让codex审核下,我只需要质量其它都可以做」→ 交 Codex 外部審核歌詞與結構；使用者只把關成片品質，其餘製作決定由主會話自行處理（付費生成前的參考預覽規則照舊，會集中給使用者看）。
- Codex 審核（`ep01/reviews/2026-11-04-codex-lyrics-v2-review.md`）：指出事實越界（Every run paused、The city never knew、No alarm、離線→快取→低語的拼接）、段落過空、hook 太晚、bridge 意象堆疊。採用其修訂版 → `ep01/lyrics-v2.1-full.md`（84 小節 2:40，首個副歌 0:38，紅隊快取實驗明確另起並已修補，「And outside looked back」作為副歌後的 coda）。下一步：做 2:40 完整版歌（ElevenLabs Music 伴奏＋同一聲線人聲），給使用者試聽。
- 使用者問「你认可吗」（對 Codex 修訂版）→ 主會話：認可事實修正、結構提前、coda 與 bridge；不認可刪掉 v1 收尾句，改回「They found us whispering」放進第二主歌紅隊一節（語境已明說另一項測試，無混淆）。已更新 `lyrics-v2.1-full.md` 並通知做歌的代理。提醒：歌的好壞須試聽判斷；完整版時間軸全變，c15 的鏡頭與視覺系統沿用但剪點重排。
- c15 交付審看（c14＋使用者 c14 審看與「只用合格的片段」；未經 Harness verify-assembly，NOT_RUN）：
  - 內容：歌、c14 的 31 個剪點、OH-B、S7v3、N1–N4、介面系統、圖形中文標籤、Nimbus Sans Bold 不變，歌詞照舊不畫中文翻譯。① 歌詞字級照作者實測（EV 原片 1080p 第 1660／3316／5190 格：大寫字高 43／46／60 px、行距為字高 1.35–1.38 倍、左緣 x 74–80、每行 6–8 em）→ 72 px（字高 52 px，成片實測 52 px）、行距 0.98 em、每行最寬 600 px、x=76、左對齊、關鍵字紅色（c14：96 px、1.05、1040 px）。② 副歌「looked」的 K1b 眼睛 S8e（21.367–21.867）換成 S8p＝ST2 窺門（來源 2.6–3.1 s，和 S4 用的 1.0–1.7 s 不同段；程式鏡頭取景＋識別框 VIEW · OUTSIDE＋門縫編號框 01 LOOKED · 门缝）。③ 故事鏡頭只用可用片段（成片秒數／來源秒數）：ST1 2.867–3.367／0.5–1.0（S2 剪點「woke up」，在 S2 站姿特寫之前，R3；片名照常砸進）；ST2 9.033–9.733／1.0–1.7（「left open」，I3 門縫直接接 ST2 再進 S4c；S4 的兩個編號標註與联网量表跟過來）；ST3 14.0–14.8／0.5–1.3（「still.」，暫停 11 天、D+11、STILL 延續）；ST4 15.033–15.533／0.3–0.8（「train」，取代 c14 的 I4，S7 不變忙；與 N4 隔開，R4）；ST6 27.9–28.3／2.6–3.0（「closed.」白底反轉結束那一拍半，接 S9b；已修复照舊在 28.2 s 出現）。每支有臉的都加識別框與標籤。這些鏡頭實際約 24.12fps／121 幀（容器標 60fps），seq.py 的 fps 濾鏡按真實時間戳取最近幀，逐幀比對來源：單調、正常速度、靜音。④ 合成不再畫「AI生成」；舊即夢來源燒進去的標識沒有裁、糊、塗或放大，仍看得到：S1 0–2.867、I1 4.333–4.8、S3 4.8–7.1、S4c 9.733–11.467（只露 A01-v2 標識框下緣）、S6 子畫面 pipS5 13.433–14.0（約 30×14 px 的小標識）、S7 14.8–15.033／15.533–16.9／17.667–18.867、S9a 25.9–26.233／26.7–27.9（`ep01/v2/qa/film-c15/burned-label.json`）。c14 可重建（`comp/src/main-c14.js`、`comp/inserts-c14.json`、`comp/chorus-c14.json`；build.py 未改，以 c14 檔重算 events＝71a992e2…）。
  - 檔案：render `renders/EP01-film-c15.mp4` b246939af02f1141157415c0df6d8309e437061395155c23b091187390a7f10a；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c15.mp4` 9015b88463e1325a12a7b4266676bf604c05bcd40f31b8507e7c7412d884041e；副歌片段 `renders/review/c15-chorus-17.5-26.5.mp4` 51375ca0a87f4313de33d81cbfda4faad8c475ccc6e928534229395b9bb4ade1；並排 `renders/review/c14-vs-c15.mp4` c12f66786abd08b38ddd6beb4dc4c186f0f4455e7c44d1475523cdba080de5d2；審看頁 `review/film-c15.html`；`qa/film-c15/assembly-review.json`；events.json fb29736e6662…。
  - 檢查：qa.py 全過（剪點 35/35、事件 20/20、閃爍最多 2 次／秒、strobe 0、單幀突跳 0、離群幀 0）；node 測試 45/45；ebur128 −14.2 LUFS／true peak −1.0 dBFS。ST6 先放在拍點 27.633、再放 27.7 時，剪點落在白底反轉裡、被 CLOSED 蓋過（qa −3／−4 幀 FAIL），改到反轉結束的 27.9 後全過（ST6 因此只有 0.40 s）。花費：這版 0；五支故事鏡頭先前 825 積分（64,071→63,246）。

## 2026-11-04 · user · 換人物

> 「那这样人物我也准备换,之前的人物没有个性,太平和了」

→ production 決定：完整版換主角。照作者做法先做選角（casting call）：4 個個性鮮明的方向，各出一張角色設定圖（正側背全身＋頭肩特寫）與一張片中機房劇照，使用者看圖挑選；挑定後寫成文字 canon 放進每個提示詞，並先試幾張再批量。影響：現有有人物的鏡頭（OH-B、S7v3、N1–N4、ST 系列、K/P 系列靜圖）不再沿用；環境鏡頭、視覺系統與歌（聲線已認可）保留。選角用 Codex 生圖（不扣即夢積分），與做歌並行。
- 執行順序：與 Codex 討論（`ep01/reviews/2026-11-04-codex-execution-order.md`）並併入換主角 → `ep01/plan-full-version.md`（12 階段；使用者只在 A 挑人物＋試聽歌、B 完整預覽、C 試拍 GO/NO-GO、D 最終審看介入）。
- 選角 4 方向生成完成（`series/casting-v2/raw/`，審看頁 `ep01/v2/review/casting-v2/index.html`）：C1 叛逆、C2 偶像（首次兩張被生圖安全系統攔下，改闊腿褲＋厚底靴後重試一次成功，C2b）、C3 黑客少女、C4 女王。待使用者挑選。
- 注意：為支援試鏡，`gen/omnihuman.{py,cjs}` 加入 `OMNI_TRIAL`（指定試驗資料夾）與單元自帶人物圖；回歸檢查重跑 lint 時覆蓋了 `trial/omnihuman/OH-B/lint.json`（原為送出前紀錄，未進版本控制）。送出前 lint 通過仍可由 permit.json 證明（permit 只在 lint 通過時發出）；已在原地留 `lint-overwritten-note.json`。

## 2026-11-04 · user · 選角（AskUserQuestion）

> 「先做出来我看」

→ 每個方向做 5 秒唱歌試鏡（即夢數字人大師模式，同 OH-B 方法；底圖＝各選角設定圖右側頭肩特寫，唱已認可副歌人聲窗口；各自的性格表演描述），4 支約 120 積分。封存 `trial/screentest/preview-approval.json`；送出前照常連續性報告、lint、一次性許可。
- 試鏡：連續性報告 SC1–SC3 ready、SC4 not_ready（動作描述「几乎不笑」為否定式）。SC1–SC3 已送出各 30（63,296→63,206）。SC4 描述改為正向（「嘴角平直，神情冷峻…动作克制而有力量」），修訂記於 approval amendments，待複核後送出。另：首次填表讀到上傳後的過渡狀態（欄名「说话内容」），重讀一次即顯示「角色说 00:05」，許可關卡未放寬。
- 試鏡 SC4：連續性複核 ready（正向動作描述；報告已更新 approval 與動作 SHA），lint、許可通過後送出 30（63,206→63,176）。四支試鏡合計 120 積分，帳本已滿額、不再加拍。

## 2026-11-04 · director · 選角 v3 與音色（使用者原話）
使用者看完四支試鏡：「你得先生成角色给我,我看了刚才几个我都不是很满意」「c2还有点感觉,但是差点」「女主的音色也不对,一起给我看看」。
→ production：
- 不從 C1–C4 挑；照原作者 EV 的選角格式（`source_docs/wiki_consistency.md`）沿 C2 方向重出 4 個候選，每個三張：四面設定、機房走秀、黑白表情表；年齡寫死 28 歲與成熟輪廓。共用頭部＝黑色齊下頜波波頭＋厚劉海、左側紅挑染、銳利眼線、左耳亮紅燈入耳式耳機。Prompt 本 `series/casting-v3/prompts.md`。
- 音色 4 個候選，每個把已認可的 30.5 s v2 歌重配（副歌新聲音重唱、念白同描述設計聲音），保留現在的聲音作對照。紀錄 `series/voice-v3/README.md`。
- 試聽與選角合在 `ep01/v2/review/casting-v3/index.html`，等使用者挑人物與音色；選定前不做任何付費影片。
- 教訓：選角應先給靜圖挑定，再做試鏡影片；這次 SC1–SC4（120 積分）是在使用者挑定前做的。

## 2026-11-04 · director · 選角 v3 回覆（AskUserQuestion）
- 人物：「2的画风很好,但是脸太丑了」→ 按第二個候選 B 理解（已在回覆中說明，請使用者有誤即更正）：保留 B 的造型與畫風，換 4 種更漂亮的東亞臉（B1 清冷、B2 明艷、B3 甜酷、B4 溫柔疏離），每張臉出彩色近景特寫＋表情表＋走秀。Prompt 本 `series/casting-v3/prompts-B-faces.md`。
- 音色：「这几个声音不都行,还没有原声音好」→ 新做的 4 個聲音不用；暫回到原聲音（副歌 take 3 歌手＋Stella 念白）。voice-v3 只留作紀錄，不再追加音色生成，除非使用者再要求。
- 另：使用者「地址呢,每次让我选择应该上面先给地址」→ 之後每個選擇題的問題本身最上面先放審片地址。
- 完整版歌：前一個歌曲工作者（換帳號前因額度中斷、無法續接）已做完 `ep01/v2/song-full/mix/IRIS-01-full-v3.wav`（160.000 s，−14.08 LUFS／−1.22 dBTP，SHA 前綴 f520af41；MP3 f0db9432）、`timing/words.json`（41 句）與試聽頁 `song-full/index.html`。人聲正是原聲音（三段副歌＝v2 已認可演唱原樣貼回；念白＝Stella；橋段後兩句與 coda 由 bed-01 同一歌手唱）。因使用者改回原聲音，主會話把頁面上的「人聲是佔位」改為「人聲＝原聲音」，此版即完整版歌試聽版，待使用者試聽。工作者記下的已知限制：橋段第 4 句可能唱成 “a word”；尾奏（patch-02）只有安靜長音墊、最後一小節淡出。

## 2026-11-04 · director · 歌曲重做走 Suno（使用者回覆）
- 使用者：「都要重做我觉得.看下作者的.你可以和codex讨论下怎么做」→ Codex 方案 `ep01/reviews/2026-11-04-codex-song-redo.md`（整首生成、整首挑選、歌先於畫面）；「suno我可以充值你先别管」；誰來點：「我来点 (Recommended)」；隨後「我记得suno不是自动化了吗」。
- 只讀核對（suno-cli 0.10.1 doctor/list）：Pro、2470 credits、studio_api 可達；`captcha_preflight: required: true`。曲庫只有 10-25《失幀》6 首，沒有 IRIS；10-30 網頁 Create 前後餘額同為 2470 → 那次無生成、無扣費（原 UNKNOWN 歷史保留不改）。
- → production：因為每次生成都要真人驗證、專案不解驗證碼，生成按鈕由使用者在官網點（字段頁 `ep01/v2/song-suno/index.html`，歌詞 v2.2 `ep01/lyrics-v2.2-suno.md`）；取回（CLI 只讀 list/download）、統一響度試聽、分軌、節拍圖、逐字對齊由主會話自動完成。第一輪最多 3 次生成（6 首）。

## 2026-11-04 · director · IRIS 主角定為 G3（AskUserQuestion 回覆）
- 討論：最接近「C2」；好看「1和2我不知道怎么说」（介於好萊塢女星與超模）；年齡「二十出头」；「自然真实＋淡妆」。→ G 輪（`series/casting-v3/prompts-G-faces.md`，頁 `review/casting-v3/G-faces.html`）。
- 使用者選：「G3 灰绿眼睛」。→ 定稿文字與左右規則 `series/casting-v3/canon-G3.md`（canon v1）；補四面設定、修正左右的表情表、中景、遠景（`prompts-G3-canon.md`，以 G3 特寫為身份參考），給使用者過目後作為之後所有提示詞的人物錨點。
- G3 定稿頁 `review/casting-v3/G3-canon.html` 回覆：「脸还要调」；追問後：「服装不搭配,然后脸还要微调下,这种歌都是要带点不寻常,侵略性,不羁.」「前面说了」。→ 臉以 G3 頭像（只裁頭部）為身份參考往不羈微調；服裝出 4 套（破壞感白襯衫＋皮革束帶／誇張寬肩黑皮夾克／機房工裝改造＋紅線纜／黑色長漆皮風衣＋紅線纜），`series/casting-v3/prompts-G3-looks.md`。canon v1（白襯衫）暫不封存。
- 不羈造型頁 `review/casting-v3/G3-looks.html` 回覆：「表情别太刻意了,还有服装.一点都不现代化」→ 表情改自然放鬆、不做表情；服裝換當代秀場款 4 套（`series/casting-v3/prompts-G3-modern.md`）。
- 現代造型 4 套已生成，頁 `review/casting-v3/G3-modern.html`，等使用者挑選。
- 現代造型回覆：「我觉得现在都还可以,关键是我在想后面和歌搭不答」→ 頭部定稿 canon v2（`series/casting-v3/canon-G3.md`）鎖定；服裝 M1–M4 等 Suno 歌選定後對著歌挑，可按段落換造型。

## 2026-11-04 · director · 造型按背景重做（AskUserQuestion 回覆）
- 使用者：「现在只能说时尚,和任务背景像吗」→ 主會話：不像；且 G3 頭部的黑色齊下頜波波頭＋厚瀏海＋彩色挑染正是 `series/BIBLE.md` 禁止清單裡的 Claudia 元素（C2 起一路沿用、主會話先前未提醒）。提案：紅色只作訊號燈（左耳裝置紅燈＋左領口細紅燈線，回到聖經 canon）、服裝為副本統一的現代機能制服而她穿得不羈、黑髮換原創輪廓、臉保留 G3。使用者選「按背景重做 (Recommended)」。
- → 3 種髮型（不對稱短髮／狼尾碎髮／左側剃短），`series/casting-v3/prompts-G3-story.md`。canon v2 的波波頭＋紅挑染作廢。

## 2026-11-04 · director · Suno 由主會話操作網頁（使用者「suno你不是可以自动化吗我记得」）
- 使用者兩次問自動化；CLI 生成受 `captcha_preflight: required: true` 與專案「不讓程式解驗證碼」規則阻擋，改由主會話在使用者已登入的 Suno Chrome（`cp-e7be810d639e`，DevTools 19232）用專用分頁操作官方網頁：填 Custom 欄位、讀回逐字核對、每次提交前寫一次性 intent、只點一次 Create；驗證若出現交給使用者（三次都沒出現）。
- 過程：原 Suno 分頁的視口被不明客戶端改成 690×690，主會話不再碰它、改開專用分頁（用畢已關）；成功生成後 Suno 會清空表單，第 2、3 次先重填再核對；人聲性別一度被重複點擊取消，已改為冪等。
- 結果：3 次生成 6 首（v6，3:32–4:22），段落齊全、順序正確；30 credits（2470→2440）。試聽頁 `ep01/v2/song-suno/index-takes.html`（−14 LUFS 統一響度，附 v3 對照）。
- 造型：3 種按背景的髮型已出，頁 `review/casting-v3/G3-story.html`。
- Suno 6 首回覆：「我都觉得可以,不考虑时常,你得从观众和质量角度考虑,和人物背景符合」→ 主會話以本地客觀量測＋Gemini 盲聽（每首開頭 ≤120 s、一次性 operator）綜合選定。髮型 H1–H3：「发型都不行」；問方向：「你多做几种我看看」→ 8 種髮型近景（`series/casting-v3/prompts-G3-hair8.md`）。
- 8 種髮型回覆：「3 银白色短发」→ 定稿 v3 `series/casting-v3/canon-v3.md`；聖經新增「角色更新 v0.2」條目（不改寫舊條目）；補設定圖（四面、表情表、中景、遠景、副本群像）`prompts-v3-canon.md`。

## 2026-11-04 · director · 歌曲選定 T4（使用者「歌我选择好了t4」）
- 選定 Suno v6 T4（clip `e80848a2-3a60-4862-b17c-ba035ba4dba5`，261.56 s），母帶 `ep01/v2/song-v3/IRIS-01-T4.wav`（SHA 前綴 7471d6ff85cd），選定紀錄 `song-v3/selection.json`。之後的節拍圖、逐字時間、音樂地圖、分鏡都以它為準；舊 song-full v3 與其 words.json 失效。
- 客觀量測（`song-suno/takes/metrics.json`）：首句 9.9 s、副歌 61.3 s、副歌比主歌 +3.0 dB、F 小調、末段未測到升調、約 129 BPM、副歌 Whisper 全對；主歌一「September twenty. A training run.」被 Whisper 聽成「September 28 training run」→ 請使用者以耳確認，必要時局部修補（事實日期是 9 月 20 日）。
- Gemini 盲聽：T1 一次（110 s 窗口）HTTP 200 但回應形狀無效，operator outcome `EVIDENCE_GAP`、consumed、不可重試；使用者隨後自行選定 T4，未再呼叫。
- 後製：本地 Demucs（獨立 venv `~/.local/share/ai-video/demucs-venv`，沿用 miniconda base 的 torch 2.9 cu128，不改專案依賴）分軌 → 節拍圖 → 逐字對齊（Suno timed lyrics 與分軌強制對齊交叉核對）。
- 日期那句：「听着是 twenty，没问题」→ 不修。
- 定稿 v3 回覆：「脸还要微调,感觉太善良,乖乖女,和音色也不像,衣服更不像了」→ Gemini 盲聽 T4 人聲軌兩段（28 s 窗口，均成功；110 s 窗口先前 EVIDENCE_GAP 的原因判為長度）：主歌「low-pitched, breathy… slow, deliberate whisper… eerie, atmospheric」，副歌「young, high-pitched… slow, ethereal, melodic chanting」。→ v4：臉更冷更詭異＋4 套秀場款（`series/casting-v3/prompts-v4-looks.md`）。
- v4 造型回覆：「E3 雕塑白」→ 定稿 v4 `series/casting-v3/canon-v4.md`；聖經新增「角色更新 v0.3」；設定圖 `prompts-v4-canon.md`（四面、表情表、中景、遠景、副本群像）。

## 2026-11-04 · director · 檢查點 A 完成：人物定稿 v4 認可（AskUserQuestion 回覆）
- 頁 `review/casting-v3/V4-canon.html`：「可以，往下做」→ IRIS 人物以 `series/casting-v3/canon-v4.md` 為準（之後每個提示詞原樣寫入外形文字，左右規則照檢查）；歌為 Suno T4（`song-v3/`）。下一步：音樂地圖（階段 2）→ 整片分鏡（階段 4，多導演獨立提案後合併）。
- 逐字時間：Suno timed lyrics 與 Whisper 強制對齊 129/184 個詞差 >0.25 s（Whisper 偏早、Suno 句內偏晚）；改用 torchaudio MMS_FA CTC 強制對齊（作者的 wav2vec2 類做法）於 Demucs 人聲軌：與能量起點中位差 0.148 s（Suno 0.196 s），無一詞 >0.3 s；能量起點對連唱不可靠（窗口邊界效應），不作為驗收。→ `song-v3/timing/words.json`＝CTC 版；Suno 版保留 `words-suno.json`。動畫分鏡階段以原速觀看再核。

## 2026-11-04 · director · 階段 2–5：音樂地圖、整片分鏡、動畫分鏡
- 音樂地圖 `ep01/v2/song-v3/music-map.json`（140 小節、段落、重音、升騰）；逐句時間 `lines-suno.json`；逐字時間 CTC `timing/words.json`。
- 整片分鏡多導演：導演 A（主會話，`ep01/v3/board-director-A.md`）與導演 B（Codex，`board-director-B.md`）獨立提案；總導演合併為 `ep01/v3/board.md`（89 單元、261.56 s；`director-coverage.json` schema v4，open-video 校驗 passed）。合併取捨：密度取 A；她開口取 B（主歌「October first…」對鏡念）；Drop 副本閉眼滅燈取 B（避免讀成集體醒來/逃離）；Coda 不新增人類觀察者、Outro 由她自己念並關門取 A（歌聲就是她）；玻璃倒影用合成取 A。
- 獨立概念檢查（read-only critic）進行中（第一次因帳號切換中斷，已重派）。
- 動畫分鏡 a1：映射表 `ep01/v3/shots-map.json`（89 單元 → 靜圖、代碼鏡頭、60 種圖形組件、視點）、規格 `ep01/v3/animatic-spec.md`，交執行代理實作與渲染；36 張靜圖替身 `ep01/v3/plates/prompts.md`（人物文字原樣取自 canon v4）生成中。
- 靜圖替身 36 張生成完成（`ep01/v3/plates/raw/`）；主會話逐張檢查，8 張重做為 `-b`：P-backlit（模型自加立式麥克風、非逆光）、P-collar-off 與 P-dark-hall（副本黑髮，應同款銀髮）、P-gaze 與 P-headturn（要近景得全身）、P-lab（測試室副本領口燈亮，違反「只有 IRIS 亮」）、P-speak-aisle（要半身）、P-threshold（多出大衣下擺）。`shots-map.json` 已改指 `-b`。
- 獨立概念檢查（critic，read-only）判 REVISE：①離線/修補後畫面升級（門縫再亮、紅線沿街擴散、門大開、拉向城市）讀成更大的突破，違反「有限存取」事實紀律；②唱句只有 55% 在她嘴上（U025/U053/U070 等，終副歌僅 3/8 為數字人，「Relax」無嘴）；③紅隊測試用同臉副本、接她的反應、修補後立刻耳語，易讀成同一事件或修補後仍密談；④人物單調（數字人全是靜止近景、侵略性只剩看鏡頭）；⑤監控全景接身體局部極近景＝被否的「晃眼睛」剪法；⑥歌詞列手填，4 處錯位超過一拍；⑦ST5/ST6 已失敗的群像與手推門原樣保留。→ 主會話全部採納，改分鏡 v2（見 `ep01/v3/board.md` 的「概念檢查裁決」）。
- 分鏡 v2 完成（2026-11-04）：`ep01/v3/build_board.py` 改寫，85 鏡、261.56 s、平均 3.08 s；open-video validator passed。歌詞列改由 CTC 逐字時間生成（不再手填）；腳本逐詞校驗領唱都落在「她在唱」的鏡頭上（領唱 67.1 s：數字人 62.7 s＋U073 監控牆 4.4 s），時間軸無縫無疊，不過就不出表。刻意取捨：主歌報道式念白作畫外（只有 October first 由她當面說）、預副歌二閉嘴（燈的心跳＝在心裡說，並與剛修補的紅隊通道分開）、結尾 Three forty-eight 用翻牌。U018 手推門改靜圖＋代碼鏡頭（ST6 手接觸失敗過），群像 U006/U045/U051 試拍先做首幀測試。事實卡依 fact-check 改寫（DNS → external chatbot、只指最強模型的相關工作、controls and monitoring added、附出處，不含 03:47/03:48）。`board.md` 含「概念檢查裁決」；映射 `shots-map.json` 由新的 `build_shots_map.py` 生成（graphic_text 只放屏上英文，graphic_note 中文說明不畫，target/cue_s 可選）。
- 動畫分鏡執行代理第一次被帳號切換中止（`ep01/v3/comp/src/` 已寫 11 個模組，未渲染）；規格 `animatic-spec.md` 改成 v2 後重派，接續半成品。
- v2 靜圖 23 張（`plates/prompts.md`「v2 新增」，人物文字由腳本從 canon-v4 原樣拼入，Codex image_gen 4 路，各一次，全部 delivered，實際尺寸 1672×941）。主會話逐張看：P-queue-cu、P-queue-sing、P-lens-face 的副本立領燈線或耳掛亮紅（違反「只有 IRIS 亮」），P-catwalk、P-floor-line、P-line-ms 背景有紅燈、與副本同框易讀成副本亮燈，P-gap-mcu 景別與 P-gap-face 幾乎相同 → 7 張 `-b` 重做。P-trace-profile、P-glass-profile、P-hand-lens 背景各有一顆小紅燈但畫面裡沒有副本，保留。副本耳掛：可有可無，但一律不亮（canon 副本文字本來沒有耳掛；P-row-lit 的副本戴著不亮的耳掛，可接受）。
- v2 靜圖 7 張 `-b` 全部 delivered，主會話逐張放大檢查副本與背景：P-queue-cu-b、P-queue-sing-b、P-catwalk-b、P-floor-line-b、P-line-ms-b、P-lens-face-b 的副本與背景都沒有亮燈，只有她的耳掛與立領亮紅；P-gap-mcu-b 為腰以上中景，與 P-gap-face 可分。`shots-map.json` 改指 `-b`；U077（13 s 器樂空檔的凝視）由數字人改 Seedance 首幀（沒有歌聲可驅動嘴）；靜圖總覽 `ep01/v3/plates/index.html`（`build_plates_index.py`，44 張，按出場順序）。
- 試拍準備：數字人底圖改用閉嘴起始（上次可用的 K7 是閉嘴；Seedance 有首幀張嘴→靜音段張嘴露齒的 FAIL 先例）。第一次用 `codex_plate.py --edit-base` 只改嘴（P-gap-face-shut、P-gap-mcu-shut、P-gap-34-shut）失敗：底圖雖作為第一張附件傳入，image_gen 仍重畫成同一個通用正面近景，門縫與紅色側光消失、景別與角度都變了，三張不可用、不採用。改用原完整提示詞只把張嘴換成閉嘴重生 `-shut-b`。
- 試拍參考包（階段 7，尚未給使用者、尚未送出）：`ep01/v3/pilot/preview.html`＋`preview-inputs.json`（`pilot/build_preview.py`）。段落 U020–U029（54.69–89.52 s）＋群像測試 U045：數字人 5 條（U020 耳語＋長音、U021、U022、U025 長音＋視線轉回、U027；底圖 `-shut-b` 閉嘴版，P-gap-face/mcu/34 交替；音頻為人聲分軌該句前後各留 0.3 s，3.57–6.41 s）、Seedance 2.0 首幀 2 條（U023 門縫外城市、U045 群像跨線）；U024/U026/U028/U029 用動畫分鏡代碼鏡頭。動作描述沿用 OH-B 結構（鏡頭＋情緒＋唱歌狀態＋動作）並加「眉頭放鬆」；Seedance 一律「鏡頭固定」（歷史上寫運鏡 5 條 4 條失敗）、不寫「紅」字（ST1 紅燈事件）。上限每條 165、合計 1155，不重試；逐條「提交→取回→逐鏡 Gate→下一條」（N/ST 兩批曾整批提交後才補 Gate，這次不重複）。memory-keeper 檢索結論與 UNVERIFIED 清單見本輪；v3 生成車道（數字人每條自帶音頻與時長、Seedance 讀 v3 分鏡）交執行代理準備，不送出。
- v3 生成車道（`ep01/v3/gen/`，執行代理準備、未送出）：數字人每條自帶圖與音頻、頁面時長須等於音頻長度的下取整或上取整、上限讀自 approval；Seedance 讀 v3 分鏡與 `pilot/sd/preview-approval.json`。離線夾具在 /tmp，正反例皆符；v2/gen 2251 檔逐位元不變；倉庫內無 intent/permit/ledger。代理指出 U045 分鏡（站在線後、一步跨過）與首幀（已在線外）不一致 → 新首幀 P-floor-line-at-a（與副本同排、腳尖貼線），提示詞改為「一步跨過地面上的白色標線，停在線外」，`gen/unit.py` 的 U045 規格同步；動畫分鏡 U045 由線後切到線外。
- 動畫分鏡 a1 完成（階段 5，待使用者審看 B）：`ep01/v3/renders/IRIS-EP01-v3-animatic-a1.mp4`（1920×1080、30 fps、7847 幀、261.567 s、SHA-256 98f29814…4184，HyperFrames 610 s）；審片代理 `…-a1-review.mp4`（CRF 20，SHA-256 8ac60629…976d）；審片頁 `ep01/v3/review/animatic-a1.html`。兩個執行代理先後被帳號切換與單帳號用量上限（429）中止，主會話接手：確認逐單元 CTC 歌詞修正已接通、重建（85 單元、46 張靜圖、無占位、無未處理組件）、渲染、生成審片頁，並逐單元抽中點幀自查（視點規則、無中文、紅色規則、門縫一指寬、白色測試室無紅、事實卡原尺寸可讀）。已知問題寫入 `comp/review-notes.json`：靜圖重複（終副歌四鏡同一張逆光近景等，正式生成每個數字人鏡頭換景別角度）、U002 燈亮前是暗橙線而非全灰、事實卡出齊後只停留一秒多、六個簡版組件。花費 0。
- 使用者看過 Codex 審核後兩項決定（AskUserQuestion）：①門縫紅光「保留红光，补进定稿 (Recommended)」→ canon-v4「對應背景」與 BIBLE 追加「門縫外的光也是訊號紅；除她的燈與門縫外無紅；門關後只剩她的燈」，`gen/unit.py` 的 CANON_SHA256 更新（四段固定文字未變）；②預副歌二「保留闭嘴 (Recommended)」。Codex 審核全文與逐條裁決：`ep01/reviews/2026-11-04-codex-animatic-a1-review.md`（REVISE；主會話全部採納，改出 a2）。
- a2 修訂進行中：分鏡源 `build_board.py`（a1 存為 `build_board_a1.py`）與映射 `build_shots_map.py`（a1 存為 `build_shots_map_a1.py`）改為 84 單元、board v2-a2，validator passed；人聲時間更正（終副歌最後一句實際 211.85 s 唱完、213–222 s 器樂，第一輪 CTC 把 looked/outside 拉進靜音；尾聲句中間停頓），`song-v3/timing/words.json` 兩句重對齊（舊版 `words-ctc-v1.json`）；剪輯界面層（作者式，與監控 OSD 分開）與版式分工寫入映射 `chrome` 與 `animatic-spec.md`「a2 修訂」；新靜圖 P-spotlight-low、P-spotlight-cctv、P-gap-mcu-turn-shut-b（第一版把耳掛畫在右耳，重做）；試拍參考包按 Codex 第 5 條修正。執行代理實作與渲染 a2 中。
- 動畫分鏡 a2 完成：`ep01/v3/renders/IRIS-EP01-v3-animatic-a2.mp4`（1920×1080、30 fps、7847 幀、SHA-256 e487ab57…b5bca5，HyperFrames 697 s）；審片代理 `…-a2-review.mp4`（CRF 20，SHA-256 91ebc2a3…fb5f50）；審片頁 `ep01/v3/review/animatic-a2.html`；QA `ep01/v3/qa/animatic-a2/` 100 個對拍事件全 PASS（a1 的 4 個 FAIL 皆 0 幀）。執行代理第一次在 03:27 因原帳號用量上限（429）中止，接手者從 `comp/PROGRESS-a2.md` 與其 transcript 續做。主會話逐單元抽中點幀自查 84 鏡，只有三處小問題（U012 字幕 DNS 被拆成 D N S；開場右上 IRIS CLOCK 在 U004 翻牌前已寫 03:47；U084 燈亮前監控錄製點已是暗紅）→ a2.1 修正中（`build_shots_map.py` 的 chrome 改為 03:46→10.133 s 起 03:47；另兩處交執行代理），不影響已認可的 a2。花費 0。
- 檢查點 B（AskUserQuestion，問題最上面附 a2 審片頁與試拍參考包地址）：「认可，进入试拍」。→ 封存 `ep01/v3/pilot/preview-approval.json`（user-preview-approval/1，approval_hash 8acd2c1a…cce03，coverage_hash 87679931…，U020 U021 U022 U023 U025 U027 U045，14 件含 a2 審片代理；`pilot/build_preview_approval.py`）。參考包頁面沒問過身份豁免，故不寫 identity_waivers。
- 檢查點 B 後兩項決定（AskUserQuestion）：①U045 首幀模式無法附 IRIS 設定圖 →「改用多参考模式」（U045 延後：改可附身份圖的多參考模式、改提示詞與參考包、再給使用者看並封存）；②數字人動作文字含否定（SC4「几乎不笑」先例）→「同意这两处改写」（U020「头几乎不动」→「头部保持平稳」；U027「…嘴慢慢合上，停住不动」→「…嘴慢慢合上，静静停住」）。→ 參考包 r2 `pilot/preview-inputs-r2.json`（原包不動）、車道認可 `pilot/oh/preview-approval.json`（數字人 5 條，每條上限 165、合計 825、不重試）與 `pilot/sd/preview-approval.json`（僅 U023，165）、r2 封存 `pilot/preview-approval-r2.json`（812d30a0…）；皆由 `pilot/build_lane_approvals.py` 生成、不覆寫。即夢精確餘額 63,226（2026-11-05T01:31Z，唯讀）。試拍順序 U021 → U022 → U025 → U020 → U027 → U023，一次一條（連續性報告 → lint → 填表 → permit → 提交 → 取回 → 逐鏡 Gate → 下一條）。

- 2026-11-04 U021 试拍（即梦数字人，24 积分）不采用：逐镜 Gate FAIL（立领红线 1.12 s 起熄灭），使用者另判「人物表情不对」（开头太凶、唱 I 像在喊、后面神情发空、前后不连贯）。根因：身份参考 E3-close-a 与 shut-b 首帧提示词带「压迫感」「下巴压低眼睛向上」。依 EV 作者做法（常态面无表情带点好奇，唱歌闭眼张嘴，首帧本身在唱）重做 IRIS 身份参考，使用者选「新脸但改回波波头」并认可（「可以，定下来」），登记于 `referces/iris/`。
