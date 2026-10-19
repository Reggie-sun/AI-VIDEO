---
record_kind: media_experiment
topic_id: jieshi-3d-anime-minimax
learning_eligibility: ineligible
---

# Jieshi 3D Anime References Before MiniMax Test

Date: 2026-10-20

## Scope

用户要求“我想把界蚀做成3d动漫风在测试下minimax”。沿原S01做一次视觉风格变体：成熟国漫3D人物、材质与电影光照；保留八人布局、道具、原倒影异常、左手靠窗、右手手机、原广播与表演方向。不是全集制作、受控A/B或原S01正式完成。

选择最近实际使用的official MiniMax `MiniMax-H3-Max` CN，5秒、768P、balanced、first-frame，视频POST上限1、零重抽、S02 POST0。实际输入与生命周期仍归现有Canvas、Planner/compiler、Paid Gate、`VideoGenerationService`及`ProductionStateCommitter`，不增加共享源码、Provider、执行链或renderer。

[官方接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)与当前adapter均表明首尾帧模式和多模态reference模式互斥；本镜显式选择first-frame，历史v015白模保留但不绑定，不冒称其动作进入请求。原3秒采用窗口及后镜Gate保留，5秒原片不是最终3秒composition。

## Image Inputs

证据根：`runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-20261020-001/`。

Codex内置`image_gen.imagegen`完成两次有界作图：先将原PNG转成3D动漫风，发现工牌空白，再仅针对工牌恢复头像、姓名和部门。工具未暴露generator model，不猜型号。原图不覆盖。

| Artifact | SHA-256 | Observation |
| --- | --- | --- |
| 原首帧 | `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923` | 原写实布局及剧情来源 |
| `firstframe-v1.png` | `8cbde2bb5bc5c7f3079727efee64854ebb199b5539992ce5dbfe60eaf508e216` | 3D风格转换；工牌丢失内容，不能用于视频 |
| `firstframe-v2.png` | `a557098d22e737896e0a5fd75496c0b365d3cf5626081eabbc376afb8134ad65` | 941×1672，2,214,363 bytes；工牌恢复，独立静态复核未见明确新增回归 |

`image-generation-v1.json`、`image-generation-v2.json`保存实际图identity，`concept-review.json`保存同一原生read-only `reviewer_high`的概念与两版静帧复核。静态finding为空不证明视频动作、全帧倒影或声音。第二次生成不提供非目标像素逐字节不变保证。

## Authored Contract

标准reader核验旧Manifest157/Project22及既有历史后，新source在原四段前显式新增风格段、绑定新首帧，原剧情/对白/动作/表演段保留。`source.json`、`candidate-prompt.txt`、`project-data.json`、`authoring-input.json`及`author-preflight.json`保存来源与适配。新QA为`2447a4674cd6826286a7c53a4768710b25196a2caf6d089185de5ad195ee8b1d`：原15项raw要求保留，增加`s01-3d-anime-style`，共16项；FinalOutput原37项保留并增加风格项。输入预检不是模型服从或媒体验收。

## Current Execution

用户随后纠正“你在干什么,先做referces啊”，再明确选择“直接补齐八人＋车厢”。停止视频准备，当前交付目标改为先完成独立人物/场景references。此前已通过唯一committer登记新source/QA：Manifest160 / Project23；这些authoring记录保留，不回滚历史。

本地进程中止于`ProductionPlanningService.prepare()`的标准reader历史budget/evaluation校验，尚未materialize新component或创建新video attempt；本单元无wire-observations、无预算/额度扩展、无新paid permit或视频POST。原budget revision40、内部上界450,000,000及task used10保留。不能把本地中断称为远程UNKNOWN，不能把已登记authoring称为视频或人物/场景reference验收。原S01 STOP与S02 POST0保留。

最终reference候选为八个人物＋空车厢，共9张1536×1024 PNG；原图合计18,989,416 bytes。见[本地总览](../../runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-20261020-001/references/index.html)与[索引](../../runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-20261020-001/references/README.md)。这批独立references未导入Production；前面已登记的authoring仍是旧单首帧变体，不能冒称它已消费本批九图。

reference阶段实际完成9张初稿＋4次有界修图：苏遥先修无刘海直发及持机手，再单独修背面换手；林砚修鞋面多余品牌标记并增加清晰工牌细节；陈立修回约35岁方脸短寸。另一次陈立修图因前一步本地复制尚未完成、输入文件不存在而被工具在读取输入时拒绝，无新PNG；修正本地输入后只执行一次实际修图，不记成远程unknown或模型质量失败。此前两张风格首帧保留为独立历史阶段。

| Reference | Selected file | SHA-256 |
| --- | --- | --- |
| 林砚 | `references/linyan-v2.png` | `9f415189e608d6fb9beb5567fa946fe0b8fbb24a65294f7acb584b149b3b4017` |
| 苏遥 | `references/suyao-v3.png` | `336341af057b0ef3b91ca21cddb4ec2c5046aa45f36a91b05db8742935d32932` |
| 周伯祥 | `references/zhouboxiang-v1.png` | `e858ced58324a4570c106bd2f2b5acfa2110b3c8842508213713a4ca26fc592d` |
| 陈立 | `references/chenli-v2.png` | `56000b47a5fef3a13d284ab003342bd41541b66701e022ae956cfad742c1a8ff` |
| 许雯 | `references/xuwen-v1.png` | `747575b2a2991b28d411fa3451784407d1510464ec06c5b94643e73eea22a8f2` |
| 郭向东 | `references/guoxiangdong-v1.png` | `b3e6047f3f750af378a26fbee49d0efd4dc2d9566552c77e29611e2beb37a778` |
| 沈嘉程 | `references/shenjiacheng-v1.png` | `0093dc5df662984a0d157dac7095303fe98936437c94bea3096e88459c652dcb` |
| 何静 | `references/hejing-v1.png` | `384bafc9dff74c962cd1c5162bf3699dfca7b4b7ac791a3232b9a15b4170fb99` |
| 地铁车厢 | `references/subway-v1.png` | `86c3a3267a3a66f1416d9f0d56a4a1362424112ae75896d688485702cec94fb3` |

全部PNG已实际解码、尺寸/bytes/SHA校验。人物图是同一人物的正面、斜侧、背面和表情，不是多人图；何静额外展示膝上灰袋及袋细节，车厢为空场景多角度参考，不证明原S01七人倒影已满足。完整生成与修图提示词保存在`references/*prompt*`。

同一原生`reviewer_high`的初次references复核发现苏遥侧/背视图换手及发型偏离，Parent按exact图修复。用户随后明确要求整套九图，新scope有据将同一有限审查上限3→6，历史轮次1–4保留；round5绑定上述9图，`references/review-target-index.json` SHA为`ba3145397aa825fb04ff481d2241cb96e2dcb431094c545acdc08ec7416a2df5`，不以换Agent重置轮次。复核仅判断静态reference缺陷，不代签用户风格偏好、3D几何、动作或声音。

## Evidence Boundaries

本单元同时改变首帧和风格文本、无受控seed，不用于宣称3D风格改善动作或倒影的因果结论。原写实版本及失败、消费、unknown边界均保留。`record-ai-video-session`评估record；`distill-ai-video-learning`当前为`no_candidate`，不修改Skill/Policy/Gate或全局memory。

## Verification And Publication

Round5实际完成全部9张exact PNG的独立静态复核，finding set为空；苏遥SREF-001/002在当前v3未再出现，Parent记录`OBSOLETE_AFTER_CHANGE`。`references/review-round5.json`与不可变`review-target-index.json`保存target及证明边界；`asset-index.json`随后仅更新review metadata，9份PNG identity保持不变。

Parent实际核验9图PNG可解码、1536×1024、bytes/SHA；HTML恰好9个有效本地图片链接；下载ZIP通过CRC检查且仅含9份selected PNG，旧稿不混入下载包。`references/verification.json`保存archive identity。PNG、HTML、ZIP及prompt留本地run；Git仅提交本主记录，不把图片上传远端。

文档范围exact staged Harness receipt：`.agent/harness/runs/jieshi-3d-anime-references-record-20261020-r1/receipt.json`；实际结果以该receipt为准，不证明模型视频、场景三维几何或用户风格认可。无共享源码改动，implementation Risk Gate为Parent自审；独立reference复核另按上述实际证据记录。无关dirty/staged工作保留。当前完成的是用户要求优先制作的references，MiniMax新视频测试尚未执行。
