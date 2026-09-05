---
record_kind: session_summary
topic_id: vidu-credential-live-preflight
learning_eligibility: ineligible
---

# Vidu Credential Live Preflight

Date: 2026-09-05

## Verified Result

用户提供 credential 并要求测试。使用 no-echo stdin 将 credential 写入本机
Secret Service；exact reference 为 `VIDU_API_KEY`，attributes 为
`application=ai-video / provider=vidu / credential=VIDU_API_KEY`。
Raw credential 未写入 repository、command argument、profile、stdout 或此记录。

使用 `HttpxViduTransport` 和 exact injected supplier 对国内站进行只读调用：

- `GET https://api.vidu.cn/ent/v2/credits`：三次 HTTP 200。
- `GET https://api.vidu.cn/ent/v2/tasks?count=1`：HTTP 200；未获得可核验的 result origin。
- 最后余额观察：general `credit_remain=32000`，concurrency limit 5，current concurrency 0。
- 实际响应使用 `remains / general_remains / exclusive_remains`，不能把文档中的
  `remaining_credits` 缺失误判为余额为零；未对重复投影的 general balance 累加。

这些结果证明此轮 credential 可访问国内 API 的账户查询接口，不证明生成模型 entitlement、
submit/poll/fetch、媒体质量、activation 或 P6 / Final Acceptance。

## Stop Before Submit

官方国内价格页本轮 HTTP 200：Q3 Turbo 540p 为每秒 7 积分；公开换算为
1 积分 ¥0.03125。拟测试 1 秒、一次 POST、费用 ceiling ¥1，但没有提交。
当前缺少能够在 Vidu profile 中事先 exact-bind 的可信生成结果 CDN origin。
官方首页展示素材 host 不是该账号生成物 CDN 的证明；未猜测、复制成 allowlist
或在提交后替换 frozen profile。

本轮 generation POST、媒体上传、视频生成、candidate/Manifest mutation 均为零。
Key 已保存不代表 safe live-generation profile 已准备完成。下一步需先取得可信 result-origin
证据并准备真实 Production root、profile 与 exact Paid Provider authorization evidence；
不得复用 test fixture、伪造 permit 或借用历史 Seedance/Hailuo run。

## Sources And Learning

- [国内查询积分接口](https://platform.vidu.cn/docs/search-credits)
- [国内积分消耗表](https://platform.vidu.cn/docs/pricing)
- [国内公开价格换算](https://platform.vidu.cn/pricing)
- `src/ai_video/production/vidu.py` / `vidu_profile.py`。

记录更新了此前 offline-only checkpoint 的 credential/access 边界，未提升其生成验证状态。
`distill-ai-video-learning`：`no_candidate`；只有单次 credential preflight，没有独立生成实验。
