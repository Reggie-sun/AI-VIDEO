# MiniMax H3 Local Quality Parameters

## Scope

本 note 只回答 Local MiniMax H3 `fl2va` 首轮受控画质 A/B 应使用哪些已有参数。它不授权 remote/paid Provider，不改变 Shot Router、continuity contract、sampler、steps、量化、refiner、Manifest、Registry、P5 或 state writer。

## Official Findings

- ComfyUI 官方 H3 教程说明 template 默认使用 fast-preview resolution；16:9 的 full-quality target 约为 `1.0 MP`、`1344×768`，width/height 保持 `32` 的倍数。当前 A/B 选用 `1344×672` 是为了保持旧成片 `2:1` aspect ratio，且仍在 sealed profile 的 `1344×768` capability bounds 内；它不是官方完整 `1344×768` native canvas。[ComfyUI MiniMax H3 tutorial](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)
- 同一官方教程固定 H3 为 `24 fps`，duration 使用 `17k+5` frame grid，并推荐当前下载组合 `minimax_h3_fl2va_pruned_int8_convrot`、`qwen3vl_32b_minimax_h3_nvfp4_awq`、video VAE 与 audio VAE。因此首轮保持 quantization、`res_multistep`、`simple`、`20 steps` 不变，不能在没有独立 A/B 时把它们写成模糊根因。[ComfyUI MiniMax H3 tutorial](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)
- MiniMax 官方将 local H3-Base 描述为 768p output；2K 依赖独立的 `H3-Regenerate-2K` stage，不是对 local base output 做简单插值即可等价。[MiniMax H3 README](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/README.md)
- ComfyUI `SaveVideo` 提供 `codec=auto|h264`；H.264 可选择 `encoding=auto|re-encode`，`re-encode` 接受 CRF `0–51`，默认 `23`，lower CRF means higher quality/larger files。首轮选择 CRF `17` 是受控的高质量 encoder setting，不是 MiniMax 模型官方专属推荐。[ComfyUI SaveVideo source](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_video.py)

## Exact Local Runtime Schema

本机 ComfyUI checkout 为 `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`。`GET http://127.0.0.1:8188/object_info/SaveVideo` 与本地 `comfy_api.latest._io.get_finalized_class_inputs()` / `build_nested_inputs()` 共同确认，API workflow 必须使用 flat dotted dynamic inputs：

```json
{
  "format": "mp4",
  "codec": "h264",
  "codec.encoding": "re-encode",
  "codec.encoding.crf": 17
}
```

ComfyUI 在 execution boundary 将这些 fields 重建为 `SaveVideo.execute()` 使用的 nested codec object。只写 `codec=h264` 不会提供 explicit CRF；直接把自造 nested object 放进 API workflow 也不会进入 finalized dynamic schema。

## Community Signals

- 一条与当前症状相似的 H3 报告称，即使把 CRF 改成 `0`，first frame 仍变软；单独 VAE encode/decode 后也观察到细节损失。这是“编码并非唯一变量”的社区信号，不是当前 Alice root cause proof。[Community blur report](https://www.reddit.com/r/comfyui/comments/1vg96hg/minimax_h3_output_looks_much_blurrier_than_the/)
- 社区还有 BF16/INT8、额外 sigma、Turbo LoRA、Sage Attention 和 external upscaler 方案，但它们通常同时改变多个变量，缺少同一 Alice inputs 的 sharpness/SSIM/bitrate comparison，不应进入首轮受控 A/B。

## First-Round Decision

只改变两项：

1. `1024×512 -> 1344×672`，保持 `2:1` aspect ratio、`24 fps`、`124 frames`、`res_multistep`、`simple`、`20 steps`、相同 prompts/seeds/reference bytes。
2. `SaveVideo codec:auto -> H.264 re-encode CRF 17`，并优先以 stream copy 连接两个兼容 source clips，避免 final composition 再次有损编码。

`608×352` 原始 Alice reference 的插值放大不能称为 native high-resolution reference。若上述 A/B 证明 source encoding/resolution 有改善但人物细节仍受 reference 限制，下一轮才使用现有 local P7 image lane 生成或导入原生高分 reference，并独立保存 provenance。

## Measured Result

- 同一插值reference、prompts与seeds的受控A/B中，新quality profile把两段source video bitrate从`559/798 kbps`提高到`2994/2958 kbps`。统一缩到`1024×512`后抽16帧，Laplacian variance mean从`109.154`提高到`112.647`（+3.20%），Tenengrad mean从`9170.554`提高到`9701.114`（+5.79%）；decoded Shot boundary SSIM从`0.928515`提高到`0.936091`。因此输出分辨率与编码被证实是贡献因子，但不是完整根因。
- 人物细节仍相对背景偏软后，使用既有loopback-only P7 Qwen Image Edit 2511 lane生成一次原生`1344×672` RGB Alice reference，SHA-256 `99253a9dc5a705487a35b016e18e5fb5b693d78f444a959054c1fbce0c73ed6d`。P7 result为`succeeded`；candidate activation在result materialize后被P5 scope validation拒绝，已explicit recovery、没有blind retry，并以exact request/result/receipt/profile provenance诚实import该PNG，不称为activated P7 asset。
- P7 reference最终片为`runs/h3-shot-router-quality-p7-20260820-v1/evidence/alice-cafe-exact-terminal.mp4`，SHA-256 `05c00691a7a04d8e0864f018073ea746ccba3e0cba38aa0c9f651180d30bae9e`。统一缩放后Laplacian mean为`244.187`（相对旧片+123.71%），Tenengrad mean为`11032.689`（+20.31%）；decoded boundary SSIM为`0.937613`，exact terminal/input SHA一致。该结果把当前Alice模糊归因为低输出/弱编码与低原生reference的共同作用；int8、20 steps与无refiner仍未被本轮A/B判定为根因。
