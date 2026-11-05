# C Interior Source Preparation

C 已由现有 canonical committer 实际 author 到独立 `project/`，Project revision 1，准备时 Manifest revision 5；无 transport prepare 返回 `GENERATE_ONCE` / `compiled`。这只是独立源素材资格试验准备，没有第二条最终成片 timeline。

## Frozen Actual Inputs

最终 `resolved_request.image_bindings` 实测两份：

1. `iris-c-interior`：已认可 A03，SHA `24e5bb452e90e1c9566ad914ac11213cfaecb9596131db6a1b8b5f585199ca0f`。控制原室内、景别、人物身体朝向、设备视线、构图与显示器背面关系。
2. `iris-cf-details`：已认可 ID7b，SHA `e19d9473c40c19d4834554055298351e1bdea3f856a6de76b057b575fcb563ea`。它是完整正面 IRIS 身份，控制面貌、左耳装置和左领红线，不是仅设备特写。

CF-a 不在 payload；原 canonical Character 对象原样保留，因此其历史 Registry / creative provenance 仍保存，不冒充本次上传。`source-selections.json` 的 `selected_for_provider` 明确区分本次输入与资料。

C 仅承担观察反应：保持认可 A03 的身体朝向、设备视线与显示器背面，不转到正面、不操作设备、不敲键盘、不贴图形或文字。嘴唇自然静置，无连续说话/演唱口型；自然呼吸或眨眼是可接受变化，不要求额外像素配准、呼吸幅度/次数或必须观测到某次独立事件。允许正常平台 AI 标识，禁止新增剧情字幕、片名和新闻图形。D 的解释图形、歌曲、逐字字幕仍归唯一最终 composition。

## Parent Gate And History

执行 authoring 前已重开 A01v2 的 exact fetched bytes、execution binding、canonical MCP evaluator source 和四项全 PASS diagnosis，并核对 `qa/A01-v2/post-media-gate.json` 的 attempt/raw SHA/PASS。A2 raw 为 `850b3807757e570dc59c2a6af96fcf930d8689322408e11f1be81db2c5adae1c`。旧 A1 `65f17d...` 的 FAIL 与旧项目保持原样。

当前 source lineage 保留：A1 实际 198 积分 + A2 实际 198 积分，已调用 2 次、累计 396 积分。Parent 新的有限 C 单元最多一次、operator ceiling 250；全任务累计最多 3 次、operator ceiling 750。它不是把前两次额度清零，也不是 submit permit、Production activation 或人物审美接受。

独立 source project 是现有资格试验 unresolved state fence 的显式合法路径；没有向 active A2 项目写入，没有复制/清零 A1/A2 attempt history。原数据只作为有 hash 的来源与费用记录保留。最终素材采用仍由唯一 composition/Registry owner 完成。

## Exact Executed Local Command

Parent 明确授权本地 apply 且 A2 canonical Gate 落盘后，实际运行：

```bash
python outputs/ai-city-takeover/ep01/generation-c-draft/materialize.py \
  --project-root outputs/ai-city-takeover/ep01/a01-first-frame-repair/project \
  --a01-attempt iris-ep01-a01-two-reference-repair-002 \
  --post-media-gate outputs/ai-city-takeover/ep01/qa/A01-v2/post-media-gate.json \
  --profile outputs/ai-city-takeover/ep01/c-binding/profile.json \
  --independent-source-root /home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/generation-c-draft/project \
  --apply
```

该独立目录现在已经存在，**不要为重新 prepare 再跑 materialize**；脚本拒绝覆盖或隐式重建。`materialization-result.json` 保留本次真实 authoring/prepare 结果。

## Verification And Handoff

- `driver-config.json`：fresh C `node_vdk8wx4zs5`，同一账户/IRIS画布，model2.0 VIP multimodal，6s1080p16:9；task `iris-ep01-c-source-003`。
- `prepare-result.json`、`compiled-native-prompt.zh.txt`：实际 compiled request 与 execution binding。
- `assert_resolved_bindings.py`：核验最终真实图序、bytes、role 与提示词职责。
- `final-preparation-validation.json`：canonical reader、A2 Gate、A1 FAIL 保留、Character 完全一致、两参考实际字节与错误 SHA 拒绝、AI 标识/自然嘴部/无额外测量门槛、累计费用与次数边界。

准备时尚无 C video attempt，0 新 Provider 调用，未 start、paid 或浏览器操作；C 媒体质量和人工接受均为 `NOT_EVALUATED`。Parent 再审 exact preview/预算/egress/一次性 permit 后，通过共享 runtime / unit operator 接管，不能由这些准备文件推断已获平台成功。
