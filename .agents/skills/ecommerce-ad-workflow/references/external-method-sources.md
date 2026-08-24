# External Method Sources

## Use Posture

本 Workflow 只独立重写可验证的方法论；不安装、fork、vendor、submodule 或依赖以下项目，也不运行它们的 Provider、account、campaign、media 或 persistent-profile components。

| Repository URL | License posture in governing spec | Adopted idea, independently rewritten |
| --- | --- | --- |
| https://github.com/tengbot/aiads-skills | 当前未发现明确 license | Hook taxonomy、direct-response sequence、product-benefit-proof、variant dimensions |
| https://github.com/HiAPIAI/awesome-ai-video-workflows | future copied MIT bytes require notice | Product Truth、claim ledger、Shot state、contact/shadow QC、one-variable variants |
| https://github.com/Hainrixz/claude-ads | no reuse license asserted by this Workflow | thin orchestrator、progressive disclosure、typed artifacts、fail-closed aggregation |

URL 仅作为 spec 中 owner/repository identity 的记录，不表示本次联网验证、安装或运行。

## Explicit Exclusions

- `aiads-skills`：不复制六个平级 Skills，不将 UGC testimonial 设为默认路线。
- `awesome-ai-video-workflows`：不采用 Provider execution、installer、parallel storyboard/runtime 或 HiAPI handoff。
- `claude-ads`：不采用 19 Skills + 7 agents、live ad APIs、publishing、budget、performance optimization、persistent user profile 或 media runtime。

## Attribution Rule

本目录当前没有复制上述仓库的文字、模板或代码 bytes；内容均为围绕 governing spec 的独立中文重写。未来只有在复制明确 MIT-licensed bytes 时，才可复制，并必须保留对应 license notice 与 source attribution。无明确许可时只吸收 ideas，不复制表达；不得把 reference 变为 Runtime dependency。

## Quick Reference

| Action | Allowed? |
| --- | --- |
| Independently restate an idea | Yes, with this boundary |
| Copy unlicensed text/template/code | No |
| Copy MIT bytes with notice + attribution | Only if future scope explicitly does so |
| Install, fork, vendor, submodule, execute | No |
