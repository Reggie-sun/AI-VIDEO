# T8 And LatentSync Local Runtime

## Purpose

本文记录 2026-08-25 在当前 RTX 5090 主机上实际验证过的 MiniMax H3 T8
生成、LatentSync v1.6 嘴型校正、SyncNet 检测与硬字幕运行方式。它是
Development-side 操作记录，不是 Production Provider profile、Manifest、Registry、
P6、Final Acceptance 或自动启动授权。

运行原则：ComfyUI/T8 与 LatentSync 串行使用 GPU。先完成 T8 生成并显式停止
ComfyUI，再启动 LatentSync；不要让两套大模型同时驻留显存。

## Validated Host Environment

| Surface | Validated value |
| --- | --- |
| GPU | `NVIDIA GeForce RTX 5090`, `32607 MiB` |
| NVIDIA driver | `595.84` |
| ComfyUI checkout | `/home/reggie/ComfyUI` at `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` |
| ComfyUI Python | `/home/reggie/miniconda3/bin/python`, Python `3.13.5` |
| ComfyUI Torch | `2.9.0+cu128`; torchvision `0.24.0`; SageAttention `2.2.0` |
| T8 custom node | `/home/reggie/ComfyUI/custom_nodes/minimax-h3-audio-T8` at `28cb160827c245b2d6a37539df30c1d7c5e7aecd` |
| LatentSync checkout | `/home/reggie/.cache/ai-video/latentsync-v1.6` at `a229c3948406bc2cf6eaf4873e662e70c6a04746` |
| LatentSync Python | `.venv-5090/bin/python`, Python `3.12.13` |
| LatentSync Torch | `2.11.0+cu130`; torchvision `0.26.0+cu130` |
| Main LatentSync packages | diffusers `0.32.2`, transformers `4.48.0`, onnxruntime-gpu `1.21.0`, insightface `0.7.3` |

Current T8 model files used by the quality/20-step route include:

```text
/home/reggie/ComfyUI/models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors
/home/reggie/ComfyUI/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
/home/reggie/ComfyUI/models/vae/minimax_h3_video_vae_fp16.safetensors
/home/reggie/ComfyUI/models/vae/minimax_h3_audio_vae_fp32.safetensors
```

## T8-Only Workflow Boundary

本路线的生成 graph 使用 T8 自有组件：

```text
MiniMaxH3AudioConditioningT8
  -> MiniMaxH3DualClockSamplerT8
  -> MiniMaxH3AVDecodeT8
```

`/home/reggie/ComfyUI/custom_nodes/ComfyUI-MiniMax-H3-Turbo` 是主机上预先存在的
checkout，但本路线不安装、不更新、不修改也不调用它。T8-only request 必须满足：

- 不出现 `MiniMaxH3TurboLoRA`；
- 不出现 `MiniMaxH3TurboSampler`；
- 不出现 `LoraLoaderBypassModelOnly`；
- 不加载任何 Turbo LoRA；
- sampling-policy owner 只有一个 `MiniMaxH3DualClockSamplerT8`。

ComfyUI 启动时可能发现并注册所有已安装 custom nodes；节点被注册不等于 workflow
使用它。是否使用 Larry/Turbo 必须以 exact submitted graph 为准。

## Supervised ComfyUI Lifecycle

只使用 repository owner `scripts/comfyui_supervisor.py`。不要用 `nohup`、后台 shell、
可复用 unit name 或直接运行长期 `main.py`。

```bash
cd /home/reggie/vscode_folder/AI-VIDEO

python scripts/comfyui_supervisor.py status

python scripts/comfyui_supervisor.py start \
  --comfy-root /home/reggie/ComfyUI \
  --python /home/reggie/miniconda3/bin/python \
  --port 8188 \
  --health-timeout 60

python scripts/comfyui_supervisor.py logs --lines 100
```

`start` 创建一次性的 `ai-video-comfyui-<32-lowercase-hex>.service` user-systemd
transient unit，固定 `127.0.0.1:8188`、`Restart=no`、`--lowvram` 与
`--use-sage-attention`。启动后仍需单独检查应用 queue；service active 不能证明
queue empty、生成成功或媒体质量通过。

```bash
curl --fail --silent http://127.0.0.1:8188/system_stats >/dev/null
curl --fail --silent http://127.0.0.1:8188/queue | jq .
```

提交工作前确认 queue empty；只提交 accepted scope 内的 exact request。生成完成、输出
fetch 与 decode 验证结束后：

```bash
cd /home/reggie/vscode_folder/AI-VIDEO
python scripts/comfyui_supervisor.py stop
python scripts/comfyui_supervisor.py status
ss -ltnp | rg ':8188\b' || true
```

若非登录 shell 报 `Failed to connect to bus`，先确认当前用户 runtime bus 实际存在，
再在同一用户 session 中恢复以下 task-scoped values；不要切换到 root systemd：

```bash
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
test -S "$XDG_RUNTIME_DIR/bus"
```

## LatentSync Weights

Validated files:

| File | SHA-256 |
| --- | --- |
| `checkpoints/latentsync_unet.pt` | `0a478e89eb660f82da4c35dbdde8a5adfb27f99d1b4e50edd03729e1e98316d3` |
| `checkpoints/auxiliary/syncnet_v2.model` | `961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442` |
| `checkpoints/auxiliary/sfd_face.pth` | `d54a87c2b7543b64729c9a25eafd188da15fd3f6e02f0ecec76ae1b30d86c491` |
| `checkpoints/whisper/tiny.pt` | `65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9` |

LatentSync 的 `.venv-5090` 是基于本机 ComfyUI Python 3.12 environment 的 isolated
overlay；不要用 `/home/reggie/miniconda3/bin/python` 运行 LatentSync。

## CUDA 13 NVRTC Preflight

Torch `2.11.0+cu130` 需要 CUDA 13 NVRTC builtins。库已存在，但 overlay 启动时若
没有正确的 dynamic-library search path，会在 face affine transform 阶段失败：

```text
nvrtc: error: failed to open libnvrtc-builtins.so.13.0
```

不要重装整套 CUDA 或 blind retry。先设置本次进程使用的精确目录并运行最小复现：

```bash
export LATENTSYNC_CUDA_LIB=/home/reggie/micromamba/envs/comfyui/lib/python3.12/site-packages/nvidia/cu13/lib
export LD_LIBRARY_PATH="$LATENTSYNC_CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

/home/reggie/.cache/ai-video/latentsync-v1.6/.venv-5090/bin/python - <<'PY'
import torch
x = torch.eye(2, device="cuda")
print(torch.__version__, torch.version.cuda, torch.det(x.float()).item())
PY
```

Validated result is Torch `2.11.0+cu130`, CUDA `13.0`, determinant `1.0`.

## LatentSync Inference

先确认 ComfyUI 已停止，并为输入 MP4 提取 exact 16 kHz mono PCM：

```bash
INPUT_VIDEO=/absolute/path/to/t8-source-audio.mp4
INPUT_AUDIO=/tmp/t8-source-16k.wav
OUTPUT_VIDEO=/absolute/path/to/latentsync-output.mp4

ffmpeg -y -v error -i "$INPUT_VIDEO" -vn \
  -ac 1 -ar 16000 -c:a pcm_s16le "$INPUT_AUDIO"

ss -ltnp | rg ':8188\b' || true
nvidia-smi --query-gpu=name,memory.used,memory.free --format=csv,noheader
```

从 LatentSync checkout 运行：

```bash
cd /home/reggie/.cache/ai-video/latentsync-v1.6

export LATENTSYNC_CUDA_LIB=/home/reggie/micromamba/envs/comfyui/lib/python3.12/site-packages/nvidia/cu13/lib
export LD_LIBRARY_PATH="$LATENTSYNC_CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

HF_HOME=/home/reggie/.cache/ai-video/huggingface \
HF_HUB_CACHE=/home/reggie/.cache/ai-video/huggingface/hub \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
NO_ALBUMENTATIONS_UPDATE=1 \
.venv-5090/bin/python -m scripts.inference \
  --unet_config_path configs/unet/stage2_512.yaml \
  --inference_ckpt_path checkpoints/latentsync_unet.pt \
  --inference_steps 20 \
  --guidance_scale 1.5 \
  --seed 1247 \
  --video_path "$INPUT_VIDEO" \
  --audio_path "$INPUT_AUDIO" \
  --video_out_path "$OUTPUT_VIDEO" \
  --temp_dir /tmp/latentsync-task-temp
```

LatentSync v1.6 会把视频规范化到 25 fps；这不是 T8 generation setting 变化。
输出后必须重新 `ffprobe` 并做 video/audio full decode。

## SyncNet Comparison

对原 T8 source 与 LatentSync output 使用不同的 `--temp_dir`，保持同一模型：

```bash
cd /home/reggie/.cache/ai-video/latentsync-v1.6

NO_ALBUMENTATIONS_UPDATE=1 \
.venv-5090/bin/python -m eval.eval_sync_conf \
  --initial_model checkpoints/auxiliary/syncnet_v2.model \
  --video_path "$INPUT_VIDEO" \
  --temp_dir /tmp/syncnet-source

NO_ALBUMENTATIONS_UPDATE=1 \
.venv-5090/bin/python -m eval.eval_sync_conf \
  --initial_model checkpoints/auxiliary/syncnet_v2.model \
  --video_path "$OUTPUT_VIDEO" \
  --temp_dir /tmp/syncnet-output
```

若该 shell 没有继承前述 `LD_LIBRARY_PATH`，先重新执行 CUDA 13 NVRTC preflight。
SyncNet confidence/offset 只属于 automated technical evidence；它不能证明中文逐字
viseme、自然度、声音语义或 human full-speed acceptance。

## Burned Chinese Subtitles

当前 `/home/reggie/miniconda3` ffmpeg 没有 `subtitles/libass` filter，但有
`drawtext/libfreetype`。使用 Noto CJK 字体烧录固定文本，音轨用 `-c:a copy`：

```bash
CAPTION_TEXT=/tmp/caption.txt
SUBTITLED_VIDEO=/absolute/path/to/subtitled-output.mp4

printf '%s\n' '我们快到了，再往前走一段。' >"$CAPTION_TEXT"

ffmpeg -y -v error -i "$OUTPUT_VIDEO" \
  -vf "drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc:textfile=$CAPTION_TEXT:fontcolor=white:fontsize=36:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-text_h-42:enable='between(t\,0.8\,3.9)'" \
  -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p \
  -c:a copy -movflags +faststart "$SUBTITLED_VIDEO"
```

字幕时间必须来自 accepted dialogue contract 或实际转写/人工确认，不能把 prompt 文本
自动当作 native audio 的逐字事实。烧录后再次 full decode，并比较烧录前后 decoded PCM
hash，确认字幕步骤没有更换音轨。

## Validation Checklist

```text
[ ] exact request graph contains T8 nodes and no Larry/Turbo/LoRA nodes
[ ] supervised unit owns exact 127.0.0.1:8188 listener
[ ] queue empty before unique submit
[ ] T8 output has video and audible audio streams
[ ] full video/audio decode passes
[ ] ComfyUI is stopped before LatentSync
[ ] CUDA 13 torch.det preflight passes
[ ] every source frame retains a usable face before lip-sync processing
[ ] LatentSync output full decode passes
[ ] source/output SyncNet metrics are reported separately
[ ] subtitle render is visually inspected and preserves corrected audio
[ ] human full-speed lip-sync and voice verdict remains explicit
```

## Provenance Boundary

这套环境目前是 host-native checkout + isolated Python overlay，不是 Docker。不要因为
本文存在就自动下载、更新、启动、提交媒体、retry、fallback 或进入 Production lifecycle。
Larry plugin 的 installed presence、T8 technical completion、LatentSync success 与 SyncNet
offset `0` 均不能单独升级为 Production qualification、P6 或 Final Acceptance。
