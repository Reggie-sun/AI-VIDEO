---
record_kind: session_summary
topic_id: shizhen-mc00-process-and-user-feedback
learning_eligibility: ineligible
---

# Shizhen MC00 Process And User Feedback

> **Superseded status (2026-10-29):** 停止后的分析、MC00 v4 重做（Gate FAIL）、宏观开场改为 CITY-RISE 调度对讲版（用户否定）及新生成参考规划门禁（提交 `d5c0718`）见 [2026-10-29 记录](2026-10-29-shizhen-macro-opening-redo-and-reference-gate.md)。下文 v3 时间线与测量作为历史证据保留。

Date: 2026-10-28

## Purpose And Stopped State

用户说“直接停止,我让claude分析下为什么你做的不行”后，制作已停止。随后用户指出“不对啊,没看到你做的过程,和我的反馈”，本文件补齐这个窗口的决策、反馈与处理经过，供另一 Agent 分析。它不是新的执行提示，也不授权继续制作。

此前只给了试片目录和 FAIL，遗漏了用户多次纠正方向、Agent 如何处理，以及哪些准备没有真正进入模型。这个遗漏使另一 Agent 无法仅凭目录还原失败过程。

下列用户引文来自本线程可见消息；早期操作经过结合延续摘要和已有记录恢复，不声称逐字还原所有 Assistant 回复或完整工具日志。没有可靠时间的步骤只记先后，不补造时间。当前可直接核对的试片、提交和 Gate 证据另行链接。

## Intended Result

用户的整段目标是《失帧》独立冷开场：MC00 城市长镜头、市政异常、董文慧楼梯异常、站台定位，完整保留 B6。本轮先做 MC00 空间、参考与连续运镜准备；MC00 内部一镜到底，之后明确接 MC01，不把整个开场改成一镜到底。

已认可的 MC00 路线：屋檐滴雨近景 → 横移越过建筑外转角，城市从遮挡后展开 → 沿同一主路缓弧下降，住宅与站棚依次显露 → 近街面从容减速 → 钢索入前景，交给工人与控制盒。异常留给 MC01，不能重复工人按停，不能为时长加速、藏切或删事件。12–18 秒只是容量估计；后来试片采用 20 秒。

城市地理是新设计，并非原市政片已经证明的空间。验收目标始终是完整原速声画和连续接点，静图、轨迹计算、解码和代码测试不能替代。

## User Feedback And Agent Responses

| 顺序 | 用户原话／要求 | Agent 实际处理 | 是否解决及遗漏 |
| --- | --- | --- | --- |
| 1 | “先不要开始生成视频,生成之前给我看referces” | 先制作／展示参考，没有立即提交视频。 | 遵守了先参考的顺序，但最初展示重点偏向 MC00 布局和草图。 |
| 2 | “为什么别的都是草图” | 补做 MC00 写实屋檐、城市展开、下降、市政接近参考。早期中间图仍有高台、矮墙等空间问题。 | 写实图增加了，整段覆盖仍不足；不能把换成写实视作解决空间和运动。 |
| 3 | “开始” | 继续推进当前参考准备。 | 这句没有豁免后续参考、视频 Gate 或整段目标。 |
| 4 | “不够,我不是只要一个shot的” | 扩成 MC00–MC06＋B6 的 21 图总览，市政用已认可原片实际帧；复用门、反应、站台参考，保留完整 B6 播放。 | 修正了只展示一个 Shot 的范围偏差；仍是参考覆盖，不是整段视频已经完成。 |
| 5 | “m2和m3你準備怎麼切” | 解释市政断控和门到限位在原市政宽景内完成；原文件在第 104 帧／约 4.333 秒切近景。 | 这是复用已认可市政剪辑的切点说明，不是将所有事件重编成连续一镜。 |
| 6 | “對應的文件在哪,我給另一個agent看下” | 提供分镜、创意讨论和参考目录。 | 另一 Agent 后续修改，不能算本窗口自行完成的创意修正。 |
| 7 | “另一個agent改完了,你可以開始了” | 核对提交 `59e80dd`：采用落点方案 A，MC00 尾帧绑定已认可市政第 0 帧；旧生成近似图降为接近路线参考。之后继续做 Blender 城市 proxy。 | 继承了准确末态要求，但选择继续完整城市白模，后来被用户明确否定。 |
| 8 | “你這白模不是一拖史嗎” | 接受否决，预演标 FAIL，页面标已退回，保留失败证据。 | 没有把技术解码、尾速为零等当作质量通过。但在这之前白模已占用了制作过程。 |
| 9 | “有必要做白模嗎” | 承认没有必要默认做完整城市白模，建议改位置总图＋连贯写实参考，确有需要时才局部几何验证。 | 工具选择失当是本窗口应承担的问题；不是用户事先要求必须白模。 |
| 10 | “可以” | 按上述方向停止扩大白模，制作新 SVG 总图和写实参考。 | 用户认可的是准备方式调整，不是对白模、最终视频或任意正式准入的接受。 |
| 11 | “Hook stopped … maxBytes=1048576 … native_hook_stdin_oversized這個得先修復” | 暂停制作，核对真实图片 stdin 超限，将本机 OMX 两处 1 MiB 限制修为有限 32 MiB，保留错误拒绝；归档复现和针对性测试。 | 处理了工具传图阻断；这是本机安装热修复，不改善视频摄影质量，也不表示上游已修复。 |
| 12 | “生成视频我看看” | 最终提交一次 Seedance 2.5 首尾帧、20 秒、480p、原生音频试片。提交前又处理不同景别 contract、重复校验、首尾尺寸、表演验收和模型映射缺口。 | 付费视频只有一次，但生成前工程处理很长。实际仅两张首尾图进入模型，中间参考和路线没有直接绑定。详见下文。 |
| 13 | “直接停止,我让claude分析下为什么你做的不行” | 停止继续制作、重试和后续 Shot，给出试片目录及 FAIL。 | 停止已执行；当时给的材料主要是技术结果，没有完整呈现本表中的过程与用户反馈。 |
| 14 | “不对啊,没看到你做的过程,和我的反馈” | 只补写本记录和历史记录的状态提示。 | 不恢复生成，不替 Claude 作最终因果裁决。 |

## What Was Made Before The Video

第一阶段以 Blender blockout 处理城市和相机，随后又补写实图；用户指出不是只要一个 Shot，才扩成完整开场参考总览。参考范围应更早按整段事件组织。

在另一 Agent 修改落点后，Agent 又制作完整城市白模。20 秒、1280×720、无声音的预演 `MC00-previs-v3.mp4` 虽能播放，但城市展开／地标表达弱，设备被裁切，与照片端点没有可信对应。一次导出还因 Blender 媒体枚举设置失败；已知没有 MP4 后才进行有限本地修复。用户直接否决后，该版保留 FAIL，不作为后来模型参考或可行性通过依据。

白模文件在 `outputs/shizhen-episode01/MC00-previs-20261028/`，含 `build_previs.py`、`MC00-city-v3.blend`、`camera-samples-v3.json`、`qa/rejected-previs.json`。白模试片 SHA256 为 `c9ac5e2975cef56f9df4f9a144f1c6c222cd85167e957fde15778415c2f6488a`。

改方向后，新参考包是 `referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/`：可编辑 `city-map.svg`，屋檐、城市展开、下降写实候选，末态直接用原市政第 0 帧。首版城市图仍有高台和墙，第二版移除前方高台／墙、增加平街面接近路线；站棚厚框、广告面和工人手臂靠近控制盒等问题仍没有完全解决。独立静态复核也没有签运动、表演或站棚身份通过。

完整参考页在 [full-opening-references-20261027/index.html](../../referces/shizhen/macro-opening-20261027/full-opening-references-20261027/index.html)。其余镜头参考和原 B6 没有因为 MC00 的修订而重生成。

## Actual Generation Preparation

“生成视频我看看”后，Agent 没有立即得到可执行请求，做了以下准备和修复。这里列出是为了显示时间花在哪里，不能当作观看效果的成绩。

1. 现有首尾兼容校验要求 `same_subject_scale=True`，与屋檐近景到市政末态的景别变化冲突。新增可选 typed `scale_transition`，绑定 exact 首尾 SHA、相机空间／时长 hash 和 prospective evidence；其余校验继续保留。代码提交 `5ccfdf9`。它让受约束的不同景别意图可表达，并未让模型获得中间轨迹控制能力。
2. 首帧原图 1672×940、末帧 1920×1080，准备阶段拒绝尺寸不一致。用 FFmpeg Lanczos 将首帧技术缩放至 1920×1080，没有裁切、绘制或补内容。新建本地 v3 准备目录，v2 的准备失败没有发生付费视频提交。
3. feedback 层仍重复扫描 False，拒绝 canonical 校验已经允许的 typed 景别变化。最小修复改为复用 canonical 校验，提交 `c289b74`，有针对性测试和独立代码复核。
4. 草稿没有完整覆盖工人表演 acceptance；随后 native 编译发现相机、空间、光线、音频等约 50 个叶字段缺映射。通过现有 committer 修订 Project／Shot／QA，补明确中文表达和字段映射，最终提示词从 395／417 字修订到 459 字。没有删除原要求来绕过编译。
5. 最终 prepare 可执行、lint 通过后，才在原有 permit／预算／egress／durable intent 流程提交一次。前面的本地准备错误不计作付费视频重试；也不能因为本地流程通过而称导演意图通过。

代码验证记录：[camera-scale-transition-contract](2026-10-28-camera-scale-transition-contract.md)。相关 receipt：`.agent/harness/runs/camera-scale-transition-20261028/receipt.json` 和 `.agent/harness/runs/camera-scale-feedback-20261028/receipt.json`。这些只证明所测代码行为。

## Actual Model Inputs

本次使用 Seedance 2.5 原生首尾帧模式、20 秒、480p、16:9、原生音频。这个模式实际只接两张图。

| 实际输入 | 文件／身份 |
| --- | --- |
| 首帧 | `outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/first-frame-1920x1080.png`；SHA256 `9c7c08897a2c8ff30ea21de3560112491518a0cb2cb240e480615cd13cabefee` |
| 尾帧 | 已认可市政第 0 帧 `referces/shizhen/macro-opening-20261027/full-opening-references-20261027/MC01-normal.png`；SHA256 `a2cef0e9ff42796e09e72105bb04ea336149b4551a20dc767ffdd3179910eeed` |
| 实际编译提示词 | [compiled-native-prompt.zh.txt](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/compiled-native-prompt.zh.txt)，与 authored prompt 分开留存 |
| 请求身份 | resolved generation hash `89776e9fa6c18d15b8722e7625ab2e71f4ffa5defdbaa5af6e2913560cde2cb8` |

**城市总图、城市展开图、下降图、Blender 预演、prospective trajectory 均没有作为中间图／运动视频直接输入模型。** 总图、写实图和估计轨迹影响了文字与提交前判断；首尾模式并没有硬性约束模型逐点沿这些路径运动。展示过整套参考不等于整套都实际参与生成。

`prospective-trajectory.json` 是人为新设计的坐标验证，不是照片反求几何或真实成片相机数据。计算的碰撞、速度和末段停止只对这套设计成立，不能证明视频遵从。

## Paid Attempt And Exact Result

唯一新视频 attempt：`shizhen-macro-MC00-city-qualification-007`。提交回执时间 `2026-10-28T19:59:47.062933Z`。宏观累计实际视频由 6 次变 7 次，本轮新增 1 次，没有重试。旧楼梯／推门单元上限没有挪作 MC00。平台只读报价为 240 CRD，实际结算未暴露，不能把报价当最终扣费。

原始试片：[失帧-MC00-城市试片-480p.mp4](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/失帧-MC00-城市试片-480p.mp4)。文件 SHA256 `af1507969bb88b6be6379bfd991c8ba26864fd11a334e66144a4de371b8df5b2`，30,229,169 bytes，20.065 秒，854×480，AAC 立体声 44100 Hz。源下载和交付副本一致；没有剪辑、补片、变速或重编码。实测 481 个呈现帧、PTS 0–20 秒，不能把 nominal 60/1 头字段当真实运动帧率再变速。

播放页：[index.html](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/index.html)。页面保留原速原声试片，并另放原市政片对照，**没有完成 MC00＋市政的连续拼接验收**。

当前文件证据为 FAIL：

- 0–4 秒主要是近屋檐和狭窄道路走廊，城市没有按意图充分展开。
- 6–10 秒近楼体、墙和屋顶占据大量画面，主路与地标缺乏可追踪的连续关系。
- 棚体更像大面积围合设施雨棚，未保持 B6 的透明玻璃、细框、薄顶站棚形制。
- 末态的工人／控制盒／设备和门的关系比中段更接近目标，但不能因此认定全程或精确接点通过。

这些是 Agent 取样复核及 Gate 记录的失败项，不冒充用户逐项口头裁决。用户明确否定过白模，最终又要求停止并让 Claude 分析；本线程没有最终原速声画接受。

## Evidence And Limits

| 材料 | 能说明什么／不能说明什么 |
| --- | --- |
| [submit-result.json](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/submit-result.json) | 实际一次提交回执、请求身份与时间；不是质量通过。 |
| [delivery-verification.json](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/delivery-verification.json) | exact 文件、复制一致、次数、规格与保护声明；实际结算仍未知。 |
| [qa/post-media-gate.json](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/qa/post-media-gate.json) | action／camera／space FAIL；identity／performance／art／sound NOT_EVALUATED；禁止下一 Shot 和自动重试。 |
| [qa/video-analysis.json](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/qa/video-analysis.json) | 显式 project-local video-analysis 调用及技术信息；一个 scene 不能证明没有隐藏切镜。 |
| [qa/contact-sheet.jpg](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/qa/contact-sheet.jpg) | 采样中的城市和遮挡问题；不能证明全程建筑稳定或工人没重复按停。 |
| [qa/browser-playback.json](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/qa/browser-playback.json) | 浏览器原速、未静音播放至结束；不等于人实际完整听音并接受。 |
| [qa/audio-preview.json](../../outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v3/qa/audio-preview.json) | 仅 offline preview、network_calls=0；没有声音语义分析或人工听音通过。 |

市政保护源：`outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4`，SHA256 `b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d`。B6 保护源：`outputs/shizhen-episode01/fusion-B-motion-20261027/variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4`，SHA256 `d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a`。本轮交付核验记录二者未改；旧 MC03 楼梯 FAIL 仍阻止越过 Gate 的后续正式制作。

## Assessment For Independent Review

以下是 Agent 对自身过程的检查，供 Claude 独立核对，不声称已隔离模型失败根因：

1. **参考范围起初理解窄了。** 用户要整段开场，Agent 先集中一个 Shot，经用户指出才补全总览。
2. **工具选择失当。** 连续空间确实需要解释，但完整城市白模质量差，不能满足用户想看的摄影效果；应更早根据问题选择准备方式。用户没有要求为用 Blender 而用 Blender。
3. **展示参考与实际输入之间有落差。** 做了总图和中间图，但实际模型只有首尾两图。前期准备不能自动转换为模型可执行的中间运镜约束。
4. **已知参考问题没有消失。** 站棚形制和动作姿态仍有局限，参考包的静态可用性没有证明与 B6 的空间／身份连续性。
5. **工程修复不能弥补摄影失败。** 不同景别 contract、映射和校验修复使请求可合法执行，没有证明选定模式能实现这个连续城市揭示。测试和大量准备不等于影片更接近目标。
6. **停止时交代材料不完整。** 只给最后文件和 FAIL，把用户反馈及决策来回遗漏了，导致另一 Agent 难以定位偏离从哪里开始。

首尾模式能力、参考设计、提示词表达各自对失败贡献多少，本轮没有受控对照，不能凭一次结果下普遍结论。没有授权自动追加对照视频。

## Source Records And Publication State

- 分镜：[MACRO-SHOTBOARD-20261027.md](../../outputs/shizhen-episode01/opening-A-revision-20261026/production-inputs/MACRO-SHOTBOARD-20261027.md)；讨论：[MACRO-CREATIVE-DISCUSSION-20261027.md](../../outputs/shizhen-episode01/opening-A-revision-20261026/production-inputs/MACRO-CREATIVE-DISCUSSION-20261027.md)。
- 早期准备、完整参考和白模退回：[2026-10-27-shizhen-macro-reference-preparation.md](2026-10-27-shizhen-macro-reference-preparation.md)。
- Hook 独立中断：[2026-10-28-omx-native-hook-image-stdin.md](2026-10-28-omx-native-hook-image-stdin.md)。
- 工程景别修复：[2026-10-28-camera-scale-transition-contract.md](2026-10-28-camera-scale-transition-contract.md)。
- 历史已提交关键点：另一 Agent 落点修订 `59e80dd`；白模退回／准备 `ef6401d`；Hook `5833762`；新参考 `13fd16a`；参考校验映射缺口说明 `27b720d`；景别 contract `5ccfdf9`；feedback 重复校验 `c289b74`。
- 写本记录前实际 HEAD 为 `3bf4f4d`，其最新 skills 整理不是本记录新做的工作。`MC00-city-v2/`、`MC00-city-v3/` 原始运行交付目录此时仍为本地未跟踪文件，本记录链接它们，不夹带提交媒体／运行材料，不声称它们已远端归档。
- 本次仅补过程记录及旧记录的最新状态提示，保持其他 dirty／staged 工作。没有恢复媒体制作、付费调用、后续 Shot、重试或原始媒体变更；也没有刷新 RAG 索引。
- 本记录验证：17 个相对链接全部存在；14 条用户反馈逐条保留；重新计算试片 SHA 与 Gate／交付记录一致；`git diff --check` 和 `python3 -m scripts.docs_contract_gate check` 通过。代码测试与媒体分析没有因补记录重新执行。

自动学习评估：`no_candidate`。这里只有一次真实视频结果及相关准备链，没有可归因的多臂对照或两个独立视频实验支持普遍结论；不更新 Skill、Policy、Gate 或全局记忆。
