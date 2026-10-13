# Preserved Source Dialogue Controls

## Goal And Scope

原《界蚀》S01/S02 的原句、窗口与画内/画外、口型字段在 project data 中保留，但 compiler v3 尚未表达这些 typed controls。补通用的、逐字段有原文依据的 source dialogue mapping；不删除字段来通过 coverage，不改时间线、Provider、预算、permit 或验收。

## Contract

仅当 source 中有一行完整匹配 `原生对白约束：普通话；[start–ends]“verbatim”；画内/画外；口型与对白同步/不要求口型同步。` 时，compiler 才可声明相应 `dialogue_intent` scalar control paths。该行是作者声明的自然语言适配，和原对白行并存；编译不得添加或改写原文。支持明确的 `zh`/`zh-CN`；其他语言、缺窗、错字、错窗口、错画内外或错口型声明仍由 existing expression check 拒绝。中文逐字对白的 mode/language 保留已有 compiler v2 同等的映射依据，不泛化 scalar coverage。

`on_screen=None` 不映射画内外；`lip_sync_required=false` 必须有明确不要求口型同步语句，不能推断演员不动嘴。角色不动嘴仍是独立的原剧情 QA。窗口不得超出 request duration；需要 native audio，不能借 source mapping 准许 silent output。

## Invariants And Acceptance

Source parts、hash、参考职责与 immutable lineage 沿既有 owner；不改变 v3 identity 或 schema。所有未表达的其他字段继续 fail closed。此 mapping 只证明输入表达，绝不证明模型发音、语义、窗口、口型或真实听看。原生音轨不得静音、替换或删除，per-shot Gate 仍必需。

针对正例、每个字段的错误/缺失、其他 authored field 与 source bytes preservation 运行 executable tests，原候选重跑 shared inspect/author/preflight 并输出 native-expression diagnostic；qualified runtime prepare 另列当前未验证。

## Self Review

本变更属于用户授权的必要共享适配。映射以 exact same-line declaration 为依据，不能 caller-supplied arbitrary controls 或仅通过对白子串为数字/布尔值签名。独立声音证据缺口不通过此修复关闭。无需新付费授权即可实现与离线验证。
