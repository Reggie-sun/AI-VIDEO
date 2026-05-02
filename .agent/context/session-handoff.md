## Current State

- Updated: 2026-05-02
- Current Lane: other (wan22 init-image guard)
- Last Window Done: 为渲染链路加入首镜头 `init_image` fail-fast 规则，CLI `validate` 现在会拦截模板占位图回退；同时为 `wan22_quick` 补入仓库内的横版起始图 `assets/wan22_quick_init.png`
- Next One Thing: 用修复后的 `wan22_fast.project.yaml` + `wan22_quick.shots.yaml` 重新跑一次快测，确认首帧不再泄漏模板流程图，并据此决定是否继续压 sampler
- Allowed Paths: assets/*, configs/*, src/ai_video/cli.py, src/ai_video/workflow_renderer.py, tests/test_cli.py, tests/test_config.py, tests/test_workflow_renderer.py, README.md, .agent/context/session-handoff.md
- Validation Done: `pytest tests/test_workflow_renderer.py tests/test_cli.py tests/test_config.py tests/test_pipeline.py -q` 22 passed；`ai-video validate --project configs/wan22_fast.project.yaml --shots configs/wan22_quick.shots.yaml` 成功
- Blocker: none
- Notes: `render_workflow()` 现在会在绑定了 `init_image` 且没有 chain frame 时检查模板默认值，若是非空占位图则直接报 `CONFIG_INVALID`
- Notes: `wan22_quick.shots.yaml` 现在显式引用 `../assets/wan22_quick_init.png`，并继续覆盖为 3 秒 / 20fps 快测参数

## History

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

## Round 7 (2026-05-02)
- Done: 新增 `video_apply_optimization` 第三段自动应用器，已对真实 `wan22.project.yaml` 自动提升到 1024x576@24fps 并通过 validate
- Next: 重开会话使 `video_review` / `video_optimize_plan` / `video_apply_optimization` 进入可调用工具清单，然后按待跟进项检查 `ffmpeg_tools.py`、`pipeline.py`、`wan22_i2v_api.json` 并跑第一次重新生成
- Blocker: none
- Notes: 真实 run 的配置层安全改动已应用；剩余待跟进项集中在 `src/ai_video/ffmpeg_tools.py`、`src/ai_video/pipeline.py`、`workflows/templates/wan22_i2v_api.json`
