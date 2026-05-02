# UX Analysis: F-005 Result Gallery

**Feature**: 视频和帧预览画廊，支持 clip/last_frame/final 浏览和下载
**Priority**: Medium | **UX Concern Level**: Medium
**Framework Reference**: @../guidance-specification.md

## User Journey

```
生成完成 → 自动跳转结果画廊
  → 按镜头浏览各产物 (clip.mp4 / last_frame.png / final.mp4)
  → 播放视频预览
  → 对比不同 shot 的结果
  → 下载单个产物 / 批量下载
  → 不满意 → 进入参数调优 (F-007) / 重新生成
```

## Information Architecture

### Gallery View Structure

画廊 MUST 按 Run 组织，每个 Run 下按 Shot 排列：

```
┌─────────────────────────────────────────────────────────┐
│ 生成结果 — 2026-05-02 14:30                              │
│ 总时长: 6s · 3 个镜头 · 最终视频: final.mp4               │
│                                                         │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│ │ ▶ 镜头 1  │  │ ▶ 镜头 2  │  │ ▶ 镜头 3  │               │
│ │ [clip]   │  │ [clip]   │  │ [clip]   │               │
│ │ 2s·16fps │  │ 2s·16fps │  │ 2s·16fps │               │
│ └──────────┘  └──────────┘  └──────────┘               │
│                                                         │
│ 最终合成视频                                              │
│ ┌──────────────────────────────────────────┐            │
│ │ ▶  [============================]  0:06  │            │
│ └──────────────────────────────────────────┘            │
│                                                         │
│ [下载全部]  [下载最终视频]  [重新生成]                      │
└─────────────────────────────────────────────────────────┘
```

### Asset Types per Shot

基于 `ClipArtifact` model，每个 shot 的产物包括：

| Asset | Source | Display | Action |
|-------|--------|---------|--------|
| clip.mp4 | 单 shot 生成结果 | 视频缩略图 + 播放 | 播放 / 下载 |
| last_frame.png | clip 最后一帧 | 帧图片缩略图 | 预览 / 下载 / 作为下一 shot 的 init_image |
| final.mp4 | 全部 shot 拼接 | 视频播放器 | 播放 / 下载 |

**Rule**: 用户最关心的是最终合成视频 (final.mp4)，MUST 优先展示；单个 clip 作为补充。

## Interaction Design

### Video Player (Native HTML5 - MUST)

- 点击缩略图 MUST 在原地展开播放器（无需跳转新页面）
- 播放器 MUST 提供标准控件：播放/暂停、进度条、音量、全屏
- 播放器 SHOULD 自动播放首个 clip，但 MUST 遵循浏览器 autoplay 策略
- 短视频（< 5s）MUST 在进度条旁显示总时长
- 播放器 MUST 支持逐帧查看（左右箭头键），便于内容创作者检查细节

### Thumbnail Grid

- 每个 shot MUST 显示视频首帧作为缩略图
- 缩略图 MUST 显示播放图标 overlay，暗示可点击播放
- 缩略图 hover MUST 显示 1s 预览动画（如技术可行）
- 缩略图角落 MUST 显示时长标签（"2s"）

### Gallery Navigation

- **Shot-Level View**: 默认视图，每个 shot 一张缩略图卡片
- **Detail View**: 点击 shot 进入详情，显示 clip + last_frame + 参数摘要
- **Comparison View**: SHOULD 支持并排对比两个 shot 的结果（同一 run 内）
- **Back Navigation**: 从详情/对比视图 MUST 轻松返回画廊总览

### Download UX

- 单个下载：hover 缩略图显示下载图标，点击即下载
- 批量下载：MUST 提供"下载全部产物"按钮（打包为 zip 或逐个下载）
- 下载进度：MUST 显示下载进度指示
- 文件命名：下载文件 MUST 使用有意义的命名 `{project}_{shot}_{asset_type}.ext`

## State Management

### Auto-Transition from Monitor

- 生成全部完成时 MUST 自动跳转到结果画廊
- 跳转 MUST 有 2s 延迟，显示"生成完成！正在准备预览..."
- 部分完成时 SHOULD 允许查看已完成 shot 的结果，未完成项显示"等待生成"
- 用户 MUST 也可手动从监控页跳转到画廊（即使未全部完成）

### Empty & Partial States

| State | Display |
|-------|---------|
| 生成中 | 已完成 shot 的缩略图 + 未完成项的骨架占位 |
| 全部失败 | "生成失败，请查看错误详情或调整参数后重试" + 错误摘要 |
| 部分失败 | 已完成项正常展示 + 失败项显示错误标记 + "重新生成失败项"按钮 |
| 无产物 | "暂无生成结果" + "开始第一次生成"引导 |

## Error Handling

- 视频加载失败（文件损坏/路径错误）MUST 显示"视频无法加载"占位图 + 重试按钮
- last_frame 缺失时 MUST 显示灰占位图 + "此镜头无末帧截图"
- final.mp4 未生成时 MUST 显示"最终视频尚未合成" + 合成触发按钮

## Recommendations

1. **Filmstrip Timeline**: SHOULD 在画廊底部提供电影胶片式时间线，显示各 shot 的首帧缩略图，点击跳转
2. **Quick Regenerate**: SHOULD 在每个 shot 卡片上提供快捷"重新生成"按钮，无需跳转到参数调优
3. **Thumbnail Generation**: SHOULD 在 shot 完成后立即生成缩略图（使用 last_frame），避免视频解码延迟
4. **Lightbox Preview**: MAY 提供全屏 lightbox 模式，支持左右切换 shot 预览
5. **Export Sharing**: MAY 支持生成分享链接（本地场景下，复制文件路径到剪贴板）
