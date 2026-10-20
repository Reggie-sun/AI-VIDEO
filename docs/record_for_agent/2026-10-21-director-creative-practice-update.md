---
record_kind: session_summary
topic_id: director-creative-practice-update
learning_eligibility: ineligible
---

# Director Creative Practice Update

Date: 2026-10-21

## Scope And Authority

用户在[Director研究](2026-10-21-director-capability-study.md)交付后明确要求“修改”。本轮直接修改现有Director advisory owner `.agents/skills/open-video/`，不把该请求视作新生成、付费调用或Production提交授权。此前研究的只读范围保持为该轮历史事实，本轮才实施Skill变更。

唯一writer为Parent，拥有`SKILL.md`、`references/creative-completion.md`及本记录；其余共享dirty文件保持原状。采用`skill-creator`完成现有Skill的局部更新，未创建第二导演流程、schema、评分器或新Gate，未改产品源码、Policy、Manifest、Registry或历史QA。

## Changed Practice

- 从观众体验选择表达机制；在存在实质分歧时比较不同创意，而非把焦段形容词当成新方案。
- 以人物任务、反馈和选择指导表演；保留静止、克制、无明显冲突、单镜和感官表达的适用空间。
- 用相称的取景、空间图或简易排演核对目标、替代选择、路径及参考职责；不默认白模或更长Prompt能保证执行。
- 由注意力和行动/反应时机安排镜头、剪辑与声音；不以切镜数、动作幅度或固定结构代替判断。
- 核对coverage到Canvas / Shot，再到typed intent或preserved source和actual native的语义；核心动作缺失时回到实际owner修复。
- 以输入、参考和输出区分设计、交接、生成、制作及证据缺口，允许多因共存，保留原目标和已满足项。
- 澄清上游自动planner/judge/stitcher并非本项目已安装Director runtime；H3示例只在选定H3后的authoring范围参考。

护腰贴只作已知交接/参考风险反例，未把研究中的7秒方案、纸卷走位或纸面比较升级为已验证配方。外部方法保留作者、冻结来源及许可归属，不照搬作者数量规定或模型成功率经验。

## Verification

Skill frontmatter/scaffold检查通过；两个Skill文件的本地链接与本次新增anchors均可解析；`git diff --check`通过。

相关现有测试`test_open_video_skill.py`、`test_seedance_authoring_skill.py`、`test_runtime_skill_boundary.py`共58项通过。未新增匹配文字措辞的测试；这些测试不证明导演审美或实际影片质量。

### Independent Text Trial

首次使用native `reviewer_high`，task `director_skill_forward_trial`，但该profile明确限制为findings-only，不能交付创作设计；它的空findings不计作四案试用完成。随后使用fresh-context native `conceptual_planning_agent`，task `director_skill_creative_trial`，只读试用修改后的Skill；禁止nested delegation、写文件、生成和付费调用。给它未附预期答案的四项请求：桌面灯生活广告、固定批准目标的《界蚀》诊断、固定机位陶杯感官片、走廊门行动与音效的混合失败诊断。未提供研究结论、旧review结果或本记录。

第二个context实际返回四案的具体答复，Parent逐案核对：

| Case | Observable answer / assessment |
| --- | --- |
| 桌面灯广告 | 设计“等一个句号”的室友约定，以伸向开关、推近未完纸页、等待、补句号、手动关灯串起互动；未添加自动感应/调光/护眼功能。仅证明给出了具体商业情境，未证明趣味或商品记忆效果 |
| 《界蚀》 | 保留3秒、本人/空位同框、七人、左手与广播；分别查raw与合成里的额外手影，并核对反射位置/注意关系，没有通过删人或改剧情避险 |
| 陶杯 | 采用固定机位，以窗光、画外水流、水位与水声变化、涟漪安定组织8秒；未强加人物冲突、切镜或CTA，明确需原速带声观看 |
| 门与音效 | 将coverage→authoring/native动作丢失、门被遮挡、raw遵从弱输入、合成脚步声提前分开；未无据指认Compiler或模型拒绝动作，提出对应owner修复 |

Parent未发现需据此修改Skill的语义blocker。试用者明确把四案视作文字设计/诊断，未创建coverage、goal binding或正式authoring artifacts；未选择模型，未套用H3语法。完整制作前的既有合同检查不因这次纸面范围免除。

所试Skill候选SHA-256：`SKILL.md`为`83e1c114d86f6eb723c7109878cb3b06012092184c2611185ddbb4fb30d594af`；`creative-completion.md`为`ad1efaaf43d7a9ecdc820370071f15299f47b73f52e43fa7f598ed07d58e8dff`。这是一次含四题的文本试用，不是四个独立媒体实验，未观看新片、未进行受众实验或Production验收。

## Completion Boundary

Parent Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`：局部可回滚的advisory文档更新，不改变执行权限、持久化或验收标准；独立文本试用用于检查创作灵活性，不冒充代码审查或实际媒体质量证明。

最终exact staged snapshot按policy运行Harness，receipt为`.agent/harness/runs/director-creative-practice-20261021-r1/receipt.json`；实际结果与Git publication在本次交付另报。仅提交上述三个owned paths。

`record-ai-video-session`以本文件记录用户授权的Skill实施，研究报告保持其原证据范围。`distill-ai-video-learning`: `no_candidate`；没有新的受控媒体改善或跨实验效果证据，不创建Learning Claim或`ADOPTED`声明。直接用户修改请求不经自动学习产生授权。

剩余限制是实际成片的因果可读性、自然表演、节奏、商品关联和吸引力尚需相称媒体与观看证据。Skill更新提供判断方法，不保证每次创作成功，不改变已有授权、计数、unknown处理或逐镜媒体Gate。
