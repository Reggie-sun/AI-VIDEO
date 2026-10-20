# Seedance Prompt Length

## Official Guidance

截至 2026-10-21，火山方舟[创建视频生成任务 API 文档](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)
对 Seedance 2.0 系列（包括 2.0 Fast）和 2.5 给出的写作建议为：中文不超过 500 字，英文不超过 1000 词。
文字过长可能使信息分散，模型遗漏细节、只关注重点，导致生成视频缺少部分元素。

这是效果建议，不是 API 拒绝请求的硬阈值。目前未从该官方文档核实三个版本分别的 Prompt 硬上限；
不把第三方平台、网页输入框或项目自身限制视作模型统一限制。字、词、字符、字节和 token 不可互换。

## Runtime Behavior

Seedance 的 rich intent 经 `seedance_native_prompt.compile_seedance_request` 调用共享 prose compiler，
显式关闭共享 compiler 的旧本地 5000 字符限制。`SeedanceNativePromptBinding` 只要求非空文本并核验 exact
SHA-256，不再额外设置 65536 字符的本地 authoring 上限。来源保留、recipe coverage、sealed intent、
reference 与 request identity 的既有检查继续生效，系统不自动删减、截断或重写 Prompt。

其他 Provider 继续使用原来的本地编译边界。这次没有重新定义它们的官方上限，也没有修改公共字段、
Provider 选择、授权、预算、permit、重试或验收规则。旧 Prompt 在相同输入下的文本及 seal 不因长度设置改变。

不拒绝较长输入不代表 Provider 必然接受，也不证明长文本效果更好；实际服务端响应仍经既有 typed
failure/unknown 路径处理，不能因失败而盲目重试。官方字数建议由现有
[Seedance authoring 指导](../.agents/skills/seedance-authoring/references/authoring-common.md#prompt-length-guidance)
承载，不增加机器语言识别、自动摘要或第二套质量 Gate。
