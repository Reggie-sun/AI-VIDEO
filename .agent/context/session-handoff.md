## Current State

- Updated: 2026-05-02
- Current Lane: other (wan22 shot+init iteration)
- Last Window Done: 连续完成两轮快测迭代：先只加强 `shot prompt` 生成 `quick-verify-prompt2-20260502`，再把起始图换成左侧站位版 `assets/wan22_quick_init_left.png` 并生成 `quick-verify-init2-20260502`
- Next One Thing: 决定是否继续使用 `assets/wan22_quick_init_left.png`；它让动作方向更合理，但也引入了明显的人工边框/左侧结构线，下一步应换成更自然的原生起始图而不是继续平移现有图
- Allowed Paths: assets/*, configs/*, src/ai_video/cli.py, src/ai_video/workflow_renderer.py, tests/test_cli.py, tests/test_config.py, tests/test_workflow_renderer.py, README.md, .agent/context/session-handoff.md
- Validation Done: `pytest tests/test_workflow_renderer.py tests/test_cli.py tests/test_config.py tests/test_pipeline.py -q` 22 passed；`ai-video validate --project configs/wan22_fast.project.yaml --shots configs/wan22_quick.shots.yaml` 成功；真实 run `quick-verify-prompt2-20260502` 与 `quick-verify-init2-20260502` 均成功
- Blocker: none
- Notes: `quick-verify-prompt2-20260502` 证明单纯加强 prompt 只能带来轻微收益；动作仍偏保守
- Notes: `quick-verify-init2-20260502` 证明换图比继续堆 prompt 更有效，但当前左移生成图存在白边和左侧结构线伪影，需要更自然的起始图来源

## History

## Round 11 (2026-05-02)
- Done: 用修复后的 `wan22_fast.project.yaml` + `wan22_quick.shots.yaml` 成功跑通 `quick-verify-fixed-20260502`，确认首帧占位图污染已经消失，新 prompt 与起始图匹配后技术链路稳定
- Next: 继续迭代 `configs/wan22_quick.shots.yaml` 或替换 `assets/wan22_quick_init.png`，让动作从“轻微抬眼/小幅前进”提升到更明确但仍符合起始图构图的镜头表现
- Blocker: none
- Notes: 新成片在 `runs/quick-verify-fixed-20260502/final/final.mp4`

## Round 10 (2026-05-02)
- Done: 为渲染链路加入首镜头 `init_image` fail-fast 规则，CLI `validate` 现在会拦截模板占位图回退；同时为 `wan22_quick` 补入仓库内的横版起始图 `assets/wan22_quick_init.png`
- Next: 用修复后的 `wan22_fast.project.yaml` + `wan22_quick.shots.yaml` 重新跑一次快测，确认首帧不再泄漏模板流程图，并据此决定是否继续压 sampler
- Blocker: none
- Notes: `render_workflow()` 会检查模板默认 `init_image`

## Round 9 (2026-05-02)
- Done: 为 `wan22` 增加独立快测 preset，新增 `configs/wan22_fast.project.yaml`，让 `wan22_quick.shots.yaml` 自带 3 秒 / 20fps 覆盖，并启动真实 `quick-verify-20260502` run
- Next: 等待 `quick-verify-20260502` 产出 `shots/shot_001/clip.mp4`，记录真实耗时并判断是否还需要继续压 sampler 或模板参数
- Blocker: 等待 `quick-verify-20260502` 的真实生成终态
- Notes: 快测 preset 仍然使用同一份 `workflows/templates/wan22_i2v_api.json`

## Round 8 (2026-05-02)
- Done: 为 `wan22` 加入动态 `resolution/frame_count/frame_rate` binding，修复 ComfyUI error 被误报成 output missing 的问题，并在模板里启用 VAE tiling 后启动第二次真实 rerun
- Next: 等待 `opt-pass-20260502-b` 完成；若失败则读取新的 ComfyUI history 错误并继续自动降级，若成功则立即对新成片运行 `video_review`
- Blocker: 等待 `opt-pass-20260502-b` 的真实生成终态
- Notes: `wan22_i2v_binding.yaml` 现在会把 project defaults 注入到模板的 resolution / frame_count / frame_rate
