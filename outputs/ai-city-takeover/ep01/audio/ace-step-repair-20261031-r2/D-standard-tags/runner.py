"""Execute one sealed local IRIS repair unit through the pinned official API."""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    """Hash exact file bytes without loading large weights into memory."""
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def words(text):
    """Keep verbatim spoken words and punctuation while ignoring section labels and spacing."""
    return re.sub(r"\s+", " ", " ".join(
        line for line in text.splitlines() if not line.strip().startswith("[")
    )).strip()


def main():
    """Validate one-use inputs, generate once, and retain the exact known outcome."""
    intent_path = Path(sys.argv[1]).resolve()
    intent = json.loads(intent_path.read_text())
    folder = intent_path.parent
    if (folder / "consume.json").exists():
        raise SystemExit("Consumed unit: inspect existing outcome; no replay")
    if sha(__file__) != intent["runner_sha256"]:
        raise SystemExit("Runner snapshot changed")
    series_path = Path(intent["series_intent_path"])
    if sha(series_path) != intent["series_intent_sha256"]:
        raise SystemExit("Series identity changed")
    series = json.loads(series_path.read_text())
    ordinal = intent["cumulative_attempt_ordinal"]
    if not series["old_attempts_used"] < ordinal <= series["new_cumulative_ceiling"]:
        raise SystemExit("Attempt ceiling exceeded")
    for prior in intent["predecessor_results"]:
        path = Path(prior["result_path"])
        if sha(path) != prior["result_sha256"]:
            raise SystemExit("Predecessor receipt changed")
        result = json.loads(path.read_text())
        if result.get("success") is not True or not result.get("outputs"):
            raise SystemExit("Predecessor is not a verified successful local outcome")
        for item in result["outputs"]:
            if sha(item["path"]) != item["sha256"]:
                raise SystemExit("Predecessor artifact changed")
    source = Path(intent["source_intent_path"])
    if sha(source) != intent["source_intent_sha256"]:
        raise SystemExit("Original brief changed")
    fields = json.loads(source.read_text())["fields"]
    if hashlib.sha256(fields["lyrics"].encode()).hexdigest() != intent["original_lyrics_sha256"]:
        raise SystemExit("Original lyrics identity changed")
    inputs_path = Path(intent["inputs_path"])
    if sha(inputs_path) != intent["inputs_sha256"]:
        raise SystemExit("Execution input changed")
    inputs = json.loads(inputs_path.read_text())
    if words(inputs["params"]["lyrics"]) != words(fields["lyrics"]):
        raise SystemExit("Spoken words, punctuation, or order changed")
    if inputs["config"]["batch_size"] != 1 or inputs["params"]["duration"] != 30:
        raise SystemExit("Output count or duration changed")
    root = Path(intent["runtime_root"])
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if revision != intent["code_sha"]:
        raise SystemExit("Pinned runtime code changed")
    manifest = json.loads(Path(intent["weights_manifest_path"]).read_text())
    if not manifest.get("all_files_verified") or manifest["revision"] != intent["weights_revision"]:
        raise SystemExit("Pinned weight verification missing")
    model_dir = root / "checkpoints" / intent["selected_dit"]
    if not (model_dir / "config.json").is_file() or not any(model_dir.glob("*.safetensors")):
        raise SystemExit("Selected local model unavailable; automatic download disallowed")

    import torch
    from loguru import logger
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable")
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    print(json.dumps({"event": "initializing", "label": intent["label"],
                      "model": intent["selected_dit"], "use_lm": intent["use_lm"]}), flush=True)
    dit = AceStepHandler()
    message, ready = dit.initialize_service(
        project_root=str(root), config_path=intent["selected_dit"], device="cuda",
        use_flash_attention=False, compile_model=False, offload_to_cpu=False,
        offload_dit_to_cpu=False, quantization=None, use_mlx_dit=False,
    )
    if not ready or not str(dit.device).startswith("cuda"):
        raise RuntimeError(f"DiT initialization failed: {message}")
    lm = None
    if intent["use_lm"]:
        lm = LLMHandler()
        message, ready = lm.initialize(
            checkpoint_dir=str(root / "checkpoints"), lm_model_path="acestep-5Hz-lm-1.7B",
            backend="pt", device="cuda", offload_to_cpu=False, dtype=torch.bfloat16,
        )
        if not ready:
            raise RuntimeError(f"LM initialization failed: {message}")
    params = GenerationParams(**inputs["params"])
    config = GenerationConfig(**inputs["config"])
    if bool(params.thinking) != intent["use_lm"]:
        raise SystemExit("Planning mode does not match sealed selection")
    text, lyric = dit.build_dit_inputs(
        "text2music", None, params.caption, params.lyrics,
        {"bpm": params.bpm, "duration": params.duration,
         "keyscale": params.keyscale, "timesignature": params.timesignature}, params.vocal_language,
    )
    counts = [len(dit.text_tokenizer(t, truncation=False).input_ids) for t in (text, lyric)]
    if counts[0] > 256 or counts[1] > 2048:
        raise SystemExit("Sealed input would be truncated")
    (folder / "token-preflight.json").write_text(json.dumps(
        {"caption_tokens": counts[0], "lyric_tokens": counts[1], "truncation": False}, indent=2) + "\n")
    consume = {"intent_sha256": sha(intent_path), "series_sha256": sha(series_path),
               "cumulative_attempt_ordinal": ordinal, "label": intent["label"],
               "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
               "generation_params": params.to_dict(), "generation_config": config.to_dict(),
               "automatic_retries": 0, "remote_generation_calls": 0}
    with (folder / "consume.json").open("x") as stream:
        json.dump(consume, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"event": "generation_started", "label": intent["label"],
                      "ordinal": ordinal, "use_lm": intent["use_lm"]}), flush=True)
    result = generate_music(dit, lm, params, config, save_dir=str(folder))
    outputs = [{"path": str(Path(a["path"]).resolve()), "sha256": sha(a["path"]),
                "bytes": Path(a["path"]).stat().st_size} for a in result.audios]
    receipt = {"success": result.success, "error": result.error,
               "status_message": result.status_message, "label": intent["label"],
               "intent_sha256": sha(intent_path), "cumulative_attempt_ordinal": ordinal,
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
               "completed_at_utc": datetime.now(timezone.utc).isoformat(),
               "outputs": outputs, "human_listening": "NOT_EVALUATED",
               "remote_generation_calls": 0, "production_state_writes": 0}
    (folder / "result.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"event": "generation_finished", "success": result.success,
                      "label": intent["label"], "outputs": outputs}), flush=True)
    if not result.success or len(outputs) != 1:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
