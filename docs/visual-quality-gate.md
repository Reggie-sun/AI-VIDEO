# Overall Visual Quality Gate

## Scope

字体、配色、排版、画风一致性与整体观感进入现有 `QaPolicy.final_output`，仍由
Review / Repair 和 `ProductionStateCommitter` 裁决并持久化。没有新增 QA layer、
评分平均值、renderer 或第二套交付状态。旧 policy 未声明视觉要求时不追溯修改历史。

## Authoring

新建开发报告必须显式区分 `advertising` 与 `drama`，不能共用一份字体审美方向：
[广告方向](../configs/visual-quality/advertising.json)关注商业标题、品牌、CTA和条件说明；
[电视剧方向](../configs/visual-quality/drama.json)关注对白连续阅读、稳定位置、表演避让与
题材画风，并将片名等展示字与对白字幕分开。两份文件是独立 authoring 起点，不是
自动分类器或普遍适用的字体白名单；仍需根据具体作品明确字体、字号和观看标准。

`VisualDirection.content_kind` 显式声明类型后，factory 生成
`visual.advertising.<dimension>` 或 `visual.drama.<dimension>` requirement IDs。
即使方向文案相同，contract hash 也不同；广告证据不能通过电视剧合同的原有
exact identity 校验。选对作品类型由 authoring caller 负责，Gate 不从 MP4 猜类型。
两类共用 bytes、抽帧引用与完整观看校验，仍使用唯一 SEMANTIC / Final Acceptance
owner；电视剧对白准确性和同步仍由原 CAPTION Gate 负责，本次没有替换它。

兼容：已有未分类 `VisualDirection` 在 Python API 中继续可读，缺省字段不序列化，
旧 requirement ID、已封存 packet 和 `check` 行为不变。新私有 `prepare` CLI 要求
`--content-kind` 且必须与方向文件一致；旧创建命令需补该参数及显式分类的方向文件，
不能依靠默认广告类型。此变更不增加或改变公共 `ai-video` CLI 命令。

`visual_quality.VisualDirection` 保存五项具体期望，`visual_requirements(direction)`
将其转换为普通 `FinalOutputRequirement`，合并进完整用户目标的 requirements；
不得替换或删掉原音频、动作、叙事等要求。新 `visual_dimension` 可选，缺省不序列化，
旧 contract/hash 保持原样；启用时五项必须齐全且维度唯一。

示例方向：[ninebot.json](../configs/visual-quality/ninebot.json)。这是一套可修改的
具体 authoring 示例，不是适用于所有片种的默认审美或对旧成片的追溯授权。
将 contract 纳入 policy 后，仍通过原 `activate_qa_policy()` 显式选择，遵守原目标
版本规则；本工具不自动替换已激活 QA。

## Evidence And Gate

视觉 finding 仍在 `measured_payload.final_output.findings` 中，每项包含原
requirement ID、verdict、observation，以及 `visual_frames`：timestamp_ms、
frame_sha256、render_output_sha256。原 request/contract/tool/timeline/graph 绑定继续有效。
同一 observation 的 `visual_frame_inventory` 封存 duration_ms 与完整抽帧引用；
引用必须命中清单，时间必须在片长内，清单不得混用其他 MP4 或重复时间点。
Production 验证 selected evaluator 的测量声明，不重新解码 MP4/JPEG，也不证明
截图像素真实性；本地报告则重验实际 MP4/JPEG bytes 与 packet inventory。
缺少帧引用、引用其他 MP4、空白观察或遗漏要求不产生 PASS。

全片观感要求 `HUMAN`、`viewing_speed_milli=1000` 和 `viewing_mode=full_playback`。
抽帧可为明确局部 FAIL 提供证据，但不证明完整播放、文字驻留时间或真实人类观看。
工程检查验证证据声明与 identity，不具有辨别评审者说真话的能力。
若一项有效 FAIL，整体 FAIL；否则缺项或未评审为 NOT_EVALUATED。原最终验收入口
重新读取并裁决语义证据，失败或未知不能进入 Final Acceptance。

## Local Report

完整作品的开发侧审片使用 `prepare --contract /path/to/final-output-contract.json`，
同时提供该作品的 `--direction` 和 `--content-kind`。`--contract` 读取原
`FinalOutputContract`，保留 `goal_id`、`goal_version`、`user_goal` 与所有 requirements；
其中五项视觉要求必须与 direction 完全一致，差异在 probe/抽帧/建目录前拒绝。
叙事、表演、商品、声音等普通要求不会被视觉要求替换或过滤，任何有效 FAIL 都阻断
整体 PASS，缺项为 NOT_EVALUATED，仍使用同一个 `adjudicate_final_output`。

此模式产生 `visual-review-packet/2` 与 `review_scope=full_contract`。不传 contract
则保持旧 `/1` packet 和 `review_scope=visual_only`；旧 Python positional API、已有
packet 与旧合同身份继续兼容。HTML 显示原目标和所有要求，非视觉项使用原 requirement ID。
`full_contract` 仅描述 caller 输入范围：工具不会自动理解叙事、听音频、验证合同穷尽原意，
也不拦截 Agent 直接发链接。原始 brief 到合同的覆盖和审片纪律见
[Creative Completion Practice](../.agents/skills/open-video/references/creative-completion.md)。

以下私有开发工具读取现有 MP4，使用 ffprobe 与 ffmpeg 生成截图和 HTML；不写
Production Manifest、Registry、ReviewReceipt 或 FinalAcceptanceReceipt。

```bash
python -m scripts.visual_quality_report prepare \
  --video /absolute/path/video.mp4 \
  --content-kind advertising \
  --direction configs/visual-quality/ninebot.json \
  --output /absolute/path/new-review-folder \
  --timestamps-ms 1000 3000 6000 9000 15000 21000 24000 27000

python -m scripts.visual_quality_report check \
  --packet /absolute/path/new-review-folder \
  --answers /absolute/path/new-review-folder/observations.json
```

电视剧使用 `--content-kind drama --direction configs/visual-quality/drama.json`。
类型缺失或冲突在抽帧和创建报告目录前拒绝；改变类型需新合同、新 packet 和新评审。

先打开 `report.html` 看方向和截图，再复制 `observations.template.json` 填写实际
评审。帧引用必须来自 packet；未观察到的项目保持 not_evaluated，不能为了通过
填写 human 或 full_playback。`prepare` 成功退出 0 只表示材料已生成；`check`
只有开发侧 visual PASS 退出 0，FAIL/NOT_EVALUATED 退出 1，输入无效退出 2。

每次 check 重验 MP4、截图和封存 packet，清除旧派生 result/report 后重建，
防止换片后旧 PASS 报告继续留下。报告是可重算的开发侧观察，不是受控 human
host，也不具备签发 Production 验收的权限。

## Verification

`python -m pytest -p no:cacheprovider tests/test_production_visual_quality.py
tests/test_visual_quality_report.py -q` 验证逐项阻断、真实 committer/strict reopen、
旧序列化、实际 ffmpeg 抽帧、替换 MP4/截图、陈旧回答、HTML 转义与缺少全片观看。
Harness 的 `visual_quality_tests` 路由这些检查，相关 Review / Repair 回归继续执行。
测试通过不代表某条成片已达到用户的审美要求。
