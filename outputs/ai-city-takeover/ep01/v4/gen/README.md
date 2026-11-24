# IRIS EP01 v4 付费生成 lane（待使用者认可预览包后运行）

本目录是 `ep01/v3/gen/` 三条 lane 的 v4 副本，读 v4 分镜 `../board/shots.json`；v3 原件不动。**使用者认可该片段的预览包之前，下面会提交、填页面、写 permit、加节点或读余额的命令一条都不跑。** 预览包之前只能跑本地、只读或只写本地文件的两步：`units.py`（列输入）和 `cut_audio.py`（切人声）。

- 命令一律在仓库根执行，不要 `cd` 进子目录。
- unit 编号就是分镜的 clip 编号：`SG..` 唱段（`motion_tier: sung`），`MO..` 动作段（`motion`）；`plate3d` 镜头不走这里。
- approval 与 operator-bound 里的所有 path 都相对仓库根（例：`outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03.wav`）。只有 bound 的 `ledger` 相对 unit 文件夹的上级目录（默认就是本目录）。
- 首帧／参考图一律是该 clip 的底片 `../board/plates/<start_frame>.png`（1672×941）。身份锚点 `../face/IRIS-anchor-F1a.png`（sha `2dd80e2f…d54b6a`）取代 v3 的 canon v4／E3：写进 Character 的出处并逐字节核对，**不发给 Provider**；身份仍由认可的底片加 approval 的 `identity_waivers: ["IRIS"]` 承担。
- 数字人：`omnihuman.py`（lint / permit / record）+ `omnihuman.cjs`（fill / observe / submit / fetch）。trial 文件夹默认 `ep01/v4/pilot/oh/`，可用 `OMNI_TRIAL` 改。
- 画质：使用者 2026-11-17「积分随便用，我现在积分很多。画质最高」→ Seedance 一律 `4k`（`seedance_2.0_vip` 支持 720p / 1080p / 4k；16:9 4k 栅格 3840×2160）。4k 的积分价仓库里没有记录：单条上限按页面报价封存，`operator.py prepare` 冻结的付费预览上限就是 bound 的 `operator_ceiling`。数字人 lane 没有画质选项（见第一节）。
- Seedance 2.0 VIP：`unit.py`（draft / materialize / show）、`operator.py`（prepare / start / submit / poll / fetch）、`lint.py`，以及 `addnode.cjs`、`balance.cjs`（与 v3 逐字相同，同一张 IRIS 画布）。approval 与连续性报告放 `ep01/v4/pilot/sd/`（`SD_PILOT`），unit 文件夹与 ledger 放本目录（`SD_UNITS`）；单独一条 take 用 `SD_TRIAL` 把四者放进同一文件夹（见第三节）。

## 〇、预览包输入（本地，不联网）

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/cut_audio.py SG03          # 唱段：切该 clip 的生成窗口 → pilot/audio/SG03.wav，并封存进 pilot/audio/windows.json
uv run python outputs/ai-city-takeover/ep01/v4/gen/units.py SG03 MO06         # 列预览包要的输入：底片 path+sha、人声 path+sha+秒数、窗口、逐字时间、该镜的动作与机位文字
```

- `cut_audio.py`：从 Demucs 人声轨 `song/stems/htdemucs_ft/all-hands-r4-edc6c6bf/vocals.wav`（44.1 kHz 立体声）取 `[round(t0·sr), round(t1·sr))` 样本，`floor((L+R+1)/2)` 混成单声道，16-bit PCM WAV，不加淡入淡出——与 v3 `pilot/audio/U021.wav` 的切法逐样本相同（测试核对）。窗口是 clip 的 `window`（含前置余量），不是 `plays`。起点落在 `song/timing/words.json` 某个词内部超过 0.05 s 就拒绝；已存在且字节不同的 wav 不覆盖。打印秒数（0.01）与 sha256。SG03 的结果：5.99 s，sha256 `a41a1ba3c57e65a36154b84dd21c4a546c072d5e1a49ca06139b1f27f9e22559`。
- `units.py`：只读；任一输入缺失（底片没出、人声没切或不是 windows.json 封存的窗口）就列进 `missing` 并以 2 退出，不拿半套输入做预览包。

## 一、数字人（即梦 数字人 · 大师模式 · OmniHuman 1.5），以 SG03 为例

```bash
# 0. continuity-supervisor 出报告 → outputs/ai-city-takeover/ep01/v4/pilot/oh/continuity-report.json（units.SG03.verdict = "ready"）
uv run python outputs/ai-city-takeover/ep01/v4/gen/omnihuman.py lint SG03      # 1. 输入、秒数、动作文本、报告、ledger 余量
node outputs/ai-city-takeover/ep01/v4/gen/omnihuman.cjs fill SG03              # 2. 上传本 take 的图和音频、选大师模式、填动作描述；不点生成
uv run python outputs/ai-city-takeover/ep01/v4/gen/omnihuman.py permit SG03    # 3. 核对页面观察，写一次性 permit（20 分钟）
node outputs/ai-city-takeover/ep01/v4/gen/omnihuman.cjs submit SG03            # 4. 先写 intent，再点一次生成；读点击前后精确余额
uv run python outputs/ai-city-takeover/ep01/v4/gen/omnihuman.py record SG03    # 5. 记账；非 submitted 即关账
# 6. 主会话手写 pilot/oh/SG03/job.json（点击后标签页跳到的 generate workspace）
node outputs/ai-city-takeover/ep01/v4/gen/omnihuman.cjs fetch SG03             # 7. 下载结果卡片的唯一视频 → SG03/fetch/<sha256>.mp4
# 8. 逐镜 Gate（shot-gate-reviewer，video-analysis MCP）全 PASS 才做下一个 take
```

fill 之后、permit 之前若要重读页面，用 `omnihuman.cjs observe SG03`（不点击）。画质：`omnihuman.cjs` 不选分辨率，只从面板文字里读 `1080P/720P/480P/2K/4K` 标签；v3 两次实拍面板上都没有这个标签（`resolution: null`），取回的片子是 1920×1088、60 fps。permit 只拦低于 1080P 的标签和「生动模式」。permit 只认页面上音频时长等于该 take `seconds` 的向下取整或向上取整：SG03 5.99 s → `00:05` / `00:06`。

主会话手写：`pilot/oh/preview-approval.json`、`pilot/oh/continuity-report.json`、`pilot/oh/<unit>/job.json`。approval 示例（形状与 v3 相同；只列 SG03）：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-digital-human",
 "question": "<问使用者的原问题>",
 "user_quote": "<使用者原话，逐字>",
 "approved_at": "<UTC ISO 时间>",
 "preview_page": {"path": "<预览页 path>", "sha256": "<sha256>"},
 "preview_artifacts": [
  {"path": "outputs/ai-city-takeover/ep01/v4/board/plates/p012.png", "sha256": "5c5323ace6605783c58a029b275e67b21523ed6f1f74d63a87f6de4ad5d5f0d2", "role": "SG03 still"},
  {"path": "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03.wav", "sha256": "<cut_audio.py 打印的 sha256>", "role": "SG03 vocal"}
 ],
 "takes": {
  "SG03": {
   "image": {"path": "outputs/ai-city-takeover/ep01/v4/board/plates/p012.png", "sha256": "5c5323ace6605783c58a029b275e67b21523ed6f1f74d63a87f6de4ad5d5f0d2"},
   "audio": {"path": "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03.wav", "sha256": "<sha256>", "seconds": 5.99},
   "action_prompt": "<使用者认可的纯中文动作描述>",
   "action_prompt_sha256": "<sha256>"
  }
 },
 "mode": "即梦 数字人 · 大师模式（OmniHuman 1.5）· single subject",
 "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_take_CRD": "<单条上限>", "cumulative_CRD": "<总上限>"}
}
```

`seconds` 必须等于 wav 实际时长（四舍五入到 0.01 s），lint 会核对。上限每次都从 `budget` 读（整数）：`generations` 总次数、`cumulative_CRD` 总积分、`operator_ceiling_per_take_CRD` 单条积分、`retries` 单条重试（0 = 每条只交一次）。v3 的单条上限 165 是按 3.6–6.4 s 定的；v4 唱段 4.0–7.8 s，上限按页面报价重新封存。

continuity-report 示例（三条 lane 同形；代码只认 `units.<unit>.verdict == "ready"`）：

```json
{"schema": "iris-v4-continuity-report/1", "reviewed_by": "continuity-supervisor", "reviewed_at": "<日期>",
 "inputs": {"preview_approval": {"path": "outputs/ai-city-takeover/ep01/v4/pilot/oh/preview-approval.json", "sha256": "<sha256>"}},
 "units": {"SG03": {"verdict": "ready", "continuity": "<…>", "handoff": "<…>", "axis_action_camera": "<…>", "prompt_fit": "<…>", "lint": "<…>"}}}
```

## 二、Seedance 2.0 VIP 首帧（canonical runtime），以 MO06 为例

前提：`ep01/v4/director-coverage.json`（schema 4，unit_id = clip 编号）。它由 `build_coverage.py` 从使用者 2026-11-17 认可的分镜机械生成（导演授权），用仓库自己的 `director_coverage_authoring_input` 校验；分镜一改就重跑 `uv run python outputs/ai-city-takeover/ep01/v4/gen/build_coverage.py`，`--check` 只核对不写。没有它 `unit.py draft` 直接 Blocked。`draft` 先核对分镜、spec、coverage（不写任何文件），再读 approval。`unit.py` 只收写了 spec 的 clip（现在是 `MO06`、`SG03`），其他 clip 先在 `SPECS` 里按同样的格式写 spec（底片 sha、秒数 = clip 秒数向上取整、必须出现在 prompt 里的字句）。

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py draft MO06                  # 1. 从 approval 取 prompt 与首帧；核对分镜 sha、底片 sha、锚点 sha、clip 窗口与秒数，绑定 v4 coverage
node outputs/ai-city-takeover/ep01/v4/gen/addnode.cjs outputs/ai-city-takeover/ep01/v4/gen/MO06   # 2. IRIS 画布加一个空视频节点 → MO06/node-created.json
# 3. 主会话手写 gen/MO06/profile.json（node_id 取自 node-created.json）与 gen/MO06/operator-bound.json
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py materialize MO06 --profile outputs/ai-city-takeover/ep01/v4/gen/MO06/profile.json   # 4. 建 unit 项目 + transport-free prepare
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py show MO06                   # 5. 打印将提交的精确请求（只读）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py prepare MO06            # 6. 冻结 prepared.json（无调用）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py start MO06              # 7. 建 attempt（无调用）
# 8. continuity-supervisor 出报告 → outputs/ai-city-takeover/ep01/v4/pilot/sd/continuity-report.json
uv run python outputs/ai-city-takeover/ep01/v4/gen/lint.py MO06                        # 9. 全部检查通过才可提交
node outputs/ai-city-takeover/ep01/v4/gen/balance.cjs                                 # 提交前精确余额
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py submit MO06             # 10. 一次性提交
node outputs/ai-city-takeover/ep01/v4/gen/balance.cjs                                 # 提交后精确余额
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py poll MO06               # 11. 查询（可重复）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py fetch MO06              #     完成后取回
# 12. 逐镜 Gate 全 PASS 才做下一条
```

主会话手写：`pilot/sd/preview-approval.json`、`pilot/sd/continuity-report.json`、`gen/<unit>/profile.json`、`gen/<unit>/operator-bound.json`。approval 示例：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-seedance-first-frame",
 "question": "<问使用者的原问题>",
 "user_quote": "<使用者原话，逐字>",
 "approved_at": "<UTC ISO 时间>",
 "preview_page": {"path": "<预览页 path>", "sha256": "<sha256>"},
 "preview_artifacts": [
  {"path": "outputs/ai-city-takeover/ep01/v4/board/plates/p011.png", "sha256": "77caea925e5522cb371f1c9abe155ae84fa552781ecd5f9d6412643567d01887", "role": "MO06 first frame"}
 ],
 "prompts": {"MO06": {"text": "<使用者认可的纯中文 prompt>", "sha256": "<sha256>"}},
 "generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "4k", "aspect": "16:9", "audio": null},
 "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": "<单条上限>", "cumulative_CRD": "<总上限>"},
 "identity_waivers": ["IRIS"],
 "identity_waiver_basis": "<首帧承担 IRIS（v4 锚点 F1a）的身份>"
}
```

- `generation` 必须逐字等于 spec：`seconds` 是 clip 秒数向上取整（MO06 4.156 s → 5；SG03 5.991 s → 6）。
- MO06 spec 要求 prompt 里逐字出现：`全身远景`、`她从走秀台远端快步走向镜头`、`镜头固定`、`她走到走秀台中段`、`长焦正面`、`外套肩线一颠一颠`、`前排工程师们一个接一个站起来`。prompt 必须是纯中文：分镜的「T 台」写成「走秀台」。改了措辞先改 spec。
- 分镜写 MO06「40.786 的重音上全场日光灯一排排砰地亮起」，但底片 p011 的灯已经亮着，首帧生视频做不出「亮起」；spec 没写这件事，交导演决定（换底片或把亮灯放进剪辑）。

profile.json 示例（账号、画布与 v3 相同；`node_id` 每条新建，只能是 `node_` 加字母数字；`duration_seconds` = spec 秒数；`benefit_amount` 必须等于 `duration_seconds`——adapter `jimeng_browser.cjs` 在没有输入视频时强制这一条；4k 的 `benefit_type` 是 `seedance_20_pro_4k_output`，取自即梦页面只读配置 `resolutionBenefitKeys.4k`，提交时 adapter 要求页面选中的权益与它逐字相同）：

```json
{"model_id":"seedance_2.0_vip","input_mode":"first_frame","account_sha256":"72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe","project_id":"829df260-5a63-4f0d-8265-8353dc693b3b","node_id":"<node-created.json 的 node_id>","duration_seconds":5,"resolution":"4k","aspect_ratio":"16:9","benefit_amount":5,"benefit_type":"seedance_20_pro_4k_output","credit_upper_bound":"<= approval 单条上限>"}
```

operator-bound.json 示例（`user_quote` 与 approval 逐字相同；两个累计上限等于 approval 的 `budget.generations` / `budget.cumulative_CRD`，lint 会核对）：

```json
{"schema_version": "iris-v4-unit/1", "unit": "MO06", "task": "IRIS EP01 v4 MO06（走秀台长焦正面，首帧，固定机位）; Seedance 2.0 VIP first-frame, 5 s 4k 16:9, no audio",
 "user_quote": "<与 approval.user_quote 逐字相同>", "preview_approval": "outputs/ai-city-takeover/ep01/v4/pilot/sd/preview-approval.json",
 "attempt_id": "iris-mo06-source-001", "policy_id": "iris-mo06-source-001", "reservation_id": "iris-mo06-reservation-001",
 "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": "<单条上限>",
 "ledger": "ledger-sd.json", "cumulative_submit_ceiling": 1, "cumulative_operator_credit_ceiling": "<总上限>",
 "issued_at": "<UTC 现在>", "expires_at": "<issued_at + 3 小时>", "stop_on_unknown": true}
```

## 三、Seedance 2.0 全能参考 / 多模态口型（ESCAPE VELOCITY 做法），以 SG03 为例

做法同 v3 `pilot/sd-r3b/U021`（v3 由同一个 `unit.py` 在 `SD_TRIAL` 下产出）：认可的底片作 `{{image:0}}`，`cut_audio.py` 切的该 clip 人声窗口作 `{{audio:1}}`，短 prompt 说她逐字对嘴。这一条 take 的 approval、连续性报告、ledger 与 unit 文件夹都放 `ep01/v4/pilot/sd-SG03/`，所有命令前加 `SD_TRIAL`。前提同第二节（v4 director coverage）。p012 是闭嘴起始帧（窗口开头有 0.68 s 静音；张嘴版留作 `plates/p012-open.png`），因为 v3 sd-r3b 的 Gate 卡在静音里冻住的张嘴上。

```bash
export SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03
uv run python outputs/ai-city-takeover/ep01/v4/gen/cut_audio.py SG03                   # 0. 人声窗口（预览包前已切好则跳过；同字节可重跑）
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py draft SG03                  # 1. 取 approval 的图、人声、prompt；分镜、底片、锚点、窗口、标记、时长全核对
node outputs/ai-city-takeover/ep01/v4/gen/addnode.cjs $SD_TRIAL/SG03                    # 2. IRIS 画布加一个空视频节点 → sd-SG03/SG03/node-created.json
# 3. 主会话手写 sd-SG03/SG03/profile.json（node_id 取自 node-created.json）与 sd-SG03/SG03/operator-bound.json
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py materialize SG03 --profile $SD_TRIAL/SG03/profile.json   # 4. 建项目 + transport-free prepare（无调用）
uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py show SG03                   # 5. 打印将提交的精确请求（model / mode / 秒数 / 分辨率 / 图与音频绑定 / prompt）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py prepare SG03            # 6. 冻结 prepared.json 与付费预览（上限 = bound 的 operator_ceiling，无调用）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py start SG03              # 7. 建 attempt（无调用）
# 8. continuity-supervisor 出报告 → $SD_TRIAL/continuity-report.json（units.SG03.verdict = "ready"）
uv run python outputs/ai-city-takeover/ep01/v4/gen/lint.py SG03                        # 9. 全部检查通过（含 audio_binding、bound_output）才可提交
node outputs/ai-city-takeover/ep01/v4/gen/balance.cjs                                 # 提交前精确余额
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py submit SG03             # 10. 一次性提交；先写 intent 与 ledger 再提交
node outputs/ai-city-takeover/ep01/v4/gen/balance.cjs                                 # 提交后精确余额 → 如实记账
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py poll SG03               # 11. 查询（可重复）
uv run python outputs/ai-city-takeover/ep01/v4/gen/operator.py fetch SG03              #     完成后取回
# 12. 逐镜 Gate（shot-gate-reviewer，video-analysis MCP）：片段自带音轨与 SG03.wav 对齐量测 + 看口型；全 PASS 才往下
```

主会话手写 `sd-SG03/preview-approval.json`（`unit.py` 只认这个形状）：

```json
{
 "schema": "iris-v4-preview-approval/1",
 "unit_group": "v4-seedance-lipsync-SG03",
 "question": "<问使用者的原问题>",
 "user_quote": "<使用者原话，逐字>",
 "approved_at": "<UTC ISO 时间>",
 "preview_artifacts": [
  {"path": "outputs/ai-city-takeover/ep01/v4/board/plates/p012.png", "sha256": "5c5323ace6605783c58a029b275e67b21523ed6f1f74d63a87f6de4ad5d5f0d2", "role": "SG03 reference image"},
  {"path": "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03.wav", "sha256": "<cut_audio.py 打印的 sha256>", "role": "SG03 vocal"}
 ],
 "prompts": {"SG03": {"text": "<使用者认可的 prompt，含 {{image:0}} 与 {{audio:1}}>", "sha256": "<sha256>"}},
 "generation": {"model": "seedance_2.0_vip", "mode": "multimodal", "seconds": 6, "resolution": "4k", "aspect": "16:9", "audio": "reference_audio"},
 "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": "<单条上限>", "cumulative_CRD": "<总上限>"},
 "identity_waivers": ["IRIS"],
 "identity_waiver_basis": "<这张参考图承担 IRIS（v4 锚点 F1a）的身份，不附身份图>"
}
```

- 标记是即梦原生的 **0 起全局序号**（先图后音频）：图 `{{image:0}}`、人声 `{{audio:1}}`；写成 `{{image:1}}` 会被 draft 拦下。prompt 里只能有这两个标记，各至少出现一次；标记外不得有英文字母。
- 以 `SG03 ` 开头的 role 只能是这两个；多列一个 draft 就 Blocked。人声必须是 `pilot/audio/windows.json` 封存的 SG03 窗口（path、sha、`song_window` = 分镜 clip 窗口 `[44.9422, 50.933]`），16-bit 单声道 WAV，时长在 2 s 到 spec 秒数之间。
- SG03 spec 要求 prompt 里逐字出现：`中景`、`对着他唱歌`、`逐字精确同步`、`她慢慢直起身`、`他还攥着椅子扶手`、`嘴唇轻轻合上`、`唱第一个字时张开嘴`、`一只手撑在他的椅背上`、`他抱着笔记本电脑往后缩`。使用者认可的方法测试原文（`pilot/method/preview-inputs.json` 的 `seedance_multimodal.prompt`，sha `b219295c…`）逐字包含这些，测试核对它能过 draft；定稿措辞再变就先改 spec，不改认可原文。
- 分镜给 SG03 的机位是「锁定中景，48.17 小节线上 4% 推近」：卡小节线的百分比推近按剪辑里的数码推近处理，生成的 take 锁定机位（spec 写的是 `LOCKED`）；导演要在生成里推就改 spec。
- 片段自带音轨（native audio，本 adapter 恒开）跟着参考人声生成，用来量对嘴偏移；成片换成歌曲母带。

profile.json 示例：`input_mode` 写 `multimodal`，`duration_seconds` 6、`benefit_amount` 6，其余同第二节（4k、`seedance_20_pro_4k_output`）。operator-bound.json 同第二节，`unit` / `task` / `attempt_id` 换成 SG03，`preview_approval` 指向 `outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03/preview-approval.json`，`ledger` 写 `ledger.json`（相对 `$SD_TRIAL`）。

离线核对（不联网、不写仓库）：`PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider outputs/ai-city-takeover/ep01/v4/gen/test_unit_lanes.py`（SG03 / MO06 在 tmp 里 draft → materialize → show，coverage 用 `build_coverage.py` 现场生成的副本；另核对 coverage 有效、一 clip 一单元、与仓库文件一致）。

## 四、节选单元（26.05–59.23 s：MO04、SG02、MO05、MO06、SG04、MO07）

使用者认可了节选预览页 `pilot/excerpt/index.html` 与其输入 `pilot/excerpt/preview-inputs.json`（每个单元的模式、秒数、底片 sha、逐字 prompt 与 sha；SG02 / SG04 人声已封存在 `pilot/audio/windows.json`）。`unit.py` 已为这六个单元写好 spec（底片 sha 取自分镜，秒数 = clip 秒数向上取整，造型 L1，机位锁定），每条 spec 要求的字句都逐字取自认可的 prompt；`test_excerpt_approved_prompts_pass_the_prompt_lint` 用认可原文逐条跑 draft → materialize → show（4k）。s009 是 plate3d 镜头，没有 clip，不走这里。

主会话记下使用者的认可后，用下面这条一次写出六份 approval（每个单元一个 `pilot/sd-<UNIT>/`，形状即第二、三节；generation 取自 spec，4k；budget 1 次、0 重试、单条 800、每个文件夹累计 800；`identity_waivers: ["IRIS"]`）。任一输入与页面或 spec 不符、或目标 approval 已存在，一份都不写：

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --question "<问使用者的原问题>" --quote "<使用者原话，逐字>" --approved-at "<UTC ISO 时间>"
```

之后每个单元按第二节（MO..，首帧）或第三节（SG..，`SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-<UNIT>`）逐条走；第二节的 MO 单元同样用 `SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-<UNIT>`，让 approval、报告、ledger 与 unit 文件夹在同一处。

## 五、v4 第一轮：s011 / s012 换 W1 新首帧（MO06、SG03）

使用者重做了人物外形（28 岁成熟、有棱角的脸，面无表情带好奇；相机直闪夜间快照的底片）和造型 W1，并在 `excerpt/flash/v4r1.html` 上认可「s011 选 1，s012 选 1，开拍」。

- **分镜**：`board/plates/p011-w1.png`、`p012-w1.png`（分别与 `excerpt/flash/v4r1/V11a-1.png`、`V12a-1.png` 逐字节相同）成为 s011 / s012 的底片。`shots.json` 的 shot、clip（`start_frame`）、`plates` 条目都已改指新底片，底片提示词取自 `excerpt/flash/v4-round1.md` 的 V11a / V12a（去掉「16:9 横幅画面。」前缀，与 `plates-book.md` 的约定一致）。旧的 `p011.png`、`p012.png` 保留。
- **unit.py**：MO06、SG03 的 spec 改为 W1。必须出现的字句只取自新认可的短 prompt：MO06 是 `低机位`、`她沿着湿的水泥走秀台大步向前走`、`镜头固定`、`两边前排的值班工程师一个接一个站起来`、`从侧前方拍`、`抬起的那只靴子落地`、`重心越过支撑脚`、`长的那只袖子随后摆回`、`面无表情，带着一点好奇看着前方`；SG03 是 `中近景`、`对着值班工程师唱歌`、`逐字精确同步`、`镜头全程锁定`、`一镜到底`、`嘴前没有任何遮挡`。W1 的身份与造型文字逐字取自 `v4-round1.md`（按 sha 锁定），不再沿用分镜里 22 岁的 `fixed_text`；锚点仍是 F1a；没有立领灯线。
- **coverage**：分镜改了，`build_coverage.py` 已重跑。

主会话记下认可后，用下面这条写出两份 approval（`pilot/sd-MO06-w1/`、`pilot/sd-SG03-w1/`；4k；1 次、0 重试；单条上限 MO06 600、SG03 700；已存在就一份都不写）：

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set v4r1 --question "<问使用者的原问题>" --quote "s011 选 1，s012 选 1，开拍" --approved-at "<UTC ISO 时间>"
```

**MO06 换成 V11a-2（p011-w1b）**：场记拦下了 V11a-1（露的是右肩，其他 W1 静图都露左肩），使用者在 `excerpt/flash/shoulder.html` 选「改用 s011-2 (Recommended)」。`board/plates/p011-w1b.png`（= `V11a-2.png`，sha `d262a4ec…`）现在是 s011 / MO06 的底片，`p011-w1.png` 保留；prompt 不变。`--set v4r1` 对 MO06 会拒绝（底片已换），改用 `--set v4r1b`，写到新文件夹 `pilot/sd-MO06-w1b/`（4k、1 次、0 重试、上限 600，并记下它取代的 `pilot/sd-MO06-w1/preview-approval.json` 的 sha；那个文件夹不动）：

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set v4r1b --question "http://127.0.0.1:8769/excerpt/flash/shoulder.html ／ 原认可：outputs/ai-city-takeover/ep01/v4/pilot/sd-MO06-w1/preview-approval.json（「s011 选 1，s012 选 1，开拍」）" --quote "改用 s011-2 (Recommended)" --approved-at "<UTC ISO 时间>"
```

之后各自按第二节（MO06，`SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-MO06-w1b`）或第三节（SG03，`SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03-w1`）走。profile 用 `4k`、`seedance_20_pro_4k_output`、`benefit_amount` = 秒数，`credit_upper_bound` 不超过 approval 的单条上限。

## 六、SG03C：s012 后半句的闭眼唱脸（2026-11-19）

s012 重新设计：前半（44.94–48.17）仍是 SG03；48.17 小节线（beats.json 48.1698）起切进闭眼唱的近脸，到 50.933。分镜里 s012 在 48.1698 处拆成 s012 / s012b，新增 clip `SG03C`（sung，窗口 46.93–50.93，4 s，起点在 tight 46.81 与 I'm 47.517 之间的空隙；plays 48.1698–50.933），底片 `board/plates/p012c-w1.png`（= `excerpt/flash/design/D1-b.png`，提示词取自 `design-frames.md` D1）；SG03 的 plays 改为到 48.1698。`board_audit.py`（`--sung-max 160`，与原合并版同口径）前后都全过，sung 145.5 → 149.5 s，clips 45 → 46。

- 人声已切：`pilot/audio/SG03C.wav`（4.00 s，sha `4b3bb33c…`），封存进 `pilot/audio/windows.json`。
- `unit.py` 的 SG03C spec：W1、多模态、4 s、4k；必须出现的字句只取自 `excerpt/flash/closeup.html` 上的 prompt：`近景`、`她闭着眼睛唱歌`、`逐字精确同步`、`镜头全程锁定`、`一镜到底`、`前排笔记本屏幕的光照着她的脸`、`嘴前没有任何遮挡`。
- 写 approval（`pilot/sd-SG03C/`；4k、1 次、0 重试、上限 400；已存在就不写）：

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set sg03c --question "http://127.0.0.1:8769/excerpt/flash/closeup.html ／ s012 后半句 · 闭眼唱脸（Seedance 2.0 VIP 4k 唱段，4 秒，约 320 积分）" --quote "没有我只是让你自己判断" --approved-at "<UTC ISO 时间>"
```

**底片换成 D2-b（p012c-w1b）**：场记拦下了 D1-b（露右肩、斜挎带方向与已接受的 SG03-w1 相反，接点在一句中间）。主会话按同一授权重做底片：`board/plates/p012c-w1b.png`（= `excerpt/flash/design/D2-b.png`，sha `dca4dab5…`，提示词 D2：露左肩、斜挎带右肩到左胯、卫衣面料、笔记本竖抱几乎合上），`p012c-w1.png` 保留；clip prompt 与人声不变。`--set sg03c` 现在会拒绝（底片已换），改用 `--set sg03c-b`，写到新文件夹 `pilot/sd-SG03C-b/`，并记下它取代的 `pilot/sd-SG03C/preview-approval.json` 的 sha（那个文件夹不动）：

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set sg03c-b --question "http://127.0.0.1:8769/excerpt/flash/closeup.html ／ 底片由 D1-b 换成 D2-b（p012c-w1b）：场记拦下 D1-b 露右肩、斜挎带方向与 SG03-w1 相反；D2 露左肩、斜挎带右肩到左胯，与 SG03-w1 连续；clip prompt 与人声不变" --quote "没有我只是让你自己判断" --approved-at "<UTC ISO 时间>"
```

**再换成 D3-b（p012c-w1c）**：场记又拦下 D2-b（没有黑色高领内搭，与 SG03-w1 不连续）。D3（`excerpt/flash/design-frames.md`）加黑色高领内搭、外套只在左肩滑落、左前臂一截灰长袖、斜挎带右肩到左胯。`board/plates/p012c-w1c.png`（= `design/D3-b.png`，sha `779b1414…`）现在是 s012b / SG03C 的底片，前两张保留；clip prompt 与人声不变。这一次使用者在 `excerpt/flash/closeup2.html` 上与 SG03-w1 的 f12 并排看过，认可「可以，拍 (Recommended)」。`--set sg03c`、`--set sg03c-b` 现在都会拒绝，改用 `--set sg03c-c`，写到新文件夹 `pilot/sd-SG03C-c/`，记下它取代的 `pilot/sd-SG03C-b/preview-approval.json`（那个文件夹不动），并封存 `bound_ids`：

```bash
uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set sg03c-c --question "<主会话问使用者的原问题（closeup2：「闭眼唱脸的首帧改了两次…约 320 积分」），逐字>" --quote "可以，拍 (Recommended)" --approved-at "<UTC ISO 时间>"
```

`pilot/sd-SG03C-c/SG03C/operator-bound.json` 必须写 `"attempt_id": "iris-sg03c-c-source-001", "policy_id": "iris-sg03c-c-source-001", "reservation_id": "iris-sg03c-c-reservation-001"`：`lint.py` 的 `bound_ids_match_approval` 只认 approval 封存的这三个 id；写 approval 时只要任何现有 `pilot/sd-*/*/operator-bound.json` 已用过其中之一就拒绝。之前各文件夹都用 `iris-sg03c-source-001` 这类同名 id，所以这里换掉。

**第三次换底片 D4-a（p012c-w1d），一份认可拍两条**：SG03C-c 生成片逐镜 Gate FAIL（机位环绕、丢了前景工程师、场地与 SG03-w1 不同、开头抢拍、尾部空口型；`pilot/sd-SG03C-c/post-media-gate.json`）。D4-a 是在 SG03-w1 实拍 4K 帧（`design/D4/D4-base.png`）上编辑的：同一停车场、同一机位轴线，左前景同一个工程师；她闭眼、下巴抬起、嘴闭着。`board/plates/p012c-w1d.png` = `design/D4/D4-a.png`（sha `21c5f96a…`；`closeup3.html` 上的 `D4-a-1080.jpg` 就是它的缩图），前几张保留。新 clip prompt 只取自 `closeup3.html`：必须字句是 `近景`、`她闭着眼睛唱歌`、`逐字精确同步`、`镜头固定不动，不推不拉不摇不环绕`、`一镜到底`、`机头直闪`、`左前景的工程师一直在画面里`、`嘴前没有任何遮挡`。

两组 approval 各写一个新文件夹（`sd-SG03C-d1`、`sd-SG03C-d2`），内容相同（4k、4 s、1 次、0 重试、上限 400、`replaces_approval` → `sd-SG03C-c`），`bound_ids` 分别是 `iris-sg03c-d1-*`、`iris-sg03c-d2-*`，`takes` 写明是同一认可下的两条 take（合计 2 次、800）：

```bash
Q='重做的首帧：http://127.0.0.1:8769/excerpt/flash/closeup3.html

这次底图直接用前一镜的实拍画面，往她脸上推近：同一个停车场，同一根柱子，左前景还是同一个工程师。她改成闭眼、下巴抬起、嘴先闭着，为的是避开上次开头抢拍。

生成的 prompt 加了“镜头固定不动、工程师一直在画面里”。同一首帧拍 2 条，挑最好的一条。从 you'"'"'re 前的拍点切进来，唱 you'"'"'re awake。

用哪张？'
for S in sg03c-d1 sg03c-d2; do
  uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set $S --question "$Q" --quote "D4-a，拍 (Recommended)" --approved-at "2026-11-19T15:09:00Z"
done
```

每个文件夹各跑一次 `addnode.cjs`（各自一个新的空节点）；`lint.py` 的 `fresh_canvas_node` 要求 profile 的 `node_id` 等于本文件夹 `node-created.json` 的节点，且不在任何别的 `pilot/sd-*/*/` 里出现过，所以两条 take 不会共用节点。各自的 `operator-bound.json` 写 approval 封存的 `bound_ids`。

之后按第三节走，`SD_TRIAL=outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03C-d1`（再 `-d2`）；profile `duration_seconds` 4、`benefit_amount` 4、`credit_upper_bound` ≤ 400。

## 七、第二轮：SG04（s013）、MO07（s014），各拍两条（2026-11-19）

使用者在 `excerpt/flash/round2.html` 认可「s013 用 b、s014 用 c，拍 (Recommended)」。

- 分镜：`board/plates/p013-w1.png` = `design/R2/S13-b.png`（sha `2f159721…`），`p014-w1.png` = `design/R2/S14-c.png`（sha `db997e4f…`），旧 `p013.png`、`p014.png` 保留；底片提示词取自 `design-frames.md` 的 S13 / S14（去掉前缀）。s013 改成工程师仰视她的反打（手机一直在胸口下方，「把手机扔回他怀里」由剪辑短插完成）；s014 机位改为镜头不动的长焦正面。
- `unit.py`：SG04（W1、multimodal、5 s、人声仍是封存的 `pilot/audio/SG04.wav`）和 MO07（W1、first_frame、5 s）的必须字句只取自 `round2.html` 上的两段 prompt。节选那一套（`--set excerpt`）对 SG04 / MO07 会拒绝；旧的 `pilot/sd-SG04/`、`pilot/sd-MO07/` 不动。
- 四组 approval：`sg04-r2-1`、`sg04-r2-2`、`mo07-r2-1`、`mo07-r2-2` → `pilot/sd-<UNIT>-r2-<n>/`；4k、1 次、0 重试、上限 400；`replaces_approval` → `pilot/sd-<UNIT>/preview-approval.json`；`bound_ids` 为 `iris-<unit>-r2-<n>-*`；`takes` 写明同一认可下的两条 take。

```bash
Q='第二轮首帧：http://127.0.0.1:8769/excerpt/flash/round2.html

- s013（唱 I'"'"'m the call you had to take）：换成工程师抬头看她的仰拍。她站直了，手里拿着刚从他手里抽走的亮屏手机，低头看着他。我推荐 b。
- s014（旋身收尾）：长焦正对 T 台，她在尽头急转身甩开长袖，然后按住寻呼机走开。我推荐 c。

页面上都和前面已认可的镜头并排放着，生成用的 prompt 也在上面。每镜拍 2 条，挑最好的一条。

可以按推荐的拍吗？'
for S in sg04-r2-1 sg04-r2-2 mo07-r2-1 mo07-r2-2; do
  uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set $S --question "$Q" --quote "s013 用 b、s014 用 c，拍 (Recommended)" --approved-at "2026-11-19T17:13:30Z"
done
```

`prep_unit.sh` 的参数（`TRIAL_DIR` 必须指向 r2 文件夹，否则默认落到旧的 `sd-<UNIT>`）：

```bash
TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-SG04-r2-1 bash outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh SG04 5 multimodal 400
TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r2-1 bash outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh MO07 5 first_frame 400
```

（`-r2-2` 同样各跑一次；每次 `addnode.cjs` 为该文件夹建一个新的空节点。）`run_unit.sh` 对 SG04 要带第二个参数 `50.933`（人声窗口在歌里的起点，sync_check 用）；MO07 是动作段，不带。

## 八、斜挎带修正：MO06（s011）、MO07（s014），各拍两条（2026-11-19）

场记查出已接受的 s011 首帧 p011-w1b 和 S14-c 的斜挎带是左肩→右胯，与 W1 定稿（右肩→左胯）相反。以原首帧为底图只改带子方向（`design-frames.md` 的 STRAP）：`board/plates/p011-w1c.png` = `design/STRAP/s011-b.png`（sha `22492025…`），`p014-w1b.png` = `design/STRAP/s014-b.png`（sha `c85aa47e…`），旧底片保留；底片提示词注明「斜挎带右肩→左胯（2026-11-19 修正）」。clip prompt 不变（MO06 用 v4r1 那段，MO07 用 round2 那段）。`v4r1b`、`mo07-r2-1/-2` 现在会拒绝（底片已换），四个 MO07-r2 trial 不动。同时把 s012 / s012b 的切点从 48.1698 改为 49.087（剪辑已用、v4r6 认可的切点；SG03 / SG03C 的 plays 跟着改，生成窗口不变），审计仍全过。

```bash
Q='斜挎带修正后的首帧：http://127.0.0.1:8769/excerpt/flash/strapfix.html

以原首帧为底图，只把带子改成右肩斜到左胯，构图、动作、场地都没动。每镜两张，我放大核对过 b。

生成用的 prompt 都不变：s011 用你上次认可的走台 prompt，s014 用第二轮页面上那段。每镜拍 2 条，挑最好的一条。

用 b 拍吗？'
for S in mo06-s-1 mo06-s-2 mo07-s-1 mo07-s-2; do
  uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py --set $S --question "$Q" --quote "两镜都用 b，拍 (Recommended)" --approved-at "2026-11-19T17:54:00Z"
done
for T in MO06-s-1 MO06-s-2 MO07-s-1 MO07-s-2; do
  TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-$T bash outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh ${T%%-*} 5 first_frame 400
done
```

两个单元都是动作段（first_frame），`run_unit.sh` 不带第二个参数。

## 停止规则

- 任何 units / cut_audio / lint / permit / draft / materialize / prepare 失败或 Blocked：停，报告失败项；不手改产物硬过。
- 分镜 `shots.json`、底片或身份锚点的 sha 变了：draft Blocked；重读后更新 `unit.py` 的 `BOARD_SHA256` / spec 的 `plate_sha256`，不绕过。
- 页面音频时长既不是向下取整也不是向上取整（或读不到）：permit 失败，停，报告页面实际显示。
- permit 或 lint 之后 approval、fill 观察有任何改动：submit 拒绝；permit 只用一次，不重签。
- 价格超过单条上限，或累计次数 / 积分会超过 approval 的 `budget`：停。
- 数字人任一 outcome 不是 `submitted`（含 unknown）：ledger 关账，整个 lane 停；Seedance attempt 出现 `outcome_unknown` / `interrupted`：operator 拒绝，只经 canonical committer 取证恢复。不盲目重试、不重签、不重复提交。
- 即梦入口审核拒绝新脸：停，不做预处理绕过。
- 一条出现冻脸、牙齿碎裂、多出的手或身份漂移：停该 lane，报告，不加 take。
- 一次只做一条：submit → fetch → 逐镜 Gate（全 PASS）→ 下一条；每次提交前后读精确余额，完成后如实报告积分。
