# Qingyan T8 Regeneration Post-Media Gate Record

Date: 2026-08-26

## Purpose

本文记录用户在 Ecommerce post-media Gate 代码更新后明确要求“重新生成”的青颜苗家女孩广告
checkpoint。目标是验证新顺序约束是否真实执行：每次只生成一条 Shot，固定 exact MP4 SHA，
显式调用 project-local `video-analysis`，完成 requirement-level `PASS` / `FAIL` /
`NOT_EVALUATED` adjudication，并且只有全部 required findings 为 `PASS` 才允许下一次 local submit。

本记录保存 development-side local media evidence。它不是 Production Manifest candidate
activation、P6、Final Acceptance、抖音审核或广告效果证明。

## Current Runtime Truth

本轮开始时 repository 已包含 Ecommerce candidate Gate 和 sequential coordinator code；相关 focused
tests 在当前 working state 重新运行得到 `33 passed in 0.54s`：

```text
tests/test_production_ecommerce_ad_coordinator.py
tests/test_production_ecommerce_shot_candidate_gate.py
tests/test_production_ecommerce_media_acceptance.py
```

当前 canonical Qingyan Ecommerce profile 包含与本用户原始 brief 不一致的 elder/dialogue requirement，
因此本轮没有将该 profile 的 PASS 冒充本广告 acceptance，也没有伪造 Production coordinator lifecycle。
执行使用 development-side local T8 portrait runner，并把新代码规定的逐 Shot post-media discipline 映射到
用户原始需求：年轻苗家女孩、包装 identity、手部/人物数量、动作、运动连续性、镜头意图和 portrait
canvas。每条 `.gate.json` 都绑定 exact output SHA；只在上一条 `overall_verdict=PASS` 后提交下一条。

Runtime identity：

- ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- T8 checkout commit `28cb160827c245b2d6a37539df30c1d7c5e7aecd`；
- route：T8 main chain + Turbo4 LoRA，`I2VA`、`768x1344`、56 frames、24 fps、4 steps、
  `dual_clock_euler` + `native_flow`；
- loopback endpoint only；没有 remote submit、fallback 或 retry。

这不等于 canonical Production T8 profile activation，也不改变既有 Provider/Manifest owner。

## Sequential Shot Evidence

所有输出位于：

```text
artifacts/qingyan-miao-ad-20260826-regenerated/runtime/t8_portrait_ad/
```

| Shot | SHA-256 | Local effects | Post-media result |
| --- | --- | --- | --- |
| `01_concern` | `9e3d64b6fa85e4eba47fcbae09c55e10d0b6897b663da65ff1708acf71619a0f` | submit 1; retry/fallback/remote 0/0/0 | `PASS`：克制腋侧衣物检查、单人、两手、连续放下动作 |
| `02_product_lift` | `6d7f12ed2d9f7ec4e4346893aac667c57fe578c1330ceab75423fe35aa08f499` | submit 1; retry/fallback/remote 0/0/0 | `PASS`：产品从腰部抬到胸前、双手稳定、黄色标签与白盖 coarse identity 稳定 |
| `03_preuse_hint` | `ef4e6ae65181eff913a1e3086510c7e70125f05815e6066523023745f69ad3e8` | submit 1; retry/fallback/remote 0/0/0 | `PASS`：封盖瓶轻微旋转/抬起，没有旧批次的额外手臂，也不伪装成可见喷雾 |
| `04_walk_forward` | `423c9c5483ed691e2611a225bc0a80572b6be2d1f2c87fc3f44fea1d72b4c8a0` | submit 1; retry/fallback/remote 0/0/0 | `PASS`：脚步、裙摆与人物位移连续；没有旧 Stock20 长镜头的 24-frame hard seam |
| `05_social_turn` | `92222b20f055b32ddad48a2da2da8dd63e0f5a049adeaa53c4d0d0ea05ebb7f7` | submit 1; retry/fallback/remote 0/0/0 | `PASS`：三人位置/身份稳定，主角转向朋友再回到近镜头视线 |

每条均显式调用 `video_probe`、`video_extract_frames`、`video_review`，再完成 video/audio full
decode、motion metric 和 measured-peak dense frame review。Generic `video_review` 对 `768x1344` 的
`low_resolution` 提示仅由 `width < 1024` 的 landscape-oriented heuristic 触发；portrait pixel count
高于其 `1024x576` baseline，因此没有把该提示当作内容失败，也没有据此改变 output tensor。

`04_walk_forward` 的背景存在轻微连续 forward-follow drift，但 dense frames 没有 abrupt pan、反向抽动
或周期性接缝。旧 `2026-08-25-qingyan-miao-t8-motion-smoothness.md` 对 Stock20 124-frame route 的
`REJECT` 仍然有效；本次较短 Turbo4 clips 不能外推证明长镜头问题已经修复。

## Product Truth And Composition

可读包装使用用户提供的 source packshot byte-for-byte：

```text
03d27bd46be48082b6d5ac737fbbb1f6cdca68b891d6c7d7c58eaa2c1c14f078
```

它对应用户文件 `微信图片_20260824194053_128_138.jpg` 和 composition source
`artifacts/qingyan-miao-ad-20260825/assets/product-packshot.jpg`，确保黄色盒装、黄色瓶身标签、白色瓶盖、
盒型与瓶型在可读产品镜头中不由生成模型改写。人物手持瓶只承担动作和 coarse identity，不作为标签文字真值。

新的 composition：

```text
artifacts/qingyan-miao-ad-20260826-regenerated/final/青颜_苗家女孩T8动态广告_重新生成_28s_9x16.mp4
```

- SHA-256 `2713634e60f590deb7203cc629812f61c7e9f6b1e68b13edbb4f60127bb0e36d`；
- `15,250,957` bytes；container duration `28.022s`；
- H.264 High、`1080x1920`、24 fps、672 frames、`yuv420p`；
- AAC 48 kHz stereo，audio duration `28.000s`；
- integrated loudness `-19.5 LUFS`，true peak `-1.6 dBFS`；
- video/audio full decode、SHA sidecar 和 black-frame scan 全部通过；
- project-local whole-video `video_analyze` 和 `video_review` 实际调用；后者返回 no issues，
  unique-frame ratio `0.996`。

成片结构为痛点动态镜头、产品抬起、使用暗示、source packshot、抽象卖点、户外行走、轻社交、
场景 recall、product hero 和 2 秒落版。copy 保持在用户提供范围内，没有使用“清爽一整天”、医疗治疗、
永久或量化效果 claim。

## Assessment

技术封装和 agent-side post-media Gate 为 `PASS`。与旧 current-facing candidate 相比，新成片用 5 条
逐 Shot 验收的真实时间运动镜头替换静帧/Ken Burns 依赖，并用新的 `03_preuse_hint` 消除已知额外手臂
failure mode。5 次 local submit 全部是新 output identity，且严格串行；没有自动 batch、blind retry、
fallback 或 remote effect。

该结论仍只属于 development media acceptance。没有把 agent `.gate.json` 当作
`ProductionStateCommitter` candidate、P6 receipt 或 Final Acceptance。

## Remaining Risks Or Next Work

- 尚缺用户或独立人类在目标手机上的一次 uninterrupted 1.0x 整片观看；frame sampling、dense strips 和
  motion metrics 不能替代这一 subjective verdict。
- 尚未在真实 Douyin UI overlay 下做 device/account-specific safe-area preview。
- BGM/SFX 的商业投放 license/provenance 仍未在 artifact 中闭合。
- 当前成片没有旁白；用户提供的口播方向以字幕/BGM/SFX表达。若买方要求 spoken copy，需要独立合法音源、
  P4 timeline 和完整听感验收。
- 使用动作为克制的封盖瓶旋转/抬起暗示，不是 literal nozzle/mist shot；它符合原 brief 允许的“使用动作暗示”，
  但若用户明确要求可见喷雾，需要新的 exact Shot 和同样的 post-media Gate。
- artifacts 当前为 local-only、repository-untracked media；本记录不声明 push、release、平台审核或投放表现。

## Agent Guardrails

- 不能把 5 条短 Turbo4 portrait clips 的 PASS 推断为 Stock20 124-frame route 已修复。
- 不能把 readable source packshot 的真值推断到 generated hand-held label 小字。
- 不能把 project-local MCP no-issues、technical decode 或 `.gate.json` 推断为 human 1.0x verdict、P6 或
  Final Acceptance。
- 不能恢复旧批次中有 extra hands 或 near-static motion 的 rejected clips。
- Development FFmpeg composition 不得描述成 canonical HyperFrames render 或 Production activation。
