---
record_kind: recovery_incident
topic_id: omx-native-hook-image-stdin
learning_eligibility: ineligible
---

# OMX Native Hook Image Stdin Repair

## Result

用户在《失帧》参考审看中遇到 `native_hook_stdin_oversized`，要求先修复。当前已安装 OMX `0.21.38` 的 native stdin 与 plugin wrapper 上限从 1 MiB 同步提高到 32 MiB；没有关闭 Hook、修改注册命令或改变超限拒绝语义。修复已作用于当前全局安装。MC00 参考制作在修复期间暂停，未新生成图片或视频。

这是当前 npm 安装的本地补丁，不是上游已发布修复。升级／重装可能覆盖；[hotfix.patch](evidence/omx-native-hook-stdin-20261028/hotfix.patch) 保存八个文件的精确差异，[verification.json](evidence/omx-native-hook-stdin-20261028/verification.json) 保存原／新 SHA、实际安装路径和测试范围。原件另存 `/home/reggie/.local/share/ai-video/omx-hotfixes/native-stdin-20261028/original/`。没有修改 AI-VIDEO 产品源码、媒体 Gate、其他用户的 dirty/staged 文件。

## Cause And Scope

实际 `/home/reggie/.codex/hooks.json` 直接执行全局安装的 `dist/scripts/codex-native-hook.js`。该入口在 JSON.parse 前通过 `MAX_NATIVE_STDIN_JSON_BYTES` 限制 stdin。另一个 plugin launcher 有独立 `MAX_WRAPPER_STDIN_BYTES`，本次同步二者及诊断／测试夹具，避免入口不同导致旧限制复现。

刚才审看的四张 PNG 总计 12,807,552 字节；使用它们原始 bytes 构造同类 PostToolUse base64 JSON 为 17,077,084 字节。修复前复现原错误，修复后进入正常 dispatch。没有保存 base64、原始会话或凭据。此输入是可归因的同类复现，不宣称已捕获原先被宿主拒绝的完整事件。

仍保留 bounded read、持续 drain、畸形 JSON 拒绝、PreToolUse 超限 deny、PostToolUse 超限停止以及 Stop 的当前 session/workflow 裁决。argv 的 64 KiB、raw event scan 的 64 KiB、plugin stdout 的 1 MiB 均未改变。输入内存峰值仍高于单份 32 MiB，因为有 concat、UTF-8 和 JSON 解析开销；本次没有引入无限缓冲或截断后放行。

## Verification

- [before.json](evidence/omx-native-hook-stdin-20261028/before.json)：实际图片字节复现失败及原 1 MiB 诊断。
- [after.json](evidence/omx-native-hook-stdin-20261028/after.json)：九项全部通过，包括实际四图输入、Pre/PostToolUse 的 32 MiB−1／32 MiB／32 MiB+1 UTF-8 边界、小输入和超过旧限制的畸形 JSON。
- [native-targeted.tap](evidence/omx-native-hook-stdin-20261028/native-targeted.tap)：原生 Hook／protocol 的 oversized、byte-limit、malformed、drain 定向测试 25 通过。
- [plugin-targeted.tap](evidence/omx-native-hook-stdin-20261028/plugin-targeted.tap)：plugin 对应边界、owned routing/delegation、超限不委派、Stop 与 SubagentStop 等 15 通过。
- [native-protocol.tap](evidence/omx-native-hook-stdin-20261028/native-protocol.tap)：完整 native protocol 文件 21 通过。
- 修改的 JavaScript 与复现脚本经 `node --check`。独立原生 `code-reviewer` 审查无阻断问题。
- 使用现有 4,098,545 字节市政 PNG 再次实际调用 `view_image` 并返回图片；没有新生成媒体。未取得宿主 Hook callback 的独立 readback，保留 `NOT_EVALUATED`，不把 CLI 测试代称宿主端到端验收。
- 安装包仅包含部分 TypeScript 源码，没有运行会删除 dist 的全量 build、完整 OMX 测试或 packed-install 实际安装；本次为精准验证，不宣称全仓通过。

一次 Harness 临时索引隔离尝试未被 Harness 采纳，实际选中了原有的其他任务 staged 文件，并在旧 `ai-video-p2` 环境因缺少 numpy 收集失败。该 receipt（`omx-native-hook-stdin-20261028`）不属于本任务 owned scope，不用作本修复的通过／失败依据；owned 文档校验与上述实际 Node 回归分别取证，提交后使用 exact commit range 核验归档范围。

复现命令（在 AI-VIDEO 根目录）：

```bash
node docs/record_for_agent/evidence/omx-native-hook-stdin-20261028/check_stdin.mjs \
  /home/reggie/.nvm/versions/node/v22.21.0/lib/node_modules/oh-my-codex \
  /tmp/omx-native-hook-stdin-check.json
```

补丁已通过当前安装的 reverse dry-run；应用到另一份安装前须核对版本、原始 SHA 并先 dry-run，不自动覆盖不同版本或他人的修改。

## Learning Evaluation

已按 `record-ai-video-session` 记录并评估 `distill-ai-video-learning`：`no_candidate`。这是单个安装问题的有界修复，没有足够跨实验依据形成通用媒体生产规则；不修改 Skill／Policy／Gate，也不写入全局 memory。

## Remaining Work

MC00 改用城市位置总图与连贯写实参考；完整城市白模停止。原白模 `FAIL`、旧楼梯 `FAIL`、正式视频未提交及原速声画／接点验收缺口保持，Hook 修复不改变这些状态。
