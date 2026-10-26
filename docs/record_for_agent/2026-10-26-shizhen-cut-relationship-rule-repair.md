# Cut Relationship And Reuse Review Repair

## Authority And Scope

用户针对 A 版两处分析明确要求“这个是规则上的缺失得修改下”。本次直接修订既有 `open-video` 指导，
不创建新 Skill、QA schema 或自动评分器；不修改视频、不新增付费生成，不改变已认可的失踪事件。
这是用户明确要求的规则修订，不是由自动学习候选推导出的授权。

## Exact Evidence

- A 版：`outputs/shizhen-episode01/opening-world-title-20261026/variant-A/失帧-独立开场-A-结构预演.mp4`，
  SHA256 `1a2efa795beba621d962ac9c2cf817a2f697c95489bcac756d39f204f0d7ecd6`。
- 实际第 72 帧 / 3.000 秒：干地街景硬切雨夜站台，没有画内空间定位、行动或视线交接；
  “同属城市”不足以实现原定宏观到微观的关系。用户先报告约 2 秒处不理解转场。
- 实际第 322 帧 / 13.417 秒：A2→A3 同景别切镜，女人头部朝向、手臂与衣领状态跳变。
  12–14 秒逐帧解码未发现完全重复帧；本地 1x 播放报告零掉帧，不足以排除观感顿挫。
- A 第 304–336 帧与 focus-002 对应第 232–264 帧，经 480×270 RGB 解码比较完全一致；
  这是该采样范围的事实，不外推全片像素相同。旧接点存在不构成质量豁免。
- 本地证据：同输出根目录下 `qa/user-two-cut-analysis/decoded-analysis.json`、
  `seam-before-after.jpg`、`first-cut.jpg`、`qa/playback-A.json`、`qa/integrity.json`。
  这些为原会话本地媒体证据，本次规则提交不夹带生成视频或旧未提交工程。

## Rule Delta

旧规则已经要求逐接缝审查，本次同时承认执行遗漏，不能把问题全部归咎于没有规则。
在 `references/creative-completion.md#cut-relationships-and-reused-footage` 补足具体判断，
并从 `open-video/SKILL.md` 的编辑/拼接入口显式引用：

- 切镜的空间、行动、声画、因果或情绪联系必须能由观众感知；不能靠作者解释或特效补缺。
- 同构图接镜检查姿态、动作阶段和速度；区分播放问题、源动作与接续问题，不以零掉帧放行。
- 已认可事件、单镜和未改源文件不豁免新成片及被复用片段内部接缝审查。
- 保留有意跳切、蒙太奇、静止与省略的空间；不要求每刀空间连续或跨镜像素一致。
- 沿既有 review 留具体观察与编辑理由；无声画证据仍为 NOT_EVALUATED，分析限定不授权改片。

## Verification And Boundaries

`tests/test_open_video_skill.py`、`tests/test_seedance_authoring_skill.py`、
`tests/test_runtime_skill_boundary.py`：58 passed；`scripts.docs_contract_gate check` 通过。
另核对新增相对链接/标题锚点、任务 diff 和媒体 SHA；不新增逐字匹配文档内容的测试。
这是关联 Skill/契约的静态回归，不是完整工程回归，更不证明导演已自动执行规则或成片审美通过。

Parent 自审：范围仅两个 advisory 文档及本记录，无 runtime/权限/状态变更，
`NATIVE_REVIEW_NOT_REQUIRED`。未联系其他 session，未调用 TUI。
学习评估 `no_candidate`：本次是一个媒体链的直接用户纠错，未建立跨实验改善效果，
不另建候选或声称新规则已经通过真实修复后的成片验证。A/B 仍为预演，既有缺陷未修。
