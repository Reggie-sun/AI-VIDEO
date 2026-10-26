# Two Passengers Review Film

## Review File

[失帧-两位冷开场加S01-1080p审看版.mp4](失帧-两位冷开场加S01-1080p审看版.mp4)：1920×1080、24fps、868帧、约36.167秒。冷开场含片名484帧／20.167秒，随后接已认可S01名义16秒原片区间与已有双语字幕。也可打开[index.html](index.html)播放。

成片SHA-256：`5ab3a929258db93606196ab537d89c795343899dba8616dbdd8905e55433e48a`。状态为`REVIEW_READY`，human审美/听审`NOT_EVALUATED`，未发布、未Production激活、未签Final Acceptance。

## Director And Source Decisions

开画即为普通同事通话候车，保留关心路滑的关系；同一空间在货车遮挡后只剩一位，罗敏平常确认自己一人。准确时钟03:16:53自然推进到03:16:59，遮挡后03:17:11；电影片名后“翌夜”进入S01。不增加新机制，不预泄终场反转。

用户提出Seedance2.5可单次30秒后，已实际一次生成22秒完整事件。该原片四轮对白与事件完整，但高峥开头未保留挎包，原始identity判FAIL，声音证据当时不全；完整原片和原判决保留，未倒签PASS。导演剪辑用已合格A1/A2前段修复此偏差，再取整段版实际胸上近景的电话核对和回答。没有追加视频生成，也不声称交片全部来自一次原片。

原单次生成文件：[两位-Seedance2.5单次22秒原片-整条未采用.mp4](两位-Seedance2.5单次22秒原片-整条未采用.mp4)。其完整raw Gate仍为FAIL，不作最终认可版本。

## Audio And Music

配乐使用现有Music Director/Suno v6生成的“缺席的应答”候选B，仅在3.5秒片名处播放，S01前退出；对话及失踪过程留给原生城市环境与表演。工具描述其为器乐钢琴/弦乐/氛围合成器，不宣称指定单簧管或两音审美已实现；冷峻程度由用户听审。

`music/ending-theme-handoff.json`保留同一实际录音首段主题用于终场反转之后再现的交接；完整88.8秒原WAV保留，不重复生成，不提前预示反转。片尾实际入点由未来整集ResolvedTimeline确定。

`qa/final-v1-original-audio-preservation.json`证明四段选中原声窗口在实际P4 canonical WAV内逐样本一致，0增益／无fade／无duck，不挪句、不重配或变速。最终AAC有正常编码损耗，不能称字节无损。最终盲音频观察确认四轮开场对白齐全，电话男性声线与滤波可辨，S01原对白完整、表演自然。

## S01 Preservation

保护源：`../失帧-第一集-S01-1080p高清版-Seedance2.5-16秒.mp4`，SHA-256 `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，再次核验未变。复用此前认可的0–16秒名义区间、原生解码音轨与四组双语字幕。原文件16秒后的endpoint/AAC空尾仍保留于原文件，不声称编码padding全部进入审看版；原对白最后一句约14.16秒结束。本次没有重生成S01或修改其源文件／字幕。

## Verification

- `qa/final-editorial-review.json`：交片范围、逐项发现与边界
- `qa/final-v1-mcp.json`、`final-v1-summary.json`：exact最终MP4的project-local MCP与真实Gemini音频观察
- `qa/final-v1-boundaries/`：遮挡接点、准确时钟、片名、翌夜、S01四组字幕的实际成片帧
- `composition/composition-spec.json`、`resolved-timeline.json`、`render-receipt.json`：唯一P4时间线与HyperFrames真实渲染，未direct mux
- `qa/p4-verification-receipt.json`、`p4-related-tests.xml`：59项相关测试通过，不是全量回归或人工验收

为出片修复现有`_composition_visual.py`的组合限制：每条captured video仍严格绑定同源同区间原声，允许无对白静态片名和独立BGM；原声0gain/no-fade/no-duck、字幕归属、连续区间及activation fence保留。相关负向测试与真实出片已验证。完整工程验证及owned-path commit/push按film-first等待用户审片认可；未夹带其他窗口改动。

## Counts And Cost

本次内置imagegen5次、即梦视频3次（8秒、4秒、22秒）均有已知结果；新视频无UNKNOWN。原六次历史及同期其他窗口S03一次保留，合计10次；冷开场自身3次上限未增加。内部CRD上界不是实际费用，视频及图像实际费用待结算。

本次Suno一次逻辑请求生成一对候选，实际10credits，余额2480→2470；历史调用与两次UNKNOWN未改动。真实音频理解6次独立exact unit已知完成，实际API费用未结算。相关intent、one-use消耗、原始结果与身份均保留。未发布，未做新付费生成。
