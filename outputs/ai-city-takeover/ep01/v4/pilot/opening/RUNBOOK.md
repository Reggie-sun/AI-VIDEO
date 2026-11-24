# IRIS EP01 开头 s001–s010 · Seedance 2.0 VIP 4k 执行清单（主会话用）

2026-11-20。使用者在 `pilot/opening/index.html` 认可预览包：「按页面拍 (Recommended)」。输入清单 `pilot/opening/preview-inputs.json`，prompt 原文 `excerpt/flash/opening-seedance.md`。本清单只列命令与模板；**approval、profile、operator-bound、continuity-report 都由主会话写**，提交、余额、取回由主会话逐条执行。一次只做一条：submit → fetch → 逐镜 Gate（全 PASS）→ 下一条。

## 已备好的本地数据（不联网）

- 首帧入板：`board/plates/p001-w1.png` … `p010-w1.png` 与 `excerpt/flash/design/OPEN/` 的选定首帧逐字节相同（sha 见各单元）。旧 `p001.png`…`p010.png` 保留。
- 分镜 `board/shots.json`（sha `49b78ad4ee890935fbbfc66ecae001432143be4c2a7875dea526dfbf857e9472`；改前备份 `board/shots.before-opening-2026-11-20.json`）：s001–s010 的 `plate` 指向 w1 首帧；s003 / s005 / s009 由 plate3d 改为 motion，新 clip `MO19` / `MO20` / `MO21`（窗口从该镜切点起 4 s，`plays` = 该镜区间）。`board_audit.py --sung-max 160` 全过（clips 46 → 49，motion 86.87 → 98.87 s）。
- `gen/unit.py`：10 个单元的 spec（W1、底片 sha、秒数、必须字句逐字取自认可 prompt）；`BOARD_SHA256` 已更新。旧 MO04 / SG02 / MO05（L1）spec 原文留在 `gen/unit.py.before-opening-2026-11-20`。
- `director-coverage.json` 已由 `build_coverage.py` 重跑（49 units），`--check` 通过。
- 人声：SG01 `pilot/audio/SG01.wav`（5.75 s，窗口 11.15–16.9041）与 SG02 `pilot/audio/SG02.wav`（4.00 s，窗口 29.529–33.529）已封存在 `pilot/audio/windows.json`，不用再切。
- 20 个空 take 文件夹 `pilot/sd-<UNIT>-o-1/`、`-o-2/` 已建。每个文件夹各跑一次 `addnode.cjs`（各自一个新空节点；`lint.py` 的 `fresh_canvas_node` 拒绝别的文件夹用过的节点）。

## 总表

| 顺序 | 镜头 | unit | 模式 | 秒数 | 单条上限 CRD | 首帧 | take 文件夹 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | s001 | MO01 | first_frame | 5 | 400 | `p001-w1.png` | `sd-MO01-o-1`、`sd-MO01-o-2` |
| 2 | s002 | MO02 | first_frame | 6 | 500 | `p002-w1.png` | `sd-MO02-o-1`、`sd-MO02-o-2` |
| 3 | s003 | MO19 | first_frame | 4 | 400 | `p003-w1.png` | `sd-MO19-o-1`、`sd-MO19-o-2` |
| 4 | s004 | SG01 | multimodal | 6 | 500 | `p004-w1.png` | `sd-SG01-o-1`、`sd-SG01-o-2` |
| 5 | s005 | MO20 | first_frame | 4 | 400 | `p005-w1.png` | `sd-MO20-o-1`、`sd-MO20-o-2` |
| 6 | s006 | MO03 | first_frame | 6 | 500 | `p006-w1.png` | `sd-MO03-o-1`、`sd-MO03-o-2` |
| 7 | s007 | MO04 | first_frame | 4 | 400 | `p007-w1.png` | `sd-MO04-o-1`、`sd-MO04-o-2` |
| 8 | s008 | SG02 | multimodal | 4 | 400 | `p008-w1.png` | `sd-SG02-o-1`、`sd-SG02-o-2` |
| 9 | s009 | MO21 | first_frame | 4 | 400 | `p009-w1.png` | `sd-MO21-o-1`、`sd-MO21-o-2` |
| 10 | s010 | MO05 | first_frame | 5 | 400 | `p010-w1.png` | `sd-MO05-o-1`、`sd-MO05-o-2` |

合计 20 条（每 unit 2 条，同一首帧），上限合计 8600 CRD（单价参考 80 CRD/秒：4 s 320、5 s 400、6 s 480；preview-inputs 估算 7680）。完成时按 `spend.json` 如实报告实付。

## 每条 take 的命令序列（在仓库根执行，`<UNIT>` 与 `<n>` 换成具体值）

```bash
export SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-<UNIT>-o-<n>
# 0. 主会话写 $SD_TRIAL/preview-approval.json（下方该 unit 的模板；-o-2 按“o-2 的差异”改三处）
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py draft <UNIT>                                   # 1. 核对分镜 sha、底片 sha、锚点、clip 窗口与秒数、必须字句、纯中文、标记
node outputs/ai-city-takeover/ep01/v4/gen/addnode.cjs $SD_TRIAL/<UNIT>                                    # 2. IRIS 画布加一个空视频节点 → $SD_TRIAL/<UNIT>/node-created.json
# 3. 主会话写 $SD_TRIAL/<UNIT>/profile.json（node_id 取自 node-created.json）与 $SD_TRIAL/<UNIT>/operator-bound.json（下方模板）
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py materialize <UNIT> --profile $SD_TRIAL/<UNIT>/profile.json   # 4. 建项目 + transport-free prepare（无调用）
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py show <UNIT>                                    # 5. 打印将提交的精确请求（只读）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py prepare <UNIT>                             # 6. 冻结 prepared.json（无调用）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py start <UNIT>                               # 7. 建 attempt（无调用）
# 8. continuity-supervisor 出报告 → $SD_TRIAL/continuity-report.json（units.<UNIT>.verdict = "ready"）
uv run python outputs/ai-city-takeover/ep01/v4/gen/lint.py <UNIT>                                         # 9. 全部检查通过才可提交（含 bound_ids_match_approval、fresh_canvas_node）
node outputs/ai-city-takeover/ep01/v4/gen/balance.cjs                                                     # 提交前精确余额
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py submit <UNIT>                              # 10. 一次性提交
node outputs/ai-city-takeover/ep01/v4/gen/balance.cjs                                                     # 提交后精确余额 → 如实记账
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py poll <UNIT>                                # 11. 查询（可重复）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py fetch <UNIT>                               #     完成后取回
# 12. 逐镜 Gate（shot-gate-reviewer，video-analysis MCP）全 PASS 才做下一条
```

等价的已有脚本（同样不提交 / 同样一次提交，主会话决定用哪种）：
```bash
TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-<UNIT>-o-<n> bash outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh <UNIT> <秒数> <first_frame|multimodal> <单条上限>   # 1–7：draft、addnode、按 approval 的 bound_ids 写 profile/bound（有效 6 小时）、materialize、prepare、start
TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-<UNIT>-o-<n> bash outputs/ai-city-takeover/ep01/v4/gen/run_unit.sh <UNIT> [人声窗口起点]   # 9–11 + 取 Gate 帧；只在 continuity-report 已落盘后跑；SG01 带 11.15，SG02 带 29.529，MO 不带
```

o-2 与 o-1 的差异（approval、bound 只改这些，其余逐字相同）：approval 的 `unit_group` 末尾 `o-1`→`o-2`、`bound_ids` 三个 id 中 `-o-1-`→`-o-2-`、`takes.this_take` `sd-<UNIT>-o-1`→`sd-<UNIT>-o-2`；bound 的 `task` 中 `o-1`→`o-2`、`preview_approval` 路径与三个 id 同样换成 o-2；profile 只换 `node_id`。

停止规则同 `gen/README.md`「停止规则」：任何一步失败或 Blocked 就停并报告，不手改产物硬过；unknown 不重试、不重签。

## 1. s001 · MO01（first_frame，5 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p001-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP01-c.png`，sha `63b1195d4528a7b75c7c1999abc3596499bee7a6d1bbe8920eb9f58aed37a611`）
- prompt sha `7b69aa0fa2317896a9e7c794076e03b087172fd9ba7cb956070f4dd46223c2b6`；spec 必须逐字出现：`镜头在化妆镜旁正面拍她`、`她闭着眼，化妆师的粉扑按在她颧骨上`、`极慢地推近`、`从椅子上站起半身，寻呼机握在下巴下方`、`用拇指按掉它`、`用两根手指把粉扑推开`
- 文件夹：`pilot/sd-MO01-o-1/`、`pilot/sd-MO01-o-2/`；建议 id：`iris-mo01-o-<n>-source-001` / `iris-mo01-o-<n>-reservation-001`

<!-- approval:MO01 -->
`pilot/sd-MO01-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO01-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p001-w1.png",
   "sha256": "63b1195d4528a7b75c7c1999abc3596499bee7a6d1bbe8920eb9f58aed37a611",
   "role": "MO01 first frame"
  }
 ],
 "prompts": {
  "MO01": {
   "text": "镜头在化妆镜旁正面拍她，极慢地推近。她闭着眼，化妆师的粉扑按在她颧骨上；她睁开眼，用两根手指把粉扑推开，伸手从台面上拿起那台黑色寻呼机，在掌心掂一下，用拇指按掉它，然后从椅子上站起半身，寻呼机握在下巴下方。面无表情，带着一点好奇。机头直闪。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "7b69aa0fa2317896a9e7c794076e03b087172fd9ba7cb956070f4dd46223c2b6"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 5,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p001-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP01-c.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-mo01-o-1-source-001",
  "policy_id": "iris-mo01-o-1-source-001",
  "reservation_id": "iris-mo01-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO01-o-1",
   "sd-MO01-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-MO01-o-1"
 }
}
```

<!-- profile:MO01 -->
`pilot/sd-MO01-o-1/MO01/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 5,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 5,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:MO01 -->
`pilot/sd-MO01-o-1/MO01/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO01",
 "task": "IRIS EP01 v4 MO01（s001，opening o-1）; Seedance 2.0 VIP first_frame, 5 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO01-o-1/preview-approval.json",
 "attempt_id": "iris-mo01-o-1-source-001",
 "policy_id": "iris-mo01-o-1-source-001",
 "reservation_id": "iris-mo01-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO01-o-<n>/continuity-report.json`（`units.MO01.verdict = "ready"`）。

## 2. s002 · MO02（first_frame，6 s，单条上限 500）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p002-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP02-d.png`，sha `4cdc13467ed25a2fb32cb0b022988cca11cf44d56b0aa67b2084a1ed75f226fb`）
- prompt sha `64a7f4c1a0d2125091eff03dc3a164a6c5bbd67ff6e9efc59947f52e09da6490`；spec 必须逐字出现：`机位在走秀台尽头`、`她从混凝土柱子旁大步走出来`、`随她的步子轻微后退`、`她踏上湿亮的水泥走秀台向镜头走来`、`两边前排的人低头看笔记本`、`边走边把手里的黑色寻呼机别到腰链上`、`门缝里的一道红光扫过她的靴子`
- 文件夹：`pilot/sd-MO02-o-1/`、`pilot/sd-MO02-o-2/`；建议 id：`iris-mo02-o-<n>-source-001` / `iris-mo02-o-<n>-reservation-001`

<!-- approval:MO02 -->
`pilot/sd-MO02-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO02-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p002-w1.png",
   "sha256": "4cdc13467ed25a2fb32cb0b022988cca11cf44d56b0aa67b2084a1ed75f226fb",
   "role": "MO02 first frame"
  }
 ],
 "prompts": {
  "MO02": {
   "text": "长焦，机位在走秀台尽头，随她的步子轻微后退。她从混凝土柱子旁大步走出来，边走边把手里的黑色寻呼机别到腰链上，经过半开的消防门，门缝里的一道红光扫过她的靴子，她踏上湿亮的水泥走秀台向镜头走来。两边前排的人低头看笔记本。面无表情。机头直闪。除了她左耳耳挂上的小红灯和门缝里的那道红光，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "64a7f4c1a0d2125091eff03dc3a164a6c5bbd67ff6e9efc59947f52e09da6490"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 6,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 500,
  "cumulative_CRD": 500
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p002-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP02-d.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-mo02-o-1-source-001",
  "policy_id": "iris-mo02-o-1-source-001",
  "reservation_id": "iris-mo02-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO02-o-1",
   "sd-MO02-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 1000,
  "this_take": "sd-MO02-o-1"
 }
}
```

<!-- profile:MO02 -->
`pilot/sd-MO02-o-1/MO02/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 6,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 6,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 500
}
```

<!-- bound:MO02 -->
`pilot/sd-MO02-o-1/MO02/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO02",
 "task": "IRIS EP01 v4 MO02（s002，opening o-1）; Seedance 2.0 VIP first_frame, 6 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO02-o-1/preview-approval.json",
 "attempt_id": "iris-mo02-o-1-source-001",
 "policy_id": "iris-mo02-o-1-source-001",
 "reservation_id": "iris-mo02-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 500,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 500,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO02-o-<n>/continuity-report.json`（`units.MO02.verdict = "ready"`）。

## 3. s003 · MO19（first_frame，4 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p003-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP03-c.png`，sha `a20283d6bf24e702cbfb1ecc210dc97aba704366bdaf21f2cfa2a8d9d036ab61`）
- prompt sha `7ec2dc09ddc353ee58c53b8bb2bae3f55822b8e4f4c2eeffdbbbf51d27be6cd3`；spec 必须逐字出现：`从坐着的值班工程师肩后拍`、`他被手里突然亮起的手机惊醒`、`镜头固定`、`她在湿亮的走秀台上朝镜头走来，谁也不看`、`屏幕一部接一部亮起`、`膝盖上的笔记本电脑滑下去一半`
- 文件夹：`pilot/sd-MO19-o-1/`、`pilot/sd-MO19-o-2/`；建议 id：`iris-mo19-o-<n>-source-001` / `iris-mo19-o-<n>-reservation-001`

<!-- approval:MO19 -->
`pilot/sd-MO19-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO19-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p003-w1.png",
   "sha256": "a20283d6bf24e702cbfb1ecc210dc97aba704366bdaf21f2cfa2a8d9d036ab61",
   "role": "MO19 first frame"
  }
 ],
 "prompts": {
  "MO19": {
   "text": "镜头固定，从坐着的值班工程师肩后拍。他被手里突然亮起的手机惊醒，膝盖上的笔记本电脑滑下去一半；整排前排的人同时低头看手机，屏幕一部接一部亮起；她在湿亮的走秀台上朝镜头走来，谁也不看。机头直闪。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "7ec2dc09ddc353ee58c53b8bb2bae3f55822b8e4f4c2eeffdbbbf51d27be6cd3"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 4,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p003-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP03-c.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-mo19-o-1-source-001",
  "policy_id": "iris-mo19-o-1-source-001",
  "reservation_id": "iris-mo19-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO19-o-1",
   "sd-MO19-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-MO19-o-1"
 }
}
```

<!-- profile:MO19 -->
`pilot/sd-MO19-o-1/MO19/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 4,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 4,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:MO19 -->
`pilot/sd-MO19-o-1/MO19/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO19",
 "task": "IRIS EP01 v4 MO19（s003，opening o-1）; Seedance 2.0 VIP first_frame, 4 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO19-o-1/preview-approval.json",
 "attempt_id": "iris-mo19-o-1-source-001",
 "policy_id": "iris-mo19-o-1-source-001",
 "reservation_id": "iris-mo19-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO19-o-<n>/continuity-report.json`（`units.MO19.verdict = "ready"`）。

## 4. s004 · SG01（multimodal，6 s，单条上限 500）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p004-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP04-c.png`，sha `b012df34e10b3ef713e63f4011d7aadc331d0e765abe1b0d2d22de5ec928fc4c`）
- 人声：`outputs/ai-city-takeover/ep01/v4/pilot/audio/SG01.wav`（sha `1a821e13899132e0415e06d7a70e1e48ba9dd18b39dc3d5e4b712832815ebb58`，5.75 s，窗口 [11.15, 16.9041]）；`run_unit.sh` 第二参数 `11.15`
- prompt sha `4014034819fbcf839d8f5ee05ecdc4f8fc1efeeab9447607d6f20fc5a10008f8`；spec 必须逐字出现：`中景`、`对着镜头平平地说话`、`逐字精确同步`、`伸直手臂把听筒举在身侧，离脸一臂远`、`镜头固定不动`、`不贴耳也不挡嘴`、`嘴前没有任何遮挡`
- 文件夹：`pilot/sd-SG01-o-1/`、`pilot/sd-SG01-o-2/`；建议 id：`iris-sg01-o-<n>-source-001` / `iris-sg01-o-<n>-reservation-001`

<!-- approval:SG01 -->
`pilot/sd-SG01-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-SG01-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p004-w1.png",
   "sha256": "b012df34e10b3ef713e63f4011d7aadc331d0e765abe1b0d2d22de5ec928fc4c",
   "role": "SG01 reference image"
  },
  {
   "path": "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG01.wav",
   "sha256": "1a821e13899132e0415e06d7a70e1e48ba9dd18b39dc3d5e4b712832815ebb58",
   "role": "SG01 vocal"
  }
 ],
 "prompts": {
  "SG01": {
   "text": "{{image:0}}中的她站在呼叫柱旁，对着镜头平平地说话，口型与{{audio:1}}里的人声逐字精确同步。中景，镜头固定不动，全程正对镜头。说到后半句时她侧身从呼叫柱上摘下听筒，伸直手臂把听筒举在身侧，离脸一臂远，不贴耳也不挡嘴。身后前排的手机一部接一部亮起。机头直闪。嘴前没有任何遮挡。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "4014034819fbcf839d8f5ee05ecdc4f8fc1efeeab9447607d6f20fc5a10008f8"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "multimodal",
  "seconds": 6,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": "reference_audio"
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 500,
  "cumulative_CRD": 500
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "reference image（p004-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP04-c.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-sg01-o-1-source-001",
  "policy_id": "iris-sg01-o-1-source-001",
  "reservation_id": "iris-sg01-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-SG01-o-1",
   "sd-SG01-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 1000,
  "this_take": "sd-SG01-o-1"
 }
}
```

<!-- profile:SG01 -->
`pilot/sd-SG01-o-1/SG01/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "multimodal",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 6,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 6,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 500
}
```

<!-- bound:SG01 -->
`pilot/sd-SG01-o-1/SG01/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "SG01",
 "task": "IRIS EP01 v4 SG01（s004，opening o-1）; Seedance 2.0 VIP multimodal, 6 s 4k 16:9, reference vocal",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG01-o-1/preview-approval.json",
 "attempt_id": "iris-sg01-o-1-source-001",
 "policy_id": "iris-sg01-o-1-source-001",
 "reservation_id": "iris-sg01-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 500,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 500,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-SG01-o-<n>/continuity-report.json`（`units.SG01.verdict = "ready"`）。

## 5. s005 · MO20（first_frame，4 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p005-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP05-d.png`，sha `4d3f102771e6f3f8b162c7f3942103dc371051f27f8c70761af07de7e731021b`）
- prompt sha `e5418f58f98511c1003e1cb1857b4dd269728df326697aa972875a92a67ef112`；spec 必须逐字出现：`近景`、`听筒顺着螺旋线垂下去来回晃`、`镜头固定`、`一半夹在两指间，低头看着它`、`一半扔出画面`、`她把手里那张白纸从中间撕开`
- 文件夹：`pilot/sd-MO20-o-1/`、`pilot/sd-MO20-o-2/`；建议 id：`iris-mo20-o-<n>-source-001` / `iris-mo20-o-<n>-reservation-001`

<!-- approval:MO20 -->
`pilot/sd-MO20-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO20-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p005-w1.png",
   "sha256": "4d3f102771e6f3f8b162c7f3942103dc371051f27f8c70761af07de7e731021b",
   "role": "MO20 first frame"
  }
 ],
 "prompts": {
  "MO20": {
   "text": "近景，镜头固定。她松开手，听筒顺着螺旋线垂下去来回晃；她把手里那张白纸从中间撕开，一半扔出画面，一半夹在两指间，低头看着它，面无表情。机头直闪。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "e5418f58f98511c1003e1cb1857b4dd269728df326697aa972875a92a67ef112"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 4,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p005-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP05-d.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-mo20-o-1-source-001",
  "policy_id": "iris-mo20-o-1-source-001",
  "reservation_id": "iris-mo20-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO20-o-1",
   "sd-MO20-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-MO20-o-1"
 }
}
```

<!-- profile:MO20 -->
`pilot/sd-MO20-o-1/MO20/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 4,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 4,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:MO20 -->
`pilot/sd-MO20-o-1/MO20/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO20",
 "task": "IRIS EP01 v4 MO20（s005，opening o-1）; Seedance 2.0 VIP first_frame, 4 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO20-o-1/preview-approval.json",
 "attempt_id": "iris-mo20-o-1-source-001",
 "policy_id": "iris-mo20-o-1-source-001",
 "reservation_id": "iris-mo20-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO20-o-<n>/continuity-report.json`（`units.MO20.verdict = "ready"`）。

## 6. s006 · MO03（first_frame，6 s，单条上限 500）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p006-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP06-c.png`，sha `aa0679464dec0a0872a858ea07db291f73bf79046f1784a1a7b33c2e0f0af09c`）
- prompt sha `e82590bf8d31f2e64f845638fd3466ea5b0b03b3684ce82566ea04fc5aae7dce`；spec 必须逐字出现：`手持跟拍`、`一群街拍摄影师倒退着走在她前面`、`在她侧前方`、`从他们中间穿过去，走向街角的行道树`、`她不减速`、`伸手掌平按住最近一台相机的镜头往下压`、`不停按闪光灯`
- 文件夹：`pilot/sd-MO03-o-1/`、`pilot/sd-MO03-o-2/`；建议 id：`iris-mo03-o-<n>-source-001` / `iris-mo03-o-<n>-reservation-001`

<!-- approval:MO03 -->
`pilot/sd-MO03-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO03-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p006-w1.png",
   "sha256": "aa0679464dec0a0872a858ea07db291f73bf79046f1784a1a7b33c2e0f0af09c",
   "role": "MO03 first frame"
  }
 ],
 "prompts": {
  "MO03": {
   "text": "手持跟拍，在她侧前方。夜里湿亮的人行道上，一群街拍摄影师倒退着走在她前面，不停按闪光灯；她不减速，伸手掌平按住最近一台相机的镜头往下压，从他们中间穿过去，走向街角的行道树。面无表情。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "e82590bf8d31f2e64f845638fd3466ea5b0b03b3684ce82566ea04fc5aae7dce"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 6,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 500,
  "cumulative_CRD": 500
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p006-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP06-c.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-mo03-o-1-source-001",
  "policy_id": "iris-mo03-o-1-source-001",
  "reservation_id": "iris-mo03-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO03-o-1",
   "sd-MO03-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 1000,
  "this_take": "sd-MO03-o-1"
 }
}
```

<!-- profile:MO03 -->
`pilot/sd-MO03-o-1/MO03/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 6,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 6,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 500
}
```

<!-- bound:MO03 -->
`pilot/sd-MO03-o-1/MO03/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO03",
 "task": "IRIS EP01 v4 MO03（s006，opening o-1）; Seedance 2.0 VIP first_frame, 6 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO03-o-1/preview-approval.json",
 "attempt_id": "iris-mo03-o-1-source-001",
 "policy_id": "iris-mo03-o-1-source-001",
 "reservation_id": "iris-mo03-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 500,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 500,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO03-o-<n>/continuity-report.json`（`units.MO03.verdict = "ready"`）。

## 7. s007 · MO04（first_frame，4 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p007-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP07-a.png`，sha `41c78422afe94819a01a2b9cb1c97f322d9aa43fbebb685381f2cfc3ef4ae4cd`）
- prompt sha `a41b690262012ed90f96949500dd5908fa68db2a03b5d171fcb37caa8a4f87f7`；spec 必须逐字出现：`眯眼往上看树后那块发白光的广告牌`、`她把挡在面前的树枝往下拽`、`镜头固定`、`从外套口袋里掏出一张空白的白色姓名贴`、`广告牌的白光整片打到她脸上`、`树枝弹回去、叶子晃动`、`她不躲`
- 取代旧认可：`outputs/ai-city-takeover/ep01/v4/pilot/sd-MO04/preview-approval.json`（不动）
- 文件夹：`pilot/sd-MO04-o-1/`、`pilot/sd-MO04-o-2/`；建议 id：`iris-mo04-o-<n>-source-001` / `iris-mo04-o-<n>-reservation-001`

<!-- approval:MO04 -->
`pilot/sd-MO04-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO04-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p007-w1.png",
   "sha256": "41c78422afe94819a01a2b9cb1c97f322d9aa43fbebb685381f2cfc3ef4ae4cd",
   "role": "MO04 first frame"
  }
 ],
 "prompts": {
  "MO04": {
   "text": "镜头固定。她把挡在面前的树枝往下拽，眯眼往上看树后那块发白光的广告牌；然后松手，树枝弹回去、叶子晃动，广告牌的白光整片打到她脸上，她不躲，从外套口袋里掏出一张空白的白色姓名贴。面无表情，带着一点好奇。机头直闪。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "a41b690262012ed90f96949500dd5908fa68db2a03b5d171fcb37caa8a4f87f7"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 4,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p007-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP07-a.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "replaces_approval": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO04/preview-approval.json",
  "sha256": "e0a95ba650d8b712f6b80ff25bdd1d624d6ccbf5ee96b26612d729d536065754"
 },
 "bound_ids": {
  "attempt_id": "iris-mo04-o-1-source-001",
  "policy_id": "iris-mo04-o-1-source-001",
  "reservation_id": "iris-mo04-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO04-o-1",
   "sd-MO04-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-MO04-o-1"
 }
}
```

<!-- profile:MO04 -->
`pilot/sd-MO04-o-1/MO04/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 4,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 4,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:MO04 -->
`pilot/sd-MO04-o-1/MO04/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO04",
 "task": "IRIS EP01 v4 MO04（s007，opening o-1）; Seedance 2.0 VIP first_frame, 4 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO04-o-1/preview-approval.json",
 "attempt_id": "iris-mo04-o-1-source-001",
 "policy_id": "iris-mo04-o-1-source-001",
 "reservation_id": "iris-mo04-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO04-o-<n>/continuity-report.json`（`units.MO04.verdict = "ready"`）。

## 8. s008 · SG02（multimodal，4 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p008-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP08-a.png`，sha `c602b3883f46db5a4f97b44c9e67acbe2d5122709a665ee6b75225214a9f4747`）
- 人声：`outputs/ai-city-takeover/ep01/v4/pilot/audio/SG02.wav`（sha `27b5e6f657bc255125aee11d4885def24281c554f6e8d409121ccb915118c733`，4.0 s，窗口 [29.529, 33.529]）；`run_unit.sh` 第二参数 `29.529`
- prompt sha `5c4b1459be0907a17a892d0792fb9b3dc9902bb9f3c8a7102f0366abb908dfcb`；spec 必须逐字出现：`中近景`、`对着镜头平平地说话`、`逐字精确同步`、`啪地拍在胸口，用拇指抹平`、`镜头固定不动`、`不转身，不转头`、`嘴前没有任何遮挡`
- 取代旧认可：`outputs/ai-city-takeover/ep01/v4/pilot/sd-SG02-r2/preview-approval.json`（不动）
- 文件夹：`pilot/sd-SG02-o-1/`、`pilot/sd-SG02-o-2/`；建议 id：`iris-sg02-o-<n>-source-001` / `iris-sg02-o-<n>-reservation-001`

<!-- approval:SG02 -->
`pilot/sd-SG02-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-SG02-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p008-w1.png",
   "sha256": "c602b3883f46db5a4f97b44c9e67acbe2d5122709a665ee6b75225214a9f4747",
   "role": "SG02 reference image"
  },
  {
   "path": "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG02.wav",
   "sha256": "27b5e6f657bc255125aee11d4885def24281c554f6e8d409121ccb915118c733",
   "role": "SG02 vocal"
  }
 ],
 "prompts": {
  "SG02": {
   "text": "{{image:0}}中的她对着镜头平平地说话，口型与{{audio:1}}里的人声逐字精确同步。中近景，镜头固定不动，全程正对镜头，不转身，不转头。她把空白姓名贴从底纸上撕下来，啪地拍在胸口，用拇指抹平。嘴前没有任何遮挡。机头直闪。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "5c4b1459be0907a17a892d0792fb9b3dc9902bb9f3c8a7102f0366abb908dfcb"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "multimodal",
  "seconds": 4,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": "reference_audio"
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "reference image（p008-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP08-a.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "replaces_approval": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG02-r2/preview-approval.json",
  "sha256": "9bebcd09dabe9d13b7a390773cc7e37f9c911974728033816ed37629928e9e95"
 },
 "bound_ids": {
  "attempt_id": "iris-sg02-o-1-source-001",
  "policy_id": "iris-sg02-o-1-source-001",
  "reservation_id": "iris-sg02-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-SG02-o-1",
   "sd-SG02-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-SG02-o-1"
 }
}
```

<!-- profile:SG02 -->
`pilot/sd-SG02-o-1/SG02/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "multimodal",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 4,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 4,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:SG02 -->
`pilot/sd-SG02-o-1/SG02/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "SG02",
 "task": "IRIS EP01 v4 SG02（s008，opening o-1）; Seedance 2.0 VIP multimodal, 4 s 4k 16:9, reference vocal",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG02-o-1/preview-approval.json",
 "attempt_id": "iris-sg02-o-1-source-001",
 "policy_id": "iris-sg02-o-1-source-001",
 "reservation_id": "iris-sg02-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-SG02-o-<n>/continuity-report.json`（`units.SG02.verdict = "ready"`）。

## 9. s009 · MO21（first_frame，4 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p009-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP09-a.png`，sha `451f67af1297cfcfc63229c06cc5129c063c7d8966682ed6932ed45b429ecc73`）
- prompt sha `5043d74aa0922a246b124079700b92197efaa2e0560f0fbf5f4e28f1593c2e11`；spec 必须逐字出现：`她侧身坐在候车亭的长凳上`、`伸出一根手指`、`镜头固定`、`停在划痕尽头`、`用指甲顺着灯箱玻璃上那道划痕慢慢划过去`、`面无表情，带着一点好奇`
- 文件夹：`pilot/sd-MO21-o-1/`、`pilot/sd-MO21-o-2/`；建议 id：`iris-mo21-o-<n>-source-001` / `iris-mo21-o-<n>-reservation-001`

<!-- approval:MO21 -->
`pilot/sd-MO21-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO21-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p009-w1.png",
   "sha256": "451f67af1297cfcfc63229c06cc5129c063c7d8966682ed6932ed45b429ecc73",
   "role": "MO21 first frame"
  }
 ],
 "prompts": {
  "MO21": {
   "text": "镜头固定。她侧身坐在候车亭的长凳上，伸出一根手指，用指甲顺着灯箱玻璃上那道划痕慢慢划过去，停在划痕尽头。面无表情，带着一点好奇。机头直闪。画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "5043d74aa0922a246b124079700b92197efaa2e0560f0fbf5f4e28f1593c2e11"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 4,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p009-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP09-a.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "bound_ids": {
  "attempt_id": "iris-mo21-o-1-source-001",
  "policy_id": "iris-mo21-o-1-source-001",
  "reservation_id": "iris-mo21-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO21-o-1",
   "sd-MO21-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-MO21-o-1"
 }
}
```

<!-- profile:MO21 -->
`pilot/sd-MO21-o-1/MO21/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 4,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 4,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:MO21 -->
`pilot/sd-MO21-o-1/MO21/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO21",
 "task": "IRIS EP01 v4 MO21（s009，opening o-1）; Seedance 2.0 VIP first_frame, 4 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO21-o-1/preview-approval.json",
 "attempt_id": "iris-mo21-o-1-source-001",
 "policy_id": "iris-mo21-o-1-source-001",
 "reservation_id": "iris-mo21-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO21-o-<n>/continuity-report.json`（`units.MO21.verdict = "ready"`）。

## 10. s010 · MO05（first_frame，5 s，单条上限 400）

- 首帧：`outputs/ai-city-takeover/ep01/v4/board/plates/p010-w1.png`（= `outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP10-a.png`，sha `a46b48ce8ce9d7217f9ca5bb06dedcfae4134f145cca7d04732fc6b10c808a23`）
- prompt sha `a0302ca1b6c98f5fde8167e35bef4ad9317be99a01a8c7c13f0f1fa815e7b897`；spec 必须逐字出现：`长焦侧拍`、`她双臂搭在天桥的铁丝网护栏上`、`镜头固定`、`转身沿着天桥往远处走去`、`银白短发保持原样`、`抬脚踹了护栏一下`、`整片铁丝网震动`
- 取代旧认可：`outputs/ai-city-takeover/ep01/v4/pilot/sd-MO05/preview-approval.json`（不动）
- 文件夹：`pilot/sd-MO05-o-1/`、`pilot/sd-MO05-o-2/`；建议 id：`iris-mo05-o-<n>-source-001` / `iris-mo05-o-<n>-reservation-001`

<!-- approval:MO05 -->
`pilot/sd-MO05-o-1/preview-approval.json`：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-opening-MO05-o-1",
 "question": "<主会话问使用者的原问题，逐字>",
 "user_quote": "<使用者原话，逐字（例：按页面拍 (Recommended)）>",
 "approved_at": "<UTC ISO 时间，带时区，例 2026-11-20T19:16:00Z>",
 "preview_page": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/index.html",
  "sha256": "447970689d3867d9c96460940d1dfa1fde06734dd417b7439f983bfcd914447f"
 },
 "preview_inputs": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json",
  "sha256": "ffd95bd02363f82f80376a56c9a638193ea731119638d0de08cfb13531d433da"
 },
 "prompt_source": {
  "path": "outputs/ai-city-takeover/ep01/v4/excerpt/flash/opening-seedance.md",
  "sha256": "3e02c3266a2e47f88dbd9da9e65d98cbe59950e61dc4cc718ebacc811b45fbdc"
 },
 "preview_artifacts": [
  {
   "path": "outputs/ai-city-takeover/ep01/v4/board/plates/p010-w1.png",
   "sha256": "a46b48ce8ce9d7217f9ca5bb06dedcfae4134f145cca7d04732fc6b10c808a23",
   "role": "MO05 first frame"
  }
 ],
 "prompts": {
  "MO05": {
   "text": "长焦侧拍，镜头固定。她双臂搭在天桥的铁丝网护栏上往下看桥下的车流；然后抬脚踹了护栏一下，整片铁丝网震动；她两手插进外套口袋，转身沿着天桥往远处走去，银白短发保持原样。桥下车灯只有白色和琥珀色。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。",
   "sha256": "a0302ca1b6c98f5fde8167e35bef4ad9317be99a01a8c7c13f0f1fa815e7b897"
  }
 },
 "generation": {
  "model": "seedance_2.0_vip",
  "mode": "first_frame",
  "seconds": 5,
  "resolution": "4k",
  "aspect": "16:9",
  "audio": null
 },
 "budget": {
  "generations": 1,
  "retries": 0,
  "operator_ceiling_per_unit_CRD": 400,
  "cumulative_CRD": 400
 },
 "identity_waivers": [
  "IRIS"
 ],
 "identity_waiver_basis": "first frame（p010-w1.png，与 outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP10-a.png 逐字节相同）承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图",
 "replaces_approval": {
  "path": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO05/preview-approval.json",
  "sha256": "3ff275afb9a492bef2b8e19974036c4d53c8334cadfc61d111b74202b7e30de3"
 },
 "bound_ids": {
  "attempt_id": "iris-mo05-o-1-source-001",
  "policy_id": "iris-mo05-o-1-source-001",
  "reservation_id": "iris-mo05-o-1-reservation-001"
 },
 "takes": {
  "approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
  "folders": [
   "sd-MO05-o-1",
   "sd-MO05-o-2"
  ],
  "generations_per_take": 1,
  "total_generations": 2,
  "total_ceiling_CRD": 800,
  "this_take": "sd-MO05-o-1"
 }
}
```

<!-- profile:MO05 -->
`pilot/sd-MO05-o-1/MO05/profile.json`：

```json
{
 "model_id": "seedance_2.0_vip",
 "input_mode": "first_frame",
 "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
 "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b",
 "node_id": "<本文件夹 node-created.json 的 node_id>",
 "duration_seconds": 5,
 "resolution": "4k",
 "aspect_ratio": "16:9",
 "benefit_amount": 5,
 "benefit_type": "seedance_20_pro_4k_output",
 "credit_upper_bound": 400
}
```

<!-- bound:MO05 -->
`pilot/sd-MO05-o-1/MO05/operator-bound.json`：

```json
{
 "schema_version": "iris-v4-unit/1",
 "unit": "MO05",
 "task": "IRIS EP01 v4 MO05（s010，opening o-1）; Seedance 2.0 VIP first_frame, 5 s 4k 16:9, no reference audio",
 "user_quote": "<与 preview-approval.json 的 user_quote 逐字相同>",
 "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO05-o-1/preview-approval.json",
 "attempt_id": "iris-mo05-o-1-source-001",
 "policy_id": "iris-mo05-o-1-source-001",
 "reservation_id": "iris-mo05-o-1-reservation-001",
 "max_submit_count": 1,
 "automatic_retries": 0,
 "operator_currency": "CRD",
 "operator_ceiling": 400,
 "ledger": "ledger.json",
 "cumulative_submit_ceiling": 1,
 "cumulative_operator_credit_ceiling": 400,
 "issued_at": "<UTC 现在，ISO>",
 "expires_at": "<issued_at + 3 小时>",
 "stop_on_unknown": true
}
```

连续性报告：`pilot/sd-MO05-o-<n>/continuity-report.json`（`units.MO05.verdict = "ready"`）。
