# MiniMax H3 / T8 能力评估与集成建议（2026-10-21）

调研对象：`github.com/T8mars/comfyui-minimax-h3-audio-T8` HEAD `e576eba`（2026-10-20，版本 1.101.0）
对照基线：本仓库当前 sealed runtime
证据等级：**[已验证]** = 本机源码直接证 / 实跑 / 独立 cross-check；**[作者声明]** = 仅 T8 changelog/doc；**[结构]** = 仅 CPU/单元测试

---

## 0. 执行摘要

> **最重要的结论不是"该加什么功能"，而是"几乎所有被宣传的 T8 新功能都不解决本项目的真实瓶颈，并且其中相当一部分在本机硬件上会静默不生效。"**

1. **版本落差是实的**：本项目 seal 在 T8 `1.36.2@977df788fcf8`（2026-08-21），T8 HEAD 相距 **135 个 commit**；T8 自身的 V3 `comfy_entrypoint()` 已注册 **738 个唯一节点 ID**（`features.json`），但仓库 `tests/test_preflight_and_registration.py:19` 仍断言 `len(ids) == 371`，**两值已经不一致**。本项目侧全部 seal 仍指向老 schema。

2. **本项目真实瓶颈不在功能缺口，在稳定性**。17 秒 Ref2VA 任务在 `comfy_kitchen.int8_linear → torch.cat(scaled_parts)` 路径上 6 次连续物理提交全部 OOM（`docs/v0.2-runtime-baseline.md:1012-1053`）。Turbo v2 虽可达比 Quality v1 快 65.6%，但 **audio ≈ -52.5 LUFS 几乎不可闻、motion/detail 弱**。这条质量-速度空隙才是要找答案的地方。

3. **T8 新能力命中该空隙的候选几乎都附带严重警告**：
   - 唯一有希望的真候选是 **Wuli Native 8**（19.9 GiB INT8 ConvRot、CFG1、8 步、shift 12/3）；
   - 其它热门能力（Spark、Sage Kijai、Sol-Attn、Veda、FreeVideo、视觉标记、Semantic Bridge、AudioFirst）经源码核实**至少有 5 个会在 5090 上静默失效或回退**。

4. **真正明确、低风险、且完全不依赖 T8 的增量在云端官方 API 侧**：本项目 `src/ai_video/production/minimax_h3.py:200-202` 直连被限死在 `768P/4s/16:9` T2V、`max_reference_count=0`；官方实际支持 2K（$0.13/秒）、9 张参考图、首尾帧、3 段参考视频、3 段参考音频、H3-Context-IR、Regenerate (`base_video` 或 `source_task_id`，二选一)。

5. **建议的净结论**：本轮**不整体升级 T8 大版本，也不逐一引入 1.85.0→1.101.0 的小特性**。仅做两个受控 A/B（Wuli Native 8 + 官方 API 能力补全），并把 T8 的工程纪律（UUID 身份、canonical SHA、Stage Save/MID resume、fail-closed 状态机）作为**借鉴模式**而不是依赖其实现。

---

## 1. 项目侧当前真实能力（已验证）

| 能力 | 现状 | 证据 |
| --- | --- | --- |
| 本地 H3/T8 Provider | `comfy-local-h3-t8` family，6 个 child capability，全部 seal | `src/ai_video/production/local_h3_provider_family.py:101` |
| Quality v1 | 20 步 / `res_multistep` / `simple` / 1344×768 / 124 帧 / 无 LoRA | `comfy_t8_video.py:66,226-244` |
| Turbo native v2 | 4 步 / `dual_clock_euler`+`native_flow`；wall 119–155s；peak GPU 19932–26797 MiB；peak RSS ≈ 58 GB | `comfy_t8_native_turbo_profile.py:267`、`docs/v0.2-runtime-baseline.md:1173` |
| Turbo v2 代价 | motion/detail 弱；audio ≈ **-52.5 LUFS 几乎不可闻** | `docs/v0.2-runtime-baseline.md:1173` 独立 review |
| 云端 Provider | METASO H3（9 参考图）、官方 H3 Max（480P/768P）、官方 H3（仅 768P/4s T2V）、Hailuo、Seedance、Vidu、Grok | `metaso_h3.py:148`、`minimax_h3_max.py:37-40`、`minimax_h3.py:200-202` |
| 音画同步 | 双时钟采样 `shift_video=12.0 / shift_audio=3.0`；HyperFrames 独占 mixer | `comfy_t8_video.py:236-237`、`video_retime.py` |
| 连续性 | 十维因果契约 + `state_reference` + sequence owner 签发 | `video_transition.py`、`docs/agent-primary-contract-matrix.md:192` |
| QA | Per-Shot post-media Gate + `video-analysis` MCP + content-addressed receipts + 唯一 committer | `quality_gate_coordinator.py:358`、`ProductionStateCommitter` |
| 17s 长片 | 6 次提交全失败；0 MP4；OOM 根因为 `torch.cat(scaled_parts)` | `docs/v0.2-runtime-baseline.md:1012-1053` |
| 30s 成片 | 由 6 镜拼接；1344×768@24fps；720 帧；30.000s | `runs/drama-h3-t8-30s-preview-20260830-final-v2/outputs/*.mp4` |

### 1.1 项目架构的现实约束（任何 T8 适配都绕不过去）

- **唯一 selector**：`VideoGenerationResolver.resolve_requirement()`（`docs/agent-primary-contract-matrix.md:463-466`），不接收外部 `selected_capability_id`；
- **零 provider 隐式 fallback**：`VideoProviderRegistry` 明确无 selection/fallback；
- **唯一 writer**：`ProductionStateCommitter`，且 `ARCH104` 强制；
- **节点 schema 双层 seal**：T8 节点逐个封 `schema_sha256`，profile 再用 `workflow_sha256` / `binding_sha256` / `profile_content_hash` 三重封；
- **穷举 widget 映射**：`src/ai_video/workflow_loader.py:13-106`（`ARRAY_WIDGET_NAME_MAP`），未知节点类型直接 `WORKFLOW_INVALID`；
- **MCP 只读**：`video-analysis` MCP 不写 Manifest / Registry / activation / P6 / Final Acceptance；
- **ATTENTION owner**：`optimized_attention_override` 是单槽位，Keen 的 RunSage 与本项目的 SageAttention 2.2.0 必须严格共存契约。

这些约束共同决定了：**任何 T8 引入必须在新模板（template/binding/profile）层级 + 新 capability_id + 重新 seal，且只取"已验证且可证明"的特性**——包装一个华而不实的特性等于破坏全部 seal。

---

## 2. 关键证伪与核实（不是"它们说能做"，是"它们实际能做"）

### 2.1 [已验证] T8 节点规模与测试基线不可信

| 实测事实 | 证据 |
| --- | --- |
| **0 个 `NODE_CLASS_MAPPINGS`**；改用 V3 `comfy_entrypoint()` | `t8/__init__.py:187-216`（用户原问的"922 个节点"在源码里**不存在**） |
| `features.json` 列 **738 个唯一节点 ID** | `features.json`（实测 `len=738, unique=738`） |
| `tests/test_preflight_and_registration.py:19` 断言 `len(ids) == 371` | 已与 `features.json` 不一致 —— **自动化基线已破** |
| `tests/` 984 个 .py / 179k 行，几乎全部 **CPU-only 结构测试** | `tests/test_freevideo_quality.py:1` 显式 "CPU only, no model downloads"；`test_token_lora.py:247`、`test_h11_wuli.py:53`、`test_audio_first.py:47` 全部 `assert not torch.cuda.is_initialized()` |
| **没有任何 GPU smoke 测试套件**；GPU 证据只在 `docs/*.md` 散文记录中、无法自动复跑 | 全仓 `tests/` grep `cuda` ≈ 0 命中（除显式禁用） |

**结论**：不能再用"T8 测试通过"作为成熟度信号。任何要在 5090 上跑的特性都必须自己重做验收。

### 2.2 [已验证] 三类加速路线在 RTX 5090 上会静默失效

| 路线 | 失败机制 | 证据 |
| --- | --- | --- |
| **Spark Attention** | **硬门 SM89**；5090 是 SM120，`spark_runtime.py:286-297` 静默委托 dense | `h3_t8/spark_runtime.py:286-297`；节点显示名写死 `(SM89)` |
| **KJ Sage** | `res_kj_sage_identity.py:104,107,132` 同样 SM89 硬门 → RES 缓存资格失效 | 同上 |
| **Sol-Attn** | 没有 `get_device_capability` 检查；kernel 抛错被 `sol_attn_minimax_v2.py:639-642` 的 bare `except` 吞掉，fallback dense | `sol_attn_minimax_v2.py:402-421,639-642` |

**通用陷阱**：T8 `AGENTS.md` 与 `PATCH_STACK_POLICY.md` 明确禁止"未验证就拒绝执行"——所有"不生效"都以 warning 形式出现，**节点不会变红**。验收唯一可靠手段是逐次读 `report_json` 的 `scope_effective` / `actual_*_calls` / `delegate_reasons`。

### 2.3 [已验证] FreeVideo 不是加速路线（含更多负证据）

- 引擎本体 **不在仓库**——`find . -name freevideo_engine` = 空；只是 `t8/h3_t8/freevideo_exp/worker.py:44-59` 的子进程适配器，调用**独立 Python 3.12** + 上游 pinned VDN/Triton/Diffusers；
- 分辨率上限 **448×256 → learned 1.2× → 512×288**，比项目 1344×768 低 **7.5 倍像素量**；
- **整图约 608 秒**（`docs/FREEVIDEO_EXP.md`），与项目 1344×768 的 5 秒片（10–15 分钟）**耗时不构成数量级优势**；
- LoRA 不兼容（"暂不支持需要 fused 重建/调制投影的 LoRA，不自动回退"，作者原话）；
- 路由 `choose(..., attention="cudnn", available_backends={"cudnn"})`，**无回退**——5090 上要么跑通要么硬失败；
- 三个 Apply 节点 `mode` 默认 `report_only`（`freevideo_exp/nodes.py:148`）——**不设 `apply_exp` 等于不走**；
- 唯一真实价值是 **Stage Save/MID resume** 工程的纪律（`freevideo_exp/runtime.py:263-301`、`split_runtime.py:89-124`）。

**真实可借鉴**：Stage Save/Load + MID 续跑的工程纪律值得参考。但要不要为这个改造本机质量基线？→ 见 §5.1 方向 3。

### 2.4 [已验证] Veda 不是加速路线，反而更慢

| 实测 | 数据 |
| --- | --- |
| 作者 4060Ti 上 dense vs Flex sparse | **628.187s vs 1266.219s —— sparse 慢 2.02×**（`docs/VEDA_SPARSE_T2VA_EXP.md:189`） |
| Heuristic 5% 接触表 | "明显比 dense 更暗、构图也不同"（`:213`） |
| Kernel 名实不副 | `veda_r2va_runtime.py:65` 写死 `"t8_pytorch_flex_not_upstream_int8"` —— 用的是 PyTorch FlexAttention，**拿不到上游 Triton INT8 性能** |
| 默认 `report_only` | `nodes_veda_r2va.py:44`、`nodes_veda_sparse_exp.py:69`、`nodes_veda_heuristic_exp.py:29` |

**结论：弃 Veda。**

### 2.5 [已证伪] 视觉空间引导不是空间约束

- 自述："Opt-in visual annotations and deterministic text, **not a spatial sampler**；Plans describe **source-image rectangles, not generated-video coordinates**"（`h3_t8/visual_marker.py:1-3`）；
- 真实机制：彩色矩形画进输入 IMAGE 走普通 VAE encode，描述文字追加到 prompt 走 CLIP Text Encode，**无 `attn_mask` / 无 latent mask / 无 regional token / 无 per-step 重施加**；
- `features.json` 自认 **`marked_and_split_marker_residue_observed: true`** —— **成片里确实残留色框**；
- `visual_marker_binding.py:129-130` `old_embedding_modified: False`，全仓**零代码读** `t8_visual_marker_binding` 这个 metadata key。

**对比项目**：白模参考（Blender blockout）+ 十维因果契约是被 Gate 实际验收过的空间/状态约束。**T8 视觉标记是净退步。**

### 2.6 [已证伪] Semantic Bridge 不是 LoRA 级注入

机制是**对 conditioning 一次插值**：

```python
# h3_t8/semantic_bridge.py:337,415（逻辑摘要）
out = h + alpha * (MLP(h) - h)   # 默认 alpha=0.10 → 10% 偏移
```

- 输入只有 CONDITIONING；**不注入主网络、不碰 `nn.Module`、无 forward hook**；
- grep `nn.Module | state_dict | register_forward_hook` 在三个相关文件里 0 命中；
- **多桥直通会被直接拒绝**（`semantic_bridge.py:355-356`），要走显式 Compose 节点做 **ordered_serial**（`:465-471`，作者原话："not additive LoRA merging, multiple bridges can worsen picture/voice quality"）；
- 作者自述："局部改善，不保证所有镜头有效"、"可能退化声音"。

**结论**：默认 10% 的 conditioning 偏移几乎不可感知；如确需漫剧风格增强，应在 evidence pool 上证明有效再投，目前**不投入**。

### 2.7 [已证伪] AudioFirst 只是证明"数值没被改"

- 音频锁死在 **32×32 小画幅联合采样**的输出，全画幅重采样时**音频一格不动**，**无任何唇音同步验证**；
- `audio_first.py:169` 自述 `"perceptual_quality_accepted": False, "sampler_completion_proof": False`；
- 作者原话 "只证明音频 latent 与小画幅采样结果 **数值相同**，不保证音画对得上"；
- 总步数 16（8+8），比 Quality 20 步只省 20%。

**结论**：性价比远低于 Wuli Native 8 单步；**暂不投入**。

### 2.8 [已验证] 整体升级 T8 的成本-收益不匹配

- 项目 T8 pin 在 `1.36.2@977df788fcf8`（2026-08-21）；HEAD `e576eba`（2026-10-20）相差 **135 个 commit**；
- T8 改一行 input 定义 → 项目全部 schema SHA 失效 → 503 个 sealed profile + workflow 全部需重审；
- T8 节点数 620 → 738，**零 deprecation**（声明"保留旧接口/默认值/顺序"），实际是叠加而非替换；
- HEAD 中 **191 个模块**改用 `comfy_api.latest`，要求更新 ComfyUI 运行时；
- T8 AGENTS.md 明确"不要恢复准入硬禁令"——意味着**它放弃了一切兼容性 gate**，等价于把验收负担完全转嫁给上游消费者。
- T8 GPU 实测证据**全部**挤在 RTX 4060 Ti 16GB，**最低显存余量 8.51 MiB**；**5090 32GB 上零官方 T8 证据**。`docs/README_ComfyUI.md:614` 还诚实记录了一条 **376 MiB 未过 512 MiB 发布门**的旧样片。

**结论：不做整体升级；至多取其中已验证、且能在 5090 上证明有效的孤立能力。**

---

## 3. 真正可能命中的候选（严格推理）

### 3.1 Wuli Native 8：唯一可信的填空候选

| 维度 | 项目 Quality v1 | 项目 Turbo v2 | **T8 Wuli Native 8** |
| --- | --- | --- | --- |
| 步数 | 20 | 4 | **8** |
| LoRA | 无 | 780 MB 转换 LoRA | **无**（已烘焙 FlashGen0.5） |
| 权重体积 | 34 GB | 34 GB + LoRA | **19.9 GiB INT8 ConvRot** |
| 采样配置 | `res_multistep`/`simple` | `dual_clock_euler`/`native_flow` | `simple`/`Euler`/`shift12:3`/`CFG1` |
| 拓扑变更 | — | — | **换权重 + 删 LoRA 节点** |
| 模式覆盖 | T2VA/I2VA/FL2VA/Ref2VA | 同 | **FL2VA unlocked + blocks 25-49 Ref2VA AdaLN（混合）** |
| 已记录质量 | 最好但慢 | motion/detail 弱、audio ≈ −52.5 LUFS | 8 次调用作者已自验（features.json `wuli_native_completed_calls.{8step:8}`）；2 片 864×480 人审通过 |

**关键优势**：
- **19.9 GiB ≤ 5090 32 GB**：装得下，单 LoRA 还省了 780 MB 与 audio-row 污染风险；
- **FL2VA + Ref2VA 混合**对本项目 `state_reference` + 首尾帧两套契约都能覆写；
- **无 LoRA 节点** = 无 `_LORA_MAIN_SHAPES` 路径冲突，可直接装到现有 `UNETLoader` 之后；
- **8 步 native** 比 Turbo v2 4 步的运动学更稳、比 Quality v1 20 步明显快。

**关键风险**：
- `int8_convrot` 与项目当前**同精度**，**仍可能走 `torch.cat(scaled_parts)` OOM**——不保证；
- 高分辨率证据仅至 864×480；项目标准 1344×768、5 片缝合 30s 全空缺；
- 接口不是 `Wuli8Recipe` + `Guider`，而是 `UNETLoader → MiniMaxH3DualClockSamplerT8`（作者工具 77 行 `tools/prepare_h13_wuli_hybrid.py`）；项目侧拒接 `BasicScheduler`/`KSamplerSelect`/`LoraLoader`，需核 `comfy_t8_native_turbo_profile.py:23-100` 的 `_FORBIDDEN_CLASSES` 是否仍兼容。

### 3.2 官方 API 能力补全：本项目自有的、与 T8 完全无关的缺口

| 能力 | 项目现状 | 官方实际支持 |
| --- | --- | --- |
| 分辨率 | `minimax_h3.py:200-202` 仅 `768P/4s/16:9` T2V | H3: **768P + 2K**（2K 实际宽高官方未给） |
| 参考图 | `max_reference_count=0` | `reference_image` ≤ **9** |
| 首尾帧 | 无 | `first_frame` (≤1) + `last_frame` (≤1) |
| 参考视频 | 无 | `reference_video` ≤ **3** |
| 参考音频 | 无 | `reference_audio` ≤ **3** |
| 混合 | — | 全部混用 ≤ **12** 文件（但 I2V 与 reference 互斥） |
| 提示增强 | 无 | 独立 `POST /v2/h3_context_ir`，`task_type=h3_context_ir`，**`model` 仅 `MiniMax-H3`**；返回分段式 IR 而非润色 prompt |
| Regenerate | 无 | `POST /v2/video_regeneration` 二选一：`source_task_id`（**无 content**，需白名单）**或** `content` + `base_video` |

**定价（confirmed from pricing page）**：

| 项 | 价格 |
| --- | --- |
| H3 输出 768P | **$0.08/秒** |
| H3 输出 2K | **$0.13/秒** |
| H3 输入图片 | 前 5 张免费，之后 **$0.04/张** |
| H3 输入视频 | 768P → $0.08/秒；2K → $0.13/秒 |
| Regenerate（768P→2K）输出 | **$0.05/秒** |
| H3-Context-IR | 输入 $0.90 / M tokens；输出 $3.60 / M tokens |
| H3 / H3-Max 订阅包 | **不含 H3 视频**；`"Video packages support Hailuo video models. MiniMax H3 is not supported yet"` |

**许可事实**（新增硬约束）：
- **领土排除**：开源权重 "Excluded Territories" = 美国、欧盟、英国、韩国；这些地区**不能使用开源权重**；
- 商用门槛：年营收 > **$20M** 需事先书面授权；UI 必须显著显示 "MiniMax H3"；
- 官方明确："A self-hosted H3-Base service therefore does not reproduce the complete MiniMax Platform Context-IR and 2K workflow"——本地无法达到 2K，必须走 API Regenerate（**且 Regenerate 是上下文内重生成，不是逐帧等同的超分**）。

**结论**：这是**唯一不依赖 T8、且完全由本项目控制**的能力缺口，且承诺可量化、可证、可回滚。

---

## 4. 功能评审矩阵

> 成熟度判定：**已验证** = 本机/合规证据已收；**作者声明** = changelog/doc 单方面；**结构** = 仅 CPU/单元。
> 集成成本 = 新增 template / binding / profile / capability_id / 重新 seal 五件套的程度；risk 中 **5xx** = 会在 5090 上静默失效或回退。

| 功能 | 项目现状 | 真实收益 | 成熟度 | 集成成本 | 风险 | 源码证据 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Wuli Native 8** | 无 | 填补质量-速度空隙；19.9 GiB 单 UNet；FL2VA+Ref2VA | 已验证 | **中**：weight + recipe + 新 capability | `int8_convrot` 同精度 → **可能仍 OOM**；512 max/Hi 自验；高分辨率空缺 | `tools/prepare_h13_wuli_hybrid.py:67`，25,007,719,260 bytes（19.9 GiB），作者在 4060Ti 8 调用自验 | **P0 验证**（先 A/B，不先集成） |
| **官方 API 2K / 多参考 / Context-IR / Regenerate** | H3 仅 768P/4s/16:9 T2V；0 参考图 | 2K、本地不可达的能力；9 参考图；3 段参考音频；独立 Context-IR；2× 价格标签可见 | 已验证（官方文档、官方定价表） | **低**：现有 paid provider 骨架，新增 capability + profile | 付费 + credential；2K 逐帧不对齐源；I2V 与 reference 互斥 | 官方 `v2/video_generation`、`v2/video_regeneration`、`v2/h3_context_ir`、`/docs/pricing/overview` | **P0 推进**（不依赖 T8） |
| **T8 Stage Save/MID Resume（仅借鉴工程纪律）** | 项目已有 RunBacktrack / Receipt | 内容地址化 + revision CAS + 原子写 + fsync | 已验证（T8 内部使用） | 中 | 与本项目唯一 committer / content-addressed receipt 体系**正面竞争 owner** | `freevideo_exp/runtime.py:263-301`、`nfe_resume_advanced.py:266-284` | **P1 借鉴**（设计模式而非代码依赖） |
| **H14 Token LoRA（设 `require_scope`）** | 单 LoRA `strength_model=1.0` | 隔离音频/视频行 | 作者声明（GPU 仅 attention 行 50 块 ×qkv/out） | 中 | **MLP fc1/fc2 从未在大模型 GPU 跑过**（`features.json` `fc2_large_model_GPU_asset_qualified: false`）；默认 `owner_policy='delegate_without_scope'` 静默失效 | `token_lora.py:94-99, 207-215` | **P2 暂不**（fc2 风险未关） |
| **Semantic Bridge comic-combat / wushu** | 无 | 漫剧风格增强（潜在） | **仅作者声明**："仅 conditioning 插值，默认 10% 不可感知" | 中 | 与项目 `_LORA_MAIN_SHAPES` 不同（旁路 correction，非低秩 LoRA）；多桥被拒；可能退化声音 | `semantic_bridge.py:337, 415` | **不推荐** |
| **AudioFirst（Tiny8→完整8）** | 无 | audio latent exact（仅数值层面） | 作者声明 | 中 | 总 16 步（仅省 20%）；**不证明音画对得上**；A/B 中两条路径同时要 8+8+8 | `audio_first.py:169`、`docs/H13_AUDIO_FIRST_HYBRID.md:26` | **不推荐**（性价比差） |
| **FreeVideo** | 无 | 经核实不构成加速 / 不是 7.5× 像素差距下的速度优势 | 作者声明（448×256） | **很高**（独立 Python 3.12 + 内核） | LoRA 不兼容；cudnn 无回退；三个 Apply 默认 report_only；引擎本体**不在仓库** | `freevideo_exp/worker.py:44-59, 121`；`features.json` apply 默认 `report_only` | **不推荐** |
| **Spark / Kijai / Sol-Attn** | SageAttention 2.2.0 已 seal | 作者明确不保证提速 | 结构 | 高 | **5090 SM120 全部静默失效或 fallback dense**（Spark SM89 硬门；KJ Sage SM89；Sol-Attn bare except） | `spark_runtime.py:286-297`；`res_kj_sage_identity.py:104,107,132`；`sol_attn_minimax_v2.py:639-642` | **不推荐** |
| **视觉空间引导 / 视觉标记** | 白模参考 + 十维因果契约 | **无净增量**（且退化） | 作者自述缺陷 | 中 | **色框残留进成片**（`features.json` `marked_and_split_marker_residue_observed: true`）；无 attn_mask、无 latent mask | `visual_marker.py:1-3`、`visual_marker_binding.py:129-130` | **不推荐** |
| **Temporal Chunk** | 短镜头 124 帧 + 强契约拼接 | 无净增量 | 作者声明（12s 样片） | 高 | 与既有 timeline owner 冲突；chunk 边界无 crossfade；音频根本不走二采；**人审未完成** | `chunked_two_pass_upscale_advanced.py:84-116`、`_temporal_overlap_mask :636-657`、`docs/CHUNKED_STANDARD_4PLUS4_EXP.md:142` | **不推荐** |
| **Veda / R2VA** | 已有 Ref2VA | 重叠；作者实测更慢（2.02×） | 已验证 | 高 | 用 PyTorch FlexAttention（拿不到上游 Triton INT8）；三个 Apply 默认 report_only；预测器只是 mean-pooled QK | `veda_r2va_runtime.py:65`；`docs/VEDA_SPARSE_T2VA_EXP.md:189` | **不推荐** |
| **H11 Audio-only 参考** | 无 | 极窄 | 作者声明 | 中 | 仅一条 5 秒定向验收；`audio_only_runtime_history_recovered: false`、`paired_and_standalone_two_speakers_qualified: false` | `docs/H11_NATIVE_EXTENSIONS.md:59-60` | **不推荐** |
| **DRIVE/FINAL 两遍采样** | 无 | LOW 8 + HIGH 4 路径 | 作者声明 | 高 | 一采声音不交付；底模是 pruned FL2VA；8 条 CORE 日志存在 `ERROR lora ... adaln_proj.linear.weight shape ... invalid` → "成功视频不证明 LoRA patch 生效" | `docs/DIRECTOR_TWO_PASS_20260921.md:23`；`h3_t8/director_two_pass.py:115-119, 128-164` | **不推荐** |
| **NFE Resume（冷恢复）** | 项目有 Receipt | Stage Save/Load 纪律 | 已验证 | — | **`model_contract_id` 是操作者字符串、不哈希权重；prompt 不在 resume 身份里** → 换 UNet/换 prompt 报告成功、结果不同 | `nfe_resume_advanced.py:335-343, 405-407`、`AVStageCache.save:81-83` | **不引入**（自有 Receipt 不需要） |
| **RADAR / 导演台** | Canvas 编排 + Router + Planner + Gate | 概念层 ≈ 80% 重叠；执行后端 100% 硬绑 ComfyUI 队列；**QA/评分 0** | 已验证 | **极高** | **唯一 selector / 唯一 committer / 唯一 Gateway owner 边界正面冲突**；跨进程无文件锁；CPU 子进程解码；最大并发受 ComfyUI 单卡限 | `__init__.py:215-216`、`director_routes.py:316`、`director_generation.py:705-725`、`director_project.py:548-565` | **不推荐** |
| **整体升级到 T8 1.101.0** | pin 在 1.36.2 | 不确定 | — | **很高** | 135 commit；191 模块改 `comfy_api.latest`；零 deprecation；`features.json` 与测试断言已不一致（738 vs 371）；5090 上零官方 T8 证据；旧记录 376 MiB 未过门 | `git rev-list --count 977df78..HEAD` = 135；`features.json`；`tests/test_preflight_and_registration.py:19` | **不推荐** |

---

## 5. 最值得验证的技术方向与最小 A/B 实验

### 方向 1（P0）：Wuli Native 8 能否填补质量-速度空隙

**假设**：在 1344×768 / 124 帧 / 同 seed / 同 prompt / 同首尾帧下，Wuli Native 8 的 motion/detail 与音频可用性显著优于 Turbo v2，且明显快于 Quality v1。

**最小可行实验**（单变量、严格同输入）：
1. 在**隔离的 ComfyUI 环境**装 T8 HEAD + Wuli Native 8 权重（19.9 GiB），**不动**本机 `custom_nodes/minimax-h3-audio-T8@977df788fcf8`。
2. 取项目已接受的一条 Shot 的 exact request（从 `runs/drama-h3-t8-30s-preview-20260830-final-v2` 复用 prompt / seed / first_frame / last_frame / reference 三张图）。
3. 生成三片，同 seed、同帧数、同分辨率：**Quality v1（20 步基线）/ Turbo v2（4 步现状）/ Wuli Native 8（8 步候选）**。
4. 测量：**wall time、peak GPU、peak RSS、音频 LUFS**（直击 −52.5 LUFS 缺陷）、是否出现 `torch.cat(scaled_parts)` OOM。
5. 跑本项目 Per-Shot post-media Gate（`video-analysis` MCP + 逐项 requirement PASS），**人审** motion/detail。
6. 用 `sol_attn_stats()` / `spark_runtime.audit()` 逐次核 `report_json.scope_effective` ≠ `effective_fallback_dense`，**严格拒绝任何"节点没变红但实际 dense"** 的走样。

**判定门槛**：
- audio LUFS 回到可闻区间（>= −30 LUFS approx.）；
- motion/detail 不劣于 Turbo v2 且接近 Quality v1；
- 无 OOM（`torch.cat(scaled_parts`）触发；
- wall time 显著低于 Quality v1（10–15 min/片 → ≤ 6 min/片）。

**回滚**：隔离环境，删除即完整回滚；本机 sealed lane 完全不动。

### 方向 2（P0）：官方 API Regenerate-2K 与多参考补全

这是**唯一不依赖 T8、且完全由本项目控制**的能力缺口。
1. **先做契约审计**：核 `minimax_h3.py` 当前对 `max_reference_count=0` 的 cap；与官方 `reference_image` ≤9、`reference_video` ≤3、`reference_audio` ≤3、`first_frame`/`last_frame` ≤1 比对，列缺口。
2. **新建 capability**：`minimax_h3_v2_api`（不替换，向后兼容），profile 显式 `model=MiniMax-H3`、`role` 支持 `first_frame/last_frame/reference_image/reference_video/reference_audio`、`extra.prompt_expansion_mode=disabled|balanced|quality`、`ratio` 必须显式（不能 `adaptive`）。
3. **Regenerate 双路并存**：
   - 路径 A：`source_task_id`（无 content，需白名单），用于向官方"承接"任务；
   - 路径 B：`content` + 1 `video_url` `role=base_video`，用于复现原 content。
4. **小规模 A/B**：用现有 6 镜 30s 成片中 1 镜升 2K，验证 "上下文的重生成" 不破坏已有 `state_reference` 契约（如破坏则升 2K 不可作为连续性手段）。
5. **H3-Context-IR 作为 authoring 辅助** 离线小试验：不生成视频、只验 prompt 增量与现有 3-field prompt 模板的兼容性。

**前置**：credential 注入 + 付费授权 + Budget Guard + one-use permit（按项目 paid provider 规则走）。

**硬约束**：
- **I2V 与 reference media 不能混用**；
- **T2V 必须具体 ratio**（不能 `adaptive`）；
- **$0.13/秒** 2K 成本纳入 Budget Guard：每提交前算剩余预算与 ceiling；
- **I2V/FL2VA 与 reference_role 互斥** 进 profile 校验。

**回滚**：capability 删除 + profile 删除；现有 768P 路径不受影响。

### 方向 3（P1，借鉴模式）：T8 Stage Save + MID Resume 工程纪律

不是引入 T8 代码，是**读懂**三个 T8 文件：**作为**对本项目 `Receipt` / `RunBacktrack` / `AuthoringSnapshot` 体系的对照参考：
- `freevideo_exp/runtime.py:263-301`（stage save/load 签身份）
- `split_runtime.py:89-124`（mid 续跑）
- `nfe_resume_advanced.py:266-284`（resume state 序列化）
- `director_project.py:67-78`（原子写 + fsync + revision CAS）

同时把 T8 的 silent state drift 教训**反向写进本项目 Receipt**（**不能** 只哈希 SHA-256 of generated artifact，必须哈希:
- 实际加载的 UNet/LoRA 权重的 SHA-256；
- actual prompt 的 content hash；
- actual seed、shift_video、shift_audio、CFG、sampler、scheduler、steps；
- actual VAE、text encoder 身份）

**目标**：把"换底层机制但报告成功"的不可能性升到 Receipt 标准。

### 方向 4（P1，零成本核查）：先验证 Turbo v2 音频是否真的不可闻

在方向 1/2 之前先做一次**零 GPU 成本**核查：取 `runs/` 下已存在的 Turbo v2 MP4，重新测量 LUFS。
- 若实测确认不可闻 → 方向 1 必须包含音频门槛，方向 2 不增加复杂度，方向 5 也暂不投；
- 若实测确认只是偏低（≈ −40 LUFS 仍可闻）→ 方向 1 可在音频维度做更宽容的判定。

### 方向 5（P2，暂不启动）：Semantic Bridge comic-combat

仅在确有漫剧风格需求时以同 seed 单桥/无桥 A/B 试。**当前证据（默认 10% conditioning 偏移，多桥需 explicit Compose ordered_serial，可能退化声音）不支持投入。**

---

## 6. 分阶段实施方案

### 阶段 0：零成本核查（可立即并行，无需任何授权）

| 任务 | 依赖 | 产出 |
| --- | --- | --- |
| 用 `ffprobe`/sox 重测 `runs/` 下 Turbo v2 MP4 音频 LUFS | 无 | 音频是否真不可闻的硬证据 |
| 核 `minimax_h3.py` 与官方 `reference_image` ≤9 等 4 项契约差异 | 无 | 云端能力缺口清单 |
| 核 Wuli Native 8 权重获取路径与许可（**开源权重的 US/EU/UK/KR 领土限制**） | 无 | 部署边界前置 |
| 记录本机 ComfyUI/T8/GPU 精确身份（已知：0.33.2@7cee3ceb1、T8@977df78、RTX 5090 32607 MiB cc12.0） | — | 环境快照 |

**Gate**：若阶段 0 证明 Turbo v2 音频不可闻 → 方向 1 Wuli 验证包含音频门槛；若可闻 → 方向 1 单独推进。

### 阶段 1（条件）：隔离环境 A/B Wuli Native 8

| 任务 | 依赖 |
| --- | --- |
| 搭建隔离 ComfyUI（独立目录/venv/custom_nodes） | 与下列可并行 |
| 装 T8 HEAD + Wuli Native 8 权重 | 与环境搭建可并行 |
| 执行方向 1 的 A/B | 必须等就绪 |
| Per-Shot post-media Gate + 人审 | 必须等生成完成 |
| 逐次核 `report_json.scope_effective` | 严格拒绝走样 |

**绝对约束**：本机 `custom_nodes/minimax-h3-audio-T8@977df788fcf8` 与项目 sealed profile 在本阶段**保持原样**。改动 sealed lane 必须在阶段 2 之后、单独授权。

### 阶段 2（与阶段 1 完全并行）：官方 API 能力补全

不依赖 T8、不依赖 GPU、不触碰本地 sealed lane。新 capability + profile + focused tests，走既有 paid provider 骨架（credential 注入、Budget Guard、one-use permit、Task ID 持久化、ratio 校验、I2V/reference 互斥校验）。

### 阶段 3（条件启动，依赖阶段 1 结论）：Wuli Native 8 集成决策

**必须等待阶段 1 A/B 通过**。若通过：
1. 新增 `workflows/templates|profiles|bindings/minimax_h3_t8_wuli8_*.{json,yaml}` 三件套
2. 在 `workflow_loader.ARRAY_WIDGET_NAME_MAP` 补映射（视 T8 节点接口变化而定）
3. 新 capability_id，挂到 `LocalH3VideoProviderFamily`
4. 跑 `production_video_provider_tests` + Architecture Gate + 完整 policy checks
5. 提交到一个 feature branch；**一次性、可回滚**（删除三件套 + family 条目即可）

### 阶段 4（条件启动，借鉴）：Receipt 体系加固

把 T8 silent drift 教训**反向写进 Receipt**（详见方向 3）。本项目 Receipt 原本就比 T8 `nfe_resume_advanced.py` 更严（已有 Receipt + RunBacktrack），这一阶段是**确认覆盖完整**而非修补漏洞。

### 明确不启动

整体 T8 升级、FreeVideo、视觉标记、Temporal Chunk、RADAR/导演台、Spark/HyperFlow/Kijai、Veda/R2VA、H14 LoRA（因 fc2 未在大模型 GPU 验证）、Semantic Bridge、H11 Audio-only 参考、DRIVE/FINAL 两遍采样、NFE Resume（冷恢复）。理由见 §4 矩阵与 §2 证伪。

### 并行与顺序图

```
[阶段 0 零成本核查]   ──并行──→   Gate: 音频门槛 + 部署边界前置
        ↓
   ┌────┴────┐
   ↓         ↓
[阶段 1     ][阶段 2 官方 API 补全]   ← 完全并行；阶段 2 与 T8 无关
 Wuli A/B ]  paid provider 骨架
   ↓
 Gate: 通过?
   ↓ 是
[阶段 3 Wuli 集成]
[阶段 4 Receipt 加固]   ← 完全并行于阶段 3；前置是阶段 0/1 总结
```

---

## 7. 环境、许可与许可传染

```
ComfyUI   /home/reggie/ComfyUI           0.33.2 @ 7cee3ceb1 (2026-08-17)
T8        custom_nodes/minimax-h3-audio-T8 @ 977df78 (2026-08-21), 版本 1.36.2, GPL-3.0-or-later
GPU       NVIDIA GeForce RTX 5090, 32607 MiB, driver 580.178.04, compute capability 12.0 (sm_120)
T8 HEAD   e576eba (2026-10-20), 版本 1.101.0, 相距 135 commit
T8 依赖   pyproject dependencies = []（明确不污染主 ComfyUI Torch/CUDA 栈）
```

**许可结论**：
- **代码**：T8 = GPL-3.0-or-later；FreeVideo/VDN = Apache-2.0；
- **权重**：MiniMax H3 Community License
  - **领土硬限制**：开源权重禁止 US / EU / UK / KR（"Excluded Territories"）；
  - **商用门槛**：年营收 > $20M 需事先书面授权；
  - **品牌**：UI 必须显著显示 "MiniMax H3"；
  - **禁止**：用于军事目的；用 H3/其输出改进其他模型（H3 衍生除外）。
- **传染边界**：本项目通过 loopback HTTP 调用 ComfyUI，**不打包、不链接 T8 代码**；workflow JSON 属配置而非 GPL 源代码，边界清晰。若未来分发包含 T8 代码，触发 GPL-3.0 传染，需另行评估。

---

## 8. 未验证与剩余风险

- 本报告全部结论基于**源码阅读、官方文档与项目既有实跑记录**。**未执行任何新的 GPU 生成**（本轮无 paid submit、无 ComfyUI 提交、无隔离环境搭起）。
- 方向 1（Wuli Native 8）的效果、耗时、显存与音频指标**全部为待验证假设**，实测前不是收益承诺。
- 2K 的具体宽高、生成超时、URL 过期时长**官方页未给**，本报告不假定。
- T8 1.85.0–1.101.0 中未逐条覆盖的次要条目（Meridian、TAEH3、HyperVAE、Topaz/DLSS、Avatar、Topaz、H16、LonPaint 等）未纳入评审；后续若需要单独调研。
- 5090 SM120 上的 Spark / KJ Sage / Sol-Attn 静默失效结论**只在源码层验证**——若有人未来真的拉到上游对应 kernel，仍需要单独一次 A/B 验证。但这与本次评审无关。
- 本研究产出**未提交至任何分支、未触发任何 Provider 调用、未修改 Production 状态**。写入本文件后由用户单独决定是否推广到 spec / plan / feature branch。

---

## 9. 引用索引（关键源码与文档）

### 项目侧
- `docs/v0.2-runtime-baseline.md:1173`（Turbo v2 实测代价，独立 review 标注音频 −52.5 LUFS）
- `docs/v0.2-runtime-baseline.md:1012-1053`（17s OOM 根因 `torch.cat(scaled_parts)`）
- `src/ai_video/workflow_loader.py:13-106`（穷举 widget 映射白名单）
- `src/ai_video/production/minimax_h3.py:200-202`（官方 H3 768P/4s/16:9 T2V only）
- `src/ai_video/production/minimax_h3_max.py:37-40`（H3-Max 480P/768P）
- `src/ai_video/production/metaso_h3.py:148`（9 参考图）
- `src/ai_video/production/comfy_t8_native_turbo_profile.py:23-100, 267`（T8 Turbo 限制类 / 4 步采样配置）
- `docs/agent-primary-contract-matrix.md:463-466, 723-725`（唯一 selector / committer；provider 描述）

### T8 侧（HEAD `e576eba`）
- `__init__.py:187-216`（V3 `comfy_entrypoint()`；0 NODE_CLASS_MAPPINGS）
- `features.json`（738 唯一节点；200+ feature 块）
- `tests/test_preflight_and_registration.py:19`（断言 371，与 features.json 738 不一致）
- `h3_t8/spark_runtime.py:286-297`（SM89 硬门；5090 静默 dense）
- `h3_t8/sol_attn_minimax_v2.py:402-421, 639-642`（bare except fallback dense）
- `h3_t8/res_kj_sage_identity.py:104,107,132`（KJ Sage SM89 硬门）
- `h3_t8/visual_marker.py:1-3` / `visual_marker_binding.py:129-130`（视觉标记不是空间采样；色框残留）
- `h3_t8/semantic_bridge.py:337, 415, 355-356, 465-471`（conditioning 插值默认 10%；多桥拒绝）
- `h3_t8/audio_first.py:169`（数字层证明，不证明音画对得上）
- `h3_t8/freevideo_exp/worker.py:44-59, 121` / `runtime.py:263-301` / `docs/FREEVIDEO_EXP.md`（独立 Python 3.12；448×256→512×288；cudnn 硬后端）
- `h3_t8/freevideo_exp/nodes.py:148` / `nodes_veda_r2va.py:44` / `nodes_veda_sparse_exp.py:69` / `nodes_veda_heuristic_exp.py:29`（三个 Apply 默认 report_only）
- `h3_t8/veda_r2va_runtime.py:65` / `docs/VEDA_SPARSE_T2VA_EXP.md:189`（PyTorch FlexAttention；dense 比 sparse 快 2.02×）
- `h3_t8/nfe_resume_advanced.py:335-343, 405-407`（resume 身份不含权重、不含 prompt）
- `h3_t8/chunked_two_pass_upscale_advanced.py:84-116` / `_temporal_overlap_mask:636-657`（无 crossfade；音频不走二采）
- `h3_t8/director_routes.py:316, 320-329, 548-565` / `director_generation.py:705-725`（导演台完全绑 ComfyUI；无文件锁；QA 为空）
- `tools/prepare_h13_wuli_hybrid.py:67`（19.9 GiB 权重；8 步自验）
- `AGENTS.md` / `docs/PATCH_STACK_POLICY.md:30-37`（禁止"未验证就拒绝执行"；放弃兼容性 gate）

### 官方 API 侧
- https://platform.minimax.io/docs/api-reference/video-generation-v2-create（H3 768P+2K；role 全 5 类 + base_video；混合 ≤12；I2V 与 reference 互斥）
- https://platform.minimax.io/docs/api-reference/video-generation-v2-h3-context-ir（独立入口；H3 only；分段式 IR 输出）
- https://platform.minimax.io/docs/api-reference/video-regeneration-v2（双路：`source_task_id` 或 `content`+`base_video`）
- https://platform.minimax.io/docs/pricing/overview（H3 768P $0.08/秒；2K $0.13/秒；图片前 5 免费后 $0.04/张；Regenerate 输出 $0.05/秒；H3-Context-IR 输入 $0.90/M、输出 $3.60/M；H3 不在订阅包）
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE（领土排除 US/EU/UK/KR；$20M 营收门槛）
- https://platform.minimax.io/docs/guides/local-deploy-h3（本地 1344×768 硬顶；Comfy-Org 量化件非 BF16/FP32 基线）
- https://platform.minimax.io/docs/guides/rate-limits（H3 RPM 300 / inflight 30；H3-Max 未列）
