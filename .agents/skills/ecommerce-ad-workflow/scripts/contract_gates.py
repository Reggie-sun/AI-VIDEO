"""Cross-field G0-G7 gates for ecommerce advertising packages."""

from __future__ import annotations

from collections.abc import Iterable

from contract_models import (
    ClaimType,
    EcommerceAdInput,
    EcommerceAdProductionPackage,
)


_REQUIRED_VARIANT_CONSTANTS = frozenset(
    {
        "claim_ledger",
        "cta_destination",
        "delivery_intent",
        "objective",
        "platform_constraints",
        "product_identity",
        "product_truth",
        "rights",
        "unchanged_strategy_fields",
    }
)
_REQUIRED_HOOK_COMPONENT_KINDS = frozenset(
    {"VISUAL", "DIALOGUE_OR_VO", "COPY", "AUDIO"}
)


def validate_input_contract(document: EcommerceAdInput) -> None:
    _validate_product_truth(
        source_assets=document.product.source_assets,
        sources=document.product_truth.sources,
        facts=document.product_truth.facts,
        allowed_claims=document.product_truth.allowed_claims,
        prohibited_claims=document.product_truth.prohibited_claims,
    )


def validate_package_contract(document: EcommerceAdProductionPackage) -> None:
    _validate_product_truth(
        source_assets=document.product_truth.source_assets,
        sources=document.product_truth.sources,
        facts=document.product_truth.facts,
        allowed_claims=document.product_truth.allowed_claims,
        prohibited_claims=document.product_truth.prohibited_claims,
    )
    _validate_claim_ledger(document)
    _validate_product_name(document)
    _validate_hook(document)
    _validate_product_presentation_roles(document)
    _validate_runtime_handoff(document)
    _validate_physical_interaction(document)
    _validate_commercial_copy(document)
    _validate_mechanical_typography(document)
    _validate_audio_coverage(document)
    _validate_dialogue_bindings(document)
    _validate_source_audio(document)
    _validate_cta_brand_closure(document)
    _validate_variants(document)
    _validate_pacing(document)
    _validate_traceability(document)
    if not document.ad_qc_report.ready or document.unresolved_items:
        raise ValueError(
            "ad_qc_blocked: package must close all authoring blockers before readiness"
        )
    if any(item.status == "BLOCKER" for item in document.ad_qc_report.findings):
        raise ValueError(
            "ad_qc_blocked: blocking Ad QC findings prevent package readiness"
        )

def _require_unique(label: str, values: Iterable[str]) -> None:
    materialized = tuple(values)
    if len(materialized) != len(set(materialized)):
        raise ValueError(f"contract_invalid: duplicate {label}")


def _validate_product_truth(
    *,
    source_assets: Iterable[object],
    sources: Iterable[object],
    facts: Iterable[object],
    allowed_claims: Iterable[object],
    prohibited_claims: Iterable[object],
) -> None:
    source_assets = tuple(source_assets)
    sources = tuple(sources)
    facts = tuple(facts)
    allowed_claims = tuple(allowed_claims)
    prohibited_claims = tuple(prohibited_claims)
    _require_unique("source asset_id", (item.asset_id for item in source_assets))
    _require_unique("source_id", (item.source_id for item in sources))
    _require_unique("fact_id", (item.fact_id for item in facts))
    _require_unique("allowed claim_id", (item.claim_id for item in allowed_claims))
    _require_unique(
        "prohibited claim_id", (item.claim_id for item in prohibited_claims)
    )
    allowed_ids = {item.claim_id for item in allowed_claims}
    prohibited_ids = {item.claim_id for item in prohibited_claims}
    if allowed_ids & prohibited_ids:
        raise ValueError(
            "claim_lineage: a claim cannot be both allowed and prohibited"
        )
    if any(item.rights_status != "CONFIRMED" for item in source_assets) or any(
        item.rights_status != "CONFIRMED" for item in sources
    ):
        raise ValueError(
            "rights_not_confirmed: every product asset and truth source requires confirmed rights"
        )
    source_ids = {item.source_id for item in sources}
    facts_by_id = {item.fact_id: item for item in facts}
    for fact in facts:
        _require_unique(
            f"source_id in fact {fact.fact_id}",
            fact.source_ids,
        )
        if not set(fact.source_ids).issubset(source_ids):
            raise ValueError(
                "claim_lineage: product fact references an unknown source"
            )
    for claim in allowed_claims:
        if claim.claim_type is ClaimType.MEDICAL_OR_THERAPEUTIC:
            raise ValueError(
                "medical_claim_forbidden: medical or therapeutic claims are forbidden in V1"
            )
        _require_unique(f"fact_id in claim {claim.claim_id}", claim.fact_ids)
        _require_unique(f"source_id in claim {claim.claim_id}", claim.source_ids)
        if not set(claim.fact_ids).issubset(facts_by_id):
            raise ValueError(
                "claim_lineage: allowed claim references unknown truth evidence"
            )
        supporting_sources = {
            source_id
            for fact_id in claim.fact_ids
            for source_id in facts_by_id[fact_id].source_ids
        }
        if set(claim.source_ids) != supporting_sources:
            raise ValueError(
                "claim_lineage: allowed claim sources must exactly match its fact evidence"
            )


def _validate_claim_ledger(package: EcommerceAdProductionPackage) -> None:
    allowed = {item.claim_id: item for item in package.product_truth.allowed_claims}
    prohibited = {item.claim_id for item in package.product_truth.prohibited_claims}
    _require_unique("claim ledger claim_id", (item.claim_id for item in package.claim_ledger))
    if {item.claim_id for item in package.claim_ledger} != set(allowed) | prohibited:
        raise ValueError(
            "claim_lineage: claim ledger must cover every allowed and prohibited claim exactly once"
        )
    usage_ids = (
        {item.component_id for item in package.hook_contract.components}
        | {item.beat_id for item in package.ad_beats}
        | {item.copy_id for item in package.copy_graphics_plan}
        | {item.event_id for item in package.audio_plan.events}
        | {item.shot_id for item in package.shot_intents}
    )
    for entry in package.claim_ledger:
        if entry.status == "USED":
            truth = allowed.get(entry.claim_id)
            if (
                truth is None
                or entry.claim_id in prohibited
                or not entry.fact_ids
                or not entry.source_ids
                or set(entry.fact_ids) != set(truth.fact_ids)
                or set(entry.source_ids) != set(truth.source_ids)
                or not entry.used_at
                or not set(entry.used_at).issubset(usage_ids)
                or len(entry.used_at) != len(set(entry.used_at))
                or (entry.spoken_form is None and entry.visual_form is None)
            ):
                raise ValueError(
                    "claim_lineage: used claim must bind exact truth, real usage IDs, and a declared form"
                )
        elif entry.status == "NOT_USED":
            truth = allowed.get(entry.claim_id)
            if (
                truth is None
                or set(entry.fact_ids) != set(truth.fact_ids)
                or set(entry.source_ids) != set(truth.source_ids)
                or entry.used_at
                or entry.spoken_form is not None
                or entry.visual_form is not None
            ):
                raise ValueError(
                    "claim_lineage: unused claim must preserve truth lineage without usage forms"
                )
        elif (
            entry.claim_id not in prohibited
            or entry.fact_ids
            or entry.source_ids
            or entry.used_at
            or entry.spoken_form is not None
            or entry.visual_form is not None
        ):
            raise ValueError(
                "claim_lineage: prohibited ledger entry must remain unused and exist in Product Truth"
            )


def _validate_product_name(package: EcommerceAdProductionPackage) -> None:
    product_name = package.product_truth.product_name.casefold()
    visible = any(
        item.role in {"PRODUCT_LABEL", "BRAND_END_CARD"}
        and product_name in item.text.casefold()
        for item in package.copy_graphics_plan
    )
    audible = any(
        item.kind in {"DIALOGUE", "VOICE_OVER"}
        and item.verbatim_line is not None
        and product_name in item.verbatim_line.casefold()
        for item in package.audio_plan.events
    )
    if not visible and not audible:
        raise ValueError(
            "product_name_missing: product name must be visible or audible at least once"
        )


def _validate_hook(package: EcommerceAdProductionPackage) -> None:
    _require_unique(
        "Hook component_id",
        (item.component_id for item in package.hook_contract.components),
    )
    kinds = {item.kind for item in package.hook_contract.components}
    if kinds != _REQUIRED_HOOK_COMPONENT_KINDS:
        raise ValueError(
            "hook_contract: Hook requires visual, dialogue or voice-over, copy, and audio components"
        )
    if not any(item.cue_seconds < 1.0 for item in package.hook_contract.components):
        raise ValueError(
            "hook_first_second: at least one Hook component must be observable before one second"
        )
    used_claims = {
        item.claim_id for item in package.claim_ledger if item.status == "USED"
    }
    if not set(package.hook_contract.promise_claim_ids).issubset(used_claims):
        raise ValueError(
            "claim_lineage: Hook promise must bind used claim ledger entries"
        )
    beats = {item.beat_id for item in package.ad_beats}
    shots = {item.shot_id for item in package.shot_intents}
    copies = {item.copy_id for item in package.copy_graphics_plan}
    dialogue = {
        item.event_id
        for item in package.audio_plan.events
        if item.kind in {"DIALOGUE", "VOICE_OVER"}
    }
    audio = {item.event_id for item in package.audio_plan.events}
    allowed_bindings = {
        "VISUAL": beats | shots,
        "DIALOGUE_OR_VO": dialogue,
        "COPY": copies,
        "AUDIO": audio,
    }
    for component in package.hook_contract.components:
        if not set(component.claim_ids).issubset(used_claims):
            raise ValueError(
                "claim_lineage: Hook component claims must bind used ledger entries"
            )
        if len(component.bound_ids) != len(set(component.bound_ids)) or not set(
            component.bound_ids
        ).issubset(allowed_bindings[component.kind]):
            raise ValueError(
                "hook_contract: each Hook component must bind an exact cue of its declared kind"
            )


def _validate_product_presentation_roles(
    package: EcommerceAdProductionPackage,
) -> None:
    roles = {item.role for item in package.product_presentation}
    if not {"INTRO", "HERO_SHOT", "CTA_SUPPORT"}.issubset(roles) or not roles & {
        "DEMONSTRATION",
        "BENEFIT_PROOF",
    }:
        raise ValueError(
            "product_presentation_roles: product presentation requires intro, demonstration or proof, hero, and CTA support"
        )


def _validate_runtime_handoff(package: EcommerceAdProductionPackage) -> None:
    requirements = {
        item.requirement_id: item for item in package.runtime_handoff.requirements
    }
    gaps = {item.gap_id: item for item in package.runtime_handoff.classified_gaps}
    if len(requirements) != len(package.runtime_handoff.requirements) or len(gaps) != len(
        package.runtime_handoff.classified_gaps
    ):
        raise ValueError(
            "runtime_handoff: requirement and classified-gap IDs must be unique"
        )
    classified_requirement_ids = tuple(
        requirement_id
        for gap in package.runtime_handoff.classified_gaps
        for requirement_id in gap.requirement_ids
    )
    if (
        len(classified_requirement_ids) != len(set(classified_requirement_ids))
        or set(classified_requirement_ids) != set(requirements)
    ):
        raise ValueError(
            "runtime_handoff: every requirement must appear in exactly one classified gap"
        )
    for gap in package.runtime_handoff.classified_gaps:
        if any(
            requirements[requirement_id].classification != gap.classification
            for requirement_id in gap.requirement_ids
        ):
            raise ValueError(
                "runtime_handoff: gap classification must match every bound requirement"
            )


def _validate_physical_interaction(package: EcommerceAdProductionPackage) -> None:
    for item in package.product_presentation:
        if item.mode != "PHYSICAL_INTERACTION_REQUIRED":
            continue
        raise ValueError(
            "blocked_capability_gap: V1 has no authoritative evidence seam for source-generated or Runtime physical interaction"
        )


def _validate_commercial_copy(package: EcommerceAdProductionPackage) -> None:
    roles = {item.role for item in package.copy_graphics_plan}
    if roles == {"DIALOGUE_SUBTITLE"}:
        raise ValueError(
            "commercial_copy_roles: advertising graphics cannot be serialized only as dialogue subtitles"
        )


def _validate_mechanical_typography(package: EcommerceAdProductionPackage) -> None:
    all_shots = {item.shot_id for item in package.shot_intents}
    repeated: dict[tuple[str, str, str], set[str]] = {}
    for item in package.copy_graphics_plan:
        if item.role == "DIALOGUE_SUBTITLE":
            continue
        key = (item.role, item.text, item.treatment_id)
        repeated.setdefault(key, set()).add(item.shot_id)
    if all_shots and any(shots == all_shots for shots in repeated.values()):
        raise ValueError(
            "mechanical_typography: one commercial typography treatment cannot be repeated across every Shot"
        )


def _validate_audio_coverage(package: EcommerceAdProductionPackage) -> None:
    intervals = sorted(
        (item.start_seconds, item.end_seconds) for item in package.audio_plan.events
    )
    cursor = 0.0
    for start, end in intervals:
        if start > cursor + 1e-6:
            raise ValueError(
                "audio_coverage_gap: audio intent must cover the full ad duration"
            )
        cursor = max(cursor, end)
    if cursor < package.duration_seconds - 1e-6:
        raise ValueError(
            "audio_coverage_gap: audio intent must cover the full ad duration"
        )
    for item in package.audio_plan.events:
        if item.end_seconds > package.duration_seconds + 1e-6:
            raise ValueError(
                "audio_coverage_gap: audio event exceeds the ad duration"
            )
        if item.kind == "INTENTIONAL_SILENCE" and item.silence_rationale is None:
            raise ValueError(
                "audio_coverage_gap: intentional silence requires a commercial rationale"
            )


def _validate_dialogue_bindings(package: EcommerceAdProductionPackage) -> None:
    for item in package.audio_plan.events:
        if item.kind == "DIALOGUE" and item.on_camera:
            if (
                item.speaker_id is None
                or item.verbatim_line is None
                or len(item.shot_ids) != 1
                or not item.lip_sync_required
            ):
                raise ValueError(
                    "dialogue_binding: on-camera dialogue requires speaker, exact Shot, verbatim line, and lip-sync requirement"
                )


def _validate_source_audio(package: EcommerceAdProductionPackage) -> None:
    shot_ids = {item.shot_id for item in package.shot_intents}
    policy_shot_ids = tuple(
        item.shot_id for item in package.audio_plan.source_audio_policies
    )
    if len(policy_shot_ids) != len(set(policy_shot_ids)):
        raise ValueError(
            "source_audio_policy: every Shot requires exactly one source-audio policy"
        )
    policies = {item.shot_id: item for item in package.audio_plan.source_audio_policies}
    if set(policies) != shot_ids:
        raise ValueError(
            "source_audio_policy: every Shot requires exactly one source-audio policy"
        )
    for item in policies.values():
        if item.lead_in_noise_risk and (
            item.policy == "KEEP"
            or not item.p6_measurement_required
            or item.measurement_requirement is None
        ):
            raise ValueError(
                "source_audio_policy: noisy lead-in requires mute, replace, or trim plus a P6 measurement requirement"
            )


def _validate_cta_brand_closure(package: EcommerceAdProductionPackage) -> None:
    final_beat = max(package.ad_beats, key=lambda item: item.end_seconds)
    final_shot = max(package.shot_intents, key=lambda item: item.end_seconds)
    copies = {item.copy_id: item for item in package.copy_graphics_plan}
    cta_copy = copies.get(package.cta.cta_copy_id)
    end_card = copies.get(package.cta.end_card_copy_id)
    if (
        cta_copy is None
        or cta_copy.role != "CTA"
        or end_card is None
        or end_card.role != "BRAND_END_CARD"
        or package.cta.beat_id != final_beat.beat_id
        or package.cta.shot_id != final_shot.shot_id
        or cta_copy.beat_id != final_beat.beat_id
        or end_card.beat_id != final_beat.beat_id
        or cta_copy.shot_id != final_shot.shot_id
        or end_card.shot_id != final_shot.shot_id
    ):
        raise ValueError(
            "cta_brand_closure: CTA and brand end card must bind the final beat and Shot"
        )


def _validate_variants(package: EcommerceAdProductionPackage) -> None:
    if (
        package.creative_variant_matrix.master_strategy_id
        != package.ad_strategy.strategy_id
    ):
        raise ValueError(
            "variant_isolation: variant matrix must bind the exact master strategy"
        )
    for item in package.creative_variant_matrix.variants:
        if set(item.held_constants) != _REQUIRED_VARIANT_CONSTANTS:
            raise ValueError(
                "variant_isolation: every creative variant must hold complete master truth constants"
            )
        if item.baseline_value == item.variant_value:
            raise ValueError(
                "variant_isolation: creative variant must change one declared value"
            )


def _validate_pacing(package: EcommerceAdProductionPackage) -> None:
    durations = [item.end_seconds - item.start_seconds for item in package.shot_intents]
    if len(durations) > 1 and max(durations) - min(durations) <= 1e-6:
        if any(
            item.duration_basis != "INTENTIONAL_EQUAL_RHYTHM"
            for item in package.shot_intents
        ):
            raise ValueError(
                "mechanical_pacing: equal Shot durations require an explicit equal-rhythm rationale"
            )


def _require_exact_membership(
    label: str, declared: Iterable[str], expected: set[str]
) -> None:
    materialized = tuple(declared)
    if len(materialized) != len(set(materialized)) or set(materialized) != expected:
        raise ValueError(f"traceability: {label} must match in both directions")


def _validate_traceability(package: EcommerceAdProductionPackage) -> None:
    _require_unique("beat_id", (item.beat_id for item in package.ad_beats))
    _require_unique("shot_id", (item.shot_id for item in package.shot_intents))
    _require_unique(
        "presentation_id", (item.presentation_id for item in package.product_presentation)
    )
    _require_unique("copy_id", (item.copy_id for item in package.copy_graphics_plan))
    _require_unique("audio event_id", (item.event_id for item in package.audio_plan.events))
    _require_unique("storyboard group_id", (item.group_id for item in package.storyboard))
    _require_unique("storyboard beat_id", (item.beat_id for item in package.storyboard))
    _require_unique(
        "Runtime requirement_id",
        (item.requirement_id for item in package.runtime_handoff.requirements),
    )
    beats = {item.beat_id: item for item in package.ad_beats}
    shots = {item.shot_id: item for item in package.shot_intents}
    presentations = {
        item.presentation_id: item for item in package.product_presentation
    }
    copies = {item.copy_id: item for item in package.copy_graphics_plan}
    audio = {item.event_id: item for item in package.audio_plan.events}
    hook_components = {
        item.component_id: item for item in package.hook_contract.components
    }
    product_assets = {
        item.asset_id for item in package.product_truth.source_assets
    }
    requirements = {
        item.requirement_id for item in package.runtime_handoff.requirements
    }
    ordered_beats = sorted(package.ad_beats, key=lambda item: item.start_seconds)
    cursor = 0.0
    for beat in ordered_beats:
        if abs(beat.start_seconds - cursor) > 1e-6:
            raise ValueError(
                "traceability: ad beats must form one contiguous duration budget"
            )
        if abs((beat.end_seconds - beat.start_seconds) - beat.duration_seconds) > 1e-6:
            raise ValueError(
                "traceability: beat duration must match its declared budget"
            )
        cursor = beat.end_seconds
        _require_exact_membership(
            f"beat {beat.beat_id} Shot IDs",
            beat.shot_ids,
            {item.shot_id for item in package.shot_intents if item.beat_id == beat.beat_id},
        )
        _require_exact_membership(
            f"beat {beat.beat_id} presentation IDs",
            beat.presentation_ids,
            {
                item.presentation_id
                for item in package.product_presentation
                if item.beat_id == beat.beat_id
            },
        )
        _require_exact_membership(
            f"beat {beat.beat_id} copy IDs",
            beat.copy_ids,
            {
                item.copy_id
                for item in package.copy_graphics_plan
                if item.beat_id == beat.beat_id
            },
        )
        _require_exact_membership(
            f"beat {beat.beat_id} audio event IDs",
            beat.audio_event_ids,
            {
                item.event_id
                for item in package.audio_plan.events
                if beat.beat_id in item.beat_ids
            },
        )
    if abs(cursor - package.duration_seconds) > 1e-6:
        raise ValueError("traceability: ad beat budgets must equal target duration")
    for shot in package.shot_intents:
        if shot.beat_id not in beats:
            raise ValueError(
                "traceability: every Shot must bind one existing beat"
            )
        _require_exact_membership(
            f"Shot {shot.shot_id} presentation IDs",
            shot.presentation_ids,
            {
                item.presentation_id
                for item in package.product_presentation
                if item.shot_id == shot.shot_id
            },
        )
        _require_exact_membership(
            f"Shot {shot.shot_id} copy IDs",
            shot.copy_ids,
            {
                item.copy_id
                for item in package.copy_graphics_plan
                if item.shot_id == shot.shot_id
            },
        )
        _require_exact_membership(
            f"Shot {shot.shot_id} audio event IDs",
            shot.audio_event_ids,
            {
                item.event_id
                for item in package.audio_plan.events
                if shot.shot_id in item.shot_ids
            },
        )
    for item in package.product_presentation:
        if (
            item.beat_id not in beats
            or item.shot_id not in shots
            or shots[item.shot_id].beat_id != item.beat_id
            or item.product_source_asset_id not in product_assets
            or not set(item.capability_requirement_ids).issubset(requirements)
        ):
            raise ValueError(
                "traceability: product presentation must bind existing product, beat, Shot, and capability evidence"
            )
        if (
            not set(item.copy_cue_ids).issubset(copies)
            or not set(item.audio_cue_ids).issubset(audio)
        ):
            raise ValueError(
                "traceability: product presentation references an unknown cue"
            )
        if any(
            copies[copy_id].beat_id != item.beat_id
            or copies[copy_id].shot_id != item.shot_id
            for copy_id in item.copy_cue_ids
        ) or any(
            item.beat_id not in audio[event_id].beat_ids
            or item.shot_id not in audio[event_id].shot_ids
            for event_id in item.audio_cue_ids
        ):
            raise ValueError(
                "traceability: product presentation cues must bind the same beat and Shot"
            )
    for item in package.copy_graphics_plan:
        if (
            item.beat_id not in beats
            or item.shot_id not in shots
            or shots[item.shot_id].beat_id != item.beat_id
        ):
            raise ValueError(
                "traceability: copy graphic must bind an existing beat and Shot"
            )
        if not set(item.synchronized_event_ids).issubset(
            set(presentations) | set(audio)
        ):
            raise ValueError(
                "traceability: copy graphic references an unknown synchronized event"
            )
        if any(
            (
                event_id in presentations
                and (
                    presentations[event_id].beat_id != item.beat_id
                    or presentations[event_id].shot_id != item.shot_id
                )
            )
            or (
                event_id in audio
                and (
                    item.beat_id not in audio[event_id].beat_ids
                    or item.shot_id not in audio[event_id].shot_ids
                )
            )
            for event_id in item.synchronized_event_ids
        ):
            raise ValueError(
                "traceability: copy synchronization must bind the same beat and Shot"
            )
    for item in package.audio_plan.events:
        if not set(item.beat_ids).issubset(beats) or not set(item.shot_ids).issubset(
            shots
        ):
            raise ValueError(
                "traceability: audio event references an unknown beat or Shot"
            )
        if {
            shots[shot_id].beat_id for shot_id in item.shot_ids
        } != set(item.beat_ids):
            raise ValueError(
                "traceability: audio event beat IDs must exactly match its Shot beats"
            )
        if not set(item.synchronized_event_ids).issubset(
            set(hook_components) | set(presentations) | set(copies)
        ):
            raise ValueError(
                "traceability: audio event references an unknown synchronized event"
            )
    if {item.beat_id for item in package.storyboard} != set(beats):
        raise ValueError(
            "traceability: storyboard must contain every ad beat exactly once"
        )
    for group in package.storyboard:
        _require_exact_membership(
            f"storyboard beat {group.beat_id} Shot IDs",
            group.shot_ids,
            set(beats[group.beat_id].shot_ids),
        )
