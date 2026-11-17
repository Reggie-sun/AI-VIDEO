# Jimeng Seedance Owner Decisions

## Scope And Evidence Layers

仅即梦渠道。模型官方宣传、`jimeng_models.py` 注册/UNQUALIFIED状态、渠道native参数及真实媒体分别陈述；本次未重测live渠道能力。Ark 2.0/Fast对照及API Mini白模不参与即梦效果推断。历史案例见 [case audit](2026-11-16-jimeng-seedance-history.md)，GitHub正文审查见 [candidates](2026-11-16-jimeng-seedance-skill-candidates.md)。

## Existing Coverage And Decisions

| Gap from actual history | Existing owner and regression | Decision / remaining hypothesis |
| --- | --- | --- |
| 消失后道具悬停、接触释放因果 | open-video known-failure repair；scenario-seedance-storyboard Reference Preparation；tests/test_reference_planning.py 的 motion duty/required tests；test_jimeng_causal_compilation.py | 保留现有职责。状态图不证明持续动作；合规连续motion reference是否改善该exact案例仍待单变量实验，不提升为所有镜头必需 |
| 白纸消失再现、重复笑、重复扫码 | open-video Required Product Gates；junction_review.py；test_junction_review_gate.py | 保留逐镜与全片两层验收。新增历史索引关联原始失败、修剪与后续证据；不把单镜认可迁移到整片 |
| 画布素材不等于native输入 | storyboard Jimeng Canvas Handoff；seedance-authoring Authoring Procedure；test_jimeng_shot_modes.py及causal compilation | 保留actual_model_inputs/exact native绑定，不新建参考路由。历史UI截图无submit绑定时保留未知 |
| 表演与关键动作未完整达成 | Director intent与performance_authoring；test_performance_authoring.py | 保留原目标，偏好/修复margin不变成用户硬要求。放松姿态约束是否改善自然度尚无即梦受控证据 |
| 原声UNKNOWN与技术存在性混淆 | Per-Shot Gate、junction review audio evidence | 保留UNKNOWN不重试；原声语义、正常速度听感、用户认可独立记录 |

## Integration

不新增或替换Skill。现有三个Skill已经包含上述检查，继续追加泛化Prompt模板会增加上下文且不能补媒体证据。新增能力限定为可检索的真实案例清单、输入/输出identity审计及历史失败到已有离线回归的关联。仅在对应失败出现时按record→retrieve流程按需读取案例，不默认把全案例库预载进每个Agent。

离线回归只证明现有控制面仍拒绝错误绑定、缺motion evidence及未完成接点审查；不能重现随机生成质量，更不能保证修复悬枪或自然度。后续A/B须先固定同版本/渠道/模式、原目标、已满足项、exact输入与唯一变化，单独获得本任务范围内生成授权并走原预算/permit/逐镜Gate。当前任务明确禁止为验证Skill擅自生成。

## Learning Assessment

现有Learning目录未发现即梦专属已确认采纳claim；H3/Vidu效果排除，HyperFrames caption claim非即梦模型效果。历史不同Shot、同片多次观察、混变量修复不自动构成独立重复实验。本轮 `no_candidate`，不新增待确认占位、不更新正式Skill/Policy/Preflight/Contract/Gate经验规则。若未来满足admission，则按distill-ai-video-learning封存exact candidate commit/hash，请用户确认后由现有owner验证采纳。
