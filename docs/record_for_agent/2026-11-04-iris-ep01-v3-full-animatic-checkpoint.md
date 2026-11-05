---
record_kind: session_summary
topic_id: iris-ep01-v3-full-length-animatic-checkpoint
learning_eligibility: ineligible
---

# IRIS EP01 v3《Looked Outside》全长分镜与动画分镜 a1 检查点记录

Date: 2026-11-04（本机 PST，UTC−8；下文时间均为本机时间，取自文件 mtime 或 `logs/` 记载）

## Purpose

记下 EP01 完整版（4:22）计划阶段 5「全长动画分镜」完成时的真实状态：分镜 v2、静图、动画分镜 a1 的渲染与技术 QA、阶段 7 试拍参考包与离线生成车道。使用者尚未看片，下一步是检查点 B（动画分镜与试拍参考包一次审看）；但 02:49 起主会话已采纳 Codex 对 a1 与试拍包的审核意见，a2 与试拍包修订尚未实施（见 External Review And Adjudication），本记录记的是修订前的 a1 与现行试拍包。目的是让接手的 Agent 分清「已核对的事实」「Agent 自检」和「尚无人判的」。

这是检查点的事后整理，不是会话当下的第一手记录。由 `memory-keeper` 子代理于 2026-11-04 约 02:25–02:55 依主会话给的清单逐项对照磁盘文件与离线量测写成；状态快照以各文件 mtime 和下方 SHA 为准，主会话仍在继续工作（期间 QA 被重跑、`review/sheets/` 出现），之后的变化不在本记录内。没有调用付费或远程 Provider，没有生成媒体，没有读取 `.env`，没有 commit。核对手段只有只读文件读取与图像查看、进程与端口查看、`sha256sum`、`ffprobe`/`ffmpeg`（解码测量、响度与单帧提取，帧放在 `/tmp` 下独立的临时目录并已删除）、只读的 `validate_director_coverage.py` 与 `validate_evidence_identity.py`、对本机审片服务的 loopback 请求，以及一次 `experience` scope 的记忆检索（exit 0，结果 `[]`）。

路径自 `outputs/ai-city-takeover/ep01/`（下称 `ep01/`）起，除非标明 repo 路径。注意 JSON 里的 `*_utc` 时间是 UTC：`selection.json` 的 `selected_at_utc` 是 2026-11-04T07:37:50Z，相当于本机 2026-11-03 23:37；`logs/` 里的日期标签与本机日期不一定对得上。

## Current Runtime Truth

- **阶段与认可状态。** 位于 `ep01/plan-full-version.md` 的阶段 5 之后。检查点 A 已过：人物定稿 v4（`series/casting-v3/canon-v4.md`，使用者「可以，往下做」）、歌曲选定 Suno v6 T4（使用者「歌我选择好了t4」，`ep01/v2/song-v3/selection.json`）。检查点 B 待使用者审看：动画分镜 a1 与试拍参考包都**未获认可**，没有 `preview_approval`，没有 Final Acceptance。
- **动画分镜 a1 不是成片。** 内容是 85 个单元的静图替身（46 张）加 2.5D 代码镜头、基础图形、英文歌词，音轨是 T4 母带；人物不动，唱句都是静图加歌词。正式片里唱句换数字人真唱、动作镜头换 Seedance（`ep01/v3/comp/review-notes.json`「这一版是什么」「已知问题」）。
- **a1 与现行试拍包已进入修订，修订未做。** 02:46–02:49 主会话用 `omc ask codex` 取得只读审核（判 REVISE），并在 `ep01/reviews/2026-11-04-codex-animatic-a1-review.md` 顶部把全部意见裁决为采纳（其中门缝红光是否保留交使用者）；该文件的处理项指向 a2 与试拍包修订。记录定稿时，`shots-map.json`、`comp/`、`pilot/`、`gen/README.md` 的 SHA 都没有变，`decisions.md` 没有对应条目。是否先把 a1 交给使用者，还是等 a2，由主会话决定，本记录不替它判断。该次委派是外部 Agent 只读审核，不是 Provider 提交，也不是付费媒体生成。
- **本段没有 Provider 提交。** `ep01/v3/` 下没有任何 permit、intent、ledger、preview-approval、continuity-report、`job.json`、`operator-bound.json`；`ep01/v3/pilot/` 只有 `audio/`、`build_preview.py`、`preview.html`、`preview-inputs.json`；`outputs/ai-city-takeover/logs/ledger.md` 的最后一条是 Gemini 对 T4 人声轨的两次听审（早于检查点 A）。静图由 Codex CLI `image_gen`（`motion-kit/tools/codex_plate.py`）生成，共 82 次；`ledger.md` 没有这些静图的独立条目，「订阅额度、不计即梦积分」的性质由同工具先例推定（`ledger.md` 第 44 行 casting v3 同工具记「no Jimeng credits」），未另行验证。同日更早的付费或远程效果（试镜 120 积分、ElevenLabs、Suno 3 次生成 6 首、Gemini 听审）见 `ledger.md` 第 41–47 行，不在本记录范围，金额未重新核对。
- **全部未追踪、未提交、未推送。** `git status`：`?? outputs/ai-city-takeover/ep01/`（整个目录，含 `v2/`、`v3/`）；HEAD `5bb3ab7f`，`main` 与 `origin/main` 同步，没有 staged 内容。`.gitignore` 排除 `*.mp4`（第 10 行）与 `*.png`（第 13 行），所以三个渲染文件和 82 张静图只在本机，跨机器的身份只剩 SHA 与 JSON 证据。没有被忽略的字节并不少：整个 `ep01/` 有 4,743 个未追踪且未被忽略的文件、约 1.10 GB（其中 18 个超过 20 MB），仅 `ep01/v3/` 就有 213 个、约 94 MB（含 `comp/audio/IRIS-01-T4.wav` 的 50 MB 字节相同副本与约 38 MB 的 QA JPEG 联系图），`ep01/v2/song-v3/` 约 235 MB（T4 母带与四轨 Demucs 分轨）。整目录 `git add` 会把这些 WAV 与 JPEG 带进仓库。
- **工作树里其他改动不是本段工作。** 记录时 `git status --short` 有 415 条：36 个已修改、309 个已删除（其中 300 个是 T01 `phase1-t01/renders/work-*/captured-frames/` 的被追踪帧）、70 个未追踪。已修改文件里只有 `logs/runs.md`（01:59）与 `logs/decisions.md`（02:27）的 mtime 落在本段；`logs/ledger.md` 是 2026-11-03 23:44，早于本段；其余（`motion-kit/`、`src/`、`tests/`、`docs/`、T01 文件）最晚是 2026-11-03 05:41，不归于本会话。
- **本机审片服务。** 02:39 时 loopback `127.0.0.1:8768`（`motion-kit/tools/serve.py --dir outputs/ai-city-takeover/ep01/v3`）仍在服务：`/review/animatic-a1.html`、`/plates/index.html`、`/pilot/preview.html` 均 HTTP 200，审片代理 mp4 支持 Range（206）。进程是临时的（主会话报告审片服务曾被账号切换杀掉，本次未核实），用前再确认。

## Core Artifacts

| 产物 | 路径 | 状态 |
| --- | --- | --- |
| T4 母带 | `ep01/v2/song-v3/IRIS-01-T4.wav` | 使用者选定；261.56 s、48 kHz 双声道 PCM；−15.5 LUFS、LRA 7.1（ebur128，本次测量） |
| 分镜 v2 | `ep01/v3/board.md`、`board-table.md`、`director-coverage.json`、`build_board.py` | 85 单元；open-video validator `status: passed`（本次重跑）；歌词列与唱句校验来自 CTC 逐字时间 |
| 分镜 v1（存档） | `ep01/v3/board-v1.md`、`build_board_v1.py`、`director-coverage-v1.json`、`shots-map-v1.json` | 89 单元，被概念检查判 REVISE 后取代，只作历史 |
| 动画分镜映射 | `ep01/v3/shots-map.json`（`build_shots_map.py` 生成） | 85 单元连续无缝，0–261.56 s；`comp/data/units.json` 绑定同一 SHA |
| 动画分镜渲染 | `ep01/v3/renders/IRIS-EP01-v3-animatic-a1.mp4` | **被审看的那一版** |
| 审片代理 | `ep01/v3/renders/IRIS-EP01-v3-animatic-a1-review.mp4` | 同一渲染的转码（x264 crf 20，约 12.7 Mbps）；审片页只引用它 |
| 较早渲染 | `ep01/v3/renders/IRIS-EP01-v3-animatic-a1.hf.mp4` | **过期，不要审看或引用**，见 Evidence Boundaries |
| 审片页 | `ep01/v3/review/animatic-a1.html`（`comp/review.py` 生成） | 播放器加 85 单元表；85 张帧缩略与 46 张静图缩略在 `review/thumbs/` |
| 合成工程 | `ep01/v3/comp/`（`build.py`、`src/*.js` 共 11 个模块、`data/`、`engine.js`、`review-notes.json`） | 02:12:13–16 重建后渲染 |
| 技术 QA | `ep01/v3/qa/animatic-a1/`（`report.json`、`report.md`、4 张联系图） | 跑过两次，第二次 02:45:06 覆盖第一次（02:28:34），见 Animatic Technical QA |
| 外部审核 | `ep01/reviews/2026-11-04-codex-animatic-a1-review.md` | 02:49:48；顶部是主会话裁决表，下面是 Codex 原文；来源 artifact 在 `.omc/artifacts/ask/`（被 Git 忽略） |
| 审片联系图 | `ep01/v3/review/sheets/sheet-1.jpg`…`sheet-5.jpg` | 02:42:47 新增，1920×944，每张约 20 个单元的中点帧加单元标签；`animatic-a1.html` 未引用，`decisions.md` 无对应条目，用途未记录；标签里的中文显示为缺字方块（标签字体，不在视频里） |
| 静图 | `ep01/v3/plates/raw/`（82 张）、`plates/prompts.md`、`plates/index.html`（46 张） | 见 Plates |
| 试拍参考包 | `ep01/v3/pilot/preview.html`、`preview-inputs.json`、`build_preview.py`、`audio/`（5 个人声窗口与 `windows.json`） | 未获认可，未提交任何生成 |
| 离线生成车道 | `ep01/v3/gen/`（`README.md`、`unit.py`、`lint.py`、`operator.py`、`omnihuman.{py,cjs}`、`addnode.cjs`、`balance.cjs`） | 未运行；`README.md` 有过期示例，见 Remaining Risks |

SHA-256（记录时重算，路径相对 `outputs/ai-city-takeover/ep01/`）：

```text
7471d6ff85cd32e9fa5f795dcd78ec0d69402f38f6f8083c466d36a3e70ee4a5  v2/song-v3/IRIS-01-T4.wav
66d8641a5cc2820feff19ff88c295d3af47f7fb1a284c1f7ac1ea1c358cc5557  v3/board.md
ad89078d677798b124f0c85c4c3dd0b597f20f9c0da537e994a0ce77b393a09d  v3/board-table.md
a5f2437e839abb0554c73176266125d2313e7f3efc998a0fb3e22f288dd83c1a  v3/director-coverage.json
48d2fa29b304011b21238599dc042ecd25684166bf14079606fcc8337d173856  v3/build_board.py
0e8674268ac1faef2cbf3a2ea7438322320d8117162e7b98026bcad1c13c2f1f  v3/shots-map.json
82f9d830d8411fb67ea29cfb7770a0b8c44a8066a850ea507fb3fa6492b80ff9  v3/build_shots_map.py
07e0fa6b1454c40a50e5cb97402731162d7d76b550bd54132d14387bd5e2048a  v3/plates/prompts.md
b82c670ba387a13d39b8b8080a4eff44f3efabb86365137e4f8c8bacf53773b4  v3/plates/index.html
98f29814d13f908d2ed62f6868decb50df5dbd8e42d3edbd948aed5933964184  v3/renders/IRIS-EP01-v3-animatic-a1.mp4
8ac6062980dca96b9af1e85d2c12b51ab4b441ed0952c22362b282915b76976d  v3/renders/IRIS-EP01-v3-animatic-a1-review.mp4
606eff03a25c8fec910eee080a677bbbbf8a3ee91e3fd0e8092f42414b8fc2b1  v3/renders/IRIS-EP01-v3-animatic-a1.hf.mp4
04c4dbf48ff1a53afd352aa9446429ea24504fc96e68c9d3efb577115ffe8ac8  v3/review/animatic-a1.html
84bb74987407a4e6c89b02ee2ef91fcfc73f230ecb7a30ebe8c3901a95b03339  v3/comp/engine.js
dba86474ca64cc64b3e44d09ff7324c5c8bec88bb9848d1152705a9dcd51d057  v3/comp/data/units.json
908921eed84a274881d18a182bb3e488a86fa6a445fee0422d156cdda3ddc2a4  v3/comp/data/events.json
2275a9199a88c63a3bc995b85076126ee20beb284807468ea1ff89b9d1e0256b  v3/comp/review-notes.json
ca8cd9f17787acdd61c5b35204b49f5d7d5e35ae2b5dc0e559f6c5aa7a8014df  v3/qa/animatic-a1/report.json
b929e69c0e656c905f577be4f1e51574c0cf80dc2057d1855a6f5ae51e3a0e92  v3/qa/animatic-a1/report.md
1fb6a5034afaf612f2315849c72ea0aefc6196d83c6bc88809c6f80bdba85191  v3/review/sheets/sheet-1.jpg
88a2d3e38a8810c89987b81bfd7e4b8fccc6d228266245b92251a3dd930c34fe  v3/review/sheets/sheet-2.jpg
2aecd4bc0826227b496ee17dd75791821f7cd6951a033be66b22160a612493b1  v3/review/sheets/sheet-3.jpg
339813f4c7007ae726013f528b1b7df0eff5a927655aca7fe244087e408999ba  v3/review/sheets/sheet-4.jpg
18a82136c1b882d3ac65c527a728f3d5358386e4fd08691ccb5e68652dc45393  v3/review/sheets/sheet-5.jpg
588ae56a4f173359c493ec87619b39779cb943f11178c86885e349c7ad296bb7  v3/pilot/preview.html
1521f5ae809a9d6f8c2016049acfb6444d0174dbd0b807492225522b44f64138  v3/pilot/preview-inputs.json
184571a279e2713821ca3a7307c281460dc9ad1cef845db27d51229e5e13ae57  v3/pilot/build_preview.py
a15a937f6fa63e876d487eac26d5d879b6851a09403d4527861d820bbf5dcc42  v3/pilot/audio/windows.json
fb0974ff68aaa2729b094573c38ae282b3d0c81c999179e33c05522807723ab0  v3/gen/README.md
356d3d506b41cced2f0fd0a9bbfe1cebd4ce0ce136af5bae65ce5d78a1c4015b  v3/gen/unit.py
ec992510b052cb9ad686ff4d65592357bcdf0d02d10e77a05a54c686af537df3  v3/plates/raw/P-floor-line-at-a.png
1eb6555ae7c7f378eb79cf2b021c6258096c470cb711fa3a0772a0518a436169  v3/plates/raw/P-gap-face-shut-b.png
ffe0c323ef57309e72002e93811472d54490865b81b35f4a5afe96e809ef5bdf  v3/plates/raw/P-gap-mcu-shut-b.png
df5cc9f24b0ae079517e63440f5ee06df61fdcaf3e8a8868c8e9e6e322f11733  v3/plates/raw/P-gap-34-shut-b.png
61248d1238a7cef119676bd84244548cba615b83cf96866a00a3637dd4597426  v3/plates/raw/P-city-gap-a.png
6808251210e0142f56f5b9bca5630d9afe691d26ad0535500e0320fe143b4a74  reviews/2026-11-04-codex-animatic-a1-review.md
```

最终渲染（本次 `ffprobe`）：2,002,589,563 字节；h264（x264 crf 15）1920×1080 yuv420p、30 fps、7847 帧、视频 261.567 s；AAC 48 kHz 双声道，音频流 261.566 s，容器 261.588 s。音轨是 T4 母带的 AAC 编码，没有做响度归一（−15.6 LUFS、LRA 7.1；母带 −15.5 LUFS、LRA 7.1），动画分镜规格允许对齐到 −14 LUFS 但未做。审片代理 422,585,507 字节，同尺寸、同帧数。渲染耗时 610 s 与 `npx --no-install hyperframes render … -f 30 -w 4 --browser-gpu --quality high` 的参数形态来自主会话报告与 `motion-kit/README.md` 的用法；磁盘上没有保存这次渲染的命令记录，本次只能证实文件 mtime（引擎重建 02:12:16，渲染文件 02:22:42）与这个耗时相容。

## Session Work And Decisions

本段自检查点 A 起。使用者没有新的裁决，所有取舍由主会话自行决定（使用者早先原话：「让codex审核下,我只需要质量其它都可以做」，`logs/decisions.md`）。仍然有效的一条长期要求来自同日更早的条目：向使用者提问时，问题文字最上面先放审片地址。

| 阶段 | 本机时间 | 做了什么 | 证据 |
| --- | --- | --- | --- |
| 音乐地图（阶段 2） | 检查点 A 之后 | 140 小节（129.2 BPM）、段落、重音；逐句时间 `lines-suno.json`；逐字时间改用 torchaudio MMS_FA CTC 对 Demucs 人声轨强制对齐（47 句、184 词），取代 Suno 逐字时间与 Whisper 强制对齐 | `ep01/v2/song-v3/music-map.json`、`timing/words.json`；`timing/ctc-check.json`：CTC 与能量起点中位差 0.148 s（Suno 0.196 s）；`timing/check.json`：Suno 与 Whisper 有 129 个词差超过 0.25 s |
| 整片分镜（阶段 4） | 约 00:00–00:59 | 导演 A（主会话）与导演 B（Codex，外部 Agent）各自独立提案，总导演合并为 v1（89 单元）；只读独立 critic 判 REVISE（7 条，全部采纳，另有 2 条约束与规格补充）；改为 v2（85 单元） | `ep01/v3/board-director-A.md`、`board-director-B.md`、`board-v1.md`、`board.md`「概念检查裁决」 |
| 静图 | 00:11–01:59 | 82 次 Codex `image_gen`，见 Plates | `logs/runs.md`、`ep01/v3/plates/prompts.md` |
| 动画分镜（阶段 5） | 00:44–02:28 | 映射与规格；执行代理写 `comp/`（被中止两次）；主会话接手重建、渲染、审片页、`review-notes.json`、QA。主会话报告逐单元抽中点帧自查，本次没有复核 | 见 Process Facts |
| 试拍准备（阶段 7 准备） | 01:05–02:00 | 5 个人声窗口、`pilot/` 参考包、`gen/` 离线车道；U045 首帧改为 `P-floor-line-at-a` | 见 Pilot Reference Package |
| 外部审核与裁决 | 02:46–02:49 | `omc ask codex` 只读审核 a1 与试拍包；主会话全部采纳，处理项指向 a2 与试拍包修订 | 见 External Review And Adjudication |

概念检查七条的实质见 `board.md`，其中最要紧的两条：离线或修补后画面不得升级（有限访问只画成一条线、一个点、一指宽，门从不大开，最后由系统关上，高潮改成「被看」）；所有领唱句必须落在数字人嘴上（原先只有 55%）。刻意取舍留给检查点 B 请使用者判断：主歌报道式画外念白、预副歌二闭嘴、结尾翻牌 Three forty-eight、镜长平均 3.08 s（EV 是 2.0 s）。分镜 v2 不是使用者认可的最终分镜。

### Plates

`ep01/v3/plates/raw/` 共 82 张，全部是 1672×941 的 PNG，对应 `logs/runs.md` 的 82 条 Codex CLI `image_gen` 运行记录（2026-11-04 00:11:42 至 01:57:47 启动；每张一次，全部 `delivered`、exit 0，没有重试）；`prompts.md` 有 82 个对应小节。构成：v1 36 张加 8 张 `-b`；v2 新增 23 张加 7 张 `-b`；三分之四侧脸近景 `P-gap-34`；闭嘴数字人底图 `-shut` 3 张（失败）与 `-shut-b` 3 张；U045 首帧 `P-floor-line-at`。最终动画分镜用其中 46 张（`shots-map.json`）；其余是被 `-b` 取代的原图、被分镜 v2 弃用的图（`plate_revisions`）、失败的 `-shut`，以及只用于试拍的 `-shut-b` 底图。

`-b` 重做的原因（`logs/decisions.md`，主会话逐张放大目检）：v1 的 8 张是模型自加立式麦克风、副本黑发而非银发、景别不对（要近景或半身却出全身）、测试室副本领口灯亮、多出大衣下摆；v2 的 7 张是副本立领灯线或耳挂亮红、背景红灯与副本同框、景别与另一张几乎相同。这些是主会话对「只有 IRIS 亮」等封存约束的合规检查，不是使用者的观感判断。

### 闭嘴数字人底图与失败的 `--edit-base`

试拍的数字人底图要用闭嘴起始：上次可用的 K7 是闭嘴，Seedance 有首帧张嘴导致静音段一直张嘴露齿的 FAIL 先例（出自 `logs/decisions.md`，先例的原始证据本次没有重开）。第一次用 `codex_plate.py --edit-base` 对 `P-gap-face-a`、`P-gap-mcu-b`、`P-gap-34-a` 三张只改嘴：三次运行 01:21:29 同时启动，同一条编辑指令（`prompt_sha256` 前缀 `1e5ec2bd`），各附两张图（底图加身份参考 `series/casting-v3/raw-E/E3-close-a.png`），01:22 交付。本次逐对打开核对：三张输出都变成同一种泛用的正面近景，门缝与红色侧光消失，景别与角度都变了（中景 `P-gap-mcu-b` 被换成近景），嘴是闭的但已不是原图；三张字节不同。于是改用原完整提示词、只把张嘴改成闭嘴，重新生成 `-shut-b`（01:23:22 启动，只附 `E3-close-a.png` 作身份参考）：本次打开核对，三张都保留了门缝、红色侧光与原景别，嘴闭合。

边界：这是主会话与本次的 Agent 目检，不是使用者判断；`-shut-b` 尚未用于任何生成，「闭嘴首帧能避免张嘴露齿」没有被验证。`--edit-base` 失败不能外推成一般结论：更早的用法有记录可查（`ep01/v2/keyframes/prompts-v3-performance.md`、`prompts-v5-action.md`、`prompts-v6-story.md` 都写明以已认可图作编辑底图），`ledger.md` 第 27 行记其中 6 张表演静图获使用者认可，本次没有逐个重开那些图；本次失败还混有一个变量：第二张附件 `E3-close-a.png` 本身就是正面近景，三张输出恰好收敛到近景构图，两者没有被分开。

## Animatic Technical QA

`motion-kit/tools/qa.py` 对最终 `.mp4` 跑过两次，报告写在同一目录 `ep01/v3/qa/animatic-a1/`，后一次覆盖前一次（逐帧临时文件由脚本删除，`frames/` 为空）：

- **第一次，02:28:34 完成**（启动约 02:26；本次在运行中和刚完成时看到）。命令没有传 `--dur`、`--fps`（进程列表所见），而 `--dur` 默认 10.0（T01 测试片的时长），所以 `spec` 与 `frames_match_comp` 为 False：判定式是 `n_frames == round(args.dur × fps)`，7847 帧对 `round(10.0 × 30) = 300`，这是调用造成的，不是渲染缺陷。该份报告已被覆盖，不在磁盘上，它的哈希不再可核。
- **第二次，02:45:06 完成，是现行报告**（本次发现时进程已结束，没有观察到第二次的命令行；`spec`、`frames_match_comp` 翻为 True，与补传 `--dur` 约 261.56 相符，这是依判定式的推断）。`report.json` 的 `verdicts`：`spec`、`flash`、`frames_match_comp`、`pops`、`strobe`、`outliers` 为 True，`sync` 为 False。`motion-kit/README.md` 的用法示例没有提醒按片长传 `--dur`。

两次共同的内容（现行报告）：

- `spec`：1920×1080、30/1、7847 帧、yuv420p、bt709；音频 AAC 48 kHz 双声道；7847 帧与 261.56 s × 30 = 7846.8 → 7847 一致。
- `sync`：96 个事件（84 个剪点、12 个图形或静图切换提示），容差 ±1 帧，92 通过、4 失败：`cut_U053`（GROUND 单元）+2 帧，`U004_cue`（flipclock_0346_0347）−3 帧，`U056_plate1`、`U056_plate2`（照片翻转的两次切图）各 +2 帧。检测器按像素起变化点量，没有判断这 4 个是真错位还是检测假象（例如 U053 的 `invert_flash_OUTSIDE` 提示在 4891 帧通过）；两次结果相同；`review-notes.json`（02:25，早于两次 QA）没有提到它们。
- `flash`：最多 2 次/秒（上限 3），51 次转换；无单帧突跳、无 strobe 格、无离群帧。
- 每小节运动量共 139 小节：最高第 87 小节（t0 161.437 s）10.899，其次第 89 小节（165.14 s）6.435，其余最高 4.476（第 119 小节）。只是描述，不是节奏判定。
- 联系图 `sheet-eighths.jpg`、`sheet-shots.jpg`、`sheet-legibility-390.jpg`、`sheet-safe-area.jpg` 是给人看的，没有人看过的记录。

## Pilot Reference Package

`ep01/v3/pilot/preview.html` 与 `preview-inputs.json`（`build_preview.py` 生成）。段落 U020–U029（54.69–89.52 s）加群像测试 U045（144.80–147.33 s）；U024、U026、U028、U029 用动画分镜的代码镜头，不生成。页面是静态的（没有 `fetch`、XHR 或 POST）。

| take | 路线 | 片中窗口 | 输入 | 人声窗口（含前后各 0.3 s） |
| --- | --- | --- | --- | --- |
| U020 | 数字人 大师模式 | 54.69–60.50 | `P-gap-face-shut-b`（耳语加长音） | 6.41 s |
| U021 | 数字人 | 60.50–64.26 | `P-gap-mcu-shut-b` | 4.36 s |
| U022 | 数字人 | 64.26–67.23 | `P-gap-34-shut-b` | 3.57 s |
| U025 | 数字人 | 72.53–78.14 | `P-gap-mcu-shut-b`（长音加视线转回） | 6.21 s |
| U027 | 数字人 | 79.56–83.13 | `P-gap-face-shut-b` | 4.17 s |
| U023 | Seedance 2.0 VIP 首帧，5 s、1080p、16:9、无音频 | 67.23–69.90 | `P-city-gap-a`（门缝外的城市，无人） | — |
| U045 | 同上 | 144.80–147.33 | `P-floor-line-at-a`（她与闭眼副本同排、脚尖贴线） | — |

- 预算（`preview-inputs.json`）：数字人 5 条、Seedance 2 条，重试 0，单条 operator 上限 165，合计上限 1155；数字人页面上次读到的 5 s 单价为 30。上限是 operator 封存的 ceiling，不是价格；Seedance 本次没有任何单价读数。
- 两条 Seedance 申请用 `identity_waivers: ["IRIS"]`（首帧承担身份，`gen/README.md` 的说明），须随认可一并封存。
- 顺序与停止规则（`preview-inputs.json`、`gen/README.md`）：一次一条，提交、取回、逐镜 Gate（`shot-gate-reviewer`，`video-analysis` MCP）全 PASS 才做下一条；每条提交前要有 `continuity-supervisor` 报告、lint、一次性 permit 与精确余额；入口审核拒绝新脸、冻脸或牙齿碎裂或多手或身份漂移、页面音频时长既非下取整也非上取整、任一 outcome 非 `submitted`，一律停。
- 试拍没有覆盖 `board.md`「生成前要先验证的风险」里的：终副歌的长音（点名的 195.63–200.24 s，属 U067，6.77 s，是最长的数字人单元；试拍里最长的数字人单元是 U020，5.81 s，含前后留白的人声窗口 6.41 s）；群像 U006 与 U051（只有 U045 做首帧）；代码特效 U066（探照灯）与 U078（门缝遮罩）的真实效果，它们目前只在动画分镜里，探照灯是简版。

## External Review And Adjudication

02:46:55 主会话用 `omc ask codex`（文件自述 OpenAI Codex v0.166.0）取得只读审核，来源 artifact 在 `.omc/artifacts/ask/`（138,036 字节，被 Git 忽略）；02:49:48 写成 `ep01/reviews/2026-11-04-codex-animatic-a1-review.md`：顶部是主会话的裁决表，下面是 Codex 原文。Codex 的结论是 **REVISE**；它只看了五张中点总览、开场抽帧、分镜表与 `preview-inputs.json`，**没有以正常速度带声音看片**，并自述读不到 `qa/animatic-a1/report.md`（主会话注为 QA 正被重跑；本次看到该文件的 mtime 是 02:45:06，早于 Codex 启动的 02:46:55，二者对不上，原因不明）。

| Codex 的意见（摘要） | 主会话裁决 | 本次核对 |
| --- | --- | --- |
| 唱段仍是静帧，证明不了真唱；U020–027、U043–048 多为正面压下巴盯镜头；U005→006 接点 | 采纳：数字人单元写出不同的呼吸、重心、视线乐句；U005→006 用同侧耳挂、领线和视线对齐 | 未复核画面；静帧是 a1 的性质 |
| 长句（U025、U044、U067、U072）应在同一表演内切景别；U023–024、U045、U049、U059、U061、U075「标唱却切走」 | 采纳；后半是显示误差，校验改为重叠超过 0.05 s 才算 | 本次重算与「显示误差」相符：这些单元表里的「唱」「长音续」标注来自 CTC 领唱词边界 1–5 ms 的重叠（例如 `outside.` 结束于 67.233 s，U023 起于 67.23 s）；U049 的「合唱」是真实的（Drop 的 `Outside.` 重叠 0.98 s），它的「唱」部分同样只是 1 ms 重叠。这些单元里人声分轨仍有较弱能量（−34.4…−48.7 dBFS，唱单元中位 −30.4，无人声单元中位 −71.7），Agent 听不到，是否影响观感归使用者 |
| 事实画面：U013 插错网线像物理故障；U017–019 像自由浏览；U028 范围过宽；缓存应在离线前出现；03:47/03:48 标明虚构时钟；U036–040 标签放大 | 采纳：U013 改「DNS 控制缺口」图解；U017 只通到一个 EXTERNAL CHATBOT；U019 不横扫；U028 改 STRONGEST MODELS · RELATED WORK PAUSED；U010 加 INDEXED, CACHED PAGES；翻牌下加 IRIS CLOCK；测试室标签放大 | 未复核画面 |
| 版式仍像普通字幕；事实卡读不完；门缝大面积红光与 canon v4 冲突 | 采纳；**红光是否保留交使用者**。加全片贯穿的剪辑界面层（角标、计数、片名标签、底部事实滚动条），事实卡缩成可读摘要并延长 | U084 六行事实在约 3.8 s 内出现，与 `review-notes.json` 一致 |
| 试拍包：U025 首帧视线与动作矛盾；长音换气与「嘴不中断」矛盾；余量与时长映射未定义；U023、U045 可用区间未定义；1155 是上限非报价 | 采纳：U025 改首帧（先看门缝）；按实际音频写「长音—换气—长音」；写明音频起点对应的歌曲时间、按互相关对齐、成片带原曲审看；写明两条 Seedance 的可用区间与失败条件；上限措辞改正 | **属实**：`P-gap-mcu-shut-b` 里她直视镜头，而 U025 动作描述开头要她看向右侧门缝；U025 动作描述写「长音中间轻轻换气」而验收项写「长音期间嘴持续张开不中断」；U023、U045 生成 5 s 只用 2.67、2.53 s；1155 在 `preview-inputs.json` 是 `total_cap` |
| 可优化：U002 灯灭不彻底；终副歌动作递进；监控墙静止；视点接点动态检查 | 采纳，随 a2 处理 | U002 与监控墙已在 `review-notes.json` 里 |

主会话的处理项都指向 a2 与试拍包修订，**记录定稿时一项都没有落盘**。有两处会连带改动现有产物：门缝红光若改判，`-shut-b` 底图、`P-gap-*` 静图与试拍输入都要重做（它们现在刻意保留门缝的红色侧光）；U025 改首帧会改 `preview-inputs.json`、`pilot/build_preview.py` 与 `gen/unit.py` 的哈希与认可绑定。Codex 的画面观察本次没有逐条复核，只有上表标「属实」「相符」的几条做了核对。

## Verification And Evidence

| 项目 | 方法 | 结果 |
| --- | --- | --- |
| 渲染与代理 | `sha256sum`、`ffprobe` | SHA、1920×1080、30 fps、7847 帧、261.567 s 与主会话清单全部相符 |
| 较早渲染 `.hf.mp4` | 视频流与音频流 md5，U045 起点（144.9 s）单帧提取并目检 | 视频流与最终渲染不同、音频流相同；起点帧显示旧首帧 `P-floor-line-b`（她已走到线前），最终渲染显示 `P-floor-line-at-a` |
| 映射与工程 | 读 `shots-map.json`、`comp/data/units.json`、`comp/plates/` | 85 单元连续无缝；路线 HY 27、OH 24、GR 13、SD 13、PL 8；视点 iris 48、system 24、graphic 13；46 张静图全部在盘（`comp/plates/` 47 个文件含 `GROUND.png`）；`units.json` 的 `shots_map_sha256` 等于当前映射；`comp/data` 的 CTC 字词、节拍、重音、音乐地图与 `v2/song-v3/` 字节相同 |
| 分镜 validator | 只读 `validate_director_coverage.py` | `status: passed`，85 单元，261.56 s；带一条 UserWarning（相邻单元重复镜头类别，规则允许） |
| 唱句落点 | 用 `build_board.py` 同一规则对 `words.json` 与映射重算 | 领唱 62.66 s 在数字人（24 个 OH 单元）、4.42 s 在 U073 监控墙，念白 30.31 s，闭嘴 2.59 s，合唱 9.11 s；0 个领唱词落在非唱单元，与 `board.md` 的 62.7/4.4/30.3/2.6/9.1 相符。规则本身来自同一脚本，这不是独立判据 |
| 静图 | 数运行记录、读 `plates/raw/`、`prompts.md`、`index.html`、打开三组底图、`-shut`、`-shut-b` 共 9 张 | 82 条记录对 82 个文件对 82 个小节；`index.html` 46 张（`decisions.md` 当时写 44，以文件为准）；三组编辑失败与重生成如上 |
| 试拍包 | 读 `preview-inputs.json`、`windows.json`，重算哈希，查找 permit 等文件 | 5+2 条与表中一致；没有 approval、permit、intent、ledger、continuity-report 或 `pilot/oh`、`pilot/sd`；`ep01/v2/gen` 2251 个文件、没有 2026-11-04 00:00 之后的 mtime（与主会话报告的「逐位元不变」相容，没有基线可比字节） |
| 生成车道 | 逐文件比较 `v2/gen` 与 `v3/gen` | `addnode.cjs`、`balance.cjs` 字节相同；`lint.py`、`operator.py`、`unit.py`、`omnihuman.{py,cjs}` 有改动（与 README 说法一致）；`README.md` 的 U045 首帧与两个示例 SHA 过期 |
| 技术 QA | 读 `report.json`、`qa.py` 的判定与参数；两次运行的 mtime | 见 Animatic Technical QA；现行报告是 02:45:06 的第二次 |
| 外部审核 | 读审核文件，核对 `.omc/artifacts/ask/` 来源文件存在；对「标唱却切走」的 7 个单元重算 CTC 词重叠与人声分轨 RMS；对试拍包的几条矛盾核对图与文本 | 来源存在；重叠 1–5 ms（U049 另有真实合唱）；U025 首帧视线、换气、可用区间三条属实；其余画面观察未复核 |
| 人声分轨对 CTC 词 | 逐词量 `vocals.wav` 的 RMS（184 词） | 4 个词低于 −45 dBFS，集中在终副歌最后一句，见 Evidence Boundaries |
| 审片页与服务 | 读页面引用、loopback 请求 | 页面只引用审片代理 mp4；`/review`、`/plates`、`/pilot` 均 200，Range 返回 206 |
| 记忆检索 | `experience` scope 一次检索（索引未报 stale） | `[]`；另手工核对 4 份既有 Learning Claim，没有与本段重叠的 |

**没有验证**：主会话的逐单元中点帧自查（视点规则、无中文、红色规则、门缝一指宽、白色测试室无红、事实卡可读）；歌词与画面的原速观感；音轨与画面的对拍观感（Agent 不能听音）；渲染命令与耗时的原始记录；第二次 QA 的命令行；`review/sheets/` 的用途；`ccam-worker`、SendMessage 的具体行为；`v2/gen` 的字节级不变；同日更早各笔费用；`comp/`、`gen/`、`qa` 脚本的代码正确性与测试；任何 Harness receipt。

## Evidence Boundaries

- **没有人类判断。** 分镜 v2、静图、动画分镜都只有 Agent（主会话、独立 critic、Codex、本次对少量图帧）看过。「好不好看、怪不怪」只有使用者能判，节奏、字幕与成片观感未知；Agent 不能听音，音画对拍的观感只有使用者能判。
- **技术 QA 不是节奏或观感判定。** `qa.py` 检查规格、剪点与图形时机、闪烁、突跳、strobe 与离群帧；现行（第二次）报告 `sync` 仍为 False，4 个失败未分诊；第一次报告的 `spec`、`frames_match_comp` 为 False 是调用缺 `--dur`，已被第二次覆盖。
- **概念检查是 AI critic 的 REVISE。** 七条全部采纳是主会话的决定；分镜 v2 是否比 v1 更好，没有人类证据。critic 与导演 B 的意见都只是建议。
- **唱句落点校验只证明「按 CTC 字词时间，领唱词都落在标了『她在唱』的单元里」。** 它不证明数字人的对嘴能力（v3 还没有任何一支数字人视频），也不证明 CTC 字词时间准确：`ctc-check.json` 用的能量起点参照被主会话自己判为对连唱不可靠，没有真值，要等使用者原速审看。
- **CTC 字词时间在终副歌最后一句缺声学支撑（本次测量，未分诊）。** 对 184 个词逐词量人声分轨（`stems/htdemucs_ft/IRIS-01-T4/vocals.wav`）的 RMS：中位 −25.6 dBFS，只有 4 个词低于 −45 dBFS，其中 `looked`（210.60–215.63 s，5.03 s）−46.1 dBFS、`outside.`（216.59–221.01 s，4.42 s）−87.4 dBFS，另有 `I`（209.26–209.28 s，仅 0.02 s）−60.4 dBFS 与一个 0.3 s 的 `run`（63.6–63.9 s，−49.2 dBFS）。同一区间 `other` 分轨约 −25 dBFS、混音约 −19 dBFS，有能量。可能是 Demucs 把终副歌最后的持续长音归入 `other`，也可能那里本来没有清晰的人声；Agent 不能听音，分不出。这影响 U072（`I just looked`，209.26–215.27 s）、U073（监控墙，215.27–218.98 s，board 计为领唱 4.42 s）与 U074（218.98–221.01 s）的「她在唱」依据；强制对齐总会给词分配时间，所以它们的字词边界与「她在唱」标注缺少声学佐证，不能当已验证。
- **`.hf.mp4` 是过期渲染。** 它的 mtime（02:08:25）早于 `comp/` 引擎与数据重建（02:12:13–16；`shots-map.json` 的 U045 首帧改动在 02:00:30，`comp/data` 随后才重建）；视频流与最终渲染不同、音频流相同；144.9 s 的起点帧显示它仍是旧的 U045 首帧。「它是更早的一次渲染」是依 mtime、流哈希与单帧得出的推断，磁盘没有记录为何留下它。
- **动画分镜里的唱歌静图是张嘴版，试拍的生成输入是闭嘴版。** QA 表里 U020、U021、U022 用 `P-gap-face-a`、`P-gap-mcu-b`、`P-gap-34-a`（张嘴），试拍输入是 `-shut-b`。生成前的认可与封存必须绑定后者。
- **ceiling 不是花费。** 试拍包的 165 与 1155 是 operator 封存上限，不是价格或预计花费；本段没有新的积分消耗，也没有新的余额读数。

## Process Facts

- 本段有三次子代理运行被中止（`logs/decisions.md`）：只读 critic 的第一次（账号切换，已重派并交出 REVISE）；动画分镜执行代理的第一次（账号切换；`comp/src/` 已写 11 个模块、未渲染；`animatic-spec.md` 改成 v2 并写明「已有的半成品，先读懂并复用，逐个确认完成度」后重派）；第二个执行代理（账号切换或单账号用量上限 HTTP 429；`decisions.md` 对两个执行代理合写为「先后被账号切换与单账号用量上限中止」，没有逐个标明）。主会话从磁盘状态接手，完成重建（85 单元、46 张静图、无占位、无未处理组件）、渲染、审片页与自查。
- 主会话另报告：被中止的子代理无法用 SendMessage 续接；一个 `ccam-worker` headless（acceptEdits）会话写不了 `/tmp`；审片服务曾被一并杀掉。这几点在仓库文件里没有痕迹，本次**未核实**；记录时审片服务在线。
- v3 生成车道由执行代理离线准备（`decisions.md`），没有 intent、permit、ledger；该代理发现 U045 的分镜（站在线后、一步跨过）与首帧（已在线外）不一致，促成新首帧 `P-floor-line-at`，动画分镜 U045 因此先显示线后、146.07 s 切到线外（QA 表 `U045_plate1`）。
- 以上是本段的有界经验，不外推为一般规则。

## Superseded Or Displaced Prior Claims

- [2026-11-02-iris-ep01-v2-production-and-realignment.md](2026-11-02-iris-ep01-v2-production-and-realignment.md)：其中作为现行方向的「EP01 不再付费生成」「以 c1 为底收尾」，以及 v2 时期的人物、歌曲（`IRIS-01-v2.wav`）与 15 支生成片，已被 2026-11-03 起使用者「做成完整版 2–3 分钟」与 2026-11-04 换人物、换歌、重做分镜取代。本次已在该文件顶部加 supersession notice；没有 `retrieval: retired`，因为 v2 时期的事实（Gate、SHA、费用链、证据边界）仍作为历史有效。其中 561 积分待确认等未结算项本次没有重新核对。
- `outputs/ai-city-takeover/logs/status.md`（非 record）：2026-10-30 的「歌曲阻塞…不能继续付费视频」「EP01 延后」仍写成当前状态，实际已过期。它是被追踪的已修改文件，本次保持只读，是否更新由主会话决定。
- `logs/decisions.md` 是追加式日志，同一份里并存 89 单元（v1）与 85 单元（v2）：以 `shots-map.json`（85 单元）为准。
- 「EP01 不再付费生成」被取代不等于已授权付费：任何 Seedance 或数字人提交仍要逐条 `preview_approval`、连续性报告、lint、一次性 permit 与逐镜 Gate。

## Remaining Risks Or Next Work

- **检查点 B 未过，且 a1 与现行试拍包已被主会话判为待修订。** 动画分镜与试拍参考包都等使用者；a2 与试拍包修订（见 External Review And Adjudication）未做，之后产生的新渲染、新 `preview-inputs.json` 与新哈希须另记，不要覆盖本记录的 a1 结论与 SHA。向使用者提问时，问题文字最上面先放审片地址（使用者 2026-11-04 的要求，`logs/decisions.md`）。
- **待使用者判**：门缝大面积红光是否保留（Codex 指出与 canon v4「红色限于左耳装置与左领信号灯」冲突，主会话交使用者决定）；它连带 `-shut-b` 底图、`P-gap-*` 静图与试拍输入。
- **终副歌最后一句的人声来源未确认。** 试拍窗口的做法是从 `vocals.wav` 切人声（`pilot/audio/windows.json` 的 `source`）；`outside.`（U073–U074，216.59–221.01 s）在该分轨里近乎无声，`looked`（U072，210.60–215.63 s）很弱（数字见 Evidence Boundaries）。阶段 8 若沿用同一做法，这几个数字人单元的输入音频会是静音或极弱；需先确认那里的真实人声在哪条轨（`other`、合唱？），这要靠使用者听或 `audio_understand` 的合格执行，不是本次能判的。
- **`gen/README.md` 有过期示例。** 它写于 01:54，早于 02:00 的 U045 与预览包改动：U045 首帧写成 `P-floor-line-b.png`（现为 `P-floor-line-at-a.png`，见 `gen/unit.py`、`preview-inputs.json`）；`preview_page`、`preview_inputs` 的示例 SHA `cb99a412…`、`544ba5d9…` 不是现在的 `588ae56a…`、`1521f5ae…`。封存认可前须以当前文件重算，不要照抄；本次没有跑 lint 验证其后果。
- **试拍前置条件都未做**：`preview_approval` 封存（含 `identity_waivers`）、`continuity-supervisor` 报告、lint、一次性 permit、精确余额读数。
- **QA**：`sync` 的 4 个失败未分诊（真错位还是检测假象）；`motion-kit/README.md` 的用法示例应提醒按片长传 `--dur`（是否修改由主会话决定，本记录不改）。第二次 QA 的命令行与 `decisions.md` 都没有留下记录（最后一条 02:27 早于它）。
- **联系图与中点帧会截到滚动中的字样**：`review/sheets/` 与 QA 联系图取单元中点帧；翻牌类单元会被截到滚动中的值。例如 U009（26.63–28.50 s）的中点缩略图显示「SEC 92」，本次抽帧显示它依次滚过「AFC 47」（27.2 s）、「SEP 92」（27.6 s）、「SEP 15」（28.0 s），在 28.0–28.1 s 之间落定为「SEP 20」，约 0.4 s 后切到 U010；这是翻牌动画本身，终值与歌词一致。落定后只停约 0.4 s，正常速度下读不读得清由使用者判。
- **动画分镜已知问题**（`review-notes.json`）：静图重复（终副歌 U067、U069、U072、U074 同一张逆光近景，U052、U057、U076、U077 共用一张正面近景等）；U002 灯亮前是暗橙线而非全灰；U084 事实卡出齐后只停约一秒；六个简版组件（探照灯、城市灯光呼吸、灯重新亮起、倒影、雾、监控墙）。
- **试拍覆盖缺口**：见 Pilot Reference Package。
- **提交卫生**：整目录 `git add` 不可取（整个 `ep01/` 约 1.10 GB 非忽略字节，含 WAV 与 JPEG，而 mp4 与 png 被忽略）；需选定精确路径，媒体靠 SHA 与 JSON 证据。本记录与 2026-11-02 记录都是未追踪文件，后者被加了 notice，是否一并提交由主会话决定。
- **磁盘**：`ep01/v3` 约 4.8 GiB，其中三个渲染文件约 4.43 GB，另有 `renders/samples/` 三个样片约 0.33 GB；`.hf.mp4`（约 2.0 GB）是过期副本。媒体被 `.gitignore` 排除、没有其他备份，清理或归档由主会话与使用者决定。
- **共享能力**：这一段新建的控制多在作品专属脚本里，例如领唱词必须落在数字人嘴上的硬校验在 `ep01/v3/build_board.py`，U045 首帧与分镜不一致靠执行代理发现。按 Product Invariants 它们只是验证案例，不是共享能力；是否提升到 `open-video` 或 Harness 由主会话与使用者决定，本记录不提议改 Skill 或 Gate。
- **工程验证**：本检查点没有看到独立 code review 或 Harness receipt 的记录；按「成片优先」，使用者认可成片后才跑分级验证并 commit/push。

## Agent Guardrails

- 不把动画分镜 a1、技术 QA、分镜 v2、critic 与 Codex 的 REVISE 或 Agent 的目检当成使用者认可、Final Acceptance 或质量验收；Codex 的画面观察未经复核，不当事实引用。
- 审看与引用只用 `IRIS-EP01-v3-animatic-a1.mp4`（`98f29814…`）及其代理 `…-review.mp4`（`8ac60629…`）；`.hf.mp4`（`606eff03…`）是更早的渲染。
- 试拍参考包获认可并封存前，不运行 `ep01/v3/gen/` 里任何一条命令，不建 intent 或 permit，不提交；认可要绑定的是 `-shut-b` 底图、`P-city-gap-a`、`P-floor-line-at-a` 与 `pilot/audio/*.wav` 的当前 SHA，不是动画分镜里的张嘴静图。
- 不照抄 `gen/README.md` 示例里的 SHA 与 U045 首帧，以当前文件重算；U025 首帧与动作描述的矛盾、门缝红光的决定落定之前，不封存试拍认可。
- 不把 CTC 字词时间在终副歌最后一句的位置当成已验证的「她在唱」；也不假定那里的 `vocals.wav` 窗口有人声。
- 不把本次 `--edit-base` 失败写成「`--edit-base` 不可用」，也不把 `-shut-b` 当成已验证的闭嘴首帧方案。
- 引用 QA 只用 02:45:06 的现行报告（`report.json` `ca8cd9f1…`）；第一次报告已被覆盖，其中 `spec`、`frames_match_comp` 的 False 是调用缺 `--dur`，不是渲染缺陷；现行报告 `sync` 的 4 个失败不要当成已确认的错位，也不要当成已排除。
- 不把「本段没有付费」扩大成「同日没有任何付费」：见 `ledger.md` 第 41–47 行。
- 不对工作区做 `git clean` 或整目录 `git add`；`ep01/` 的媒体被 `.gitignore` 排除、没有其他备份。
- 向使用者提问时，问题最上面先放审片地址（使用者要求）。

## Learning Assessment

`record-ai-video-session`：recorded。`distill-ai-video-learning`：**no_candidate**，不建立 Learning Claim，不修改 Skill、Policy 或 Gate，不标 `ADOPTED`；本记录标 `learning_eligibility: ineligible`，因为下列近似候选都不满足证据门槛，不是证据不存在。

- 检索 `experience` scope 得 `[]`；既有 4 份 Learning Claim 里没有与本段重叠的（两份提到首帧，分属 H3 与 Vidu，且都是 `PENDING_CONFIRMATION`）。
- **`--edit-base` 只改嘴失败**：3 组配对在同一批、同一指令、同时启动，不是独立尝试；混有变量（第二附件是正面近景）；有反例（更早的 `--edit-base` 用法含使用者认可的 6 张表演静图）。要成立至少需要第二次独立发生，或对同一底图做受控对照（有无身份参考、编辑对重生成），并带精确的请求与结果身份和 Evidence Index。
- **多副本场景的静图首轮违反「只有 IRIS 亮」等封存约束**（v1 8/36、v2 7/23 被主会话标记，`-b` 全部交付）：判定是 Agent 目检，同工具同日，没有使用者或下游结果；目前做法（放大目检加 `-b`）已在执行，没有可提议的 owner 改动。
- **CTC 强制对齐优于 Suno 与 Whisper 的逐字时间**：只有一首歌，没有真值，使用者原速审看还没发生；更早的歌 v2 那次 0.31 s 偏差来自另一条管线；本次又测到终副歌最后一句 CTC 词时间缺人声分轨支撑（见 Evidence Boundaries）。属 `SINGLE_CASE`，且已有局部反面数据。
- **采纳独立预审**：现在有三次事件（2026-11-03 Codex 歌词审核、2026-11-04 critic 判分镜 v1 REVISE、2026-11-04 Codex 判 a1 与试拍包 REVISE），对象各不相同，主会话都全部或大部分采纳。但三次都是 REVISE，没有一次 APPROVE 作对照，不知道审核者是否总是给 REVISE；采纳后的版本也没有结果层验证（使用者还没判过修订后的成品）。不足以提议改 Preflight 或 Gate。等使用者在检查点 B、C、D 的判断出来后，可回头看被采纳的意见与使用者否决点是否对得上。
- **子代理被账号切换中止**：属编排环境事实，没有可校验的产物身份，不是 AI-VIDEO 产品层经验。
