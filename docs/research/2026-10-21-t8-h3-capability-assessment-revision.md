# T8 / MiniMax H3 能力评估 · 修订复核（2026-10-21）

**属性**：对同日初版 [2026-10-21-t8-h3-capability-assessment.md](2026-10-21-t8-h3-capability-assessment.md) 的 5 项针对性证据复核
**授权边界**：不动 sealed runtime、不下载大模型、不调用付费 API、不跑 GPU 生成
**结论性质**：本报告全为 desk research；任何 GPU 实证必须等另行授权

---

## 0. 证据分级标准（修订版强制）

| 等级 | 含义 | 标识 |
|---|---|---|
| **L1 源码/官方原文证实** | 在指定文件指定行可读到语义；官方文档原文 | `[L1]` |
| **L2 作者 GPU 实测** | T8 或官方作者在他们硬件上产生的数据 | `[L2]` |
| **L3 本机 RTX 5090 实测** | 在本项目本机 ComfyUI/RTX 5090 上产生的数据 | `[L3]` |
| **L4 未验证推测** | 基于源码推测、基于他人硬件外推、或基于模型相似性的推理 | `[L4]` |

**严格规则**：
- L1 ≠ L2 ≠ L3 ≠ L4。**禁止跨级直推**。
- L4 不得作为"风险已排除"的依据（最多作为"被源码证伪前的暂定"）。
- 同一句子同时承载多级时必须拆分；高优等级支配结论。
- 本报告全部断言带等级标签；混用等级的句子**全文不接受**。

---

## 1. 五项针对性修正

### 1.1 [L1 修正] Wuli Native 8 权重：23.29 GiB（不是 19.9 GiB / 25 GB）

**字节验证**：`25,007,719,260 bytes ÷ 1024³ = 23.290 GiB`；`÷ 1000³ = 25.008 GB`。
- `tools/prepare_h13_wuli_hybrid.py:67` 原文：字节数与 SHA `a852255134e20112d63a23848be122bd0076e37b9ddac09e436d9d61abbba42b` 完全一致 [L1]。
- 初版报告行 §3.1 与 §4 矩阵曾以 19.9 GiB / 25 GB 表述 —— **均为不准确**；以本修正为准。

**RTX 5090 模型驻留精算 [L1]**：

| 量 | 值 |
|---|---|
| 5090 显存总量 | 32,607 MiB = **31.843 GiB**（`nvidia-smi` 报告） |
| Wuli weight 占 | **23.290 GiB** |
| 模型驻留后剩余 | **8.553 GiB** |
| 历史项目峰值（Turbo v2，5s @ 1344×768）[L3 `v0.2-runtime-baseline.md:1173`] | peak GPU 19,932 / 26,236 / 24,828 / 26,797 MiB（4 次均值 **24,448 MiB ≈ 23.88 GiB**） |
| 项目当前路径 OOM 触发点 [L3 `v0.2-runtime-baseline.md:1012-1053`] | `comfy_kitchen.int8_linear → torch.cat(scaled_parts)` 临时分配峰 19,157 MiB；reserved 21,952 MiB |
| 17s 历史 OOM 实验 [L3] | 6 次物理提交全部失败、0 MP4 |

**结论（修订）**：
- Wuli weight `int8_convrot` 与项目当前路径**同精度** [L1]；
- Wuli weight **23.29 GiB 装得下** 5090 [L1]；
- 但 8.55 GiB 剩余 < 历史峰值 23.88 GiB 的**一半** —— 即 Activation budget 极紧 [L1]；
- **Wuli 跑 5s 片是否触发 `torch.cat(scaled_parts)` OOM 是 [L4] 未验证**；
- 概率判断 [L4]：若 Turbo v2 历史峰值 23.88 GiB 是同 base 模型 + LoRA 增量的叠加，Wuli + 同 base（无 LoRA）的激活路径**很可能低于** 23.88 GiB；但绝对数字依 activation buffer 形状、`int8_convrot` 内部 scaling path、`max_attention_tokens` 与 audio VAE 等决定 **未在本机实测**。
- **因此原"填空质量-速度空隙的 P0 候选"必须降为 P0 高风险候选**：前置 3 步探针 → 才进入质量 A/B。

**修订后的 P0 A/B 必需探针顺序**：

```
P0-a 装好 weight 不跑推理，nvidia-smi 验 ≈ 8.55 GiB 剩余（[L1] OK / 失败 → 失败就此止住）
P0-b 5s 单片空提示 forward（无 prompt、无 LoRA），验 torch.cat(scaled_parts) 是否仍 OOM（[L4]）
P0-c 124 帧 1344×768 完整 prompt forward（[L4] → [L3] 升一档）
P0-d quality/audio 4 维对比（依赖 P0-c 通过）
```

**禁止**：在 P0-a ~ P0-c 任何一步失败时进入 P0-d。

### 1.2 [L1 修正] MiniMax-H3 与 H3-Max API 参数差异（精确版）

| 字段 | MiniMax-H3 | MiniMax-H3-Max | 等级 |
|---|---|---|---|
| 输出 480P | 不支持 | **$0.05/秒** | [L1] `docs/pricing/overview` |
| 输出 768P | **$0.08/秒** | **$0.08/秒** | [L1] |
| 输出 2K | **$0.13/秒** | 不支持 | [L1] |
| 输入图片计费 | 前 5 张免费，其后 $0.04/张 | 前 2 张免费，其后 $0.074/张 | [L1] |
| 输入音频 | 免费 | 免费 | [L1] |
| 输入视频（按目标分档） | 768P $0.08/秒 · 2K $0.13/秒 | 480P $0.0553/秒 · 768P $0.143/秒 | [L1] |
| **Regenerate 输出** | 仅 768P 源可升 2K，输出 **$0.05/秒** | 480P / 768P 不可升 2K | [L1] |
| `extra.prompt_expansion_mode` 字段 | **不支持**（视频生成 body 不含此参数） | disabled / balanced / quality | [L1] |
| 独立 prompt 增强端点 | **H3-Context-IR**（`POST /v2/h3_context_ir`，仅 `model=MiniMax-H3`）—— 分段式 IR 输出（retention tags、`<d>[lang]…</d>` 对白、shot 切分） | 不支持 | [L1] |
| `ratio`（T2V） | **必须显式**，不能 adaptive | 同 | [L1] |
| `reference_image` 上限 | 9（与视频混合 ≤12） | 9（同） | [L1] |
| `reference_video` 上限 | 3 | 3 | [L1] |
| `reference_audio` 上限 | 3 | 3 | [L1] |
| `first_frame` / `last_frame` | ≤1，**与 `reference_*` 互斥** | ≤1，同 | [L1] |
| I2V 与 `reference_*` | **互斥** | **互斥** | [L1] |
| Regenerate 资格 | **两条路二选一**（同时传或都不传报错） | 仅适用 768P 源 | [L1] |
| ↳ 路径 A：`source_task_id` | 需白名单 + 源任务属当前账号 + succeeded + **≤7 天查询窗口**；无需 content | 需白名单 + ≤7 天 | [L1] + [L2] |
| ↳ 路径 B：`content` + 1 个 `video_url role=base_video` | content 复现原 video 的 prompt/role，其余参可微调；目标 ≤7 天内 | 不支持 2K | [L1] |
| RPM / inflight | 300 / 30 | **官方未列**（限流表无 H3-Max 行） | [L1] |
| Subscription 包 | **不含 H3 视频**（仅 Hailuo 等） | 同 | [L1] |
| 2K 像素确切尺寸 | **官方未公布**（`api-reference` 只有 enum，无 W×H） | 不支持 | [L1] |
| 输出 URL 过期时长 | 官方原文 "output URLs are temporary"，**未给数字** | 同 | [L1] |

**修正点**：
- 原评估 §3.2 把 `extra.prompt_expansion_mode` 描述为 H3 支持 —— **错误**。H3 视频 body 不含此字段；H3 的 prompt 增强是**独立 `POST /v2/h3_context_ir`** 端点（仅 H3）。
- 原评估 §3.2 把 Regenerate 描述为 "需复现原 content + 1 个 `base_video`" —— **不完整**：实际**两条路并存（`source_task_id` ↔ `content + base_video`）**，且 `source_task_id` 需白名单 + 7 天。
- 原评估未区分"路径 A `source_task_id` 不需要 content"。**这是一个外部 Provider 调用决策的关键事实** —— 如果 Project 选路径 A，profile 必须能识别路径 A 与路径 B，且不能同时填两者。

**新增事实**：
- **H3-Max 不支持 2K** [L1]，不是价格上的边际，是字段上不存在；
- **2K H3 由 Regenerate 双路走**，H3-Context-IR 改 prompt，Regenerate 升 2K，**两步分离**；
- **`ratio` 必填**且 T2V 不可 adaptive [L1]，必须进 profile validation（不会"自动填"）；
- **I2V 与 reference 互斥** [L1]，必须在 profile 层校验；
- **H3-Max RPM/并发无官方数字** [L1] —— 这一项在付费前**应当计入风险**（即使买了也不知道 ceiling 是多少）。

### 1.3 [L1/L4 修订] 严格证据分级

**初版混用等级的句子**：

| 初版句 | 错位等级 | 拆分为 |
|---|---|---|
| "Wuli 已被作者在 4060Ti 8 次自验" | 把 [L2] 当成本项目 [L3] | [L2] 仅作者硬件；非本机 |
| "Spark 在 5090 上完全失效" | 把 [L1] 硬门 + [L4] 实际 dispatch 后果合并 | 拆为 [L1] 硬门 + [L4] fallback dense 实际后果 |
| "Sol-Attn 错误被 bare except 吞" | [L1] 是 bare except；"会吞"是 [L4] | [L1] 存在 / [L4] 运行时确实 swallow |
| "Semantic Bridge 默认 10% 不可感知" | [L1] alpha=0.10 lerp 是事实；"不可感知" 是 [L4] | 拆为 [L1] alpha=0.10 + [L4] 主观感知 |
| "视觉标记色框残留进成片" | 部分 [L1] + 部分 [L2]（作者未提供 sample） | [L1] `features.json` 字段 + [L2] 作者自承 |

**强制拆分规则**：本报告每条带证据等级的断言都遵循 `≤1 个 [L1]/[L2]/[L3]` + 可附 `[L4]` 推测；不允许把 L2 当成 L3，不允许把 L1 + L4 写成"L1"。

### 1.4 [L1/L4 修订] Spark / KJ Sage / Sol-Attn 按等级分类

| 路线 | [L1] 源码证实 | [L4] 未验证推测 |
|---|---|---|
| **Spark Attention** | `spark_runtime.py:286-287` 硬门 `(8,9)`；`block_patch:293-297` 委托 dense | 5090 SM120 的`!= (8,9)`分支实际 dispatch 后果：可能 (a) 走 dense 完整无错；(b) dense path 在 sm120 有 arch-specific bug hard fail；(c) 仍部分安装 kernel 但关闭 optimization。无 A/B 不能定 |
| **KJ Sage / RES** | `res_kj_sage_identity.py:104,107,132` 硬门 SM89 → RES cache 资格失效 | 5090 SAGE 本体 forward 行为、cache re-built 路径、最终磁盘占用 —— 全部 [L4] |
| **Sol-Attn** | `sol_attn_minimax_v2.py:402-421` `_ineligible` 不读 `get_device_capability`；`:639-642` bare except | 该 bare except 是否在 5090 上确实 swallow 而**不**向 ComfyUI 日志冒泡 —— [L4] |

**严重告警**（仍是 [L1]，与是否 5090 无关）：
- T8 `AGENTS.md` 与 `PATCH_STACK_POLICY.md` 明确禁止"未验证就拒绝执行" —— **节点永远不红**，所有 fallback 都以 warning 出现 [L1]；
- T8 `pyproject.toml` 故意 `dependencies = []`，"不污染主 ComfyUI Torch/CUDA 栈" [L1]；
- 因此 **验收唯一可靠手段是逐次读 `report_json`** 的 `scope_effective` / `actual_*_calls` / `delegate_reasons` —— 这是 [L1]，不依赖硬件。

**最低限度 A/B（即使不正式引入 T8）**：
- 临时最小 ComfyUI 环境（独立目录 + venv），临时装 T8 HEAD + 单个 Spark / KJ Sage / Sol-Attn 节点；
- 各跑一次 **空 latent forward**（最小耗时），观测 stdout / ComfyUI log；
- 严格判据：节点红/不红 + `report_json.actual_sparse_calls` 是否真 > 0；
- 即便结果在该 env 下"能跑"，仅证明 [L1+disp] 在 SM120 下不报 hard fail，不证明速度提升（属 [L4]）。

### 1.5 [L1/L4 修正] 音频 4 维评估

**初版错误**：用单一 LUFS 阈值（>= −30 LUFS）做"音频可用"判定。**这是把 4 个独立维度压成 1 维**：

| 维度 | 客观指标 | 工具 | 等级门槛 / 验收标准 |
|---|---|---|---|
| **Loudness**（响度） | Integrated LUFS · True-peak (dBTP) | `ffmpeg -af loudnorm`, `pyloudnorm` | AAC 32kHz 双声道通常目标 −16 到 −20 LUFS；<= −40 LUFS 几乎不可闻为失格 |
| **Audio Quality**（音质） | P.563 / ViSQOL / NISQA / DNSMOS / UTMOS；THD+N、SNR | `mcp__video-analysis__audio_understand`（preview offline） | MOS >= 3.0 / 5（具体阈值待 baseline 取） |
| **Lip-sync**（唇音同步） | phoneme ↔ 唇部 landmark 时间差 | `mcp__video-analysis__audio_understand` 唇部对齐 | 时间窗 <= 80 ms（ITU-T P.1109）；不通过 = 不可用 |
| **Audio-Action 同步**（音效-动作） | 脚步/碰撞/拟音 ↔ 动作 onset 时差 | onset detection + 主观验收 | 项目级：人工逐镜确认，或专用 VAD + 事件检测对比 |

**强制规则**：
- 任何"音频通过/不通过"判定必须 4 维全列；
- **单维度不通过不算不通过**（但必须单独列出修复方向）；
- **任何一维 NOT_EVALUATED = NOT_EVALUATED**（不能算 PASS）；
- 本项目《Per-Shot Post-Media Gate》本来就不接受 hook/score 替代 —— 这条规则与本评估一致。

**对本评估的影响**：
- Wuli 4 维 A/B 必须基于既有 MP4 baseline：先在 `runs/drama-h3-t8-30s-preview-20260830-final-v2/*.mp4` 跑 4 维 → 取 baseline 阈值；
- 不能拿单一 LUFS −30 跨项目一刀切（每个项目的 codec / mix 习惯不同）。

---

## 2. 修订后的 P0 / P1 / P2

### P0（必须做、且本轮授权内可启动）

1. **A1 / A2：0 GPU 音频 4 维 baseline**（针对既有 MP4）
2. **A3：核 `minimax_h3.py` 与官方 v2 API 参数差异**（写一份 capability-level delta sheet）
3. **A4：核 Wuli Native 8 权重获取路径与许可**（US/EU/UK/KR 领土限制 / 商用门槛）
4. **Wuli Native 8 探针三步**：P0-a（装）、P0-b（5s 空提示）、P0-c（124 帧完整）—— 任何一步失败即降级
5. **minimax_h3_v2_api capability profile**（按 H3 / H3-Max 各一子 capability，先 768P 试，Budget Guard 控 2K）

### P1（条件启动）

1. **Receipt 加固 [L1 反向借鉴 T8]**：在现有 Receipt 上加 权重字节 SHA、actual prompt content hash、actual seed、actual scheduler、actual CFG、actual shift_video/shift_audio —— 用 T8 的 silent drift 教训加固本项目 Receipt，不引入 T8 代码
2. **Spark / KJ Sage / Sol-Attn 最小 dispatch A/B**（仅隔离 ComfyUI env）

### P2（暂不启动 / 不推荐）

- 整体 T8 升级
- FreeVideo
- 视觉标记
- Semantic Bridge（默认 10% conditioning 插值证据不足 [L1+L4]）
- AudioFirst 16 步（仅证明 latent exact，不证明感官对齐 [L1]）
- H14 Token LoRA（`fc2_large_model_GPU_asset_qualified: false` [L1]）
- Temporal Chunk（与项目十维因果契约 + 短镜拼接架构重复 [L1]）
- Veda Sparse T2VA（作者实测 2.02× **更慢** [L2]）
- H11 Audio-only（仅一条 5 秒定向验收 [L1]）
- DRIVE/FINAL 两遍采样（ORE 日志有 LoRA 形状错误，成功样片不证明 patch 生效 [L1+L2]）
- RADAR / 导演台（与唯一 selector / 唯一 committer 冲突 [L1]）
- NFE Resume（不哈希权重、不哈希 prompt [L1]，与现有 Receipt+RunBacktrack 体系为异代）

### P0 验证门槛（不达即降级）

| 验证项 | 门槛 |
|---|---|
| Wuli OOM 探针 P0-c | 124 帧完整 forward 不 OOM [L3] |
| Wuli Audio 4 维 | 4 维全 [L3]（与 baseline 比较）|
| Wuli motion/detail | 不劣于 Turbo v2 且接近 Quality v1 [L3] |
| minimax_h3_v2 API | 768P 试跑成功，profile 校验齐 [L3] |
| 2K 上线 | Budget Guard 通过 + one-use permit + Task ID 持久化 [L3] |

---

## 3. 已证实风险（仅 [L1] / [L2] / [L3]）

| # | 风险 | 等级 |
|---|---|---|
| R1 | Spark 硬门 SM89；5090 SM120 不可能装载 Spark kernel | [L1] |
| R2 | T8 `nfe_resume_advanced.py:335-343` 不哈希权重、不哈希 prompt；T8 内部署 NFE 引 silent drift | [L1] |
| R3 | `features.json` 738 节点 vs `tests/test_preflight_and_registration.py:19` 断言 371 —— T8 测试基线已破 | [L1] |
| R4 | FreeVideo 引擎本体不在仓库；要求独立 Python 3.12 + VDN + Triton + Diffusers pinned | [L1] |
| R5 | T8 全部 GPU 证据仅在 RTX 4060 Ti 16GB（最低 VRAM 余量 8.51 MiB）；5090 32GB 零 T8 官方证据 | [L1] |
| R6 | Veda Sparse T2VA 在作者 4060Ti 上 dense vs sparse = 628 vs 1266 秒（**2.02× 更慢**） | [L2] |
| R7 | T8 changelog 全部带 EXP 限定；任何"作者声明"前提都是限定结果 | [L1] |
| R8 | T8 旧记录 `docs/README_ComfyUI.md:614` 376 MiB 未过 512 MiB 发布门 | [L1] |
| R9 | MiniMax H3 weight license "Excluded Territories" 含 US / EU / UK / KR —— 本项目若部署开源权重路径在硬领土限制中 | [L1] |
| R10 | MiniMax H3 weight license 年营收 > $20M 需事先书面授权 | [L1] |
| R11 | T8 Visual Marker `features.json` 自认 `marked_and_split_marker_residue_observed: true` —— 色框残留进成片 | [L1] |
| R12 | T8 Semantic Bridge 默认 `alpha=0.10` conditioning 插值；多桥必须 explicit Compose 且 ordered serial | [L1] |
| R13 | T8 Sol-Attn `sol_attn_minimax_v2.py:639-642` bare except —— 错误吞咽，外层观测需 `report_json` | [L1] |
| R14 | T8 director 与本项目唯一 selector / 唯一 committer 正面冲突；强行引入需改 owner 边界 | [L1] |
| R15 | H3-Max 2K 不支持（enumeration 缺）；走 2K 必须 H3 + Regenerate | [L1] |
| R16 | H3 Regenerate `source_task_id` 路径需白名单 + ≤7 天 —— 申请 profile 时必须确认白名单状态 | [L1] |
| R17 | H3-Max RPM / inflight 未列；按量付费采购前 ceiling 不确定 | [L1] |
| R18 | I2V / FL2VA 与 reference media 不能混用；T2V 必须 ratio；规则必须进 profile validation | [L1] |
| R19 | T8 节点无 deprecation 政策：620 → 738 单调增长，任何升级都是叠加而非替换 | [L1] |
| R20 | Wuli weight 23.29 GiB；激活预算极紧 [L1] —— 是否 OOM 是 [L4]，必须 P0-a~c 探针 |

---

## 4. 尚需本机 A/B 的假设（[L4]）

| # | 假设 | 必要 A/B 类型 |
|---|---|---|
| H1 | Wuli Native 8 在 5090 上仅装 weight 即不触发 OOM | nvidia-smi 探针；3 分钟（[L3]） |
| H2 | Wuli 5s 单片空提示不 OOM | 隔离 ComfyUI + 5s 片 1 次（[L3]） |
| H3 | Wuli 124 帧 1344×768 完整 forward 不 OOM | 同上，但 1 条 Shot 请求（[L3]） |
| H4 | Wuli Audio 4 维全 [L3] 通过 | 4 维 baseline → 同 seed / prompt / first+last / ref 三图 A/B |
| H5 | Wuli motion/detail 不劣于 Turbo v2 且接近 Quality v1 | 同上 + Per-Shot post-media Gate |
| H6 | Spark fallback dense 在 5090 上 forward 不硬错 | 最小 dispatch A/B（[L3]） |
| H7 | KJ Sage / Sol-Attn fallback 在 5090 上 forward 不硬错 | 同上 |
| H8 | FreeVideo 在独立 Python 3.12 stack 上能否在本机装完并调度 | 隔离 env 搭 + 1 次适配性提交（[L3]，**不产生真成片**） |
| H9 | H3 2K 升频不破坏 state_reference / causal continuity 10 维契约 | 1 镜升 2K + continuity Gate（[L3]） |
| H10 | H3-Context-IR 与现有 3-field prompt 模板兼容性 | 离线 prompt 增量分析；不调 API（[L1]） |

---

## 5. 可直接实施的最小任务（按执行成本递增）

### A 档：0 GPU 成本、文件与脚本类（立即可做）

- **A1**：`ffmpeg -af loudnorm=print_format=json` 对 `runs/drama-h3-t8-30s-preview-20260830-final-v2/outputs/*.mp4` 测 Integrated LUFS · True-peak · LRA
- **A2**：`pyloudnorm` 对同 6 个 MP4 验 loudness；记录 baseline JSON
- **A3**：写 `docs/research/2026-10-21-minimax-h3-v2-api-delta.md`，列本项目现有 capability 与官方 v2 API 字段差异；含 prompt_expansion_mode / ratio / first_frame 等显式矩阵
- **A4**：核 MiniMax H3 weight license 的 US/EU/UK/KR 排除 + $20M 营收门槛；填 Receipt metadata 字段
- **A5**：写 isolated env 目录约定（`/tmp/wuli-ab/` 或等价临时位置），不污染本机 sealed lane

### B 档：隔离 ComfyUI env、低风险

- **B1**：搭隔离 env：独立 venv、临时 ComfyUI 实例（port != 8188）、临时 T8 HEAD 安装
- **B2**：装 Wuli weight 23.29 GiB；用 nvidia-smi 验 ≈ 8.55 GiB 剩余
- **B3**：5s 单片空提示 forward（无 prompt，无 LoRA），验 `torch.cat(scaled_parts)` 是否触发
- **B4**：同 env 跑 Spark / KJ Sage / Sol-Attn 各 1 次最小 dispatch（空 latent），只验 `[L3]` "是否硬错"

### C 档：隔离 env、A/B 质量对比（依赖 B 全过）

- **C1**：复用 `runs/drama-h3-t8-30s-preview-20260830-final-v2` 中 1 条已接受 Shot 的 exact request
- **C2**：三片同 seed / 同 prompt / 同 first+last / 同 3 reference 图：
  - Quality v1（20 步基线）
  - Turbo v2（4 步现状）
  - Wuli Native 8（8 步候选）
- **C3**：每片 4 维音频 + motion/detail Gate + 人审
- **C4**：决定 Wuli 是否进入 P0 集成或维持 P2

### D 档：官方 API capability 推进（独立于 T8、无 GPU）

- **D1**：新建 `minimax_h3_v2_api` family，按 H3 / H3-Max 各一 capability
- **D2**：profile 完整显式所有 v2 字段（含 `ratio`、`extra.prompt_expansion_mode` 仅 H3-Max、`first_frame` / `last_frame` 与 reference 互斥）
- **D3**：先 768P + 1 reference_image 试；profile 校验全开
- **D4**：可选上 2K + 9 reference 图 + 3 段参考视频 + H3-Context-IR；Budget Guard + one-use permit + Task ID 持久化

### E 档：Receipt 加固（独立于 T8、无 GPU）

- **E1**：在 Receipt schema 上增 `weight_bytes_sha256`、`prompt_content_hash`、`actual_seed`、`actual_scheduler`、`actual_cfg`、`actual_shift_video`、`actual_shift_audio`
- **E2**：在 ProductionStateCommitter 写入路径强制上述字段必须非空
- **E3**：回归测试：故意换 weight / 换 prompt 提交，验 Receipt 哈希不一致时 Manifest 拒绝接受

---

## 6. 与初版报告的差异汇总

| 维度 | 初版 | 修订版 |
|---|---|---|
| Wuli 权重 | 19.9 GiB / 25 GB（混用） | **23.290 GiB**（按字节）|
| 5090 模型驻留 | "装得下"断言 | **8.553 GiB 剩余；vs 历史激活峰值 23.88 GiB 极紧** |
| Wuli 优先级 | P0 验证（直接 A/B） | **P0 高风险 A/B**（强制 P0-a 探针顺序）|
| H3 prompt 增强 | 误 `extra.prompt_expansion_mode` 描述 | H3 不支持；独立 H3-Context-IR 端点 |
| H3-Max 2K | 未单独指出 | **不支持（enumeration 缺）** |
| Regenerate 资格 | 描述为单一 path | **双路并存**：A) `source_task_id`（白名单 + ≤7 天）/ B) `content` + 1 `video_url role=base_video` |
| Spark / Sol-Attn 5090 结论 | "完全失效" | 拆为 [L1] 硬门 + [L4] 实际 fallback 后果未测 |
| 音频评估 | 单一 LUFS 阈值 | **4 维：Loudness / Quality / Lip-sync / Action-sync** |
| 证据等级标注 | 部分混合 | **全文强制 [L1]/[L2]/[L3]/[L4]** |
| 最小任务分解 | 阶段 0~4 + 条件 Gate | **A/B/C/D/E 五档**（按成本递增、并行明确）|

---

## 7. 未变更项（保留初版结论）

- [L1] 不引入整体 T8 升级：135 commit；191 模块改 `comfy_api.latest`；零 deprecation；project 五重 seal 失效风险
- [L1] 不引入视觉标记：`visual_marker.py:1-3` 自承 "not a spatial sampler"；`features.json` 自认残留
- [L1] 不引入 Semantic Bridge：默认 `alpha=0.10` 插值；多桥需 ordered serial；可能退化声音
- [L1] 不引入 Temporal Chunk：与十维因果契约 + 短镜拼接架构重复；chunk 无 crossfade；音频不参与二采
- [L1] 不引入 RADAR / 导演台：与唯一 selector / 唯一 committer / 唯一 Gateway 冲突；无自动 QA；硬绑 ComfyUI 队列
- [L1] 不引入 Veda：作者实测 2.02× 更慢；kernel 名实不副；mode 默认 report_only
- [L1] 不引入 H14 Token LoRA（fase）：`fc2_large_model_GPU_asset_qualified: false`；默认 `delegate_without_scope` 静默失效
- [L1] 不引入 NFE Resume：不哈希权重、不哈希 prompt；与本项目 Receipt+RunBacktrack 异代
- [L1] 不引入 FreeVideo：448×256→512×288 vs 项目 1344×768（7.5× 像素差）；独立 Python 3.12 stack；LoRA 不兼容；cudnn 硬后端
- [L1] 不引入 DRIVE/FINAL 两遍采样：底模是 pruned FL2VA；ORE 日志 `ERROR lora ... adaln_proj.linear.weight shape ... invalid`

---

## 8. 完成清单（相对本次复核要求）

- [x] 五项修正全部执行并按 [L1]/[L2]/[L3]/[L4] 分级
- [x] Wuli 23.29 GiB 算准，5090 内存精算
- [x] H3 / H3-Max API 字段差异精确到字段名 + 计费 + 双路 Regenerate + 7 天窗
- [x] 不再以其他硬件样片当本机已验证
- [x] Spark / KJ Sage / Sol-Attn 严格 [L1]/[L4] 分离
- [x] 音频 4 维评估与既有 Gate 对齐
- [x] P0/P1/P2 结论修订、已证实风险、待 A/B 假设、可直接实施的最小任务
- [x] 不修改生产代码、不下载大模型、不调用付费 API
- [x] 现有 sealed runtime 未动
- [x] 完成最终报告（非仅计划）
