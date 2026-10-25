---
record_kind: architecture_implementation
topic_id: blender-blockout-skill-installation
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Add scenario-blender-blockout Skill For Video-Model Whitebox

Date: 2026-10-20

## Purpose

记录本次对 AI-VIDEO 项目 Blender skill 链的架构决策：新增 `scenario-blender-blockout` 作为项目主流程（白模参考 → 视频模型渲染）的 blockout / proxy geometry 主导 skill。用户评估起点是"角色 / 有机体建模能力不够"，但通过 `npx skills add --list` 的源仓核对后，本决策基于 description 与项目实际工作流的精准匹配。

## Candidate Skills Considered

四选一评估（`npx skills add scenario-labs/skills --list` + `scenario-blender-expert` persona pipeline 表对照）：

| Skill | 描述核心 | 项目匹配度 | 评估 |
|---|---|---|---|
| `scenario-blender-blockout` | "a Blender blockout whose playblast guides a render-to-real video pass (a video model that takes a reference clip, such as Seedance)" | 精确命中 | **采纳** |
| `scenario-blender-hard-surface` | "modeling hard-surface objects (sci-fi panels, props, weapons, vehicles, robots...)" | 次优 | 延后 |
| `scenario-blender-sculpting` | "sculpt a head, face or bust... block out from primitives... brush moves" | 用户原始痛点对应 | 延后 |
| `scenario-blender-retopology` | "turning a dense sculpt, scan or AI-generated mesh into clean topology" | Provider mesh 收尾场景 | 延后 |

采纳 blockout 的关键理由：

1. description 跟项目定位逐字对齐：`docs/blender-routing.md` 明确 Blender = "白模参考 → 视频模型渲染"，blockout skill 就是为这个用途设计。
2. 项目定位（[docs/blender-routing.md:3](docs/blender-routing.md#L3)）写明 Blender 不替代 Provider / ResolvedTimeline / HyperFrames 最终 renderer；完整 sculpt→retopo→uv→texture 链 over-spec。
3. 用户后续澄清 "headless 和 head 都可以" 拓宽了 channel scope，但未改变项目定位，所以 sculpting 的 brush 优势有限。

## Current Runtime Truth

1. Skill 落地：
   - 实体路径：`.agents/skills/scenario-blender-blockout/`（SKILL.md + `references/` 7 篇 + `scripts/` 主程序 + `scripts/examples/` 5 例）
   - 可见性接缝：`.claude/skills/scenario-blender-blockout -> ../../.agents/skills/scenario-blender-blockout`（symlink）
   - 锁文件：`skills-lock.json` 新增 entry，`computedHash: a40d2b97f8793f66959b2968a01f3283228d2028e6fe35500d771e60f1c61314`

2. `docs/blender-routing.md` skill 链最小补丁：在 `scenario-blender-expert` 之后插入 `scenario-blender-blockout` 分支，其它 chain 项（previs-storyboard / animation / rigging）不动：

   ```
   制作白模时先读 scenario-blender-expert；
   blockout/proxy几何/送视频模型渲染的playblast读 scenario-blender-blockout；
   staging/camera/shots读 scenario-blender-previs-storyboard，
   motion/timing/contact读 scenario-blender-animation，
   确需rig/IK/FK才读 scenario-blender-rigging。
   ```

3. Channel 覆盖：headless Codex 子代理 + GUI human session 双通道；blockout 依赖 `scenario-blender-expert` 的 Verified capability matrix，mesh / voxel / remesh ops headless 可用，brush 仅 GUI（`bx_gui.py`）。

4. 远端状态：commit `d24741f4d676544212518d208be0b6995550017e` 已推到 `origin/main`，local 与 remote SHA 一致。

## Verification And Boundaries

实际执行：
- `npx skills add scenario-labs/skills --skill scenario-blender-blockout --list` 确认源仓存在
- 实际 install 后 `ls .agents/skills/scenario-blender-blockout/` 确认目录结构
- `.claude/skills/scenario-blender-blockout` symlink 验证
- `git show HEAD:.agents/skills/scenario-blender-blockout/SKILL.md` 第 1 行 description 跟源仓 list 完全一致
- `git rev-parse HEAD` 与 `git rev-parse origin/main` SHA 一致
- `docs/blender-routing.md` diff 是单行插入，未触动其它行

未做（属 validation gap）：
- `references/` 7 个文件未逐内容核验（仅目录结构 + 摘要确认）
- `scripts/bx_blockout.py` / `scripts/bx_kits.py` 未在 headless Blender 5.2.1 实际运行（属于未来真实使用时的 validation scope）
- 不构成 skill 已 production-ready 的判定，仅证明 install 正确

## Remaining Risks Or Next Work

### 1. 延后 skill 的再评估触发条件

仅在下列真实失败出现时再考虑 `sculpting` / `hard-surface` / `retopology`：

- `sculpting`：需要 GUI 通道 + 角色有机形体确实是成片瓶颈（用户领域约束不变，不绕过）
- `hard-surface`：hard-surface 道具 / 场景几何白模成为独立失败类别时
- `retopology`：Provider 输出 mesh 收尾出现可重复失败时

延后不等于拒绝 —— 任何新 skill 安装前必须重跑 `npx skills add --list` 看 source-of-truth 生态最新候选。

### 2. 本次 commit 的 bundle 污染（保留为执行教训）

工作树状态机的误解：`git status` 里**大写 `M` = staged**，小写 ` M` = 单纯 dirty。本 session 开局误把 `M  AGENTS.md` / `M  .agent/context/control-plane-playbook.md` 当作普通 dirty work，`git add` 在既有 staged index 上叠加，导致 commit `d24741f` 把 2 个不属于本 task 的文件一并提交：

| 文件 | 改动行 | 实际主题 |
|---|---|---|
| `.agent/context/control-plane-playbook.md` | 14 | Kimi → native reviewer 迁移 |
| `AGENTS.md` | 2 | 同步上述迁移 |

用户对污染处理决定 "不动 (推荐)"，保留远端 `d24741f` 不动。**远端 commit message 主题描述 blockout skill install，但实际改动包括 Kimi→native reviewer 迁移**；如需修正主题可走 GitHub UI amend。

下次执行时必须先 `git diff --staged --name-only` 验证 staged set 仅含 task-owned paths；pre-existing staged work 永不并入本 session commit。

### 3. 遗漏 Co-Authored-By

按 attribution 规则 commit message 末尾应带 `Co-Authored-By: Claude Code <noreply@anthropic.com>`，本次 commit 未带。已 push 且项目禁止 force-push，无法单独修复。下次 commit 必含此行。

### 4. 既存 scenario-blender-* skill 缺 `.claude/skills/` 可见性接缝

`scenario-blender-expert` / `scenario-blender-animation` / `scenario-blender-previs-storyboard` / `scenario-blender-rigging` 在 `.agents/skills/` 实体存在，但 `.claude/skills/` 没有对应 symlink（pre-existing 状态，本 session 不触动）。意味着 Claude Code runtime 自动加载路径不完整，使用这些 skill 需走 routing doc 的 explicit read。本次新增的 `scenario-blender-blockout` 是首个 `.claude/skills/` symlink 同步建立的 blender skill —— 这反而让 routing 的实际效果有差异。如未来决定补齐 symlink，需独立评估后逐个走。

## Agent Guardrails

- **新 skill 评估前先跑 `npx skills add scenario-labs/skills --skill <candidate> --list`**：先用 list 揭示源仓全部候选再问用户。本 session 教训：不跑 list 会把 hard-surface 当唯一 / 最佳推荐，而 blockout 这个 description 与项目主流程逐字对齐的 skill 被错过。
- **commit 前必看 `git diff --staged --name-only`**：验证 staged set 仅含 task-owned paths；工作树大写 `M` 的 pre-existing staged 文件不属于本 task，绝不并入。
- **routing doc 限定 skill 实际用途**：skill 的 description 是上游作者视角的通用描述；本项目实际用途由 `docs/blender-routing.md` 等 routing 文档限定。装上不等于全用。
- **Co-Authored-By 必带**：commit message 末尾必须含 `Co-Authored-By: Claude Code <noreply@anthropic.com>`。
- **记录是 secondary，代码是 source of truth**：本记录描述决策与实施，不替代 `docs/blender-routing.md` / `skills-lock.json` / skill 自带 SKILL.md。后续 Agent 评估时优先看 routing doc + skill 自身。