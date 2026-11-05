# Patchright MCP Browser Connection

本接线供普通浏览器操作使用，通过现有 Chrome 的 CDP 连接复用登录状态。它不拥有 Production state、歌曲提交预算或媒体验收，也不求解、读取或导出验证码 token。

## Runtime

独立依赖目录为 `/home/reggie/.local/share/ai-video/patchright-mcp`：

```bash
npm install --prefix /home/reggie/.local/share/ai-video/patchright-mcp --save-exact patchright@1.64.2 @modelcontextprotocol/sdk@1.32.2 --ignore-scripts --no-audit --no-fund
```

Node 需至少 20；本机已验证 Node 22.21.0。当前已有 Chrome，因此本接线不下载或启动另一份浏览器。依赖版本由该目录的 `package.json` 和 `package-lock.json` 固定；没有替换现有 Playwright 或 Jimeng runtime。

## Connection

入口是 `scripts/patchright_mcp.cjs`。它使用 Patchright 的 `chromium.connectOverCDP()`，再将实际 `BrowserContext` 交给现有 `@playwright/mcp` 的公开 `createConnection(config, contextGetter)`。

项目 `.mcp.json` 和 `.codex/config.toml` 新增独立的 `patchright` server，保留原 `playwright` server。显示环境为用户指定的 `DISPLAY=:1`、`XAUTHORITY=/run/user/1000/gdm/Xauthority`、`XDG_RUNTIME_DIR=/run/user/1000`。

`--profile-dir` 只读取 `DevToolsActivePort` 的本地端口，不读取 cookie、认证文件或存储内容。每次浏览器操作前仍需确认可见账号。连接失败保持失败，不新建浏览器、不复制登录资料、不切换账号。

MCP 标准工具可用后，普通表单填写与一次 Create 仍须匹配当次授权、准确预览和持久化单次 intent。验证码由用户在官方窗口完成；安装 Patchright 不代表平台验证已免除。

## Verified Boundary

2026-10-30 已实际验证 Patchright 原生账号读取及 MCP `browser_tabs`、`browser_snapshot`、`browser_evaluate`、表单填写与一次按钮操作。MCP 连接退出后原 Chrome 与 Suno 标签仍在。

证据位于 `outputs/ai-city-takeover/ep01/audio/patchright-integration-validation.json`。本次 Create 后的实际截图是 Cloudflare “Verify you are human”，所以歌曲生成状态仍为 `NOT_CONFIRMED`；浏览器接通不代替音乐成功。

初始化错误报告阶段及安全的本地原因，第三方错误不回显带查询参数的 URL。回滚时只移除新增 `patchright` 配置并停止其连接；原 server 与浏览器保持原状。配置原文备份在隔离 runtime 的 `config-backups/`，不进入 Git。

## Sources

- [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [Patchright Node package](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-nodejs)
- [Playwright MCP public context interface](https://github.com/microsoft/playwright-mcp/blob/main/index.d.ts)
