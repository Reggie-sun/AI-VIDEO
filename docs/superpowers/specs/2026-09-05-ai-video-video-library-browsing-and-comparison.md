# AI-VIDEO Video Library Browsing And Comparison

Date: 2026-09-05
Status: Implemented locally; current verification and limits are recorded in the runtime baseline.
Scope: Existing Provider Console local read-only browsing surface.

## Goal

默认体验以浏览、播放与比较视频为中心。用户无需理解 `runs/`、Production fetch layout 或
Provider lifecycle，即可找到已有视频；生成排障与证据仍可从详情进入。

初始 checkpoint 只交付轻量 spec。后续用户明确要求实施，现已在既有只读 Console 实现下方
contract；本次仍不包含媒体生成、Production mutation 或新的 execution gateway。

## Current Evidence And Problem

- `provider-console/src/video-library-rail.jsx::VideoLibraryRail` 在默认 `all` 下只展示当前
  workspace attempts；其他 workspace 仅在 `runs` 下可访问。“全部视频来源”因此不等于全部视频入口。
- `provider-console/scripts/external-media.mjs::walkRoot` 的 `run_outputs` 扫描覆盖
  `output/outputs/sidecars/evidence`，不覆盖 Production fetch 目录。不能靠该 external source
  替代 canonical Runs projection。
- `src/ai_video/provider_console.py::catalog_runs`、`project_workspace_detail` 已能读取以下两个项目；
  当前 Console 支持播放各自 `fetched_media`，无需先成为 candidate。
- 2026-09-05 本会话真实浏览器验证：Mini 为 15.104 秒、2.5 为 30.08 秒，均为 1280×720，
  exact media token 的 `readyState=4`、播放时间递增且无 media error。它们的 attempt 为
  `running / validate`，不等于仍在生成，也不证明任何质量验收通过。
- 当前详情首屏优先展示长 Prompt、record chain 和 Provider 参数，播放器需要额外定位；列表以
  截断目录名为主，缺少可供辨认的缩略图。以上是本次展示问题的 evidence，不是媒体质量结论。

| Acceptance fixture | Run | Exact artifact SHA-256 |
| --- | --- | --- |
| Greenhouse Mini | `director-seedance-mini-greenhouse-20260905-002` | `1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564` |
| Greenhouse 2.5 | `director-seedance25-greenhouse-20260905-001` | `26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a` |

## Information Architecture

1. **视频库**是当前浏览 surface 的默认入口，统一展示已发现的 canonical Runs 与 allowlisted
   external 视频。默认不要求先选 workspace，不以“证据已关联”过滤掉可预览的原始输出。
2. **生成记录**是同一 surface 内的次级视图，保留无视频、进行中、失败和待恢复的 attempts，
   以及没有 video attempt 的 workspace/Shot 检查入口。不可播放记录不能冒充视频卡片。
3. 点击视频进入**预览详情**：播放器、完整可辨认标题、模型、实测时长和状态摘要优先；下方或
   次级区域提供版本、创作意图、生成详情和证据。沿用现有导航范围，不要求重做全站 sidebar。

## Library Contract

### Entries And Identity

- 列表单位是 exact 视频内容，以已验证 `sha256 + size_bytes` 去重。同一内容出现在多个来源或
  多个 attempts 时只显示一个视频条目，并可展开全部来源、角色和关联；不同 bytes 不合并。
- candidate、fetched、已注册视频与 external output 均按各自现有 reader 的允许范围投影。
  同时包含 strict Project reader 已验证的 `active_render_state` 成片输出；不裸扫 render 目录，
  不从恢复旁证推导 active render。成片不借用源 Shot 的 Provider、Prompt 或版本身份。
  External `run_outputs` 覆盖 run 根目录直属视频和既有 `output/**` / `outputs/**`；直属
  文件仍是非 canonical 媒体，不递归发现其他 Production 内部目录，不解释相邻任意 JSON。
  同一 attempt 的 fetched/candidate 若不同 bytes，则作为不同输出保留角色标记；不只取 active。
- 展示层只合并 read-only projections，不成为第二个 Registry、Manifest、timeline 或证据 owner。
  每个来源仍保留自身 authority；多个绑定有歧义时，显示歧义并让用户选择详情上下文，不能任取
  一个 Prompt、质量结论或 Project title 当成唯一真相。
- 无有效 media descriptor、文件已变化、越界或 reader 校验失败时，不提供播放。保留可解释的
  不可用条目/记录和刷新入口；不能裸扫 fetch 目录补造 canonical binding，也不复制 MP4 到
  `outputs/` 来绕过现有展示范围。

### Cards, Search And Ordering

- 卡片优先显示 exact 视频缩略图、作品/Shot 名、模型、实测时长、生成时间与媒体可用状态。
  缺失字段明确显示“未提供”；模型未知时不从目录名猜测。标题可换行，详情可见完整名称与
  source-relative identifier，不用一串相同的 `director-se…` 作为主要辨识信息。
- 缩略图必须来自当前 exact 视频 bytes；失败时显示“预览图暂不可用”，但不阻断可用视频播放。
  不生成替代画面、不调用模型。缩略图是可丢弃的本地预览，不能注册或被当作质量 evidence。
- 一个统一搜索框覆盖所有已加载来源的标题、run/workspace、Shot、模型与文件名。
  第一轮不要求跨 workspace 全文 Prompt 搜索；Prompt 仍从选中视频的允许详情中查看。
  来源、模型、媒体状态和高级证据筛选对同一列表生效；来源筛选不切换成另一套列表逻辑。
- 默认按关联 video attempt 的 `started_at` 降序；没有可信 attempt 时间的 external 条目使用
  已投影的文件时间，并标明“文件时间”。未知时间置后；同时间以稳定 identity 排序。
  workspace mtime、刷新时间不得伪装成生成时间。
  Active render 成片使用其 canonical render attempt 的 `started_at` 参与相同排序；缺失时置后。
- 首屏呈现可用结果，不等待所有来源关联完成。显示“已加载 N 段”和扫描/关联是否完成；计数与
  筛选一致。扫描截断、单来源失败、恢复旁证或 stale 数据必须可见，不能宣称已完整列出全部内容。
- 大量视频采用分页或虚拟列表，预览解码与请求并发有界；滚动离屏不保留无限 video decoder。
  查询覆盖的已加载范围必须明确，不能把未完成索引下的零结果表述为“视频不存在”。

## Preview And Status Contract

- 选中可用视频后，在详情顶部直接看到播放器及封面，无需先穿过 Prompt 或点击底部跳转按钮。
  播放由用户触发；切换视频停止上一段的播放，音频不在多个播放器间意外叠加。
- 实测时长/尺寸与请求规格分开。实际没有测量值就显示未知，不拿计划时长填作成片时长。
- 播放错误须区分文件不可用、浏览器无法解码和请求失败；不能仅凭 `MediaError` 把已存在的
  exact bytes 标记为丢失。后两者保留原文件下载，刷新可重试，切换视频取消旧错误检查。
- 用户明确授权的本地兼容转码副本通过既有 External 来源作为独立视频展示，名称标明兼容预览。
  原文件与 SHA 保持不变；副本不自动替换原播放器，不继承原文件的模型、lifecycle 或质量结论。
  浏览、刷新和解码失败本身均不触发转码。
- Prompt、完整 request 参数、Provider identity、source-relative paths 和 exact evidence references
  放进“创作意图 / 生成详情 / 证据”；不删除现有允许查看的诊断信息。
- 状态分为三个独立维度，详情保留原始 typed lifecycle：

| Dimension | Display meaning | Forbidden inference |
| --- | --- | --- |
| Media availability | 已获取 · 可预览 / 尚无视频 / 文件不可用 | 可预览不等于 candidate、active 或成片交付 |
| Generation lifecycle | 真实 attempt status 与 phase；如“等待验证（running / validate）” | `running` 不能统一翻译为仍在生成；不得据此修改 Manifest |
| Review evidence | exact、适用且新鲜的 requirement findings；缺失显示“未评估”，陈旧显示“证据已过期” | Provider success、播放成功、旁证已关联不等于 P6 或 Final Acceptance |

- 全部 required findings 的展示遵循既有 Gate；多个 proof layers 独立显示。缺少 canonical
  receipt 时不得把外部 `media-gate.json` 或 Agent 评论提升为 Production 质量通过。
- 手动选择的视频保持固定。后台刷新或新输出不会抢走播放器；沿用显式“跟随最新”选择语义，
  手动选择退出跟随。异步旧响应不得覆盖新选择；被选文件消失时显示不可用，不静默切换其他视频。

## Versions And Comparison Contract

- **内容去重、版本关联、临时比较是三件事。** 相同 bytes 可以有多个上下文；不同 bytes
  的版本关系必须来自明确项目/Shot 身份，不能由相似文件名、标题、日期或模型推断。
- 第一轮自动版本 key 为 strict reader 验证的 `(workspace, project_id, target_shot_id)`。
  每个 member 必须具有 `target_shot_revision`、`target_shot_content_hash` 以及
  `shot_snapshot_status=verified`；缺字段、identity 冲突或 unverified 时保留独立条目，不擅自归组。
  显示各自 revision、模型、时间及输出角色。不同 workspace/project 的视频保持独立，除非未来
  另行引入明确的关系契约。
- Greenhouse Mini 与 2.5 当前是独立 Project。本 spec 不把它们自动合并；用户可从统一视频库
  临时选择任意两段可用视频，进入双视频比较。比较选择仅是当前浏览会话状态，不写项目关系。
- 比较同时呈现两段视频、各自完整标题、模型、实测时长与状态。各自独立播放/暂停/定位；
  默认静音，用户打开一路声音时关闭另一路。退出后回到原筛选、滚动与选中状态。
- 15 秒与 30 秒媒体不强制对齐、不自动循环或改速，不宣称时间线或 Shot 已同步。
  同步时间线、自动质量排名、多视频批量比较和持久化版本编辑不在第一轮范围。

## Ownership And Compatibility

- 当前 read-only truth 继续由 `provider_console.py`、`provider_console_media_index.py` 和既有
  evidence projectors 提供；local media transport 继续由 `provider-console/scripts/runs-api.mjs`
  与 external-media owner 负责。UI aggregation 只消费它们，不自行解析 Manifest/Registry。
- 保留 opaque token、exact bytes revalidation、path containment/no-follow、sanitized projection、
  HTTP Range 和 local-only 边界。Browser 不接收 absolute paths、raw Provider responses、signed
  remote URLs、credentials 或 arbitrary evidence JSON。
- 如现有 projection 不足以支撑统一列表，应在现有 read-only owner 内补充最小字段或 assembly，
  并在 implementation planning 时落实 additive compatibility、focused tests 与 Harness routing；
  不新增独立 scanner、第二份持久化 catalog、新 runtime dependency 或 Product subsystem。
- 本 spec 的 UI Contract 在实施后替换旧
  [Runs integration spec](2026-08-22-ai-video-provider-console-runs-integration.md) 的
  workspace-first/default selected-workspace 展示方式；旧 spec 的 reader、transport 和安全边界继续有效。
  [Execution control spec](2026-08-22-ai-video-provider-console-execution-control.md) 的 mutation scope
  不由本 spec 激活或变更。实现与验证范围由 current runtime baseline 记录。

## Acceptance Criteria

| ID | Scenario | Required result |
| --- | --- | --- |
| A1 | 打开默认视频库，搜索两个 greenhouse run 或模型 | 无需切换到 Runs，两个 exact 视频均可找到；可见区别、缩略图、各自模型和时长 |
| A2 | 点选其中任一视频 | 详情首屏有播放器；exact identity 对应，解码成功且播放时间递增；Prompt 不遮挡首要播放入口 |
| A3 | `running / validate` 且 fetched 成功、candidate 缺失 | 显示已获取可预览及等待验证；不显示为仍在 Provider 生成或质量已通过 |
| A4 | 同 bytes 多来源 / 不同 bytes 同标题 / ambiguous bindings | 分别去重保留全部来源、不误合并、显式上下文歧义；不借用其他 artifact 的 Prompt 或 verdict |
| A5 | 独立 Project 的 Mini 与 2.5 | 不自动归组；可手动选择两段比较，各自时长与状态正确，声音不叠加，不生成持久关系 |
| A6 | failed/no-media attempt、无 attempt workspace | 可在生成记录中找到错误和 Shot 上下文；默认可播放视频列表不混入假视频卡片 |
| A7 | 新视频到达、乱序刷新、选中内容删除/变更 | manual pin 保持；旧响应不覆盖新选择；失效媒体停止服务，提示真实不可用 |
| A8 | partial/stale/truncated source、local bridge 不可用 | 显示覆盖范围与错误，保留有效结果；不自动 remote fallback 或使用静态假数据 |
| A9 | 大列表、缩略图失败、keyboard 与窄屏 | 初始浏览不等待全部解码；失败缩略图不挡播放；筛选/选择/比较键盘可达且焦点可见；窄屏仍可看视频与完整身份 |
| A10 | 浏览、刷新、筛选、播放和比较 | 不发 Provider submit/retry/activate，不写 Manifest/Registry，不重新生成、改写或上传源媒体；只允许可丢弃的本地预览，安全与 Range contracts 不退化 |

## Verification And Completion

- 实施前按真实 changed paths 执行 Harness inspection。补充 unified-list identity/filter/status/selection
  的 focused tests；若修改 reader/bridge，同步覆盖坏文件、歧义、stale 和 token transport 的失败路径。
- 在真实本地前端执行 A1–A10，重点记录两个 fixture 各自 exact media identity、HTTP Range、
  decoded dimensions、duration、播放进度与 console error；原始 run 只读，不重新生成或激活。
- Browser QA 检查桌面与窄屏，包含键盘选择/焦点及两个 unequal-duration 视频的手动比较。
  mock/unit/build/Harness 不能替代真实页面验收，也不能证明媒体质量。
- 代码实施完成才更新相应 current-runtime owner，运行 exact snapshot 的 policy-required checks，
  获取 fresh receipt，并接受独立 review。初始 docs-only checkpoint 的证据仅限文档及其 policy checks。
