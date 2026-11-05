---
record_kind: recovery_incident
topic_id: suno-native-xdotool-restart
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Suno Native Xdotool Restart

Date: 2026-10-30

## User Direction And Exact Route

用户要求先解决 Suno，改用此前成功的 `xdotool`。本轮实际操作原登录 Chrome 的官方 Suno 页，profile 为 `cp-e7be810d639e`、可见账号 `sunruijie42`；没有用 Patchright/Playwright MCP 填表或点击 Create。CLI 只读曲库/余额，CDP 只读普通表单和 endpoint metadata，不读 credential、cookie、header、response body 或 challenge token。

已重新打开历史 session `01a1748d-b86a-7610-ad87-bcfab8cbc67a`，核对当时成功链确实是 `xdotool` 普通 UI Create 后 CLI status/download；旧窗口 ID 和坐标没有复用。当时为 instrumental v6 且未出现实际人工验证，不证明当前歌曲或平台状态相同。

## Native Preflight And Single Click

通过 X11 `_NET_CLIENT_LIST` / `WM_CLASS` 找到本轮窗口 `205520910`，置前后重验 active window。使用明确的 `DISPLAY=:1` 与 `XAUTHORITY=/run/user/1000/gdm/Xauthority`，没有读取进程环境或复制浏览器凭据。窗口移至主屏，调整为 1920×1080、页面 67%，原几何信息保存在 intent。其他 Chrome profile 未用于歌曲生成。

歌詞与 style 经原生剪贴板回读一致；四个字段最终均以只读 DOM 对照原 `suno-ui-intent.json` 的 exact values/hash，标题、exclude、v6、Female、0:30、账号和 enabled Create 均核对。原生鼠标悬停后只读 DOM 确认命中 `Create song`。没有改写已认可歌词或音乐方向。

依用户本次明确的原生 UI 操作要求封存一个有限单元，`max_create_clicks=1`、`automatic_retries=0`、operator ceiling 20 credits，原上限及旧未决历史保留；没有把旧未知结果改判为 `KNOWN_NO_EFFECT`、回放旧 CLI UUID 或重用旧 consume。2026-10-31 01:08:40 UTC 在 fsync 本轮 `consume.json` 后，`xdotool click 1` 实际执行一次，退出 0。

## Actual Platform Result

Create 后的实际画面出现 Cloudflare “Verify you are human”，Create 进入等待状态；只读网络观察见 challenge 请求/回应，12 秒窗口内没有观察到歌曲生成 POST。该有界观察不证明旧请求未提交，也不证明歌曲生成成功或确定零费用。

随后只读截图显示进入图片验证阶段。Agent 没有点击验证控件、识别/选择答案、调用 solver 或取出 token；已将官方窗口留在前台并通过结构化消息请求用户手动完成。只等待这一轮结果，不再点击 Create。

当前只读曲库仍为六首旧歌、无新 clip，余额为 2470（相对本轮前读回未变，结算/生成结果仍未确认）。`suno agent-info --command download` 的只读命令发现已完成；实际歌曲 ID 出现后才能下载，不以旧作品 ID 代替。

## Evidence And Boundaries

相对目录：`outputs/ai-city-takeover/ep01/audio/suno-xdotool-restart-20261030/`。

- `intent.json`：本轮用户指令、原 preview anchor、字段 hashes、窗口/次数/上限和旧未知状态。
- `preflight.json`：四字段一致、账号/模型/性别/时长、enabled Create 和真实 hover 检查。
- `consume.json`、`click-result.json`：本轮单次原生点击与时间，不等于 provider submit receipt。
- `network-metadata.json`：仅 host、method/path/status/time；query、headers、body、token 及可变 challenge path 已省略。
- `after-create.png`、`current-challenge.png`：实际 Cloudflare 与后续图片验证画面；不裁决或解答验证。
- `challenge-readback.json`：真实曲库/余额读回与 `NOT_CONFIRMED`，不宣称生成、扣费结算或 Production 状态变化。

本轮没有新工程实现、媒体生成成功证明、正式歌曲 asset、render、对嘴或 Production 激活。原 staged 工作保持；因平台人工验证与成片验收未完成，未 commit/push。后续只读取本轮结果或确切新 clip，不能把换控制方法等同于清除未知或自动再次提交。

## Learning Assessment

按 `record-ai-video-session` 记录该真实阻塞，并自动评估 `distill-ai-video-learning` 为 `no_candidate`。本次只证明该账号/页面在这次原生点击后仍要求人工验证，不能推出驱动、账户、IP 或平台风控的因果规则；没有修改 Skill、Policy 或 Gate。
