"""Content-addressed authoring input; immutable evidence, never lifecycle state."""
import json
from pathlib import Path

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import SourceReference
from ai_video.production.paths import _read_regular_file_nofollow


PREFIX = "evidence/authoring-input/"


def authoring_input_reference(value):
    digest = canonical_sha256(value)
    return SourceReference(kind="user_input", reference=f"{PREFIX}{digest}.json", content_hash=digest)


def authoring_input_payload(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False) + "\n").encode()


def require_authoring_input(reference, payload):
    if (reference.kind != "user_input" or reference.content_hash is None
            or reference.reference != f"{PREFIX}{reference.content_hash}.json"):
        raise ValueError("authoring input reference is not content addressed")
    value = json.loads(payload)
    if canonical_sha256(value) != reference.content_hash or payload != authoring_input_payload(value):
        raise ValueError("authoring input bytes differ from the selected sealed input")
    return value


def prepared_authoring_input_references(artifacts):
    """Collect sealed import receipts for a Project's source provenance.

    Prepared media bytes alone are insufficient: bootstrap also requires each
    accompanying authoring-input artifact to be referenced by the Project.
    """
    references = []
    for artifact in artifacts:
        path = artifact.relative_path.as_posix()
        if not path.startswith(PREFIX):
            continue
        reference = authoring_input_reference(json.loads(artifact.payload))
        require_authoring_input(reference, artifact.payload)
        if reference.reference != path:
            raise ValueError("asset source evidence path differs from its sealed input")
        if reference not in references:
            references.append(reference)
    return tuple(references)


def reopen_authoring_input(root, reference):
    raw = _read_regular_file_nofollow(Path(root) / reference.reference, contained_by=root)
    return require_authoring_input(reference, raw.data)
