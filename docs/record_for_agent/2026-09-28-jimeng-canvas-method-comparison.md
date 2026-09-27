---
record_kind: research_note
topic_id: jimeng-canvas-method-comparison
learning_eligibility: ineligible
---

# Jimeng Canvas Method Comparison

Date: 2026-09-28

## Purpose And Scope

用户要求解释为什么 Parent 刚生成的广告/剧情测试比其即梦画布差，并明确选择此比较对象。本次是已有素材与制作方法的只读诊断，不授权修图、生成、模型切换或下一轮提交。承接 [first/last retests](2026-09-28-creative-goal-first-last-reference-retests.md)，不改变旧 FAIL/OOM 与 corrected-end 未提交的事实。

画布 `f0ed223b-090e-4ed6-b394-283f8b7dbd07`，标题 `《零号档案》2资产+重置片段`。gstack browse 复用用户实际 Chrome profile 的即梦域登录态后进入；未记录 cookie 值或 signed media URL。Parent 查看总览、四个文字节点、一个完整参考图与代表视频预览；不声称已逐项审查全部素材。

证据根目录：`runs/jimeng-canvas-diagnosis-20260928-001/`，下称 `R/`，为忽略的本地观察产物。节点库存实际为 296：image 172、video 66、group 25、text 24、audio 8、timeline 1；edges 162。检查结束仍为 296 nodes / 162 edges；只进行了选择、预览与 seek，没有编辑内容或点击生成。

## Verified Observations

- `node_9sznptmnrz` 的分镜图模板分别指定人物身份、服装道具、机位构图动作、场景光线四类参考职责；强调每张图只表现一个关键瞬间，不平均混合身份和资产。
- `node_qw4v1w4jnf` 的视频模板分开整段概述、全局拍摄规则、时间轴动作与常见错误，按预备 → 发起 → 接触 → 受力 → 反馈 → 制动/恢复组织动作。
- `node_5d3v7f72da` 概述锁定资产 → 压缩整段逻辑 → 统一拍摄规则 → 按时间执行动作 → 封堵模型错误；`node_5tf55px00d` 的版权文字是用户 authoring policy，不是本次法律判断或项目规则。
- 选择 `node_bq6wajb5xe`（`视频 10 (17)`）后，当前 composer 显示 Seedance 2.5 / 全能参考 / 17s，三张 reference images 与 `COCO声线` 7s reference audio；composer 实际可读文字 6326 characters。文字明确区分宠物 A/B/C/D 的行动职责、COCO 与诺萨的身份、接触点、受力反馈与连续摄影机路线。
- 该节点 generation-history viewer 有 15 results；主预览实测 duration 17.056009 s、1280×720、readyState 4。单个 current composer 与历史主视频不必是同一次 request，且 composer 文字写 15s、当前 duration control 为 17s；不将这个 UI 组合冒充 exact historical submit receipt，也不把 result count 推导成 15 次付费调用。
- 完整参考图可见黑色长外套的高大诺萨、较小机器人、宠物、木质收容处、窗侧自然光与动作接触状态；确认的 8s 视频画面可见这组角色和同类空间。只比较可见资产准备与画面，不签发 identity/continuity PASS。

## Diagnosis And Parent Responsibility

Parent 的上轮实际模式是 H3 fl2va / Vidu q3-pro 首尾两帧，等待态与泵头细节没有作为中间状态输入。生成更多图片与模型实际消费更多参考不是同一能力。画布当前全能参考 composer 展示了按职责组织多张图及声线的另一输入方式，不能将上轮两帧实验称作已经复现用户方法。

最具体且已证实的 authoring defect 是 Parent 初版广告尾帧换了持瓶手，同时 anatomical left/right 与图像冲突；模型即使连续连到那个终态也违背原目标。这个错误发生在 submit 前，不能用模型、参考数量或安全门控解释掉。

动作目标在文本/QA 中被保留不等于已经得到足够的视觉指导。剧情只有开闭状态，未对中间等待态进行模型可消费的约束；实际 API 输出钥匙末态改善，等待触发仍 FAIL。如何改用支持的参考方式或分镜，在不删除完整目标的前提下重新设计，是创作执行工作；增加检查项不能替代它。

画布存在独立角色/场景/分镜资产和多 result 的选择界面，Parent 上轮每 route 只提交一个初始候选，随后 budget 编排错误封死本地 corrected-end repair。不能把一次未充分迭代的候选当作制作水平或模型能力的上限，也不能借此自动扩大已耗尽的任务。

local 广告 416×736 与画布代表预览 1280×720 的画面规格不同；local 剧情 OOM 则没有可比较的成片。模型、内容、尺寸、参考类型与选片过程均不同，无法量化某个因素的贡献或断言 Seedance 对所有任务更强。

## Evidence And Limits

`R/node-inventory.json` SHA-256 `fe6ba7bdcb8932773c11b5a7df1ae8eeb45897c95a13327328eb142cc9069f92`；`R/selected-texts.json` SHA-256 `4477d7081c9aa4ddb6db25984afedec33cc93c76afcc16d97a0f8e0741ee2a2f`；`R/selected-video-ui.json` SHA-256 `780922a204ca5ea0f126b4fea4c074dc517e229f971119c6a8e098693dcd66a9`。这些是 UI captures，不是 immutable Provider execution evidence。

`R/video10-confirmed-preview.png` SHA-256 `4d7bccfb8e693292699e3bece14b9a1603f034c32ced7eea32470b54e9643458`，实际截图播放器显示 0:08 / 0:17。早期按 seek target 命名的三个截图存在 compositor 异步滞后，不能按文件名认定精确时间，排除于 timed findings。没有下载并 hash 原 MP4，没有完整原速观看与实际聆听，不评价整片或全部 generation history。

Mandatory managed Kimi worker invocation `1593bf9b-137a-4f33-9d1b-ff3b938d2267`，seal `99a8fe8346e9a2d96aa59a42637e8ce3b913fa5425456989574957682466a081`，qualified route `27ba7e0c-32b1-41a9-8210-4f49474e0a30`，receipt PARSED；两次 wire requests 均 IDENTITY_VERIFIED、两项 expected Reads complete。其 scope 仅四个文字模板与原实验记录，不曾查看图像或视频。Parent 接受 reference-role / compatibility / method-equivalence findings，拒绝将此当作模型因果证明或未经授权修改画布/Skill 的建议。

## Learning And Publication

`record-ai-video-session` 在只读诊断稳定后执行；`distill-ai-video-learning` outcome `no_candidate`。本轮没有新生成 attempt、隔离变量或 material existing-claim update，UI 预览没有原始 MP4 identity，因此 classification 为 ineligible；不以多节点、多 result 或多个截图凑独立支持，不改变既有 learning claims。

检索使用 experience scope，重开原实验记录作为当前事实；后续针对新发现的全能参考/角色职责查询返回 fresh advisory hits。本次未主动 rebuild index，新记录的检索 freshness 未验证。记录本身无新 Provider/media 调用、Product mutation、push/release；仅 path-limited docs checkpoint，保留 unrelated `.codex/config.toml`。原 capture request `ai-video-record-26b95842b89fe19c` 已 ACKED，不重复 acknowledge。
