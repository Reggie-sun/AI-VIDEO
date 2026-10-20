---
record_kind: architecture_implementation
topic_id: project-playwright-mcp-install
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Project Playwright MCP Installation

Date: 2026-10-21

## Scope And Installation

用户要求为 AI-VIDEO 安装浏览器 MCP，供后续即梦网页操作使用。
在项目 `.codex/config.toml` 增加 `mcp_servers.playwright`，既有配置语义保持不变。
配置只在受信任的 AI-VIDEO 项目加载；当前 Codex 会话需重载后才能使用新增工具。

- npm package：`@playwright/mcp@0.0.83`，安装于 `/home/reggie/.local/share/ai-video/playwright-mcp`，版本和依赖保存在该目录的 `package.json` / `package-lock.json`。
- Transport：本机 `stdio`，不监听 HTTP 服务端口。
- Browser：系统 `/usr/bin/google-chrome`，使用有界面模式。
- Profile：`/home/reggie/.local/share/ai-video/playwright-mcp/profile`，权限 `0700`，由该项目 MCP 持久保存浏览器登录状态。
- Outputs：`/home/reggie/.local/share/ai-video/playwright-mcp/output`。
- GUI：配置使用当前桌面的 `DISPLAY=:1`、`XAUTHORITY=/run/user/1000/gdm/Xauthority` 与 `XDG_RUNTIME_DIR=/run/user/1000`；桌面会话变化时须重新核验。

## Verification And Evidence

使用已配置的 exact command / args / env，通过 Python MCP SDK 真实执行
`initialize`、`tools/list`、Chrome 页面导航、快照、页面内容读取、tabs 查询与浏览器关闭。

- 安装包 `--version` 返回 `0.0.83`；MCP server 自报 `Playwright`，共 25 个工具，包含上传、点击、填写、导航及快照。
- Chrome 成功访问 `https://jimeng.jianying.com/`，读回标题 `即梦AI - 即刻造梦`、`readyState=complete` 和页面正文。
- 验证结束仅关闭本次 MCP 启动的浏览器；profile 保留。
- TOML 解析及与原配置的语义比较通过；除新增 Playwright block 外，原配置不变。
- `codex mcp get playwright --json` 确认项目注册已启用；documentation contract、agent rules 与 owned-path diff 检查通过。
- 本机 smoke receipt：`.codex/tmp/playwright-mcp-install-smoke.json`，绑定配置与 npm lock SHA-256；该文件位于已忽略目录，不随 Git 发布。
- 本次执行局部安装验证，未运行完整工程 Harness，也不声明完整 Harness PASS。

## Boundaries And Next Use

本次只证明 MCP 安装、协议连接和浏览器读取可用；会员身份与额度尚未核验。
在项目专用浏览器中登录会员账号后，才能验证 references 上传与生成操作。
未提交图片或视频生成、未消费会员生成额度，未修改 Production Manifest / Registry。
即梦 Provider adapter、多模态 references、任务恢复与逐 Shot 媒体验收尚未实施。

Parent Risk Gate：`NATIVE_REVIEW_NOT_REQUIRED`；改动只增加项目 MCP 注册，
不改授权判断、凭据导出、Production writer 或恢复语义，主要运行路径已有真实 smoke。
Learning evaluation：`no_candidate`，单次工具安装不构成独立媒体实验或普遍质量结论。
