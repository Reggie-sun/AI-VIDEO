"""Allow Hero/repair generation only with one measured source-video binding."""


def has_exact_hero_source(mode, roles, assets, *, lineage_current: bool) -> bool:
    if (not lineage_current or getattr(mode, "value", None) not in {"video_edit", "video_extend"}
            or roles != ("reference_video",) or len(assets or ()) != 1):
        return False
    source = assets[0]
    return source.role == "reference_video" and source.mime_type == "video/mp4" and all(
        isinstance(value, int) and not isinstance(value, bool) and value > 0
        for value in (source.size_bytes, source.width, source.height, source.duration_millis, source.fps)
    )
