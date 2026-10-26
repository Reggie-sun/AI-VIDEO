---
record_kind: architecture_implementation
topic_id: video-import-authoring-provenance-interface
learning_eligibility: ineligible
---

# Video Import Authoring Provenance Interface

Date: 2026-10-26

## Problem And Scope

用户要求先修代码再重新生成浮夸版颜生源广告。本次实际错误出在新写的任务适配器，不能归因为即梦不支持视频参考：错误引用未导出的 `measure_png_bytes`；带入视频导入凭证却漏接 Project provenance；合并带显式视频元数据的记录时沿用 Registry 2.0。原共享作者入口已有正确的凭证收集及 Registry 2.2 合并行为。

## Code Changes

`production/authoring_input.py` 新增 `prepared_authoring_input_references()`，从 PreparedArtifact 收集、验证并按原顺序去重内容寻址的导入凭证引用。`canvas_authoring.py` 改用同一接口，保留原有 canonical bytes/path 校验，避免任务适配器再次复制并漏接这段逻辑。新测试进入现有 Harness check 与路径映射；没有放宽 bootstrap、reader 或媒体验收。

任务适配器修正测量函数导入，使用该接口将视频凭证加入 Project provenance，按 Registry 2.2 合并并重新封存；读取两个 authoring-input 时逐个核验，并精确区分主创作包和视频导入凭证。失败中间产物保留在同一 runtime 的 archive，未删除凭证、伪造 AssetRecord 或重置历史计数。

## Verification

- 新接口缺失先复现失败；新增顺序去重、错路径、非规范字节三个回归测试。
- 新接口和既有视频导入→作者→bootstrap→不可变重开测试：4 PASS。
- `test_authoring_input.py`、`test_canvas_authoring.py`、`test_canvas_assets.py`、`test_canvas_project_data.py`、`test_production_bootstrap.py`：89 PASS。此为相关定向验证，不是完整仓库 Harness PASS。
- Harness focused inspect 识别全部四个工程路径，无 fallback/unfocused path；新测试已登记。
- Exact staged focused Harness 另行执行，receipt 为 `.agent/harness/runs/video-import-interface-20261026-001/receipt.json`，结果 FAILED：docs contract PASS，harness tests 为319 PASS/2 FAIL，随后停止。失败涉及 `full_tests.covers_check_ids` 漏列 `authored_visual_revision_tests`，以及7个非本次 owned 的未映射源码/测试。只读检查当前 HEAD policy 已存在前一遗漏；7个文件分别属于 qualification quality repair、preview source clock/input 和 watermark preset。没有为此修改其他窗口文件、隐藏失败或宣称 Harness PASS；本记录更新后旧 receipt 仅作为该次失败快照的历史证据。
- 父级审查结论：现有收集逻辑提取复用，严格存储/读取与 side-effect owner 未改变，相关成功和拒绝路径已验证；`NATIVE_REVIEW_NOT_REQUIRED`。Worker 实现不冒充独立审查。

## Exact Task Evidence

下列路径相对 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/`：

- `hyperbole-001/motion-repair-001/runtime/A/H01-bootstrap-output.json`：真实 bootstrap PASS，project SHA `1b4be1a4393dcfe7b2a85b191dc759bd933881ea392a96b3030b6463c621393d`，Registry SHA `2e288fc3eb0ac67a98207aaa09b78079122b06f4edde588a289adf4e8fc9e207`。
- `hyperbole-001/motion-repair-001/runtime/A/H01-prepare-output.json`：SHA `5f14babb5b3d38622d1172eacded4f6a8ae4b3510d88486d3c29abc548548423`，request `c26ff5f91632c28e18de854ed6d9008068049ef04ac6d983394d267aab2a59fb`，3809/4000 UTF-16，4 PNG + 1 reference_video，native audio enabled。
- 视频参考 SHA `ea8a0664116d9bacd7f8307199082a57a31df528b732b099d0e570ae7d3ff80d`，6秒、360×640、24fps；只约束运动和布局，不转移白模外观、无声状态或表演。
- `hyperbole-001/motion-repair-001/native-readiness/A-H01-c26ff5f91632c28e.json`：2026-10-26T00:08:39Z 实际页面只读预检 PASS，账户、空目标节点、已上传 guide 节点/资源、三层 request 的媒体身份均核验。

本 checkpoint 尚无新 generation attempt/start/submit，历史 durable paid 槽位仍15/A9/B3/C3。旧 H01 空间 FAIL 与 sound/performance NOT_EVALUATED 均保留；技术预检不证明新片动态附着、浮夸表演或声音已通过。新片实际费用未发生；旧已发生费用仍待结算。

## Learning And Publication

自动学习评估为 `no_candidate`：这是单次适配器实现修复，测试与 bootstrap 不是多个独立媒体实验，不产生模型效果或通用生成保证。没有新建或采纳 Learning Claim，也未刷新 RAG。本记录不代表媒体发布或 Production activation；成片尚待生成和真实审片。
