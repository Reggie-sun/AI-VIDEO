# I2V Init Image Composition Regression

## Surface

- `src/ai_video/cli.py`
- `src/ai_video/workflow_renderer.py`
- `configs/*.shots.yaml`
- I2V init image assets and their focused validation/rendering tests

## Previously Correct Behavior

绑定 `init_image` 的 workflow 在首个 Shot 没有上游 chain frame 时，必须显式提供 `shot.init_image`。`validate` 应在提交任务前拒绝缺失值，而不是静默使用 workflow template 中的占位图。后续 Shot 可以使用显式 `shot.init_image`，也可以使用真实 direct-upstream chain frame。

## Regression Class

不要把 prompt 或 sampler 调整当作起始构图错误的修复。如果目标动作要求人物从画面左侧走入，而 init image 已让人物居中站定，应该先替换构图匹配的 init image。通过平移、拉伸或补边制造带白边、结构线或畸变的 init image，同样属于失败输入，不应作为质量迭代基线。

## Required Checks

- 首个绑定 `init_image` 的 Shot 缺少显式 init image 时，`validate` 必须失败。
- 显式 `shot.init_image` 和真实 direct-upstream chain frame 都必须保持合法。
- I2V 质量 review 先检查起始构图是否支持目标动作，并检查白边、结构线、拉伸或位移畸变，再评估 prompt 或 sampler。
- 相关自动化验证默认使用 fixture/fake，不要求真实 ComfyUI output。
