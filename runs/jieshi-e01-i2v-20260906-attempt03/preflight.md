# S01 Spatial Hand Repair Preflight

## Scope And Ownership

用户“继续生成测试”授权一次新 S01 Vidu `viduq3-pro` I2V submit；4秒、1080p、24fps、
native audio true，egress 为同一 PNG 和新 prompt 到既有 Vidu origin。新 task ceiling = 1。
前次明确 fetched/Gate FAIL，outcome known；本次不是旧 permit、旧 reservation 或账面余量复用。
只拥有本 attempt03；旧 attempt02 保留。没有 core/runtime/architecture 修改。

Planner/readiness、Router、compiler 仍拥有请求投影；ProductionStateCommitter 仍唯一写入。
bootstrap 复用 exact selected creative artifacts、Registry、原 import receipt 和 PNG，
新空 Manifest 不复制旧生命周期，也不激活旧失败媒体。
唯一变化类别是 authored prompt：靠窗且没有手机的手 = anatomical LEFT；手机手固定；
窗口边框坐标固定，语音只听见不显示。模型、首帧、时长、音频开关均与 attempt02 相同。
同一提示内多个短语改变，不能把差异归因于单一短语，随机生成也不是确定性对照。

## Exact Request

First-frame SHA-256: `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。
941×1672，2,064,319 bytes；注册素材和原许可未重新伪造。
Request: `4fefcd71bc735c6296f28fddd31cdb18c7dd0e127c253afc68e7b4260fd7631d`。
Paid preview: `dad0e4755c2d0230b45c134b20ffe90e253f581ec923ef38fe0a852f47f46e12`。
Profile 与 attempt02 bytes 相同，内部上限 3,000,000 microunits CNY，当前有效至
2026-09-06 08:18:04 UTC；没有重新续期或查询价格。
生成 attempt03、reservation03 和新 authorization；实际 POST 必须校验 exact image bytes。

## Verification And Stop Conditions

Canonical bootstrap/strict reopen、Planner/readiness→I2V、compiler、resolve、paid dry preview 和 AST PASS。
Independent submit review 由原 `reviewer_xhigh` 执行。Exact MP4 落盘后立即调用 project-local
video-analysis；全部 required findings PASS 才可成为下一 Shot 的候选连续性来源。
沿用 attempt02 同一 Gate：左右手、七人倒影、无主角/手影、固定镜头、无烧录字、2cm、
身份工牌、native broadcast timing/wording、native audio质量、最终字幕。不得降低标准。
一个 submit 用尽后停止，unknown outcome 禁止重试；下载恢复只能 GET 同一 canonical result。

Harness inspect 命中新 runs scripts fallback；用户禁止 worktree，因此不运行要求 detached
worktree 的完整 Harness，不声称 fresh passing receipt。真实媒体测试不替代工程验收。
Experience RAG 返回 stale advisory 片段；本次从 exact 当前记录和 source 重核，未前台重建。
