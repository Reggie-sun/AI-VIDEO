# RTX 5090 Continuity Visual Backend Selection

## Status

Selection and bounded local-install record. 已安装并技术验证GPU runtime与exact model bytes；没有生成媒体，也没有作出质量验收结论。

## Executive Decision

推荐 bounded install target：

1. **Detector:** official `YOLOX-S` COCO ONNX release asset `yolox_s.onnx` from tag `0.1.1rc0`。
2. **ReID:** author-published `OSNet x1.0`, trained on `MSMT17 combineall`, source checkpoint `osnet_x1_0_msmt17_combineall_256x128_amsgrad_ep150_stp60_lr0.0015_b64_fb10_softmax_labelsmooth_flip_jitter.pth`。
3. **GPU runtime:** `onnxruntime-gpu==1.26.0`, CUDA 12.8 / cuDNN 9 build, replacing—not co-installing beside—the CPU `onnxruntime` distribution。
4. **Execution policy:** sealed `CUDAExecutionProvider` only for Production evaluation; no silent CPU fallback. A separate explicit CPU profile may remain available for tests or recovery, but it must have a different profile hash。

## Installed Result

当前host最终把`onnxruntime-gpu==1.26.0`隔离安装在`/home/reggie/.local/share/ai-video/continuity-gpu-venv/`，wheel SHA-256为`cfda2fad535595bfc3e570eb588092717711dcb2957656d814695e0c9ceb1508`。主Conda环境已恢复`onnxruntime==1.23.2`，避免破坏既有Agent Memory CPU runtime identity；legacy offline adapter按profile中的exact distribution identity兼容`onnxruntime`或`onnxruntime-gpu`，不会伪造runtime name。GPU profile还seal当前CUDA 12.8/cuDNN 9 NVIDIA wheel identities，并从各distribution的exact library directory显式preload shared libraries，不依赖silent global loader state。

Model store为`/home/reggie/.local/share/ai-video/continuity-models/yolox-osnet-v1/`，不在Git repository内，文件为regular、single-link、mode `0444`：

- `yolox_s.onnx`: `35,858,002` bytes，SHA-256 `c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063`。
- `osnet_x1_0_msmt17.onnx`: `8,728,948` bytes，derived SHA-256 `afea03904fab11c61e6a32b4e36a1cd5942875b4b3e4514c15de1e98d795173e`；source checkpoint SHA-256仍为`48df972f72887b95cf3b43b3a07c3a7d2398381aea0f9cae64a7ef11d512b727`。

OSNet导出固定Torchreid revision`f8cd150fdf77e8d9e1ed143b7f308c2c609ded50`、model revision`a5c5cc037c24235cda3b21085b93ad77c9616224`、PyTorch `2.9.0+cu128`、ONNX `1.19.1`、opset 12、strict state-dict load与fixed batch 1。关闭TF32后，CPU/CUDA归一化embedding最大绝对差为约`1.12e-6`。

CUDA-only profiling实际得到：YOLOX输出`(1, 8400, 85)`、OSNet输出`(1, 512)`，两者node provider集合均只有`CUDAExecutionProvider`。这只是technical execution proof；尚未用真实generated Shot完成阈值校准或quality acceptance。因此sealed profile固定`human-confirmation-required`：automatic mismatch可以保守阻止activation，automatic match必须转`not_evaluated`并由exact human fallback确认，不能单独帮助P6产生PASS。

Executable model schema还结构化seal fixed batch `1`、input channels `3`、`float32` dtype、YOLOX opset `11`、OSNet opset `12`、input geometry与output dimensions；combined with exact model SHA-256，这些字段不再只存在于opaque contract string。

这套组合的 license surface 相对清晰：YOLOX repository 是 Apache-2.0，Torchreid/OSNet repository 和 author model repository 标为 MIT；两者都有 first-party export/deployment material。[YOLOX official repository and license](https://github.com/Megvii-BaseDetection/YOLOX/tree/419778480ab6ec0590e5d3831b3afb3b46ab2aa3) · [Torchreid official repository](https://github.com/KaiyangZhou/deep-person-reid/tree/f8cd150fdf77e8d9e1ed143b7f308c2c609ded50) · [OSNet author model repository](https://huggingface.co/kaiyangzhou/osnet/tree/a5c5cc037c24235cda3b21085b93ad77c9616224)

**Important compatibility result:** these upstream assets are not drop-in compatible with the current `ContinuityVisualProfile`. Current code applies one `rgb24-nearest-chw-float32-0-1/1` transform to both roles and requires detector output exactly `[N, 6] = normalized xyxy, score, class`. YOLOX officially uses aspect-preserving letterbox input followed by decode and NMS; OSNet officially uses RGB `[0,1]` plus ImageNet mean/std normalization. Activating the files without first extending and sealing role-specific preprocessing/output contracts would produce semantically invalid measurements, even if ONNX Runtime successfully loads them。[current adapter](../../src/ai_video/production/continuity_evaluator.py)

Therefore the safe choice is **select and install the immutable upstream inputs, build sealed derived ONNX/runtime contracts, then activate only after equivalence and CUDA-placement tests pass**. Do not merely change `execution_providers` to CUDA and call the backend live.

## Current Host and Runtime Fit

Read-only inspection on 2026-08-22 found:

| Surface | Current value | Consequence |
| --- | --- | --- |
| GPU | NVIDIA GeForce RTX 5090, compute capability 12.0 | More than sufficient for sampled-frame YOLOX-S + OSNet x1.0 inference |
| Driver | 595.84 | Current CUDA-capable driver path is present; live wheel loading must still be verified |
| PyTorch | 2.9.0, CUDA 12.8, cuDNN 9.10.2 | Matches the CUDA 12.8 / cuDNN 9 ORT family |
| ONNX Runtime | GPU venv `onnxruntime-gpu==1.26.0`; main env CPU `onnxruntime==1.23.2` | 隔离GPU runtime已完成两份exact model的CUDA-only profiled smoke；既有CPU consumers保持不变 |
| NumPy | 2.2.6 | Already satisfies the evaluator's numerical runtime |

ONNX Runtime's official compatibility table says versions `1.21.x` through `1.26.x` use CUDA 12.8 and cuDNN 9, while PyPI packages from `1.27` switch their default build to CUDA 13.0. For this host, pinning `1.26.0` avoids introducing a CUDA-13 runtime alongside the existing CUDA-12.8 PyTorch stack.[ONNX Runtime CUDA compatibility table](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements)

The exact PyPI artifact for this Python 3.13 Linux x86-64 environment is:

- `onnxruntime_gpu-1.26.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl`
- size: `276,974,871` bytes
- PyPI SHA-256: `cfda2fad535595bfc3e570eb588092717711dcb2957656d814695e0c9ceb1508`

PyPI publishes that digest in its first-party release metadata; ONNX Runtime documents `pip install onnxruntime-gpu` as the official CUDA package and warns that CUDA/cuDNN major versions must match.[PyPI 1.26.0 release metadata](https://pypi.org/pypi/onnxruntime-gpu/1.26.0/json) · [official installation guide](https://onnxruntime.ai/docs/install/#install-onnx-runtime-gpu-cuda)

## Detector Assessment

### Selected: YOLOX-S

YOLOX is an anchor-free general object detector distributed under Apache-2.0, and its official repository provides ONNX export and ONNX Runtime deployment paths. In the official ONNX table, YOLOX-S uses 640×640 input, 9.0M parameters, 26.8 GFLOPs and reports 40.5 COCO mAP; `person` is COCO class index `0` in the upstream class tuple.[YOLOX ONNX Runtime guide](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/demo/ONNXRuntime/README.md) · [COCO class list](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/yolox/data/datasets/coco_classes.py) · [Apache-2.0 license](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/LICENSE)

Selected upstream asset identity:

| Field | Value |
| --- | --- |
| release tag | `0.1.1rc0` |
| release commit | `e1052df71842031413f6030723c3607b839c80ce` |
| filename | `yolox_s.onnx` |
| published size | `35,858,002` bytes |
| download | `https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.onnx` |
| upstream checksum | **not published**; GitHub release API returns `digest: null` |

The missing upstream checksum is not permission to omit identity. The installer must download to a temporary held file, verify the exact byte count, compute SHA-256 locally, inspect ONNX graph inputs/outputs, then seal the resulting hash and source URL in the profile. The release API is the primary source for filename and size.[YOLOX 0.1.1rc0 release API](https://api.github.com/repos/Megvii-BaseDetection/YOLOX/releases/tags/0.1.1rc0)

Official export defaults name the input `images` and output `output`, with opset 11. The official demo does **not** consume a normalized `[N,6]` tensor directly: it calls `demo_postprocess`, converts center-width-height boxes to xyxy, combines objectness and class scores, and runs multiclass NMS.[official export script](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/tools/export_onnx.py) · [official ONNX inference script](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/demo/ONNXRuntime/onnx_inference.py) · [official decode/NMS helpers](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/yolox/utils/demo_utils.py)

YOLOX preprocessing is also materially different from the current adapter: upstream resizes with aspect ratio preserved, pads the lower/right area with value `114`, transposes HWC to CHW, and retains float values in the `0..255` scale for current weights. It does not use the evaluator's anisotropic nearest resize and `/255` transform.[official preprocessing source](https://github.com/Megvii-BaseDetection/YOLOX/blob/419778480ab6ec0590e5d3831b3afb3b46ab2aa3/yolox/data/data_augment.py#L132-L147)

Required bounded integration:

- Add a sealed detector preprocess contract for RGB input converted to YOLOX's 640×640 aspect-preserving linear letterbox, including pad value and scale/offset metadata.
- Add a sealed `yolox-raw-coco/1` output decoder or build a reproducible derived ONNX wrapper that emits `normalized-xyxy-score-class/1`.
- Prefer deterministic NumPy decode/NMS in the existing cohesive adapter over adding YOLOX as a runtime dependency. If a derived ONNX wrapper is used, its converter source revision, upstream hash, opset, tensor names, thresholds and final derived SHA-256 must all be sealed.
- Filter class `0` only, but retain sub-threshold person detections as ambiguous exactly as the current evaluator requires.

### Rejected detector alternative: Ultralytics YOLO

Ultralytics has a polished official ONNX export path and models that would be computationally easy for a 5090. It is rejected for this bounded Product Runtime install because the official repository and models use AGPL-3.0 unless an Enterprise License is obtained; Ultralytics' own documentation says projects that cannot meet the AGPL source-disclosure requirements need that commercial license.[Ultralytics license](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) · [official licensing explanation](https://github.com/ultralytics/ultralytics/blob/main/docs/en/help/contributing.md#what-does-the-agpl-30-license-mean-if-i-use-ultralytics-yolo-in-my-own-project) · [official ONNX export documentation](https://github.com/ultralytics/ultralytics/blob/main/docs/en/modes/export.md)

This rejection is licensing/scope driven, not a claim that Ultralytics detection quality is inferior.

## ReID Assessment

### Selected: OSNet x1.0 MSMT17 combineall

Torchreid is the first-party OSNet implementation, under MIT. Its model zoo identifies OSNet x1.0 as a 2.2M-parameter, 0.98-GFLOP ReID model with 256×128 input; the author-maintained Hugging Face repository explicitly labels the model repository MIT and publishes the MSMT17-combineall checkpoint.[Torchreid model zoo](https://github.com/KaiyangZhou/deep-person-reid/blob/f8cd150fdf77e8d9e1ed143b7f308c2c609ded50/docs/MODEL_ZOO.md) · [Torchreid MIT license](https://github.com/KaiyangZhou/deep-person-reid/blob/f8cd150fdf77e8d9e1ed143b7f308c2c609ded50/LICENSE) · [author model card](https://huggingface.co/kaiyangzhou/osnet/tree/a5c5cc037c24235cda3b21085b93ad77c9616224)

Selected checkpoint identity:

| Field | Value |
| --- | --- |
| model repository revision | `a5c5cc037c24235cda3b21085b93ad77c9616224` |
| filename | `osnet_x1_0_msmt17_combineall_256x128_amsgrad_ep150_stp60_lr0.0015_b64_fb10_softmax_labelsmooth_flip_jitter.pth` |
| size | `17,273,805` bytes |
| LFS SHA-256 | `48df972f72887b95cf3b43b3a07c3a7d2398381aea0f9cae64a7ef11d512b727` |
| license declared by model repository | MIT |

The immutable LFS hash and size are available from the first-party model API with `blobs=true`.[author model API with blob metadata](https://huggingface.co/api/models/kaiyangzhou/osnet/revision/a5c5cc037c24235cda3b21085b93ad77c9616224?blobs=true)

Official inference preprocessing is RGB resize to 256×128, conversion to `[0,1]`, then ImageNet normalization with mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`. The official feature-extractor example reports a `(B, 512)` embedding. The current continuity backend already L2-normalizes finite embeddings after ONNX inference, so the derived model may output the raw 512-vector, but preprocessing must not be omitted.[official FeatureExtractor](https://github.com/KaiyangZhou/deep-person-reid/blob/f8cd150fdf77e8d9e1ed143b7f308c2c609ded50/torchreid/utils/feature_extractor.py#L585-L729)

Torchreid includes a first-party ONNX exporter with input name `images`, output name `output`, 256×128 BCHW shape and opset 12. The exporter does not embed the FeatureExtractor's image normalization—it exports the model against an already prepared tensor—so either the evaluator needs a sealed OSNet normalization contract or the derived ONNX graph must embed normalization.[official Torchreid exporter](https://github.com/KaiyangZhou/deep-person-reid/blob/f8cd150fdf77e8d9e1ed143b7f308c2c609ded50/tools/export.py#L670-L759)

Because the source checkpoint is a PyTorch pickle container, conversion should occur in a temporary no-network build environment only after SHA verification, using `torch.load(..., weights_only=True)` or an equivalently restricted state-dict loader. The final Production runtime should consume only the derived ONNX bytes and must not depend on Torchreid, PyTorch or Hugging Face at runtime. This is a security recommendation derived from the checkpoint format; the author repository's file scanner shows only expected tensor/OrderedDict pickle imports, but that is not a runtime trust boundary.[author file listing](https://huggingface.co/kaiyangzhou/osnet/tree/a5c5cc037c24235cda3b21085b93ad77c9616224)

### Rejected ReID alternative: FastReID SBS R50-IBN

FastReID is credible prior art: it is Apache-2.0, publishes Market1501 baselines and an official ONNX conversion/inference path with PyTorch-vs-ORT numerical comparison. Its SBS R50-IBN model reports 95.7% Rank-1 and 89.3% mAP on Market1501.[FastReID repository/license](https://github.com/JDAI-CV/fast-reid/tree/c9bc3ceb2f7a6438b62fb515ea3df6d1e999e95d) · [model zoo](https://github.com/JDAI-CV/fast-reid/blob/c9bc3ceb2f7a6438b62fb515ea3df6d1e999e95d/MODEL_ZOO.md) · [official ONNX deployment guide](https://github.com/JDAI-CV/fast-reid/blob/c9bc3ceb2f7a6438b62fb515ea3df6d1e999e95d/tools/deploy/README.md)

It is not selected because:

- the official `market_sbs_R50-ibn.pth` release asset is `301,378,459` bytes versus 17.3 MB for selected OSNet x1.0;
- GitHub's release metadata publishes no digest (`digest: null`), whereas the OSNet author repository publishes an exact LFS SHA-256;
- it is trained specifically on Market1501, while the selected checkpoint is trained on the larger MSMT17 domain; this does not prove superior generated-video accuracy, but is a more reasonable starting point for cross-scene continuity;
- its preprocessing still requires 256×128 resize and ImageNet normalization, so it does not remove the required adapter extension.[FastReID v0.1.1 release API](https://api.github.com/repos/JDAI-CV/fast-reid/releases/tags/v0.1.1) · [FastReID default preprocessing](https://github.com/JDAI-CV/fast-reid/blob/c9bc3ceb2f7a6438b62fb515ea3df6d1e999e95d/fastreid/config/defaults.py)

FastReID remains a reasonable future A/B challenger after a real local continuity calibration set exists; benchmark-table accuracy alone is not enough to replace the selected profile.

## Exact Tensor and Preprocessing Target

The installed/sealed derived profile should expose these contracts to `OnnxSubjectTrackerBackend`:

| Role | Input | Preprocess | Output consumed by evaluator |
| --- | --- | --- | --- |
| YOLOX-S detector | `images`, float32 `[1,3,640,640]` | source RGB frame → aspect-preserving bilinear resize → right/bottom pad `114` → model's expected channel/range convention; retain scale and padding for inverse mapping | deterministic decoded/NMS rows `[N,6]`: normalized source-frame `x1,y1,x2,y2,score,class_id`; class 0 is person |
| OSNet x1.0 ReID | `images`, float32 `[1,3,256,128]` | RGB crop → 256×128 resize → `/255` → channel-wise ImageNet mean/std normalization | `output`, float32 `[1,512]`; evaluator verifies finite/nonzero and L2-normalizes |

The profile hash must include, at minimum:

- both upstream byte hashes and both final derived ONNX hashes;
- upstream repository/revision/release URLs and license IDs;
- exact input/output names, shapes, dtypes, opsets and preprocessing formulae;
- YOLOX decode strides, objectness/class score multiplication, NMS threshold, detection threshold and person class mapping;
- OSNet normalization constants and output dimension;
- `onnxruntime-gpu` wheel version/hash, NumPy identity, CUDA provider options, device ID and absence of CPU fallback;
- tracker/ReID thresholds and sample geometry already owned by `ContinuityVisualProfile`.

Session construction must verify that `CUDAExecutionProvider` is present and is the requested provider. ONNX Runtime allows providers to be explicitly prioritized and otherwise uses CPU for unsupported nodes when CPU is supplied; Production should therefore request only CUDA and fail closed on an unsupported graph rather than silently changing execution identity.[ONNX Runtime execution-provider behavior](https://onnxruntime.ai/docs/execution-providers/) · [CUDA session example](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#configuration-options)

## Bounded Install and Activation Plan

1. Replace CPU `onnxruntime` with exact `onnxruntime-gpu==1.26.0`; do not retain both distributions because they provide the same `onnxruntime` Python module. Verify the installed distribution version and wheel RECORD, then require `CUDAExecutionProvider` in `get_available_providers()`.
2. Download the two selected upstream assets to a temporary directory, no symlink following. Verify OSNet against its published SHA-256/size; verify YOLOX size, compute its missing upstream SHA-256 locally, and record it before any conversion.
3. In a temporary no-network conversion environment pinned to YOLOX commit `419778480ab6ec0590e5d3831b3afb3b46ab2aa3` and Torchreid commit `f8cd150fdf77e8d9e1ed143b7f308c2c609ded50`, generate or inspect the ONNX graphs. No exporter package becomes a Product Runtime dependency.
4. Implement the minimum role-specific preprocess/decode seam described above. Preserve the existing canonical owner: evaluator emits raw measurements only; P6 remains the verdict owner.
5. Cross-check upstream PyTorch/reference outputs against derived ONNX outputs on fixed local image fixtures before deleting the conversion environment. The equivalence receipt must record tensors and tolerances, not only “session loaded”.
6. Install final ONNX bytes outside the Git repository in an explicit local model directory, read-only to normal runs. Store source/derived hashes and sizes in the sealed profile; do not auto-download on missing files.
7. Run a CUDA-only provider smoke and enable ORT profiling for the smoke to prove node placement. Activation must fail if any required node cannot be assigned to CUDA or if the available provider set/profile identity differs.
8. Calibrate detection/ReID/ambiguity thresholds against a bounded labeled continuity fixture set. Until calibration passes, real outputs remain experimental evidence and must not be used to claim Production quality acceptance.

## Capability Boundary After Installation

This backend can support the v1 priority measurements only when the selected subject is detectably visible:

- motion direction;
- signed entrance;
- signed exit;
- same-track unexpected re-entry.

It does **not** establish character identity in the semantic/story sense, camera axis, or framing intent. OSNet similarity is an appearance association signal, not proof of canonical character identity. Those checks must remain `NOT_EVALUATED` with human fallback unless a separately accepted visual/semantic backend is added. P6 continues to derive the final verdict; detector/ReID outputs never self-report PASS.

## Remaining Risks and Acceptance Blockers

- YOLOX's official release does not publish an artifact checksum; the first accepted installation must record the locally computed SHA-256 and exact byte size.
- Neither benchmark establishes accuracy on AI-generated characters, costume changes, occlusion, stylized scenes or hard cuts. A local labeled calibration set is required before threshold acceptance.
- ReID models can associate background/color cues and can fail when multiple similar people appear. The current margin/ambiguity path must stay fail-closed.
- Changing CPU ORT to GPU ORT and extending profile contracts are executable Product Runtime changes. They require focused regression tests, independent review and exact staged/commit-range Harness verification.
- No model asset should be committed into Git unless repository policy explicitly establishes a licensed binary-asset owner and size policy; this research recommends external local immutable storage.
- This selection does not authorize remote providers, credentials, model auto-download, media generation or quality acceptance.

## Sources Inspected

- AI-VIDEO `src/ai_video/production/continuity_evaluator.py` and `pyproject.toml`.
- YOLOX official repository, `0.1.1rc0`/`0.3.0` releases, license, export script, ONNX Runtime demo, preprocessing, postprocessing and COCO class list.
- Torchreid official repository, MIT license, model zoo, `FeatureExtractor`, transforms and ONNX exporter.
- Kaiyang Zhou's first-party OSNet Hugging Face model card, file listing and blob metadata API.
- FastReID official repository, license, model zoo, configuration defaults, release API and ONNX deployment guide.
- Ultralytics official repository license, licensing explanation and ONNX export documentation.
- ONNX Runtime official install, CUDA Execution Provider compatibility and execution-provider documentation.
- PyPI first-party `onnxruntime-gpu==1.26.0` release metadata.
