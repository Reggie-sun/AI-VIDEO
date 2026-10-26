# Reference Continuity Integration

## Authority And Source

用户提供本地克隆 `/home/reggie/vscode_folder/SKILL/storyboard-continuity-guard-skill`，
说明作者忘记写 MIT，并明确要求审查后融合进现有 Skill 体系。
本次只读该克隆的全部三个 tracked 文件：`SKILL.md`、`README.md`、`agents/openai.yaml`；
没有执行其安装命令、创建独立上游执行器或改动原克隆。

上游：[jerrymama123/storyboard-continuity-guard-skill](https://github.com/jerrymama123/storyboard-continuity-guard-skill)，
本地 HEAD `cc9e8be140e4f318aeddcbc471b6c39aa9d2a30a`，工作树干净。
该快照只有上述三个文件，未见 LICENSE 或许可声明；“遗漏 MIT”作为用户说明记录，
不代作者补 LICENSE、不将仓库许可标为已核验 MIT。本次用本地中文重新表述适用的方法，
没有将上游全文、README、agent 配置或安装脚本复制发布到 AI-VIDEO。

| Local source | SHA256 |
| --- | --- |
| SKILL.md | `131dae70f6f8590382b18e8605d7161b28d675a901bfa881e445e31d9b05af27` |
| README.md | `e1bcf0c75b823c0086bb2ebc456f50cfffeacf22bd683cc2324aa05cb8ead0bf` |
| agents/openai.yaml | `2c9e5c9975cb09f781dbc8cc86207ee4f64377d89132f67cf189b472b208dfad` |

## Integration Decision

新增一个共享方法 owner：
`.agents/skills/open-video/references/reference-continuity.md`。
`open-video` 在参考准备、复用和交接时读取；两个 Scenario specialist 在制图/交接时引用；
`seedance-authoring` 复核它们返回的结果并执行原有实际输入核对，不再维护同一套图片审查规则。
没有新增独立 `storyboard-continuity-guard` 安装项或全局 Skill，也没有新 schema、Gate、状态仓库或 Provider。

吸收具体锚点、空间布局、物件归属/状态、POV、参考注释污染与局部问题定位；
接点叙事与真实成片运动仍交现有 creative-completion/event-led-timing，不把静态图检查当成视频验收。

## Adaptation Decisions

| Upstream tendency | Local treatment |
| --- | --- |
| 固定屏幕左右、防止换场 | 先判断物理空间及实际视角，允许合法反打、换场和批准异常；不机械锁屏幕左右 |
| 默认最新参考与固定不变项 | 选与职责匹配的可靠素材，实际出点、身份图、场景图、氛围图职责分开；未知事实留缺口 |
| 标注图只能算 rough/rejected | 标注分镜可以是合格审看资料，但不自动适合视频输入；保留干净输入与审看图的关系 |
| 第一人称禁身体/倒影 | 可见范围服从镜头意图，不能把允许的身体或倒影判错 |
| 简化手部、调整道具尺度来修图 | 仅允许不损失必要信息且在授权范围内的改动；不隐藏关键交接，不擅自改手或道具 |
| P0 立即重生成 | 只输出具体偏差和原要求，沿现有修复/授权/预算/unknown 边界，不自动提交 |
| 清理参考标记 | 教学注释与来源水印/AI标识分开，不推导去标授权；后期文字与画内文字按职责处理 |

## Verification

核对四个修改后的 Skill 元数据、相对路径/锚点及共享引用路径；运行既有 Director、Seedance authoring
和 runtime-skill 边界回归及文档契约检查。没有增加逐字匹配新增指导内容的测试。
实际结果：四个 Skill 的 `quick_validate.py` 全部通过；39 个本地链接及锚点通过；
`tests/test_open_video_skill.py`、`tests/test_seedance_authoring_skill.py`、
`tests/test_runtime_skill_boundary.py` 合计 58 passed；`scripts.docs_contract_gate check` 通过，
`git diff --check` 通过；上游三个文件 SHA256 与读取前一致。验证级别为相关回归，未运行完整工程套件。
首轮发现 Seedance 最小入口测试把跨目录 `references/` 链接也计入本地 references 集合；
最终让模型 authoring 复核既有 specialist 结果，保持该层最小依赖和图片审查唯一 owner，未改测试或放宽断言。

Parent 对照本地方法做了以下语义桌面核对，非生成实验或独立模型审片：

- 房间实际镜像与合法反打的屏幕左右变化必须分开判断。
- 原批准消失事件不得因“少一个人”被连续性规则强制改写。
- 保留旧图的身份，不把旧图中的另一场地复制进新场景。
- 带箭头分镜可用于审看，不自动作为干净首帧；真实来源标识不自动清理。
- 关键物体交接不能通过藏手或直接呈现后态省略因果。
- 图像静态一致、参考已绑定均不证明运动连续或声音合格。
- 缺证据、用户只分析或未授权付费生成时，不启动上游自动重生成。

修改范围仅 advisory 文档与记录，Parent 判定 `NATIVE_REVIEW_NOT_REQUIRED`；无关键 runtime/状态/权限变更。
学习评估 `no_candidate`：这是用户直接授权的方法整合，未产生跨实验效果证据，不宣称已改善真实成片。
本轮未生成、重剪、去标或修改《失帧》媒体；原 A/B 缺陷与最终验收状态不变。
