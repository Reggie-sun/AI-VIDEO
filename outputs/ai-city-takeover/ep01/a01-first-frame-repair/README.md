# A01 Multimodal Two-Reference Repair

**当前方案是 `multimodal-two-reference`，不是 FIRST_FRAME。** 目录和部分 asset ID 保留探索时的行政名称，Provider mode 必须读实际 typed profile / resolved request。

## Frozen Strategy

实际 `resolved_request.image_bindings` 已无 transport prepare 核对为：

1. `iris-a01-first-frame-repair-balcony`：认可 A01，SHA `0faefb4770ee7809a541af4150724dd2d188d9c7689a12f41d41ded3e4752087`。控制原头胸中近景、人物大小、front-ish 朝向/姿态、阳台构图与光线。
2. `iris-cf-details`：认可 ID7b，SHA `e19d9473c40c19d4834554055298351e1bdea3f856a6de76b057b575fcb563ea`。它实际具有完整已认可的正面面貌、左耳装置与左领红线，因此合法作为 IRIS identity，不能因历史 ID 名称把它降为仅设备图。

CF-a 实物为侧身/露肩背参考，本次不在 payload。Registry 仍留其 canonical provenance；注册不等于本次上传。原 canonical IRIS Character 对象原样保留，旧身份与装置 QA observable 也原样保留，不以删身份约束换执行。

归因变量是从原三参中只去掉侧身 CF-a，保留 A01 与 ID7b。姿态竞争是待验证假设，不是已证明原因。此次仍为 model `seedance_2.0_vip`、`multimodal`、nominal 6s、1080p、16:9；不能声称首帧像素级原生锁定。

## Explicit New Revisions

- 对照认可 A01，起始须保持原头胸中近景与 front-ish 姿态，不变成更远景别、侧身或露背；仅自然呼吸、轻眨眼和极小原轴推进。
- 用户新指示“保留 AI 标识，只禁止新增剧情字幕和图形”已封存。新规则允许平台正常人工智能生成标识，不删除或遮挡；禁止新增剧情字幕、片名、新闻图形。
- Parent 依据实际认可图明确修订未来嘴部规则为“嘴唇自然静置，不出现说话或演唱的连续口型”。不把自然微分开的嘴唇擅自判为说话；旧 QA、旧录像与旧 camera-space FAIL 不追改。

## Historical Evidence And Bounds

旧 raw `65f17d6860cbde39df398f42138149a7b4fc7a0bda7fdd96952b88134a0601d5` 已知落盘，Parent 实看 camera-space FAIL，原结果与旧项目保持不动。旧积分实际观察消耗 198、已调用 1 次。`repair-lineage.json` 和 canonical authoring-input 明确保留：累计 attempt ceiling 2、累计 credit ceiling 500，新单元最多 submit 1 次、operator ceiling 250，0 自动重试；旧账没有清零。

`first-frame-rejected.json` 保留单首帧思路的 planning 阻塞与现有 owner 边界：身份需求不能仅从 approved keyframe provenance 自动继承，现有 selector 需要真实 identity reference。未改 shared gate，没有单首帧付费调用。

`unexecuted-reference-classification-correction.json` 保留一度把 CF-a / ID7b 实际姿态写反的未执行方案。Parent 与独立 verifier 重开真实 PNG 后更正；该误方案没有 start、submit 或付费。当前真实输入以上述最终 resolved bindings 为准。

独立源片项目是为了保留旧资格试验 state fence 与真实历史，不是 UNKNOWN 绕路，更不是第二条最终成片时间线。两片最终只有既有 composition owner 能选入。

## Prepared Canonical Inputs

`project/project.yaml` 当前 authoring revision 4，准备时 Manifest 13。`row.json`、独立 coverage v4、PreviewApproval、typed QA 与真实参考 bytes 均经现有 committer/reader。`driver-config.json` 使用 Parent 实测新节点的 `../a01-repair-binding/profile.json`；此文件不是凭据或 submit 授权。

`prepare-result.json` / `compiled-native-prompt.zh.txt` 已得到 `GENERATE_ONCE` / `compiled` / executable binding；最终编号恰为 A01 图1、ID7b 图2。未 start / submit，媒体质量为 NOT_EVALUATED。

## Verification

```bash
python outputs/ai-city-takeover/ep01/a01-first-frame-repair/prepare_request.py
python outputs/ai-city-takeover/ep01/a01-first-frame-repair/validate.py
```

`final-preparation-validation.json`：两次 prepare request/binding 一致、prepare 不写 state、两份真实 payload bytes、错误 SHA 拒绝、图序与 native prompt 一致、原 Character / identity QA 保留、198 积分历史与累计边界保留。Python 编译和 whitespace 检查通过。没有 live transport，没有浏览器、start、paid、媒体 PASS 或人工接受结论。
