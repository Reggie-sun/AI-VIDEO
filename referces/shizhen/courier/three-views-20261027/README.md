# Episode One Courier References

## Current Files

用户要求简单三张：正面、侧面、背面。已返回 [正面](images/01-front.png) 和 [侧面](images/02-side.png)，均为1024×1536单人全身参考，沿用第一集S05-005原帧的脸、白头盔、黑雨衣和黑黄配送包。裤鞋是未被原片完整展示部分的补全候选。

第三次背面调用网络中断、结果UNKNOWN，没有返回图片；有限3次调用已使用，零自动重试，未用新任务或其他入口重复同一背面请求。当前为 `PARTIAL_UNKNOWN_BACK`，不是已完成三张。费用未暴露，未知调用用量待确认。

## Evidence

`source-evidence.json` 保留原视频和取帧SHA，`generation-manifest.json` 保留三项实际提示词、真实附件、计数与未知状态；`verification.json` 已重开两张工作区图和工具原始输出、核对SHA并验证解码。人工接受／具体视频模型效果未验，未修改原视频、Registry或Manifest。
