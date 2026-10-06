---
record_kind: session_summary
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: ineligible
---

# Fanxiang Motion Reference Join Check

Date: 2026-10-07

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
