# A01 Source Generation Preparation

此目录只拥有 IRIS EP01 阳台开场的独立源片准备，不拥有整集剪辑时间线。歌曲未完成；本镜只闭口观察，后期独立歌曲或念白，原生音轨在 composition 中 `MUTE`。输出请求为 Jimeng `seedance_2.0_vip` / `multimodal` / `1080p` / `16:9` / nominal 6s，精确交付帧数仍归最终 `ResolvedTimeline`。

## Current Frozen Inputs

- `project/project.yaml`：通过 `ProductionStateCommitter` 写入与严格 reader 回读的 canonical Project；最新 authoring revision 6，准备时 Manifest revision 20。前序 revision 与失败前的准备保留，不改历史。
- `row.json`：typed rich GenerationIntent、表演、连续性、参考职责、composition 静音声明。
- `director-coverage.json`：真实 v4 Director coverage，单一六秒源片职责。
- `preview-approval.json`：用户原话“三张都认可，继续镜头制作”，绑定当前 coverage；包括本次 A01 关键图和之前已认可的 CF 面貌/细节。该结构只记录实际认可，不替代原速视频验收。
- `qa-policy.json`：身份、闭口观察、空间/机位、视觉四项 raw 未来验收规则；均需 exact MP4 + project-local `video-analysis`，FinalOutput 仍要求人看。不存在视频 PASS 结论。
- `driver-config.json`：共享 `scripts/jimeng_feedback_driver.py` 的显式输入。live profile 来自 `../live-binding/profile.json`，不是凭据；首次资格试验 paid ceiling 1、used 0、max resamples 0。
- `prepare-result.json`、`compiled-native-prompt.zh.txt`：实际无 transport 编译结果，`GENERATE_ONCE` / `compiled`，带真实 execution binding 和 resolved request。

**最终发送的 `resolved_request.image_bindings` 是唯一顺序依据**：图1 `iris-a01-balcony`，图2 `iris-cf-details`，图3 `iris-cf-face`。中文编译提示词已逐一匹配。provider-bound 中间 input_assets 的排序不同，不能拿它解释实际图号。

## Canonical Ownership

没有真实 Canvas 捕获，因此没有伪造 inspected Canvas packet。普通 PNG 实测字节经 `AssetRecord` / Registry 导入；创作对象、图谱、QA 由现有 canonical committer 与 resolver 写入。所有 reference、coverage 与 approval 字节均封存到 authoring-input provenance。未改共享 schema、Provider、Gate 或其他作者 staged 文件。

`prepare.py --bootstrap` 负责本目录的任务数据到现有 canonical owner；后续 revision 使用 `prepare_project_registry_commit` 和 `prepare_strategy_dependency_transition`，没有直接改 Manifest。

## Verification

```bash
python outputs/ai-city-takeover/ep01/generation/prepare_request.py
python outputs/ai-city-takeover/ep01/generation/validate.py
```

最近验证见 `final-preparation-validation.json`：严格 reader、两次 prepare request/binding identity 一致、prepare 不写 state、三图实际字节、stale hash 拒绝、最终图号与提示词职责一致。脚本 Python 编译通过。`planning-validation.json` 是较早的 projection 调试记录，最终冻结 identity 以 `final-preparation-validation.json` 为准。

本子任务没有 transport、没有 start/submit、没有付费调用、没有视频质量或人工接受结论。Parent 在重新读当前 live 状态、exact paid preview、预算与一次性 permit 后，通过同一 runtime owner 继续。每个 exact MP4 落盘后先执行项目 Per-Shot Gate，再考虑下一镜。
