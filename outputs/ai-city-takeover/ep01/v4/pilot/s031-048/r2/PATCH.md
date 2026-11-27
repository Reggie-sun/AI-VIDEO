# s031–s048 r2 补丁计划（SG15 · SG17 · SG20）

2026-11-25。主会话在**当前一批（SG12、INS33、SG16、INS37、SG18、INS41、SG19、MO15）全部提交并 Gate 完之后**再应用。应用前不要写 SG15/SG17/SG20 的 approval；r2 的 board sha 只有应用后才成立。认可页：http://127.0.0.1:8769/pilot/s031-048/r2/index.html。

本步没有改 `gen/unit.py`、`gen/test_unit_lanes.py`、`board/shots.json`、`director-coverage.json`、`excerpt/flash/s031-048-seedance.md`、`submit/` 包、任何旧首帧或旧模板；没有提交、付费、写 approval、commit。

## 0. 前提（应用前核对）

应用前这四个文件必须仍是本补丁的底（否则 `git apply --check` 会失败；失败就停下重做 diff，不要手改）：

| 文件 | 应用前 sha256 | 应用后 sha256 |
|---|---|---|
| `gen/unit.py` | `705097ebeeb5c471bdd44ce5fd8205bb4222a6b6b1e015b9b2072cf9d90f07e1` | `d1b098eb9e7f07c3773d805d525d0259e7931f4ce07bcb5d8cd3566d51576a2f` |
| `gen/test_unit_lanes.py` | `ca2199a7d9ea5f444f5498c27f7b823824d69c3e19ceede0475bd2a48eb70623` | `329bbe8a113a67ccdf4adcc0464b274735a32bcc7a22b7ead55f83c45c9c8b36` |
| `board/shots.json` | `e981c8f27d770cbb99b8aa15f72cc6fd4633300e46f359b44af6b153c39da41c` | `15662cca27d3e3ee68ddc20737ecd04d9004dfb9e5d444085c1c69d082fc744c` |
| `director-coverage.json` | `f4f37cce0f9be693fcd343fee415623b6cf0a8f6dd5953d0d69560b07bfbdfe5` | `c012d28f9a8e9b8ff9d06a56b356948961fd3ad8a8c509261fe8edd151c5fe6f` |

补丁文件：`pilot/s031-048/r2/r2.patch`（sha256 `e2bed3eda504743ac011d1bd45c670f9bb81573a2b8125c7dc1de96abac1ec23`，4 个文件，+71 −26）。

## 1. 应用（仓库根目录）

```bash
P=outputs/ai-city-takeover/ep01/v4
for f in gen/unit.py gen/test_unit_lanes.py board/shots.json director-coverage.json; do cp $P/$f $P/$f.before-r2-2026-11-25; done
git apply --check $P/pilot/s031-048/r2/r2.patch && git apply $P/pilot/s031-048/r2/r2.patch
sha256sum $P/gen/unit.py $P/gen/test_unit_lanes.py $P/board/shots.json $P/director-coverage.json   # = 上表“应用后”
uv run python $P/gen/build_coverage.py --check                    # matches_fresh_build: true
uv run python $P/pilot/s031-048/submit-r2/build.py --check         # {"matches": true}（r2 包与磁盘逐字节一致）
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider $P/gen/test_unit_lanes.py
```

## 2. `gen/unit.py` SPECS（exact，见 r2.patch 第一段）

- `BOARD_SHA256`：`e981c8f2…` → `15662cca27d3e3ee68ddc20737ecd04d9004dfb9e5d444085c1c69d082fc744c`，注释前加「2026-11-25 s031–s048 r2：SG20 首帧与 s048 镜换 p048-w2（W1 左臂从肩到腕裸露，CONT1124/p048-arm-b-comp）；此前 e981c8f2…（」，行尾多一个「）」。
- SG15（挪椅子绑第三句）：
  - `progression`：`…；说最后一句时只垂下眼睛看那位读者` → `…；说第三句“让开”时只垂下眼睛看那位读者`
  - `natural[0]`：`只垂下眼睛看那位读者，不转头` → `说第三句“让开”时她只垂下眼睛看那位读者，不转头`（required phrase，绑序号）
  - `iris_performance` response：`…；最后一句只垂下眼睛看读者` → `…；说第三句“让开”时只垂下眼睛看读者`；gaze：`镜头，最后垂眼看读者` → `镜头，说“让开”时垂眼看读者`
- SG17（按手绑第二句）：
  - `endpoint`：`说到最后一句时把右手手掌平按进那道红光里` → `说第二句“他们找到了一道缝”时把右手手掌平按进那道红光里`
  - `close_event[0]`：`把右手手掌平按进那道红光里` → `说第二句“他们找到了一道缝”时她把右手手掌平按进那道红光里`（required phrase）
  - `iris_performance` response：`…；最后一句把右手手掌平按进门缝的红光里` → `…；说第二句“他们找到了一道缝”时把右手手掌平按进门缝的红光里`
- SG20（首帧 + 服装一句）：
  - `clip_spec("SG20", "p048-w1", "96bffc3c…")` → `clip_spec("SG20", "p048-w2", "c31412c3ba0260f5c6937b8ce6ecf4cd8d1eef4c1a038ecc9fb082da94818c32", …)`，上方注释加两行说明 p048-w2 来源。
  - `natural`：在 `嘴前没有任何遮挡` 之后插入 `她的左肩和整条左臂一直裸露，灰色外套只有右臂一只长袖`（required phrase）。
- 秒数、模式、人声窗口、`dialogue`、`take_margin_seconds` 都不变（SG15 5 s、SG17 5 s、SG20 6 s）。其余 8 条 SPECS 一个字不动。

## 3. `board/shots.json`

只把三处 `"p048-w1"` 换成 `"p048-w2"`：s048 镜的 `plate`，clip SG20 的 `plate` 与 `start_frame`。别的不动（s047 是静图，板子的 `p047` 不动；s047 用图在 r2 包的 stills 里换成 `CONT1124/p047-rb-c-2944`）。新 sha `15662cca…`。

## 4. `director-coverage.json`

`gen/build_coverage.py` 重建；只有 rationale 里的 board sha 那一行变（e981c8f2… → 15662cca…），53 个单元不变，coverage_hash `b7db9b57…`。

## 5. `gen/test_unit_lanes.py`（s031–s048 段）

- 新常量：`S3148_R2 = ("SG15","SG17","SG20")`；`S3148_BOARD_SHA256 = "e981c8f2…"`（base 包冻结在它构建时的 board，同 s015–s030 的 `S1530_BOARD_SHA256` 先例）；`S3148_R2_INPUTS` 读 `submit-r2/preview-inputs.json`，并用其 rows 覆盖 `S3148_ROWS` 里这三条。
- `S3148_PLATES["SG20"]` → `("p048-w2", "CONT1124/p048-arm-b-comp")`。
- `s3148_take`：r2 三条从 `pilot/s031-048/r2/<UNIT>-approval.template.json` 读模板。
- `test_s3148_pack_…`：base 包 board = `S3148_BOARD_SHA256`，r2 包 board = 当前 `BOARD_SHA256`；prompt 块先读 base md、再用 r2 md 覆盖三条；新增 r2 合计（16 s、2,560 / 2,600）、`base_pack` sha、s047 新静图与被替换件的 sha、三条都确实改过 prompt（`previous_prompt` sha = base 行 sha ≠ 新 sha）。
- `test_s3148_prompts_follow_the_lessons`：新增 r2 三条无“最后”；SG15「说第三句“让开”时…」、SG17「说第二句“他们找到了一道缝”时…」、SG20 左臂一句；歌词断句核对（SG15 第三句 = Out of my way，SG17 第二句以 They found a gap 开头）。
- `test_s3148_templates_shape_both_takes_with_fresh_ids`：r2 三条绑 `submit-r2/` 的页与 inputs；“新 id 不撞”只和本包 22 个 take 文件夹之外的 operator-bound 比；**已经写好的** `preview-approval.json` 必须与本 take 模板的 page / inputs / prompt_source / artifacts / prompts / generation / bound_ids 逐项相同，已有 operator-bound 的 id 必须等于模板 id（替换原来的“文件夹里不得有 approval”——当前一批提交后这条必然失败；现在工作区的基线跑就已经是 1 failed：`test_s3148_templates_shape_both_takes_with_fresh_ids`，因为 sd-SG12-a-1 等已写 approval）。
- `test_s3148_templates_pass_draft_materialize_and_lint`（参数化 11 条）不改；r2 三条自动用 r2 模板跑 draft → materialize → lint。

## 6. 应用后写 approval（主会话）

1. 用户在 r2 页的回答填进 `pilot/s031-048/r2/<UNIT>-approval.template.json`，删 `_template_notes`，写成 `pilot/sd-<UNIT>-a-1/preview-approval.json`；a-2 按模板第 2 条改三处。各 a-1 文件夹里的 `preview-approval.held-r2.json` 是被取代的旧件，保留不动。
2. 用户若选非推荐图：p048 选 a → 把 `CONT1124/p048-arm-a-comp.png` 拷成 `board/plates/p048-w2.png`（覆盖前它还没被任何 approval 用过）、补丁里 SG20 的 plate sha 改成 `19835171db26e1b4cb1eb2912a5b1a001a1384ca9a52844b594c0bbd08b356bd`、`submit-r2/build.py` 的 `FRAMES["SG20"]`/`CANDIDATES` 与测试 `S3148_PLATES` 改成 `p048-arm-a-comp`；s047 选 b → `CONT1124/p047-rc-b-comp.png` 重出 rb-c 与 2944 版、改 build.py。然后重跑 `submit-r2/build.py`（会重写模板与两页的 sha）再写 approval。
3. 提交命令不变（模板第 3 条）：SG15 `prep_unit.sh SG15 5 multimodal 400`、SG17 `… 5 multimodal 400`、SG20 `… 6 multimodal 500`；`run_unit.sh` t0：SG15 155.76、SG17 170.1094、SG20 205.2412。提交前照旧派 continuity-supervisor 写 `continuity-report.json`。

## 7. 草稿验证（已做，scratch）

- scratch：`git worktree add --detach /tmp/aiv-r2 HEAD`，再 rsync 当前工作区的 `outputs/ai-city-takeover/ep01/v4/`（不含视频）与 `logs/decisions.md`，在 scratch 里按上面 2–5 改完。
- `build_coverage.py`：重建，只变 board sha 一行。`submit-r2/build.py`：在 scratch 生成 r2 包，拷回仓库；`--check` → matches true。
- `pytest -q -p no:cacheprovider outputs/ai-city-takeover/ep01/v4/gen/test_unit_lanes.py`（scratch，.venv python）→ **112 passed**。同一测试在当前仓库工作区（未打补丁）→ 111 passed, 1 failed（上面说的 approval 已写导致的那条）。
- `git apply --check` 在当前仓库工作区通过。
