"""Explicit source-grounded cuts do not fabricate missing causal dimensions."""
import pytest

from ai_video.production.hashing import canonical_sha256
from ai_video.production._sequence_source import causal_state_column_hash, require_causal_columns
from ai_video.production.video_requirement import GenerationIntent, TypedStateReference
from ai_video.production.video_transition import CausalStateChange
from ai_video.production.seedance_source_expression import PreservedSourceExpression


def source_expression(text, *, opening=False, closing=False):
    parts = [{"type": "text", "text": text}]
    proof = {"dimension": "prop_identity", "kind": "quote", "fact": "怪物"}
    return PreservedSourceExpression.model_validate({
        "source_sha256": canonical_sha256({"parts": parts, "implicit_references": []}),
        "parts": parts, "opening": [proof] if opening else [], "closing": [proof] if closing else []})


def changes():
    return (CausalStateChange(dimension="prop_identity", source_close="怪物", target_open="怪物",
                             transition_mode="carry"),)


def test_source_column_is_explicitly_partial_and_default_stays_complete():
    with pytest.raises(ValueError, match="every dimension"):
        causal_state_column_hash(changes(), endpoint="source_close")
    assert causal_state_column_hash(changes(), endpoint="source_close", complete=False) == canonical_sha256(
        {"prop_identity": "怪物"})


@pytest.mark.parametrize("damage", [None, "missing_source", "missing_target", "wrong_fact", "wrong_hash"])
def test_partial_columns_require_both_approved_source_groundings(damage):
    digest = canonical_sha256({"prop_identity": "怪物"})
    source = GenerationIntent(close_state=TypedStateReference(kind="typed_hash", state_hash=digest))
    target = GenerationIntent(open_state=TypedStateReference(kind="typed_hash", state_hash=(
        "b" * 64 if damage == "wrong_hash" else digest)))
    old = source_expression("菱形怪物漂浮在半空", closing=damage != "missing_source")
    new = source_expression("40米高的怪物悬浮", opening=damage != "missing_target")
    edge = changes() if damage != "wrong_fact" else (
        CausalStateChange(dimension="prop_identity", source_close="机器人", target_open="机器人",
                         transition_mode="carry"),)
    call = lambda: require_causal_columns(edge, source, target, source_expression=old,
                                         target_expression=new, partial=True)
    if damage is None:
        call()
    else:
        with pytest.raises(ValueError):
            call()
