# Local H3 Readiness And Seed Live Regression Record

Date: 2026-08-21

## Purpose

本文记录current `video-planner/3`、`ShotReadinessGate`、provider-neutral generation requirement、Router、Local H3 compiler与deterministic seed resolution首次串联后的单次loopback technical live regression。

本记录不把结构性`READY`解释成generation authorization、quality acceptance或Final Acceptance，也不建立post-fetch `VideoQualityGate`。Candidate 1只作为外部regression oracle；本次没有生成Candidate 2/3。

## Implementation Preconditions

本次live regression在以下本地历史上执行：

- `404facdb254115b79d156e5d42f2136b5510d800`：实现pure、deterministic、provider-neutral `ShotReadinessGate`，并保持historical planner `/2` reopen与new-attempt `/3` STOP boundary。
- `a6d1c73bab77d36cee25c5cf4c37e69306c31e77`：Local H3 `resolve()`在compiled request未指定creative seed时，从exact `request_input_hash`机械派生non-negative 63-bit `effective_seed`；显式seed不变，其他Provider不受影响。
- experiment-bound repository commit：`45ac1d91a9e7e53eb8cb3c527a958ce897c2e6a7`。

前两项的fresh Harness receipts分别位于：

- `.agent/harness/runs/shot-readiness-gate-implementation-20260821-range-v1/receipt.json`
- `.agent/harness/runs/local-h3-effective-seed-20260821-v1/receipt.json`

## Exact Pre-Submit Lineage

Zero-submit preflight实际到达并验证：

- Planner outcome：`proposed`
- plan hash：`1ed16565be62fd524ffd1c6ec3158eb1d08b99ce6ef8d1503c4268b7e636db8e`
- readiness status：`ready`
- readiness result hash：`a54d93ef5d49c4057e7c40e072b407bf88382fe5f2b3c5e22556976012ea5c0e`
- verified requirement hash：`1be79a362308897514de712d8bcbd2233f5e791762bf7999f2ebcc35500473f0`
- Router outcome：`selected`
- selected capability：`minimax-h3-fl2va-local-v1`
- compiled request input hash：`691d4124b78b510d0af3d3e7ad9057b01c1996001a10a3a6794da6a3018c17d7`
- compiled seed：`None`
- resolved generation hash：`878d6257ac6fd321dc801ab98d8b197228725a6846de8eb38477e6dcded3e966`
- effective seed：`7574281774261031181`
- quality profile SHA-256：`a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`

Exact I2V first frame绑定activated Shot 1 terminal：

- asset ID：`video-alice-cafe-shot-1-local-h3:terminal-frame`
- SHA-256：`52596511bbea4314e39f0065559f6c01665303c4139a6c28326a8ee90b57e19b`

Preflight测得`object_info_calls=1`且`submit_calls=0`、`upload_calls=0`、`poll_calls=0`、`fetch_calls=0`。Creative preflight保持Alice黑色外套/红围巾、玻璃门、窗边木桌、绿色椅子、画面右侧暖色吊灯、left-to-right action与locked camera axis；H3 skill只约束I2V、可见动作、camera/audio与preflight boundary，`runtime_skill_calls=0`。

## Single Live Execution

本轮只执行一个Local H3 request，endpoint为loopback `http://127.0.0.1:8188`：

- provider request ID：`659848c4-e822-4d59-89a3-1d09d1915a8f`
- submit / poll / fetch：`1 / 1 / 1`
- first-frame upload：`1`
- remote calls：`0`
- selected Provider/model：`comfy-local-h3` / `minimax-h3-fl2va`
- requested output：`1344x672`、124 frames、24 fps、native audio

成功结果经existing lifecycle完成fetch、measured validation、candidate activation与strict reopen：

- run root：`runs/c2-alice-local-h3-t10-regression-20260821-001/`
- output：`runs/c2-alice-local-h3-t10-regression-20260821-001/output/alice-c2-local-h3-t10-regression-1.mp4`
- output SHA-256：`d599093f2eb52acfde3884fe5a392fb593c04564407c011e26ddab87e8eef067`
- output bytes：`1,445,320`
- activated Registry asset ID：`video-alice-c2-local-h3-t10-regression-1`
- Registry asset SHA-256：与output bytes相同
- resulting Manifest revision：34

对同一attempt重放`fetch_and_activate()`后，submit、poll、fetch、upload、object-info与remote effect delta全部为零。随后explicit recovery的Manifest revision为`34 -> 34`，没有自动激活、blind retry或第二次Provider submit。

Exact machine-readable evidence位于：

- `runs/c2-alice-local-h3-t10-regression-20260821-001/evidence/t10-live-report.json`

## Media Measurements

`ffprobe`与project-local `video-analysis`共同测得：

- container：MP4 / ISO BMFF
- video：H.264 High、`1344x672`、24 fps、124 frames、5.166667 seconds、yuv420p
- audio：AAC LC、32 kHz、stereo、约128 kbps、5.167 seconds
- total bitrate：约2238 kbps
- scene detection：1 continuous scene
- sampled-frame uniqueness：167 / 167
- heuristic structural issues：none

六帧contact sheet位于`runs/c2-alice-local-h3-t10-regression-20260821-001/evidence/frames/contact-sheet-6.jpg`，SHA-256 `869964300a8ad3b9febc568659619c143c6020d7e5793f5d457cf421c957663d`。帧序列可观察到Alice从椅旁/手扶椅背过渡到坐下并抬头，背景构图与主要场景物体保持稳定；该观察不是identity drift、motion naturalness、blur或subjective picture quality的正式判定。

用户随后查看exact output并明确回复“效果很好.go.”。本次T10 artifact的human verdict因此记录为`GO`；该verdict只接受本次artifact，不外推为universal H3 quality acceptance，也不替代P6 Review receipt或Final Acceptance。

Candidate 1 oracle保持不变：

- path：`runs/c2-alice-local-h3-quality-candidate-1-20260821/output/alice-c2-local-h3-quality-candidate-1.mp4`
- SHA-256：`2b02881d81b1226ab90e9791a472be7b6f02ef1b8584e5b2e1fe7d4050773de8`

新artifact的名字是`t10-regression-1`，不是Candidate 2或Candidate 3。

## Assessment And Remaining Boundary

本次证据证明：current Planner `/3` request、embedded requirement、verified projection、`ShotReadinessGate`、Router、compiler、Local H3 deterministic seed、loopback Provider、candidate activation、strict reopen、exact replay与explicit recovery能够在同一exact lineage闭环。

本次artifact的human `GO`已完成。以下仍未完成：

- 通用identity drift、motion naturalness、blur与subjective picture quality自动或blinded判定；
- P6 Review/Pilot receipt与Final Acceptance；
- cloud/paid Provider live proof；
- Local H3 C2 derived-keyframe Candidate 2/3或其它新媒体实验。

`ShotReadinessGate READY`仍只允许进入既有下游gates，不等于generation、activation或quality acceptance。媒体结果不能反向修改readiness owner，也不能触发新的post-fetch gate设计。

## Agent Guardrails

- 不得把本次single-scene、unique-frame或无heuristic issue外推为subjective quality PASS。
- 不得因为本次seed migration成功就为其他Provider添加相同default；该行为只属于Local H3 resolve boundary。
- 不得重用本次one-use live execution作为新submit授权。
- 不得把run artifact、fetch成功或Registry activation称为P6 Review或Final Acceptance。
- 后续若继续质量判断，只能把本次artifact交给existing P6 Review/Pilot或明确human review；不得让`ShotReadinessGate`承担感知质量。
