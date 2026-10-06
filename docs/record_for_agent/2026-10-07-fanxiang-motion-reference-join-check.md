---
record_kind: session_summary
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: ineligible
---

# Fanxiang Motion Reference Join Check

Date: 2026-10-07

## Full Withdrawal Follow-up — 2026-10-07

用户本轮明确改变剪辑目标：不强接旧撤退近景，由白模自己完成接触、即时偏转、头颈撤回破口
和空窗，再接B03空窗。008“强配旧近景未成立”的裁决保留为历史，未被改写为PASS；当前可用范围
是**完整白模动作参考**，不等于H3真人迁移或正式成片通过。旧撤退镜继续保留备用。

本轮独立目录 `F = runs/fanxiang-motion-full-withdraw-20261007-009/`：

- `F/Video-1-full-withdraw-final.mp4`：1344×768、24fps、66frames、2.750秒、H264/yuv420p、无音轨；
  SHA `065dae8a24e57f3b61766b502401d82aa9d670109ce06fb0f8ec122d3954c4b2`。
- `F/full-withdraw-join-review.mp4`：1344×768、24fps、367frames、15.291667秒、无音轨；
  SHA `9ac93147845e9e1837ec4df71c8165cf79209e3416a1a262f596243f80ac357d`。
- `F/full-withdraw.blend`、`build-full-withdraw.py`、`review.html`、`README.md`与`reference-list.json`
  是可编辑源、播放入口和最终1视频＋4图名单。4图前4项与007全等，SHA逐项重验。

前12帧直接复用007原render PNG，第5帧接触、第6帧立即偏转，见`contact-source-reuse-proof.json`。
66帧白模重开渲染的第9、10帧各有1像素RGB数值差异，kinematics不变；保留这些render原件，
实际采用原12帧，未以新render差异冒充原画面字节相同。后段固定相机、头部尺寸和破窗geometry，
按自然回撤增加时长，末尾保留可读空窗；没有追旧近景的reframe、再次攻击、循环、插值补帧或变速。
当前`metaso_h3.py`本地adapter的reference_video约束为2–15秒、24–60fps、最多50MiB；当前2.75秒
232361bytes输入符合离线limits，上游接收与动作继承未测。没有调用H3或改prompt。

独立project复用`SourceUseEvidence`、`ResolvedTimeline`、HyperFrames及committer，24fps half-open
剪辑B03 `[0,287)` → 新Video1 `[0,66)` → B03空窗 `[348,362)`，全程不使用旧recoil。
`canonical-compose-binding.json`绑定exact timeline与export/canonical output SHA。
不改原Production、raw历史、candidate/旧QA/activation或通用架构；无产品代码变更。

Blender5.2.1/Workbench/headless/factory-startup重开132整帧/半帧：camera matrix无变化，手臂长度
0.71999985–0.72000009，颈部endpoint gap最大0.000829，头部surface落入所测窗框/墙盒体为0，
第5帧keyboard case/头部完整3D接触norm0.999995。额外evaluated neck mesh检查发现35.5、36帧
有2个vertex轻微进入窗台背侧（最大约9.6mm），camera ray均先命中窗台，当前render没有可见断颈
或背侧相交点；此粗模局限保留，不宣称连续物理碰撞通过，不再为此自动精修。

project-local `video-analysis` MCP对两份exact MP4逐份probe/extract；完整decode通过。
Chrome实际1×参考2.753秒/66捕获帧/0丢帧，对照首次15.295秒/363帧/4播放器丢帧；保留观测，
降低取证负荷复播15.2946秒/367帧/0丢帧。媒体未因此重剪或覆盖。
Parent查看真实播放帧板与`join-boundary-board.jpg`：接触→即时受力→连续入同一破口→空窗可读，
前接点轴线/挥击起势一致；后接点在退出后切到原空窗特写，没有重复撤退或头部姿态切跳。
该后接点是明确中景到空窗特写，不是同景别逐像素匹配；灰模/真人外观差异继续视为diagnostic占位。
裁决`USABLE_FOR_MOTION_PREVIS_ONLY`，到动作参考程度即停止，不提升为成片质量PASS。

本轮只读Kimi source/brief/有限几何审计与Parent视频裁决分开；其报告不代签媒体质量。
Risk Gate为KIMI_REVIEW_NOT_REQUIRED：局部可逆预演/诊断，没有通用implementation、安全、付费
或critical durable-state契约变更。源代码审计不是另加required final-review gate。

原13.875秒、13.375秒、008参考/对照、B03/recoil raw均重验SHA未改；旧撤退素材保持备用。
新对照刻意无音轨，原对白未覆盖/循环/调整，声音形象与听感仍待用户确认。
本轮H3 submits=0，真人命中及H3迁移NOT_EVALUATED，原成片NOT_ACCEPTED，未自动推进下一剧情单元。
媒体local-only，未上传、发布、push；foreign `AGENTS.md`、`skills-lock.json`及新安装skills不修改或stage。
`record-ai-video-session`在本地交付checkpoint更新；自动`distill-ai-video-learning`为no_candidate：
同一制作链，替换撤退、镜头与时长同时变化，不算隔离变量的独立迁移实验；不创建placeholder或adoption。

本轮exact staged文档检查：`.agent/harness/runs/fanxiang-full-withdraw-record-20261007/receipt.json`。
文档receipt只证明文档检查，不认证真人动作、声音或成片验收。

## Endpoint Alignment Follow-up — 2026-10-07

本轮按用户要求只处理白模终态与原撤退开头，不提交H3。下方007交付保留为历史；
当前候选及新取证在独立 `E = runs/fanxiang-motion-endpoint-align-20261007-008/`。
**当前接镜仍为NOT_ESTABLISHED，不能把清单存在标成最终1视频＋4图已可用。**

先实际抽取原撤退30–106帧：77以前的悬停摆头不能充当持续撤离；78–86帧开始下偏却仍有
景别差异；最终取已进入破口的 `[93,107)`。新白模重做后段到“入窗但尚未消失”，不再以
空窗结束后接回仍在窗外的头。前12帧RGBA像素与007逐帧相同（PNG metadata bytes不同），
第5帧接触、第6帧即时反应保持；只在12帧之后连续重构图和改变后缩路径，未缩放头部。

- `E/Video-1-endpoint-motion.mp4`：1344×768、24fps、48frames、2.000秒、无音轨；
  SHA `fef41312b4c512f31eff87143b26cd0c5fe82761de306600c5ff7f57fc7b7796`。
- `E/endpoint-join-review.mp4`：1344×768、24fps、363frames、15.125秒、无音轨；
  SHA `4e357c3d4e650bec90d2372b042c7272163f7aa1917e5b60592eb0942483a070`。
- 对照是B03 `[0,287)` → 完整新Video1 `[0,48)` → recoil `[93,107)` → B03空窗 `[348,362)`。
  HyperFrames/Timeline/SourceUseEvidence/committer复用于独立诊断bundle，没有修改通用架构。
- `E/reference-list.json` 前4项与007完全一致，图像SHA逐项重验；Video1仅更换为当前候选。
  原13.875/13.375版、raw与4图均重验未改，见`E/preserved-source-check.json`。

重开最终`.blend`采样96个整帧/半帧，手臂定长、颈部最大gap0.000829，所测head surface vertices
进入墙/窗框盒体为0，第5帧3D接触norm0.999995。早期后段穿窗框的本地诊断版本保留，未交付为最终。
这些是有限proxy几何取证，不证明物理模拟、真人结果或视觉验收。

project-local `video-analysis` MCP对两份exact MP4均probe/extract，完整decode通过。
Chrome实际1×参考2.0011秒/48捕获帧，对照15.1256秒/363捕获帧，均0播放器丢帧。
Parent查看`E/actual-1x-join-sheet.jpg`、`endpoint-boundary-board.jpg`与`terminal-state-comparison.jpg`：
头部尺寸/位置跳变明显减小，后缩不重复；但破窗上沿切点下跳、白模面朝向偏正仍可见。
**剩余缺口在motion reference终态机位/破口投影与头部朝向，现有recoil93–106仍有保留价值；
不能据此宣布旧撤退源本身必须废弃。** 本轮停止，不自动修复下一版或提交H3。

受管Kimi只读`endpoint-brief.json`与旧007脚本，invocation
`fab0fcd6-fa0d-4cdf-821f-ab83c470153c`，k3/max、2 wire requests、277.897秒、PARSED。
canonical report SHA与observed Read SHA核验，Parent裁决见`E/kimi-parent-adjudication.json`。
Kimi未看视频或审最终bytes；其报告不是媒体验收。Risk Gate仍为KIMI_REVIEW_NOT_REQUIRED，
本轮没有通用代码/付费/凭据或critical state-contract改动。

新对照刻意无声，未覆盖、循环或调整原对白；声音反馈继续待用户确认。
H3 calls=0，迁移NOT_EVALUATED，成片NOT_ACCEPTED，媒体local-only，未push或发布。
`record-ai-video-session`在本地诊断交付checkpoint更新本记录；`distill-ai-video-learning`
为no_candidate：同一制作链的后段迭代，没有独立迁移实验，不创建placeholder或改Skill/Policy/Gate。
不因记录追加Provider/media或全量tests；foreign `skills-lock.json` 与新安装skills保持不动。

本次exact staged记录验证：`.agent/harness/runs/fanxiang-endpoint-alignment-record-20261007/receipt.json`。
该receipt只证明文档检查，不将当前NOT_ESTABLISHED提升为视觉PASS。

## Scope And Delivery

本轮只解决 Video 1。先对照原 V37 与13.875秒保留版的实际切点，确认V37挥击左右方向相反、
撤退依赖切景，不能作为匹配机位的连续动作示范。按当前用户授权制作本地最小Blender预演：
粗略手臂、电脑键盘、头颈、已破上亮窗和固定相机。没有H3提交、上传、prompt重抽或通用架构修改。

最终独立目录 `R = runs/fanxiang-motion-join-check-20261007-007/`：

- `R/Video-1-contact-motion.mp4`：1344×768、24fps、48frames、2.000秒、H264/yuv420p、无音轨；
  SHA `1c68305a2b62f824b891d2c3203c8db425f0fa71edd8ad85aeb1fc4b87704959`。
- `R/previs-join-review.mp4`：1344×768、24fps、343frames、14.291667秒、无音轨；
  SHA `72655d4f2b93635085720852e87b307f15bd2370e19009c9778bc90ca303d841`。
- `R/reference-list.json` 与 `R/README.md`：最终1视频＋4图名单。4图的bytes、SHA、roles、职责与
  predecessor `fanxiang-motion-reference-preflight-20261006-005/reference-list.json`逐项重验一致。
  Video只负责动作；图片分别负责小龙/黑衣、狗哥/长颈、电脑键盘、B03第287帧的破窗/机位空间。
  不将代理脸、白模材质、图片标记或原片错误动作视为输出应继承内容，没有硬motion-only权限保证。

## Production Owners And Actual Join

独立诊断project复用既有 `SourceUseEvidence`、`CompositionSpec`、`ResolvedTimeline`、
HyperFrames、`ProductionStateCommitter`；没有direct mux、第二timeline或原generation candidate激活。
当前source-use的PASS只证明所选诊断窗口用途，不代签画内命中、H3迁移或原成片验收。

24fps、zero-based half-open剪辑：原B03 `[0,287)` → 白模 `[0,12)` → 原recoil `[77,107)` →
原B03空窗 `[348,362)`。只插入0.5秒接触与初始后缩，未把2秒白模整段撤退再次接在旧撤退前。
原取键盘和挥击起势保留，接触是白模第5帧，第6帧立即受力；初始右后缩仍带向下惯性，再升回破口。

`R/production-previs-join-delivery/` 是独立诊断bundle。`R/render-state.json`、`timeline.json`、
`source-use-assessments.json` 绑定实际render，export bytes与canonical output SHA重验一致。
技术render activation仅属于该诊断project，不是原Production、P6或Final Acceptance。
诊断spec的 `audio_tracks=[]`，没有覆盖/循环对白，没有添加SFX。原保留版与13.375秒历史备选SHA
重验不变，见 `R/preserved-source-check.json`；用户拒绝省略接触及“兄弟们”声线反馈继续有效。

## Blender Corrections And Verification

使用 `scenario-blender-expert`、`scenario-blender-animation`、`scenario-blender-previs-storyboard`。
Blender5.2.1/Workbench，所有制作、render与重开均headless/factory-startup/python-exit-code1；
不加载用户add-ons，不开新GUI，不做精细模型、素材下载、完整rig或通用系统。
同一制作链的版本保留，不算独立实验或H3候选。

实际render先发现Bezier点的动画没有同步保持可见颈部弧线，颈部穿入侧墙；改成25点采样连续tube、
烘焙坐标并让颈部穿过真实破口。再修正回缩时绕脸、穿入门框以及变长手臂：两段定长proxy IK、
head在破口前先对准，再增加depth穿墙。只作本镜艺术修正，无产品层patch。

重开 `R/contact-previs-delivery.blend` 采样96个整帧/半帧：camera matrix无变化，arm length
0.71999985–0.72000009，neck endpoint max gap0.000829；head surface vertices落入所测墙/门框盒体为0。
第5帧完整3D接触点norm0.999995且落在keyboard case内。`R/saved-blend-audit.json` 是实际重开采样，
不把单点、有限surface采样或proxy尺寸声称为连续物理碰撞/完整人体力学验证。

project-local `video-analysis` MCP对最终reference与join均显式probe/extract；证据分别在
`R/mcp-delivery-motion-media.json`、`mcp-delivery-join-media.json`。两MP4完整decode exit0。
Chrome实际1×播放reference至ended，2.0015秒/48捕获帧/0丢帧。join首遍14.2922秒/338捕获帧/5播放器丢帧，
保留该观测；降低取证canvas负荷复播14.2929秒/343捕获帧/0丢帧。仅复播一次以区分播放器负荷，
没有重新剪辑或覆盖媒体。Parent查看实际播放连续帧板与精确切点，未把播放成功代替声画验收。
对应 `R/normal-speed-reference-playback.json`、`normal-speed-join-playback.json`、
`normal-speed-second-join-playback.json`、`actual-1x-reference-sheet.jpg`、`actual-1x-join-sheet.jpg`。

受管Kimi deep只读早期v02脚本/几何，invocation `d2882509-563d-4ea4-a03e-d63e38bf08bf`，
447.607秒/2 wire requests；canonical report SHA、observed Read source SHA与qualification核验。
Parent接受门框穿插、变长手臂和测量局限finding，并据实际新几何/重开/render裁决修正。
Kimi未审final bytes、未看视频或听声音，不作为最终质量裁决，见 `R/kimi-parent-adjudication.json`。
Risk Gate为 `KIMI_REVIEW_NOT_REQUIRED`：本轮是局部可逆素材/诊断，不修改通用产品实现、权限、
付费或critical durable-state契约；explorer调用不冒充implementation reviewer。

## Assessment And Remaining Boundary

白模内挥击→接触→立即偏转后缩闭环成立。接回原镜仍可读命中后撤退，但原recoil近景的头部尺寸、
头颈姿态跳变仍在，**接镜未完全成立**；明显的灰模→真人外观切换是诊断显示，不是可交付剧情素材。
`R/delivery-verdict.json` 保存 exact目标与分层裁决。H3迁移、真人接触素材和整片声画验收均未验证，
不得据本预演宣布原要求通过或推进下一剧情单元。当前无声对照不证明SFX、对白或声音形象；仍待用户听辨。

## Shared Artifact Collision And Publication

本轮起初复用了 `fanxiang-blender-motion-reference-20261006-006/` 名称；后来HEAD出现另一窗口
`4aaaf96` 的白模交付记录，发现本轮通用 `review.html`、`normal-speed-reference-playback.json` 与
部分Kimi/检索辅助文件发生同名覆盖。另一窗口的v06 MP4/.blend、原13.875/13.375 MP4未覆盖。
已停止在该共享目录继续写入，最终交付和新证据全部放到独立 `R`；既有同名辅助入口的历史字节
未恢复，不猜测旧HTML，不修改另一窗口record/receipt。旧MP4与canonical Kimi receipts仍可校验，
但旧目录混合后的辅助文件不得作为其历史验收证明。此auxiliary recovery仍需原owner核对。

本记录仅新增owned documentation checkpoint，媒体local-only；未上传、发布、修改Skill/Policy/Gate，
不push其他窗口历史或夹带 `skills-lock.json` 和新安装skill目录。记录本身不触发额外Provider/media。
`record-ai-video-session` 达到本地交付checkpoint；自动 `distill-ai-video-learning` 为 `no_candidate`：
一个局部制作链的迭代，没有独立H3迁移实验，旧robot/Seedance结果不适用于本人体接触。

记录验证owner：`.agent/harness/runs/fanxiang-motion-join-check-record-20261007/receipt.json`。
该receipt只证明exact staged文档检查，不认证媒体或原剧情质量。
