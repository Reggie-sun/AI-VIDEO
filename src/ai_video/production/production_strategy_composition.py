"""Validate the actual canonical composition against approved component uses."""

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition_contracts import FixedTransform


def _invalid(message):
    return AiVideoError(ErrorCode.COMPOSITION_INVALID, message)


def validate_strategy_composition_uses(bundle, spec):
    from ai_video.production.production_strategy_reader import production_parent_context

    checked = set()
    for child in bundle.shots:
        if child.shot_id not in spec.shot_ids or child.production_lineage is None:
            continue
        lineage = child.production_lineage
        parent, _, _, _ = production_parent_context(bundle, child.shot_id)
        coverage = next(c for c in parent.production_intent.coverage_options
                        if c.coverage_id == lineage.coverage_id)
        unit = next(u for u in coverage.units if u.component_id == lineage.component_id)
        actual = tuple(layer for layer in spec.layers if layer.shot_id == child.shot_id)
        source = lineage.source
        if source is None:
            role = next((r for r in child.required_asset_roles if r.role == "primary_visual"), None)
            if role is None or len(role.asset_ids) != 1:
                raise _invalid("Production component has no completed generated visual.")
            expected = ((role.role, role.asset_ids[0], 0, unit.duration_frames, FixedTransform(), 1000, 0),)
        else:
            expected = tuple((s.role, s.asset_id, s.start,
                s.duration if s.timebase == "frames" else None, s.transform, s.opacity_milli, s.z_index)
                for s in (source, *unit.additional_sources))
        uses = tuple((layer.asset_role, layer.asset_id, layer.trim_start_frame,
            layer.trim_duration_frames, layer.transform, layer.opacity_milli, layer.z_index) for layer in actual)
        if len(uses) != len(expected) or any(use not in uses for use in expected):
            raise _invalid("Actual composition source use differs from approved production lineage.")
        key = (parent.content_hash, coverage.coverage_id)
        if key in checked:
            continue
        checked.add(key)
        unit_ids = tuple(u.shot_id for u in coverage.units)
        present = tuple(shot_id for shot_id in spec.shot_ids if shot_id in unit_ids)
        if present != unit_ids:
            raise _invalid("Composition omits or reorders protected production coverage.")
        positions = [spec.shot_ids.index(shot_id) for shot_id in unit_ids]
        if positions != list(range(positions[0], positions[0] + len(positions))):
            raise _invalid("Composition separates protected production coverage.")
        audio_ids = {a.track.track_id for a in coverage.audio}
        audio = tuple(t for t in spec.audio_tracks if t.track_id in audio_ids or t.shot_id in unit_ids)
        if audio != tuple(a.track for a in coverage.audio):
            raise _invalid("Actual composition audio use differs from approved production coverage.")
        caption_ids = {c.binding_id for c in coverage.captions}
        captions = tuple(c for c in spec.caption_tracks
                         if c.binding_id in caption_ids or c.shot_id in unit_ids)
        if captions != coverage.captions:
            raise _invalid("Actual composition captions differ from approved production coverage.")
