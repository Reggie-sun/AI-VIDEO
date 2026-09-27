---
record_kind: provider_comparison
topic_id: creative-goal-first-last-reference-retests
learning_eligibility: eligible
evidence_index_version: "1"
---

# Creative Goal First And Last Reference Retests

Date: 2026-09-28

## Purpose And Authority

承接 [first-frame-only tests](2026-09-27-creative-goal-real-api-local-tests.md)。用户明确要求“你先生成合适的参考图不要只有首帧,多一点再测试”，并已允许临时停止 VLLM 服务后跑本地。本轮另封存 materially new reference inputs 的最小任务，共 API 2、local 2 次真实提交；没有借新任务身份绕过本轮已耗尽的 ceiling。

证据根目录为 `runs/creative-goal-multi-reference-test-20260927-002/`，下文简称 `R/`；日期跨越香港时区午夜，目录保留原实验身份。忽略的媒体、实验脚本与 JSON 留在本机，不进入 Git。本轮未修改 Product code、Provider profile、冻结的验收目标或 activation owner。

广告仍须问题开场 → 老人推荐 → 使用 → 社会反应 → 原包装 hero / CTA 的完整因果链，本轮三个动作视频不能替代完整广告。剧情仍须退避拒接 → 姐姐收回放松等待 → 弟弟看到退让后主动接取 → 唯一钥匙最终归弟弟；不能用旁白或字幕补齐。

## Reference Inputs And Correction

使用 built-in `image_gen` 实际生成 6 张 PNG，保留 5 张可用生成参考：广告修正尾帧、泵头握持细节；剧情匹配尺寸首帧、等待态、交接尾帧。展示在 `R/reference-gallery.html`，bytes / role / hash 在 `R/references/manifest.json`，整理后的 authoring requirements 在 `R/image-authoring-prompts.json`；后者不是逐字工具调用 transcript。

实际 Provider 路径仍是原 H3 fl2va / Vidu `viduq3-pro` 的首尾帧模式：每次提交确实绑定两张 exact registered images，`verified-two-frame-bindings.json` 留存断言。泵头细节与剧情等待态用于 authoring 检查，未作为第三张带时间约束的 Provider input。没有换成 Ref2VA / R2V 或其他模型，不能称为已验证任意多参考输入。

Parent 初次静态检查漏检广告首尾的持瓶手：原首帧由画面右侧袖口手持瓶，初版尾帧变成画面左侧袖口手持瓶。两个真实广告 attempt 均使用这个初版尾帧，不能把换手全归因于模型。原 prompt 的 anatomical left/right 与图像也有冲突。`R/reference-image-gate-correction.json` 明确取代初版广告兼容性结论，保留旧证据。

| Input | SHA-256 | Actual use |
| --- | --- | --- |
| existing advertising first frame | `e3e305cab076ea151a6b3cff6ad13f9bbacb8776ccb63a029c2ef0a92384782d` | 两次广告提交 |
| rejected advertising end | `7111a4f6d7295915dd2ceccc6092c3834ec261c9298cef169038224fee54857b` | 两次广告提交；现已排除 |
| corrected advertising end | `066448edf98bddfe4f825e70e5e8449f544a56773130d6108f4febb503e6c1a4` | 已生成检查，0 次提交 |
| advertising pump detail | `88abafb0da32a644198b77ba7850e0644b6f1aee5881668c6d737390f8560384` | authoring only |
| drama first frame | `dd653730e01a7f8e4400384efbcfecb60a89e22bfd895d73c398743fc4b93e0c` | 两次剧情提交 |
| drama waiting state | `ab76dda17ad3095aa39668acf467113052a95fd945bad3a2398682691c6e985f` | authoring only |
| drama end frame | `43989d7fe967c130ea3b2ed5d2fae8a90d51b165014fcc635ee82303d07fbef2` | 两次剧情提交 |

剧情另生成匹配尾帧尺寸的首帧，不能把本轮视为“只添加一张尾帧”的 controlled A/B。原 packshot 的盖子遮住实际泵头，生成细节图不证明真实商品隐藏几何，也不能替代 authentic product/source admission。

## Runtime Outcomes

本地为 stock `minimax_h3_fl2va`，profile `a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`，20 steps、294 frames / 24fps；不是 T8 Turbo。API 为 `viduq3-pro`，实际回传 `headtailimg2video` metadata。通过标准 loader、planner、compiler、committer、service、intent/permit、fetch 和 review seam；没有手写 Manifest 或自动激活候选。

| Attempt | Outcome | Exact MP4 SHA-256 |
| --- | --- | --- |
| advertising-api-attempt-01 | FETCHED；action / object / motion FAIL，space PASS | `8d56ec4f5a33d049f24eef553f1d5d695ee51b03d9e6663bcae8fbad595bcbaf` |
| advertising-local-attempt-01 | FETCHED；action / space FAIL | `ca595380cc932e9b7532c5d6541a1ed2b73d285a8582bb3cdfbebcabf23fe408` |
| drama-api-attempt-01 | FETCHED；action FAIL，space PASS | `9a91633aa4a4b4be360a31e823e2741be6cf2e412deb96e15ce7aa4c70b91668` |
| drama-local-attempt-01 | known failed / CUDA OOM；无 MP4 | `NO_ARTIFACT:CUDA_OOM` |

MP4 位于 `R/<domain>/<route>/production-v5/state/video-generation/fetch/files/<SHA>.mp4`。API 广告为 7159095 bytes、12.042 s、289 frames、720×1280；local 广告为 2853879 bytes、12.250 s、294 frames、416×736；API 剧情为 3657228 bytes、12.042 s、289 frames、1280×720。三者为 24fps H.264 / stereo AAC，API 音轨 48000 Hz、local 32000 Hz；实际完整聆听与 human full-speed acceptance 仍为 `NOT_EVALUATED`。

API 广告 9 s 持瓶手在头侧突然出现瓶子，缺少可见连续交接；初版尾帧冲突是重要 confound。local 广告 9–10 s 可见换手，1–7 s 镜头放大导致头发/脸侧裁切，违背原 locked camera / complete head 要求。二者抽样可见长袖保留，局部改善不能转换成 identity 或 overall PASS。

API 剧情最终钥匙可见在弟弟掌中、姐姐空手，相比旧回到姐姐手中的结果有所改善；但弟弟 2–3 s 深弯腰，6 s 姐姐放低钥匙时弟弟已伸手，随后两次掌部接触，缺少完整可见的等待触发链。遮挡期间不能确认两次实际钥匙转移，object 为 `NOT_EVALUATED`。

local 剧情 1344×768 / 294 frames 在 `--novram` 下仍于 H3 quantization `torch.cat` 发生 `torch.OutOfMemoryError: Allocation on device`。Own journal 记录 allocated 20689 MiB、reserved 24448 MiB、prompt elapsed 00:13:56；provider request `9849a18e-304c-455c-b1af-a61cf291eec2`，canonical observation fingerprint `a336dd126bb28bd22d8b809393a47fb98d9b1f9375600fbb0eae600ba08878d7`。public runtime-failure review evidence hash 为 `217bc1fa9c4f3cb0047a2eb3b4bc60a2385602deed82f9549e59395762466a1e`，不伪造媒体质量结论。

## Gate And Browser Evidence

三个 MP4 均完成真实 project-local `video-analysis` MCP 逐秒采样、Parent 图像检查及 public `review_generation_attempt` / `ControlledPresentationVerifier` analyzer binding；两个 API 视频另以 0.5 s 加密检查动作和交接。`R/<domain>/<route>/diagnosis.json` 均为 `all_required_observed_pass=false`，未判定项保留 `NOT_EVALUATED`。

三个 `review-packet/result.json` 均为 full_contract FAIL，Production acceptance 未评估。采样、正式 analyzer proof 和 report 来自同一 exact artifact，不重复计为独立实验。三个 fetched attempt 的 durable status 仍为 running/VALIDATE，不把负向 review 自动等同于 canonical quality rejection 或 activation。

gstack browse 实测三个 report 在 390px / 1280px 无横向溢出、各 7 张图片加载；三个 muted video 均实际播放至 ended、readyState 4、无解码错误。`R/browser-evidence.json` 仅证明报告显示与浏览器解码，不证明 Parent/用户完整原速观看或真实音频验收。结果入口 `R/results.html`。

## Repair Boundary And Service Restoration

Parent 初始预算封存 local batch ceiling 2 / total ceiling 4，两次 initial submit 后 batch 已耗尽。当前 committer 没有可重开的 typed batch-review receipt；bare hash 不允许重置 durable count，total ceiling 4 不会自动开启下一批。`R/local-corrected-repair-boundary.json` 留存具体 source anchors 与 independent mapper 结论。修正广告尾帧和 screen-relative prompt 已准备，但 readiness 为 `BLOCKED_EXECUTION`，quality repair submit 0；本轮 runtime repair 同样没有新增提交。此阻挡源自 Parent 的预算编排，不是用户授权不足或模型质量结论。

没有扩大 ceiling、重置计数、用新 task ID 躲避此边界或降低 rubric。API 两次初始提交完成，paid repair ceiling 0。operator upper bound 仅为预配置 Budget Guard 上限，不代表官方价格或余额。

local queue 确认 running/pending 均为空后，supervisor 停止 own `ai-video-comfyui-d543579794064c1fbfd6e17e47253b99.service`，readback inactive；恢复 `jianji-qwen3-vl.service`，readback active/running、MainPID `2569280`、InvocationID `f4ab67bc26c542b2be41c122699adbc9`。`R/service-restoration.json` 留存；未额外验证模型服务健康。声明的 GPU wall budget 未有独立仪表计量，不能把 prompt elapsed 当作 GPU 总时长。

## Evidence Index

非 Q0 key 使用 exact request input hash，runtime/model/workflow 边界见上；experiment 中的 attempt namespace 与旧 run 不同。没有隔离单变量，arm_id 为 N/A。四个 rows 为四次提交，不能按图片数、报告数或 proof layer 数增加独立证据。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ad-api-analysis | request:a53adac1c7b8b6635979619ec14a9e6f15b96358878eb7200795bc2160671151 | creative-goal-first-last-20260927 | advertising-api-attempt-01 | N/A | 8d56ec4f5a33d049f24eef553f1d5d695ee51b03d9e6663bcae8fbad595bcbaf | ANALYZER | FAIL | QUALITY_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-multi-reference-test-20260927-002/advertising/api/diagnosis.json |
| ad-local-analysis | request:7b33d8310eb83c74af46a2d7dba85246425192a7f700ab3236e71512a309cc2f | creative-goal-first-last-20260927 | advertising-local-attempt-01 | N/A | ca595380cc932e9b7532c5d6541a1ed2b73d285a8582bb3cdfbebcabf23fe408 | ANALYZER | FAIL | QUALITY_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-multi-reference-test-20260927-002/advertising/local/diagnosis.json |
| drama-api-analysis | request:b14ada89be71cc85d8ae2831174129679aa3ea54b1e4065c23c22c4e720d72bc | creative-goal-first-last-20260927 | drama-api-attempt-01 | N/A | 9a91633aa4a4b4be360a31e823e2741be6cf2e412deb96e15ce7aa4c70b91668 | ANALYZER | FAIL | QUALITY_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-multi-reference-test-20260927-002/drama/api/diagnosis.json |
| drama-local-runtime | request:4f2ae9bfc69de5cd9487abda69bc17e39357498426408791d32120b528086eda | creative-goal-first-last-20260927 | drama-local-attempt-01 | N/A | NO_ARTIFACT:CUDA_OOM | PROVIDER_RECEIPT | FAIL | RUNTIME_FAILURE | NEW_ATTEMPT | NONE | runs/creative-goal-multi-reference-test-20260927-002/drama/local/runtime-failure.json |

## Learning Evaluation And Remaining Work

Mandatory managed Kimi read-only preflight invocation `b76a04d8-627e-48f6-bd94-2abfecf0008b`，qualified receipt PARSED，两个 requests 均 IDENTITY_VERIFIED，三项 expected source reads complete。Parent 使用其 pose/ownership/occlusion 建议，拒绝无源码支持的 state-machine schema 根因断言。Kimi、native mapper 与 Parent 均不产生 quality acceptance。

`distill-ai-video-learning` outcome 为 `no_candidate`：检索并重开原真实测试、历史剧情 repair 和既存 `h3-shot-local-visible-context` / `h3-i2v-first-frame-condition-renders-at-head` 后，没有能隔离参考数量或兼容性修复效果的新 comparison。广告初版参考冲突、剧情首帧重生成、尺寸/资源策略不同以及缺失音频 proof 限制因果归因；新证据也未实质重开上述 claims 的具体可见上下文/头部场景命题。保留已采纳和待确认 claims，不制造模型排名或成功率。

恢复合格出片仍需可执行且足够封存的同 scope repair 预算与真实修正参考重测；本地剧情需解决可复现 OOM；完整广告须补齐 canonical source admission、composition 和整链验收。未知项不能靠再加图片自动成为 PASS。

## Publication And Checkpoint

本轮 tracked changes 仅本记录及旧记录 continuation notice；unrelated `.codex/config.toml` 保留，无 push/release。忽略脚本 py_compile 通过，三段 MP4 hash 已从实际 bytes 重算匹配。记录/学习评估本身没有额外 Provider 或媒体调用；文档依 Harness policy 验证。未手动重建 RAG index，新记录的检索 freshness 未验证。

`capture_request_id=ai-video-record-26b95842b89fe19c` 已在原 implementation checkpoint ACKED `recorded / no_candidate`；本次评估为主动 stable record，不重复 acknowledge 同一 ID。
