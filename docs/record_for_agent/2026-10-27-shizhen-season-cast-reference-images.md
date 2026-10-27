---
record_kind: media_experiment
topic_id: shizhen-season-cast-reference-images
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Season Cast Reference Images

## Scope And Result

用户要求继续生成其他角色，并授权按文中的工作、地位、性格自主决定造型。依据当前第一季 Character Bible 和 Season Outline，新增16人身份合图：林晚、周竞、谢振宇、陆建平、许家良、邵庆国、梁秀琴、韩启良、宋秋萍、孟昭、何志刚、邹美玲、何淑兰、冯有年、赵明霞、乔立文。前四人另有各一张场次图；配角本轮先少量固定身份。没有替换此前林序、董文慧、罗敏、高峥、闻素芬、唐姐或快递员的素材。

入口为 `referces/shizhen/season-cast-20261027/index.html`，选用20张。每张身份合图含正面、四分之三侧面、侧面和全身。外貌由Codex查看后自主选用，不把用户授权委托等同于用户逐图验收。场次服装、雨湿、伤势、道具和姿势不写入永久身份。

## Known Outcomes And Repairs

内置 imagegen 共23次调用，23次已知返回，0个UNKNOWN；20张选用，3张未选历史原图保留。原新单元20次，因已知换手和角色辨识度问题有据扩到23次，未更改旧消费。周竞场次v1/v2存在跨格换手，最终v3统一右手持夹，左手示意；左右手本无剧情硬约束。邹美玲v1与林晚过近，v2选短发与更宽下颌，保持原角色事实。快递员旧背面UNKNOWN不在本轮，未重试。

全部实际提示词为中文。场次初稿实际绑定各自身份图，周竞修复绑定前一版本；原提示词、引用、输出及精确SHA保存在 `batch-manifest.json` 的23条attempts中。工具未暴露费用或积分，金额待确认，不猜报价。无新增视频或音频，无Production导入、激活或Registry/Manifest修改。

## Verification And Limits

已逐张查看23张原始返回图，核对20张选用图的面貌、比例、手部、物件与状态；全部输出解码与SHA核验，原文档和提示词SHA固定，当前总览链接逐一存在，本地Chrome渲染总览并查看截图。收据为 `referces/shizhen/season-cast-20261027/verification.json`。文档合同和owned-path whitespace检查通过；未修改runtime代码，不把静态检查冒充视频模型效果或人类验收。

Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：仅可逆的参考素材与归档说明，无production持久化写入。用户逐图审看、后续视频实际输入效果及动作连续性仍NOT_EVALUATED。图片本地存储，Git仅保存本次元数据、提示词和说明。

## Learning Evaluation

no_candidate：本轮用于具体角色造型选择和局部修复，未控制变量形成可推广的模型或工作流结论，不创建Learning Claim，不修改Skill、Policy或Gate。
