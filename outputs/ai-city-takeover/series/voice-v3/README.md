# IRIS 換角 v3：音色試聽（voice v3）

使用者 2026-11-04：「女主的音色也不对,一起给我看看」（同時看選角 v3）。試聽頁：`ep01/v2/review/casting-v3/index.html`。
每個候選把已認可的 30.5 s v2 歌（`ep01/v2/song/mix/IRIS-01-v2.wav`）重配：副歌由 ElevenLabs Music 以新聲音重唱，念白與耳語用同描述設計的 TTS 聲音，拍點與歌詞照 v2 的 `placement.json`（`assemble_vo.py` 同一套）。

## 聲音（ElevenLabs Voice Design，已存入帳號）

| 候選 | voice_id | 描述 | 選用的預覽（3 選 1，依音高/氣聲量測） |
| --- | --- | --- | --- |
| VA 低沉煙嗓 | `6mk3ouimbCheKhxiHp3g` | low smoky alto, slightly husky, cool, deadpan, close-mic | 最低基頻、氣聲最多的一支 |
| VB 清亮自信 | `aNEltzsKIlazQAwqqFhj` | clear bright confident mezzo, crisp clipped diction | 基頻最高、起伏最大 |
| VC 沙啞有態度 | `tZ3NV87ZeaMB1iZ4T4R7` | raspy gritty edgy, teasing, mid-low | 基頻最低、顆粒最多 |
| VD 冷甜空靈 | `KBjgeGBIrDMMPCJIpBcm` | light airy cool, calm, distant, gentle breathiness | 中等氣聲 |

TTS：`eleven_v4`，stability 0.6，similarity 0.8（沿用 IRIS 念白設定）；VB 的耳語段放不進 v2 窗口，改 speed 1.15 重生成一次（舊檔在 `vo/VB/pre/superseded/`）。

## 副歌（music_v2，v2 伴奏 song_id `pQ32FmBFhBW3qmGDofjz` 作上下文）

| 候選 | 採用 take | song_id | 做法 | 實測（隔離人聲 Whisper） |
| --- | --- | --- | --- | --- |
| VA | `song/VA-r4` | `ff3GcSepX5DCKiYYXB2n` | 副歌放生成段開頭＋原尾奏，本地接回原前奏 | 0 s 進，兩遍完整 |
| VB | `song/VB-r3` | `nPe1DsT6s6E7fSy71tM1` | 同上 | 0 s 進，慢板只唱一遍 |
| VC | `song/VC-r3` | `k4ZhMkPQVzKSNYZYyE7b` | 同上 | 0 s 進，近兩遍 |
| VD | `song/VD` | `FaODYMmR9l2Wn2bg5VgI` | 原位補繪（前 18.3 s 原伴奏＋副歌＋原尾奏） | 約 18.7 s 進，近兩遍 |

未採用：VA/VB/VC 原位補繪兩輪（`song/V?`、`song/V?-r2`）人聲都晚進 3.7–6.2 s 或只唱半句——前面 18 s 純伴奏讓模型延續成器樂；改成副歌在生成段開頭後即準時進。VA-r3 唱不出可辨識歌詞；VB-r4 2.8 s 才進、仍一遍。

## 試過但放棄：用新聲音轉唱已認可副歌（speech-to-speech）

`sts/sts_choru_20261103_225646.mp3`（VA 聲音轉 `ep01/v2/song/isolation/chorus-18.6-26.0-isolated.mp3`）：基頻中位數低 2.6 半音（非整數，與伴奏不同調），對數基頻相關 0.35，有聲比例 0.78→0.59。不可用，改走重唱。

## 混音

`assembly/V?/`：各自的 `placement.json`（VA/VB/VC 的 pre 窗口 [30.75, 39.0] 拍，因副歌第一拍即進人聲；VD 與 v2 相同 [31, 39.5]），輸出 `assembly/V?/mix/IRIS-01-v2.wav`，皆 −14.0 LUFS、真峰 ≤ −1.1 dBTP；試聽 MP3 在 `ep01/v2/review/casting-v3/audio/`。

ElevenLabs 本輪用量：5,692 credits（帳號 5,876 → 11,568 / 40,000）。
