from ai_video.manifest import (
    RunManifest,
    ShotRecord,
    atomic_write_manifest,
    load_manifest,
    mark_shots_stale,
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


def test_mark_shots_stale_updates_only_requested_successful_records():
    manifest = RunManifest(
        run_id="run_1",
        shots=[
            ShotRecord(shot_id="shot_001", status="succeeded"),
            ShotRecord(shot_id="shot_002", status="succeeded"),
            ShotRecord(shot_id="shot_003", status="succeeded"),
        ],
    )

    updated = mark_shots_stale(manifest, {"shot_002"})

    assert [record.status for record in updated.shots] == ["succeeded", "stale", "succeeded"]
