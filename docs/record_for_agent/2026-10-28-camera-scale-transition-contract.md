---
record_kind: architecture_implementation
topic_id: prospective-camera-scale-transition
learning_eligibility: ineligible
---

# Prospective Camera Scale Transition

## Change

用户要求实际生成MC00城市试片；原FL2VA规则把 `same_subject_scale` 与其他六项一起强制True，无法如实表达已批准的屋檐近景到市政中远景。未把该字段伪填True、删除rich intent或换模式绕过。当前由原 `ConditioningCompatibilityEvidence` 增加 optional typed `scale_transition`，`_conditioning_scale_transition.py` 只负责前期证据结构与pure binding验证，不增lifecycle／Router／permit／writer。

旧True分支、序列化与固定hash保持；False分支必须绑定exact首尾ID／SHA、current camera／space／timing hash、相同时长、anchor review与trajectory来源，以及四项全PASS prospective findings。其他六项仍须True。None、I2VA携带扩展、True与扩展矛盾、locked／缺失camera、proxy-only、缺证／篡改／失配均拒绝；最终requirement重验实际asset SHA，复制／replay不跳过校验。

该分支表述的是前期可行性，不证明模型已经照做。MC00取新城市总图、实际屋檐／市政端点照片与解析设计轨迹，不使用已退回proxy作为通过依据。新创城市坐标、约28mm摄影估计与照片未标定均显式说明；实际原速视频、声音和接点另验。具体试片资料归 `outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v2/`。

## Verification

现有 provider-neutral 九文件关联回归503通过，Jimeng模式／rich正文／qualification四文件103通过。包含旧hash固定回归、缺证／错anchor／SHA／camera／duration／未知和locked拒绝等。独立原生code-reviewer按 `contract-review-target.json` 的七份exact source SHA审查，无阻断问题，结束时SHA未漂移；前期证据引用的五份源SHA另经实际核对。

Harness只新增该helper到原 provider_neutral_video_requirement mapping，未减少检查；matrix同步准入条件与媒体边界。当前没有放宽paid授权、预算、egress、unknown或one-use permit。工程验证不代正式视频通过。

## Scope And Learning

## Feedback Owner Integration

真实canonical prepare发现 `generation_feedback.py::derive_generation_interventions` 仍自行扫描conditioning中所有False，错误把已通过canonical validation的显式尺度变化改判为reference conflict。现已删除这条重复判据，直接复用 `validate_requirement_conditioning_compatibility`；reference conflict与shot_authoring出口不变。合法typedFalse、缺证False、axis失败和实际尾帧SHA漂移分别回归，相关五文件174通过；独立code-reviewer增量审查无问题，并实跑该文件31通过。新增两文件审查SHA归MC00-city-v3的feedback-review-target，旧5cc receipt不冒充覆盖此增量。

首次完整scale契约commit `5ccfdf9` 的focused Harness已通过，receipt `.agent/harness/runs/camera-scale-transition-20261028/receipt.json`，包含原voice、harness、video-provider和provider-neutral映射检查。本段额外feedback改动单独取证，未取消旧测试或改历史结果。

这是原owner的有限表达修正，服务连续摄影中的通用景别变化，不硬编码作品、时长、Provider或特定素材。其他窗口的composition／audio源码、测试和staged内容保持。

按 record-ai-video-session评估该稳定实现检查点；distill-ai-video-learning为no_candidate：本次实现和一组前期设计资料不能证明模型动态服从规律。没有更新Skill／Policy生产要求或全局memory；视频结果另记原作品记录，不把工程PASS升级为P6／Final Acceptance。
