---
record_kind: architecture_implementation
topic_id: assembly-harness-evidence-gate
learning_eligibility: ineligible
---

# Assembly Harness Evidence Gate

## User Request And Result

用户在《失帧》连续片出现约21秒与24秒重复扫码后要求把Shot拼接验证纳入Harness。本次直接实施该要求，新增现有Harness CLI的 `prepare-assembly-review` / `verify-assembly`，没有另建Product控制面、timeline或验收状态。`open-video`明确连续片交付前必须执行该入口；缺失或未通过不得称接点已验证，用户要求先看时仍可如实交未验证审看片。

## Contract And Ownership

`scripts/agent_harness_assembly.py` 只读重开当前MP4、唯一ResolvedTimeline、HyperFrames report和回答原字节，按当前时间线派生原owner的全部相邻Shot接点。回答封存视频、timeline、report、inventory身份，输出再绑定回答SHA和观察者；运行中变化拒绝。CLI在工程Git scope前独立路由，不把本命令当engineering receipt或Production接受。

`junction_review.py`仍独占接点推导与裁决；新strict模式逐刀要求 `repetition`、`state_continuity`、`pacing` 的明确观察，并保留原声音、剪辑决定、正常速度人工观看声明要求。明确动作FAIL不能被其他缺证据掩盖；缺项为NOT_EVALUATED。旧visual-review默认行为保留。实际join report未重复给 `timeline_frames` 时仍按原 `measured.duration_frames` 匹配当前时间线，显式矛盾拒绝。无自动看片/听声/语义识别，不证明填表者真实看过，不签人工接受；Shot级inventory不自动发现生成视频内部的所有摄影切镜。

## Verification

先验证缺模块的Red，再实现并运行新入口及原接点Gate：47 passed；随后新增回答SHA和运行中变化测试。手动相关组合此前为135 passed；扩展Harness/Skill/runtime组合实际381 passed、2 failed，失败指向full覆盖清单与已有未映射文件，本次新增check的full覆盖条目已补齐。真实HEAD `f12a9a1be73c143026ece695400661f9b9720ef3` 只读对照确认原来就缺 `authored_visual_revision_tests` full覆盖，并有同一7个未映射路径和3个未引用测试；不修改其他窗口的这些契约或掩盖失败。

实际运行新CLI对已落盘成片的身份与观察阻断检查：

- 当前33.875秒版本，SHA `45fb4e45f815bbe00f42165429dd5f19335e2dbf60ef4206710e09755308f233`，自动导出2个Shot接点；待填模板验证返回1、NOT_EVALUATED。
- 旧36.25秒重复版本，SHA `fbc9b34f583dabb6d86b21a2f1412243ddfea717cb83cf98fd4afdfb5c2d3e9a`，将用户指出且此前exact接触表确认的重复动作记录为explicit evaluator FAIL，其他项保持未评估；验证返回1、FAIL。

实际receipt：`.agent/harness/runs/assembly-gate-live-20261026/runtime-proof.json` 及相邻两组template/result。该结果证明现有素材与声明的绑定和阻断，不证明自动发现重复动作，也没有给当前版伪造人类PASS。本次无新生成、render、付费调用或发布，影片接受状态保持PENDING。

## Governance And Remaining Limits

Parent自审：复用唯一接点owner，新增模块只读，旧默认路径、Production与permit状态不变，错误影响有界且可逆，未触发必须独立review的风险条件。全仓agent_rules检查另发现已提交AGENTS为14,185bytes、既有预算14,000bytes；本次没有提高预算，也没有在AGENTS再加规则，流程要求归原open-video owner。完整Harness/全套回归尚不能宣称通过，最终exact staged结果由交付报告给出；旧baseline阻断保留。

首次exact staged Harness在测试前拒绝：policy/matrix同时有本任务已stage hunk与其他未stage hunk。没有覆盖或stage其他改动，也没有放松隔离检查；改用只含本任务内容的稳定commit range执行隔离验证，具体receipt和结果在交付报告披露。该失败与源码测试、成片验证分开记录。

学习评估 `no_candidate`：本次是用户直接授权的确定性合同修复，两个真实文件用于验证绑定/阻断，不能推出通用模型视觉检测能力或声画质量结论；没有自动学习adoption。旧媒体和并行dirty改动全部保留。
