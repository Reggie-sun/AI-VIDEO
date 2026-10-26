---
record_kind: session_summary
topic_id: shizhen-fusion-title-trial
learning_eligibility: ineligible
---

# Fusion Title Trial And Image Direction Checkpoint

## Current Status

用户要求尝试 Fusion 后，完成局部 3 秒 F2；用户明确反馈“这个效果太差了”，本版艺术判定为不通过。随后用户要求“你能不能先做image我看看”，已暂停视频，完成两张静态方向图。当前没有新版完整开场，也没有最终艺术验收；不含 S01。原视频与音乐没有被覆盖。

## Actual Deliverables

- 工作目录：`outputs/shizhen-episode01/fusion-title-trial-20261026/`。
- `variant-F2/失帧-Fusion片名试片-F2.mp4`：1920×1080、24fps、72帧，SHA256 `3628e4b755f48a5025e57cdc02cb37a4a258fa8a4de6e7eb8d89f4ae4659db65`，用户已拒绝。
- `title-trial-F2.comp`：实际 Resolve/Fusion 合成工程；Fusion 渲染 PNG，HyperFrames 按既有 ResolvedTimeline 加原时钟和原声音乐。
- `image-directions/A-glass.png`：雨玻璃印痕方向，SHA256 `f5bd366b6c65e1354221ae28639a4f7f611f1b3a1d47c706a741192cbe6686e6`。
- `image-directions/B-negative.png`：正负片分离方向，SHA256 `beed983a552ff9331bdc111f5e4cc2f1668c85c46ebce2809c6aae153b831caa`。
- 两图都是1672×941 RGB，通过内置 image_gen 各一次生成；exact prompt与引用角色在 `image-directions/generation-intent.json`，原始输出保留，结果复制进工作目录。仅视觉概念，不是像素保护的修图、生成视频或已接入 Production 的素材。

## Verification And Artistic Findings

F1文字首帧出现，修正 Text+ Alpha / Merge.Blend 后 F2首帧无字。浏览器实际1倍速播放72帧，0丢帧，无控制错误，见 `qa/playback-F2.json`。显式 project-local video-analysis 抽验 F2，见 `qa/video-analysis-F2.json`。对应尾段原音乐与雨声的混音PCM逐采样一致，见 `qa/audio-preservation.json`。这些技术证据不改变用户否决。

F2的实际问题：错落宋体淡入仍是常规叠字，字内纹理和立框遮挡对观看感受贡献不足，缺乏事件动机。`qa/review.json`记录用户REJECTED与Parent ART_DIRECTION_FAIL；完整目标评审包 `qa/review-F2/` 继续NOT_EVALUATED。

A图比F2更有字形力度和材质关系，但字像实体玻璃印字，未来动态揭示仍需明确导演动机；B图图形对比强，但白色乳剂区和毛边存在海报化风险。两图人物、光影有生成变化，不可直接宣称连续性通过。AI生成标识保留；原真人质感、宏观世界新镜头缺口未消失。

## Runtime Boundary

Resolve本机21.1.1.10，经内部Lua Console实际完成两轮72帧渲染；没有启用外部Network脚本。先前进程的en_US.UTF-8 locale崩溃通过用户目录独立locale和进程LOCPATH/LC_ALL修复，未改系统默认语言，详见本目录design.md。无新视频或音乐付费生成；内置图像工具未返回账单，不能声称费用为零。

## Publication And Learning

只新增本任务目录及本记录，未修改共享引擎或其他dirty文件。按媒体优先规则，尚未获得效果认可，不运行完整工程套件，不commit/push；未发布、未激活、未作Final Acceptance。自动学习评估为 `no_candidate`：一次尝试及其局部修复不是独立重复实验，当前艺术结果还被用户拒绝，不据此改Skill/Policy。

## B Direction Selected For State References

用户随后明确选择“B 图：黑白负片方向”，要求不止一张终稿，补充若干中间过渡态。此反馈仅认可 B 的美术方向，不撤销 F2 视频否决。当前范围变为静态过渡参考组，视频制作继续暂停。

准备目录 `image-directions/B-states/`，计划入口、三个过渡态及原 B 终态，共5张；4次新内置图像编辑，终态exact copy，不重生成B。中间图共同引用起始图和B，曝光前沿逐步通过左侧空位，字形应只揭示不重设计；实际结果与偏差记录归该目录 `receipt.json`，不由本计划文字代签。此后期表达不改变剧情机制、原视频、原音乐或S01范围。

## Transition Revision And Current Deliverable

上述横向擦除随后被用户明确否决：“不能是从左到右，这样太简单，高级一点”。保留失败组和原调用记录，未将其标为可用。用户进一步授权B终态也可改变，B不再是必须返回的最终帧。

当前交付目录 `image-directions/B-states-depth/`，推荐4态为01彩色入口、02远景影调分离、03字标潜影、04新终态候选。04比原B保留更多城市透光、暖色反射和雨滴层次，Parent选择为当前终态；旧B只做对照。新终态SHA256 `b4c9a6562db3474b6abff3dd19ca9fa1f9a0aa534c9e27acacc66479ef289b70`，未获得用户最终认可。

该修订执行3次内置图像编辑，原02出现白斑似起雾而失败，单独再编辑一次；结果已保存，不继续重抽。当前4张均1672×941 RGB，原人物、电话、站台相对位置经逐图观察保持，像素并不完全相同。完整SHA、prompt、范围、诊断数据与限制在`receipt.json`。无新视频、音乐生成，无生产导入或激活。

不能把本组全图直接溶解或morph为成片，否则会引入人物/雨滴漂移；正式动画仍应采用既有运动底片、受控的影调/深度遮罩及唯一字形母版，且需实际原速声画验收。静态参考已形成，动态艺术结果NOT_EVALUATED。浏览器检查只验证各图加载与切换，不代签审美。学习重新评估仍为no_candidate，全部属于同一渐进设计链。
