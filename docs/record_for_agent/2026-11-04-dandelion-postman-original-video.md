---
record_kind: media_experiment
topic_id: dandelion-postman-original-video
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Dandelion Postman Original Video

## Request And Scope

用户明确“不要用之前的图和剧情,你用这个skill重做视频我看看”，并在新《蒲公英邮差》参考图展示后回复“可以”。新故事、新机器人、新图片、新视频，未复用《失帧》媒体或剧情。使用 awesome-seedance 的 seedance-production-workflow 固定版本67df3707a4f25f860088790fb0a74d8f99a50cbb，采用单镜、参考职责、入口出口和真实结果检查；未安装或执行上游脚本。沿既有canonical生成服务执行。

## Evidence

- 工作包：`outputs/dandelion-postman-20261104/`，运行根：`runs/dandelion-postman-20261104/`。
- 参考图 SHA256：`8125187d8eba4f1b9d13262ade2301c81391ccb756c32237b9b1ffebca68cd48`。
- 视频 SHA256：`554aad1f910e2c142385a236e7ff72a32bd880e6eef4eadc974e2224799af0da`，31778915 bytes，12.065秒，1920×1080，AAC原生音轨。
- attempt：`dandelion-postman-preview-001`，Seedance2.0VIP multimodal，12秒、1080p、一次提交，零重抽，qualification。报价396 CRD，内部1500 CRD上限不是价格；实际结算待确认。
- `production/prepare.json`、`prepare-bound.json`、`submit-intent.json`、`fetch-result.json`保存执行链；输入只有新图。离线prepare executable、输入lint通过，不代表质量验收。
- 项目MCP实际video_analyze，另按0.25秒间隔观察脚步；证据`production/video-analysis.json`及`step-observation.json`。未剪辑观看副本`dandelion-postman-001.mp4`与canonical bytes hash一致。
- 音义观察经现有单次development operator和fresh项目MCP执行，USD0.05内部上限，账单待确认。初次MCP子进程PATH缺少现有ffmpeg，音轨提取失败、无POST、unit未消费；核对仅intent/reservation/lock后补现有miniconda bin路径，原未消费unit单次执行成功。保留初次失败及`qa/postman/audio-understanding-repaired.json`，未重生成视频。

## Review And Delivery

一个机器人与邮袋保持、种子飞散、抬头、落头并停留、连续微推在实际帧观察中成立。0–3.5秒步数明显多于封存的“两步”，FAIL。音义模型报告风、草叶、类似雨声及滴水，没有speech segments；未确认轻金属脚步声及无音乐，声音项NOT_EVALUATED。逐镜总体FAIL，未签正式激活、完整QA或人工观感接受，未继续重抽。完整原片作为审看结果交用户，不能把一次案例当作Skill效果证明。

## Record And Learning

记录与自动学习评估：no_candidate。没有控制变量对照，也没有支持同一方法结论的独立重复实验。本轮仅制作任务操作脚本、输入、证据与新媒体，无业务代码/Skill/Policy/Gate改动；未运行完整工程回归。按成片优先等待用户观感认可，未commit/push，未发布到外网。
