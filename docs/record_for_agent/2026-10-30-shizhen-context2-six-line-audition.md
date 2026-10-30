---
record_kind: session_summary
topic_id: shizhen-context2-six-line-audition
learning_eligibility: ineligible
---

# Shizhen New Context Six-Line Audition

## Request And Scope

用户明确要求“你再生成开头配音我听听”。旧 L3 带标签请求仍 UNKNOWN，不重试、不 remint，
不改原包或释放 reservation。独立只读审查确认可为其他未提交的新上下文行建立有限且
不重叠的单元，当前只含 L1/L2/L4/L5/L6a/L6b，不能宣称完整七句已完成。

`outputs/shizhen-episode01/opening-voices-context2-20261030/` 中的
`performance-context-six-lines.json` 从原包派生并封存 predecessor SHA、L3 exclusion 与
旧 attempt 身份。新增 excluded_line_ids 入口校验，即使 rows 包含 L3 也不能选择。
旧包保持 BLOCKED，新包 READY 只表示可进入既有 canonical preflight，不授予权限。
同原 voice/model/script/default参数，仅把逐句表演上下文编译为 tags；未改台词或语速。

## Prefix Projection Contract

生成前修复已知 tags 对齐兼容缺口，原 Provider 两组 raw arrays 先经原严格结构/时间校验。
只在字符拼接逐字等于 sealed synthesis_text 时，按 exact 已编译前缀、exact 字符条目边界
投影，保留剩余绝对时间；原台词逐字校验仍在，普通对白括号不受影响。
receipt 新增 synthesis_alignment 保留两组 raw arrays、prefix、compiled SHA、原响应 SHA；
无 tags receipt 字节兼容。不是通用删标签、不是重定时，也未转换 History duration 数组。
独立冻结源码审查无问题；provider/batch141测试通过，最后响应SHA断言精准复测5项通过。
全量/related Harness 待用户试听与必要修复后执行，不把局部测试冒充完整验证。

## Actual Bounded Generation

六次 canonical CLI 提交全部 succeeded，无重试；每句各一个独立 root
`runs/shizhen-context2-{L1,L2,L4,L5,L6a,L6b}-20261030/`。
每次仍经 shared context reader、budget/egress/intent/one-use permit/committer；
原始实际 response 在 injected recording transport 只读接收后保留，未写 key/header secret。
原响应 SHA 与 mapped receipt 一致，原音频 SHA、正常 reader reopen、FFprobe、完整 decode 通过。
原 L3 Manifest 在新单元前后 bytes SHA 完全不变。

| Line | Voice | Duration |
| --- | --- | --- |
| L1 | Evan Zhao | 8.56 s |
| L2 | Evan Zhao | 9.76 s |
| L4 | Evan Zhao | 4.08 s |
| L5 | Stella Gu | 2.08 s |
| L6a | Stella Gu | 3.84 s |
| L6b | Evan Zhao | 2.40 s |

六句共30.72秒。operator 单位上限500microunits，预计预留总上限USD0.272，
每次/每root硬上限USD0.05，本单元最大USD0.30。旧L3 USD0.0335 reservation另保留；
没有预算重置、退款或旧配额复用。实际费用待确认。

## Playback And Open Quality Issues

浏览器已打开 `http://127.0.0.1:35867/index.html`，仅 loopback；窗口标题
“失帧开局 · 新表演上下文试听”已读回。页面与六个 WAV HTTP200。
各 WAV 为 canonical 原音频 bytes 一致副本，index.json 保留 source/hash/context/duration，
提供六句顺序试听，没有把旧L3混成新结果。媒体与原响应证据本地保留。

L1/L2 明显长于旧4/5秒窗口，D6两句6.24秒长于旧3.5秒窗口；已显式提示，
不能直接装片、压缩语速或以解码通过宣称听感自然。需试听是否读出英文提示及实际人物表演。
本会话没有原生音频理解证据，不假称已听出具体发音。未接回视频或签QA/Final Acceptance。
第一次本地 operator 运行在 import 前 ModuleNotFoundError，未创建unit或POST；改用repo入口
后运行。固定18772/18773端口被占用，保留其他服务并使用OS分配空闲loopback端口。

控制代码与canonical说明保留当前工作区改动，待试听/必要修复后正式验证与提交；
仅本记录独立归档，不夹带其他窗口的 voice-routing/audio-understanding/lockfile 工作。
`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
没有本轮用户听感结论，不把对齐/生成成功转成自然度规则。

## Optional Content Check Gap

为排查 L1 时长偏长是否来自额外英文提示，尝试 project-local video_transcribe，
使用已缓存 base 模型、auto-language、原 WAV；工具在执行转写前返回 no_video_stream，
没有得到 ASR 文字。未下载模型、未用新媒体包装补证、未追加生成或改称已听审。
对白额外内容与自然度仍需用户试听；本版不是完整/已验收开局。
