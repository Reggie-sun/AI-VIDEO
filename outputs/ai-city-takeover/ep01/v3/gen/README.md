# IRIS EP01 v3 付费生成 lane（待使用者认可后运行）

本目录是 `ep01/v2/gen/` 两条已跑通 lane 的 v3 副本；v2 原件不动。使用者认可预览包（`../pilot/preview.html`、`../pilot/preview-inputs.json`）之前，下面的命令一条都不跑。

- 命令一律在仓库根执行，不要 `cd` 进子目录。
- approval 与 operator-bound 里的所有 path 都相对仓库根（例：`outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav`）。只有 bound 的 `ledger` 相对 unit 文件夹的上级目录（默认就是本目录）。
- 数字人：`omnihuman.py`（lint / permit / record）+ `omnihuman.cjs`（fill / observe / submit / fetch）。trial 文件夹默认 `ep01/v3/pilot/oh/`，可用 `OMNI_TRIAL` 改。
- Seedance 2.0 VIP 首帧：`unit.py`（draft / materialize）、`operator.py`（prepare / start / submit / poll / fetch）、`lint.py`，以及 `addnode.cjs`、`balance.cjs`（与 v2 逐字相同）。approval 与连续性报告放 `ep01/v3/pilot/sd/`（`SD_PILOT`），unit 文件夹与 ledger 放本目录（`SD_UNITS`）；单独一条 take 用 `SD_TRIAL` 把四者放进同一文件夹（见第三节）。

## 一、数字人（即梦 数字人 · 大师模式 · OmniHuman 1.5），以 U021 为例

```bash
# 0. continuity-supervisor 出报告 → outputs/ai-city-takeover/ep01/v3/pilot/oh/continuity-report.json（units.U021.verdict = "ready"）
uv run python outputs/ai-city-takeover/ep01/v3/gen/omnihuman.py lint U021      # 1. 输入、秒数、动作文本、报告、ledger 余量
node outputs/ai-city-takeover/ep01/v3/gen/omnihuman.cjs fill U021              # 2. 上传本 take 的图和音频、选大师模式、填动作描述；不点生成
uv run python outputs/ai-city-takeover/ep01/v3/gen/omnihuman.py permit U021    # 3. 核对页面观察，写一次性 permit（20 分钟）
node outputs/ai-city-takeover/ep01/v3/gen/omnihuman.cjs submit U021            # 4. 先写 intent，再点一次生成；读点击前后精确余额
uv run python outputs/ai-city-takeover/ep01/v3/gen/omnihuman.py record U021    # 5. 记账；非 submitted 即关账
# 6. 主会话手写 pilot/oh/U021/job.json（点击后标签页跳到的 generate workspace）
node outputs/ai-city-takeover/ep01/v3/gen/omnihuman.cjs fetch U021             # 7. 下载结果卡片的唯一视频 → U021/fetch/<sha256>.mp4
# 8. 逐镜 Gate（shot-gate-reviewer，video-analysis MCP）全 PASS 才做下一个 take
```

fill 之后、permit 之前若要重读页面，用 `omnihuman.cjs observe U021`（不点击）。permit 只认页面上音频时长等于该 take `seconds` 的向下取整或向上取整：

| take | 秒数 | 可接受的页面显示 |
| --- | --- | --- |
| U020 | 6.41 | `00:06` / `00:07` |
| U021 | 4.36 | `00:04` / `00:05` |
| U022 | 3.57 | `00:03` / `00:04` |
| U025 | 6.21 | `00:06` / `00:07` |
| U027 | 4.17 | `00:04` / `00:05` |

主会话手写：`pilot/oh/preview-approval.json`、`pilot/oh/continuity-report.json`、`pilot/oh/<unit>/job.json`。approval 示例（只列 U021；其余 take 照 `../pilot/preview-inputs.json` 同样写入 `takes`，图和音频也列进 `preview_artifacts`）：

```json
{
 "schema": "iris-v3-preview-approval/1",
 "unit_group": "pilot-digital-human",
 "question": "<问使用者的原问题>",
 "user_quote": "<使用者原话，逐字>",
 "approved_at": "<UTC ISO 时间>",
 "preview_page": {"path": "outputs/ai-city-takeover/ep01/v3/pilot/preview.html", "sha256": "cb99a4121ad1b2bc5713fba3d95b4cd6b3ce5366248ecc5001f17c42f7ea21a9"},
 "preview_inputs": {"path": "outputs/ai-city-takeover/ep01/v3/pilot/preview-inputs.json", "sha256": "544ba5d9fe181ecc7018f1e7741c45bfab4e491396f8322b9e48ff0510c3b1a2"},
 "preview_artifacts": [
  {"path": "outputs/ai-city-takeover/ep01/v3/plates/raw/P-gap-mcu-shut-b.png", "sha256": "ffe0c323ef57309e72002e93811472d54490865b81b35f4a5afe96e809ef5bdf", "role": "U021 still"},
  {"path": "outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav", "sha256": "b74a2cdb1581e01a6676091c7010a1380ef05b725e679fe41de26bba158d077e", "role": "U021 vocal"}
 ],
 "takes": {
  "U021": {
   "image": {"path": "outputs/ai-city-takeover/ep01/v3/plates/raw/P-gap-mcu-shut-b.png", "sha256": "ffe0c323ef57309e72002e93811472d54490865b81b35f4a5afe96e809ef5bdf"},
   "audio": {"path": "outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav", "sha256": "b74a2cdb1581e01a6676091c7010a1380ef05b725e679fe41de26bba158d077e", "seconds": 4.36},
   "action_prompt": "镜头固定中景。她冷静但投入地对着镜头唱歌，嘴随歌词自然张合，乐句之间轻轻换气，下巴微微压低，眉头放松，眼睛向上直视镜头，肩膀随呼吸微微起伏，双手自然垂在身侧。",
   "action_prompt_sha256": "dbeb5fca4bd66396e7aeed1764eeb5dcbbd54d990757420861c021fc1af8bfe7"
  }
 },
 "mode": "即梦 数字人 · 大师模式（OmniHuman 1.5）· 1080P · single subject",
 "budget": {"generations": 5, "retries": 0, "operator_ceiling_per_take_CRD": 165, "cumulative_CRD": 825}
}
```

`seconds` 必须等于 wav 实际时长（四舍五入到 0.01 s），lint 会核对。上限每次都从 `budget` 读：`generations` 总次数、`cumulative_CRD` 总积分、`operator_ceiling_per_take_CRD` 单条积分、`retries` 单条重试（0 = 每条只交一次）。

continuity-report 示例（两条 lane 同形；代码只认 `units.<unit>.verdict == "ready"`）：

```json
{"schema": "iris-v3-continuity-report/1", "reviewed_by": "continuity-supervisor", "reviewed_at": "<日期>",
 "inputs": {"preview_approval": {"path": "outputs/ai-city-takeover/ep01/v3/pilot/oh/preview-approval.json", "sha256": "<sha256>"}},
 "units": {"U021": {"verdict": "ready", "continuity": "<…>", "handoff": "<…>", "axis_action_camera": "<…>", "prompt_fit": "<…>", "lint": "<…>"}}}
```

job.json 示例：

```json
{"unit": "U021", "workspace_url": "https://jimeng.jianying.com/ai-tool/generate?workspace=<id>", "note": "点击后 home#omnihuman-U021 标签页跳到这个 workspace；按页面上的动作描述对应"}
```

## 二、Seedance 2.0 VIP 首帧（canonical runtime），以 U023 为例

```bash
uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py draft U023                  # 1. 从 approval 取 prompt 与首帧，绑定 v3 coverage
node outputs/ai-city-takeover/ep01/v3/gen/addnode.cjs outputs/ai-city-takeover/ep01/v3/gen/U023   # 2. IRIS 画布加一个空视频节点 → U023/node-created.json
# 3. 主会话手写 gen/U023/profile.json（node_id 取自 node-created.json）与 gen/U023/operator-bound.json
uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py materialize U023 --profile outputs/ai-city-takeover/ep01/v3/gen/U023/profile.json   # 4. 建 unit 项目 + transport-free prepare
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py prepare U023            # 5. 冻结 prepared.json（无调用）
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py start U023              # 6. 建 attempt（无调用）
# 7. continuity-supervisor 出报告 → outputs/ai-city-takeover/ep01/v3/pilot/sd/continuity-report.json
uv run python outputs/ai-city-takeover/ep01/v3/gen/lint.py U023                        # 8. 全部检查通过才可提交
node outputs/ai-city-takeover/ep01/v3/gen/balance.cjs                                 # 提交前精确余额
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py submit U023             # 9. 一次性提交
node outputs/ai-city-takeover/ep01/v3/gen/balance.cjs                                 # 提交后精确余额
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py poll U023               # 10. 查询（可重复）
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py fetch U023              #     完成后取回
# 11. 逐镜 Gate 全 PASS 才做 U045
```

主会话手写：`pilot/sd/preview-approval.json`、`pilot/sd/continuity-report.json`、`gen/<unit>/profile.json`、`gen/<unit>/operator-bound.json`。approval 示例（只列 U023；U045 同样加首帧 `P-floor-line-b.png`，role `U045 first frame`）：

```json
{
 "schema": "iris-v3-preview-approval/1",
 "unit_group": "pilot-seedance",
 "question": "<问使用者的原问题>",
 "user_quote": "<使用者原话，逐字>",
 "approved_at": "<UTC ISO 时间>",
 "preview_page": {"path": "outputs/ai-city-takeover/ep01/v3/pilot/preview.html", "sha256": "cb99a4121ad1b2bc5713fba3d95b4cd6b3ce5366248ecc5001f17c42f7ea21a9"},
 "preview_inputs": {"path": "outputs/ai-city-takeover/ep01/v3/pilot/preview-inputs.json", "sha256": "544ba5d9fe181ecc7018f1e7741c45bfab4e491396f8322b9e48ff0510c3b1a2"},
 "preview_artifacts": [
  {"path": "outputs/ai-city-takeover/ep01/v3/plates/raw/P-city-gap-a.png", "sha256": "61248d1238a7cef119676bd84244548cba615b83cf96866a00a3637dd4597426", "role": "U023 first frame"}
 ],
 "prompts": {
  "U023": {"text": "镜头固定。首帧是从一扇只开着一指宽的黑色门缝向外看出去的画面：门缝两侧是黑暗的门板边缘，缝里是凌晨三点雾中的城市。门不动，门缝始终只有一指宽。缝外的城市在动：高架桥上的车灯缓缓流过，远处高楼的窗灯安静地亮着，雾气慢慢飘过。城市的光是冷白和钢蓝色。画面里没有人。",
           "sha256": "c9859e795b6e33949e61feb4a7db368c20b009a3cad2d915e71ad31a5228e55f"}
 },
 "generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "1080p", "aspect": "16:9", "audio": null},
 "budget": {"generations": 2, "retries": 0, "operator_ceiling_per_unit_CRD": 165, "cumulative_CRD": 330},
 "identity_waivers": ["IRIS"],
 "identity_waiver_basis": "每条视频请求只有这张首帧；首帧承担 IRIS（canon v4）的身份"
}
```

`generation` 必须逐字如上（`model` 写 `seedance_2.0_vip`，不是显示名）。`unit.py` 里 U023 / U045 的意图文字按这两条 prompt 和首帧写成：approval 换了首帧或改了 prompt，draft 会直接 Blocked，需要先改 `unit.py` 的 spec。

profile.json 示例（账号、画布与 v2 相同；`node_id` 每条新建）：

```json
{"model_id":"seedance_2.0_vip","input_mode":"first_frame","account_sha256":"72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe","project_id":"829df260-5a63-4f0d-8265-8353dc693b3b","node_id":"<node-created.json 的 node_id>","duration_seconds":5,"resolution":"1080p","aspect_ratio":"16:9","benefit_amount":5,"benefit_type":"seedance_20_pro_1080p_output","credit_upper_bound":165}
```

operator-bound.json 示例（`user_quote` 与 approval 逐字相同；两个累计上限等于 approval 的 `budget.generations` / `budget.cumulative_CRD`，lint 会核对）：

```json
{"schema_version": "iris-v3-unit/1", "unit": "U023", "task": "IRIS EP01 v3 pilot U023（门缝外的城市，首帧，固定机位）; Seedance 2.0 VIP first-frame, 5 s 1080p 16:9, no audio",
 "user_quote": "<与 approval.user_quote 逐字相同>", "preview_approval": "outputs/ai-city-takeover/ep01/v3/pilot/sd/preview-approval.json",
 "attempt_id": "iris-u023-source-001", "policy_id": "iris-u023-source-001", "reservation_id": "iris-u023-reservation-001",
 "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": 165,
 "ledger": "ledger-pilot-sd.json", "cumulative_submit_ceiling": 2, "cumulative_operator_credit_ceiling": 330,
 "issued_at": "<UTC 现在>", "expires_at": "<issued_at + 3 小时>", "stop_on_unknown": true}
```

## 三、Seedance 2.0 VIP 全能参考对嘴（ESCAPE VELOCITY 做法），以 U021 为例

做法同 `escape_velocity_analysis/source_docs/FINDINGS.md` §B8 与 v2 `LSen1`（2026-11-03 已跑通同一 model / mode / 1080p / 5 s，实扣 115 积分）：认可的底片作 `{{image:0}}`，该镜的人声窗口作 `{{audio:1}}`，短 prompt 说她逐字对嘴。这一条 take 的 approval、连续性报告、ledger 与 unit 文件夹都在 `ep01/v3/pilot/sd-r3/`，所有命令前加 `SD_TRIAL=outputs/ai-city-takeover/ep01/v3/pilot/sd-r3`（不设时仍是上面 U023 的布局，行为不变）。

```bash
export SD_TRIAL=outputs/ai-city-takeover/ep01/v3/pilot/sd-r3
uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py draft U021                  # 1. 取 approval 的图、人声、prompt；身份、角色名、标记、时长全核对
node outputs/ai-city-takeover/ep01/v3/gen/addnode.cjs $SD_TRIAL/U021                    # 2. IRIS 画布加一个空视频节点 → sd-r3/U021/node-created.json
# 3. 主会话手写 sd-r3/U021/profile.json（node_id 取自 node-created.json）与 sd-r3/U021/operator-bound.json
uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py materialize U021 --profile $SD_TRIAL/U021/profile.json   # 4. 建项目 + transport-free prepare（填入请求，无调用）
uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py show U021                   # 5. 观察：打印将提交的精确请求（model / mode / 秒数 / 分辨率 / 图与音频绑定 / prompt）
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py prepare U021            # 6. 冻结 prepared.json 与付费预览（上限 = bound 的 operator_ceiling，无调用）
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py start U021              # 7. 建 attempt（无调用）
# 8. continuity-supervisor 出报告 → $SD_TRIAL/continuity-report.json（units.U021.verdict = "ready"）
uv run python outputs/ai-city-takeover/ep01/v3/gen/lint.py U021                        # 9. 全部检查通过（含 audio_binding、bound_output）才可提交
node outputs/ai-city-takeover/ep01/v3/gen/balance.cjs                                 # 提交前精确余额
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py submit U021             # 10. 一次性提交；一次性授权只在 bound 的窗口内有效，先写 intent 与 ledger 再提交
node outputs/ai-city-takeover/ep01/v3/gen/balance.cjs                                 # 提交后精确余额 → 如实记账
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py poll U021               # 11. 查询（可重复）
uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py fetch U021              #     完成后取回
# 12. 逐镜 Gate（shot-gate-reviewer，video-analysis MCP）：片段自带音轨与 U021.wav 对齐量测 + 看口型；全 PASS 才往下
```

与数字人 lane 的对应：fill = 第 4 步 materialize（请求在本地填好，不碰页面输入框）；observe = 第 5 步 `show`；permit = `operator-bound.json` + submit 内一次性授权；record = submit 自动写 `$SD_TRIAL/ledger.json` 加前后余额读数。

主会话手写 `sd-r3/preview-approval.json`（`unit.py` 只认下面这个形状）：

```json
{
 "schema": "iris-v3-preview-approval/1",
 "unit_group": "pilot-seedance-lipsync-r3",
 "question": "<问使用者的原问题>",
 "user_quote": "<使用者原话，逐字>",
 "approved_at": "<UTC ISO 时间>",
 "preview_artifacts": [
  {"path": "outputs/ai-city-takeover/ep01/v3/plates/raw/P-gap-mcu-sing.png", "sha256": "4cb7b152e8e9ed40320e8dcdf73ce51e12c338bbb1d118a9ad2e6a1cc21bde2f", "role": "U021 reference image"},
  {"path": "outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav", "sha256": "b74a2cdb1581e01a6676091c7010a1380ef05b725e679fe41de26bba158d077e", "role": "U021 vocal"}
 ],
 "prompts": {"U021": {"text": "{{image:0}}中的她对着镜头唱歌，口型与{{audio:1}}里的人声逐字精确同步。中近景，她闭着眼睛投入地唱，神情平静，面无表情，眉头舒展；唱到句尾慢慢睁开眼睛，平静地看着镜头。镜头全程锁定，一镜到底。", "sha256": "14f92efd96c54f1bf8582b5f8ed4aa4acc69c5977d2a3252dff1964fd526b27d"}},
 "generation": {"model": "seedance_2.0_vip", "mode": "multimodal", "seconds": 5, "resolution": "1080p", "aspect": "16:9", "audio": "reference_audio"},
 "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 200, "cumulative_CRD": 200},
 "identity_waivers": ["IRIS"],
 "identity_waiver_basis": "全能参考对嘴：这张参考图承担 IRIS（canon v4）的身份，不附身份图"
}
```

- 标记是即梦原生的 **0 起全局序号**（先图后音频）：图 `{{image:0}}`、人声 `{{audio:1}}`。写成 `{{image:1}}` 会被 draft 拦下（canonical adapter 也会拒绝）。prompt 里只能有这两个标记，各至少出现一次；标记外不得有英文字母。
- 以 `U021 ` 开头的 role 只能是这两个；多列一个（例如 `U021 first frame`）draft 就 Blocked。图与人声的 path 必须是 `unit.py` 里 U021 spec 写的那两个文件，sha256 必须等于文件当前字节；人声还要与 `pilot/audio/windows.json` 的 U021 条目一致，16-bit 单声道 WAV，时长在 2 s 到 5 s 之间（模型下限、本 take 秒数）。
- `unit.py` 的 U021 spec 要求 prompt 里逐字出现：`中近景`、`对着镜头唱歌`、`逐字精确同步`、`闭着眼睛投入地唱`、`神情平静`、`唱到句尾慢慢睁开眼睛`、`镜头全程锁定`。定稿 prompt 去掉其中任何一句，draft 会 Blocked，需要先改 spec。
- 片段自带音轨（native audio，本 adapter 恒开）会跟着参考人声生成，用来量对嘴偏移；成片换成歌曲母带。

profile.json 示例（`input_mode` 写 `multimodal`；`credit_upper_bound` = approval 的单条上限）：

```json
{"model_id":"seedance_2.0_vip","input_mode":"multimodal","account_sha256":"72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe","project_id":"829df260-5a63-4f0d-8265-8353dc693b3b","node_id":"<node-created.json 的 node_id>","duration_seconds":5,"resolution":"1080p","aspect_ratio":"16:9","benefit_amount":5,"benefit_type":"seedance_20_pro_1080p_output","credit_upper_bound":200}
```

operator-bound.json 示例（`ledger` 相对 `$SD_TRIAL`）：

```json
{"schema_version": "iris-v3-unit/1", "unit": "U021", "task": "IRIS EP01 v3 U021 对嘴（EV 做法）：P-gap-mcu-sing + U021 人声 4.36 s；Seedance 2.0 VIP multimodal 5 s 1080p 16:9",
 "user_quote": "<与 approval.user_quote 逐字相同>", "preview_approval": "outputs/ai-city-takeover/ep01/v3/pilot/sd-r3/preview-approval.json",
 "attempt_id": "iris-u021-source-001", "policy_id": "iris-u021-source-001", "reservation_id": "iris-u021-reservation-001",
 "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": 200,
 "ledger": "ledger.json", "cumulative_submit_ceiling": 1, "cumulative_operator_credit_ceiling": 200,
 "issued_at": "<UTC 现在>", "expires_at": "<issued_at + 3 小时>", "stop_on_unknown": true}
```

离线核对（不联网、不写仓库）：把 approval 草稿放进 `/tmp/sd-r3/`，`SD_TRIAL=/tmp/sd-r3` 跑 draft → materialize（profile 用占位 `node_id`）→ show。测试：`PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider outputs/ai-city-takeover/ep01/v3/gen/test_unit_lanes.py`。

## 停止规则

- 任何 lint / permit / draft / materialize / prepare 失败或 Blocked：停，报告失败项；不手改产物硬过。
- 页面音频时长既不是向下取整也不是向上取整（或读不到）：permit 失败，停，报告页面实际显示。
- permit 或 lint 之后 approval、fill 观察有任何改动：submit 拒绝；permit 只用一次，不重签。
- 价格超过单条上限，或累计次数 / 积分会超过 approval 的 `budget`：停。
- 数字人任一 outcome 不是 `submitted`（含 unknown）：ledger 关账，整个 lane 停；Seedance attempt 出现 `outcome_unknown` / `interrupted`：operator 拒绝，只经 canonical committer 取证恢复。不盲目重试、不重签、不重复提交。
- 即梦入口审核拒绝新脸：停，不做预处理绕过。
- 一条出现冻脸、牙齿碎裂、多出的手或身份漂移：停该 lane，报告，不加 take。
- 一次只做一条：submit → fetch → 逐镜 Gate（全 PASS）→ 下一条；每次提交前后读精确余额，完成后如实报告积分。
