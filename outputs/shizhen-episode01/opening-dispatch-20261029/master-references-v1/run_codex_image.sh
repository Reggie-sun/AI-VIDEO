#!/usr/bin/env bash
# One bounded Codex built-in image_gen call. Usage: run_codex_image.sh <id> <prompt-file> <ref-desc> [ref1.png ref2.png ...]
# ref-desc: Chinese sentence describing the attached references (参考一/二/三 roles).
set -euo pipefail
id="$1"; prompt="$2"; desc="$3"; shift 3
W=/tmp/codex-master/$id; rm -rf "$W"; mkdir -p "$W/out"
args=(); n=1
for r in "$@"; do cp "$r" "$W/ref$n.png"; args+=(-i "$W/ref$n.png"); n=$((n+1)); done
cat > "$W/task.md" <<TASK
只做一件事：用内置 image_gen 工具生成一张新图片，不做任何其他工作，不读写任何代码仓库。

- ${desc}
- 只调用一次 image_gen，横向宽画幅（尽量十六比九）。失败或结果未知就停止并报告，不重试、不换工具、不改用命令行备用方案。
- 生成后把原始输出文件原样复制到 $W/out/$id.png（不缩放、不重新编码），然后输出：原始生成文件路径、复制后路径、sha256、像素尺寸。

图片提示词（逐字使用，不要改写或翻译）：

$(cat "$prompt")
TASK
codex exec --skip-git-repo-check -C "$W" "${args[@]}" -o "$W/last.txt" "$(cat "$W/task.md")" </dev/null > "$W/log.txt" 2>&1
echo "exit=$?"; cat "$W/last.txt"
