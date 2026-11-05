# Clock Boundary Recheck Plan

已知结果的有限新验证单元：最多1次本地HyperFrames渲染、10分钟，不调用Provider，不生成底片，不重置前两次渲染历史。

问题：offset=2、song event=2.6s时，last()返回comp time0.6000000000000001，原pulse在0.6s帧因极小负dt丢脉冲；新增回归实测修复前1失败，修复后7项通过。修复保留last()的未来事件拒绝，将计算误差产生的负dt归零。

T01使用offset=0且拍点为精确半秒，预期该修复不改变任何已认可像素/音频。重新build/render到新路径、生成联系图与完整本地QA，比较原片SHA5e4601b0824b2cb82a42c9041178b0d3f06827f1d66de4e14755bf83b47a3697。只有bytes相同才保留exact媒体认可；不相同就保留新片证据并重新审看，不继承旧工程receipt。

旧source-and-media-sha256.json仅保留为历史，新的代码identity另存，不倒填旧PASS。
