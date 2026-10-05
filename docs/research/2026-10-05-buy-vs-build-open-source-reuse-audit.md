# Buy vs Build / Open-Source Reuse Audit

Date: 2026-10-05

## Executive Verdict

**AI-VIDEO 应进入“核心自研 + 外围复用”阶段。** 保留 truth、continuity、Router、effect gate、StateCommitter 和 QA lineage；停止把每个 Provider 的 HTTP mechanics、authoring prompt、进度展示和媒体导出技巧都当作独特 domain 重新实现。

但本次没有发现可以安全整包替换 AI-VIDEO runtime 的外部项目。最高价值是 **ADAPT**；真正符合 **PORT** 的是少量纯函数和对应测试，不能把 MIT 可复制等同于服务可直接接入。也没有证明某个完整核心模块可以现在删除。明确的 **DELETE/SHRINK** 候选首先是重复 transport，其次是可证实的重复表达和一次性 glue。

重要纠正：CineCrew 并不是已验证成熟的通用 execution graph；源码是 stage loop + shared context，当前 snapshot 没有 `tests/`。MovieAgent 是研究型 planning 实现，未找到明确 LICENSE。Wind Comic 的强项是产品功能、retake UX、Provider 覆盖及针对性 tests；其 service 同时混入 fallback、prompt 改写、数据库、网络及媒体效果，不能整体借入。

## Scope And Evidence

AI-VIDEO 审计基线是本次 `git fetch origin main` 后确认的 **`4cc1b55d81c881711175c71fa18a1f4d7326c92f`**；当时 `HEAD`、local `main` 与 `origin/main` 相同。读取的是 `git archive origin/main` 的独立源码导出，不是开发 worktree。现有 staged continuity/native-expression changes 不属于该 commit，没有被纳入当前已实现结论，也没有修改。

外部源码以 GitHub REST repository metadata、default-branch shallow clone、`rev-parse HEAD`、实际 LICENSE、dependency manifest、modules 和 tests 交叉核对。以下 stars/forks 是 2026-10-05 观察值，会漂移。活动窗口是 `2026-09-05T00:00:00Z` 之后 default branch 的 commits；100 是 API 第一页下界，不能当总数。

| Repo | Default branch / exact commit | Stars / forks | Latest default commit (UTC) | Recent commits | Actual license | Assessment |
| --- | --- | --- | --- | --- | --- | --- |
| [Wind Comic](https://github.com/ChrisChen667788/wind-comic) | `main` / `82bedb596336fc09ee85240ccf211b0edc53ef4d` | 620 / 72 | 2026-10-04 09:53:47 | ≥100 | MIT | 最新 commit 是 star asset bot；抽样最近非 bot 为 2026-10-01 `c8bd1ac`，有实质 code/activity，但不能由版本号推出质量 |
| [CineCrew](https://github.com/Ironieser/CineCrew) | `main` / `3eac773704088f65ae2e24054c48fccbd4172f2d` | 12 / 1 | 2026-09-29 00:22:48 | 4 | Apache-2.0 | 最新提交是 README；有实现，但不足以认定成熟运行框架 |
| [story-shot-agent](https://github.com/neopen/story-shot-agent) | `main` / `ec7476276ebceb198d79f33da45dc0707b56463c` | 210 / 40 | 2026-09-30 10:14:25 | 52 | MIT | active authoring/workflow implementation，有 tests；dependency surface 较重 |
| [AI Video Production Editor](https://github.com/LudwigKienle/ai-video-production-editor) | `main` / `752cd43d3af6421d2bd6d4ce27f2d9815f7acba3` | 62 / 10 | 2026-10-01 08:58:46 | 33 | GPL-3.0 | UI/workspaces/reference 价值高；默认不复制 code |
| [MovieAgent](https://github.com/showlab/MovieAgent) | `main` / `d84041bed8bc8be460664528d9e9924cdde384ba` | 366 / 44 | 2025-03-26 13:00:46 | 0 | 未发现明确 LICENSE | planning 研究参考；不可推荐复制 code 或 prompt |

`pushed_at` 与 HEAD commit date 不混用：story-shot-agent repository pushed_at 为 2026-10-03，但 default HEAD 仍是 2026-09-30。所有比较限制到以上快照；不承诺后续 main 不再变化。

本轮是静态源码/许可证审计：没有安装第三方依赖、执行其启动脚本、运行其测试、调用视频 Provider、生成媒体、实施迁移或证明 live API compatibility。阅读到的 tests 是覆盖证据，**不是本轮 PASS**。`make harness-inspect` 仅检查 routing；文档完成验证另记于 session record。

## Source Key

下表的 source keys 链接到固定 commit。行号用于定位；完整源码和当前 AI-VIDEO public seam 才是事实。媒体/UI 进一步证据见 [bounded media/UI note](2026-10-05-open-source-media-ui-audit.md)。

| Key | Exact source |
| --- | --- |
| A-transport | [H3 transport L105–175](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/minimax_h3.py#L105-L175), [Hailuo transport L132–205](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/minimax_hailuo.py#L132-L205), [Seedance transport L151–218](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/seedance.py#L151-L218) |
| A-METASO | [METASO adapter](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/metaso_h3.py#L99-L208) |
| A-routing | [continuity requirement routing](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/_video_requirement_routing.py#L310-L699), [execution binding](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/generation_execution.py#L46-L280) |
| A-continuity-tests | [FULL cannot downgrade](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/tests/test_production_shot_router.py#L248-L281), [C2 / exact terminal / bad lineage](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/tests/test_production_shot_router.py#L392-L440), [sequence stale/missing edge](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/tests/test_planning_sequence_continuity.py#L294-L340) |
| A-effect-tests | [permit and unknown-submit tests](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/tests/test_production_minimax_h3.py#L1044-L1129) |
| A-feedback | [feedback orchestrator](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/generation_feedback.py), [runtime repair](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/generation_runtime_repair.py) |
| A-job | [Job service](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/ecommerce_job.py#L57-L74), [Job projections](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/ecommerce_job_contracts.py#L481-L545) |
| A-media | [legacy FFmpeg helpers](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/ffmpeg_tools.py), [exact terminal extraction](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/video_artifact.py#L164-L300), [Vidu pinned-public download](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/vidu_download.py) |
| A-captions | [caption normalization/timing](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/captions.py), [voice provider contract](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/audio.py#L598-L615), [MiniMax speech](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/minimax_speech.py) |
| A-prompt | [remote prose](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/_remote_video_native_prompt.py#L62-L126), [Vidu versioned prose](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/_vidu_prompt.py#L46-L161), [compiler](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/video_compiler.py) |
| A-delivery | [accepted-render delivery packager](https://github.com/Reggie-sun/AI-VIDEO/blob/4cc1b55d81c881711175c71fa18a1f4d7326c92f/src/ai_video/production/delivery_packager.py) |
| W-codec | [MiniMax wire helpers](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/minimax-video-api.ts#L112-L252), [codec tests](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/tests/v12-402-minimax-h3.test.ts) |
| W-clients | [MiniMax service](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/minimax.service.ts#L203-L410), [Seedance CV service](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/seedance.service.ts#L94-L173), [Vidu](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/vidu.service.ts), [Kling](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/kling.service.ts), [ComfyUI upload](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/comfyui.service.ts#L185-L202) |
| W-new-clients | [Wan](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/wan.service.ts), [Veo](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/veo.service.ts#L102-L177), [selfhost](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/selfhost-video.service.ts) |
| W-retake | [pure retake plan](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/segment-retake.ts), [runner](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/segment-retake-run.ts), [stitch service](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/segment-retake.service.ts), [UI](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/components/project/segment-retake-panel.tsx) |
| W-export | [pure export filter plans](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/video-export.ts#L10-L141), [tests](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/tests/v3-5-video-export.test.ts), [export service](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/video-export-service.ts) |
| W-subtitle | [subtitle filter/style helpers](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/subtitle-burn.ts), [escape tests](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/tests/v3-5-subtitle-burn.test.ts), [estimated subtitle service](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/subtitle.service.ts) |
| W-voice | [TTS](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/tts.service.ts), [voice clone](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/voice-clone.service.ts), [ElevenLabs example](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/tts-providers/example-elevenlabs.ts), [lipsync clients](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/lipsync-providers.ts) |
| W-orchestrators | [simple agents](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/agent-orchestrator.ts#L104-L135), [hybrid routing/retry](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/hybrid-orchestrator.ts#L144-L220), [agent modules](https://github.com/ChrisChen667788/wind-comic/tree/82bedb596336fc09ee85240ccf211b0edc53ef4d/services/agents), [character context](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/producer-enhance.ts) |
| W-state | [Zustand project store](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/stores/projectStore.ts), [Yjs persistence](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/yjs-persistence.ts) |
| C-pipeline | [stage loop](https://github.com/Ironieser/CineCrew/blob/3eac773704088f65ae2e24054c48fccbd4172f2d/src/pipeline.py#L69-L93), [story editor](https://github.com/Ironieser/CineCrew/blob/3eac773704088f65ae2e24054c48fccbd4172f2d/src/agents/story_editor/story_editor_agent.py#L35-L89), [blueprint](https://github.com/Ironieser/CineCrew/blob/3eac773704088f65ae2e24054c48fccbd4172f2d/src/schemas/blueprint.py#L54-L110), [engine modules](https://github.com/Ironieser/CineCrew/tree/3eac773704088f65ae2e24054c48fccbd4172f2d/src/engine) |
| S-graph | [WorkflowPipeline](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/src/penshot/neopen/agent/workflow/workflow_pipeline.py#L39-L56), [compile/checkpointer](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/src/penshot/neopen/agent/workflow/workflow_pipeline.py#L250-L275), [graph tests](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/tests/workflow/test_workflow_orchestrator.py#L77-L122) |
| S-story | [authoring/workflow nodes](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/src/penshot/neopen/agent/workflow/workflow_nodes.py), [checker/pass/retry loop](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/src/penshot/neopen/agent/workflow/workflow_nodes.py#L910-L1005), [character/scene consistency contract](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/src/penshot/neopen/agent/continuity_guardian/consistency_contract.py#L23-L45) |
| S-state | [Redis/in-memory tasks](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/src/penshot/neopen/task/task_repository.py#L24-L105), [reset recovery tests](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/tests/task/test_task_lifecycle_service.py#L109-L120) |
| M-planning | [screenplay→scene→shot](https://github.com/showlab/MovieAgent/blob/d84041bed8bc8be460664528d9e9924cdde384ba/movie_agent/run.py#L139-L257), [planning prompt](https://github.com/showlab/MovieAgent/blob/d84041bed8bc8be460664528d9e9924cdde384ba/movie_agent/system_prompts.py#L276-L355), [parser/logging](https://github.com/showlab/MovieAgent/blob/d84041bed8bc8be460664528d9e9924cdde384ba/movie_agent/base_agent.py#L40-L50) |
| E-UI | [workspaces](https://github.com/LudwigKienle/ai-video-production-editor/tree/752cd43d3af6421d2bd6d4ce27f2d9815f7acba3/workspaces), [components](https://github.com/LudwigKienle/ai-video-production-editor/tree/752cd43d3af6421d2bd6d4ce27f2d9815f7acba3/components), [edit/export workflow](https://github.com/LudwigKienle/ai-video-production-editor/blob/752cd43d3af6421d2bd6d4ce27f2d9815f7acba3/docs/ui-production-workflow-guide.md#L152-L194) |

## Module Matrix

成本是适配面的相对估计，不是工期承诺。Low = 纯函数/测试；Medium = 单 adapter/UI seam；High = 跨 effect、durability 或 renderer 边界。PORT 表示静态候选，不表示已经完成安全资格。

| AI-VIDEO Area | Current Owner | External Project | External Module | Verdict | Why | License Risk | Migration Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Authored truth / intent | `GenerationIntent`, `ProviderNeutralVideoRequirement` | 全部 | Blueprint / script / prompt JSON | KEEP | proposal 不等于 approved/hash-bound intent | 不引入 | 无迁移 |
| Planning/readiness | `VideoPlanner`, `ShotReadinessGate` | CineCrew / story-shot-agent | stage loop / graph checker | KEEP | 外部 stage/checker 没有现有执行前 truth/lineage gate | 不引入 | 无迁移 |
| FULL / exact terminal / C2 | `ContinuityTransitionPolicy v2`, `PreviousShotState`, `CausalStateChange`, `HardCutKeyframeBinding` | 全部 | character DNA / scene history / checker booleans | KEEP | 阻止 soft-reference 冒充 exact conditioning；A-routing/A-continuity-tests | 不引入 | 无迁移 |
| Selection / reopen | Router profiles/capabilities, `ProviderBoundVideoRequest`, `GenerationDecisionExecutionBinding` | Wind Comic | engine chain / service default / health cache | KEEP | 选择和 paid effect 不能转给 borrowed service | 不引入 | 无迁移 |
| Permit/budget/unknown recovery | Paid Gate / committer | Wind / story-shot-agent | retries / status reset | KEEP | query retry 不等于 unknown POST 可重复；A-effect-tests | 不引入 | 无迁移 |
| API HTTP mechanics | 每 adapter 的 `Httpx*Transport` | Wind Comic | service→pure wire helper 分离 (W-codec) | DELETE/SHRINK | A-transport 有实际近重复；收敛现有 httpx mechanics，外部仅借边界设计 | reference 无 code 引入 | Medium |
| METASO H3 | `MetasoH3VideoProvider` | Wind Comic | `minimax.service.ts` | KEEP | 不同 gateway/response/egress；main 已含 I2V FIRST/optional LAST，不可误判仍仅 R2V | 无直接借入 | 无迁移 |
| Official MiniMax H3 | `MiniMaxH3VideoProvider` | Wind Comic | `lib/minimax-video-api.ts` | ADAPT | version/path/status test cases 有用；外部未知 status→pending、duration clamp、ref slice 不能复制为项目语义 | MIT notices | Low/Medium |
| Hailuo | `MiniMaxHailuoVideoProvider` | Wind Comic | `minimax.service.ts` | ADAPT | 仅 v1 wire coverage；不借 H3→legacy→Fast fallback | MIT notices | Medium |
| Seedance | `SeedanceVideoProvider` (Ark task API) | Wind Comic | `seedance.service.ts` (Volcengine CV/Volc4) | REFERENCE | 同品牌不是同 API；req_key/签名不可替换当前 Ark request/identity | MIT 可复制，但不适配当前 seam | High |
| Vidu Q3 | `ViduVideoProvider` / profile / subjects / download | Wind Comic | `vidu.service.ts`, `qyt-vidu.service.ts` | REFERENCE | 不同 endpoint/model coverage；当前 named subjects、extension、paid lineage 更完整 | MIT | Medium/High |
| Kling | main 未发现正式 Kling Provider adapter | Wind Comic | `kling.service.ts` | ADAPT | 有 API payload/parse 参考；必须新增显式 capability/profile/permit adapter，不能由 UI key 存在启用 | MIT notices | High；需求触发 |
| Local ComfyUI | `ComfyUIVideoProvider`, `comfy_client.py` | Wind Comic | `comfyui.service.ts` | KEEP | 现有 sealed workflow/components/node hashes 和 intent/permit 更强；外部上传任意 URL 不可替换 | MIT，但不整体借 | 无迁移 |
| Wan / Veo / selfhost | 未发现对应正式 production adapters | Wind Comic | `wan.service.ts`, `veo.service.ts`, `selfhost-video.service.ts` | REFERENCE | endpoint dialect 参考；不要因已有 service 扩充 Provider scope；Veo 有模型 fallback | MIT | 现在不迁移 |
| Upload / result fetch | `remote_media.py`, adapter upload/fetch, `vidu_download.py` | Wind Comic | `uploadImageFromUrl`, composer download | KEEP | 当前 exact egress/hash/containment/public-DNS-pinning 不应降级为任意 URL fetch | MIT，但拒绝借入 unsafe 路径 | 无迁移 |
| Poll / response variants | provider-specific parser + task observation | Wind Comic | `pollPath`, `parsePollResponse` | ADAPT | 借边界案例/枚举，保留 strict schema/task identity/redaction；不把 unknown 自动当 pending | MIT notices | Low |
| Quality rejection / new attempt / abandonment | feedback / intervention / runtime repair / committer | Wind Comic | retake runner | KEEP | runtime repair 与 quality intervention 保护的事实不同，不能并为一个 retry | 不引入 | 无迁移 |
| Shot→retake→compare→activate | 尚缺完整 product retake Canvas | Wind Comic | `segment-retake-panel.tsx`, inspector | ADAPT | UX 可借；take 数据映射现有 immutable attempts，activate 只调 committer | MIT notices | Medium |
| Segment interval planning | `ResolvedTimeline` / future repair proposal seam | Wind Comic | `lib/segment-retake.ts` | ADAPT | useful frame-grid / min-generation vs trim 分离；浮点/24fps/3s defaults 必须替换为当前 typed bounds | MIT notices | Medium |
| Segment stitch executor | composition / derivative candidate / QA owners | Wind Comic | `segment-retake.service.ts`, `segment-retake-run.ts` | REFERENCE | checks 可借，DB record/take writer 和 process-local lock 不借 | MIT | High |
| Canonical timeline | `ResolvedTimeline` / resolver | Wind / Editor | timeline arrays / edit state | KEEP | order/frame/sample/source-trim 唯一 owner | GPL 额外阻止直接借 Editor | 无迁移 |
| Default renderer/composition | HyperFrames adapter | Wind Comic | `video-composer.ts` | KEEP | compositor 混入独立时序/网络；还依赖 deprecated fluent-ffmpeg | MIT + dependency concerns | 无整包迁移 |
| Platform aspect filter | 新增 optional delivery derivative seam | Wind Comic | `lib/video-export.ts::buildAspectFilter` | PORT | 小型纯 filter builder + tests；需参数验证和 TS→Python，不能直接换成片 | MIT notices | Low core / Medium integration |
| Animated export argv | 新增 optional derivative seam | Wind Comic | `animFormatPlan` | PORT | 纯 codec plan 可借；当前无明确 GIF/WebP/AVIF需求，先不做 | MIT；编码器/build 另审 | Low，但低当前 ROI |
| Export execution | delivery/export owner | Wind Comic | `video-export-service.ts` | ADAPT | argv spawn 模式可借；overwrite、路径、超时、probe、lineage与新导出版 QA 另包 | MIT notices | Medium |
| Subtitle timing | `CaptionTrack` / normalized alignment / timeline binding | Wind Comic | `subtitle.service.ts` | KEEP | estimated chars/duration 比现有 samples/alignment 弱 | 不引入 | 无迁移 |
| Subtitle filter path escape | optional FFmpeg subtitle export adapter | Wind Comic | `escapeSubtitlePath` + tests | PORT | 纯字符串 helper；当前 HyperFrames 无消费 seam，不能为复用而新增 burner | MIT notices | Low；延后 |
| Subtitle visual presets | existing caption styles / future export styles | Wind Comic | `subtitle-burn.ts` presets / `styleToForceStyle` | ADAPT | 可借字体/安全区 UX，先校验实际 font licensing/availability 与 field escape | MIT + fonts independently licensed | Low/Medium |
| TTS | `VoiceAssetProvider`, `VoiceGenerationRequest`, MiniMax Speech | Wind Comic | `tts.service.ts`, TTS registry | ADAPT | 只借明确所选 Provider 的 wire client；不借 registry priority/fallback 与字符时长估计 | MIT notices | Medium |
| Voice cloning | voice authorization / provenance / identity QA | Wind Comic | `voice-clone.service.ts` | ADAPT | 上传/clone endpoint 可供独立 adapter；成功 voice_id 不等于合法授权或 identity PASS | MIT；声音权利另审 | High；需求触发 |
| Lipsync | voice/video candidates + effect/evidence owners | Wind Comic | `lipsync-providers.ts`, `lipsync.service.ts` | ADAPT | Kling/Sync.so/Hailuo wire 参考；applied=false返原片不能成为成功 repair | MIT + providers/model assets另审 | High；需求触发 |
| Narrative roles | Director Skill / approved authoring | CineCrew | story editor / director / staging roles | ADAPT | 仅适配 authoring stages，并将其输出限定为 proposal；不借下游 ProductionOperator 执行权 | Apache-2.0 notices/changes | Medium |
| Lightweight orchestration | Codex workflow + feedback + Job services | CineCrew | `src/pipeline.py`, `src/engine` | REFERENCE | stage loop 缺少 tests 和可迁移恢复证据；现有 AI Job projection 也不是通用 authoring graph | Apache-2.0 | 当前不引入 |
| Authoring graph | future authoring-only workflow | story-shot-agent | `WorkflowPipeline` / LangGraph | ADAPT | 图/checkpointer 已实现，未验证为成熟生产 engine；未来分支/人工暂停需求成立时适配 | MIT + dependency notices | High；条件性 |
| Story→scene→beat→shot | open-video / Director / Storyboard | story-shot-agent / CineCrew | nodes / blueprint / story editor | ADAPT | 可借拆解、camera/beat/character inventory模板，输出校验后写既有 schema | MIT / Apache-2.0 | Medium |
| Film planning prompts | Director authoring | MovieAgent | `run.py`, `system_prompts.py` | REFERENCE | 层次拆解有启发；无明确 LICENSE，prompt文本也不复制 | No license | Low design reference |
| Character/history context | authoring artifacts / accepted source evidence | CineCrew / story-shot-agent / Wind | Blueprint / consistency contract / character Bible | ADAPT | 可作为 character/outfit/props 的 authoring提示，不能成为 PreviousShotState truth | Apache / MIT notices | Medium |
| Product Canvas / timeline / review | new UI read model + command facade | Editor | workspaces / components | REFERENCE | 借交互原则，独立实现；不可复制 GPL components、utils、schema implementation | GPL-3.0 | High product work |
| Shot inspector / generation progress | Provider Console / future Canvas | Wind Comic | shot inspector / frame inspector / progress panels | ADAPT | React UX可适配，但所有状态来自 canonical read projections | MIT notices | Medium |
| Durable project/job state | Registry / Manifest / attempts / StateCommitter | 全部 | SQLite/Yjs/JSON/task state | KEEP | 不用 loose project/task state 替换 exact snapshots/activation | 多种许可，不引入 | 无迁移 |
| Frontend view state | future Canvas ephemeral store | Wind Comic | Zustand / Yjs integration | ADAPT | 仅 selection/viewport/draft/UI progress；不复制 Yjs DB owner或让store写accepted truth | MIT；依赖另审 | Medium |
| Future task persistence | current Job/feedback projections; no generic scheduler identified | story-shot-agent | task repository / orchestrator | REFERENCE | 未发现 AI 当前可删的通用 task repository；借进度 UX 时避免引入平行 production lifecycle | MIT；不复制此 owner | 当前不迁移 |
| Frame strip / thumbnail | console/media derived display | Wind Comic | `frame-strip.ts`, frame-strip service | ADAPT | 展示计划/采样UX有价值；extractor绑定现有安全media seam | MIT notices | Low/Medium |
| Exact frame / probe / MIME | video_artifact / audio / visual_media | Wind / Editor | frame/ffprobe helpers | KEEP | accepted terminal准确性/held-fd/hash是核心，不等于thumbnail工具 | MIT/GPL；不借核心 | 无迁移 |
| Repeated FFmpeg mechanics | legacy + MCP + production helpers | Wind Comic | pure plan/argv separation | DELETE/SHRINK | 可统一兼容的probe/process plumbing；保留每个domain验证，不能统一“近似末帧”与exact terminal | reference only | Medium |
| Waveform / keyframe browsing | future UI display only | Editor / Wind | UI/media visualizations | REFERENCE | 当前无足够证据证明可直接PORT的独立包；GPL Editor只借UX | GPL / MIT | product需求成立后 |
| Prompt expression duplication | versioned native compilers | Wind / CineCrew | prompts separated from runner | DELETE/SHRINK | 合并真正重复的表达helper；保留 /1 vs /4、Provider语法及unsupported结果 | reference only | Medium；A/B后 |
| Records / docs machinery | canonical baseline / matrix / records / Harness | 全部 | readmes / plain JSON progress | KEEP | 外部没有替代验收/evidence治理的实现；可收缩重复叙述，不删history/gates | 无引入 | 内容治理，非runtime迁移 |

## Provider Client Findings

**没有一个完整 external Provider service 满足当前 PORT 的安全边界。** AI-VIDEO 已使用现成 `httpx`，不是在重造 HTTP library。重复的是包装与 mechanics：H3、Hailuo、Seedance 的 request/response dataclass、client creation、request/stream/close 和一部分 bounded JSON/id parse。它们可收敛成内部薄 transport，provider codec仍分开。

必须保留“submit 与 poll 分离”：borrowed client 的 `generateVideo = submit + internal polling` 隐藏了 effect fence、unknown outcome 和 canonical job ownership。可读 poll 的 transient retry 由当前 owner有界决定；不得把 5xx/timeout 后的 POST 当成无效果。正常 response schema、declared rejected outcome 与 unknown outcome保持现有区分。

不同 API 不能因同名替换：Wind Seedance 使用 `visual.volcengineapi.com`、Volc4、`CVSync2AsyncSubmitTask` / req_key；AI-VIDEO Seedance 是 Ark task contract。Wind Vidu service 的 endpoint/model breadth 与当前 Q3/subjects/extend不同。Wind MiniMax 的 `buildCreateRequest` 存在 ref `.slice()`、duration clamp、环境model默认及ref/first-frame选择；`parsePollResponse` 将未知status当pending。可以参考 test fixtures，但不能覆盖已经sealed的exact request。

当前 `MetasoH3VideoProvider` 复用 H3 部分 transport，又有 gateway upload/body/result边界，main 已增加 `IMAGE_TO_VIDEO`、first frame 和optional last frame。它仍不是官方 MiniMax adapter，不能假设更换 host即可复用全部response/credential逻辑。Kling/Wan/Veo/selfhost属于未来 capability扩充，不是“删除当前重复代码”的机会。

## Segment Retake And Repair

推荐 **Shot → selected range/whole-shot retake proposal → exact preview → authorized new attempt → compare → explicit activate**。用户体验可借 Wind；每一步后端状态仍由 AI-VIDEO现有 owners决定。

Wind纯plan区分 `generateDurationS` 与 `trimFromS/trimToS`，并按frame grid保持总时长，值得ADAPT。但默认24fps、3秒min、浮点秒、provider默认上限不可变成新的timing/capability owner。输入应来自 `ResolvedTimeline` 的整数frame/sample和已selected Provider bounds。

`segment-retake-run.ts` 会generate patch、FFmpeg stitch、检查视频stream duration/decoded frame count、写persistent media并`recordSegmentTake`。这是实际实现，优于只有README；仍缺AI-VIDEO的accepted-source、unknown effect、exact semantic no-regression和sole writer语义。只传首帧不能保证与尾段splice自然连续。合成后patch是新的derivative candidate，不能冒称raw Provider continuity PASS。range repair还必须检查对白/动作/axis与两端seams；仅时长相等不允许activate。

runtime repair、quality intervention、evidence repair、abandonment保留分流；unknown停止。UI“再试一次”应呈现阻断理由和合法恢复选项，不能清理历史失败或重置消耗。

## Voice And Subtitle Findings

MiniMax Speech已有显式 `VoiceAssetProvider`、opaque credential、WAV response/provenance与预算/permit边界，Wind TTS没有证明更强。新 Provider需求出现时，借selected client's payload/status知识，包在现有contract后，不整包引入TTS registry的priority/auto-discovery/failed fallback。

Wind `example-elevenlabs.ts` 返回字符数估算duration/subtitle，且使用环境key/raw响应错误；它是example，不能标为mature timing SDK。voice clone/lipsync integrations可ADAPT为新capability，声音使用授权、source hashes、derived video evidence仍独立。`lipsync-providers.ts` 的failure可返原video + `applied=false`；在hard lipsync requirement下应阻断，而不是“有videoUrl所以成功”。本轮未验证这些API当前账号/模型可用。

字幕alignment/sample timing、caption fingerprints、normalization和timeline binding全部KEEP。外部可以贡献style presets、safe zones、format/escaping tests；`escapeSubtitlePath`是小型PORT候选，但FFmpeg escaping不是SSRF/containment或完整filter-injection防护。现有HyperFrames caption路径没有消费它，先别新建第二subtitle burner。

## Agent And Authoring Findings

CineCrew 的 role separation 值得 ADAPT 为 authoring 模板，但 stage loop 缺少可转移的回归与恢复证明。其完整 pipeline 还包含 [ProductionOperator / opt-in keyframe 与 clip 执行](https://github.com/Ironieser/CineCrew/blob/3eac773704088f65ae2e24054c48fccbd4172f2d/src/pipeline.py#L297-L311)，不能整体称为 proposal-only。AI-VIDEO 仅适配 authoring stages，并在自己的边界上将输出限定为 proposal。story-shot-agent 确有 LangGraph nodes / edges / checkpointer；其 Redis / in-memory task repository、task reset 和 checker→pass/retry 不进入 Production，也未验证为可直接复用的成熟生产 engine。

AI-VIDEO 的缺口是 product authoring driver / 一部分交互封装：`GenerationFeedbackOrchestrator` 与 `EcommerceProductionJobService` 已有明确生产职责，后者从 canonical state 投影安全 next action，并不持久化自己的 Job lifecycle，也不是通用 authoring graph。通用 sequence adapter 的当前仓库 caller 仍主要是 tests；引入外部 authoring 图也不能据此宣称生产 driver 已验证。

最合适的借法是 screenplay→scene→beat→shot 的分工、camera候选、character/outfit/prop inventory和context模板，输出只有proposal，再投影现有Character/Scene/Shot/Storyboard/GenerationIntent。MovieAgent无license，连system prompt原文也只阅读参考，不直接复制。绝不把agent evaluator boolean转换成AI-VIDEO QA PASS。

## Continuity Complexity Assessment

**合理且应保留的复杂度**：accepted source activation、source execution binding、完整causal column、TYPED_HASH identity、exact terminal vs derived C2、FULL fail-closed、Router selection/reopen、one-use permit、unknown fence、no-regression/evidence lineage。这些保护不同事实，不是同一事实的任意多份表达。

这不是“别人简单，所以我们过度设计”。当前tests明确防止FULL→soft downgrade、缺C2、wrong target/lineage、exact terminal被derived frame替换、stale selection和5xx/invalid 2xx后的重复submit。历史[真实root-cause record](../record_for_agent/2026-10-03-full-continuity-capability-root-cause.md)记录了`previous_shot_state=None → Planner NONE → Ref2VA`以及raw `OPENING_STATE_RESET`的证据边界；[route authority record](../record_for_agent/2026-10-04-sequence-route-authority.md)记录public合法候选可被caller重新选择的复现。这些说明复杂度曾针对实际失效路径，不能仅借prompt-as-truth替代。没有证据称每一个validator都曾独立阻止live事故。

**可收缩的复杂度**：同一HTTP mechanics、相同safe primitive、native prompt中重复的state/endpoint表达、前端ephemeral progress重复存储。读时重验hash与写时重验effect是不同trust boundary，不能为少一份JSON删掉。版本兼容记录、Manifest和Registry重复identity字段也不能只看字段名就合并。

main的remote/Vidu表达器仍拒绝不能表达的TYPED_HASH；这是truth identity→human-readable表达的实际gap，不说明应该取消TYPED_HASH。本工作区已有另一窗口staged修复，本审计不使用、修改或评价其完成状态；后续迁移应以其正式落地后新main再校准。

## Top 10 Reuse Opportunities

ROI按现有重复成本、复用隔离难度和实际用户收益排序；新增产品能力的代码删除量为0，不能伪装成现有代码收缩。#1是reuse现有library与外部边界设计，不是复制外部service。后续条目是条件性backlog，不是本轮迁移授权。

### #1 Thin Provider Transport

Verdict: DELETE/SHRINK

Benefit: 收敛H3/Hailuo/Seedance重复HTTP包装，统一client关闭、stream/size/error redaction practices。
AI-VIDEO code removed: A-transport中重复request/response/client mechanics；准确范围要保留Vidu DNS-pinned downloader和METASO特殊stream。
Boundary retained: Router、compiler、profile、egress、permit、submit outcome、provider task parser、StateCommitter全部保留。
Estimated integration surface: 3个现有adapter + 一个内部transport seam + existing injected fake-transport tests；中等。
Main risks: 不能把所有request自动retry；不能弱化no-redirect、size bound、credential redaction或改变sealed payload。
Repo/license/mode: Wind W-codec (MIT)仅REFERENCE分离设计；现有httpx继续复用，不引入Wind service。

### #2 Shot Retake / Takes Compare UX

Verdict: ADAPT

Benefit: 将已有attempt/repair能力变成用户可操作的Shot流程，避免未来再设计一套take生命周期。
AI-VIDEO code removed: 现阶段0；未来避免新增一次性retake控制脚本。
Boundary retained: canonical attempts、paid admission、unknown fences、QA、committer activation。
Estimated integration surface: Wind W-retake UI + AI read projections / command facade；中等。先whole-shot，range repair后置。
Main risks: optimistic activation、rollback改写history、duration PASS冒充semantic PASS。
Repo/license/mode: Wind Comic MIT；复制UI代码保留notices，后端runner只REFERENCE。

### #3 Screenplay / Scene / Beat / Shot Authoring Templates

Verdict: ADAPT

Benefit: 减少Director重复prompting，复用character inventory、scene segmentation、beat/camera分工。
AI-VIDEO code removed: 只收缩确认重复的authoring模板；不删GenerationIntent或compiler。
Boundary retained: approved artifacts、existing validators、ordered Storyboard、neutral intent。
Estimated integration surface: S-story / C-pipeline中明确的authoring节点与现有open-video输入输出映射；中等。
Main risks: 把未经review的LLM JSON直接写入canonical state；复制schema产生第二truth model。
Repo/license/mode: story-shot-agent MIT / CineCrew Apache-2.0；保留对应notices，Apache改动标记。

### #4 Aspect-Fit Derivative Export

Verdict: PORT

Benefit: 借已存在且有targeted tests的contain/cover/blur-pad filter计划；是最简单的实际code migration入口。
AI-VIDEO code removed: 当前0；填补delivery derivative seam，避免重写export filter recipes。
Boundary retained: ResolvedTimeline / HyperFrames / exact original final artifact与acceptance保持独立；新尺寸导出版另行review。
Estimated integration surface: `buildAspectFilter` + tests移植、dimension validation、已有FFmpeg seam、新derivative adapter；纯核心低、完整接入中。
Main risks: cover裁掉角色/字幕/商品；blur-pad影响观看；继承原片PASS到新bytes；重编码音频/时序漂移。
Repo/license/mode: Wind W-export，MIT PORT小函数；service只ADAPT。首版contain且无新subtitle默认。

### #5 Subtitle Escaping / Format Cases

Verdict: PORT

Benefit: 借Windows drive colon、反斜线、单引号等已测试案例。
AI-VIDEO code removed: 当前0；现有HyperFrames不需要该helper。
Boundary retained: CaptionTrack timing/style/hash / no-subtitle requirements。
Estimated integration surface: `escapeSubtitlePath` + existing tests；低；实际subtitle export存在时才接入。
Main risks: filter escaping不等于path containment；`styleToForceStyle`用户字段还需单独验证；字体另审。
Repo/license/mode: Wind W-subtitle MIT；不借estimated timing。

### #6 TTS / Voice Client Coverage

Verdict: ADAPT

Benefit: 未来明确新增所选TTS/clone Provider时，借wire grammar与response cases，避免盲写client。
AI-VIDEO code removed: 已有MiniMax Speech不删除；仅收缩重复transport，避免重复client探索。
Boundary retained: VoiceAssetProvider、opaque credential、usage authorization、permit、probe、voice identity QA。
Estimated integration surface: 单selected client + existing voice contract；中等，clone更高。
Main risks: environment credential、raw error、priority fallback、duration估计；example-elevenlabs不能当成熟SDK。
Repo/license/mode: Wind W-voice MIT；API grammar需官方current verification。

### #7 Job Progress And Project UI Projection

Verdict: ADAPT

Benefit: 借Shot卡片、阶段/进度/阻断reason展示，直接投影现有Job next-action和attempt状态。
AI-VIDEO code removed: 不删Job服务；避免未来多套ephemeral task trackers。
Boundary retained: Registry/Manifest/committer，UI只持selected/viewport/draft。
Estimated integration surface: Wind W-state UI pattern + AI Job/Console DTO；中等。
Main risks: localStorage/Yjs status被当durable成功；网络恢复时reset task消除unknown。
Repo/license/mode: Wind MIT；不移植其SQLite/Yjs production owner。

### #8 Frame Strip / Selected-Range Planning

Verdict: ADAPT

Benefit: 展示帧定位与范围选择，用既有media extractor；生成时长和替换时长清晰分离。
AI-VIDEO code removed: 当前0；避免新UI重复写sampling/time conversion。
Boundary retained: accepted exact terminal与thumbnail严格分开；只消费ResolvedTimeline整数frame。
Estimated integration surface: Wind frame-strip/retake pure planners + derived-frame cache/read model；低到中。
Main risks: float rounding与fps默认；thumbnail拿作C2/terminal truth；range splice的semantic continuity未评估。
Repo/license/mode: Wind MIT；适配而非搬入filesystem/URL services。

### #9 Authoring Role Pipeline / Optional Graph

Verdict: ADAPT

Benefit: 多branch或human pause需求成立后，借CineCrew角色分工、story-shot-agent的现成图接口；避免新造通用engine。
AI-VIDEO code removed: 只替换未来重复authoring glue；现有feedback/Job/committer不删除。
Boundary retained: agent输出proposal；graph/checkpoint无Provider/QA/activation权限。
Estimated integration surface: authoring-only边界；使用真正LangGraph library时另审其version/license/dependencies；高。
Main risks: 为串行任务引入graph、Chroma/Redis等重依赖；checkpointer变第二Manifest。
Repo/license/mode: CineCrew Apache / story-shot-agent MIT；CineCrew runner本身REFERENCE，非成熟engine PORT。

### #10 Lipsync Integration Knowledge

Verdict: ADAPT

Benefit: 未来explicit lipsync需求时借Kling/Sync.so/Hailuo client shape和applied/unsupported UX。
AI-VIDEO code removed: 当前0；不因open source覆盖而新增不需要的Provider。
Boundary retained: audio/video input lineage、paid gate、new attempt、exact output与voice/semantic QA。
Estimated integration surface: selected-provider wire client→AI adapter；高，先最小真实需求再实现。
Main risks: 返回原video当成功、模型不可用、声音身份退化、remote URL/secret泄漏、重新提交。
Repo/license/mode: Wind MIT；local2D/模型资源许可证不继承root MIT，单独核验。

## Overengineering Audit

| AI-VIDEO module | Is it overengineered? | Reduction target | How external projects work | Change now? |
| --- | --- | --- | --- | --- |
| `minimax_h3.py`, `minimax_hailuo.py`, `seedance.py` transport | 是：近重复mechanics有源码证明 | 一个薄request/stream/close implementation；typed provider codec/permit仍各自保留 | Wind有pure wire helper，但service更耦合；不抄service | H3 A/B封存后，单独重构 |
| Provider poll/upload/fetch | 部分；不能整体判断 | 通用大小/parse primitives只在语义相同处共用；URL/egress验证保留 | 外部fetch/poll常内部循环、raw URL与宽松parser | 有确切重复再改；当前parser更强不降级 |
| `_remote_video_native_prompt.py`, `_vidu_prompt.py`, `_compile_neutral_prompt` | 表达helper重复；版本层次不等于重复owner | 共用可验证state/endpoint到prose的leaf helper；保留Provider/version unsupported行为与hash | 外部prompt templates很轻但无accepted truth | 活跃staged修复先完成；不要抢同file |
| feedback / ecommerce Job / MCP wrappers | 未证明整体过度设计 | 只收缩重复DTO/dispatch/ephemeral progress；保留prepare/execute/repair/evidence各职责 | CineCrew stage loop很轻，story graph额外引入task lifecycle | 不为“更短”替换；需求和caller缺口明确后 |
| repair flows | 关键区别合理 | UX共用，runtime/evidence/quality repair不混并；同attempt lineage保持 | Wind retake runner统一拼接与DB take，弱于existing fences | UX后续ADAPT，backend KEEP |
| FFmpeg/probe/frame helpers | plumbing散落；非所有重复都冗余 | 公用process/probe leaf；domain evidence guard各自保留 | Wind composer也有shell/下载耦合，不比当前安全 | A/B后，定向确认caller |
| legacy `extract_last_frame` vs production terminal | 两者不同contract；不能贸然合并 | legacy近似末帧fallback不得借入production；生产exact-frame路径KEEP | 外部末帧常秒offset/default，适合preview而非exact truth | 现在不删legacy兼容路径 |
| Manifest/Registry/execution serialization | 没有证据支持删减owner | 只centralize真正重复canonical encoding primitive；保留schema/domain hashes和write/read重验 | 外部loose JSON/TTL reset易写，但不保effect/evidence | 不用宽松serializer替代 |
| docs / records / experiment machinery | 有流程成本；不能由文件数推出过度设计 | baseline只放current summary/anchors，records保持history；例行状态无需重复长叙述 | 外部readme/plain progress不提供相同audit能力 | 内容治理可后续做；无证据删除历史 |
| Proposed new universal orchestrator | 若现在新增，容易过度设计 | authoring-only role pipeline；真正branch/checkpoint需求才引入成熟graph library | CineCrew非graph，story-shot-agent有graph但重依赖 | 现在不建新production engine |

raw file行数提示拆分机会但不构成删减依据：本snapshot Hailuo 1049、Seedance 1124、audio 1270、video_artifact 1062、captions 844、video_compiler 833；包含不同domain验证/compatibility，不能用LOC目标移除protection。

**Safe full-module deletion found: none.** DELETE/SHRINK是mechanics/重复表达的有界候选，不是可立即执行的删除清单。

## License Audit

| Repo | License | Can copy code? | Attribution required? | Copyleft risk? | Recommended reuse mode |
| --- | --- | --- | --- | --- | --- |
| [Wind Comic LICENSE](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/LICENSE) | MIT | 可以在许可范围内复制/移植 | 保留copyright + permission/license notice；翻译成Python也不豁免 | root code无强copyleft；依赖/资源另查 | 小纯函数PORT，service ADAPT，unsafe paths拒绝 |
| [CineCrew LICENSE](https://github.com/Ironieser/CineCrew/blob/3eac773704088f65ae2e24054c48fccbd4172f2d/LICENSE) | Apache-2.0 | 可以在许可范围内复制/修改 | 保留license/相关notices；修改文件标记；有适用NOTICE需保留 | root code无强copyleft；专利/商标条款仍适用 | authoring roles ADAPT、engine REFERENCE |
| [story-shot-agent LICENSE](https://github.com/neopen/story-shot-agent/blob/ec7476276ebceb198d79f33da45dc0707b56463c/LICENSE) | MIT | 可以在许可范围内复制/移植 | 保留copyright/license | 依赖license不因root MIT消失 | prompts/workflow ADAPT，production task lifecycle不借 |
| [Editor LICENSE](https://github.com/LudwigKienle/ai-video-production-editor/blob/752cd43d3af6421d2bd6d4ce27f2d9815f7acba3/LICENSE) | GPL-3.0 | 本任务默认不允许合并复制 | 接受GPL时需满足license、source等适用义务；单纯署名不够 | 分发combined/derived implementation有copyleft义务风险 | REFERENCE交互/理念，独立实现 |
| [MovieAgent tree](https://github.com/showlab/MovieAgent/tree/d84041bed8bc8be460664528d9e9924cdde384ba) | 未发现明确LICENSE | 不建议复制code/prompt | 署名不产生复制许可 | 非“copyleft”，是缺乏permission | REFERENCE理念；获得明确许可前不PORT |

许可判断参考[MIT正文](https://opensource.org/license/mit)、[Apache-2.0 §4](https://www.apache.org/licenses/LICENSE-2.0)、[无许可证说明](https://choosealicense.com/no-permission/)。本轮AI-VIDEO tracked snapshot未找到root LICENSE/NOTICE；未来对外分发前应明确项目自己的license policy与third-party notices，不假设自动继承某个外部项目license。

root LICENSE不自动覆盖模型weights、fonts、sample媒体或vendored third-party files。FFmpeg binary的build/codec许可须单独处理。本轮没有新依赖，亦未声称完成dependency CVE/SBOM audit。

## Security And Supply Chain

每个PORT/ADAPT候选均经过静态检查，但不是已qualified的组件。以下是具体迁移阻断项及边界：

| Candidate | Dependencies / effects | Static concern | Required boundary |
| --- | --- | --- | --- |
| `buildAspectFilter`, `animFormatPlan` | 纯TypeScript，无import；只输出filter/argv计划 | 未把参数类型当runtime验证；无output-byte/probe/acceptance；anim格式依赖本机encoder | 验证枚举/整数尺寸/预算；argv调用与独立derivative receipt；不继承original QA |
| `escapeSubtitlePath` | 纯字符串function；whole file含env/font lookup | 只escape FFmpeg filter-path，不校验input/output containment；style字段可能需更完整escaping | 仅摘leaf function和tests；路径no-follow/containment由AI负责 |
| Provider codecs | Node/app imports或pure mapper；API grammar | `.slice`/clamp改变sealed inputs；unknown→pending；rawURL/errors；environment默认model | exact input不归一改写；strict parser/error projection；Router所选model固定 |
| MiniMax service | app config、filesystem、tracking/network | 自动prompt sanitize、resubmit、H3→legacy/Fast；错误文本进usage tracking | 不整包移植；separate wire codec；canonical effect前后receipt |
| ComfyUI upload | arbitrary fetch→image upload | `fetch(imageUrl)`没有该方法内public destination/byte/MIME验证；潜在SSRF和大payload | loopback profile固定；任何remote input经过AI egress/media ingress gate |
| Wind composer download/shell | `fluent-ffmpeg`, static binaries、fs/http/https、shell | `downloadFile`递归redirect未见hop cap；local proxy解码path；部分`exec`/binary lookup | 不借download/shell wrapper；固定binary+argv+contained attempt files；bounded bytes/time |
| Retake plans | pure floats/default bounds | 没有effect；但默认fps/min-duration/Infinity不匹配exact profile | integer-frame projection；所有bounds由existing timeline/capability提供 |
| Retake services | ffmpeg + app DB/repos + persistent media | DB记take/activate形成第二writer；temp/media path和local锁不足以保canonical concurrency | only candidate生成/返回；durable transitions只经committer；QA后activate |
| Subtitle/voice clients | config/env、TTS/lipsync network、raw错误 | secrets/response可能进入错误；estimated timing；failed→original video | opaque supplier；redacted typed error；request counts/permit；probe/alignment/identity QA |
| Story/agent orchestration | LLM/network、LangGraph/SQLite/Redis/Chroma等 | runtime任务reset/checker PASS/automatic retry；MovieAgent raw response logging | authoring-only proposal；无Provider selector/QA PASS/state-write权限 |
| UI/persistence | React/Zustand/Yjs/DB | imported store直接mutation，draft与accepted state混淆 | ephemeral UI store；read DTO + canonical command facade；plugin/code loading另审 |

Wind `package.json`还含 `predev`/`prebuild`模型fetch hook，不能直接运行脚本或搬dependency graph。`fluent-ffmpeg` upstream已[deprecated且2025-05-22 archived](https://github.com/fluent-ffmpeg/node-fluent-ffmpeg)，明确不宜为了复用composer新引入。保持现有FFmpeg/ffprobe、httpx、Pydantic等实际library seam；不新增单用途universal-provider-framework。

没有证据把外部所有`execFile`都当command injection；argv是较好的边界。真正要检查的是shell-form interpolation、任意URL、raw provider payload、byte limits、path traversal、temporary overwrite及自动retry。无telemetry证明的纯function不应被泛称“会上传数据”；tracking/logging在service具体import/call中隔离。

## What Not To Borrow

1. Provider默认值、fallback、soft health skip或凭据存在→自动启用selection。
2. timeout/5xx/宽松错误文本后重发POST；盲retry、重置task consumption或复用permit。
3. 直接传raw override、ref截断、duration clamp或prompt sanitize修改sealed request。
4. prompt/character Bible/checker boolean当accepted source或continuity truth。
5. looseJSON/Redis TTL/in-memory task reset替代Manifest/Registry/StateCommitter。
6. UI store或外部DB `recordSegmentTake`成为activation owner。
7. 外部compositor建立第二timeline；stream duration等于semantic no-regression；raw/edited混同。
8. estimated字幕/TTS duration成为sample timing；lipsync失败返回原片成为PASS。
9. arbitrary URL fetch/uncapped redirects/raw错误日志/unsafe shell/download wrapper。
10. GPL Editor implementation、无LICENSE MovieAgent code及prompt原文；未另审的fonts/weights/media。

## Product Canvas — Five Interactions

1. **Shot card→focused inspector**：播放exact take，邻近显示intent、source lineage、required findings；Editor workspaces/Wind inspector可参考，GPL组件独立实现。
2. **Take history→side-by-side compare→explicit activate**：take对应immutableattempt；comparison与activation分离；保留historicalFAIL/unknown。
3. **Frame strip→selected frame/range→retake preview**：UI看到的frame由现有timeline/derived-frame id返回；说明实际generation duration及影响下游shots。
4. **Progress / blocker / authorized recovery**：展示submit/poll/fetch/evaluate/activate阶段；missing evidence与unknown拥有不同动作，按钮由canonicalnext-action控制。
5. **Timeline / playhead / trims→draft proposal**：支持直观scrub、source trim、audio/caption查看；确认后走existingCompositionSpec/resolver，UI时间轴始终是projection。

“Model selection”控件只表达requested/preferred model或exact selection assertion；能力与route仍由Router裁决。用户不能通过dropdown改变already-sealedrequest或恢复unknownattempt。

## Proposed Reuse Architecture

```text
AI-VIDEO Core — unchanged canonical authority
├── Truth / Intent: approved Character / Scene / Shot / GenerationIntent
├── Continuity: policy v2 / causal state / accepted source / exact terminal / C2
├── Router / Capability: selected Provider + profile + execution binding
├── Evidence / QA: exact bytes, required findings, lineage, no-regression
└── Effects / StateCommitter: authorization, permit, budget, lifecycle, recovery

Peripheral reuse — inputs/outputs cross existing contracts
├── Borrowed Provider Clients: wire encoding/parsing/transport ONLY
├── Borrowed Media Utilities: pure argv/filter plans / derived display ONLY
├── Borrowed Retake UX: proposals + existing attempts/commands ONLY
├── Borrowed TTS/Subtitle Clients: VoiceAssetProvider / CaptionTrack boundary
├── Adapted Agent Orchestration: authored proposals, no execution authority
└── New Product Canvas: canonical read models + command facade
```

唯一方向：`AI-VIDEO Router / Paid Gate → AI-VIDEO Provider adapter → borrowed wire client`。
client 不选择 Provider、不持久化 Manifest、不推进 QA，也不将 unknown 解释为可 retry。它只返回 typed task observations / bytes，由 adapter 生成既有 receipts；Registry / Manifest / evidence 仍通过原 reader / committer。

媒体 export 从经过验证的 exact final artifact 产生新的 derivative；保留原 timeline、原片与 acceptance。改变画幅、字幕或声音后的 exact 输出按要求重新 review。authoring graph 可以有自己的 ephemeral checkpoint，但不能拥有 active asset / acceptance pointer 或 effect permit。

## Three-Batch Migration Roadmap

### Batch 1 — Low Risk / High ROI

在 H3 对比到达稳定 checkpoint 后，独立收敛 HTTP mechanics，保留接口 payload、routes 与 outcome 语义。
第一份外部代码迁移选择 W-export 的 `buildAspectFilter` + tests：首版使用 contain derivative、显式 typed dimensions 和既有 FFmpeg seam。字幕 escape 随真实 export 需求接入；TTS client 只有在明确的 selected-provider 需求成立时加入。

Acceptance: public adapter 兼容；POST 不自动 retry；secret / redirect / size 约束保持；原片 bytes / hash / acceptance 不变；新 derivative 绑定 source / plan / output hash，通过 duration / fps / audio 检查和独立 review。没有 product 需求的 GIF / AVIF / clone 不纳入本批。

### Batch 2 — Medium Risk

先 ADAPT whole-shot retake / compare UI 与 canonical command facade，再做整数 frame 选区 preview。使用现有 feedback / attempt / Job projection。story-shot-agent / CineCrew 拆解模板仅接入 authoring；确有 branch / human pause 需求时才评估 LangGraph library。

Acceptance: agent 不签发 QA PASS；unknown 只显示合法 recovery；explicit activation 通过 committer；draft 不改变 current project；repair derivative 与 raw Provider evidence 分开；range 拼接需 seams / audio / no-regression evidence。

### Batch 3 — Product Layer

独立实现 Product Canvas、Shot inspector、takes / history、timeline read projection、review workspace 及 edit proposal。GPL Editor 只 REFERENCE。复用现有 React / media / progress 基础，UI 消费既有 runtime contracts。

Acceptance: UI reload 从 canonical state 重建；model choice 仍经 Router；edits 经 CompositionSpec / resolver；Final Accepted / original / derivative 状态清晰；分别提供 browser integrated tests 与 exact 成片观看证据。

## First Actual Migration And H3 Timing

**第一个实际借入模块：Wind Comic `lib/video-export.ts::buildAspectFilter`，PORT 其纯 filter builder 及针对性 tests，外层 ADAPT 为 optional derivative exporter。** 该函数没有网络、secret、selection、job 或 state-write authority，适合先建立有出处、有测试的小规模复用实践。

Exact starting files:

- [source L46–72](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/lib/video-export.ts#L46-L72)
- [existing test cases](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/tests/v3-5-video-export.test.ts)
- [MIT notice](https://github.com/ChrisChen667788/wind-comic/blob/82bedb596336fc09ee85240ccf211b0edc53ef4d/LICENSE)

Expected future AI-VIDEO surface (本轮未创建/修改):

- new `src/ai_video/production/derivative_export.py`：pure plan、contained / verified input 和 candidate 输出；不拥有原片 final acceptance。
- new `tests/test_production_derivative_export.py`：filter / probe / audio / containment / no-overwrite / boundary tests。
- existing `src/ai_video/production/delivery_packager.py`：需要 bundle derivative 时才添加 optional binding，保持当前 exact original packager 语义。
- `.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md`：为新 seam 配置 verification / owner anchor。
- future third-party license / notice artifact：保留 MIT copyright、许可与 source commit。

这项新增能力**当前删除 0 行 production code**。当前重复 maintenance 的优先级则是 #1 transport 收缩。没有真实导出需求时，不为移植小函数创造新 feature。

**安排在当前 H3 continuity A/B 之后。** 先让 A/B 完成或到达有据的稳定 admission blocker，封存 inputs / request hashes / media / verdict，再开始独立外围迁移。没有恢复路径的 A/B 不应无限推迟独立工作；进行中的 Provider / continuity snapshot 则应保持稳定，以保护实验可归因性。

当前 main 的 [H3 A/B admission record](../record_for_agent/2026-10-05-h3-api-opening-state-ab-admission.md)记录 arms `NOT_EVALUATED`、0 H3 submits，source admission 阻断；当时“METASO 仅 R2V”的 capability 结论已被 main 后续 frame adapter 取代。本审计不据此宣称 A/B 已完成或 H3 quality 改善。外围复用不能修复 accepted source 缺失、TYPED_HASH 表达 gap 或 raw opening state reset。

本报告是 research recommendation，后续实施仍需基于正式落地后的 main 确认 scope 与 verification；本轮不授权 Provider 执行。
