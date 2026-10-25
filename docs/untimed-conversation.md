# Untimed Conversation Authoring

## Development Status

2026-10-25：用户确认继续后，统一编译拦截已追加到 working tree，与独立审查的候选字节一致；实际工作树365项相关回归通过，本集首镜重新完成零付费准备预检。精确 staged Harness 被共享 compiler 的其他窗口 unstaged overlay 阻断，尚未提交/推送。代码支持与媒体质量、模型资格分开判断；详见[本主题记录](record_for_agent/2026-10-25-untimed-conversation-contract.md)。

## Scope And Owner

原生多人对白可使用现有 `GenerationIntent.dialogue_intent` 的 `mode=conversation`。Schema、兼容性与严格加载归 `src/ai_video/production/video_requirement.py`；模型表达归现有 compiler，状态仍归 `ProductionStateCommitter`。此说明不新增执行、时间线或验收 owner。

首个适配目标是 Jimeng Provider / `seedance_2.5` 的原生声音路径，视频仍受当前 profile、素材、预算、permit 与 qualification 限制。不能根据契约存在推断自然表演、声线稳定、准确口型或真实出片质量已经通过。

## Authoring Example

```json
{
  "mode": "conversation",
  "language": "zh",
  "turns": [
    {
      "speaker_id": "xiaocheng",
      "verbatim_text": "慢点，里面烫。",
      "on_screen": true,
      "lip_sync_required": true,
      "response_obligation": "林序听到后略缩手，再接话。"
    },
    {
      "speaker_id": "linxu",
      "verbatim_text": "谢了。袋子不用。",
      "on_screen": true,
      "lip_sync_required": true,
      "response_obligation": "小程听完再抽纸垫到饭团下。"
    }
  ]
}
```

Turn 顺序就是交谈顺序，speaker、逐字台词、画内/画外、口型要求和反应义务分别封存。画内说话人必须属于当前 Shot Characters。画外声音不能要求可见口型。该模式不携带 scalar speaker、逐字全文、起止秒数或整体口型字段；每轮也不接受时间字段。片段总时长仍由现有 pacing/output profile 校验，演员在片段内自然完成动作、倾听和对白。

## Compatibility And Boundaries

`mode=none` 与原有定时单人 `mode=dialogue` 保留原输入与序列化，不给旧 artifact 增加空 turns，不重算历史 hash，也不把旧时间窗自动改成自然节奏。需要按用户意图修订时，经现有 authoring revision 路径显式产生新输入。

新模式不代表 separate voice、现有定时 source-expression、其他 Provider 或其他 Seedance 型号获得支持。未适配路径必须返回 typed unsupported；不能生成“Dialogue: none”，不能退回不含对白的 neutral prompt，也不能为了填满 schema 加入虚构台词时间。

## Evidence And Acceptance

编译预检应核对：exact provider/model/profile，实际素材身份，有序 speaker 与原句，原生音频启用，native prompt 无固定对白时间，未丢弃倾听/反应义务。无对白时间字段不等于模型能任意延长已封存片段；容量不足时返回导演调整片段预算或分镜。

逐镜仍需对 exact MP4 进行实际声音语义、说话人、口型、自然节奏和连续性检查。字幕可在原声通过后按实际声音对齐，不能用事后转写的字幕时间反向宣称已给演员分配台词秒数。工程测试、静态预检和模型请求成功均不替代声画验收。
