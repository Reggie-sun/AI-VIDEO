---
record_kind: architecture_implementation
topic_id: unrestricted-download-default
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Global Download Default And Provider Transfers

Date: 2026-10-21

## Scope And Authority

用户先澄清下载放行应适用于 Codex 今后跨项目的默认行为，再明确要求删除代码中的下载拦截。
本次同时更新 `/home/reggie/.codex/AGENTS.md` 的全局默认与 AI-VIDEO 下载入口；不是只改即梦临时脚本。
该全局文件是本机配置，不在本仓库 Git 内。项目内下载行为以当前源码和本次验证为准，
不能用一条 Agent 指令声称其他仓库或第三方软件的既有代码已自动修改。

## Download Contract

常规 HTTP(S) 下载不增加域名/IP/端口白名单、固定字节上限或响应 MIME 准入，允许正常 CDN redirect。
Provider 结果下载每跳重建无 API 凭据和 Cookie 的 GET；HTTPS 保留证书/SNI 核验，网络协议错误、HTTP 失败与
重定向环仍按传输错误处理。签名 URL 不进入日志或持久 receipt。

完整响应先传输，再核验长度、实际媒体格式、SHA-256 与任务/引用的精确 identity。
媒体错误保留为错误，不将 HTML 或损坏文件伪装成有效视频；这些下载后核验不产生新生成请求，
也不代替 Shot QA、人工验收或 activation。上传与生成 API 的鉴权、固定 endpoint、
有限 paid count、one-use permit、egress 与 unknown 恢复规则继续由原 owner 执行。

## Owners And Compatibility

- `vidu_download.py` 是共享无凭据下载 owner；Vidu、Grok、MiniMax H3/Hailuo、METASO H3、
  官方 H3 Max、Seedance 结果 GET 与本地视频上传后的 readback 复用该入口。
- 旧版 `ComfyClient` 的两种 artifact GET 也支持 CDN redirect；首次读取仍可使用已选
  ComfyUI API 的原有授权，后续跳转请求重新构造，清除 client auth/cookie/header 和 URL userinfo。
- 各 adapter 删除结果来源白名单、MIME header 与体积提前阻断，仍复核同一 task/file/creation。
  广告素材 reader 也不再按旧下载体积上限拒绝真实 bytes。
- `result_origins`、`result_trust`、`max_download_bytes` 保留旧 profile 序列化身份，
  不再限制下载；新 profile 不需要先发现 CDN。历史请求、profile、receipt 不重写。
- remote materialization 如实记录起始 locator 的 HTTP(S) 协议/origin/hash 与实际 bytes；
  不把起始 URL 的 hash 冒充最终 redirect 地址的 hash。
- 已提供的上传授权、预期源文件的精确 size/hash 与媒体合同仍可在下载后拒绝不匹配内容，
  不将取消固定体积上限理解为可以接受不同的素材。

## Verification And Remaining Boundaries

验证覆盖新 CDN、私网/loopback 地址、非默认端口、HTTP(S)、跨域 redirect 无凭据、
错误或缺失 MIME、超过旧 profile ceiling、完整字节及公共 lifecycle 重开。
统一聚焦命令的 11 个测试文件共 **586 passed**（24.19 秒），包括各 Provider、广告
lifecycle、Seedance readback 与旧版 ComfyClient。额外真实 loopback 测试启动两个 HTTP
服务，完成不同主机名/端口间的 302 跳转并下载 262170 bytes，SHA-256 为
`513ca76f4f5e61f94dfd8ea7933bcabb9cd03602a9981db7cda047a78234d9f2`，没有转发 Cookie 或凭据。
文档契约、owned diff whitespace、全局规则唯一性与相关源码 lint 检查通过。

Parent 判定 `NATIVE_REVIEW_REQUIRED`：新增 CDN redirect 路径涉及凭据隔离和持久化
origin/协议真相，独立审查可核对测试之外的泄露及兼容性路径。exact staged snapshot
Harness、独立审查候选 hash/结论和发布 SHA 由本机汇总
[`.codex/tmp/download-default/receipt.json`](../../.codex/tmp/download-default/receipt.json)
绑定，不用 Markdown 的叙述替代 fresh receipt。

这次修改不发出真实 Provider submit、购买、充值或生成请求。测试使用 fake transport / 本机
fixture，不把工程检查当作所有 CDN 的线上可用性或长期媒体质量证明。

按 `record-ai-video-session` 保存有持久价值的行为变更；`distill-ai-video-learning` 为
`no_candidate`：这是用户明确要求的实现，不是多个独立媒体实验支持的学习结论。
本轮 experience 检索返回 stale last-good 并排队后台刷新；未前台重建索引，检索不拥有授权。
