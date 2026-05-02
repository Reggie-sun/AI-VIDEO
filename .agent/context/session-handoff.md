## Current State

- Updated: 2026-05-02
- Current Lane: pipeline (质量调优)
- Last Window Done: Iteration 2 全部 10 Task 完成 (31 tests pass) + brainstorm 质量十字路口分析 + 路线 A 参数修复 (移除 4-step LoRA, steps 8→30, CFG 1.0→5.0, 加 negative prompt, 优化 shot prompts)
- Next One Thing: 用户看 quality-test-a 视频反馈后，跑 3-shot 全流程测试跨 clip 一致性，评估是否需要 IPAdapter
- Allowed Paths: src/ai_video/*, tests/*, configs/*, workflows/*
- Validation Done: 31 pytest pass, 2 次真实 ComfyUI E2E run 成功 (quick-verify + quality-test-a)
- Blocker: 等用户确认 quality-test-a 单 clip 质量是否改善到 Q1+
- Notes: IPAdapter 集成在 Pipeline 代码层面零改动（character_refs/CharacterRefBinding 已预置），需先验证 Wan2.2 兼容性

## History

## Round 1 (2026-05-02)
- Done: Iteration 2 (10 Tasks): path resolution fix, manifest hashes, shot started_at/attempts, real resume with stale detection, progress callback, stitch re-encode fallback, CLI resume, E2E resume test, conftest fix. Brainstorm 确定质量优先路线。修改 workflow 参数 (LoRA=none, steps=30, CFG=5.0, negative_prompt, prompt optimization)。运行 quality-test-a。
- Next: 3-shot 全流程一致性测试 → IPAdapter 兼容性验证 → 集成或换模型
- Blocker: 等用户评估 quality-test-a 视频质量
- Notes: SME 发现当前质量差根因是 3 个参数同时严重偏差，非模型上限
