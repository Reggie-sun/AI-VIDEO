# Footage Salvage

## Entry Points

先在原 `Shot.production_intent` 编写可比较的 coverage/source options，并通过原 allocation 明确 raw/source 与 assembly 要求。在所选 `QaPolicy.production_salvage_reviews` 保存 typed `SalvageReview`，沿 `ProductionStateCommitter.activate_qa_policy` 封存；它不是新 Manifest 或资产账本。

```python
report = planning.prepare(parent_shot_id=shot_id, include_salvage_report=True)
# CanvasProductionService.prepare_production 接受同样的参数。
decision = ProductionStrategyDecision.model_validate(report["decision"])
if decision.selected is not None:
    planning.materialize(decision=decision, attempt_id=attempt_id)
    # 全部动态组件就绪后：
    spec, timeline = planning.composition(decision=decision, renderer_version=renderer_version)
```

报告不是授权，脚本中的 `attempt_id`、renderer、target、QA 和所有执行依赖仍由调用方按现有合同提供。缺失生成组件由 `prepare_generation` 进入原 Generation owner；不得调用裸 Provider。正常 compose/render 消费唯一 `ResolvedTimeline`，无手写第二 EDL。

## Authoring The Review

1. 标准 loader 重开 Registry 和 parent。`source_revision` 使用该 asset 的 `creation_receipt_id`；总帧数与时长使用 `video_metadata.frame_count`、`duration_milliseconds / 1000`。源 SHA/size 必须逐字节对应，不用文件名或 nominal FPS 推测。
2. 对每条实际 Take 保存七维 observations、具体现象/事件 requirement ID、缺陷 `[start,end)`、usable/protected/removable windows、首尾状态和替代 asset IDs。完全不可用的 Take 可以有空 usable_windows；缺维度、部分播放或 UNREVIEWED 允许记录，但不能执行修复候选。
3. `PlaybackEvidence` 记录 selected evaluator/proof、实际连续播放覆盖、1x 速度、音频观察和证据 SHA。字段是可审计的观察声明，不是软件对真实观看的证明；抽帧只作为辅助。音轨确实不存在也要明确完成该观察，不能把未听音记为已审。
4. `required_events` 必须保留 parent 的完整 protected requirements；转场/Scene requirement IDs 必须属于原 assembly allocation 和 final-output contract。广告、剧情、漫剧、宣传片、片头可填写不同 genre、scene intent、observable 和 proof，算法不内置平均镜长或广告节奏阈值。
5. 第一次 `prepare` 可列出所有原生候选；使用 `candidate_plan_key(candidate)` 绑定 coverage、allocation、sources、操作，补齐每个 `CandidateRepairPlan`，再更新 QA 并重做 prepare。plan key 排除 QA 和计算出的 blockers，避免自引用。任何字段漂移须重新评估，不能只更新 hash。
6. 所有 candidate 的缺陷处理、保留要求、影响范围、邻镜、否决原因及成本/风险必须显式记录。成本分别填 Provider、local render、elapsed time 的范围、单位和依据；未知范围为 `null/null`。本地编辑的 Provider 成本必须为零；这不意味着渲染时间为零。

## Decisions And Execution

KEEP、TRIM、REASSEMBLE、REUSE、LOCAL_REPAIR、GENERATIVE_REPAIR、GENERATE_INSERT、REGENERATE、REPLAN、OMIT 可组合描述方案。执行能力仍由原 `ProductionOperation` 决定：TRIM/复用/显式 time map/覆盖组件/原声音轨/合成沿既有 renderer；新动态 insert 沿原 generation。OMIT 只能在原 coverage 完整承担必需事件时移除旧素材；整场重设计须显式 authoring revision。

V2V、任意遮罩/调色或其它尚无当前 selected executor 的操作返回 capability gap；先通过受支持的原后期/生成入口得到独立 exact asset 并审核，才能作为复用 source 重新规划。不能把原视频的动作失败靠操作名称改成 PASS。

候选的 source-use PASS 仍是必要条件。局部尾部失败可以剪掉；结构性的动作/因果缺失不能因缺陷标注在窗口外而消失。保护窗口不能裁掉或任意变速。替代表达须在 coverage 的 source/raw/assembly 分工中明确，并用完整新片验证，不用一段导演解释抵消 FAIL。

新评估先比较质量与风险，风险相同时优先较少生成的候选；较少生成候选尚未观察时先补证。多个可行方案用逐维风险偏序比较，相同风险才比较生成次数与有依据的成本区间；unknown 或权衡冲突返回 unresolved。当前评估不估算成功概率。相同动作设计和 requirement 连续失败达到评估声明的有限阈值时返回 NEEDS_REPLAN；明确改变动作意图、对白、时长、首帧等 authored design 后，仅对新设计匹配历史，旧失败仍完整保留。新 seed 或 receipt 不构成重设计；该阈值不增加已有预算，不授权 UNKNOWN 重试。

## After Repair

物化的 child lineage 固定 review_hash/plan_key；旧决策、更新了用途/窗口的素材或旧评估不能直接 compose/generate。canonical source eligibility 在生成 begin/submit 与 composition 共用当前 review 校验，删除 review 也不能解除已物化 lineage 的义务。P5 保持未受影响组件和资产，只有原 resolver 算出的 frontier 需要重建。

每 Shot 仍须执行项目 Post-Media Gate；组装后通过原 Canvas cut packet、P6 final-output review 和原 repair baseline/outcome 比较。对 salvage 的转场/Scene findings，`viewing_mode=full_playback`、`viewing_speed_milli=1000`、`audio_reviewed=true` 是最低证据资格，缺失保留 NOT_EVALUATED。原声/完整对白、动作结果、因果、节奏和邻镜必须按原要求逐项验证。

`EDIT_CANDIDATE`、`NEEDS_GENERATION` 不等于验收。只有 standard loader 重验当前 exact FinalAcceptance，并确认其物化 family 与报告选择的 plan/review 一致，才投影 `VERIFIED`；repair outcome 仍须保留前后原片与失败记录。任何工程 fixture、自动工具成功或离线测试均不代替真实成片或人工接受。
