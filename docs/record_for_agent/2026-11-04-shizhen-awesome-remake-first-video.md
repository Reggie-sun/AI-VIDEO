---
record_kind: media_experiment
topic_id: shizhen-awesome-remake
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Shizhen Awesome Seedance Remake First Video

## Status

全新重做任务尚未完成。用户在看过新十二格 storyboard-v2 后要求“那你再用这个做出来视频我看看”。本轮实际新生成市政首镜一次，视频已下载，逐镜检查 FAIL，暂停后续提交。不是旧片复用，不是完整60秒成片，也没有人工认可或正式激活。

## Exact Evidence

- 输入与操作包：`outputs/shizhen-episode01/awesome-remake-20261104/municipal/`。
- 新 canonical root：`runs/shizhen-awesome-remake-20261104/municipal/`。
- attempt：`shizhen-awesome-municipal-preview-001`。
- 新参考板 SHA256：`1509083877457f82b02f8ef471353ade303c21b997c913f0d6640c812c76c177`。
- 视频 SHA256：`4df6946ac1e7b0bc47a6038d1814cea3aa6f3c1cc907b0183d7bced480458e4d`，20288751 bytes；审看副本 `municipal/municipal-new-001.mp4` 已核对一致。
- Seedance 2.0 VIP，multimodal，6秒请求，1080p，native audio；qualification only。整板仅软参考，不能声称已隔离前两格。
- 共享 driver → generation service → committer → Jimeng browser transport；一次 submit，无重抽。报价198 CRD，operator内部上限1500 CRD，实际结算待确认；paid状态accepted不等于结算证明。
- `prepare.json`、`prepare-bound.json`、`submit-intent.json`、`submit-result.json`、`fetch-result.json` 保存精确链路。
- 项目MCP `video_analyze` 实际调用；`video-analysis.json` 保留去除base64后的观察，`post-media-gate.json` 保存逐项裁决。

## Findings And Stop

视频约6.061秒，1920×1080，带AAC。0–1秒左侧操作者的手与右侧另一个工人同时出现，不符合“同一工人拉闸、松手、回看”的封存意图，FAIL。钢缆通往另一侧卷轴，未清楚证明拉动铁门到限位，NOT_EVALUATED。拉闸松手可见；连续右摇、无宫格可见。声音只证实有音轨，未进行语义观察，不签声音PASS。

后续镜头未提交。这个STOP属于工作流证据，不冒充Production生命周期写入或最终验收。下一步若修复，先准备单工人、清晰机械连接的干净参考并展示新exact预览；这只是待验证假设，不能照原输入盲重试。

## Remaining Full Opening Constraints

D1可生成4秒再按实际事件裁到3秒；B6的24秒必须分显式Shot，不能把多切镜谎报连续单镜。D3及站台双人需要分别身份参考，不能把同图bytes换asset ID冒充两张身份图。标准末帧handoff要求已激活来源，即梦qualification不能激活；后续须核查合法证据引用路径，不能假激活或声称完整合成已接通。

## Learning And Delivery

自动学习评估：no_candidate。只有一个未受控生成样本，不能归因于awesome-seedance或整板参考，更不能升级通用Skill规则。本轮未改业务代码、Skill、Gate，未安装依赖。全片未验收，按成片优先暂未commit/push；所有任务操作包与未验收结果保留。
