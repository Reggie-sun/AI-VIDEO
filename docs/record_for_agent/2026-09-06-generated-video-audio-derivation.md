---
record_kind: architecture_implementation
topic_id: generated-video-native-audio-derivation
learning_eligibility: ineligible
---

# Generated Video Audio Derivation

Date: 2026-09-06

## Current Correction — S01 Hand Motion Rejected

### Follow-up — Endpoint Hand Repair Candidates

用户随后明确要求“修复”。直接查看旧末帧`059bb2b261883190168057b35baafc90011866acba9fb64b1c9c186122861330`发现：抬起左臂的手背朝镜头，拇指却位于画面左侧，存在左右手形态不一致；这是动作突变的输入风险，尚未通过对照视频证明因果。使用image_gen进行了三次局部修图：前两次仍保留错误拇指侧，拒绝；第三次改为侧向微曲、手指透视重叠的试探手势，仅为待审阅候选，不宣称解剖或视频Gate通过。

三张原样输出保存在`runs/jieshi-s01-hand-repair-20260906-001/`，`candidates.json`记录exact hash与bytes。第三张`endpoint-repair-03.png` SHA256 `d9a21860e91cadc7cf4cfe0ce74a44b57c2aa6d600b8c8cc06dc17e4fb4cd1da`，2,051,993 bytes，未注册、未获得human approval。未发起新的Vidu/Seedance视频调用，未生成修复MP4，不推进S02。旧图approval不能冒充新图approval。

本次实际发生image_gen媒体调用，记录阶段不再调用媒体或网络。学习评估`no_candidate`：同一输入的迭代且第三张未验收，不足以提出已验证的跨实验修复规律。保留既有七个staged runs文件；不push。

用户观看本地preview后明确指出“手的问题很大”。该反馈取代下文“第7版视觉可以保留”的暂定判断，不得将此前“没问题”解释为全面验收。MCP补看每0.4秒的1080px帧后发现：1.6秒掌心朝镜头，2秒变手背朝镜头，轮廓变化未清晰呈现自然旋转；先前稀疏抽帧错过了主要动作问题。preview当前FAIL，不推进S02。`runs/jieshi-s02-preparation-20260906-001/`只有原07第71帧的clean continuity reference，未批准/注册为S02首帧，现不得作为accepted source。

字幕澄清与用户具体手部问题正在等待回复；本轮未新提交Provider或生成修复视频。record/learning评估no_candidate：单次同源诊断修正，不扩张为已证实的普遍模型结论。

## Follow-up — Local Editorial Preview

用户后来明确要求“别管扣费的”。已对下载的07素材完成一次本地ffmpeg剪辑预览：保留前3秒真实画面，原生音轨从0.7秒开始，添加既定叙事字幕。输出`runs/jieshi-s01-local-edit-20260906-001/s01-preview.mp4`，SHA256 `5e713b14f1ac886537a1b4076cab3a473308b58f808c2e32073a668b9a4c6182`。这是独立editorial preview，不是canonical HyperFrames composition；没有通过改名、伪造成本或登记改变Production状态。下文“未合成”只描述先前checkpoint；现在已有本地预览，canonical composition仍未完成。

Exact输出已调用project-local video_analyze和word_timestamps转写：1080×1920、72帧/24fps，container3.022秒；ASR段落结束2.64秒，字幕可见。完整逐镜判定在run的`REVIEW.md`，总体NOT_EVALUATED：人耳起音/混音、全程倒影计数、胸牌及约2cm间隙未完全确认。没有推进S02。record自动learning评估仍no_candidate：这是同源单次剪辑，不能宣称普遍的修复成功规律。

## Scope And Current Truth

用户明确批准有界原生音轨派生入口，目标是后续组合《界蚀》S01的attempt07视觉与attempt08广播。本轮完成能力实现，不重新编剧、不增加Provider调用、不改变源视频Gate结论。

`ProductionStateCommitter.register_generated_video_audio()`消费已结算、successful fetch、尚处于`VALIDATE`的remote/metered源，通过seekable临时WAV与既有probe生成独立P4语音素材。目标只支持Manifest2.0–2.2、Registry2.1，语音种类只支持dialogue/narration；更高版本在提取前拒绝。完整契约见[generated-video-audio.md](../generated-video-audio.md)。

登记复用`audio_import`事务；没有新Manifest字段、第二writer、第二timeline或direct mux。独立reader验证source submission/task、settlement budget、probe、工具、metadata、base project及Registry历史关联；TTS与派生claims独立且不得重叠。相同attempt由target内POSIX锁串行化，exact replay校验本次语义参数且不重复提取或Manifest写入。

## Review And Verification

首次独立review拒绝了参数漂移、source/probe闭包、历史snapshot关联、单进程锁、晚版本拒绝及异常路径缺失import。逐项修复并补充重新封存后的语义篡改测试；同一native `reviewer_xhigh`最终`accept`。没有用早期passing tests代替这些修复。

- 新功能及committer结构测试：30 passed，含真实本地临时MP4→PCM WAV→登记→strict reopen。
- 相关project/state-commit/generated-video-e2e组合：417 passed。
- Harness、CLI、runtime Skill边界组合：223 passed。
- Documentation contract、policy audit与task architecture delta：PASS；policy无unmapped/unverified paths。
- 完整Production suite：`python -m pytest -p no:cacheprovider tests -k 'production or video_candidate or video_generation' -q`，3147 passed、3 skipped、1353 deselected，736.61秒。最终focused+structure由parent另行复跑30 passed（9.30秒）。

用户明确禁止worktree，因此未执行会创建detached worktree的Harness verify，也没有签发fresh isolated Harness receipt。以上是已知working-tree上的实际验证，不冒称隔离receipt。保留七个原有staged runs文件；不push。

## Live Blocker And Next Action

### Follow-up — Minimal Edit Candidate

用户在了解分层制作方法后同意继续。Parent通过project-local `video_extract_frames`复看07的0/1.01/2.021/3.031秒画面：约2秒真实左手已抬起，所查看玻璃区域未见匹配的林砚或手部倒影。因此不应仅因刚讨论遮罩技术就重做已有可用视觉。

07既有广播ASR窗口为0.84–3.40秒，语音本身约2.56秒。现有`AudioTrackSpec.trim_start_sample`和同一timeline的audio span已经支持源裁切；可先试听从音轨前部移除约0.6–0.7秒是否仅移除广播前间隙，使广播落入前三秒。此候选保留07原生声音，无需先借08音轨；未实际试听/渲染，不能承诺不会切掉起音或产生环境声接缝。登记与结算blocker不因这一编辑候选消失；未执行新Provider、提取WAV、合成或activation。学习评估仍`no_candidate`，不是新生成实验。

attempt07 MP4：`88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e`，3,350,152 bytes。

attempt08 MP4：`cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e`，3,232,566 bytes。

两源paid state均为`ACCEPTED`、reservation仍`reserved`、`actual_cost_microunits=null`。已检查的fetch evidence无实际扣费字段。原生音轨入口与既有video candidate登记均要求真实settlement；不能把operator upper bound当实际费用，也不能伪造结算。已向用户请求各任务实际人民币扣费及账单依据，尚未收到。

本轮未对07/08提取、登记、activation或合成；没有新S01成片或逐镜PASS。只读mapping还确认：`validate_once()`只登记原request的inactive candidate，并不提供另一repair composition的通用视觉输入登记。音轨能力不能替代这一缺口。取得真实结算证据后，先沿既有committer完成合法结算，再处理视觉repair输入登记与原生音轨登记，构建新composition并调用project-local video-analysis。不得激活失败源或推进S02。

## Record And Learning

`record-ai-video-session`用于保存实现checkpoint及真实live blocker，并对旧记录添加有界supersession。`distill-ai-video-learning`评估为`no_candidate`：这是一次实现与回归验证，不构成独立媒体实验或跨实验质量结论；不创建占位claim、不修改Skill/Gate、不刷新RAG索引。
