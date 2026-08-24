# Shot Continuity E0-A Development Experiment Record

Date: 2026-08-24

## Purpose

本文记录 Shot Continuity 执行顺序切换后的第一份真实 Local T8 visual evidence。实验只回答当前 rainy-station character/reference、prompt 与本地 MiniMax H3 FL2VA quality stack 能否生成值得继续检查的短视频。

本结果分类固定为 `development_experiment`。它不是 Production attempt、qualification evidence、active capability、winner evidence、P6 Final Acceptance、`C4_DESTINATION_READY`、replay proof 或 production validation snapshot，也没有写入 Production Manifest / Registry lifecycle。

## Current Runtime Truth

实验开始时 repository HEAD 为 `5ff40cf05b31c2580371b8cd2e55522a37d417de`。生成完成前另一个既有 writer 将 local `main` 推进到 `eebbd364a414762133061734967fad93f784efd7`；该提交未改变本实验的 model、workflow、reference、prompt、seed 或输出。实验没有修改、stage 或 commit 当时已有的 unrelated dirty files。

Local runtime identity：

- GPU：NVIDIA GeForce RTX 5090。
- ComfyUI：`0.33.2`，commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`，只监听 `127.0.0.1:8188`。
- T8：`minimax-h3-audio-T8` `1.36.2`，commit `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`。
- VideoHelperSuite commit：`4ee72c065db22c9d96c2427954dc69e7b908444b`。
- Python `3.13.5`、torch `2.9.0+cu128`、SageAttention `2.2.0`；ComfyUI 以 `--use-sage-attention`、`--preview-method none` 启动。
- live `/object_info` 含 `1177` nodes；quality workflow 所需 `14` nodes 全部存在。

启动时 ComfyUI 报告 unrelated `nodes_glsl.py` / `nodes_math.py` optional import warnings，但本次所需 MiniMax H3、T8 与 VideoHelperSuite nodes 均正常加载。没有安装、升级或修改 ComfyUI、T8、dependency 或 model files。

## E0-A Exact Inputs And Stack

本轮使用当前 rainy-station frozen A2/A3，保持 mustard-yellow raincoat、short black bob、black trousers、black boots、red cross-body satchel 与同一 wet station platform，不重新创作更容易的 case：

- first frame SHA-256：`c50517a17313402ef271694ea058d6c92b0b750c4b854e39858bdaf5d73c5768`，`1659x948`，`1,984,532` bytes。
- last frame SHA-256：`03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c`，`1659x948`，`1,966,518` bytes。
- prompt SHA-256：`f9d0f7492af21bbfd52e6affa8e1f93bc8b73982152ed046a38c0011d12e9e7a`。
- seed：`6623081611478359059`。
- request source：pre-existing untracked `workflows/qualification/minimax_h3_fl2va_rainy_station_source_v1_profile.json`，本实验未修改；file SHA-256 `e5d9e001d3cb0d2e8315749e95a3e5ca7b3df622180bf39a446a92a8217310fe`，internal profile hash `783aad50225848ef055eab724d5f3e25ead77771ff41cc6f775b8261bbd77cb0`。

Exact execution stack：

- profile：`workflows/profiles/minimax_h3_fl2va_quality.json`，content hash `a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`。
- workflow：`workflows/templates/minimax_h3_fl2va_quality_api.json`，SHA-256 `8b6c338279d8af768fae8106034f9f26e8e9d59583e95a8ca8b16d36a930ad65`。
- binding：`workflows/bindings/minimax_h3_fl2va_quality_binding.yaml`，SHA-256 `e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c`。
- diffusion：`minimax_h3_fl2va_pruned_int8_convrot.safetensors`，SHA-256 `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a`。
- text encoder：`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`，SHA-256 `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6`。
- video VAE：`minimax_h3_video_vae_fp16.safetensors`，SHA-256 `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522`。
- audio VAE：`minimax_h3_audio_vae_fp32.safetensors`，SHA-256 `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48`。
- sampling：`1344x768`、124 frames、24 fps、20 steps、`res_multistep` / `simple`、Turbo LoRA off、native audio、H.264 re-encode CRF 17。

四个 model files 在 submit 前重新计算 SHA-256，均与 profile exact 匹配。workflow dry-render 与 API topology validation 通过；当时 ComfyUI queue 与 history 均为空。

## E0-A Local Execution And Media Evidence

唯一 local prompt ID 为 `62e6db35-ed5e-4c56-90d0-27eec6139ea0`。ComfyUI terminal status 为 `completed` / `success`，执行时间 `391.84s`。

Effect counters：

- local input uploads：`2`；
- local prompt submits：`1`；
- retry：`0`；
- fallback：`0`；
- remote submits：`0`；
- paid effects：`0`。

Output：

- path：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0a_20260824_00001_.mp4`；
- SHA-256：`08daec78d274fa2fae67595f17488f1811d7ecaa00c5795ac8fb4760305cc93f`；
- size：`3,493,186` bytes；
- video：H.264 High、`1344x768`、yuv420p、24 fps、124 frames、`5.166667s`；
- audio：AAC LC、32 kHz、stereo、`5.167s`；
- decoded frame 0 SHA-256：`658a5a7c86e9f24a2a57ff63edd3d2c0dbf6860879c7e6686f3376531159287b`；
- decoded frame 123 SHA-256：`25dee57a0f3f5883909d6e0f5a406ac20fb2b779cd5e64e8876199ba70e584b9`。

隔离 metadata 位于 `/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0a_20260824_metadata.json`，SHA-256 `5edb1159dd6b1a976785ea748af0ddb409f70a968faa8f3042f209d057b141fb`。12-frame contact sheet 位于同目录的 `shot_continuity_e0a_20260824_contact_sheet_12.jpg`，SHA-256 `f74d7b4fe06b04502fba62ea3b4274a5a440795dc2bbb564585683aca5b3513c`。

## Visual Triage

Agent 对 12 个按时间排序的代表帧做了直接视觉检查，并使用 project-local `video-analysis` 做辅助结构检查。自动结果为 one scene、167/167 sampled frames unique、audio present、issues empty；这些自动指标不拥有视觉 verdict。

代表帧中 character face、short black bob、mustard-yellow raincoat、black trousers 与 red satchel 保持可辨识稳定；screen-right direction 与 wet platform geometry 连续，没有看到 duplicated person、extra limb、hard cut、teleport、gross pose collapse 或 obvious segment seam。短烟测中的 framing 变化渐进，整体达到继续核查长路线的门槛。

初始 Agent triage 为 `PASS_TO_E0_B`。随后用户直接观看 exact MP4，指出约4秒后画面进入近静止；frame-level复核确认该初始 verdict 过于乐观。修正后的 E0-A 结论为：technical execution `PASS`、motion quality `BORDERLINE`，不得直接进入 E0-B。

124个 decoded frames 的hash均不同，因此不是 repeated-frame export padding。Exact local source mapping确认 `length=124` 直接创建 video latent `T=37`，sampler保持该 temporal shape，VAE直接解码为124帧；不存在先采样107帧再补17帧的路径。Baseline在frames 105–119的 consecutive-frame MAD mean仅为`0.248160`，median optical-flow mean仅为`0.008383`；frames 120–123进一步降至`0.069485`与`0.002880`。这说明最后一个17-frame temporal block虽然被真实采样，但显著收敛到 explicit A3 last-frame anchor。

## Follow-up Single-Variable Prompt A/B

为区分 prompt interaction 与强 endpoint conditioning，2026-08-24执行一次单变量 local prompt A/B。必须先纠正一个事实：baseline exact prompt并不包含“gradually slows down”或“comes to a stop”，而是已经要求“mid-stride with continuing gait and satchel motion”。因此该A/B测试的是普通持续运动指令与显式 anti-freeze指令的差异，而不是删除实际不存在的stop语义。

A/B保持以下内容exact不变：model、seed `6623081611478359059`、A2/A3 bytes、workflow、`1344x768`、124 frames、24 fps、20 steps、`res_multistep/simple`、Turbo off、native audio与H.264 CRF 17。唯一改变是将endpoint-motion句加强为：角色必须持续自然步行并保持可见前进运动直到最后一刻，不得 pause、freeze、hold pose或在final frame前提前settle。新prompt SHA-256为`4cbb034a207964854465c0250975383975a105f6f65ef50c70912f36251920c5`。

唯一A/B submit prompt ID为`e15897e1-de22-4fb6-8198-9b189b3c5023`，terminal status为`success`，wall time `379.80s`。输出：

- path：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0a_prompt_ab_motion_20260824_00001_.mp4`；
- SHA-256：`163a79d5e697dc44fd7f8fbe3ea99ed4602200c089e218ff7709de07aeb665f0`；
- `3,408,858` bytes，H.264 `1344x768` yuv420p、24 fps、124 frames、`5.167s`，AAC 32 kHz stereo；
- isolated metadata：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0a_prompt_ab_motion_20260824_metadata.json`，SHA-256 `57f46163afab853ec517e786ac126281e53024c12150d05cb7810a62aa302ebe`；
- baseline/A-B tail contact sheet：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0a_prompt_ab_tail_compare_20260824.jpg`，SHA-256 `261d24a821988e86bf67294e258d72de94db80f7c32e713d26118a3eebeccd58`。

结果没有改善。A/B在frames 105–119的 consecutive-frame MAD mean为`0.125685`，median optical-flow mean为`0.004082`；frames 120–123为`0.046602`与`0.001623`，均低于baseline。并排视觉检查同样显示A/B约在frames 100–105快速落到A3，随后保持近静止。结论为`STRONG_LAST_FRAME_ENDPOINT_CONDITIONING_DOMINATES`：更强的prompt语言不足以抵抗当前A3 endpoint conditioning，prompt interaction不是主要解释。

在该A/B前曾按上一条用户指令提交一次141-frame overshoot experiment；用户随后明确改为124-frame clean A/B，因此该prompt在sampler step 4/20时被显式interrupt，terminal status为`execution_interrupted`，没有output。它不是retry、fallback或A/B evidence。本follow-up共发生2次local prompt effect：1次superseded/interrupted、1次A/B success；remote submit、paid effect、fallback与input upload均为0。

## Why E0-B Was Not Submitted

当前 installed T8 `1.36.2` 确实包含 `MiniMaxH3LongVideoConditioningT8`、`scene_plus_identity`、22-frame context 与 background orchestration route，但 frozen E0-B 仍缺可执行的 exact identity：

1. `docs/record_for_agent/2026-08-23-shot-continuity-experiment-contract.md` 明确记录尚未选择或生成 beige-trench character 的 exact canonical reference；当前 rainy-station A2/A3 是 mustard-yellow raincoat，不能在不改 frozen prompt/reference 的情况下代替。
2. installed ready-to-import `ScenePlusIdentity` background template 使用 `minimax_h3_fl2va_int8_convrot.safetensors`、Turbo 4-step LoRA 与 4-step dual-clock sampling；accepted Shot Continuity plan 冻结 Stock20、`dual_clock_euler`、`native_flow`、Turbo off。当前没有已冻结、已核对的 exact 770-frame workflow/profile 把这些 surfaces 统一起来。

因此 E0-B seed `320001` 未提交。没有临时换 reference、改 prompt、开 Turbo、降 resolution/duration/motion、写一次性 fallback workflow、自动 retry 或运行其他 seed。这符合 current task 的 stop condition，而不是 Local T8 technical generation failure。

## Repository And Publication State

本次 generation、probe、frames、contact sheet 与 metadata 全部保存在 `/home/reggie/ComfyUI/output/development_experiment/`，不在 Production state 中。除本记录外，本任务没有修改 repository source、tests、workflow、plan、Manifest、Registry、Harness policy 或 lifecycle。

记录创建前 local `main` 为 `eebbd364a414762133061734967fad93f784efd7`，相对 `origin/main` ahead 2；publication、push 与 release 未执行。既有 dirty/untracked work 与空 index 保持不变。

## Assessment And Next Boundary

新的 empirical evidence 是：current RTX 5090、current ComfyUI/T8/model bytes 与 frozen rainy-station A2/A3 能用20-step local FL2VA quality route稳定完成技术执行，但当前strong A3 last-frame conditioning会吞掉最后约一个17-frame block的可见运动。显式anti-freeze prompt没有改善，反而得到更低的tail motion measurements。此前“能否真实运行”的未知已关闭；“该FL2VA endpoint strategy能否提供可接受的motion tail”仍未关闭。

Production Qualification gates 仍保持 open，包括 exact E0-B stack/reference freeze、M0/M1 qualification、one-use Production permit、lifecycle/replay/recovery、winner selection、P6 与 Final Acceptance。`PASS_TO_E0_B` 不自动关闭任何这些 gates。

Next One Thing：先将A3替换或重新设计为真正 motion-compatible 的 endpoint，并做一次新的single-variable endpoint A/B；在短片最后一个temporal block恢复可见步态前，不直接进入32-second E0-B。该变化属于新的experiment contract，不得把本次失败A/B自动重跑或改写为Production evidence。

## Agent Guardrails

- 本输出只能称为 `development_experiment`，不能导入或激活为 Production evidence。
- 当前E0-A只能称为technical `PASS` / motion-quality `BORDERLINE`；不得沿用初始`PASS_TO_E0_B`描述。
- explicit anti-freeze prompt没有关闭motion-tail问题；后续优先检查motion-compatible A3，而不是继续堆叠prompt措辞。
- 任何后续 E0-B submit 必须继续保持 local-only、seed `320001`、`1344x768`、24 fps、770 frames、22-frame context、no retry、no fallback，并先关闭 exact reference/stack identity。
- 不得因 E0-A 好看而跳过 materialization、permit、lifecycle、replay、recovery、qualification 或 P6。
- 不得用 E0-A 的 mustard-raincoat frames 偷换 E0-B frozen beige-trench prompt/reference，也不得用 installed Turbo example 代替 frozen Stock20/Turbo-off route。
