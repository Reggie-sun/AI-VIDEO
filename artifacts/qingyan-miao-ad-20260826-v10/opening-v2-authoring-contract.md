# Qingyan V10 Opening V2 Authoring Contract

## Diagnosis

`01_problem_open_cap_spray`不能作为第一镜。其 exact first frame 和 prompt 在开场已让女主手持青颜瓶，
因此观众读到的是“准备处理问题”，而不是“意外遇到问题”。这属于 `F-ACTION-ORDER` 与
`F-ACTION-OVERLOAD`：problem discovery、product introduction、cap mechanics、spray和relief被压入同一 Shot。

## Retired Opening Path

以下路径保持历史 provenance，但不得再作为 opening Shot：

```text
artifacts/qingyan-miao-ad-20260826-v10/prompts/01a_problem_open_cap_spray.txt
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.mp4
```

其中前约 1.6 秒的问题反应段不得在新 timeline中重复。后续只有在 exact MP4 通过 per-Shot Gate 后，
才可考虑从开盖动作起作为 treatment beat消费；这不等于当前已接受或已合成。

## Corrected Beat Boundary

| Order | Role | Product state | Visible action | Close state |
| --- | --- | --- | --- | --- |
| Shot 00 | `PROBLEM_DISCOVERY` | `none` | 天气热导致腋下出汗 → 出现真实汗印 → 女主抬臂检查 → 头部靠近被衣物遮挡的腋下并短促闻一下 → 轻微皱鼻 | 仍无产品；观众明确理解是腋下汗湿和异味顾虑，不是衣服故障 |
| Shot 01 | `PRODUCT_INTRO_AND_DEMO` | `explicit` | 动作切进入取产品 → 完整拔盖并落桌 → 裸露喷头后才喷 | 女主放松；单一大盖在桌面；单一瓶身在手中 |
| Shot 02 | `DIALOGUE_PROOF` | `explicit or capped hand-held` | 老人自然入场并发生产品推荐对话 | 双人自然微动；无静态 comparison |

第一镜的 `product_presence`固定为`none`；瓶子、盒子、喷头、盖子、品牌黄色、产品贴图和喷雾声均不允许出现。
衣物只承担可见证据：汗液来自腋下身体状态，形成局部汗印与轻微贴肤；不得表述成布料材质、衣服破损或穿着不适。
“使用前 / 使用后”由 Shot 00 problem state 与 Shot 01 relief state共同表达，不再单独插入静态 slider。

## Exact Control Frames

```text
artifacts/qingyan-miao-ad-20260826-v10/assets/00-problem-discovery-first-v2.png
SHA-256 0d5fe47955eb309cb3982fc904edeb58458474b95c5bd3ec782222990404065c

artifacts/qingyan-miao-ad-20260826-v10/assets/00-underarm-odor-sniff-last-v4.png
SHA-256 ba578d2a830a21ddd0b4cadc3e818fb83208362a4fd4c020293c97d58a63ad4f
```

对应 prompt：

```text
artifacts/qingyan-miao-ad-20260826-v10/prompts/00_problem_discovery_v2.txt
```

## Execution Barrier

新 Shot 00拟使用 H3/T8 `FL2VA`、`768x1344`、124 frames、24fps、20 steps、
`res_multistep` + `simple`、无 LoRA。当前 project-local `video-analysis` MCP preflight仍返回
`Transport closed`，因此禁止提交新的 T8 job。服务恢复后必须：单次提交 Shot 00 → 固定 exact MP4 + SHA →
requirement-level Gate全部`PASS` → 才允许处理 Shot 01。不得用控制帧、local contact sheet或旧 MP4替代 Gate。
