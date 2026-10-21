# Jimeng Web Canvas Operation Guide

Date: 2026-10-21

## Purpose And Status

本指南说明怎样用项目已安装的通用 Playwright MCP，在即梦网页画布上按镜头工作。MCP 提供浏览器控制；它不是即梦专用 API，也不会自动把网页功能变成稳定的项目 Provider。

资料优先级：即梦帮助中心链接到的官方画布手册是网页操作主来源；官方 Seedance 2.5 手册补充模式与模型输入说明；火山方舟文档只属于 API 提示词参考，不能代替消费端即梦 UI 的操作说明。

**证据状态：**已通过浏览器读取官方画布手册的入门、基础操作、资产管理、视频创作及时间线章节，以及 Seedance 2.5 手册的部分参数和功能说明。以下步骤属于文档摘要；本轮没有新建/编辑画布、上传、生成或下载。普通 web 抓取无法打开飞书链接，本轮使用公开浏览器页面读取，无需登录飞书。

**后续接口实测：**同日[源码与接口研究](../record_for_agent/2026-10-21-jimeng-interface-research.md)已完成三类直接存储上传、旧结果恢复，以及一次 Seedance 2.5 / 720p / 17 秒的图片+音频+视频同次生成、轮询与新 MP4 下载，实际扣除 442 积分。运行中独立客户端重连和保存后页面刷新均找回同一任务，没有重复生成。当前画布使用 `octo_api/v1`；生成通过正常网页原生 owner 发出请求，无需视觉点击，但仍依赖登录浏览器及 UI 内部方法。浏览器整体重启、登录失效、无响应提交恢复及长期稳定性未验证；媒体质量 Gate 仍为 `NOT_EVALUATED`。下文保留原文档研究的证据范围。

## Official Documentation Entry Points

### Jimeng Canvas User Manual

从即梦网页右下方的「客服中心」进入「新画布」分类，再打开「新画布使用手册」FAQ，链接到官方文档：[即梦画布｜使用手册](https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd)。这是目前最贴近画布操作的主手册。

页面署名 ByteDance，最后更新显示 September 18（年份未显示）。本轮按目录读取相关正文，未完整观看全部视频演示。下文只摘要已读章节，不猜测尚未验证的控件位置。

### Jimeng Seedance 2.5 User Manual

即梦帮助中心也链接到[【即梦】Seedance 2.5 使用手册](https://bytedance.larkoffice.com/wiki/RXh5ww6EqighMdkVTMccm2d4n7e)。文档标注 ByteDance，页面显示最后更新为 September 21（页面未显示年份）。本轮公开读取了「正式上线」「参数设定」及「功能交互」的部分内容；细节以该手册当前正文为准。

## Local Browser MCP

项目安装的是通用 `@playwright/mcp`，通过本机 `stdio` 启动并控制专用 Chrome；它没有一个供即梦调用的 HTTP 服务地址。[项目安装与 smoke 记录](../record_for_agent/2026-10-21-playwright-mcp-install.md)证明 MCP 已完成初始化、页面导航、快照和文本读取。该记录没有验证画布素材绑定、视频生成、历史查找或下载。

把 MCP 当作可观察、可操作的浏览器：读取当前页，再执行有明确目标的 UI 操作，并在模式切换、素材变更和提交前重新读取页面。不要从旧截图、别的平台界面或 API 字段推断当前控件。

## Canvas And Material Operations

按主手册「认识新画布」，访问[官方画布入口](https://jimeng.jianying.com/ai-tool/ai-canvas)，在列表中新建空白画布或打开已有草稿。画布、工具栏、素材与生成历史、生成器、Agent 面板分别承担内容组织、添加、查找、生成和对话工作。

按[画布基础操作](https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd#ZXmldMK9loFPWsxBkeucQbI0nnh)：

1. 按住 Space 或使用抓手平移，用鼠标、触控板或底部工具缩放。
2. 通过工具栏或双击空白处的菜单创建文本、图片、视频、音频节点。
3. 上传/拖入本地文件，或从即梦资产库、生成历史导入素材。
4. 搜索节点名称、文本或类型，点击结果定位。节点保存内容，连线表示引用或生成关系。

画布导入章节列出图片不超过 30 MB、视频不超过 500 MB、音频不超过 15 MB。这些是画布导入限制；模型作为 reference 接受的格式、大小、数量和时长另按模型手册及当前界面检查，不能混用。

按[资产管理](https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd#Acjmd7n0IoEfmHxdLOwc3GN2nLh)，可在生成器中选择主体资产作为图片/视频参考，也可将画布内容保存为主体供后续复用。素材出现在画布上，不等于已绑定到当前生成请求。手册另有主体资产专用输入规范，不应与普通文件导入限制混为一谈。

## Current Seedance 2.5 Entry And Modes

即梦 Seedance 2.5 手册「二、怎样更好地使用即梦 Seedance 2.5？— 2.功能交互 — 基础设置」记录的流程是：

1. 选择「视频生成」。
2. 选择「即梦 Seedance 2.5」。
3. 选择画幅比例、分辨率和时长。
4. 选择模式：手册列出「全能参考」「智能编辑」「超长视频」「首尾帧」。
5. 检查当前显示的设置和输入后，再点击生成。

上面是手册记载的入口，控件顺序和可选值仍以当前账号实际页面为准。手册同时出现 480p/720p 的通用参数说明，也展示过超长视频的 720P+ 示例；因此不要把该表当作当前 UI 的完整选项清单。

| 模式 | 手册支持的用途 | 操作边界 |
| --- | --- | --- |
| 全能参考 | 用文字和参考素材生成视频；Seedance 2.5 手册列出图片、视频、音频输入，并支持纯音频输入 | 具体素材插入和编号映射尚未通过 MCP 实测 |
| 首尾帧 | 输入首帧，或输入首帧与尾帧来约束生成 | 提交前核对起止素材；上传控件位置仍需当前页面确认 |
| 智能编辑 | 手册列为 Seedance 2.5 可选模式 | 详细控件与操作步骤待读取，不据模式名称推断能力 |
| 超长视频 | 一次生成 30–180 秒长视频，无需先做短片再延长 | 时长通过模式中的时钟/时间设置选择；这是独立模式，不是「视频延长」 |

## References And Prompt Binding

Seedance 2.5 手册「参数设定」给出以下模型侧素材范围，并与 2.0 分开列示：

| 素材类型 | Seedance 2.0 手册范围 | Seedance 2.5 手册范围 |
| --- | --- | --- |
| 图片 | 最多 9 张 | 30 张 |
| 视频 | 最多 3 段，总时长约 15 秒 | 最多 10 段，总时长约 30 秒 |
| 音频 | 最多 3 段，总时长约 15 秒 | 最多 10 段，总时长约 30 秒；支持仅音频输入 |

这是手册中的模型/输入参数说明，不是对当前会员账号、当前页面每次提交或网页上传校验的实测结论。实际可用数量、时长、格式和单素材限制，提交前以当前 UI 的校验结果及当日官方说明为准。

字节 Seed 的[官方示例](https://seed.bytedance.com/zh/blog/seedance-2-0-%E6%AD%A3%E5%BC%8F%E5%8F%91%E5%B8%83)使用 `@图片 1`、`@视频 1` 等写法描述参考用途；画布手册说明在生成器中选择参考素材。本轮没有实际执行 @ 插入，不能据此声称编号和素材映射已经通过 MCP 验证。操作时须回看生成器中的实际素材，删除、重排或切换模式后重新核对；仅写一个名字不能证明绑定完成。

电影/电视剧制作时，准备一份每镜输入清单：镜头意图、人物/场景身份、动作或状态承接、摄影参考、声音要求，以及每份素材希望模型参考的内容。把素材按它实际承担的职责说明清楚；生成后核对画面与声音。素材数量本身不证明模型使用了预期的参考。

## Long Video And Extension

官方 2.5 手册把「超长视频」和「视频延长」描述为两种不同工作：

- **超长视频**：在生成模式中选择「超长视频」，填写脚本/提示词，使用时钟控件选 30–180 秒，核对画幅、分辨率和时长后生成。这是一次生成长片段。
- **视频延长**：在生成流里找到一条不超过 30 秒的目标视频，点击其下方「视频延长」；用时钟控件设置新增时长，给新增部分写提示词，然后生成。原片保留，结果时长为原片加新增时长。
- 手册说单次延长可增加 4–30 秒，且最新底片仍不超过 30 秒时可再次延长；示例上限为 30 秒底片加 30 秒，得到 60 秒结果。

后两项是官方手册描述的功能边界，不是本项目或当前账号的实测结果。延长只说明平台提供延长路径，不能单独证明前后表演、空间或音画连续性合格。

## Generation, History, Download, And Recovery

### Generation And Result Selection

按[主手册：视频创作](https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd#Oxqbd9ybVo3r1uxvN5gcpScUnep)，创建视频节点，填写描述、添加参考、设置模型/比例/时长，再点击生成；结果保留在该节点。展开节点历史查看批次，同节点多轮结果可左右切换；预览画面和声音，选择满意结果设为主视频。右键「应用全部视频」可使用历史结果，操作前核对是否确实需要全部结果。

**项目操作建议：**提交前逐项回看输入，并记录对应 Shot、参考素材清单及页面显示的任务/结果标识。按钮点击成功不证明模型使用了预期素材。

### History And Export

主手册「资产管理」说明，生成历史按时间倒序记录项目的生成与编辑任务，可按类型筛选；点击结果定位并展开对应节点，原节点已删除时可从历史重新添加。

按[时间线与成片](https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd#MbhSdaYZ5oI1vexO0YwcfGNVn0e)，可创建时间线，加入视频/音频并调整顺序、位置及裁剪；完整预览后选择「导出」和规格，处理完成后下载到本地，或转到剪映继续编辑。

本轮已读章节没有核实单个视频节点的下载菜单位置，也没有执行媒体下载。后续需确认文件实际落盘并对应正确节点/批次；预览成功或拿到 URL 不等于已下载。即梦自身时间线不替代本项目的 `ResolvedTimeline` 与最终合成 owner。

### Recovery Limits

重新打开已有草稿、结合生成历史和原节点查找结果，是依据上述历史能力形成的操作建议，不是官方对仍在运行任务的可靠恢复承诺。本轮没有执行断线恢复测试。提交后结果未知时先核对状态，没有证据证明原任务未提交时，不重复生成。

## Verification Boundaries For Film And TV Work

浏览器操作证据只说明当前页面接受了操作。它不证明模型实际遵循导演意图、素材语义绑定成功、角色跨镜一致、剪辑连续或对白/环境声正确。

每个待验镜头都要检查下载到的准确成片，并根据项目规则运行逐 Shot 的媒体验收。项目要求 exact MP4 落盘后、下一 Shot 提交前运行 project-local `video-analysis` MCP；缺失或身份不匹配的证据不能推进镜头。字幕、配音、剪辑与最终合成继续由项目现有模块负责，手册中的 Seedance 功能不替代这些验收。

本指南描述的是通过浏览器操作消费端网页的工作方式，不代表已有自动化 Provider 闭环。完整的「Shot → 绑定 references → 提交 → 找回任务 → 下载 → 登记素材 → 验收」仍须逐步取证。

## Sources And Evidence Scope

| Source | Evidence in this guide | Limit |
| --- | --- | --- |
| [即梦画布｜使用手册](https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd) | 帮助中心链接，以及入门、基础操作、资产管理、视频创作、时间线章节正文 | 文档说明已读；未在用户画布执行写入/生成/下载；页面仅显示 Sep 18 |
| [【即梦】Seedance 2.5 使用手册](https://bytedance.larkoffice.com/wiki/RXh5ww6EqighMdkVTMccm2d4n7e) | 公开读取的标题、版本概览、参数设定和部分功能交互 | 页面更新时间只显示 Sep 21；未完整读取所有提示词章节或逐项验证账号能力 |
| [Seedance 2.0 正式发布](https://seed.bytedance.com/zh/blog/seedance-2-0-%E6%AD%A3%E5%BC%8F%E5%8F%91%E5%B8%83) | 字节 Seed 的官方 2.0 模型能力与体验入口说明 | 属于 2.0 发布资料，不作为 2.5 当前网页控件说明 |
| [Doubao Seedance 2.5 提示词指南](https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=zh) | 火山方舟官方 API 模型指导的范围辨析 | 不是即梦消费端操作指南；其 schema/参数不能推断网页行为 |
| [Project Playwright MCP installation record](../record_for_agent/2026-10-21-playwright-mcp-install.md) | 本机通用 Playwright MCP 已完成初始化、浏览器导航与读取的证据 | 未验证画布写入、视频生成、任务恢复或媒体下载 |

本机研究 receipt：[`.codex/tmp/jimeng-operation-doc-research-receipt.json`](../../.codex/tmp/jimeng-operation-doc-research-receipt.json)，绑定 8 份可见官方文档 capture 的 SHA-256，位于忽略目录、不随 Git 发布。生成提交、素材上传、新建画布、Production mutation 与客服消息发送均为 0。飞书采用虚拟滚动，本轮未把单次页面文本当成整份手册已读。
