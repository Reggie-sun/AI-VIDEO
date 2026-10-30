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
