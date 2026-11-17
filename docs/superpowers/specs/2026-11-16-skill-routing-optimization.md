# Skill Routing Optimization

## Evidence

2026-11-16 初始 git status clean。当前 blender-artist skills 预载五项、memory-keeper 三项、shot-gate-reviewer 无条件预载 h3-video。h3-video description 将 T2V/I2V/FL2VA 列为触发词。只读 reviewer/researcher 的 tools 包含 Bash；提示词不能强制阻止 shell 写入。mandatory-gate 仅 pull_request。Claude 2.1.325、Codex 0.169.0 已本机核实；官方 Claude subagents 文档说明 skills 全文注入，实际 Token 成本尚未测量。

## Scope

按 P0 → P1 → P2 修改现有 Skill descriptions、角色按需加载与工具最小权限；新增至少 20 条 routing 契约案例和可选 observations 评分、只读环境诊断、轻量 main push CI。共享职责以现有角色文档及薄映射表达，不增加框架或 Skill 正文副本。Product Runtime、Provider、状态 owner、付费与质量 Gate 不变，不调用媒体/付费 API。

## Acceptance

全部原有 Skill 名称及 Claude symlink 保留；Provider 选择必须明确，通用术语不能推断 Provider。Blender 按任务加载，memory 按检索/记录/提炼分开。只读角色不保留任意 Bash，所需执行证据由授权执行 lane 返回；Harness runner 明确是会写本地验证证据的执行角色。新增 tests 必须可重复，静态契约通过不能称真实自动路由通过。真实触发率、Token、速度未实测则 NOT_EVALUATED。focused/related 及发布前 full Harness 用 exact snapshot，报告 receipt 与差距；不弱化原测试。

## Rollback

按本任务 commit 逐项 git revert，保留既有 Skill 实体与接口；不 reset/clean，不恢复或改写 Production 状态。MCP 启动配置保持原样，诊断只报告本地缺失与跨平台风险。
