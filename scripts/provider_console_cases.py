"""Read-only projection of a small, explicitly pinned set of media cases.

CASE_CATALOG pins evidence identities and source paths. Verdicts below are
derived from the current bytes and their exact artifact bindings.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


_RAW_RUN = "runs/canvas-jieshi-original-s01-s02-20261013-001"
_RAW_PROOF = f"{_RAW_RUN}/official-h3-max-acting-S01-20261020-001"
_CLEAN_RUN = "runs/jieshi-s01-acting-edit-20261020-002"
_ROBOT_RUN = "runs/edit-first-temporal-control-20261017-001/robot-audiovisual-followup-001"
_SEEDANCE_RUN = "runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005"


def _proof(path: str, sha256: str, size: int, kind: str, validator: str, **binding: str) -> dict[str, Any]:
    return {"path": path, "sha256": sha256, "bytes": size, "kind": kind, "validator": validator, **binding}


CASE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "jieshi_s01_raw",
        "title": "《界蚀》S01 原始生成",
        "description": "MiniMax H3 Max CN 的 S01 原始媒体及对应 QA 证据束。",
        "category": "raw_generation",
        "attempt_id": "canvas-81d3a07583cc6684a370e6dc9b729cda828be208",
        "artifact": {
            "path": f"{_RAW_RUN}/production/state/video-generation/fetch/files/4c9589f49dd92104ed6c6a2f5f7ed2f47306535f11a10784d5585ce9652c957f.mp4",
            "sha256": "4c9589f49dd92104ed6c6a2f5f7ed2f47306535f11a10784d5585ce9652c957f",
            "bytes": 7036305,
        },
        "proof_specs": (
            _proof(f"{_RAW_PROOF}/controlled-answers.json", "427497e0bd6966ebba4404e40a2699e36e845e74b5c805facec3fa398ecc9427", 4554, "qa", "raw_answers"),
            _proof(f"{_RAW_PROOF}/controlled-presentation.json", "483d1066bc254a252bd548152c34df514a342c413e128f2b34c62b62518692b1", 1426732, "qa", "raw_presentation"),
            _proof(f"{_RAW_PROOF}/quality-rejection.actual.json", "d5e110470abd0bcabfad97ac3f2ef3383c1642ad75622930ffb925f138395c1c", 637, "record", "raw_rejection"),
        ),
    },
    {
        "id": "jieshi_s01_cleaned_preview",
        "title": "《界蚀》S01 手影清理预览",
        "description": "同一原始 S01 的非生成式清理剪辑预览及范围复核记录。",
        "category": "edited_preview",
        "artifact": {
            "path": f"{_CLEAN_RUN}/outputs/Jieshi-S01-acting-cleaned-v2-3s-preview.mp4",
            "sha256": "f98e2c0ab5198962450a8dca2b7b3a53c133559ebb36c2b6f511700e976f4a47",
            "bytes": 2165551,
        },
        "proof_specs": (
            _proof(f"{_CLEAN_RUN}/render-evidence.json", "70bf1a4dcd62e61133b5c7d4297c56f8d5fcb8e2938a64d13eff02998e88123f", 4473, "artifact", "cleaned_render"),
            _proof(f"{_CLEAN_RUN}/media-review-r4.json", "e1bbd395cfc7eb626f586d243e3975cb2669943feed42ed94d3c1fd5162b8c7c", 1361, "qa", "cleaned_review"),
        ),
    },
    {
        "id": "robot_edited_preview",
        "title": "机器人动作与原声剪辑预览",
        "description": "机器人动作片段的原声剪辑预览及人工 review 记录。",
        "category": "edited_preview",
        "artifact": {
            "path": f"{_ROBOT_RUN}/av-candidate-001/render-001/verified.mp4",
            "sha256": "173cd95b4629c4d758ccf40d7725870cc8f3cca18685695fe4e0d2ef8f2ca5c9",
            "bytes": 698830,
        },
        "proof_specs": (
            _proof(f"{_ROBOT_RUN}/av-candidate-001/render-evidence.json", "cb264c63b33c60798df1d7241dba07fe97d67e456dcf1c83dc8b17ebf59dd7b4", 5323, "artifact", "robot_render"),
            _proof(f"{_ROBOT_RUN}/human-review-001.json", "2c8eb481e08b971a6e4f047409dbed625dcfdddda4c30bc2f8ad852ecb48e5e7", 1109, "human", "robot_human"),
        ),
    },
    {
        "id": "seedance_white_model_example",
        "title": "Seedance 白模动作迁移例",
        "description": "Seedance 机器人白模动作迁移媒体及其逐镜 gate、activation 记录。",
        "category": "production_example",
        "artifact": {
            "path": f"{_SEEDANCE_RUN}/output/seedance-mini-stylized-robot-motion-transfer.mp4",
            "sha256": "127b435cef282fe2b297929013e813e667f1b30b50d1046da0cc043eb2bfc674",
            "bytes": 1762880,
        },
        "proof_specs": (
            _proof(f"{_SEEDANCE_RUN}/evidence/post-media-gate.json", "dae62a7112f4abc587e7bc97ec361c9072aa1121e825c687870b300e97eef2cd", 4447, "qa", "seedance_gate"),
            _proof(f"{_SEEDANCE_RUN}/evidence/activation-report.json", "5a76f6e3b3aedd85f33388d33cefe9013219a4d385ceedf7246478daa1f5a98c", 707, "record", "seedance_activation", gate_path=f"{_SEEDANCE_RUN}/evidence/post-media-gate.json", gate_sha256="dae62a7112f4abc587e7bc97ec361c9072aa1121e825c687870b300e97eef2cd"),
        ),
    },
)

_MAX_JSON_BYTES = 2_000_000
_MAX_MEDIA_BYTES = 256_000_000
_CHUNK_BYTES = 1024 * 1024
_SHA256_LENGTH = 64
_NOFOLLOW = getattr(os, "O_NOFOLLOW", None)
_DIRECTORY = getattr(os, "O_DIRECTORY", None)


class _EvidenceUnavailable(Exception):
    pass


def _valid_identity(path: Any, sha256: Any, size: Any) -> bool:
    return (
        isinstance(path, str)
        and bool(path)
        and not path.startswith("/")
        and "\\" not in path
        and "\x00" not in path
        and all(part not in {"", ".", ".."} for part in path.split("/"))
        and isinstance(sha256, str)
        and len(sha256) == _SHA256_LENGTH
        and all(char in "0123456789abcdef" for char in sha256)
        and isinstance(size, int)
        and not isinstance(size, bool)
        and 0 <= size <= _MAX_MEDIA_BYTES
    )


def _open_beneath(root_fd: int, relative: str) -> int:
    if _NOFOLLOW is None or _DIRECTORY is None:
        raise _EvidenceUnavailable("safe no-follow file opening is unavailable")
    parts = relative.split("/")
    parent_fd = os.dup(root_fd)
    try:
        for index, part in enumerate(parts):
            last = index == len(parts) - 1
            flags = os.O_RDONLY | _NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            if not last:
                flags |= _DIRECTORY
            next_fd = os.open(part, flags, dir_fd=parent_fd)
            if parent_fd != root_fd:
                os.close(parent_fd)
            parent_fd = next_fd
        result = parent_fd
        parent_fd = -1
        if not stat.S_ISREG(os.fstat(result).st_mode):
            os.close(result)
            raise _EvidenceUnavailable("evidence path is not a regular file")
        return result
    except (OSError, ValueError) as exc:
        raise _EvidenceUnavailable("evidence file is missing or unsafe") from exc
    finally:
        if parent_fd not in (-1, root_fd):
            os.close(parent_fd)


def _read_identity(root_fd: int, identity: dict[str, Any], *, keep_bytes: bool) -> tuple[dict[str, Any], bytes | None]:
    path = identity.get("path")
    expected_hash = identity.get("sha256")
    expected_size = identity.get("bytes")
    proof = {
        "path": path if isinstance(path, str) else "",
        "sha256": expected_hash if isinstance(expected_hash, str) else "",
        "bytes": expected_size if isinstance(expected_size, int) and not isinstance(expected_size, bool) else 0,
        "state": "unavailable",
    }
    if not _valid_identity(path, expected_hash, expected_size):
        return proof, None
    maximum = _MAX_JSON_BYTES if keep_bytes else _MAX_MEDIA_BYTES
    if expected_size > maximum:
        return proof, None
    try:
        fd = _open_beneath(root_fd, path)
        try:
            before = os.fstat(fd)
            if before.st_size != expected_size:
                return proof, None
            digest = hashlib.sha256()
            chunks: list[bytes] | None = [] if keep_bytes else None
            total = 0
            while True:
                block = os.read(fd, _CHUNK_BYTES)
                if not block:
                    break
                total += len(block)
                if total > maximum:
                    return proof, None
                digest.update(block)
                if chunks is not None:
                    chunks.append(block)
            after = os.fstat(fd)
            stable = (
                before.st_dev == after.st_dev
                and before.st_ino == after.st_ino
                and before.st_size == after.st_size == total
                and before.st_mtime_ns == after.st_mtime_ns
                and before.st_ctime_ns == after.st_ctime_ns
            )
            if not stable or total != expected_size or digest.hexdigest() != expected_hash:
                return proof, None
            proof["state"] = "verified"
            return proof, b"".join(chunks) if chunks is not None else None
        finally:
            os.close(fd)
    except _EvidenceUnavailable:
        return proof, None


def _json_document(raw: bytes | None) -> dict[str, Any]:
    if raw is None:
        raise _EvidenceUnavailable("evidence JSON is unavailable")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _EvidenceUnavailable("evidence JSON is malformed") from exc
    if not isinstance(value, dict):
        raise _EvidenceUnavailable("evidence JSON has an unsupported shape")
    return value


def _bound_proof(
    documents: dict[str, dict[str, Any]], artifact: dict[str, Any], spec: dict[str, Any]
) -> bool:
    validator = spec["validator"]
    media_sha = artifact["sha256"]
    media_size = artifact["bytes"]
    document = documents[validator]
    if validator == "raw_answers":
        return isinstance(document.get("interaction_ref"), str) and isinstance(document.get("observations"), list)
    if validator == "raw_presentation":
        items = document.get("items")
        analysis = document.get("analysis")
        return (
            isinstance(items, list)
            and len(items) == 15
            and isinstance(analysis, dict)
            and analysis.get("artifact_sha256") == media_sha
            and analysis.get("size_bytes") == media_size
            and all(
                isinstance(item, dict)
                and item.get("artifact_sha256") == media_sha
                and isinstance(item.get("requirement_id"), str)
                for item in items
            )
        )
    if validator == "raw_rejection":
        return (
            document.get("attempt_id") == spec.get("attempt_id")
            and document.get("artifact_sha256") == media_sha
        )
    if validator == "cleaned_render":
        return (
            document.get("file_sha256") == media_sha
            and document.get("size_bytes") == media_size
            and document.get("scope") == "development_preview"
            and document.get("production_acceptance") == "NOT_EVALUATED"
            and document.get("human_full_1x") == "NOT_EVALUATED"
        )
    if validator == "cleaned_review":
        return (
            document.get("artifact_sha256") == media_sha
            and document.get("review_status") == "COMPLETED_SCOPED_MEDIA_REVIEW"
            and document.get("human_full_1x") == "PENDING"
        )
    if validator == "robot_render":
        return (
            document.get("output_sha256") == media_sha
            and document.get("output_size_bytes") == media_size
            and document.get("scope") == "development_preview"
            and document.get("production_acceptance") == "NOT_EVALUATED"
        )
    if validator == "robot_human":
        return (
            document.get("artifact_path") == artifact["path"]
            and document.get("artifact_sha256") == media_sha
            and document.get("playback_rate_requested") == 1.0
            and document.get("user_reported_complete_watch_and_listen") is True
            and document.get("reported_scope") == ["action", "final_turn", "sound"]
            and document.get("reported_verdict") == "ACCEPTABLE"
            and document.get("product_qa_or_activation_written") is False
        )
    if validator == "seedance_gate":
        candidate = document.get("candidate")
        findings = document.get("required_findings")
        return (
            document.get("overall_verdict") == "PASS"
            and isinstance(candidate, dict)
            and candidate.get("path") == artifact["path"]
            and candidate.get("sha256") == media_sha
            and candidate.get("size_bytes") == media_size
            and candidate.get("provider") == "seedance"
            and isinstance(findings, list)
            and len(findings) == 8
            and all(isinstance(item, dict) and item.get("verdict") == "PASS" for item in findings)
        )
    if validator == "seedance_activation":
        return (
            document.get("output_sha256") == media_sha
            and document.get("output_size_bytes") == media_size
            and document.get("gate_path") == spec.get("gate_path")
            and document.get("gate_sha256") == spec.get("gate_sha256")
            and document.get("status") == "activated_after_post_media_gate"
            and document.get("video_phase") == "activate"
        )
    return False


def _unavailable_case(spec: dict[str, Any], artifact: dict[str, Any], proofs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": spec["id"],
        "title": spec["title"],
        "description": spec["description"],
        "category": spec["category"],
        "artifact": artifact,
        "quality": {"state": "unavailable", "pass": 0, "fail": 0, "not_evaluated": 0},
        "human": {"state": "unavailable", "scope": "证据无法核验"},
        "qualification": {"state": "unavailable", "scope": "证据无法核验"},
        "activation": {"state": "unavailable", "scope": "证据无法核验"},
        "proofs": proofs,
    }


def _project_case(root_fd: int, spec: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    expected = spec["artifact"]
    artifact_proof, _ = _read_identity(root_fd, expected, keep_bytes=False)
    artifact = {
        "path": artifact_proof["path"],
        "sha256": artifact_proof["sha256"],
        "bytes": artifact_proof["bytes"],
        "state": artifact_proof["state"],
    }
    proof_rows: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    all_available = artifact["state"] == "verified"
    for proof_spec in spec["proof_specs"]:
        identity = {key: proof_spec.get(key) for key in ("path", "sha256", "bytes")}
        proof, raw = _read_identity(root_fd, identity, keep_bytes=True)
        proof["kind"] = proof_spec.get("kind", "record")
        if proof["state"] == "verified":
            try:
                document = _json_document(raw)
                validator = proof_spec["validator"]
                documents[validator] = document
            except (KeyError, _EvidenceUnavailable):
                proof["state"] = "unavailable"
                all_available = False
        else:
            all_available = False
        proof_rows.append(proof)
    if all_available:
        try:
            for proof_spec in spec["proof_specs"]:
                if not _bound_proof(documents, expected, {**spec, **proof_spec}):
                    all_available = False
                    proof_rows[spec["proof_specs"].index(proof_spec)]["state"] = "unavailable"
            if spec["id"] == "jieshi_s01_raw":
                answers = documents["raw_answers"]
                presentation = documents["raw_presentation"]
                observations = answers["observations"]
                answer_ids = [item.get("requirement_id") for item in observations if isinstance(item, dict)]
                presentation_ids = [item.get("requirement_id") for item in presentation["items"]]
                raw_link_valid = not (
                    answers.get("interaction_ref") != presentation.get("interaction_ref")
                    or len(answer_ids) != 15
                    or len(set(answer_ids)) != 15
                    or set(answer_ids) != set(presentation_ids)
                    or any(item.get("verdict") not in {"PASS", "FAIL", "NOT_EVALUATED"} for item in observations)
                )
                if not raw_link_valid:
                    all_available = False
                    for index, proof_spec in enumerate(spec["proof_specs"]):
                        if proof_spec.get("validator") in {"raw_answers", "raw_presentation"}:
                            proof_rows[index]["state"] = "unavailable"
                elif documents["raw_rejection"].get("artifact_sha256") != expected["sha256"]:
                    all_available = False
        except (KeyError, TypeError):
            all_available = False
    if not all_available:
        return _unavailable_case(spec, artifact, proof_rows), False

    if spec["id"] == "jieshi_s01_raw":
        verdicts = [item["verdict"] for item in documents["raw_answers"]["observations"]]
        quality = {
            "state": "failed" if "FAIL" in verdicts else "bounded",
            "pass": verdicts.count("PASS"),
            "fail": verdicts.count("FAIL"),
            "not_evaluated": verdicts.count("NOT_EVALUATED"),
        }
        human = {"state": "not_evaluated", "scope": "S01 完整 1× 人工听看未评估"}
        activation = {"state": "not_evaluated", "scope": "该失败候选的当前激活状态未从历史项目状态推导"}
    elif spec["id"] == "jieshi_s01_cleaned_preview":
        quality = {"state": "bounded", "pass": 0, "fail": 0, "not_evaluated": 0}
        human = {"state": "not_evaluated", "scope": "完整 1× 人工听看未评估；只有范围有限的画面复核"}
        activation = {"state": "not_evaluated", "scope": "开发预览的 Production 激活未评估"}
    elif spec["id"] == "robot_edited_preview":
        quality = {"state": "not_evaluated", "pass": 0, "fail": 0, "not_evaluated": 0}
        human = {"state": "bounded_acceptance", "scope": "动作、最后转向、声音；用户报告完整 1× 听看"}
        activation = {"state": "not_evaluated", "scope": "人工接受记录未写入 QA 或 activation"}
    else:
        findings = documents["seedance_gate"]["required_findings"]
        quality = {"state": "bounded", "pass": len(findings), "fail": 0, "not_evaluated": 0}
        human = {"state": "not_evaluated", "scope": "未找到完整 1× 人工验收记录"}
        activation = {"state": "recorded", "scope": "历史 activation-report 绑定了同一 MP4 与 post-media Gate"}
    case = {
        "id": spec["id"],
        "title": spec["title"],
        "description": spec["description"],
        "category": spec["category"],
        "artifact": artifact,
        "quality": quality,
        "human": human,
        "qualification": {"state": "not_established", "scope": "所审查的证据束未建立 Production qualification"},
        "activation": activation,
        "proofs": [
            {**proof, "artifact_sha256": expected["sha256"]}
            for proof in proof_rows
        ],
    }
    return case, True


def project_delivery_cases(repo_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Verify and summarize the four pinned case bundles without writing files."""
    cases: list[dict[str, Any]] = []
    all_verified = True
    root_fd = -1
    try:
        root = Path(repo_root).resolve(strict=True)
        if _DIRECTORY is None:
            raise _EvidenceUnavailable("safe directory opening is unavailable")
        root_fd = os.open(root, os.O_RDONLY | _DIRECTORY | getattr(os, "O_CLOEXEC", 0))
        if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
            raise _EvidenceUnavailable("repository root is not a directory")
        for spec in CASE_CATALOG:
            case, verified = _project_case(root_fd, spec)
            cases.append(case)
            all_verified = all_verified and verified
    except (OSError, RuntimeError, _EvidenceUnavailable):
        all_verified = False
        for spec in CASE_CATALOG[len(cases) :]:
            artifact = spec.get("artifact", {})
            artifact_projection = {
                "path": artifact.get("path", "") if isinstance(artifact, dict) else "",
                "sha256": artifact.get("sha256", "") if isinstance(artifact, dict) else "",
                "bytes": artifact.get("bytes", 0) if isinstance(artifact, dict) else 0,
                "state": "unavailable",
            }
            cases.append(_unavailable_case(spec, artifact_projection, []))
    finally:
        if root_fd >= 0:
            os.close(root_fd)
    return {
        "cases": cases,
        "delivery": {
            "state": "not_established_in_reviewed_cases" if all_verified else "unavailable",
            "scope": "selected_case_audit",
            "autonomy": "not_measured",
        },
    }
