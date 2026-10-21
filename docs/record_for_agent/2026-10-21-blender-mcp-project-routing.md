---
record_kind: architecture_implementation
topic_id: blender-mcp-project-routing
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Blender MCP Project Routing

Date: 2026-10-21

## Scope And Decision

用户授权按已确定的职责修改MCP配置。`.codex/config.toml` 以同名 `blender` 覆盖本项目配置，保留既有 `blender-mcp==1.8.7`、loopback `127.0.0.1:9876` 及禁用server telemetry设置；不修改全局配置或安装新服务。

项目只暴露 `get_addon_status`、`get_scene_info`、`get_object_info`、`get_viewport_screenshot`、`execute_blender_code`、`disable_telemetry` 六项本地制作工具，startup/tool timeout均为120秒。白模不需要的外部下载、远程3D生成工具不在本项目tool allow list内；这不是对任意Python的网络沙箱，原授权边界仍适用。

既有 `blender-agent-studio` 插件保持启用，按需提供版本、资产检查和证据渲染，不另建重复server entry。白模选择、headless通道和Skill工具适配沿 [Blender routing](../blender-routing.md)。

## Verification And Boundaries

- `codex mcp get blender --json` 已读取project override：六项工具、120秒timeout、原pinned executable及loopback配置一致。工具列表的运行时刷新需重开Codex会话；当前会话已载入的旧工具不能据此声称已热更新。
- 初始没有运行中的Blender实例，9876无监听；这不是MCP包缺失。
- 使用独立Xvfb显示与 `--factory-startup` 启动一次临时Blender GUI，加载已安装addon，不打开用户作品或修改用户preferences。现有MCP实测 `get_addon_status`：protocol `4` 匹配、Blender `5.2.1 LTS`、`telemetry_consent=false`。
- `get_scene_info` 读到factory场景的三个对象；`execute_blender_code` 返回版本及未打开作品的空filepath，并成功创建、删除一个本次专用临时对象。未执行Provider、上传或媒体生成。
- 测试关闭时首次引用脚本局部函数得到明确 `NameError`，没有执行关闭；随后直接注册退出operator，临时进程exit `0`。Blender退出产生临时session recovery，未保存Production资产；没有留下常驻实例。
- Studio `blender_version` 返回exit `0`、Blender `5.2.1 LTS`，build `9e2066aef7ef`。本次未验证asset inspection、evidence render或白模成片质量。
- 工程验证receipt：`.agent/harness/runs/blender-mcp-project-routing-20261021/receipt.json`；以实际receipt状态为准，不把本记录当作Harness PASS。

## Completion Assessment

这是本地工具配置与隔离连接验证，不是用户日常GUI实例已连接、白模生成验收或Production qualification。完成后日常live操作仍须先启动Blender并确认addon监听；纯脚本任务按routing使用headless。

Risk Gate：本地可逆的工具暴露与timeout配置，不修改凭据、Production状态或授权规则，无需独立review，由Parent核对diff与可执行证据。Learning evaluation：`no_candidate`，单次配置验证不提供跨实验质量结论。
