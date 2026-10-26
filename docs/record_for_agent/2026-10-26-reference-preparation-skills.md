# Reference Preparation Skill Installation

## Authorization And Scope

用户明确要求下载制作参考素材的开源 skills，并保证不与已有 skills 冲突。
使用 skill-installer 从 scenario-labs/skills 的 commit
`e0a051cd6e3a7ce3b27b607f4f859611de0c49df` 下载
`scenario-identity-library`、`scenario-seedance-storyboard` 到 `.agents/skills/`。
本轮未生成图片/视频、未付费、未改变Shot3素材或生产状态。

## Integration

各目录以本地中文 `SKILL.md` 为唯一入口，下载的原入口逐字保留为 `UPSTREAM.md`，其余参考文件
未改，保存MIT LICENSE与SOURCE.json原文件hash。上游Scenario平台操作、自动依赖安装、重试
默认值、分数验收及2.5特定假设不作为本项目执行指令。

人物/道具素材归identity specialist，动作状态图与分镜素材归storyboard specialist；
open-video继续拥有导演与coverage，seedance-authoring继续拥有所选版本的视频表达，
Registry/committer/adapter/permit/QA/HyperFrames的职责不变，不默认转Blender白模。
两个现有入口增加缺失参考检查与制图分流，随后核对实际模式与输入列表；不强制固定图片数量，
不把画布摆放、图片数量或静态关键帧当实际绑定/运动正确的证明。

## Verification And Limits

58项精准测试通过：test_open_video_skill、test_seedance_authoring_skill、test_runtime_skill_boundary。
脚本核对上游原文件SHA、MIT许可证、入口相对链接和本项目skill name唯一性通过。
Parent自审：仅Agent侧文档与routing链接，不修改运行代码或权限，NATIVE_REVIEW_NOT_REQUIRED。
这不证明即梦实际消耗新参考、自然表演或Shot3质量；新skills待下一轮发现加载，当前可直接读取。
工程Harness receipt：`.agent/harness/runs/reference-skills-focused-20261026/receipt.json`，结果FAILED。
文档contract与两个skill测试通过；harness_tests为319通过/2失败：既有policy缺少
`authored_visual_revision_tests`的full coverage映射，以及7个非本任务源码/测试未映射。
另行policy-audit确认新增skill不在unmapped中；未改他人policy来消除失败。receipt绑定检查时
的staged快照，随后仅本记录追加结果，不声称最终提交有完整Harness PASS。

本次为用户直接授权安装与适配，不是自动学习采用；distill评估no_candidate，尚无新参考包的
真实生成对照，不作通用质量提升承诺。原视频失败与未接受状态保留。
