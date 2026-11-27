# s031–s048 r3 补丁计划（SG12 · SG15 · SG16 · SG17 · SG18 · SG20；取代 r2）

2026-11-25。起因：SG12 a-3（9e5230d5…）原生音轨与口型是中文，prompt 引了歌词中文译文。使用者原话「删掉译文、精简动作后重拍 (Recommended)」（`logs/decisions.md` 2026-11-25 最后一条）。认可页：http://127.0.0.1:8769/pilot/s031-048/r3/index.html。

**本补丁取代 `r2/r2.patch`**：r2 的全部改动（SG15 / SG17 改绑句序、SG20 首帧 p048-w2 与左臂一句、s047 静图）都在 r3.patch 里。r2.patch 不要再应用；`r2/`、`submit-r2/` 留作历史，不改。

主会话在**当前一批（INS33、INS37、INS41、SG19、MO15）全部提交并 Gate 完之后**再应用。应用前不要写这六条的 approval；r3 包的 board sha 只有应用后才成立。

本步没有改 `gen/unit.py`、`gen/test_unit_lanes.py`、`board/*`、`director-coverage.json`、`excerpt/flash/s031-048-seedance.md`、`submit/`、`submit-r2/`、`r2/`、任何首帧或旧模板；没有提交、付费、写 approval、commit。新写的只有：`excerpt/flash/s031-048-seedance-r3.md`、`pilot/s031-048/submit-r3/{build.py,index.html,preview-inputs.json}`、`pilot/s031-048/r3/{index.html,r3.patch,PATCH.md,<UNIT>-approval.template.json ×6}`。

## 0. 前提（应用前核对）

应用前这四个文件必须仍是本补丁的底（与 r2 的底相同；否则 `git apply --check` 会失败，失败就停下重做 diff，不要手改）：

| 文件 | 应用前 sha256 | 应用后 sha256 |
|---|---|---|
| `gen/unit.py` | `705097ebeeb5c471bdd44ce5fd8205bb4222a6b6b1e015b9b2072cf9d90f07e1` | `ad652af3344aedc1d0621480f922eae9439525585a3fa8092e24138d5e152bfe` |
| `gen/test_unit_lanes.py` | `ca2199a7d9ea5f444f5498c27f7b823824d69c3e19ceede0475bd2a48eb70623` | `51de6b7c94797f0773f6c58c80575ffba96940529085c8141c61fa74911afdda` |
| `board/shots.json` | `e981c8f27d770cbb99b8aa15f72cc6fd4633300e46f359b44af6b153c39da41c` | `15662cca27d3e3ee68ddc20737ecd04d9004dfb9e5d444085c1c69d082fc744c` |
| `director-coverage.json` | `f4f37cce0f9be693fcd343fee415623b6cf0a8f6dd5953d0d69560b07bfbdfe5` | `c012d28f9a8e9b8ff9d06a56b356948961fd3ad8a8c509261fe8edd151c5fe6f` |

补丁文件：`pilot/s031-048/r3/r3.patch`（sha256 `6351ff3cfb805dcfb50658dc8d46e1e5bd54ebcc9f8530aa13e5c4332bc06751`，git diff 格式，4 个文件，+167 −47）。`board/plates/p048-w2.png`（sha `c31412c3…`，r2 已放进 plates，未被任何 approval 用过）不在补丁里，不用动。

## 1. 应用（仓库根目录）

```bash
P=outputs/ai-city-takeover/ep01/v4
for f in gen/unit.py gen/test_unit_lanes.py board/shots.json director-coverage.json; do cp $P/$f $P/$f.before-r3-2026-11-25; done
git apply --check $P/pilot/s031-048/r3/r3.patch && git apply $P/pilot/s031-048/r3/r3.patch
sha256sum $P/gen/unit.py $P/gen/test_unit_lanes.py $P/board/shots.json $P/director-coverage.json   # = 上表“应用后”
# SG16 / SG18 还没提交，但 a-1|2 里躺着上一批（引译文的 prompt）写好的 approval 与连续性报告：改名保留，不删
for u in SG16 SG18; do for k in 1 2; do d=$P/pilot/sd-$u-a-$k
  mv $d/preview-approval.json $d/preview-approval.held-r3.json
  mv $d/continuity-report.json $d/continuity-report.held-r3.json; done; done
uv run python $P/gen/build_coverage.py --check                    # matches_fresh_build: true
uv run python $P/pilot/s031-048/submit-r3/build.py --check         # {"matches": true}（r3 包与磁盘逐字节一致）
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider $P/gen/test_unit_lanes.py
```

SG16 / SG18 的旧 approval 不改名时，`test_s3148_templates_shape_both_takes_with_fresh_ids` 会报 `AssertionError: sd-SG16-a-1`（已在 scratch 复现）——这是有意的：上一批 approval 绑的是引译文的 prompt，必须被 r3 模板取代。

## 2. `gen/unit.py` SPECS（exact，见 r3.patch 第一段）

- r2 部分原样带上：`BOARD_SHA256` `e981c8f2…` → `15662cca…`（注释前加 r2 说明）；SG20 `clip_spec("SG20", "p048-w2", "c31412c3…")` 与 `natural` 加「她的左肩和整条左臂一直裸露，灰色外套只有右臂一只长袖」。
- s031–s048 段注释加 r3 说明（6 行）。
- SG12（只留收腰带）：
  - `close`：→ `她仍站在原地看着镜头，右手一直捏着纸币垂在腰前，机位与构图不变`
  - `endpoint`：→ `右手一直捏着纸币垂在腰前，她一直看着镜头，不转头`
  - `close_event`（required）：`("说第四句“运气不好”时，她把纸币塞进风衣口袋", "同时眼睛往画面左侧的走廊瞟一眼，不转头，不转身")` → `("右手一直捏着纸币垂在腰前", "她一直看着镜头，不转头，不转身")`
  - `iris_performance`：response 去掉塞纸币与瞟眼；body `始终不转头、不转身`；hands `左手收紧风衣腰带，右手一直捏着纸币垂在腰前`；terminal `她仍站在原地看着镜头，纸币仍在右手`
  - `natural`（含「说出第一个词的同时用左手把风衣腰带一拉收紧」）不变。
- SG15：`progression` / `natural[0]`（required）/ performance response、gaze：`说第三句“让开”时` → `说到第三句时`（natural[0] = `说到第三句时她只垂下眼睛看那位读者，不转头`）。
- SG16：`endpoint` / `close_event[0]`（required）/ performance response、hands：`说到“十二点三十四分停掉”那句时` → `说到第四句时`。
- SG17：`endpoint` / `close_event[0]`（required）/ performance response：`说第二句“他们找到了一道缝”时` → `说到第二句时`（close_event[0] = `说到第二句时她把右手手掌平按进那道红光里`）。
- SG18：`close` / `endpoint` / `close_event[0]`（required）/ performance response：`唱到“十月”这个词刚开口时`（及 `唱到“十月”刚开口时`）→ `唱到第三句刚开口时`。
- 秒数、模式、人声窗口、`dialogue`、`take_margin_seconds` 都不变（SG12 9、SG15 5、SG16 7、SG17 5、SG18 10、SG20 6 s）。INS33 / INS37 / INS41 / SG19 / MO15 一个字不动。
- 补丁后 s031–s048 段 SPECS 里不再有任何引号。`iris_performance` 的 trigger 标签（如「念白：九月二十日的搜索」「念白：他们找到了一个缝」）是合同里的中文概述、不进 provider prompt，本次没改（见 §7）。

## 3. `board/shots.json` 与 `director-coverage.json`（= r2）

- shots.json：三处 `"p048-w1"` → `"p048-w2"`（s048 镜 `plate`、clip SG20 的 `plate` 与 `start_frame`），新 sha `15662cca…`。
- coverage：`gen/build_coverage.py` 重建，只有 rationale 里的 board sha 一行变；`--check` → matches_fresh_build true，coverage_hash `b7db9b57…`。

## 4. `gen/test_unit_lanes.py`（s031–s048 段）

- 常量：`S3148_R3 = ("SG12","SG15","SG16","SG17","SG18","SG20")`、`S3148_TAGS = {"SG12": "b"}`、`S3148_BOARD_SHA256 = "e981c8f2…"`（base 包冻结在它构建时的 board）、`S3148_R3_INPUTS` 读 `submit-r3/preview-inputs.json` 并覆盖这六条的 rows；`S3148_PLATES["SG20"]` → `("p048-w2", "CONT1124/p048-arm-b-comp")`。
- `s3148_take`：r3 六条读 `pilot/s031-048/r3/<UNIT>-approval.template.json`，按各自 tag（SG12 `b`，其余 `a`）换 take 号。
- `test_s3148_pack_…`：base 包 board = 冻结 sha，r3 包 board = 当前 `BOARD_SHA256`；prompt 块先读 base md 再用 r3 md 覆盖；r3 合计 42 s、6,720 / 7,000；`new_over_plan` = SG12 1,440 / 1,600；`base_pack` 与 `supersedes`（submit-r2）sha；s047 新静图与被替换件；`previous_prompt` = SG15/17/20 的 r2 块、其余的 base 块，`base_prompt` = base 块；除 SG20（与 r2 相同）外都确实改了，六条都与 base 不同。
- `test_s3148_prompts_follow_the_lessons`：r3 六条无“最后”；SG15/16/17/18 的序号句、SG20 左臂一句；SG12 有收腰带与“右手一直捏着纸币垂在腰前”，没有“塞进 / 口袋 / 瞟 / 第四句”。
- **新增** `test_s3148_spoken_and_sung_prompts_quote_no_lyric`（7 条念白 / 唱段，含 SG19）：prompt 里没有任何引号 `「」『』“”‘’"'`；没有拉丁字母（英文歌词词）；不含该窗口歌词行中文释义（`lyrics/glosses-v5.json`）里任何 ≥3 字片段；不含退役译法（运气不好、让开、找到了一道缝、十二点三十四分、十月）；required phrases 里也没有引号；`第N句` 只出现绑定的那一处，且按 words.json 在本窗口里分句后第 N 句的首词就是 Out / Killed / They / October；SG12 窗口句首是 September / The / Google, / No / It，只绑“说出第一个词”。
- `test_s3148_templates_shape_both_takes_with_fresh_ids`：r3 六条绑 `submit-r3/` 的页与 inputs；SG12 的 folders / id 为 `sd-SG12-b-1|2`、`iris-sg12-b-<n>-source-001` 等；b 文件夹可以还不存在；新 id 不得撞上 a-1/a-2/a-3 已用 id；已写的 `preview-approval.json` 必须与模板逐项相同（所以 SG16/SG18 旧件要先改名）。
- `test_s3148_templates_pass_draft_materialize_and_lint`（参数化 11 条）不改；r3 六条自动用 r3 模板跑 draft → materialize → lint。

## 5. 新提交包 `submit-r3/`（已生成，build.py 可 `--check`）

| 文件 | sha256 |
|---|---|
| `submit-r3/build.py` | `40c8108e5e2328ddf017df79788e791938ceffbf996adcebf120e658e1236687` |
| `submit-r3/index.html`（approval 绑的包页） | `e88334d59cd140b47f683d89f9633b4f738882aecd851d2b6dbd8899b78e48df` |
| `submit-r3/preview-inputs.json` | `bae532c8f168a8fb67542813e4ea33dbdaedd33f2dc6450a675efbc032b1852e` |
| `r3/index.html`（认可页） | `45f950b4b5c011c560a99de5b5d485f5f9b47c165f90aaa5f2089ccfdd3f8c1e` |
| `excerpt/flash/s031-048-seedance-r3.md`（prompt 来源） | `9040e687cfa8d6f5aa4b6339250faa6c636da4e525d2f5fc154e0b6858a5530b` |
| `r3/SG12-approval.template.json`（b-1） | `09a6eacb81f599e14c06d0ecc310978f59cd39bf1febae40e5c285fb02c9348a` |
| `r3/SG15-approval.template.json` | `b6decfbe16dbf66e6f31919ad88cfa1fc1290cfe8ada1411ae8ea38474481f50` |
| `r3/SG16-approval.template.json` | `f0f00667548284e3819555639cf1421be906fda42ce55789f3a483d617add08b` |
| `r3/SG17-approval.template.json` | `b507a323f831199a01fd87894c8e3f2aecaac97605b55df3c59dc746cee208c7` |
| `r3/SG18-approval.template.json` | `6faa19544f0fd73f4ee57dcbd61277a6e105f103107d973158c767897c1966a4` |
| `r3/SG20-approval.template.json` | `feaa6f258e6e88daf99c8d45ff2c45b71d9b54bc31ae4b8ca254e9d48ddec792` |

build.py 只能在补丁已应用的树上跑（断言 board sha）；它 hash 的输入有 `submit/` 与 `submit-r2/` 的 preview-inputs、base / r2 md、方案页、首帧预览页、首帧与人声。当前一批提交期间这些都不该变；`--check` 不一致就先查是谁改了，再重跑 build.py（会重写模板与两页的 sha），不要手改。

## 6. 应用后写 approval（主会话）

1. 用户在 r3 页的回答填进 `r3/<UNIT>-approval.template.json`，删 `_template_notes`，写成 take 1 的 `preview-approval.json`；take 2 按模板第 2 条改三处。
   - SG12 → `pilot/sd-SG12-b-1|2/`（新文件夹；`sd-SG12-a-1|2|3` 是已用掉的旧 take，不动），id `iris-sg12-b-<n>-source-001` / `iris-sg12-b-<n>-reservation-001`（未被任何 operator-bound 用过）。
   - SG16 / SG18 → `sd-<UNIT>-a-1|2/`，**取代**上一批的 approval（§1 已改名为 held-r3）。
   - SG15 / SG17 / SG20 → `sd-<UNIT>-a-1|2/`（里面的 `preview-approval.held-r2.json` 是更早的旧件，保留）。
2. 提交前照旧派 continuity-supervisor 按 r3 prompt 重出六条的 `continuity-report.json`（SG16/SG18 的旧报告已 held-r3）。
3. 提交命令（模板第 3 条）：SG12 `prep_unit.sh SG12 9 multimodal 800`（TRIAL_DIR `sd-SG12-b-<k>`）、SG15 `… 5 multimodal 400`、SG16 `… 7 multimodal 600`、SG17 `… 5 multimodal 400`、SG18 `… 10 multimodal 800`、SG20 `… 6 multimodal 500`。
4. 花费：r3 六条 42 s × 80 × 2 = **6,720**（单条上限合计 3,500 × 2 = 7,000）。其中 SG12 b-1/b-2 **1,440（上限 1,600）是原 10,400 计划外新增**（原计划的两条已花在 a-1 720、a-3 720；a-2 known_no_effect 未扣费）；其余五条 5,280 在原计划内。s031–s048 全段约 11,840（上限 12,800）。

## 7. 引号 / 译文扫描（只报告，未改）

- 当前 `s031-048-seedance.md`：SG12「“运气不好”」、SG16「“十二点三十四分停掉”」、SG18「“十月”」——r3 已替换。`s031-048-seedance-r2.md`：SG15「“让开”」、SG17「“他们找到了一道缝”」——r3 已替换。
- SG19、INS33、INS37、INS41、MO15（当前一批）：prompt 无引号、无拉丁字母、无歌词释义片段、无退役译法。SG19 只有「唱完这一句之后」，不引歌词。
- `excerpt/flash/` 下其他 `*.md` 的 ```prompt 块没有引号。
- prompt 之外仍有译文 / 引号（不进 provider prompt）：unit.py 各 `iris_performance` 的 trigger 中文概述；`submit/build.py` 的 NOTES / LESSONS 与 base 模板 `decision_notes`（历史记录）；`sd-SG12-a-*`、`sd-SG16/18-a-*` 已写 approval 里的 prompt 原文（历史）。

## 8. 草稿验证（已做，scratch）

- `git worktree add --detach /tmp/aiv-r3 HEAD`；rsync 当前工作区 `outputs/ai-city-takeover/ep01/v4/`（排除 mp4/mov/webm/mkv）与 `logs/decisions.md`；`uv sync --all-extras`。
- 在 scratch 暂存底版四个文件 → `git apply r2/r2.patch` → 按 §2、§4 改 → `submit-r3/build.py` 生成包（拷回仓库）→ `build_coverage.py --check` matches true、`submit-r3/build.py --check` matches true → 按 §1 改名 SG16/SG18 旧件 → `pytest -q -p no:cacheprovider outputs/ai-city-takeover/ep01/v4/gen/test_unit_lanes.py` **113 passed**（r2 时 112，+1 新测试）。
- 反证：把 base / r2 的 SG12、SG15、SG16、SG17、SG18 prompt、错绑第二句的 SG15、不加引号写“运气不好”的 SG12 喂给新测试，七种都被拦下；SG16 旧 approval 不改名时 fresh_ids 测试报 `sd-SG16-a-1`。
- `r3.patch` = scratch 里 `git diff`（暂存底版 → 改后）四个文件；`git apply --check` 在当前仓库工作区通过。scratch worktree 已删除。
