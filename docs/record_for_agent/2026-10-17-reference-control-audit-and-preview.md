---
record_kind: architecture_implementation
topic_id: reusable-reference-control-preview
learning_eligibility: ineligible
---

# Reference Control Audit And Preview

Date: 2026-10-17

## Goal And Scope

建设跨项目、跨镜头的控制目标→参考职责→所选路线→exact输入→验收证据说明，沿既有 Canvas、Planner、Router、compiler 与唯一 committer；《界蚀》是现有失败案例，不是特殊分支。前序 10-13 reference preflight 与 10-16 preserved-video spec/plan 只作历史依据，本轮没有把它们当新通用 spec 或付费许可。未新增 Provider、执行链、timeline、renderer、状态库、依赖或 QA 放宽。

## Audit Findings

| Control Goal | Existing Owner / Material Duty | Exact Route And Native Binding | Control Strength And Evidence |
| --- | --- | --- | --- |
| 首帧一致 | approved_keyframe / FIRST_FRAME；原图负责初始视觉 | Planner IMAGE_TO_VIDEO；H3 Max / Seedance `content.role=first_frame` | 显式 API 端点输入；不证明中段动作、人数或镜面合格，仍需 exact 输出逐项 QA |
| 生成末态 | LAST_FRAME 与原末态要求；采用切点另由 composition 声明 | 同一 I2V route 可选 `last_frame` | 生成末端输入，不等于原较早切出帧；不能拿5秒尾帧代3秒采用末态 |
| 人物身份 | Character 的 identity 引用与 Scene 参考分别有 owner | R2V 将 identity/scene 编为 native `reference_image`；exact semantic evidence 与 index 可在报告中对照 | 模型引导；同图多个 alias 不是多份独立人物证据；人数、身份及道具须实测 |
| 动作时序 | generation_intent.subject_action / motion_intent；视频负责明确声明的动作/几何预演 | R2V 实际 `reference_video` + 原文；frame route 不可混该 role | 模型引导；参考时长、生成时长及采用窗口分开；duration 参数不保证动作落点 |
| 空间/摄影 | scene_continuity / camera_intent / camera_endpoint 与原图/白模 | 端点图或 reference_image/video；无额外硬摄影保证 | 轴线、位置、遮挡、人数、反射、机位/焦段、输出画幅均需当前媒体观察 |
| 白模职责 | Director 既有逐镜说明、实测 Registry metadata 与白模 QA | 视频须实际成为 `reference_video`；普通 existing_video 仅是候选，不能推断合格白模 | 必须核对用途、几何、完整动作及采用接点；精确 frame mode 不支持并用视频时逐镜记录能力证据/例外，不静默丢弃 |

MiniMax 当前[官方 V2 API](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)与火山[创建接口](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)、[Seedance 2.5 提示词说明](https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=zh)均区分端点与参考路线；两类 roles 互斥。Seedance reference 模式可在原文指定图片为首尾帧，但仍是参考引导，不获得端点模式约束。本轮公开文档 GET/搜索，无 API POST；MiniMax 国内页首次超时，已核对可访问的国际官方同接口，不外推网页端或第三方网关。

项目已有 H3 Max frame/reference、Seedance 2.0/2.5 frame/reference 能力，并非全部缺失。H3 Max sealed ratio 为 adaptive 才开放 `minimax-h3-max-fl2va-v1`，frame native 不发 ratio；Seedance 2.5 frame native 为 adaptive，R2V 明确 `omni_reference_task_type=reference`，2.0 不发送该值。unsupported 混用或 native hard control 继续沿原 capability/compiler 拒绝，没有为了预览扩大能力。

## Shared Changes

- `canvas_preflight` 保留显式 owner、媒体实测尺寸/时长/fps/帧数；显示 semantic binding 数、SHA/bytes/MIME 唯一组、重复组和原 composition / requested duration。selected route、独立人物证据、白模用途/时序仍为 NOT_EVALUATED；不运行 Router、自动去重或推断所有视频是白模。
- `production.video_reference_controls` 解释既有 PreparedGeneration，关联 requirement semantic evidence、native content 路径/媒体序号、原文 prompt、实际模式/profile/compiler、同字节组及原 QA 全部要求。H3/Seedance scalar native 参数复用实际 payload builder，不读 reference、credential、transport 或签 permit；materialization/admission/quality 仍独立。
- 共享 CLI prepare/prepare_repair 只序列化 immutable 输入、决策、编译、request/binding 与报告，不 deepcopy/序列化运行时 Provider。修复此前 dataclass 默认编码会触及 Provider 并产生不可序列化结果的实际路径，未改变 service 生命周期。
- 原文到媒体编号由既有 `seedance_source_expression._source_media_indices` 唯一推导，Canvas 和 actual compiler 复用；后者仍先做完整 evidence/role/bytes 校验。没有改 /1、/2 原文语义、旧 hash/native顺序，也未删除重复绑定。若未来按 bytes 合并上传，必须另验全部角色及 alias→index→compiler 输出；本轮没有证据支持静默合并。
- 已验证步骤写回 `docs/canvas-production-harness.md`、matrix 和官方 H3 Max provider owner。Harness policy 只把新测试加入既有 generation_feedback suite 与路径映射，没有削弱检查或质量 Gate。

## Current Jieshi Evidence

通过标准 `load_production_project`、`reopen_authoring_input` 及 author validation 重开 current sealed input，再运行只读 preflight：Manifest103 / Project14，source SHA `302772dd855b9ae60dd9b15b5c4319cae63c0b781f20b528c4cdad2adc908980`；10 个 semantic bindings、2 组 unique bytes。9 个 image aliases 均为原 PNG `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`；另一个是 v015 视频 `8b8d1e43d5295109fceda1755bc41e005f6e927ef2b8e657d0328f288aa50e33`，720×1280、24fps、96帧、4000ms。作者职责和每个 owner 保留。原 docs 初版定义直接 resume 当前修订项目被 source-selection guard 正确拒绝；不能把新项目的 position=None 当当前运行状态。

独立重开 CN unit 的 sealed execution-binding 文件 SHA `8b86179a31b94e04b0d9d241816d9dbdee3f5b520b2fa765cac8c4d101410c3b`，新报告给出 native `content[1]`–`content[9]` 为9份同PNG reference_image，`content[10]` 为白模 reference_video；保留 identity/scene/video_reference 各语义证据。resolved hash `821b422b878fa4a105eb4ba55dd417236f7f4c9d7bec1d7adb45d04a51fd662a`。这是历史 exact 请求的解释，不是新选路、调用或 accepted state。

当前 attempt `canvas-c5f04a3750cb384d4bf55ae00424511ede0f818c` 仍 failed / validate；只读核对前后 project.yaml 与 state/manifest.json 的 SHA 未变。原15项、4 PASS/5 FAIL/6 NOT_EVALUATED、缺陈立/手部幽影/3秒动作不到位的 STOP 保留。历史累计17次视频调用、本轮新增视频/图片/音频 POST 均0，S02仍0；未读取凭据、重用额度/permit、激活或重生成。

## Verification

源码 commit `473ed99d7c449689baaf797dffd57546a8d140f2`，base `9917a28d60498fbe823794a29bf072fd25f20a59`。focused aggregate 325 PASS，覆盖新报告17项、Canvas/source 73项及既有 H3 Max/METASO/Seedance/feedback：不同人物、动作与空间；三模型族各首帧/首尾帧/视频参考；重复字节但保留语义职责与原native输入；actual payload 参数/role核对；错 requirement 拒绝、blocked无伪造route、CLI不copy Provider、preflight无runtime/写入及 immutable resume。

完整 exact-range 为17 PASS / 1同run覆盖后的适用性 skip，receipt核验的 integrity / fresh / complete_completion_proof / scope_worktree_clean 全true。完整 exact-range receipt：`.agent/harness/runs/reference-control-preview-20261016-r1/receipt.json`；验证结果、freshness/integrity/completion proof 以该机器证据为准。Architecture scoped check 有既有 Seedance adapter +6 effective LOC 的单一 WARN、0 error；这里只从原 payload 提取同一职责的参数 builder，并保留原 body 顺序/参数和回归，未扩入报告职责或刷新 baseline。

Risk Gate 对上述 exact source candidate 为 `NATIVE_REVIEW_NOT_REQUIRED`：修改只解释既有已选输入、统一纯编号与原 payload 参数，未改变许可、凭据、预算、持久化或状态推进；normal/boundary/failure 与历史 replay 已由 focused 和完整 Harness 覆盖，没有剩余重大运行语义缺口。Parent 自审并裁决；两次只读调查不冒充独立最终审查，旧任务已关闭的 review 历史不重开。

源码已 push 到 origin/main 并用 ls-remote 核验 exact SHA为上述源码 commit。

文档 checkpoint receipt：`.agent/harness/runs/reference-control-record-20261017-r1/receipt.json`。publication 以对应 Git 与 remote main SHA 核对为准；原 AGENTS/playbook 及旧记录/spec/plan/baseline 的 staged/dirty/untracked 工作全部保留。

## Empirical Boundary And Next Unit

本轮完成通用工程表达与多场景离线行为验证，未证明任何模型的通用质量改善、单镜通过、连续镜通过、完整故事交付或 human 1.0x 验收。9份同图、4秒reference/5秒generation/3秒采用分别造成多大影响仍无受控因果结论。

最小下一实证问题是“同一严格目标下，端点输入与视频参考各保留/失去哪类控制”，不是再投旧失败请求碰运气。建议先封存一个最多2次、零重抽的 paired unit：官方 H3 Max CN / MiniMax-H3-Max / 768P / nominal5s；同一原PNG与全部15项/0–3秒采用保持。A为原PNG first_frame、adaptive、无reference视频，必须显式记录所选mode无法并用动态白模的逐镜例外；B为原PNG语义reference与已核验v015 reference_video，显式比例，记录失去端点输入。若保持旧9个语义alias，报告必须原样披露；不能将去重混进模式变量。两臂 binding cardinality 随模式改变且 seed 不受控，因此不是 isolated A/B；即使执行也只给有界观察，不足以证明因果或跨项目质量。

这是可审阅的外部决定方案，未执行、未创建授权/预算/intent/permit。恢复须用户新的有限付费授权，operator 新封存 exact profile/inputs/preview、内部 upper bound、egress、恢复 grant及当前剩余计数；不沿用已消费单元、预算或用户Key存在。每臂 exact MP4 后先逐项 MCP，FAIL/NOT_EVALUATED 停止 attempt；第二臂只有其独立授权与第一臂known/closed outcome齐备才执行；证据型 NOT_EVALUATED 先补证，不以缺证为第二臂重生理由。工程报告不解除旧S01 STOP。跨项目质量仍需另有当前授权、真实素材及代表性 holdout，不用本工程 fixture 或单《界蚀》结果代替。

## Record And Learning

`record-ai-video-session` 记录为共享工程工作，不是新媒体实验。`distill-ai-video-learning` 自动评估为 no_candidate：experience 检索及当前源码复核显示历史 Alice参考/编码比较、旧METASO frame能力和当前《界蚀》失败属于不同边界；没有新增可归因模型质量实证，不能把离线用例数量当 independent attempts。未创建 Learning placeholder、修改 Skill/Policy/Gate 的经验采纳或全局 memory。
