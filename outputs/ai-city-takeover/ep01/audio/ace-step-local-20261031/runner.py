"""Run one sealed IRIS local audition through the pinned ACE-Step Python API."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    """Hash one exact local artifact."""
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    """Initialize the pinned local models and consume one bounded audition."""
    parser = argparse.ArgumentParser()
    parser.add_argument("intent", type=Path)
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    intent = json.loads(args.intent.read_text())
    root = Path(intent["runtime_root"])
    output = args.intent.parent / f"attempt-{args.attempt:02d}"
    output.mkdir(exist_ok=True)
    result_path = output / "result.json"
    if (output / "consume.json").exists():
        raise SystemExit("Attempt already consumed; inspect its existing outcome")
    if args.attempt > 1 and not (args.intent.parent / "attempt-01/result.json").is_file():
        raise SystemExit("Previous generation has no known outcome")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if revision != intent["code_sha"] or digest(__file__) != intent["runner_sha256"]:
        raise SystemExit("Pinned code or runner changed")
    if digest(intent["source_intent_path"]) != intent["source_intent_sha256"]:
        raise SystemExit("Original brief changed")
    fields = json.loads(Path(intent["source_intent_path"]).read_text())["fields"]
    for key, expected in intent["field_sha256"].items():
        if hashlib.sha256(fields[key].encode()).hexdigest() != expected:
            raise SystemExit(f"Original {key} changed")
    manifest = json.loads(Path(intent["weights_manifest_path"]).read_text())
    if not manifest.get("all_files_verified"):
        raise SystemExit("Weight verification incomplete")
    if manifest["revision"] != intent["weights_revision"]:
        raise SystemExit("Weight revision changed")

    import torch
    from loguru import logger
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    logger.remove()
    logger.add(os.sys.stderr, level="WARNING")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable")
    probe = torch.arange(128, device="cuda", dtype=torch.float32)
    if float(probe.sum().item()) != 8128.0:
        raise SystemExit("CUDA arithmetic validation failed")
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    print(json.dumps({"event": "initializing", "device": torch.cuda.get_device_name(0),
                      "torch": torch.__version__, "cuda": torch.version.cuda}), flush=True)
    dit = AceStepHandler()
    message, ready = dit.initialize_service(
        project_root=str(root), config_path="acestep-v15-turbo", device="cuda",
        use_flash_attention=False, compile_model=False, offload_to_cpu=False,
        offload_dit_to_cpu=False, quantization=None, use_mlx_dit=False,
    )
    if not ready or not str(dit.device).startswith("cuda"):
        raise RuntimeError(f"DiT initialization failed: {message}")
    lm = LLMHandler()
    message, ready = lm.initialize(
        checkpoint_dir=str(root / "checkpoints"), lm_model_path="acestep-5Hz-lm-1.7B",
        backend="pt", device="cuda", offload_to_cpu=False, dtype=torch.bfloat16,
    )
    if not ready:
        raise RuntimeError(f"LM initialization failed: {message}")
    caption_input, lyric_input = dit.build_dit_inputs(
        "text2music", None, fields["style"], fields["lyrics"],
        {"bpm": 126, "duration": 30.0, "keyscale": "", "timesignature": "4"}, "en",
    )
    counts = [len(dit.text_tokenizer(text, truncation=False).input_ids)
              for text in (caption_input, lyric_input)]
    if counts[0] > 256 or counts[1] > 2048:
        raise SystemExit("Original input would be truncated")
    (output / "token-preflight.json").write_text(json.dumps(
        {"caption_tokens": counts[0], "caption_limit": 256,
         "lyric_tokens": counts[1], "lyric_limit": 2048, "truncation": False}, indent=2) + "\n")
    seed = intent["seeds"][args.attempt - 1]
    params = GenerationParams(
        task_type="text2music", caption=fields["style"], lyrics=fields["lyrics"],
        instrumental=False, vocal_language="en", bpm=126, timesignature="4",
        duration=30.0, inference_steps=8, seed=seed, thinking=True,
        lm_negative_prompt=fields["exclude"], use_cot_metas=False,
        use_cot_caption=False, use_cot_lyrics=False, use_cot_language=False,
    )
    config = GenerationConfig(batch_size=1, use_random_seed=False,
                              seeds=[seed], audio_format="wav")
    consume = {"intent_sha256": digest(args.intent), "attempt": args.attempt,
               "seed": seed, "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
               "max_outputs": 1, "automatic_retries": 0,
               "generation_params": params.to_dict(), "generation_config": config.to_dict()}
    with (output / "consume.json").open("x") as stream:
        json.dump(consume, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"event": "generation_started", "attempt": args.attempt,
                      "seed": seed, "batch_size": 1, "target_seconds": 30}), flush=True)
    result = generate_music(dit, lm, params, config, save_dir=str(output))
    receipt = {"success": result.success, "error": result.error,
               "status_message": result.status_message, "attempt": args.attempt,
               "seed": seed, "intent_sha256": digest(args.intent),
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
               "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
               "completed_at_utc": datetime.now(timezone.utc).isoformat(),
               "source": "ACE-Step local generation", "outputs": [],
               "human_listening": "NOT_EVALUATED", "production_state_writes": 0}
    for item in result.audios:
        path = Path(item["path"]).resolve()
        receipt["outputs"].append({"path": str(path), "sha256": digest(path),
                                   "bytes": path.stat().st_size})
    result_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"event": "generation_finished", "success": result.success,
                      "receipt": str(result_path), "outputs": receipt["outputs"]}), flush=True)
    if not result.success or len(receipt["outputs"]) != 1:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
