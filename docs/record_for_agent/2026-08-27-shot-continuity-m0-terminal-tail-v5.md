# Shot Continuity M0 Terminal Tail V5 Record

Date: 2026-08-27

> Supersession notice (2026-08-27): v5的human `FAIL`与exact measurements仍是有效历史证据；其当时关于
> 下一步root-cause isolation的current-facing结论已由v6 layout-repair experiment细化。ComfyUI packed-layout
> keyframe origin修复后，hard snap从frame `84` / `3.500s`推迟到frame `101` / `4.208s`，但没有消除seam或
> near-static tail；v6自动媒体门与human原速三项 verdict均为`FAIL`，Manifest revision `75`已canonical关闭
> v6。Current exact profile已停止继续迭代，但该结论不泛化为RTX 5090或全部local H3能力失败。Current evidence见
> `docs/record_for_agent/2026-08-27-shot-continuity-m0-layout-repair-v6.md`。

## Purpose

本文记录M0 `quality-v1`在full-source reference视频被human reviewer判定为人物移动明显偏慢后，使用exact
2秒terminal motion tail、固定historical materialized seed并执行一次local one-submit v5 experiment的current
truth。它区分runtime成功、技术媒体检查与最终human rejection；不会把`video-analysis`无冻结或Provider成功升级为
P6、winner、activation或Final Acceptance。

Production root：

`runs/shot-continuity-rainy-station-p0-20260826-v9/production`

## Superseded Runtime Boundary

`docs/record_for_agent/2026-08-26-shot-continuity-m0-quality-v1-live-attempt.md`记录的v1-v3 OOM仍是各自exact
attempt的历史事实，但“current M0 runtime execution = capacity FAIL”已被后续证据取代。Isolated `--novram`
能够在本机完成Stock20/no-LoRA、20-step T8 route；它的代价是约18分钟的模型装载、CPU offload、sampling与
decode wall-clock，而不是改变steps、geometry、seed或attention contract。

先于本轮的v4 full-reference attempt
`rainy-station-m0-quality-v1-mcp-released-novram-20260827-v4`已经生成并fetch exact MP4：

`state/video-generation/fetch/files/d9ba42cea20a4cd9b53f240dcf1f923425f1cd7b3579f6f572b02c8f4483fcc7.mp4`

它为`1344x768`、24fps、124 frames、5.167s。Project `video-analysis`确认没有technical freeze，但human reviewer
判定人物移动明显偏慢；canonical attempt随后以`video_provider_failed`关闭，error明确记录human rejection，
没有candidate activation。该v4 verdict只针对full-source-reference artifact，不自动决定v5。

## Terminal Tail And Fixed-Seed Closure

Current M0 reference改为derived terminal tail asset：

- asset ID：`video-shot-rainy-station-3-terminal-motion-tail-m0-quality-v5`；
- asset SHA-256：`4ed0a8121166ba5a5e056ce25bcb8d142117a47371c8eaf65393901438191729`；
- receipt：`b4028b933b43ee7cba2cca818bdcc28a10ed3356244a7ac4b6c54cf4c31663b7`；
- exact source frames：`76..123` inclusive，48 frames，24fps，2000ms；
- decoded sequence seal：`9785685b3ce11990a96c190de53dd3b7ebe26f64299eb8989997107f52925453`；
- terminal decoded-frame seal：`7aee1519f5bd585278acceba016b34f4cba291b929b2d0510308258943cec095`。

Terminal PNG asset为`video-shot-rainy-station-3-source-v1:terminal-frame`，SHA-256
`bb9ec5050ebf450f5b8057eee8f3af09c928a4c919dfebc69efde73cabd95328`，creation receipt
`5b5037188d580537277fd74837ced1d90dd99e0c47180cef9f059f23f4d9a510`。

Registry更新使content-addressed seed closure变化。用户明确选择保留旧seed，因此新增
`historical-materialized-m0-fixed-seed-v1` fail-closed contract。Historical source必须精确为receipt
`bd69e6f9edcae76d1acb1996215192bf8c0a459f4a7c3b88a7ca86342681497d`的canonical `candidates[0]` M0：

- historical materialized stack：`c37f6a594e473a5d73ed6a19a4d3e9892420880a99ed71149e8e525b4c519b4d`；
- historical profile materialization：`acef730cd2cab44fe5a0fb50693798eb4958844b2639d1fa9ca1b99b7315bb4a`；
- sealed seed：`5696170359736854830`。

M1即使hash匹配也不能冒充M0；seed derivation与mode/shape validation留在exact sealed compiler bytes中，任何
语义bytes drift都会改变compiler与execution-stack identity。除current P0/Registry closure、seed mode与三个
historical lineage字段外，新profile与historical materialized profile逐字段exact-equal。

Relevant commits：

- `6eb5379 fix: materialize exact M0 terminal motion tail`；
- `448ba4a fix: isolate terminal video frame hashing`；
- `c805639 fix: preserve M0 seed across tail reseal`；
- `57eb5ea chore: seal M0 terminal-tail profile`。

Fresh Harness receipts：

- `.agent/harness/runs/m0-terminal-tail-audio-map-v2/receipt.json`；
- `.agent/harness/runs/m0-fixed-seed-reseal-v3/receipt.json`；
- `.agent/harness/runs/m0-terminal-tail-v5-profile-v1/receipt.json`。

后两份receipt的`verify-receipt`全部关键字段为true。Fixed-seed run通过Harness `185 passed`与Shot Continuity
P0 `334 passed`；profile run通过workflow `9 passed`与Shot Continuity P0 `334 passed`；Architecture Gate均为
`PASS`且0 findings。Independent `reviewer_xhigh`对fixed-seed implementation、compiler reseal和new profile均为
`accept`，无blocking或non-blocking concern。

## Production Reseal

Manifest revision `55`时，active Registry为
`e212390f7852c3a995c4e582c33a950e5c12abd2421a565b651254bd359afc3d`且active P0 pointer因tail activation已被
precise invalidation清除。Canonical reprepare从historical unmaterialized receipt
`b1790306edc9417d054c91c865d70965f790be6d4c4a5400f6a610f332e19468`重建current closure，结果：

- reprepare receipt：`f67ba6309c6dea54803f70c4d213d9053160068b07119a25d9c11dc3e2f6d6f5`；
- Manifest revision：`56`；
- validation set：`87af94a686e85f1aa6d02703ba0f6e79346960e9c15f19adbd27e3f0793849be`。

新profile document SHA-256为
`5bf373e4cb28bba6eb03cadf5c5959c894f5f98d03a6485a516a9985ffc95b48`，materialized profile hash为
`f8ee00045696bf41c2276f56f0a806659b3ae696b0dc74813eebf6e3e75ea63a`。M0-only materialization产生：

- P0 receipt：`fb58c6f27bd66129440965d63e0e200c26917ad52772548b66811591d691e952`；
- M0 stack：`8d6691d5b8419e485f651db522f167bcdf0b9f6c21c69d1691ee7d4905b65aba`；
- compiler：`978d79cfa9d2e890f77a44dc20da3a66daed0197bcb10a5bc20983a1157bdb3f`；
- workflow：`963bd91ad81ca102053deb08b29a7aa8fb6849a6256a78ccbfbc6138d7a855d2`；
- Manifest revision：`57`。

M1保持`unmaterialized`，Hybrid artifact仍为`absent/none`；materialization报告Provider effects、generated video、
winner、activation、P6与Final Acceptance均为false。

Exact human feasibility approval
`1ed8e7c207db3b6a5690a7ec99790b5a6db132236a6563be884df370e3d50cf9`绑定one local `quality-v1` submit、
no retry/fallback、上述stack/profile/identity/endpoint/tail与5167ms output；它只关闭pre-submit geometry feasibility，
不是generated-video quality verdict。

## V5 Live Attempt

唯一attempt：

- attempt：`rainy-station-m0-quality-v1-terminal-tail-20260827-v5`；
- generation：`rainy-station-shot-4-m0-quality-v1-terminal-tail-20260827-v5`；
- output asset ID：`video-shot-rainy-station-4-m0-quality-v1-terminal-tail-v5`；
- request hash：`6f4af2798a8acf145903a7ab3981a32cc8e1763c1e088cdaafb2825fcd727acd`；
- submit intent：`331600286c16b3c2a3f073b37d5106870313e86676f9caa9a68fe2ac98c669a7`；
- submit result：`9e775513a72856e99a90c7ece18865340b62f149bd19b44b4e54abfe69fefb17`；
- Provider request ID：`3ead64d1-c7ac-41a7-9bb6-ec0893d45cb0`；
- succeeded observation：`6fdcf1289e01ad9335747e8335d3bbe39d9e422139f3032d1b8f44a8016e86fe`；
- fetch receipt：`909ebbeaf84b6cc5b904d693fd92a65bad535ae9a5af3907070d5bb81a23e7a9`。

Real caller full preflight确认attempt absent、`next_action=submit`、sealed seed与四个exact inputs；permit-inner guard后
只提交一次。ComfyUI为`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`，T8临时切到sealed
`977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`，VideoHelperSuite为
`4ee72c065db22c9d96c2427954dc69e7b908444b`。Supervisor exact memory route为
`--novram --use-sage-attention`。Submitted graph仍是Stock20/no-LoRA、20 steps、`dual_clock_euler`、
`native_flow`与seed `5696170359736854830`；reference video只有tail SHA
`4ed0a8121166ba5a5e056ce25bcb8d142117a47371c8eaf65393901438191729`。

Provider成功后只执行canonical poll与fetch；submit/poll/fetch=`1/1/1`，retry/fallback/remote/paid=`0/0/0/0`。
ComfyUI随后停止，port `8188`关闭；T8恢复到session前commit
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`且clean。

## Exact Media Evidence

Fetched MP4：

`runs/shot-continuity-rainy-station-p0-20260826-v9/production/state/video-generation/fetch/files/22bdcad0ee2da2614b6781bd8d46ffd478174259557ca96be66614dd61ec49e6.mp4`

Measured facts：

- SHA-256：`22bdcad0ee2da2614b6781bd8d46ffd478174259557ca96be66614dd61ec49e6`；
- size：`2325322` bytes；
- video：H.264 High、`1344x768`、24fps、124 frames、5.167s、`yuv420p`；
- audio：AAC、32kHz、stereo；
- full video decode与full audio decode：PASS。

Project `video-analysis` MCP得到：1 scene、11 extracted keyframes、166 sampled frames、166 unique frames、
unique ratio `1.0`、`issues=[]`。这些证据只排除literal repeated-frame freeze或decode failure，不能证明自然速度，
也不能覆盖human观察到的后段近静态内容与visible seam。

一个额外的advisory OpenCV Farneback对比使用同一downsample与123对adjacent frames。相对于v4 full-reference，v5：

- mean flow：`0.1952 -> 0.1775 px/frame`；
- mean p90 flow：`0.4647 -> 0.4103 px/frame`；
- mean luma absolute difference：`1.9543 -> 1.4807`。

该诊断会混合subject、camera、rain与background motion，不是P6 metric；它只说明现有automated evidence不支持
“2秒tail使人物整体运动更快”的假设。抽帧检查同样显示后半段较明显变化主要来自composition/camera push，而不是已被
证明的更快步态。

Human rejection后，以`cv2.INTER_AREA`把BGR frame缩放到`336x192`、转grayscale，再用Farneback参数
`pyr_scale=0.5, levels=3, winsize=15, iterations=3, poly_n=5, poly_sigma=1.2, flags=0`对v5做分段诊断：

- `0.000-2.000s`：48 pairs，mean flow `0.150535`、mean p90 flow `0.405257`、mean luma absdiff `1.209407`；
- `2.000-3.500s`：36 pairs，mean flow `0.364727`、mean p90 flow `0.765966`、mean luma absdiff `2.336214`；
- `3.500-5.167s`：39 pairs，mean flow `0.012688`、mean p90 flow `0.027723`、mean luma absdiff `0.229524`。

唯一异常大转场为frame `83 -> 84`、timestamp `3.500s`：flow `7.440274`、p90 flow `13.151134`、luma
absdiff `37.967711`。随后尾段mean flow相对前2秒下降约`91.6%`；每0.5秒窗口从`3.5s`起稳定在
`0.012298..0.014887`，而非正常步态或camera motion。这些数值是对human verdict的advisory corroboration，
不替代P6或human owner。

## Human Verdict And Canonical Closure

Human reviewer对exact v5 MP4的原速结论为：`速度不通过,并且后面变成静图,seam明显`。因此：

- motion speed：`FAIL`；
- latter-segment dynamic continuity：`FAIL`；
- seam continuity：`FAIL`。

`ProductionStateCommitter.record_video_provider_failure()`已将attempt以`video_provider_failed`原子关闭；Manifest
revision `64 -> 65`，attempt为`failed/validate`、`next_action=stop`，error明确绑定上述human rejection。
`local_fetch_receipt`仍为`909ebbeaf84b6cc5b904d693fd92a65bad535ae9a5af3907070d5bb81a23e7a9`，artifact SHA-256
仍为`22bdcad0ee2da2614b6781bd8d46ffd478174259557ca96be66614dd61ec49e6`且size `2325322` bytes；candidate asset
IDs为空，没有activation、retry、fallback或M1 effect。

## Current Assessment

- fixed-seed / exact-tail engineering closure：`PASS`；
- local one-submit / poll / fetch lifecycle：`PASS`；
- MP4 hash、probe与full decode：`PASS`；
- literal repeated-frame freeze / decode evidence：`PASS`，但不覆盖perceptual near-static tail；
- “人物移动速度自然且不再像0.5倍速”：human `FAIL`；
- latter-segment dynamic continuity：human `FAIL`；
- seam continuity：human `FAIL`，advisory metric定位在`3.500s`；
- M0 P6 requirement verdict：未签发；
- winner / capability activation / M1 / Final Acceptance：均未发生；
- publication：local commits only，未push、未release。

Manifest当前为schema `2.14` revision `65`。V5 attempt已是`failed/validate`、`next_action=stop`，保存exact local
fetch receipt与MP4；candidate asset IDs为空。不得把`issues=[]`升级成quality PASS，也不得自动激活或进入M1。

## Remaining Work

V5已canonical关闭为human quality FAIL。Exact v5证明缩短到2秒tail没有改善速度，并与`3.500s` discontinuity及
余下约1.67秒近静态尾段同时出现；reference conditioning、endpoint conditioning与prompt三者的相对因果尚未隔离。
因此现有证据只拒绝“只缩短reference tail即可修复慢动作”的hypothesis，不应被升级为通用model contract或单一
root-cause claim。

下一步必须先重新设计temporal handoff/endpoint contract或停止M0 experiment；不得blind retry、换seed、继续缩短tail、
切fast policy或自动进入M1。任何新generation、M1 preparation/submit或不同policy都需要新的明确授权。此前已通过的
30秒成片与本M0 single-edge qualification是不同acceptance scope；本次FAIL不撤销其既有人眼通过结论。

本记录本次更新没有新的Provider/media call；它只沉淀human verdict、canonical closure与已有exact MP4的分段分析。
Agent memory/RAG index未刷新，后续检索在独立授权的index owner执行前可能仍缺少本记录。
