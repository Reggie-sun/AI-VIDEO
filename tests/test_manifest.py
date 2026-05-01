from ai_video.manifest import (
    RunManifest,
    ShotRecord,
    atomic_write_manifest,
    load_manifest,
    successful_shot_is_valid,
)


def test_atomic_write_and_load_manifest(tmp_path):
    manifest = RunManifest(run_id="run_1", status="running")
    path = tmp_path / "manifest.json"
    atomic_write_manifest(path, manifest)
    loaded = load_manifest(path)
    assert loaded.run_id == "run_1"
    assert loaded.status == "running"


def test_successful_shot_validates_hashes(tmp_path):
    clip = tmp_path / "clip.mp4"
    frame = tmp_path / "last.png"
    clip.write_bytes(b"clip")
    frame.write_bytes(b"frame")
    record = ShotRecord.succeeded(
        shot_id="shot_001",
        seed=100,
        clip_path=clip,
        last_frame_path=frame,
        chain_input_hash=None,
        character_ref_hashes={"hero": "abc"},
    )
    assert successful_shot_is_valid(record) is True
    clip.write_bytes(b"changed")
    assert successful_shot_is_valid(record) is False
