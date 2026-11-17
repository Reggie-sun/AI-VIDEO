# Jimeng Seedance History Audit

## Scope And Evidence Boundary

本次只读审计即梦案例；无新生成、未重新原速审片或听音。下表观测与用户反馈来自可追溯历史记录，当前只核验文件存在和SHA，不冒充重新裁决。原始prompt保留路径/hash而不复制入新规则；缺失绑定与参考均NOT_EVALUATED。fixture不是Production QA真值。

## Cases

| Case | Model / mode | Finding / time | Repair and acceptance |
| --- | --- | --- | --- |
| shizhen-s03-cg-hover | seedance_2.5 / first_frame | f122–129无支撑悬停，5PASS/2FAIL/1NE；5.083s–约5.4s | 试剪删123..129，随后真人方向覆盖CG；未验收；用户：旧10秒迟缓反应被否决；后续明确改真人 |
| shizhen-s03-004-hover | seedance_2.5 / first_frame | 瓶支撑改善但枪6.019/7.023仍悬停；6.019s,7.023s; 7.75–8s落台 | 同首帧加强动作文字未解决；后续005同时换模型/参考/时长；用户：要求重做不自然、过慢扫码与掉枪 |
| shizhen-s03-005-state-refs | seedance_2.0_vip / multimodal | 3.716667人在，3.75人消失枪接触台面；全部8项仍NE；3.716667s–4s | 增加ready/landed/reaction状态图；无隔离变量，不能归因；用户：PENDING |
| shizhen-duplicate-scan | seedance_2.0_vip + seedance_2.5 / composition_of_distinct_sources | 36.25秒版21/24秒重复扫码；约21s及24s | 裁掉20.875–23.25，同窗声画保留后一次；33.875秒版未人工接受；用户：明确指出重复扫码并要求剪辑 |
| jieshi-mini-cg | seedance_2.0_mini / reference | 修复上传后CG成功出片，手倒影仍出现；NOT_EVALUATED | 先两次KNOWN_NO_EFFECT，exact上传域修复后出片；真人方向覆盖CG；用户：明确要真人，CG不能算完成 |
| jieshi-mini-realperson | seedance_2.0_mini / reference | SUCCEEDED/fetched，不是质量PASS；NOT_EVALUATED | 复用1202字符旧prompt/真人图，无新生图；按用户要求未QA；用户：仅测试、不追加检查 |
| yanshengyuan-junction | seedance_2.0_vip / first_last_frame (bridge mode3) | 4秒桥段视觉五PASS，但43秒连续版7秒后卡顿重叠被用户否定；连续版约7s后 | 删重复桥段、源窗修剪至38秒并去重复笑；声音/全片接受仍NE；用户：7秒后仍卡顿/重叠；后来改三条夸张新片 |

## Original Evidence

精确记录、媒体、prompt、参考路径及本次SHA在 `tests/fixtures/jimeng-seedance-history.json`。缺失文件不会由相似命名补齐；用户认可只按记录明确文本，不能由请求继续或播放器执行推断。

- `shizhen-s03-cg-hover`：[2026-10-26-shizhen-s03-witness-and-live-action-override.md](../record_for_agent/2026-10-26-shizhen-s03-witness-and-live-action-override.md)；media exists=False；prompt exists=True。
- `shizhen-s03-004-hover`：[2026-10-26-shizhen-s03-witness-and-live-action-override.md](../record_for_agent/2026-10-26-shizhen-s03-witness-and-live-action-override.md)；media exists=True；prompt exists=True。
- `shizhen-s03-005-state-refs`：[2026-10-26-shizhen-s03-witness-and-live-action-override.md](../record_for_agent/2026-10-26-shizhen-s03-witness-and-live-action-override.md)；media exists=True；prompt exists=True。
- `shizhen-duplicate-scan`：[2026-10-26-shizhen-s03-witness-and-live-action-override.md](../record_for_agent/2026-10-26-shizhen-s03-witness-and-live-action-override.md)；media exists=True；prompt exists=NOT_EVALUATED。
- `jieshi-mini-cg`：[2026-10-26-jieshi-jimeng-mini-upload-stop.md](../record_for_agent/2026-10-26-jieshi-jimeng-mini-upload-stop.md)；media exists=True；prompt exists=NOT_EVALUATED。
- `jieshi-mini-realperson`：[2026-10-26-jieshi-jimeng-mini-upload-stop.md](../record_for_agent/2026-10-26-jieshi-jimeng-mini-upload-stop.md)；media exists=True；prompt exists=NOT_EVALUATED。
- `yanshengyuan-junction`：[2026-10-25-yanshengyuan-seedance20-two-shot.md](../record_for_agent/2026-10-25-yanshengyuan-seedance20-two-shot.md)；media exists=True；prompt exists=NOT_EVALUATED。

## Gaps And Candidate Search Brief

1. 接触/支撑/释放/落点的可观察状态与运动参考：004仅强化文字仍悬停；005同时改变模型、时长、prompt和图像，不能证明状态图有效。
2. 接点事件账目：单镜局部通过仍出现重复扫码、重复笑和物体状态跳变；现有owner已规定逐镜/接点审查，缺口是执行与可追溯证据，不应再建QA引擎。
3. 参考职责与native输入绑定：画布展示多图不能证明实际历史请求消费了它们；须用现有request/dispatch/Registry验证。
4. 反例和supersession：Mini早期无出片已被后续fetch替代，但后者不反证旧失败，也不证明自然度。

## Exclusions And Generalization

10-21 2.0/Fast对照实际为Ark API，排除即梦效果。当前范围没有绑定完整的即梦Fast质量案例，因此Fast质量NOT_EVALUATED。09-28画布方法只提供UI观察，排除版本能力/效果推论。其他模型一律不纳入。现有Learning Claims未发现可直接采纳的即梦专属确认项；本次案例不自动成为Learning Claim或ADOPTED规则。

## Offline Regression Contract

离线可核查scope、artifact hash、supersession、失败/未验证保留以及owner分工；不能离线证明新Skill改善真实出片。固定旧视频可补原速画面/声音分析；付费A/B必须另行封存明确变量、版本、渠道、模式、预算与验收。

## Evidence Reconciliation

已将原失败与修后媒体分开：`original_failure_media` 锚定旧36.25秒重复扫码版、旧43秒颜生源接点失败版；`media_role=repaired_composition` 的当前媒体不承接旧FAIL。混合2.5与2.0源的失帧连续片标为composition，并分别列出source_models及待核验绑定，不归因单一模型。原CG18秒prompt改为实际 `S03-revision-02/native-prompt.txt`，不误用前一10秒attempt的 `S03-execution` prompt。

Mini两案例已重开本地compiled request，只读取prompt_text/image_bindings等输入字段，保存文件与字段hash、generation/model/mode/request identity；不导出账户信息。composition没有单个native prompt，不能伪造。缺失或尚未重开的binding明确NOT_EVALUATED，存在文件不等于证明实际提交消费。

## Bounded Success

第8例 `yanshengyuan-two-shot-limited-acceptance` 是有限成功反例。原 `two-shot-human-feedback.json` 明确用户回答“可以”，上下文是两段视频及S02完整商品名原声确认，绑定原S02 SHA `8a9d3b27d7b7e571419e8c1851ab3eefe392d01f3df546d354280dc4b520bde4`。两片认可不批准未来或整广告，旧声音operator UNKNOWN仍保留。后续43秒接点被否决不抹掉这次单镜有限认可，同样不能从该认可推出2.0一般成功率。

Fast未找到可核实即梦样本，明确NOT_EVALUATED；Ark 2.0/Fast不补位。本审计现在8案例，含失败、有限成功及质量未验证，非失败样本普查或频率估计。
