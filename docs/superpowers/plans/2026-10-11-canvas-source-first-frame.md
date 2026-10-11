# Canvas Source First Frame Plan

## Goal

执行用户“这种也算过继续下一个视频”：保存视频6的有偏差人工接受，按原画布视频7原文、图片5首帧、Fast2.0、480p、15秒完成一次新增提交。

## Scope And Invariants

现有原文入口拒绝 I2V；来源检查还把已生成参考图片的上游创作依赖纳入执行闭包，导致其祖先 subject 能力误阻断。
只修复这两个已复现的必要边界。图和全部问题保留，执行闭包与已有 packet projection 一致：选中视频及直接引用；
直接引用的 bytes/resource/history 缺项仍阻断。不得重新生成首帧、改引用角色、消费视频6末帧或改写旧 FAIL。
单首帧 I2V 仅限一个 FIRST_FRAME asset，无丰富 v4、typed-hash continuity、conditioning compatibility 或 separate voice；
沿同一个 recipe、compiler、Registry、execution binding、budget、egress、permit 和 post-media Gate。
原文 UTF-8、原始完整 PNG bytes 保持，原720p参数留作观察值，480p是已授权输出覆盖。
原文未指定声音，不添写对白/配乐/音效规则；沿当前批准 native-audio 设置，另列未评估的听感。
历史物理POST4次，新增上限1次，累计上限5次；不自动重试。

## Files And Ownership

- `scripts/canvas_production_source.py` 与 `tests/test_canvas_production_source.py`：选中链直接依赖闭包，祖先问题仍完整保存。
- `src/ai_video/production/seedance_native_prompt.py` 与 `tests/test_seedance_source_prompt.py`：单首帧原文正向编译与错误 conditioning shape 拒绝。
- `docs/agent-primary-contract-matrix.md`：同步原文支持边界。
- 本计划及新 session record：有限单元、实际媒体和验证结果。

## Milestones And Verification

1. 可靠 red reproduction 后修复上述边界；原 compiler/native source、canvas source/sequence/authoring/planning 的相关 tests 保持通过。
2. exact staged Harness 与 fresh receipt 后 Parent 执行 Implementation Review Risk Gate；不修改已暂停的 retarget dirty files。
3. 正常 `CanvasProductionService` 导入、批准、prepare；预览原文及 first_frame identity、零改写 lint；新封存 operator bound 沿前序历史。
4. 一次 canonical submit，恢复 poll/fetch；exact MP4 显式 video-analysis，单独展示正常速度视听。新片没有自动人工接受。

## Self-Review

范围继承 reusable canvas spec 的原文/引用保留与默认480p契约。下一节点是操作员选择编号7，并不推断连续剧情。
Kimi只读映射确认现有 common compiler 支持该 I2V shape；修复不新增生命周期 owner，不扩写 prompt，不削弱未知结果 fail-closed。
Parent 保留最终 diff、真实调用计数、验收与 publication responsibility。
