# T8 And LatentSync Local Runtime

## Purpose And Evidence

按需读取的 host-native advisory recipe，不是 Production profile、自动启动授权或 acceptance。
历史版本、weights hashes、实验结果见
[2026-08-25 experiment](../../docs/record_for_agent/2026-08-25-t8-latentsync-speaking-subtitle-experiment.md)。
下面路径/版本先核对当前存在与依赖，不把历史配置当作 current runtime。

## Lifecycle And Workflow

T8 与 LatentSync 串行占 GPU；完成 T8 fetch/decode 后显式停止 ComfyUI，再启动 lip-sync。
ComfyUI 仅用 repository `scripts/comfyui_supervisor.py`，不 nohup/裸 main.py/复用 unit。

```bash
python scripts/comfyui_supervisor.py status
python scripts/comfyui_supervisor.py start --comfy-root /home/reggie/ComfyUI --python /home/reggie/miniconda3/bin/python --port 8188 --health-timeout 60
python scripts/comfyui_supervisor.py logs --lines 100
curl --fail --silent http://127.0.0.1:8188/queue
python scripts/comfyui_supervisor.py stop
```

使用前确认 queue empty、unique request 与 exact loopback listener ownership；service active 不证明媒体成功。
默认 normal GPU memory management + SageAttention，无隐式 lowvram；仅 accepted task 要 CPU offload 时显式 novram。
非登录 shell 的 bus failure 先核对同用户 `/run/user/<uid>/bus`；不切 root systemd。
T8-only graph 必须包含 Conditioning/DualClockSampler/AVDecode T8，单一 sampling owner；
不能用 TurboLoRA/TurboSampler/BypassModelOnly 或 Turbo weights。已注册 plugin 不证明提交 graph 用了它。
这些 lifecycle/profile 约束由 policy `local_comfyui_supervisor_tests` 与 Provider suites 验证；live graph 仍须重开核对。

## LatentSync Preflight And Inference

使用 `/home/reggie/.cache/ai-video/latentsync-v1.6/.venv-5090/bin/python`，不使用 ComfyUI Python。
先核对 GPU、checkout、weights 和每帧 usable face；拒绝只为修嘴型破坏已满足整体观看要求的方案。
CUDA 13 NVRTC 缺 builtins 先最小复现，不重装 CUDA/blind retry。下例独立 task paths 用实际 identity 替换，
existing outputs 不覆盖；ComfyUI 必须已经停止。

```bash
cd /home/reggie/.cache/ai-video/latentsync-v1.6
export LATENTSYNC_CUDA_LIB=/home/reggie/micromamba/envs/comfyui/lib/python3.12/site-packages/nvidia/cu13/lib
export LD_LIBRARY_PATH="$LATENTSYNC_CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
.venv-5090/bin/python -c 'import torch; print(torch.det(torch.eye(2,device="cuda")).item())'
ffmpeg -v error -i /absolute/task/source.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le /absolute/task/source-16k.wav
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 NO_ALBUMENTATIONS_UPDATE=1 \
.venv-5090/bin/python -m scripts.inference \
  --unet_config_path configs/unet/stage2_512.yaml --inference_ckpt_path checkpoints/latentsync_unet.pt \
  --inference_steps 20 --guidance_scale 1.5 --seed 1247 \
  --video_path /absolute/task/source.mp4 --audio_path /absolute/task/source-16k.wav \
  --video_out_path /absolute/task/corrected.mp4 --temp_dir /absolute/task/latentsync-temp
```

历史 v1.6 输出规范化为 25 fps；重新 probe + video/audio full decode，不把它当 T8 setting 变化。
离线 env 不授权自动模型下载；缺依赖停在当前证据边界。

## SyncNet And Subtitles

同一 SyncNet model，对 source/output 分开 temp dirs：

```bash
NO_ALBUMENTATIONS_UPDATE=1 .venv-5090/bin/python -m eval.eval_sync_conf \
  --initial_model checkpoints/auxiliary/syncnet_v2.model \
  --video_path /absolute/task/corrected.mp4 --temp_dir /absolute/task/syncnet-output
```

若 NVRTC 失败重查本次 library path；分别报告 source/output metrics。confidence/offset 不证明中文逐字 viseme、
声音语义/自然度或 human full-speed acceptance。
字幕从 accepted dialogue 或实际转写/人工确认取时间，不能把 prompt 当 native audio 事实。
先核对当前 ffmpeg filter/font availability；libass 不可用时 drawtext 使用 exact Noto CJK font 和 UTF-8 textfile，
编码 video、`-c:a copy`。最终 full decode + decoded PCM hash 比较；字幕排版/遮挡与嘴型仍需观看。

## Completion Boundary

逐 Shot 使用显式 video-analysis Gate；全部媒体 effects 走当前 accepted seams，不裸 submit、自动 retry/fallback。
本 recipe 没有通用 lip-sync execution Harness：当前 GPU/queue、CUDA、face availability 与输出仍须实际取证。
Host-native checkout 不是 Docker；technical completion、SyncNet offset 0、历史实验不产生 qualification/P6/Final Acceptance。
