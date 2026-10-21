# Jimeng Model Family Implementation Plan

**Goal:** 在同一个 Jimeng Provider / Browser Worker 中声明四个 Seedance 型号，并强制正式路由资格边界。

**Scope:** `seedance_2.5`、`seedance_2.0_mini`、`seedance_2.0_vip`、`seedance_2.0_fast_vip` 的原生 mode 4 参数、素材限制、身份及静态生产资格声明。

**Invariants:** 不替换模型、不降级规格、不新增 Provider、状态 owner、预算 owner 或恢复入口；无新付费生成；所有型号默认 `UNQUALIFIED`。资格是 capability 的不可变准入声明，不是第二套任务生命周期。

**Compatibility:** 保留旧 2.5 profile 的序列化 identity；未声明资格的其他 Provider 及其历史 capability hash 保持兼容。历史任务的读回、恢复不受新任务路由资格阻断。

## Major Milestones

### Milestone 1: Evidence And Independent Model Contracts

新增 `jimeng_models.py`，集中只读 native config / reference constraints 证实的各型号限制；修改现有 `jimeng_contracts.py`、`jimeng.py`、`jimeng_browser.cjs` 消费精确模型标识。保持一个 adapter 类和 worker，未知标识拒绝。新模型支持当前接口证实的分辨率；原有型号保留现有输出范围。把脱敏只读投影留在已有 fixture 目录，不保存账号、Cookie、URL 或完整响应。

### Milestone 2: Production Route Eligibility

在现有 `VideoCapabilityVariant` 增加 optional `production_qualification`，非空值进入 capability fingerprint；旧 snapshot 未声明时保持原字节及 hash。现有 `VideoGenerationResolver` 对 `UNQUALIFIED` 明确返回 `BLOCKED_CAPABILITY / MODEL_UNQUALIFIED`，没有 profile 开关或自动晋级。四个 Jimeng 型号均显式声明未获资格。

### Milestone 3: Verification And Delivery

在现有 Jimeng / Router tests 中验证四型号映射、独立 profile、边界拒绝、Worker action 原生 model、素材次序、UNKNOWN 保留、未获资格不能 route 和旧 Provider hash。标准生命周期 Mock 显式使用测试资格 snapshot，不冒充真实资格。运行 focused tests、exact staged Harness，区分基线失败。按 Risk Gate 进行一名 native reviewer 审查，修复确认问题；更新 provider 文档及工程记录，按 owned paths commit / push 并核对远端 SHA。

**Acceptance:** 四型号可技术解析并映射，未获资格的正式路由零提交；没有新真实生成，模型真实出片、扣费结算和完整持久化成功链保持 `NOT_EVALUATED`。
