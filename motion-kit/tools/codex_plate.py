#!/usr/bin/env python3
"""Generate one plate with the Codex CLI built-in `image_gen` tool.

The exact prompt is read from a fenced ```prompt block in a prompt book (Markdown),
so the text sent to the image model is the sealed text in the book.  Codex runs in
a scratch directory outside the repository (so the repository AGENTS.md is not loaded
and Codex cannot commit), copies the raw output there, and this script verifies the
file, copies it into the project and appends a run record.

Usage:
  python3 motion-kit/tools/codex_plate.py --book PROMPTS.md --plate P1 \
      --dest outputs/<film>/<unit>/plates/raw/P1-a.png --runs outputs/<film>/logs/runs.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import uuid
from pathlib import Path

WRAPPER = """你的唯一任务：调用你内置的 image_gen 工具生成一张图片。
规则：
1. image_gen 的 prompt 参数必须逐字等于下方 <<<PROMPT>>> 与 <<<END>>> 之间的文本，不得增删改、翻译、润色或补充任何内容，也不得加入任何英文。
2. 只调用一次 image_gen。若工具支持尺寸参数，使用 {size}；若不支持，不要设置尺寸。
3. 生成后，用 cp 把 image_gen 保存的原始文件原样复制到：{dest}（不得重新编码、缩放或裁切）。
4. 最后只输出一行 JSON：{{"source_path": "...", "dest_path": "{dest}", "width": 宽, "height": 高, "sha256": "..."}}，用 sha256sum 与 python 计算真实值。
不要执行任何其他操作，不要读取或修改其他目录的文件。
<<<PROMPT>>>
{prompt}
<<<END>>>"""


def read_prompt(book: Path, plate: str) -> str:
    text = book.read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(plate)}\b.*?```prompt\n(.*?)\n```", text, re.S | re.M)
    if not m:
        raise SystemExit(f"prompt block for {plate} not found in {book}")
    return m.group(1).strip()


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    raise SystemExit(f"not a PNG: {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", type=Path, required=True)
    ap.add_argument("--plate", required=True)
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--size", default="2160x3840")
    ap.add_argument("--timeout", type=int, default=1500)
    args = ap.parse_args()

    prompt = read_prompt(args.book, args.plate)
    run_id = f"{args.plate}-{dt.datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    scratch = Path("/tmp/ev-codex") / run_id
    scratch.mkdir(parents=True, exist_ok=False)
    scratch_out = scratch / f"{args.plate}.png"
    instruction = WRAPPER.format(size=args.size, dest=scratch_out, prompt=prompt)
    (scratch / "instruction.txt").write_text(instruction, encoding="utf-8")
    prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    argv = [
        "codex", "exec", "--skip-git-repo-check", "-C", str(scratch),
        "-c", 'approval_policy="never"',
        "-o", str(scratch / "last-message.txt"), "--json", "-",
    ]
    started = dt.datetime.now().isoformat(timespec="seconds")
    with (scratch / "events.jsonl").open("w") as ev, (scratch / "stderr.txt").open("w") as er:
        proc = subprocess.run(argv, input=instruction, text=True, stdout=ev, stderr=er,
                              timeout=args.timeout, check=False)
    finished = dt.datetime.now().isoformat(timespec="seconds")
    record = {"run_id": run_id, "plate": args.plate, "started": started, "finished": finished,
              "exit": proc.returncode, "prompt_sha256": prompt_sha, "scratch": str(scratch),
              "argv": argv}
    if proc.returncode == 0 and scratch_out.exists():
        data = scratch_out.read_bytes()
        record["sha256"] = hashlib.sha256(data).hexdigest()
        record["bytes"] = len(data)
        record["size"] = list(png_size(scratch_out))
        args.dest.parent.mkdir(parents=True, exist_ok=True)
        if args.dest.exists():
            raise SystemExit(f"refusing to overwrite {args.dest}")
        shutil.copyfile(scratch_out, args.dest)
        record["dest"] = str(args.dest)
        record["status"] = "delivered"
    else:
        record["status"] = "no_output"
    with args.runs.open("a", encoding="utf-8") as fh:
        fh.write(f"- `{json.dumps(record, ensure_ascii=False)}`\n")
    print(json.dumps(record, ensure_ascii=False))
    return 0 if record["status"] == "delivered" else 2


if __name__ == "__main__":
    sys.exit(main())
