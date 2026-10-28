---
name: h3-video
description: >
  MiniMax H3 local video authoring for AI-VIDEO: official 3-field prompts, T2V/I2V/FL2VA mode
  choice, validated local settings, local ComfyUI lifecycle via scripts/comfyui_supervisor.py,
  and the mandatory per-Shot post-media Gate. Use when a selected route is H3 / MiniMax H3.
  Triggers: H3, MiniMax H3, T2V, I2V, FL2VA.
---

# H3 Video Authoring

**Job:** make an agent produce **good H3 video**, not a random diffusion click. Quality comes from
**prompt craft + correct mode + validated settings**, not secret samplers.

## 0. AI-VIDEO paths

All commands run from the AI-VIDEO repository root.

| What | Path |
|---|---|
| H3 prompt compiler | `src/ai_video/production/_h3_prompt.py` |
| Local ComfyUI lifecycle | `scripts/comfyui_supervisor.py` |
| ComfyUI URL | `http://127.0.0.1:8188` (loopback default) |

Generation goes through the selected AI-VIDEO adapter and its gates. The upstream OpenVideo
product CLI (`python -m open_video`), its install scripts and its `backends/` / `docs/h3/` files
are not part of this repository; do not invoke or install them from this Skill.

---

## 1. Quality hierarchy (what actually moves the needle)

| Rank | Lever | Rule |
|---|---|---|
| **1** | **3-field prompt** | Official structure; concrete visible/audible detail; camera type+amplitude+speed; dialogue in `<d>[lang]…</d>` |
| **2** | **Mode** | T2V / I2V / FL2VA chosen correctly from inputs |
| **3** | **Resolution / steps** | **1344×768**, **20 steps**, `res_multistep` + `simple` |
| **4** | **Quant** | INT8 on 5090-class; lower VRAM → nf4/w4/int8+lowvram; the selected profile owns the exact quant |
| **5** | **Duration** | 5–10 s sweet spot (max 15 s / shot); multi-shot via cut times or `open-video` Director coverage |
| **6** | **Review** | Per-Shot post-media Gate (§3F) on the exact MP4 |

**Anti-patterns (low quality):** bare one-liner prompts; abstract mood words only; wrong mode; NVFP4 on 5090; forcing 2K locally; skipping validation.

---

## 2. Best-quality recipe (local max on RTX 5090)

```text
Diffusion:  fl2va_pruned_int8_convrot
Text enc:   qwen3vl_32b_int8_convrot
VAE:        video fp16 + audio fp32
ComfyUI:    --lowvram --use-sage-attention   # lowvram optional if VRAM ≥ ~22 GiB free policy
Canvas:     1344×768 (16:9), multiple of 32
Sampler:    res_multistep | Scheduler: simple | Steps: 20
Duration:   5–10 s (snaps to 17k+5 frames @ 24 fps)
Audio:      native 32 kHz stereo — describe in prompt fields
Prompt:     official 3-field only
```

Order-of-magnitude on a 32 GB class NVIDIA GPU: ~10–15 min / 10 s clip @ 1344×768, peak VRAM ~22–30 GB (measure on your machine).

---

## 3. Agent procedure (always this order)

### A. Host ready

ComfyUI down → start the explicit user-systemd service. This keeps the server out of a
transient Agent command lifecycle; it never auto-starts or auto-restarts:

```bash
python scripts/comfyui_supervisor.py status
python scripts/comfyui_supervisor.py start
# explicit controls only:
# python scripts/comfyui_supervisor.py logs --lines 100
# python scripts/comfyui_supervisor.py stop
```

Set `COMFYUI_ROOT` to the local ComfyUI checkout when it is not the supervisor default. If ComfyUI
uses a dedicated interpreter outside `$COMFYUI_ROOT/.venv`, set
`COMFYUI_PYTHON=/absolute/path/to/python` before `start`. The supervisor binds only
`127.0.0.1`, refuses an occupied port, and does not read or mutate long-video job state.

### B. Mode

| Inputs | Mode |
|---|---|
| Text only | **T2V** |
| + 1 image | **I2V** (+ instruction line) |
| + first & last image | **FL2VA** (+ alignment line) |
| Multi-ref identity/style | R2V (needs ref2va weights — not default) |

The selected adapter/profile owns the exact mode token and support; do not invent one.

### C. Craft the 3-field prompt (quality lever #1)

```text
[<instruction line — I2V / FL2VA only, then blank line>]

integrated_multimodal_description: [Shot 1] <style first: Live-action, cinematic, …>,
  <subjects, clothing, lighting, space>. <camera: type + amplitude + speed + action>.
  [Shot 2] At 00:0X.XXX, the camera cuts to <new info only>.
overall_soundscape: <1–4 sentences: ambient / physical / non-verbal — no duplicate dialogue>
non_diegetic_music: <1–3 sentences: instruments, tempo, rhythm — no vague mood words>
```

**Hard rules (from official guide):**

- Every claim must be **visible or audible** (no pure emotion adjectives).
- **Style first** in Shot 1.
- Camera prose: e.g. `pushes in with small amplitude at slow speed`.
- Dialogue: speaker IDs + `<d>[English] verbatim words</d>`.
- Later shots: **strictly increasing** cut times inside duration.
- The in-repo compiler `src/ai_video/production/_h3_prompt.py` is the executable grammar owner.

**Expand** casual NL into 3-field; never ship a bare phrase as the only prompt for “high quality.”

#### Shot-Local Visible Context (AI-VIDEO Advisory)

对已选 `minimax-h3-t8-t2va-quality-v1` / `text_to_video` 的 authoring，参考
[H3 Shot-Local Visible Context](../../../docs/record_for_agent/learning/h3-shot-local-visible-context.md)
的灯塔案例，增加以下有限检查：

1. 从 approved Shot 区分当前可见/画外、已发生/未发生的状态；不要把未来亮灯状态提前写入暗灯镜头。
2. 对照 `palette`、`lighting`、`materials`、`camera subject` 与 `endpoints` 是否与当前画面一致；
   sea-only 镜头不应同时要求 camera 保持灯塔主体入画。保留有意义的画外光源和 narrative location，
   不做物件名称的 blanket deletion。实质冲突回到 authoring owner 修正，再走原 compiler。
3. 回查 actual compiled prompt 是否仍有相反指导；不得直接 patch resolved request，也不得将静态
   一致性检查视为媒体 PASS。修正后仍逐项执行原有 post-media Gate。

这是当前 T2VA lane 的 advisory 案例，不是 deterministic validator 或自动修复规则。
补拍同时改变 seed，不能据此保证因果改善、成功率或其他场景/模式的效果；不按时长或有无 prompt
强制 `single_take` / `multi_shot`，不改变 Director、Provider selection、预算/permit 或 Gate ownership。

### D. Validate before GPU spend

Review the exact compiled request/preview from the selected adapter and fix validator issues
before any GPU spend.

### E. Generate

Generate through the selected AI-VIDEO adapter with its exact identity/profile, intent, one-use
permit and committer, as required by the Local ComfyUI Authorization Exemption in `AGENTS.md`.

### F. Mandatory per-Shot post-media Gate

For AI-VIDEO multi-Shot work, generation is an atomic loop, never an unattended batch:

1. Generate exactly one Shot with no internal judge retries, and fix the exact output path +
   SHA-256. Internal retries must not create un-Gated extra takes.
2. Immediately call the project-local `video-analysis` MCP on that exact MP4. At minimum use
   media probe plus sampled visual review; add audio, scene, lip-sync, or continuity analysis when
   the Shot requires it.
3. Map the raw MCP evidence to the sealed Shot intent and emit requirement-level
   `PASS` / `FAIL` / `NOT_EVALUATED` findings. From Shot 2 onward, include the previous accepted
   end-state evidence when continuity applies.
4. Submit the next Shot only when every required finding for the current Shot is `PASS`.
   `FAIL`, `NOT_EVALUATED`, missing/stale evidence, identity drift, or unavailable MCP always
   blocks Shot N+1 and closes the current attempt.
5. For a local loopback, unmetered, outcome-known task that remains inside the accepted scope,
   do not treat that attempt stop as the end of the user's deliverable. Use
   `LOCAL_BOUNDED_REPAIR_LOOP`: preserve the failed Gate, seal finite task-scoped attempt-count,
   elapsed-time, and GPU budgets in run evidence, isolate one evidence-backed repair
   variable, create a new exact request/intent/one-use permit for the same Shot, and run the full
   Gate again. When only the MCP/analyzer/evidence failed, use `EVIDENCE_REPAIR_FIRST` and repair
   the evidence path without regenerating otherwise unfailed media.

The background analysis hook, command exit code, file existence, any judge score, and the
env-unset auto-PASS stub do not satisfy this Gate. Do not collapse identity, action, product/object,
camera, prompt adherence, audio, and continuity into one score. Follow the canonical procedure in
`.agent/context/control-plane-playbook.md` `Per-Shot Post-Media Gate`; MCP evidence remains advisory
raw evidence and cannot write Manifest, P6, activation, or Final Acceptance.

After a stopped Shot, diagnose a targeted repair. Under the local exemption, the agent orchestration
must continue the same Shot through `LOCAL_BOUNDED_REPAIR_LOOP` while the accepted goal remains
unmet and a new evidence-backed variable exists; this needs no extra confirmation. Never repeat the
same request, blind retry, reuse/remint the old permit, fallback, weaken requirements, change
Provider/scope, or continue to Shot N+1. Stop the whole task only for unknown outcome, exhausted
sealed repair budget or causal repair hypotheses, repeated unisolatable failure, persistent evidence unavailability, scope
change, or another real blocker. Remote/paid attempts retain their authorization gates.
For a single-Shot delivery, the same Gate runs before delivery. Shipping/public claims may still
require the separate human or Production acceptance gates.

---

## 4. Prompt micro-templates (copy & fill)

**T2V cinematic single beat**

```text
integrated_multimodal_description: [Shot 1] Live-action, cinematic, <wide/medium> shot frames <subject + clothing + age/gender if speaking>. <lighting + location>. The camera <push/pull/pan/track/arc> with <small|medium|large> amplitude at <slow|medium|fast> speed as <concrete action>.
overall_soundscape: <ambient>… <physical>…
non_diegetic_music: <instruments + tempo + dynamics>…
```

**T2V multi-shot (cut adds new info)**

```text
integrated_multimodal_description: [Shot 1] … [Shot 2] At 00:05.000, the camera cuts to …
overall_soundscape: …
non_diegetic_music: …
```

**I2V**

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, starting from Picture 1, …
overall_soundscape: …
non_diegetic_music: …
```

---

## 5. Hard constraints

| Constraint | Limit |
|---|---|
| Duration / shot | **4–15 s** |
| Frame grid | **17k+5 @ 24 fps** |
| Local res | Short edge ≤ **768**; multiple of **32** |
| 2K | **API only** — cannot upscale local 768p with open weights |
| NVFP4 on 5090 | **Forbidden** (ComfyUI #14157) |
| License | MiniMax weight terms (region/commercial) + code Apache-2.0 |

Multi-Shot direction and coverage belong to `open-video`; this Skill only authors the selected H3 Shot.
