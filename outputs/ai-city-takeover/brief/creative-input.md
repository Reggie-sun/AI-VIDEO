# Creative Input（逐字保存，只增不改）

## 2026-10-30 · user · 初始需求

你是一支由技术导演、Motion Designer、AI 视频导演、音频工程师组成的制作团队。

我要使用 Claude Code 复刻 @anabology 的 ESCAPE VELOCITY 的视觉制作技术，最终建立能够持续制作高质量抖音短视频的工作流。

参考：
https://claudia.gallery/record/escape-velocity/readme/
https://claudia.gallery/record/escape-velocity/prompts-midjourney/
https://claudia.gallery/record/escape-velocity/prompts-seedance/
https://claudia.gallery/wiki/toolkit/

我也会提供目标视频截图作为视觉参考。

第一阶段：
1. 完整研究原作者的制作流程、模型 Prompt、镜头逻辑、颜色体系、动效、时间轴和 QA 机制。
2. 明确哪些素材由图像模型完成，哪些由 Seedance 完成，哪些必须通过程序化代码完成。
3. 重建视频的关键技术能力：Canvas/WebGL 动态 HUD、识别框、胶片印刷颗粒、歌词/标题运动、节拍同步、分层合成。
4. 不强制使用 Remotion，依据制作需要选择最合理的技术栈。
5. 先制作 10 秒 1080×1920、30fps 的原创测试片段，视觉目标为蓝黑色雾中公路、红色光轨、科幻 HUD、动态排版。不要照搬原片文案、音乐或完整镜头。
6. 测试片段的图片与动画可先使用本地代码和可用素材实现，确需调用付费模型时先列出预算。
7. 每次渲染后生成关键帧联系图，检查字体、画面层次、细节精度、动画连续性、节拍匹配，不达标就修改。

第二阶段：
在测试通过后，再扩展到 25–30 秒的原创抖音短视频，主题为《如果 AI 在凌晨接管一座城市》。

要求：
- 风格必须电影化、高级、统一，杜绝廉价科幻 UI 模板。
- Claude 负责总导演、分镜、实现、渲染和质量检查。
- 优先复用现有 Seedance、Suno 等能力，不假定未验证的接口一定可用。
- 保留可编辑工程、制作日志、生成提示词和输出视频。
- 首先提交架构分析与制作方案，然后执行第一阶段。
- 不要为了完成任务而降低质量标准。

## 2026-10-30 · user · 追加（执行中）

https://claudia.gallery/record/escape-velocity/readme/?utm_source=chatgpt.com

## 2026-10-30 · user · 追加（执行中）

为什么不用即蒙provider的seedance

## 2026-10-30 · user · 追加（执行中）

你直接用codex cli生图就好

## 2026-10-30 · user · 追加（執行中，看到豎版底片後）

我需要的是横版的
