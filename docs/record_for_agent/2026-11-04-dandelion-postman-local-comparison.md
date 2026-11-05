---
record_kind: media_experiment
topic_id: dandelion-postman-local-comparison
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Dandelion Postman Local Workflow Comparison

## Scope

用户“那你用我现在的体系做一个呢”。本次保留已认可的蒲公英邮差故事、新参考图、12秒、Seedance2.0VIP multimodal、1080p和原生声音，使用本地open-video、event-led-timing、seedance-authoring/common与2.0 overlay重新表达动作。上一版也经过本地生成服务；区别是创作表达，不是换生成引擎。已经知道前版失败，非盲测；随机seed不可控，多个文字表达变化，不能声称受控因果实验。

## Exact Evidence

- 包：`outputs/dandelion-postman-local-20261104/`；canonical root：`runs/dandelion-postman-local-20261104/`。
- 同图SHA：`8125187d8eba4f1b9d13262ade2301c81391ccb756c32237b9b1ffebca68cd48`，未生成新图、未换身份。
- 新attempt：`dandelion-postman-local-001`，一次submit，无重抽；新node、新bound、新permit，未复用前版执行状态。
- 新原片SHA：`41f44af39d83658e30f5e86ca2fc4802d3da23ab154205745af1af491f76bb60`，31513323 bytes，12.065秒1920×1080、AAC。
- `production/prepare.json`、`prepare-bound.json`、`submit-intent.json`、`fetch-result.json`为操作证据；15项输入检查和prepare executable只证明结构接线。
- 项目video-analysis MCP实际观察，`production/video-analysis.json`与`step-observation.json`保存去base64结果；音义单次现有operator+fresh MCP记录在`qa/postman/audio-understanding.json`。
- 视频报价396积分、内部上限1500积分，结算待确认；音义观察内部USD0.05上限，账单待确认。未追加生成。

## Review

实际帧显示约2秒停稳，4秒开始出现脱离的种子，约11秒种子落头并保持。角色/右胯邮袋保持、单镜微推可见。严格两步计数含收脚过程仍未充分确认，不签PASS。音义模型识别wind/rustling/distant ambient noise、无speech segments，但未证明金属脚步与无音乐，NOT_EVALUATED。逐镜总状态NOT_EVALUATED，未正式激活或用户观感验收。

对照页`outputs/dandelion-postman-local-20261104/index.html`左前版、右本地版，分别播放防声音干扰。副本hash与canonical原片相同，未剪辑、未另建timeline。前版约3.5秒停稳、约9秒种子落头；这些是样本差异，不是哪个体系更好的结论。

## Record And Learning

record-ai-video-session记录；distill-ai-video-learning评估no_candidate：两版题材虽相同，但未隔离单一方法变量、已有结果影响创作，也没有重复试验支持通用方法结论。未修改业务代码、Skill或Gate，未做完整工程回归；按成片优先等待用户观感认可，未commit/push，未发布到外网。
