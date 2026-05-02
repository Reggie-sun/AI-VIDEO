# Feature Spec: F-005 - result-gallery

**Priority**: Medium
**Contributing Roles**: ui-designer, ux-expert
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- 画廊 MUST 按 Run 组织视频/帧产物，每个 Run 下按 Shot 排列
- 画廊 MUST 支持三种产物类型浏览：clip.mp4（单 shot 视频）、last_frame.png（末帧图片）、final.mp4（合成视频）
- 画廊 MUST 使用原生 HTML5 video 播放器（D-013），SHOULD 预留增强播放器替换能力
- 画廊 MUST 支持视频下载（单个产物 + 批量下载）
- API Gallery 文件服务 MUST 支持 HTTP Range Requests，MUST 防止路径遍历攻击
- 缩略图策略 MVP MUST 使用 `last_frame.png` 作为视频卡片缩略图，MUST NOT 额外生成缩略图
- 画廊 MUST 支持从生成监控（F-004）和运行历史（F-006）入口进入
- "Set as Init Image" MUST 支持将 last_frame 设为其他 shot 的初始图像

### 用户体验需求

- 最终合成视频 (final.mp4) MUST 优先展示，单个 clip 作为补充
- 视频播放器 MUST 设置 `poster` 为 `last_frame.png`，提供即时视觉反馈
- 视频 MUST 支持逐帧查看（左右箭头键），便于内容创作者检查细节
- 画廊 MUST 支持两种视图模式：Grid View（默认，3 列）和 Timeline View（水平胶片带）
- 产物卡片 MUST 使用 16:9 固定宽高比，创建视觉节奏
- 部分完成时 MUST 显示已完成项 + 未完成项骨架占位
- 空状态 MUST 提供引导 CTA："开始第一次生成"
- 视频加载失败 MUST 显示占位图 + 重试按钮

### 技术需求

- 文件 URL MUST 使用统一模式：`/api/files/{run_id}/{shot_id}/{artifact_type}`
- `<VideoPlayer>` 组件 MUST 设计为可替换增强架构，接口 MUST NOT 在切换实现时变化
- 下载 MUST 设置 `Content-Disposition: attachment` header
- 批量下载 MVP MAY 返回 501 Not Implemented（后续用 zip 流式压缩）
- 画廊 MUST 通过 URL 可访问：`/results/{run_id}` 和 `/results/latest`

## 2. Design Decisions

### Decision 1: 原生 HTML5 播放器 + 可替换增强架构 (D-013)

- **Context**: 需要选择视频播放器方案
- **Options Considered**:
  - (A) video.js/plyr 增强播放器 — 功能丰富但 MVP 复杂度高
  - (B) 原生 HTML5 video — 简单可靠，MVP 足够
  - (C) 原生先行 + 可替换架构 — MVP 用原生，预留增强接口
- **Chosen Approach**: 方案 C。MVP 使用 `<video controls>` 原生播放器，`<VideoPlayer>` 组件 MUST 接受 `enhanced` prop（默认 false），未来切换到 video.js 时接口不变
- **Trade-offs**: 优势：MVP 快速实现，后续可渐进增强；劣势：原生播放器功能有限（无逐帧精确控制）
- **Source**: guidance-specification.md D-013, ui-designer (Video Player Component)

### Decision 2: 大文件处理 — 缩略图优先策略

- **Context**: conflict_map 标记 F-005 存在大文件处理冲突
- **Options Considered**:
  - (A) 视频文件即时加载 — 大文件首帧延迟高
  - (B) 缩略图优先（poster attribute）+ 按需加载 — 即时视觉反馈
  - (C) 预生成缩略图 — 需额外处理流程
- **Chosen Approach**: 方案 B。视频卡片 MUST 使用 `last_frame.png` 作为 `poster` 属性，提供即时视觉反馈。视频 MUST 使用 `preload="metadata"` 仅加载元数据，点击播放时才加载完整视频
- **Trade-offs**: 优势：首屏渲染快，带宽友好；劣势：缩略图与视频首帧可能不完全一致
- **Source**: conflict_map F-005 (SUGGESTED: thumbnail-first, poster attribute), system-architect (Thumbnail Strategy)

### Decision 3: 最终视频优先展示

- **Context**: 用户最关心最终合成视频 (final.mp4)，但技术实现上单 shot 产物先产出
- **Options Considered**:
  - (A) 先展示单 shot 产物 — 技术自然顺序
  - (B) 先展示 final.mp4，单 shot 产物作为补充 — 用户优先
- **Chosen Approach**: 方案 B。页面布局 MUST 将 final.mp4 放在显著位置（全宽播放器，640px 高度），单 shot 产物以 Grid 卡片形式展示在上方。若 final.mp4 未生成，MUST 显示"最终视频尚未合成"
- **Trade-offs**: 优势：用户第一眼看到最重要的产出；劣势：final.mp4 依赖所有 shot 完成和拼接
- **Source**: ux-expert (Asset Types per Shot rule: "用户最关心 final.mp4"), ui-designer (Final Output Section)

### Decision 4: 两种视图模式

- **Context**: 不同用户偏好不同的浏览方式
- **Options Considered**:
  - (A) 仅 Grid View — 简单但缺乏时间线上下文
  - (B) 仅 Timeline View — 直观但单 shot 详情受限
  - (C) 双视图可切换 — 兼顾两种需求
- **Chosen Approach**: 方案 C。Grid View（默认）：3 列卡片网格，适合概览。Timeline View：水平胶片带 + Frame Relay 连线，适合理解序列关系。Header 提供 icon 按钮切换
- **Trade-offs**: 优势：灵活适应不同场景；劣势：需维护两种布局
- **Source**: ui-designer (View Modes), ux-expert (Gallery Navigation)

### Decision 5: 从监控自动跳转

- **Context**: 生成完成后用户期望立即查看结果
- **Options Considered**:
  - (A) 不自动跳转 — 用户可能不知道已完成
  - (B) 自动跳转 — 即时但可能打断用户其他操作
  - (C) 延迟自动跳转 + 手动选项 — 平衡
- **Chosen Approach**: 方案 C。全部完成时 MUST 在 2s 延迟后自动跳转到画廊，显示"生成完成！正在准备预览..."过渡。用户 MUST 也可手动从监控页跳转（即使未全部完成）
- **Trade-offs**: 优势：自动化体验，用户无需手动导航；劣势：2s 延迟可能让急躁用户困惑
- **Source**: ux-expert (Auto-Transition from Monitor)

## 3. Interface Contract

### Gallery API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs/{run_id}/gallery` | 获取 Run 的所有产物索引 |
| GET | `/api/runs/{run_id}/gallery/{shot_id}/{kind}` | 获取特定产物（clip/last_frame/normalized_clip） |
| GET | `/api/runs/{run_id}/gallery/{shot_id}/{kind}/download` | 下载单个产物 |
| GET | `/api/runs/{run_id}/gallery/download-all` | 打包下载全部 |

### Gallery 索引响应

```json
{
  "run_id": "run-...",
  "final_output": {"video": "/api/files/.../final.mp4", "duration_s": 8.0},
  "shots": [
    {
      "shot_id": "shot_01",
      "clip": "/api/files/.../clip.mp4",
      "last_frame": "/api/files/.../last_frame.png",
      "normalized_clip": "/api/files/.../normalized/shot_01.mp4",
      "duration_s": 2.0
    }
  ]
}
```

### 组件接口

**`<VideoPlayer>`**: Props: `src`, `poster?`, `enhanced?` (default false), `onEnded?`
**`<FrameThumbnail>`**: Props: `src`, `size` (sm|md|lg), `clickable` (boolean)

### URL 路由

- `/results/{run_id}` — 显示指定 Run 的结果
- `/results/latest` — 显示最近一次 Run 的结果

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| 大文件传输阻塞事件循环 | Medium | FastAPI 异步 FileResponse（默认支持） |
| 路径遍历攻击 | High | Path.resolve() + startswith() 校验 |
| 大量 Run 目录扫描性能 | Low | 限制列表分页 + 缓存 |
| 首次加载无缩略图 | Low | 使用 last_frame.png 作为替代 |
| final.mp4 依赖全部 shot 完成 | Medium | 部分完成时显示"尚未合成" + 已完成 clip 可预览 |

## 5. Acceptance Criteria

1. 画廊 MUST 在页面顶部显著位置展示 final.mp4 播放器
2. 视频卡片 MUST 使用 16:9 固定宽高比，poster MUST 设置为 last_frame.png
3. 点击视频卡片 MUST 在原地展开播放器（无需跳转新页面）
4. `<VideoPlayer>` MUST 支持 `preload="metadata"` 和 `poster` 属性
5. 下载单个产物 MUST 设置 `Content-Disposition: attachment` header
6. "Set as Init Image" MUST 打开 shot 选择器，将 last_frame 设为指定 shot 的 init_image
7. Grid View MUST 显示 3 列卡片，Timeline View MUST 显示水平胶片带
8. 视口 < 1280px 时 Grid View MUST 调整为 2 列（EP-007 桌面端最低保障）
9. 视频加载失败 MUST 显示"视频无法加载"占位图 + 重试按钮
10. 画廊 MUST 通过 `/results/{run_id}` URL 直接访问
11. 部分完成时 MUST 在已完成 shot 旁显示骨架占位
12. 空状态 MUST 提供引导 CTA

## 6. Detailed Analysis References

- @../system-architect/analysis-F-005-result-gallery.md — 文件服务架构、Gallery API、大文件处理、安全考虑、跨 Run 对比
- @../ux-expert/analysis-F-005-result-gallery.md — 用户旅程、画廊视图结构、视频播放器交互、下载 UX、状态管理
- @../ui-designer/analysis-F-005-result-gallery.md — 画廊布局、视频播放器组件、Shot 结果卡片、帧画廊、导航设计
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: F-001 (Gallery API + 文件服务), F-004 (生成完成后跳转)
- **Required by**: F-006 (历史记录查看结果跳转画廊)
- **Shared patterns**:
  - `<VideoPlayer>` 组件 — F-005, F-006 共用
  - `<FrameThumbnail>` 组件 — F-003, F-004, F-005 共用
  - `<EmptyState>` 组件 — 所有功能共用
  - 骨架加载模式 (EP-006) — 视频列表和图片加载
- **Integration points**:
  - F-004: 全部完成后"查看结果"跳转到画廊
  - F-006: 历史记录"查看结果"跳转到画廊
  - F-007: 画廊中"Open in Tuner"跳转到参数调优
