---
record_kind: recovery_incident
topic_id: suno-cli-skill-preflight-repair
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Suno CLI Skill And Native Preflight Repair

> **Latest live checkpoint:** 用户随后明确授权继续生成。保留原3次历史，新增一次有界请求，
> 累计上限3→4；真实CLI生成、查询、下载均成功，新增10 credits、累计20，余额2480。
> 详见下方 Live CLI Recovery。初次只读检查点的“未做第4次”不再代表当前状态。

## Outcome And Scope

用户明确要求修复已有 Suno CLI Skill，并允许结合 REA 分析。已修复两个实际安装的
Skill 和 AI-VIDEO 的调用参数，不新增 Skill、Provider、依赖或求解器。
这是用户直接授权的缺陷修复，不是未经确认的 Learning Claim adoption。

当前安装 CLI 0.10.1 的新参数 dry-run 成功，submitted=false、model_verified_live=false，
model=chirp-hawk。2026-10-25T21:27:26Z 的真实只读前检为 ready=true；它只证明当时
认证/API可读且没有验证码要求，不证明纯 CLI 生成已成功，也不证明先前失败只有一个根因。
此为首次只读检查点：当时新增生成0次、积分消费0，尚未获得第4次授权。

## Confirmed Defect And Fix

上游 HEAD 仍为 `6d28c67a733b32183a80d81306bf0013f46b00b7`，许可证 MIT，
Copyright (c) 2026 199 Biotechnologies。直接检查其 `src/main.rs::resolve_captcha`：
当 no_captcha=true 且没有外部token时立即返回(None,None)，跳过captcha_check。
原 Skill 和项目固定添加 --no-captcha，把“跳过前检”误当“禁用自动求解器”。
`src/api/mod.rs::looks_like_auth_expired` 又把一般token validation错误归为AuthExpired，
所以实际auth_expired不能单独定位JWT。没有复制第三方实现或修改安装的二进制。

修复后不生成 --no-captcha，并把它列入适配器禁止参数；所有传输由原 _invoke 固定
加 --json --no-browser。CLI 因而保留原生检查，同时无法自动启动浏览器求解。
此前新增的只读doctor前检仍核验jwt/studio_api/captcha detail；外层success/pass不当生成许可，
积分检查不成为预算gate。已有submitted回放、UNKNOWN拒绝先执行，request identity保持不变。
若doctor之后要求变为true，原生检查仍能在POST前返回captcha_required，记录known_no_effect。

两个Skill原SHA均为d6b6504cab126232a928fa12256da58a48a7b0fcce52a2c7df33417cc586c5b0，
修订后均为897a171b567fab95f616deeb637fcf959c82fe4402ea245126f795f245ffaa14：

- /home/reggie/.agents/skills/suno/SKILL.md
- /home/reggie/.codex/skills/suno/SKILL.md

备份及安装清单位于 /home/reggie/.local/state/ai-video/suno-skill-repair-20261026/。
Skill还明确list才是library查询命令、已有reggie/sunruijie42窗口不能被新自动化会话取代、
正常表单由Agent操作、实际challenge由人处理且不搬运token、网页Create独立计数、
旧UNKNOWN不能因刷新会话/换UUID归零，以及下载/听感证据不能混淆。
外部Skill文件不属于本仓库Git对象；本记录保留实际安装hash和可追踪备份位置。

## REA Evidence Boundary

已读取本机REA的使用边界，并通过现有REA launcher实际调用
list-browser-targets http://127.0.0.1:34537 --json。结果为execution_failure /
unreadable_output / invalid_endpoint_response。没有网页协议捕获，不声称REA证实了请求差异。
没有改REA、MCP配置、浏览器启动参数、代理或账号。源码足以证实参数缺陷，因此继续源码修复，
不为使用工具而安装引擎或逆向验证码。

## Verification And Limits

新增/修订测试先红：2失败，均暴露错误参数；修复后精准37通过，涵盖原生检查保留、
doctor到调用之间要求变化、UNKNOWN及幂等、Clip[]、无预算gate、下载/音频契约与runtime Skill边界。
两个已安装Skill均经skill-creator quick_validate通过。

证据：

- .agent/harness/runs/suno-cli-skill-repair-focused.xml（37项精准JUnit，非完整回归）
- outputs/shizhen-episode01/suno-v6-music-pilot-20261026/cli-skill-repair/verification.json

后者包含当前源码/测试/Skill hash、真实离线CLI结果、只读ready、REA失败和零新增生成。
前次音乐文件仍是官方网页生成的外部候选，不能挂到CLI旧失败UUID，也未登记/激活。
没有新的音乐质量、声画匹配、最终听感或生产验收结论。随后有界真实CLI验证见下节。

Parent Risk Gate：NOT_REQUIRED。新逻辑只增加前检和保留CLI检查，不增加凭据读取、
重试或Production写入，主要失败路径已覆盖；旧review不冒充审过新修改。
自动学习评估no_candidate：一个缺陷的源码/测试/前检是同证据链，没有独立质量对照。

## Live CLI Recovery

用户新增原话“授权我给你,可以继续生成测试”。Parent限定新增1次CLI请求（一次两首），
旧3次消费、STOP与UNKNOWN全部保留，不重提旧UUID，不设积分gate、不自动重试。
新设计为Scene04确认两个无关源的十一秒空白后，由技术确信转向自我怀疑；薄层中提琴泛音、
零星低音单簧管和自由间隙，没有固定BPM/长度/歌曲结构，不上传视频或声音。
该新cue不是对未听A/B的质量修订，也不保证同旋律。原native reviewer仅做新创作概念检查，
finding为空；这是concept check，不是第四轮implementation review，也不是成片审听。

request_id：ebd95316-1986-51d9-8c10-d65b6465b7e2。
generation_identity：8b6e6eff934dcd3972dff8563357ace9e874c240cbd97a2e18b6087490007492。
一次性消费在CLI调用前fsync，exact argv与旧消费hash绑定；guard模拟第二次调用在transport前拒绝。
经真实SunoMusicService.submit及修复后的参数获得两个ID，均complete / chirp-hawk：

- e3599d34-c24a-4750-ad48-69825671da9b：WAV199.2秒。
- 1c3f82de-fa9e-43e7-abf0-e366de84caa9：WAV214.8秒。

CLI status --wait --download及download --format wav成功；四文件完整解码通过。
两份WAV经既有probe_audio_candidate测量，再经music_asset_record生成GENERATED候选AssetRecord，
含真实SHA、sample数、响度、原request_id与generation identity；candidate layout bytes匹配。
这是未提交候选记录，不是canonical Registry登记、activation或QA acceptance。
ClipMetadata读取中tags与本次提交逐字一致，make_instrumental=true；模型落实仍需实际听音。
CLI的ClipMetadata结构本身不暴露negative_tags，字段缺失不能推断服务器丢弃排除项。

真实已提交ledger再经SunoMusicService.submit回放，NoCalls transport观察0调用，返回原两ID。
旧3次消费hash未变，未重复扣费。新增前后余额2490→2480、monthly_usage10→20；
新增消耗10 credits，全部任务累计20 credits，未购买积分。CLI内部HTTP请求数未抓包，
次数口径为logical CLI generation request，不声称只有一个HTTP POST。

证据根：outputs/shizhen-episode01/suno-v6-music-pilot-20261026/cli-repair-live-04/，
含intent/dry-run/consume/submit-result、status-download、audio-validation、candidate-assets、
clip-info、replay-verification、credits-after及执行脚本。四候选试听入口是其上级index.html。
本检查点证明实际CLI接入修复；无对应Scene04成片审听，不证明音乐创作质量、声画适配或生产验收。
工程精准37项通过；关联回归结论以本次最终Harness回执为准，不以局部结果代签整仓。

## Related Verification Blocker

`.agent/harness/runs/suno-cli-skill-repair-related/receipt.json` 的level=related、status=failed：
scope/doc/agent-rules检查通过，在全仓policy_audit_check因既有资格预览/水印模块及其测试缺映射停止，
尚未执行后面的关联suite。相关路径不属于本任务；已通知对应制作窗口协调原owner，不改规则掩盖。
此失败回执绑定的是补写本段之前的文档snapshot；当前Suno源码和测试hash保持相同，不能称最终
整个stage或整仓related通过。已通过37项精准回归、真实CLI执行及文档检查，按此有界状态checkpoint。
正式媒体保留本地输出目录；Git提交的是工程修复、记录和含媒体hash/执行回执hash的证据清单。
