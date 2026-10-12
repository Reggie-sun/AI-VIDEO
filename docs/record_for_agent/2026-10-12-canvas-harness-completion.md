---
record_kind: architecture_implementation
topic_id: reusable-canvas-production-harness-completion
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Canvas Production Harness Completion Record

Date: 2026-10-12

## Purpose

本轮沿既有 CanvasProductionService、sequence continuity、Production/Registry/Manifest/committer、
Dependency Graph、ResolvedTimeline 和 HyperFrames 完成工程接线。Native Codex 为唯一 writer，
本轮没有新增付费视频生成，历史 Seedance 7/7 未重置；没有创建 dedicated development worktree。
工程控制流与真实声画验收分别报告，AC-7 保持 NOT_EVALUATED。

## Current Runtime Truth

入口为 `scripts/canvas_production.py` / `open_canvas_project` / `CanvasProductionService`。
操作、数据字段和两份 development 示例见 [Harness guide](../canvas-production-harness.md)。
同一 CLI 支持 Inspect → Author → Prepare → Execute → Handoff → Compose → Deliver。
执行所需 qualified operator runtime 注入一次，承接既有 Provider、private suppliers、budget、
MCP evaluator 和 HyperFrames；本轮的 fixture runtime 不构成实际运行环境资格。

原文、原 chip/tray、主体主/辅图、原版本指针及重复 occurrence 保留；技术图号适配展示 diff。
历史 URI/history-material 图片沿原 source owners 导入，显式选本地 PNG，入口计算内部 hash/receipt；
不虚构图节点/连线，不自动下载或宣称平台采用。复刻拒绝 Director 对原文、对白或动作的扩写。
输入以 immutable authoring evidence 保存，canonical reader/bootstrap 验证 bytes，resume 不重写已批准数据。

生成顺序沿 Storyboard/sequence owner，剪辑顺序投影到 CompositionSpec；插入镜头与有意换场
不被强制改成上一尾帧。普通中间状态必须先有 approved state_reference 计划，再读取真正 accepted
前序 MP4、实测截帧、核验 derivation、调用 MCP 并保存所选状态 evidence。
后镜自身的 selected QA inventory 和 canonical generation findings 必须覆盖同一组所需检查并全 PASS；
前镜状态 match 不代替后镜验收。缺计划/缺证/陈旧/FAIL 均停止。

原生 WAV 绑定当前接受 request，source trim 沿唯一 ResolvedTimeline 的 frame/sample mapping；
同视频 bytes 的不同 request 音频不能串用。实际采用帧数沿 content_driven duration owner，
普通 nominal_seconds 不强求360帧，显式 fixed/frame_count 精确契约不放宽。
HyperFrames 仍为 renderer，最终声轨沿 canonical mixer；剪辑接点 P6 与用户完整1.0x听看沿原 owner。

## Ownership And Publication

用户 A 交接 canvas_production 与整组 recovery/files/tests，保留并整合前序修改。
其他旧 spec/plan/baseline/record 的未提交修改未纳入本轮，不以旧 AccountOverdueError 作为当前阻塞。
旧文件存在 ownership 限制，不能声称 supersession notices 已完整回填；本记录提供当前证据边界。
代码提交 `601b4f7a0de09e4173a328a17c5b5e0e70977fb4` 已推送 `origin/main`，本轮核对远端 SHA 与本地一致。
提交 tree `6eb88bbcbb8409fd0a02d2feb7d7e31f88d143fb` 与最终 reviewed/staged candidate 一致。
publication receipt：`runs/canvas-harness-completion-20261012/code-publication.json`。
本记录独立走 documentation snapshot 验证并提交；不改变已审源码、规则或故事数据。

## Verification And Review

Final exact staged Harness：`.agent/harness/runs/canvas-production-final6-20261012/receipt.json`。
`status=passed`，24 selected checks（23执行通过、1被同轮通过项覆盖的 skip），
`workspace_stable=true`、cleanup passed；completion 前再次 `make harness-receipt`，
artifact integrity、fresh snapshot、coverage、policy 与 complete completion proof 全 true。
完整 receipt 文件 SHA-256 为 `9224fc635d37e651eb0da4e50646bfc0dde6323a22c51f04180765b8d2b0f62b`。
Architecture Gate 通过，未刷新 baseline；现存大模块 warning 不视作新行为回归。
测试有重叠选择，不把各 check 的 test 数相加成独立案例数量。

冻结 candidate6 tree `6eb88bbcbb8409fd0a02d2feb7d7e31f88d143fb`，46 owned paths；
`runs/canvas-harness-completion-20261012/freeze-candidate6.json` 保存 source hashes。
聚焦验证 38 PASS，覆盖源导入、URI、连续性交接、8个安全诊断案例和未声明计划的零效应阻断。
此前 red evidence：8个诊断案例缺 locator；未声明交接在真实 canonical accepted-source seam 上未抛错。
修复后才冻结。原有 replay/unknown/canonical graph 局部失效与 native audio/trim/P6 检查纳入完整 Harness。

受管 Kimi mapping 与 implementation review 是不同 proof。review round1 的错 hash/未读行引用
返回 EVIDENCE_INCOMPLETE，原输出隔离，未修补或采用报告。round2 机械校验 PARSED，Parent 将
unplanned handoff 问题提升为阻断并复现/修复；帧率疑点由现有 visual_media equality guard 排除。
可选 walker 重复校验和额外3个负向测试无已证实行为缺陷，本轮不扩大 paid recovery 修改。
review round3 已绑定最终 candidate6、新 Harness 和 Parent resolution，终态 PARSED；
invocation `f65b2160-bbfc-4273-bb35-6b3e89a61cdb`，qualified Docker / Kimi deep，8次 authenticated k3/max响应，
26次实际 Read，970.724秒，输出未截断。Parent 再核验37条 report refs 的
exact hash 和本次实际 Read 行范围、artifacts、46源文件冻结值，均一致。
Parent 逐项裁决 C6R3-01至09 与两个 questions，无 unresolved blocker 或 NEEDS_MORE_EVIDENCE。
已修复问题闭合；generic error 未来 hardening 与两条额外 recovery negatives 为非阻断建议，
没有已证实的当前 bypass，不为额外建议改动 frozen bytes。
三个原 live review rounds 已消费（首轮失败保留），没有第四轮、预算重置或叠加 native reviewer。

| Review proof | Local receipt |
| --- | --- |
| Round3 exact worker report | `runs/canvas-harness-completion-20261012/review-round3-report.json` |
| Route / process / actual Read receipt | `runs/canvas-harness-completion-20261012/review-round3-receipt.json` |
| Parent adjudication / closure | `runs/canvas-harness-completion-20261012/review-round3-parent-adjudication.json` |
| Round2 confirmed-gap resolution | `runs/canvas-harness-completion-20261012/review-candidate6-resolution.json` |

review 与 Harness 只支持工程 publication decision，均不代签媒体接受或用户验收。

## Independent Holdout Data Proof

两份真实画布在候选5冻结后读取，未用于共享代码设计；候选6的交接/诊断修复来自独立审查与通用负例，
没有使用这两份故事驱动修改。再次冻结后只换数据，在同一入口复核。
精确结果：`runs/canvas-harness-completion-20261012/holdout-results-candidate6.json`，
receipt SHA-256 `2acd707ce5bed029b818b295ef25f482007cc4548457c7078c5f4957cc22244f`。
receipt 绑定实际 canvas ID、source file SHA、canonical snapshot SHA 与 ordinary-data SHA，
同时记录 first-read freeze5 与再验证 freeze6，不把已读画布重新宣称为首次盲测。

| Holdout | Canvas ID | Selected unit | Data result |
| --- | --- | --- | --- |
| 益达竞速嘉年华 | a18a9ce2-b4a9-41fe-863c-f71255612e6a | 下车4秒→加油对话15秒→餐厅15秒→看信7秒；4镜、9素材 | CLI author、完整选定数据导入、immutable resume、首镜 real compiler Prepare PASS |
| 班尼打工日记 | 35af46ab-e902-4d1f-9a02-795b96a6e747 | 回家5秒→电脑画面4秒；2镜、3素材 | 同一入口与同类操作 PASS |

两份 production root bytes 均未改变，video generation attempts 0、Provider effects 0；
唯一已有 Manifest attempt 是 dependency bootstrap。transport/credential/input-reference suppliers
显式 forbidden。QA 为离线 fixture，非真实 operator/Production qualification。
后镜 Prepare 尚未执行，必须先生成并接受前镜；两份没有真实 composition/完整听看。
益达原始开场节点仍缺3个原 node references，保持 BLOCKED；本次只选有素材的完整小单元，不删除缺口。

《机魂觉醒》、花园、零号档案、《逆行之舟》均为 development，不能计作 holdout。
逆行之舟暴露 URI 导入缺口，已沿共用 source owners 修复并作为 development 验证。
原机魂的修剪、中间状态参考、驾驶员插入镜头和推进太空的接续获用户确认；
此反馈不转移到新7→2两段，新两段连续性仍未验收。

## Acceptance Criteria

| AC | State | Evidence and limits |
| --- | --- | --- |
| AC-1 | PASS — engineering | 原 prompt/引用职责/主辅图/版本/重复 occurrence 和必要 native slot diff；URI 进口负例与忠实表达测试。未支持及缺失引用单列。 |
| AC-2 | PASS — data-level reuse | 冻结后益达4镜、班尼2镜只换项目数据，走同一 CLI author/resume/首镜 pure compiler Prepare。后镜、真实执行与完整成片尚未验证。 |
| AC-3 | PASS — offline canonical integration | 真实 canonical accepted-source seam 的直接承接、中间状态、有意换场、插入剪辑关系；错序/陈旧/缺证/非法释放停止。真实模型连续性质量 NOT_EVALUATED。 |
| AC-4 | PASS — offline control flow | 共用阶段入口覆盖 execute、handoff、native audio/trim、composition、HyperFrames/P6/deliver；scripted Provider 与合成媒体不算实拍。 |
| AC-5 | PASS — offline | exact replay 不重复 submit；unknown 不 retry；canonical graph 定位单个输入变更影响，未相关项及历史 bytes 保留。 |
| AC-6 | PASS — engineering | 素材/选用/来源冲突/原对白变化定位到 occurrence 与 field，安全错误不回显 raw input；故障限相应单元。 |
| AC-7 | NOT_EVALUATED | 没有本 Harness 真实完整声画交付与用户完整正常速度听看认可。 |

## Minimum Future Live Validation

本轮不执行。最小连续性单元为2个确有状态承接要求的新镜头：先镜 exact MP4 逐项接受，
选择实际所需状态/参考（可为中间状态），绑定后镜，生成后镜并逐项接受，再核对真实 trim 与接点。
有意换场不被强制使用尾帧；插入镜头的剪辑关系另沿原 canvas 意图核对。

至少还缺：当前明确 paid/remote 授权、保留7次历史消费的新有限2次 submit 单元与预算/上限、
当前 qualified runtime 和 exact previews、实际逐镜 MCP/声音/状态 findings、接点证据和用户正常速度听看。
首镜 FAIL/NOT_EVALUATED 即停；unknown 停止，不续传旧任务、remint 或自动重试。
AC-7 可选益达上述完整4镜单元（41秒为 nominal 提示）或班尼完整2镜单元（9秒 nominal），
需逐镜生成/验收、真实音轨、HyperFrames exact 成片及用户完整听看；工程 proof 不代签。

## Evidence Availability

完整 Harness 与 review/holdout/publication receipts 保留在本 workspace 的上述路径，
`runs/` 与 Harness generated artifacts 按 repository 规则不作为 source commit；本记录、
可复用入口、示例和说明已进入 owned publication。私有 credential 内容不进入记录，未知 Agent/API
实际费用不估成账单。历史旧 spec 的 AccountOverdueError 仅为旧证据，本轮没有查询当前账号状态。

## Learning Evaluation

`no_candidate`。本记录是工程与离线控制流证据，没有新独立媒体实验或受控模型比较，
不产生模型通则、placeholder Learning Claim，也不通过学习流程改变 Skill/Policy/Gate。
没有单独刷新 RAG index。
