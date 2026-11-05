# Tool Boundary Review

## Subsequent Test Location

工具测试已移到标准`tests/test_motionkit_tools.py`以真实纳入full pytest发现；旧命令与哈希保留为本次历史。新直接9项通过的证据见`tool-boundary-tests-r2.json`，精准Harness候选证据见`mapping-proposal-focused-r3/receipt.json`。

2026-10-30 独立代码复核发现三项问题：短音频STFT窗口越界读取、QA失败仍返回0、参考原路径可变导致事后SHA不一定对应输入。修复后独立只读复审为 **APPROVE（这四文件、0 open issues）**；没有模型或Provider调用，未重渲染已认可dev7。

当前边界：`sliding_window_view`拒绝不足2048样本；required QA失败写完报告后退出2；参考图在执行前复制封存并保存SHA及intent，子进程读取封存副本；目标已存在时执行前拒绝。

父会话新鲜运行`python -m pytest motion-kit/tests/test_tool_boundaries.py -q`得到 **9 passed in 0.69s**，覆盖空/短输入、正常FFT数值、QA成败报告和退出码、参考原图删除后identity、目标已存在时零调用。source identity见`tool-boundary-tests.json`。

此为直接有界工程验证，不是Harness receipt；full Harness仍被既有policy审计缺口阻断。工具测试不代签媒体、歌唱对嘴、Production或人工接受。
