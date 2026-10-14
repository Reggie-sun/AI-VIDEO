# Remote Image Materialization Failure Contract

## Goal And Authority

原S01底图已真实返回且视觉FAIL，paid receipt ACCEPTED，local materialize却为OUTCOME_UNKNOWN且阻断下一请求。用户随后“继续做图啊”授权有界图像修复；必要共享契约修复由Parent self-review，当前main，无development worktree。失败图绝不作为accepted S01。

## Scope And Owners

P5仍独占graph/resolver。image frontier只排除desired未变化的既有nonfresh节点，或bootstrap遗漏但在同一baseline P5 projection中desired未变的已登记asset节点；其他新引入节点不豁免。不按Provider/reference种类白名单，不能把首次投影的既有asset视作新修改。baseline composition仅用当前role唯一旧asset替换尚未存在的新output引用，是write-free scope comparison，不创建ResolvedTimeline或renderer。

唯一committer新增显式 `close_remote_image_materialization_failure`。只接受remote image、local OUTCOME_UNKNOWN/materialize、paid ACCEPTED/SETTLED、完整原PNG/result/provenance/wire证据、空candidate tuple、仍选择原base tuple、exact expected Manifest revision。将local attempt封存FAILED，并绑定immutable typed closure receipt；paid receipt/reservation、原媒体、历史、active project/Registry/graph及dependency states全部不变。真正paid unknown、缺证、tamper、stale、mixed candidate、succeeded/activated均拒绝。此动作不激活素材、不签QA、不授权新POST、不查凭据、不调用Provider。

## Persistence And Compatibility

Attempt可选字段、validator及既有serializer由 `state_commit_attempt_contracts.py` 独占，`models.py` 仅继承；既有serialization职责平移且旧字段省略语义保持，避免大型model继续增长。

closure pointer作为image attempt可选字段，未使用时完全省略，不改变旧serialization/hash。pointer包含canonical path/hash/file SHA；closure使用 `schema_version=image-materialization-failure/1`，绑定attempt/request/result/provenance/PNG/paid receipt、expected revision、operator actor及非空白理由。标准Production reader必须重新验证所有joins；同内容exact replay不写Manifest，不同actor/理由/revision拒绝。receipt先immutable落盘再atomic Manifest，crash保持证据不自动接受或删除完整orphan。

## Repair Unit

旧1图片POST、0新视频POST及200 CNY内部上限保留。当前修复最多新2图片：一张修正base，全项PASS才同源单参考去林砚映像；每调用50 CNY内部上限，累计图片最多3，不转用旧抬手机B，金额上限不变。新增输入只具体化侧窗几何、左右手和原静态准备职责，不删原S01/S02动作、对白、广播、字幕或摄影。零自动重抽/fallback；paid unknown即停，视频听音路线未qualified仍不submit。

## Acceptance And Verification

public committer测试重现bootstrap frontier failure、已接受result的本地失败封存与strict reopen/replay。paid unknown、缺/tamper PNG/result/receipt、stale expected revision/base、mixed candidate必须无mutation拒绝；close之后新请求须重新通过全部paid gates。unchanged absent asset节点可准入，已变无关节点仍拒绝。旧Seedream/reference/image/Registry/state/recovery suites及exact staged Harness通过后按Risk Gate裁决review；工程PASS不代媒体QA。真实新图逐项审查八人/八个正常对应侧窗倒影、两人左右手、摄影/空间、可编辑区域和unburned caption。

## Self-Review

保留所有原剧情与旧副作用，拒绝通过猜unknown或删除后镜解除阻断。typed closure只有canonical owner且required joins支持已知返回结果，baseline由同一P5 builder求值；不扩大Provider/model或金额，不新增故事executor、状态库或timeline。Spec scope accepted under task-necessary authorization；图像结果及视频目标仍需真实证据。
