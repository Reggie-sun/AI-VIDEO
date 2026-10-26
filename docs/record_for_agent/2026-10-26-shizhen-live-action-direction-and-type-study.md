---
record_kind: session_summary
topic_id: shizhen-live-action-rebuild
learning_eligibility: ineligible
---

# Lost Frames Live-Action Direction And Type Study

## Current Direction

用户要求重构宏观到微观的开场，随后明确“全部变成真人感觉”，并提供真人摄影质感参考。新视觉目标替换旧CG要求，其余剧情、关系、规则、音乐和保护原素材的要求继续有效。用户最后询问是否需安装motion/type技能，担心效果不足；实际核查后补装三个有用模块，不整包替换项目导演体系。

## Verified Work

全局安装 `motion-art-direction`、`animation-principles`、`kinetic-typography`。前两项来自iart-ai/motion-design-skills的 `3c129f769d90a1328c209c386492333c9ac62312`，后一项来自iart-ai/kinetic-typography-skills的 `fccc94bd325d824235ee9e715e65abde57b6513a`。安装后SKILL.md与定版上游原始bytes逐项相同。使用现有skill-installer脚本，没有安装新渲染依赖、改Product契约或触发工程workflow。

真人参考原图封存到 `outputs/shizhen-episode01/live-action-rebuild-20261026/reference/`，SHA `9ca118596b594808dcc429c2b8dd7083ab03c448b2d1e094f59a6b083873dbaa`；只迁移摄影观感，不复制人脸、挂绳或地铁场景。新目录包含导演/美术方案、两个中文Seedance2.5输入草稿、S01迁移说明及31段正片视觉范围。director coverage v4结构验证通过，未证明语义完整或媒体质量；执行准备明确 `execute_ready=false`。

复用既有P4/ResolvedTimeline/HyperFrames实际渲染两个3.5秒/84帧的1080p24字体测试：主片名SHA `1ae8b6bf039a984bb9fee99a065c6b84ac3d8582dc313db724b5ef14042bae99`，翌夜SHA `f0fd86c964d89d867aa26323e3780dda21683be4d5fbbd081f3c23405c2618ae`。前者复用原Suno B录音，后者无音轨。两次lint/check均零错误，实际MP4经显式project-local video-analysis MCP每0.5秒抽帧，中文完整、未见CG底图泄漏。只验证字形、版式与局部显现，不宣称空间文字合成、最终电影动态字体或故事开场完成。

## Evidence And Limits

审看入口 `outputs/shizhen-episode01/live-action-rebuild-20261026/index.html`。渲染记录在 `typography/render-receipt.json`；本地浏览器播放、MCP与来源保护记录在 `qa/`。8份原剧本、设计、S01、旧开场、A1及原音乐等来源哈希再次核对未变。旧CG raw判决和原Suno UNKNOWN历史未变，Manifest字节未变，没有Production activation或发布。

本轮新增付费视频/图像/音乐生成0次；安装为公开源码下载，本地字体测试没有生成调用。真人身份与空间参考、宏观动态画面、真人两位及S01还没有素材，完整声音聆听与全片七项导演审查均未完成。此时无法同时保留旧CG画面原样和实现全片真人观感；新视觉只能另作独立版本，保护原片不是继续混用旧风格。

## Remaining Work And Publication

后续先取得真人素材及任务内新付费授权，再沿原owner实际绑定profile、参考、preview和permit。旧额度与旧permit不复用，不以输入草稿冒充可submit请求。用户审片认可前遵守film-first，未做全量工程验证，相关新文件保持local/uncommitted，未push、未发布。这里是准备和后期局部测试的checkpoint，完整制作仍未完成。

## Learning Evaluation

`no_candidate`。安装及字体渲染不构成重复模型实验，也不证明新技能能稳定产生电影审美；没有把模块中的网页动效配方写入项目Policy、Skill或Gate。
