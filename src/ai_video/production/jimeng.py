"""Jimeng Seedance 2.5 video adapter for the existing P8/paid lifecycle.

The browser transport owns only technical I/O. Product task state, budget,
Registry and acceptance continue through VideoGenerationService and committer.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import BinaryIO, Protocol

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.jimeng_contracts import (
    JIMENG_ORIGIN, JIMENG_PROVIDER, JimengDispatchIntent,
    JimengCanvasSnapshot, JimengMaterial, JimengProfile, JimengSubmitNotDispatched,
)
from ai_video.production.minimax_h3 import _consume_permit, _permit_is_valid
from ai_video.production.paid_provider import (
    JimengAcceptedEffectProof, PaidProviderCallPreview, PaidProviderEgressItem,
    PaidProviderSubmitOutcome,
    validate_paid_provider_authorization,
)
from ai_video.production.video import (
    BillingKind, ResolvedVideoGenerationRequest, VideoCapabilityVariant,
    VideoExecutionKind, VideoFetchReceipt, VideoFlexibleOutputRequirement,
    VideoGenerationMode, VideoGenerationPreview, VideoGenerationRequest,
    VideoMediaCapability, VideoOutputCapability, VideoOutputRecoveryStrategy,
    VideoProviderCapabilities, VideoSubmission, VideoSubmitResult, VideoTaskObservation,
    VideoTaskState, build_video_paid_permit_binding,
)


_MARKER = re.compile(r"\{\{(image|audio|video):([0-9]+)\}\}")
_ANY_MARKER = re.compile(r"\{\{[^{}]*\}\}")
_SAFE_EFFECT = re.compile(r"^[0-9a-f-]{36}:[0-9]{1,32}$")


def _error(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


class JimengTransport(Protocol):
    """A browser-session-backed transport; never returns account credentials."""

    def upload(self, *, profile: JimengProfile, kind: str, payload: bytes,
               mime_type: str) -> str: ...

    def submit_native(self, *, profile: JimengProfile, video_params: dict,
                      materials: tuple[JimengMaterial, ...],
                      admit: Callable[[str, str], None]) -> Mapping[str, object]: ...

    def read_resource(self, *, profile: JimengProfile, resource_id: str) -> Mapping[str, object]: ...

    def read_saved_canvas(self, *, profile: JimengProfile, resource_id: str) -> Mapping[str, object]: ...

    def download(self, *, url: str, sink: BinaryIO) -> tuple[int, str]: ...


def _ordered_bindings(request):
    """Native indices: canonical images, then audios, then videos."""

    return (*request.image_bindings,
            *(x for x in request.media_bindings if x.kind == "audio"),
            *(x for x in request.media_bindings if x.kind == "video"))


def _kind(binding) -> str:
    return getattr(binding, "kind", "image")


def jimeng_meta_list(prompt: str, bindings) -> list[dict[str, object]]:
    """Preserve text and bind every explicit reference to its native index."""

    kinds = tuple(_kind(x) for x in bindings)
    pieces: list[dict[str, object]] = []
    used: set[int] = set()
    cursor = 0
    for match in _MARKER.finditer(prompt):
        if match.start() > cursor:
            pieces.append({"type": 1, "text": prompt[cursor:match.start()]})
        kind, number = match.group(1), int(match.group(2))
        if number >= len(kinds) or kinds[number] != kind:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID,
                         "Jimeng reference marker does not match its native material index.")
        pieces.append({"type": {"image": 2, "video": 3, "audio": 4}[kind],
                       "material_idx": number})
        used.add(number)
        cursor = match.end()
    if cursor < len(prompt):
        pieces.append({"type": 1, "text": prompt[cursor:]})
    if _ANY_MARKER.search("".join(x["text"] for x in pieces if x["type"] == 1)):
        raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng prompt has an invalid reference marker.")
    if used != set(range(len(bindings))):
        raise _error(ErrorCode.VIDEO_REQUEST_INVALID,
                     "Jimeng prompt must bind every material by an exact native index.")
    return pieces


def _validated_resource(resource: Mapping[str, object], intent: JimengDispatchIntent):
    if (resource.get("resource_id") != intent.resource_id
            or resource.get("submit_id") != intent.submit_id
            or resource.get("project_id") not in {None, intent.project_id}):
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng resource identity changed.")
    video = resource.get("video")
    if not isinstance(video, Mapping) or not isinstance(video.get("gen"), Mapping):
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng generation data is missing.")
    gen = video["gen"]
    if canonical_sha256(dict(gen)) != intent.params_sha256:
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng resource parameters changed.")
    task_id = resource.get("task_id")
    if not isinstance(task_id, str) or not task_id.isdecimal():
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng task identity is missing.")
    return video, task_id


class JimengVideoProvider:
    """Explicitly injected P8 adapter; no automatic provider selection."""

    def __init__(self, *, profile: JimengProfile, transport: JimengTransport,
                 reference_resolver: Callable, committer,
                 now: Callable[[], datetime] | None = None):
        self._profile = JimengProfile.model_validate_json(profile.model_dump_json())
        self._transport = transport
        self._reference_resolver = reference_resolver
        self._committer = committer
        self._now = now or (lambda: datetime.now(timezone.utc))

    def capabilities(self) -> VideoProviderCapabilities:
        mini = self._profile.model_id == "seedance_2.0_mini"
        variant = VideoCapabilityVariant(
            capability_id=self._profile.capability_id, provider_kind=JIMENG_PROVIDER,
            model_id=self._profile.model_id, profile_version=self._profile.profile_version,
            execution_kind=VideoExecutionKind.REMOTE, billing_kind=BillingKind.METERED,
            mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
            output_capability=VideoOutputCapability(
                min_duration_seconds=4, max_duration_seconds=15 if mini else 30,
                provider_selected_duration=False, timing_modes=("nominal_seconds",),
                dimension_modes=("adaptive",),
                resolution_labels=("720p",) if mini else ("480p", "720p", "1080p"),
                ratios=("16:9", "9:16", "1:1", "4:3", "3:4"),
                fps_values=(None,), containers=("mp4",), native_audio_options=(True,),
            ),
            allowed_image_roles=("reference",), required_first_frame=False,
            max_reference_count=9 if mini else 30,
            allowed_image_mime_types=("image/png", "image/jpeg", "image/webp"),
            max_image_bytes=(50 if mini else 40) * 1024 * 1024,
            min_image_width=1, min_image_height=1,
            media_capabilities=(
                VideoMediaCapability(kind="audio", roles=("reference_audio",),
                    min_count=0, max_count=3 if mini else 10,
                    allowed_mime_types=("audio/wav", "audio/mpeg", "audio/mp4"),
                    max_size_bytes=(15 if mini else 40) * 1024 * 1024,
                    min_duration_millis=2000 if mini else 1,
                    max_duration_millis=15_000 if mini else 30_200),
                VideoMediaCapability(kind="video", roles=("reference_video",),
                    min_count=0, max_count=3 if mini else 10,
                    allowed_mime_types=("video/mp4", "video/quicktime"),
                    max_size_bytes=(50 if mini else 100) * 1024 * 1024,
                    min_duration_millis=2000 if mini else 1,
                    max_duration_millis=15_400 if mini else 30_200),
            ),
            negative_prompt_supported=False, seed_supported=False, fps_supported=False,
            idempotent_submit=False, lookup_supported=True,
            output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
        )
        return VideoProviderCapabilities.create(provider_name=JIMENG_PROVIDER, variants=(variant,))

    def compile_request(self, provider_bound, requirement, *, continuity_expression=None):
        from ai_video.production._remote_video_native_prompt import (
            RemoteVideoPromptCompilation, compile_remote_video_prompt,
        )
        from ai_video.production.video_compiler import (
            ProviderNativePrompt, ProviderRequirementUnsupported,
            ProviderRequirementUnsupportedReason, compile_provider_video_request,
        )

        if requirement.target_shot.preserved_source_expression is not None:
            return ProviderRequirementUnsupported(
                requirement_hash=requirement.requirement_hash,
                provider_bound_request_hash=provider_bound.provider_bound_request_hash,
                selected_capability_id=provider_bound.capability_id,
                reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
                unsupported_field_paths=("target_shot.preserved_source_expression",),
            )
        prose = compile_remote_video_prompt(requirement,
            provider_bound=provider_bound, continuity_expression=continuity_expression)
        if not isinstance(prose, RemoteVideoPromptCompilation):
            return ProviderRequirementUnsupported(
                requirement_hash=requirement.requirement_hash,
                provider_bound_request_hash=provider_bound.provider_bound_request_hash,
                selected_capability_id=provider_bound.capability_id,
                reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
                unsupported_field_paths=("generation_intent",),
            )
        # Generic Shot prose has no Jimeng markers. The selected compiler
        # makes the reference binding explicit and hash-bound.
        rows = sorted(((role, asset.asset_id)
            for role, asset in zip(provider_bound.binding_roles,
                provider_bound.input_assets, strict=True)
            if role in {"reference", "reference_audio", "reference_video"}),
            key=lambda row: ({"reference": 0, "reference_audio": 1,
                              "reference_video": 2}[row[0]], row[1]))
        markers = "".join(f"\n参考素材{index + 1} {{{{{kind}:{index}}}}}"
            for index, (role, _) in enumerate(rows)
            for kind in ({"reference": "image", "reference_audio": "audio",
                          "reference_video": "video"}[role],))
        prompt = prose.prompt_text + markers
        native = ProviderNativePrompt(grammar_contract="jimeng-explicit-reference-v1",
            prompt_text=prompt,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            expressed_control_paths=prose.expressed_control_paths)
        return compile_provider_video_request(
            provider_bound=provider_bound, requirement=requirement,
            compiler_id=self._profile.compiler_id, compiler_version="1",
            capabilities=self.capabilities(), continuity_expression=continuity_expression,
            native_prompt=native,
        )

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        if (request.provider_name != JIMENG_PROVIDER
                or request.provider_kind != JIMENG_PROVIDER
                or request.model_id != self._profile.model_id
                or request.provider_profile != self._profile.pointer()
                or request.mode is not VideoGenerationMode.REFERENCE_TO_VIDEO
                or request.output_requirement != self._profile.output()
                or request.seed is not None or request.negative_prompt_text
                or request.subject_bindings or request.c4_multi_anchor_binding is not None):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "Jimeng request differs from its selected profile.")
        bindings = _ordered_bindings(request)
        mini = self._profile.model_id == "seedance_2.0_mini"
        if not bindings or len(bindings) > (12 if mini else 50):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "Jimeng reference material count exceeds the selected model bound.")
        if mini and (len(request.prompt_text) > 4000
                or not (request.image_bindings or any(x.kind == "video" for x in request.media_bindings))
                or any(max(x.width, x.height) > 8192 for x in request.image_bindings)
                or any(x.width is None or x.height is None
                       or not (200 <= x.width <= 2160 and 200 <= x.height <= 2160)
                       for x in request.media_bindings if x.kind == "video")):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "Jimeng Mini prompt or reference geometry is unsupported.")
        if sum(x.duration_millis for x in request.media_bindings if x.kind == "audio") > (15_000 if mini else 30_200):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "Jimeng audio reference duration exceeds the selected model bound.")
        if sum(x.duration_millis for x in request.media_bindings if x.kind == "video") > (15_400 if mini else 30_200):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "Jimeng video reference duration exceeds the selected model bound.")
        video_millis = sum(x.duration_millis for x in request.media_bindings if x.kind == "video")
        expected_benefit = self._profile.duration_seconds + (video_millis + 500) // 1000
        if self._profile.benefit_amount != expected_benefit:
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "Jimeng sealed benefit amount differs from the exact input duration.")
        if any(getattr(x, "size_bytes", None) is None for x in bindings):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng references require measured sizes.")
        jimeng_meta_list(request.prompt_text, bindings)
        capability = self.capabilities().variants[0]
        return ResolvedVideoGenerationRequest.create(
            request=request, capability=capability, effective_output=self._profile.output(),
            effective_seed=None, effective_negative_prompt_text="",
        )

    def _validate_resolved(self, request):
        if request.activation_scope is None or self.resolve(request.activation_scope.request) != request:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng resolved request changed.")

    def egress_items(self, request):
        self._validate_resolved(request)
        raw = request.prompt_text.encode("utf-8")
        items = [PaidProviderEgressItem(item_id="prompt", sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw), mime_type="text/plain", purpose="prompt")]
        for binding in _ordered_bindings(request):
            items.append(PaidProviderEgressItem(item_id=binding.asset_id,
                sha256=binding.asset_sha256, size_bytes=binding.size_bytes,
                mime_type=binding.mime_type, purpose="reference"))
        return tuple(items)

    def preview(self, request):
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=self._profile.credit_upper_bound * 1_000_000,
            currency="CRD", destination=JIMENG_ORIGIN,
            egress_item_ids=tuple(x.item_id for x in self.egress_items(request)),
        )

    def _save_canvas(self, intent: JimengDispatchIntent) -> JimengCanvasSnapshot:
        existing = self._committer.read_jimeng_canvas_snapshot(intent.attempt_id, required=False)
        if existing is not None:
            if (existing.dispatch_hash != intent.content_hash
                    or existing.resource_id != intent.resource_id):
                raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                             "Jimeng saved canvas does not match the sealed dispatch.")
            return existing
        try:
            saved = self._transport.read_saved_canvas(
                profile=self._profile, resource_id=intent.resource_id)
            snapshot = JimengCanvasSnapshot.create(
                attempt_id=intent.attempt_id, dispatch_hash=intent.content_hash,
                project_id=intent.project_id, node_id=intent.node_id,
                resource_id=intent.resource_id,
                draft_version=saved["draft_version"],
                head_draft_version=saved["head_draft_version"],
                draft_json=saved["draft_json"], recorded_at=self._now(),
            )
            return self._committer.record_jimeng_canvas_snapshot(snapshot)
        except Exception:
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng canvas save is unconfirmed; query the sealed task only.") from None

    def submit(self, request, video_preview, paid_preview, authorization, permit):
        if video_preview != self.preview(request):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng preview mismatch.")
        if paid_preview is None or authorization is None or permit is None:
            raise _error(ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                         "Jimeng submit requires the shared Paid Provider Gate.")
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        binding = build_video_paid_permit_binding(request, video_preview, paid_preview, authorization)
        if (paid_preview.billing_mode != "remote_metered"
                or paid_preview.secret_reference.kind != "secret_store"
                or paid_preview.secret_reference.reference_id != "JIMENG_BROWSER_SESSION"
                or paid_preview.egress_items != self.egress_items(request)
                or not _permit_is_valid(permit, binding)):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng paid egress or permit mismatch.")
        refs = []
        for index, item in enumerate(_ordered_bindings(request)):
            try:
                payload = self._reference_resolver(item)
            except Exception:
                raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng reference bytes are unavailable.") from None
            if (not isinstance(payload, bytes) or len(payload) != item.size_bytes
                    or hashlib.sha256(payload).hexdigest() != item.asset_sha256):
                raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng reference bytes changed.")
            kind = _kind(item)
            try:
                storage_id = self._transport.upload(profile=self._profile, kind=kind,
                    payload=payload, mime_type=item.mime_type)
            except Exception:
                raise _error(ErrorCode.VIDEO_PROVIDER_FAILED,
                             "Jimeng reference upload did not complete; generation was not submitted.") from None
            if not isinstance(storage_id, str) or not storage_id or len(storage_id) > 512:
                raise _error(ErrorCode.VIDEO_PROVIDER_FAILED,
                             "Jimeng reference upload returned no stable identity.")
            refs.append(JimengMaterial(index=index, kind=kind,
                asset_id=item.asset_id, asset_sha256=item.asset_sha256,
                size_bytes=item.size_bytes,
                duration_millis=getattr(item, "duration_millis", None),
                storage_id=storage_id))
        materials = tuple(refs)
        material_params = []
        for entry in materials:
            if entry.kind == "image":
                material_params.append({"type": 2, "image_uri": entry.storage_id})
            elif entry.kind == "audio":
                material_params.append({"type": 4, "vid": entry.storage_id})
            else:
                material_params.append({"type": 3, "role": 3, "vid": entry.storage_id})
        params = {"mode": 4, "prompt": request.prompt_text,
            "model_name": self._profile.model_id, "aspect_ratio": self._profile.aspect_ratio,
            "resolution": self._profile.resolution,
            "duration_ms": self._profile.duration_seconds * 1000,
            "materials": material_params,
            "meta_list": jimeng_meta_list(request.prompt_text, _ordered_bindings(request))}
        params_hash = canonical_sha256(params)
        try:
            validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        except AiVideoError:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED,
                         "Jimeng authorization expired during reference upload; no generation was submitted.") from None
        if not _consume_permit(permit, binding):
            raise _error(ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                         "Jimeng submit permit was already consumed.")
        admitted = False

        def admit(submit_id: str, resource_id: str) -> None:
            nonlocal admitted
            try:
                validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
            except AiVideoError:
                raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                             "Jimeng authorization expired before native dispatch; keep UNKNOWN.") from None
            if admitted:
                raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                             "Jimeng native submission tried to dispatch twice.")
            intent = JimengDispatchIntent.create(
                attempt_id=paid_preview.attempt_id,
                request_fingerprint=request.resolved_generation_hash,
                preview_fingerprint=paid_preview.preview_fingerprint,
                account_sha256=self._profile.account_sha256,
                project_id=self._profile.project_id,
                node_id=self._profile.node_id,
                submit_id=submit_id, resource_id=resource_id,
                params_sha256=params_hash, materials=materials,
                recorded_at=self._now(),
            )
            self._committer.record_jimeng_dispatch(intent)
            admitted = True

        try:
            ack = self._transport.submit_native(profile=self._profile,
                video_params=params, materials=materials, admit=admit)
        except JimengSubmitNotDispatched:
            if not admitted:
                raise
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng dispatch is sealed; keep UNKNOWN and query only.") from None
        except Exception:
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng submit outcome is unknown; query the sealed resource and never retry.") from None
        if not admitted or not isinstance(ack, Mapping):
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng submit has no sealed dispatch or acknowledgement.")
        intent = self._committer.read_jimeng_dispatch(paid_preview.attempt_id)
        if (ack.get("resource_id") != intent.resource_id
                or ack.get("submit_id") != intent.submit_id
                or not isinstance(ack.get("task_id"), str)
                or not str(ack["task_id"]).isdecimal()):
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng acknowledgement identity is incomplete; query only.")
        self._save_canvas(intent)
        return VideoSubmitResult.create(resolved=request,
            external_effect_id=f"{intent.resource_id}:{ack['task_id']}",
            submitted_at=self._now())

    def _resource(self, submission, receipt):
        effect = receipt.external_effect_id
        if (receipt.outcome.value != "accepted" or not isinstance(effect, str)
                or _SAFE_EFFECT.fullmatch(effect) is None):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng accepted task ID is invalid.")
        resource_id, task_id = effect.split(":", 1)
        intent = self._committer.read_jimeng_dispatch(receipt.attempt_id)
        if (intent.resource_id != resource_id
                or intent.request_fingerprint != receipt.request_fingerprint
                or intent.preview_fingerprint != receipt.preview_fingerprint
                or submission.paid_submit_receipt_fingerprint != receipt.submit_receipt_fingerprint):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng task and paid receipt differ.")
        try:
            resource = self._transport.read_resource(profile=self._profile, resource_id=resource_id)
        except Exception:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng resource query failed.") from None
        video, observed_task_id = _validated_resource(resource, intent)
        if observed_task_id != task_id:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng task ID changed.")
        return resource, video, intent

    def recover_unknown(self, *, attempt_id: str):
        """Read an exact sealed resource once; never submit or mint a permit."""

        manifest = self._committer._read_manifest()
        attempt = self._committer._paid_attempt(manifest, attempt_id)
        state = attempt.paid_provider_state
        if (attempt.status.value != "outcome_unknown" or state is None
                or state.submit_receipt is None or state.phase.value != "outcome_unknown"):
            raise _error(ErrorCode.PRODUCTION_STATE_INVALID,
                         "Jimeng recovery requires one canonical unknown paid attempt.")
        prior = self._committer._reopen_paid_submit(state.submit_receipt)
        if prior.outcome is not PaidProviderSubmitOutcome.OUTCOME_UNKNOWN:
            raise _error(ErrorCode.PRODUCTION_STATE_INVALID,
                         "Jimeng recovery has no exact unknown submit receipt.")
        if manifest.active_paid_provider_budget is None:
            raise _error(ErrorCode.PRODUCTION_STATE_INVALID,
                         "Jimeng recovery has no retained budget reservation.")
        dispatch = self._committer.read_jimeng_dispatch(attempt_id, required=False)
        if dispatch is None:
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng has no sealed resource to query; keep UNKNOWN.")
        if (dispatch.account_sha256 != self._profile.account_sha256
                or dispatch.project_id != self._profile.project_id
                or dispatch.node_id != self._profile.node_id
                or dispatch.request_fingerprint != prior.request_fingerprint):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID,
                         "Jimeng recovery profile or request differs from sealed dispatch.")
        try:
            resource = self._transport.read_resource(profile=self._profile,
                resource_id=dispatch.resource_id)
        except Exception:
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng resource read is unavailable; keep UNKNOWN.") from None
        _, task_id = _validated_resource(resource, dispatch)
        if resource.get("status") not in {200, 1000, 1001}:
            raise _error(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                         "Jimeng resource has no proven accepted task; keep UNKNOWN.")
        self._save_canvas(dispatch)
        proof = JimengAcceptedEffectProof.create(
            request_fingerprint=prior.request_fingerprint,
            preview_fingerprint=prior.preview_fingerprint,
            dispatch_hash=dispatch.content_hash,
            prior_unknown_receipt_fingerprint=prior.submit_receipt_fingerprint,
            base_budget_hash=manifest.active_paid_provider_budget.content_hash,
            account_sha256=dispatch.account_sha256, project_id=dispatch.project_id,
            node_id=dispatch.node_id, submit_id=dispatch.submit_id,
            resource_id=dispatch.resource_id, task_id=task_id,
            params_sha256=dispatch.params_sha256,
            observed_status=resource["status"], observed_at=self._now(),
        )
        self._committer.reconcile_jimeng_unknown(proof)
        reconciled = self._committer._paid_attempt(self._committer._read_manifest(), attempt_id)
        receipt = self._committer._reopen_paid_submit(
            reconciled.paid_provider_state.submit_receipt)
        request = self._committer._reopen_video_request(reconciled.video_generation_state.request)
        return VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=receipt)

    def get_status(self, submission, submit_receipt):
        resource, video, _ = self._resource(submission, submit_receipt)
        status = resource.get("status")
        if status == 200:
            state, progress, file_id = VideoTaskState.RUNNING, 500, None
        elif status == 1001:
            state, progress, file_id = VideoTaskState.FAILED, None, None
        elif status == 1000 and isinstance(video.get("vid"), str) and video["vid"]:
            state, progress, file_id = VideoTaskState.SUCCEEDED, 1000, video["vid"]
        else:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED,
                         "Jimeng resource status is not a verified terminal or running state.")
        return VideoTaskObservation.create(submission=submission, state=state,
            observed_at=self._now(), progress_milli=progress, provider_file_id=file_id)

    def fetch(self, submission, submit_receipt, observation, sink):
        if (observation.state is not VideoTaskState.SUCCEEDED
                or observation.submission_fingerprint != submission.submission_fingerprint
                or observation.paid_submit_receipt_fingerprint
                != submit_receipt.submit_receipt_fingerprint):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng fetch observation is not exact.")
        resource, video, _ = self._resource(submission, submit_receipt)
        if resource.get("status") != 1000 or video.get("vid") != observation.provider_file_id:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng completed result identity changed.")
        url = resource.get("download_url")
        if not isinstance(url, str) or not url:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng completed result has no download URL.")
        try:
            size, digest = self._transport.download(url=url, sink=sink)
        except Exception:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Jimeng result download failed.") from None
        if type(size) is not int or size <= 0 or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise _error(ErrorCode.VIDEO_ARTIFACT_INVALID, "Jimeng download has no verified bytes.")
        return VideoFetchReceipt.create(submission=submission, observation=observation,
            content_type="video/mp4", size_bytes=size, artifact_sha256=digest,
            fetched_at=self._now())


__all__ = ["JimengProfile", "JimengVideoProvider", "JimengTransport", "jimeng_meta_list"]
