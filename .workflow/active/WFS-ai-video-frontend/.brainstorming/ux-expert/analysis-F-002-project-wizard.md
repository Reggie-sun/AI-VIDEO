# UX Analysis: F-002 Project Wizard

**Feature**: 向导式项目创建/配置流程，引导非技术用户设定项目参数
**Priority**: High | **UX Concern Level**: Critical
**Framework Reference**: @../guidance-specification.md

## User Journey

```
开始 → 选择：新建项目 / 打开已有项目
         ↓ 新建
     Step 1: 命名项目 + 选择输出目录
     Step 2: 连接生成服务 (ComfyUI 地址)
     Step 3: 选择工作流模板 + 绑定文件
     Step 4: 配置默认参数 (分辨率/FPS/时长/种子策略)
     Step 5: 添加角色 (可选)
     Step 6: 确认摘要 → 进入分镜编辑
```

## Information Architecture

### Step Decomposition & Rationale

当前 `ProjectConfig` (from models.py) 包含 5 个配置组：`comfy`, `workflow`, `output`, `defaults`, `characters`。向导 MUST 将这些技术配置转化为用户可理解的步骤：

**Step 1: 项目基本信息**
- `project_name` → 项目名称（必填，首字段自动聚焦）
- `output.root` → 输出目录（默认 `./runs/<project_name>`，MUST 提供文件夹选择器）
- Smart Default: 用户只需输入名称，其余自动填充

**Step 2: 连接生成服务**
- `comfy.base_url` → 服务地址（默认 `http://127.0.0.1:8188`）
- `comfy.allow_non_local` → 允许远程连接（高级选项，默认隐藏）
- MUST: 提供"测试连接"按钮，点击后实时验证 ComfyUI 可达性
- UX Pattern: 输入框 + 内联验证状态 + "测试连接"按钮

**Step 3: 选择工作流**
- `workflow.template` → 工作流模板文件（MUST 提供文件选择器，限定 `.json`）
- `workflow.binding` → 绑定文件（MUST 自动推测，与模板同目录的 `_binding.yaml`）
- UX Pattern: 文件拖拽区 + 浏览按钮；绑定文件 SHOULD 自动关联，减少手动操作

**Step 4: 默认参数**
- `defaults.width/height` → 分辨率（MUST 提供预设：512x512, 768x512, 1024x576）
- `defaults.fps` → 帧率（MUST 提供滑块 + 常用值标签：8/16/24）
- `defaults.clip_seconds` → 片段时长（MUST 提供滑块，范围 1-10s）
- `defaults.seed` → 随机种子（MUST 默认 "随机生成"，高级用户可手动指定）
- `defaults.negative_prompt` / `defaults.style_prompt` → 提示词（MUST 提供模板建议）
- UX Pattern: 预设选择 + 高级折叠；参数 MUST 有说明 tooltip

**Step 5: 角色配置 (Optional)**
- `characters[]` → 角色列表
- 每个角色：`id`, `name`, `description`, `reference_images[]`, `ipadapter.weight`
- UX Pattern: 卡片式添加，拖入参考图；"跳过此步"按钮明显可见
- Frame Relay 关联：角色跨镜头一致性是核心价值，MUST 解释"为什么需要角色"

**Step 6: 确认摘要**
- MUST 展示所有配置的汇总视图，突出必填项和自定义项
- MUST 提供"保存并开始编辑分镜"按钮
- SHOULD 提供配置导出预览（YAML 格式，高级用户可参考）

## Interaction Design

### Wizard Navigation

- **Step Indicator**: 顶部水平步骤条，显示步骤编号和名称
- **Progressive Validation**: 每步 MUST 在"下一步"前验证必填项；验证失败 MUST 聚焦到首个错误字段
- **Skip Capability**: Step 5 (角色) MUST 可跳过；其余步骤 SHOULD NOT 跳过
- **Back Navigation**: 用户 MUST 可随时返回修改已完成步骤，已填数据 MUST 保留
- **Auto-save**: 每步完成 MUST 自动保存为草稿，刷新页面不丢失

### Smart Defaults Strategy

基于 `example.project.yaml` 中的默认值，向导 MUST 预填充：
- `comfy.base_url`: `http://127.0.0.1:8188`
- `defaults.width/height`: `512x512`
- `defaults.fps`: `16`
- `defaults.clip_seconds`: `2`
- `defaults.seed`: 随机生成（而非固定 100）
- `defaults.negative_prompt`: `blur, inconsistent face, extra limbs`
- `defaults.style_prompt`: `cinematic, consistent character, stable outfit`

**Rule**: 预填充值 MUST 让用户无需修改任何参数即可完成项目创建（零配置启动）。

### Error Prevention

1. **项目名称**: MUST 实时检查重名，MUST 禁止特殊字符
2. **服务地址**: MUST 格式验证 (URL pattern)，MUST 提供连接测试
3. **文件路径**: MUST 验证文件存在性，MUST 在文件选择器中过滤正确扩展名
4. **磁盘空间**: MUST 在选择输出目录后检查可用空间（`min_free_gb`）

## Cognitive Load Control

### Chunking Strategy

- 每步 MUST 不超过 5 个可交互字段
- 高级参数（`allow_non_local`, `seed_policy`, `max_attempts`, `poll_interval_seconds`, `job_timeout_seconds`）MUST 折叠在"高级设置"中
- 角色配置的 IPAdapter 参数（`weight`, `start_at`, `end_at`）MUST 折叠在角色卡片内

### Progressive Disclosure Layers

| Layer | Visibility | Content |
|-------|-----------|---------|
| L1 - Essential | 始终可见 | 项目名、服务地址、工作流选择 |
| L2 - Recommended | 默认展开 | 分辨率预设、FPS、时长 |
| L3 - Advanced | 默认折叠 | 具体数值、种子策略、超时设置、远程连接 |

## Onboarding Considerations

- 首次使用 MUST 显示简短引导（3 步以内），解释核心概念：项目 → 分镜 → 生成
- 空状态 MUST 提供示例项目模板（一键加载 `example.project.yaml`），让用户快速体验完整流程
- "打开已有项目" MUST 支持拖入项目目录或 YAML 文件

## Recommendations

1. **Template Gallery**: SHOULD 提供 2-3 个预设项目模板（如"角色动画"、"风景序列"），降低从零开始的门槛
2. **Connection Autodetect**: SHOULD 尝试自动检测本地 ComfyUI 实例，减少手动输入
3. **Config Import**: MUST 支持导入已有 `project.yaml`，将 CLI 用户迁移到前端
4. **Guided Tooltips**: 每个配置项 MUST 有 `?` 图标，hover 显示解释文案
5. **Step Completion Indicator**: 每步 MUST 在步骤条上显示完成状态（对勾/警告/错误）
