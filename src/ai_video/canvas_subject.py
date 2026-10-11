"""Pure validation for reusable subject material snapshots."""
from __future__ import annotations


def subject_material_references(node: dict) -> dict:
    """Return the exact supported main/auxiliary resource snapshot identities."""
    if not isinstance(node, dict) or node.get("type") != "subject":
        raise ValueError("subject node is required")
    data = node.get("data")
    if not isinstance(data, dict):
        raise ValueError("subject data must be an object")

    seen: set[str] = set()

    def material(value: object, label: str) -> dict:
        if not isinstance(value, dict):
            raise ValueError(f"subject {label} resource snapshot must be an object")
        if value.get("refType") != "resource_snapshot":
            raise ValueError(f"subject {label} reference type is unsupported")
        resource_id = value.get("resourceId")
        if not isinstance(resource_id, str) or not resource_id.strip():
            raise ValueError(f"subject {label} resource identity is missing")
        if resource_id in seen:
            raise ValueError("subject resource snapshot identity is duplicated")
        seen.add(resource_id)
        return {"ref_type": "resource_snapshot", "resource_id": resource_id}

    main = material(data.get("main"), "main")
    raw_auxiliaries = data.get("auxiliaries", [])
    if not isinstance(raw_auxiliaries, list):
        raise ValueError("subject auxiliaries must be a list")
    auxiliaries = [
        {"index": index, **material(item, f"auxiliary {index}")}
        for index, item in enumerate(raw_auxiliaries)
    ]
    return {"main": main, "auxiliaries": auxiliaries}
