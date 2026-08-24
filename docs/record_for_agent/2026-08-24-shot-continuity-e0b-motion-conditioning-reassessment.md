# Shot Continuity E0-B Motion-Conditioning Reassessment

Date: 2026-08-24

## Purpose

本文在已完成的 Local T8 `E0-B` seed `320001` route-kill之后，冻结一次bounded、read-only root-cause reassessment与一个single-variable follow-up experiment contract。

本记录分类为`development_experiment_design`。它不重新裁决E0-B，不授权新的local/remote/paid submit，不是Production qualification、active capability、winner evidence、P6 Final Acceptance、`C4_DESTINATION_READY`、replay proof或release evidence。

## Reconfirmed Runtime And Workspace Boundary

- repository HEAD：`6fef5932cbdb447f2f44e5dbca85821ee3b2a43a`；本轮没有修改Production code、tests、workflow、Manifest或Registry；
- E0-B accepted evidence仍只有`124 + 102 + 102 = 328` frames；不存在770-frame / 32.083-second complete output；
- accepted manifest revision仍为`3`，segments 0、1、2分别绑定同一seed `320001`与同一prompt bytes；
- ComfyUI未运行，`127.0.0.1:8188`没有listener；本轮Provider/media effect为零；
- experiment-only Qwen full-scene与identity-crop references保持非canonical，不得升级为approved Character或Production reference。

## Confirmed Evidence

### Repeated Local-Window Stop Intent

E0-B accepted manifest中的segments 0、1、2保存了完全相同的prompt。该prompt包含：

```text
... continues walking, then gradually slows and comes to a natural stop near the end.
```

Installed T8 `long_video_orchestration.build_long_video_chain_plan()`对每个segment使用`segment override prompt`，没有override时回退到同一个`global_prompt`。它没有把“near the end”解释为770-frame global endpoint；因此当前E0-B graph会在每个local render window重新呈现一次stop-oriented intent。

### Persistent Static Reference Pressure

Installed T8 `build_long_video_conditioning()`在continuation中按：

```text
(segment_index - 1) % persistent_identity_interval == 0
```

决定persistent identity injection。E0-B使用`ScenePlusIdentity + interval 1`，所以每个continuation都加入full-scene first frame与identity crop两个non-timeline reference blocks。Upstream exact strategy提高过identity proxy，但没有通过预声明motion non-regression floor并保持`Experimental/default-off`。E0-B恰好同时观察到identity/scene基本稳定与motion amplitude快速衰减，符合该trade-off，但单次组合实验尚不能独立证明其因果份额。

### 22-Frame Tail Is Present But Not Sufficient

Installed T8 source验证continuation context必须来自紧邻上一segment，并从accepted context中精确截取22-frame video/audio tail。E0-B segment 0 median-flow mean为`0.9780`，说明进入第一个continuation前存在可见forward gait；segment 1仍降到`0.1852`。因此22-frame tail并非缺失，也没有证据支持改成5或39 frames；它更可能在首个continuation被其他conditioning压低后继续传播已经衰减的gait。

### Observed Failure Shape

| Segment | Median-flow mean | Retention vs segment 0 | Interpretation |
| --- | ---: | ---: | --- |
| 0 | `0.9780` | `1.0000` | 可见medium walking |
| 1 | `0.1852` | `0.1894` | 第一个continuation已显著减速 |
| 2 | `0.0348` | `0.0356` | 第二个continuation接近原地步态 |

第4段在6/20 steps被targeted cancel；没有segment 3 candidate，因此不能声称后续必然单调降到零，也不能用未生成的frames补足因果证据。

## Root-Cause Hierarchy

1. **Primary testable trigger — local-window prompt reset.** Manifest与planner source共同确认stop-oriented global prompt在每个segment重新生效；failure从第一个continuation开始，时间形状与重复settle intent一致。该机制事实已确认，因果权重仍需single-variable A/B。
2. **Strong co-driver — `ScenePlusIdentity + interval 1` static-reference pressure.** Source确认每个continuation注入两张static references；upstream与E0-B都显示identity improvement / motion regression trade-off。它很可能放大prompt reset，但本轮不改变identity strategy或interval。
3. **Propagation path — 22-frame latent context.** Context存在且包含segment 0 forward gait，因此不是首要缺失项；segment 1降速后，它会把较弱gait继续传给segment 2。没有证据授权改变context length。
4. **Missing control surface — per-segment motion-state relay.** 当前chain没有global timeline-aware motion state，只重复同一个local prompt。Existing `segment_prompts_json`可以逐segment替换prompt，且不需要引入`Prompt Relay Advanced` attention patch。

这个hierarchy不宣称已把prompt与static references完全因果分离；它只选择最可证伪、最少新增patch owner且满足single-variable纪律的下一实验surface。

## Selected Single Variable

唯一changed variable为：

```text
prompt_temporal_allocation:
  repeated_stop_oriented_global_prompt
    -> per_segment_motion_state_schedule via segment_prompts_json
```

不使用T8 `Prompt Relay Advanced` attention patch。该patch会改变target-video query到local-text keys的attention logits，并形成新的experimental conditioning implementation surface；把它与per-segment prompt schedule同时引入会破坏单变量归因。

## Proposed Experiment Contract

### Identity And Classification

```text
experiment_id: shot_continuity_e0c_prompt_schedule_relay_v1
classification: development_experiment
execution_state: contract_only_not_authorized
comparison_owner: E0-B seed 320001 STOP record remains immutable
```

### Frozen Surfaces

以下全部保持E0-B exact不变：

- Local ComfyUI / MiniMax H3 T8 only；remote submit `0`、paid effect `0`；
- diffusion/model、CLIP、video VAE、audio VAE bytes与E0-B recorded hashes；
- `ScenePlusIdentity`、full-scene reference SHA-256 `a0eea9c27536c914c988e793682c21a2f31174df4ce39fb95861711180955336`、identity-crop SHA-256 `7e71030f3cad5e3049143be2169b5933711a80dbd277ea76025490b253dcafac`、persistent interval `1`；
- 22-frame AV latent context；
- seed `320001`，fixed across all segments；seeds `320002`、`320003`、`320004`仍不得运行；
- `1344x768`、24fps、目标`770 frames = 32.083333s`；不得降分辨率或缩短时长补考；
- Stock20、20 steps、`dual_clock_euler/native_flow`、video/audio shifts `12/3`、Turbo LoRA off；
- native audio、H.264 CRF 17、release policy`unload_all_models`；
- `max_retries=0`、fallback `0`、parallel segment `0`；
- identity、wardrobe、red satchel、scene、screen-right direction、camera language、soundscape与negative constraints。

Seed `320001`只作为未来counterfactual control冻结，以避免seed成为第二变量。当前用户指令明确禁止本窗口重跑该seed，因此本合同本身不授权执行；任何未来submit必须得到新的、明确覆盖该no-rerun guardrail的task authorization。

### Exact Prompt-Derivation Rule

Source prompt是E0-B frozen prompt，SHA-256按结尾单个LF计为：

```text
d65e4f9337c8f5b26854b3f413e61a6485ae1d2ab288bce3a87739fbcae1f22b
```

每个segment prompt只允许把source prompt中下面这一个exact sentence替换一次；其它bytes保持不变：

```text
She passes concrete columns and glass windows, briefly turns her head toward a departure display without changing identity, continues walking, then gradually slows and comes to a natural stop near the end.
```

Replacement variants：

```text
steady:
She passes concrete columns and glass windows, briefly turns her head toward a departure display without changing identity, and continues walking at the same medium speed through the end of this segment. She does not decelerate or stop in this segment.

decelerate:
She passes concrete columns and glass windows, briefly turns her head toward a departure display without changing identity, continues walking at medium speed for most of this segment, then begins one gradual physically plausible deceleration in the final third while remaining in forward motion at the segment end.

stop:
Continuing directly from the incoming gait, she completes the single gradual physically plausible deceleration and comes to one natural stop only in the final accepted frames of the 770-frame take.
```

Derived full-prompt SHA-256 values，均按结尾单个LF计算：

```text
steady:     51715a9b7a0a25017c5958147984e1000b527468390ac6973acb47e7652911c1
decelerate: f6c151b3a0f38582dbd3b8c1177da943aced49db8d28f823d470bd012ce91e38
stop:       1cbdef638176de83372f053a64631923cffe8a09ba77a42a89a00a9aeae7be2f
```

`segment_prompts_json` schedule冻结为：

| Segment | Accepted timeline frames | Prompt variant | Required motion state |
| --- | --- | --- | --- |
| 0 | `0–123` | `steady` | 建立medium forward gait，不settle |
| 1 | `124–225` | `steady` | 继承并保持gait amplitude |
| 2 | `226–327` | `steady` | 继承并保持gait amplitude |
| 3 | `328–429` | `steady` | 继承并保持gait amplitude |
| 4 | `430–531` | `steady` | 继承并保持gait amplitude |
| 5 | `532–633` | `steady` | 继承并保持gait amplitude |
| 6 | `634–735` | `decelerate` | 只在final third开始一次减速，segment end仍前进 |
| 7 | `736–769` | `stop` | 只在770-frame take的final accepted frames完成一次stop |

Planner必须使用existing `segment_prompts_json` override；不得同时启用`Prompt Relay Advanced`、EAV、MultiKeyframe、Hybrid artifact、Turbo或另一个conditioning patch。

### Frozen Route-Kill Rubric

- segments 0–2继续使用与E0-B相同的motion measurement method；
- 对segments 1与2，`median-flow mean / segment 0 median-flow mean`必须各自`>= 0.50`，并在raw full-speed review中保持可见forward displacement；任一不满足即`STOP`，最晚在328 accepted frames停止；
- identity、beige trench coat、red satchel、scene与screen direction不得出现相对E0-B新增的fatal regression；
- segments 0–5不得提前settle或进入repeated gait loop；segment 6允许一次可见减速但必须保持forward motion；segment 7才允许完成stop；
- OOM、crash、unknown outcome、seam、identity/scene drift、motion collapse/loop、结构崩坏或用户NO-GO均为`STOP`；
- `CONTINUE`只允许按同一合同继续剩余segments，不允许换seed、prompt variant、threshold、reference、interval、context、steps、resolution或fallback；
- 即使完整770 frames通过，也只产生new `development_experiment` evidence，不自动进入six-shot baseline、Production qualification、capability activation、P6或Final Acceptance。

## Why This Does Not Rewrite E0-B STOP

- E0-B原始treatment是同一stop-oriented prompt在每个local window重复；该exact treatment对seed `320001`的verdict永久保持`STOP`。
- Proposed E0-C显式改变`prompt_temporal_allocation`，所以它是new treatment，不是对E0-B partial重新打分。
- 当前没有执行submit、没有新segment、没有770-frame output，也没有把328-frame partial描述为完整32秒成片。
- experiment-only Qwen reference仍是同一非canonical limitation；新实验无论PASS/FAIL都不能升级它。
- 新实验若PASS，只支持“per-segment prompt schedule改善该exact material/seed的motion retention”；不能证明`ScenePlusIdentity`已普遍解决、32秒能力robust、six-shot baseline通过或Production ready。

## Repository, Provider And Media Effects

- Repository：只新增本reassessment/contract record；Production code、tests、workflow、canonical spec/plan、runtime baseline、Harness policy、Manifest与Registry均未修改。
- Provider：local submit `0`、remote submit `0`、paid effect `0`、fallback `0`、retry `0`。
- Media：没有启动ComfyUI，没有生成、拼接、修改或删除任何视频、图像、音频或preview。

## Next One Thing

在新的明确task authorization覆盖当前`do not rerun seed 320001`边界前保持停止。若未来获得该授权，只执行上面一个E0-C `prompt_temporal_allocation` treatment，先按328-frame route-kill gate判断；不得同时改变任何其它surface，也不得自动进入six-shot baseline。
