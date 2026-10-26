import hashlib
from pathlib import Path

import pytest

from ai_video.production.authoring_input import (
    authoring_input_payload,
    authoring_input_reference,
    prepared_authoring_input_references,
)
from ai_video.production.state_commit import PreparedArtifact


def artifact(value, path=None):
    payload = authoring_input_payload(value)
    reference = authoring_input_reference(value)
    return PreparedArtifact(
        relative_path=Path(path or reference.reference),
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def test_import_receipts_become_unique_project_provenance_in_input_order():
    video = {"kind": "canvas-local-video-selection/1", "asset_id": "guide"}
    image = {"kind": "image-selection", "asset_id": "scene"}
    media = artifact({"unrelated": True}, "assets/video/source.mp4")
    assert prepared_authoring_input_references(
        (media, artifact(video), artifact(image), artifact(video))
    ) == (authoring_input_reference(video), authoring_input_reference(image))


def test_import_receipt_path_must_match_its_sealed_content():
    wrong = authoring_input_reference({"asset_id": "other"}).reference
    with pytest.raises(ValueError, match="path differs"):
        prepared_authoring_input_references((artifact({"asset_id": "guide"}, wrong),))


def test_import_receipt_must_keep_canonical_bytes():
    value = {"asset_id": "guide"}
    selected = artifact(value)
    payload = b'{ "asset_id": "guide" }'
    changed = PreparedArtifact(selected.relative_path, payload, hashlib.sha256(payload).hexdigest())
    with pytest.raises(ValueError, match="bytes differ"):
        prepared_authoring_input_references((changed,))
