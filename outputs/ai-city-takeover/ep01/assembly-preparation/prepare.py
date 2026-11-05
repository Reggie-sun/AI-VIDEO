"""Prepare typed local source candidates; no project, timeline or state writes."""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil

from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference, require_authoring_input
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.hyperframes import probe_clip_fd_with_executable
from ai_video.production.models import AssetRecord, AssetRegistrySnapshot, AssetRoleRequirement, DurationPolicy, Shot, VideoAssetMetadata
from ai_video.production.paths import _open_regular_file_nofollow, _read_regular_file_nofollow, canonical_video_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt, probe_generated_video_candidate
from ai_video.production.repair_input_admission import _validate_preview_probe
from ai_video.errors import AiVideoError

HERE = Path(__file__).resolve().parent
EP = HERE.parent
REPO = HERE.parents[3]
DRAFT = EP / 'production-input'
TOOL = {'name': 'iris-local-source-preparation', 'version': '1'}
QUALIFICATION = (
    ('a01-v2', 'a01-first-frame-repair/project', 'iris-ep01-a01-two-reference-repair-002',
     '850b3807757e570dc59c2a6af96fcf930d8689322408e11f1be81db2c5adae1c', 'qa/A01-v2/post-media-gate.json'),
    ('c', 'generation-c-draft/project', 'iris-ep01-c-source-003',
     '974e83c050dd7cc079e6dabdf2ea3b168629d02fffc02cf8163c7881c4968f15', 'qa/C/post-media-gate.json'),
)
PRIMARY = {'ep01-intro': 'a01-v2', 'ep01-dns': 'c', 'ep01-reach': 'dns',
           'ep01-pause': 'pause', 'ep01-web': 'c', 'ep01-chorus': 'b',
           'ep01-cpu': 'cpu-cache', 'ep01-return': 'a01-v2'}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value):
    if hasattr(value, 'model_dump'):
        value = value.model_dump(mode='json')
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def write(name, value):
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def safe_bytes(path):
    return _read_regular_file_nofollow(Path(path), contained_by=REPO).data


def measured_fields(probe):
    videos = [s for s in probe['streams'] if s.get('codec_type') == 'video']
    if len(videos) != 1 or 'mp4' not in probe['format']['format_name'].split(','):
        raise ValueError('Expected one actual MP4 video stream')
    stream = videos[0]
    fps = Fraction(stream['avg_frame_rate'])
    duration = Decimal(stream.get('duration', probe['format']['duration']))
    return {'container_name': 'mp4', 'codec_name': stream['codec_name'],
            'width': int(stream['width']), 'height': int(stream['height']),
            'fps_numerator': fps.numerator, 'fps_denominator': fps.denominator,
            'duration_milliseconds': int((duration * 1000).quantize(Decimal('1'), rounding=ROUND_HALF_UP)),
            'frame_count': int(stream['nb_frames'])}


def probe_local(path, expected, executable):
    with _open_regular_file_nofollow(path, contained_by=REPO) as (fd, opened):
        payload = os.pread(fd, opened.st_size, 0)
        if not 0 < len(payload) <= 50 * 1024 * 1024 or digest(payload) != expected:
            raise ValueError('Selected source bytes differ from their exact identity')
        probe = probe_clip_fd_with_executable(fd, executable)
        if os.pread(fd, opened.st_size, 0) != payload:
            raise ValueError('Selected source changed during measurement')
    return payload, probe


def graph_specs():
    manifest_path = EP / 'graphics/source-assets.json'
    manifest_bytes = safe_bytes(manifest_path)
    manifest = json.loads(manifest_bytes)
    if {i['kind'] for i in manifest['items']} != {'dns', 'pause', 'web-cache', 'cpu-cache'}:
        raise ValueError('Expected the four separate editorial graphics sources')
    for item in manifest['items']:
        review = REPO / item['review_path']
        yield item['kind'], REPO / item['repo_relative_path'], item['sha256'], {
            'origin': 'programmatic_graphics_source', 'source_assets_manifest': str(manifest_path.relative_to(REPO)),
            'source_assets_manifest_sha256': digest(manifest_bytes),
            'review_path': item['review_path'], 'review_sha256': digest(safe_bytes(review)),
            'declared_static_criteria': item['local_static_criteria'],
            'human_acceptance': item['human_acceptance'], 'source_binding': 'director_declared_local_bytes'}


def qualification_specs(executable):
    for key, relative, attempt_id, expected, gate_relative in QUALIFICATION:
        source_root = EP / relative
        loaded = load_production_project(source_root / 'project.yaml')
        attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == attempt_id)
        state = attempt.video_generation_state
        if state is None or state.fetch_receipt is None or attempt.status.value in {'failed', 'outcome_unknown', 'interrupted'}:
            raise ValueError('Qualification source is not an exact known fetched candidate')
        committer = ProductionStateCommitter(source_root)
        request = committer._reopen_video_request(state.request)
        fetch = committer._reopen_video_fetch(state.fetch_receipt)
        source = source_root / state.fetch_receipt.artifact_path
        with _open_regular_file_nofollow(source, contained_by=source_root) as (fd, _):
            payload = os.pread(fd, os.fstat(fd).st_size, 0)
            probe = probe_clip_fd_with_executable(fd, executable)
            fields = measured_fields(probe)
            try:
                _, _, strict_receipt = probe_generated_video_candidate(fd, request, fetch, probe=lambda held: probe)
                admission = {'status': 'PASS', 'receipt_content_hash': strict_receipt.content_hash}
            except AiVideoError as error:
                admission = {'status': 'REJECTED', 'error_code': error.code.value,
                    'reason': error.user_message, 'not_a_canonical_probe_receipt': True}
            # The existing development capture contract binds measured facts,
            # request, fetch and bytes without asserting Production output fit.
            measured = MeasuredVideoMetadata(**fields,
                audio_stream_count=sum(s.get('codec_type') == 'audio' for s in probe['streams']),
                size_bytes=len(payload), artifact_sha256=digest(payload))
            receipt = VideoProbeReceipt.create(request=request, fetch_receipt=fetch, measured=measured)
            _validate_preview_probe(receipt, request=request, fetch=fetch,
                artifact_sha256=expected, size_bytes=len(payload))
            if os.pread(fd, len(payload), 0) != payload:
                raise ValueError('Qualification bytes changed during inspection')
        if digest(payload) != expected or fetch.artifact_sha256 != expected:
            raise ValueError('Qualification capture differs from the selected source')
        write(f'probes/{key}.json', probe)
        write(f'probe-admission/{key}.json', admission)
        write(f'probe-receipts/{key}.json', receipt)
        write(f'development-measurements/{key}.json', {
            'scope': 'development_preview_measurement_only',
            'strict_output_contract': admission['status'],
            'production_contract_pass': False,
            'nominal_endpoint_recovery_performed': False,
            'request_hash': request.resolved_generation_hash,
            'fetch_fingerprint': fetch.fetch_fingerprint,
            'artifact_sha256': expected, 'size_bytes': len(payload),
            'probe_receipt_content_hash': receipt.content_hash,
            'existing_preview_probe_validator': 'PASS'})
        gate_path = EP / gate_relative
        gate = json.loads(safe_bytes(gate_path)) if gate_path.exists() else None
        if gate is not None and gate.get('artifact_sha256') != expected:
            raise ValueError('Gate identifies different source bytes')
        if key == 'a01-v2' and (gate is None or gate.get('verdict') != 'PASS' or not gate.get('all_required_observed_pass')):
            raise ValueError('A01-v2 requires its actual analyzer Gate PASS')
        origin = {'origin': 'paid_qualification_source', 'source_project': str(source_root.relative_to(REPO)),
                  'source_project_hash': loaded.project.content_hash, 'attempt_id': attempt_id,
                  'request_hash': request.resolved_generation_hash,
                  'fetch_fingerprint': fetch.fetch_fingerprint,
                  'probe_receipt_id': receipt.content_hash if receipt else None,
                  'source_contract_probe_admission': admission,
                  'measurement_receipt_scope': 'development_preview_measurement_only',
                  'gate_path': str(gate_path.relative_to(REPO)),
                  'gate_sha256': digest(safe_bytes(gate_path)) if gate else None,
                  'gate_verdict': gate.get('verdict') if gate else 'NOT_EVALUATED',
                  'required_admission': 'prepare_qualification_preview_input',
                  'production_activation': False, 'human_acceptance': 'NOT_EVALUATED'}
        yield key, source, expected, origin, {**fields, 'size_bytes': len(payload)}, receipt


def build():
    executable = Path(shutil.which('ffprobe') or '').resolve(strict=True)
    if executable.name != 'ffprobe':
        raise ValueError('Explicit ffprobe tool is unavailable')
    ffprobe_sha = digest(executable.read_bytes())
    sources = []
    for key, path, expected, origin in graph_specs():
        payload, probe = probe_local(path, expected, executable)
        write(f'probes/{key}.json', probe)
        sources.append((key, path, expected, origin, measured_fields(probe), None, len(payload)))
    for key, path, expected, origin, measured, receipt in qualification_specs(executable):
        fields = {k: measured[k] for k in ('container_name', 'codec_name', 'width', 'height',
                  'fps_numerator', 'fps_denominator', 'duration_milliseconds', 'frame_count')}
        sources.append((key, path, expected, origin, fields, receipt, measured['size_bytes']))
    candidates, registry_assets, payloads, inspections = [], [], [], []
    for key, path, expected, origin, measured, probe_receipt, size in sources:
        facts = {'kind': 'iris-local-source-preparation/1', 'source_key': key,
                 'path': str(path.relative_to(REPO)), 'sha256': expected, 'size_bytes': size,
                 'measurement': measured, 'ffprobe_sha256': ffprobe_sha, 'origin': origin,
                 'adoption': 'NOT_EVALUATED', 'production_activation': False}
        reference = authoring_input_reference(facts)
        receipt_payload = authoring_input_payload(facts)
        target = HERE / 'prepared-artifacts' / reference.reference
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(receipt_payload)
        metadata = VideoAssetMetadata(**measured,
            probe_receipt_id=probe_receipt.content_hash if probe_receipt else 'local-measurement:' + canonical_sha256(facts),
            request_receipt_fingerprint=probe_receipt.request_receipt_fingerprint if probe_receipt else reference.content_hash,
            resolved_generation_hash=probe_receipt.resolved_generation_hash if probe_receipt else reference.content_hash,
            provenance_receipt_id=reference.content_hash)
        record = AssetRecord(asset_id='iris-assembly-' + key, asset_type='video',
            artifact_path=canonical_video_asset_path(expected), sha256=expected, size_bytes=size,
            mime_type='video/mp4', width=metadata.width, height=metadata.height,
            duration_seconds=metadata.duration_milliseconds / 1000, source_kind='imported', tool=TOOL,
            input_fingerprint=reference.content_hash, creation_receipt_id='iris-source-preparation:' + reference.content_hash,
            usage_license='User-authorized project source; platform ownership or adoption is not inferred.',
            video_metadata=metadata)
        candidates.append(record)
        item = {'source_key': key, 'asset_id': record.asset_id, 'source_path': facts['path'],
                'sha256': expected, 'size_bytes': size, 'destination': record.artifact_path.as_posix(),
                'receipt_path': reference.reference, 'receipt_sha256': digest(receipt_payload)}
        if origin['origin'] != 'paid_qualification_source':
            registry_assets.append(record)
            payloads.append(item)
        else:
            inspections.append({**item, 'required_admission': 'prepare_qualification_preview_input',
                'probe_receipt_path': f'probe-receipts/{key}.json' if probe_receipt else None,
                'probe_admission_path': f'probe-admission/{key}.json', 'gate_verdict': origin['gate_verdict'],
                'measurement_scope': 'development_preview_measurement_only',
                'measurement_scope_path': f'development-measurements/{key}.json',
                'source_native_frame_count': metadata.frame_count,
                'preview_trim_guard': 'trim_start_frame + trim_duration_frames <= source_native_frame_count',
                'ordinary_production_30fps_compatible': metadata.fps_numerator == 30 * metadata.fps_denominator,
                'candidate_only': True})
    registry = AssetRegistrySnapshot(schema_version='2.2', revision_id='0' * 64, content_hash='0' * 64,
                                     assets=tuple(sorted(registry_assets, key=lambda a: a.asset_id)))
    identity = registry_semantic_sha256(registry)
    registry = AssetRegistrySnapshot.model_validate({**registry.model_dump(mode='python'),
        'revision_id': identity, 'content_hash': identity})
    write('asset-candidates.json', [v.model_dump(mode='json') for v in candidates])
    write('registry-candidate.json', registry)
    write('payload-map.json', payloads)
    write('qualification-inspections.json', inspections)
    by_key = {k: next(a.asset_id for a in candidates if a.asset_id == 'iris-assembly-' + k) for k, *_ in sources}
    proposal = {'scope': 'development_audio_preview_inputs_only', 'actual_adoption': False,
        'song': None, 'audio_tracks': [], 'caption_tracks': [], 'trim_choices': {}, 'roles': []}
    for path in sorted(DRAFT.glob('shot-*.json')):
        shot = Shot.model_validate_json(path.read_bytes())
        if not verify_artifact_hash(shot):
            raise ValueError('Original Shot draft hash changed')
        key = PRIMARY[shot.shot_id]
        # Qualification clips stay unbound until the existing preview admission is sealed.
        role_ids = (by_key[key],) if key in {'dns', 'pause', 'cpu-cache'} else ()
        roles = [AssetRoleRequirement(role='primary_visual', asset_ids=role_ids, allowed_asset_types=('video',))]
        if shot.shot_id == 'ep01-web':
            roles.append(AssetRoleRequirement(role='editorial_explanation',
                asset_ids=(by_key['web-cache'],), allowed_asset_types=('video',)))
        candidate = seal_artifact(shot.model_copy(update={'revision': shot.revision + 1,
            'creation_receipt_id': 'iris-assembly-authoring-candidate',
            'duration_policy': DurationPolicy(mode='content_driven'), 'required_asset_roles': tuple(roles)}))
        write('shots/' + shot.shot_id + '.json', candidate)
        proposal['roles'].append({'shot_id': shot.shot_id, 'primary_source_key': key,
            'candidate_asset_id': by_key.get(key), 'source_audio_policy': 'MUTE',
            'final_duration_seconds': None, 'trim_choice': None, 'adoption': 'NOT_EVALUATED'})
    write('composition-inputs.json', proposal)
    return validate()


def validate():
    registry = AssetRegistrySnapshot.model_validate_json((HERE / 'registry-candidate.json').read_bytes())
    if registry_semantic_sha256(registry) != registry.content_hash:
        raise ValueError('Candidate Registry content hash changed')
    candidates = [AssetRecord.model_validate(v) for v in json.loads((HERE / 'asset-candidates.json').read_text())]
    if len(candidates) != 6 or len(registry.assets) != 4:
        raise ValueError('Expected four ordinary graphics and two qualification inspection candidates')
    payloads = json.loads((HERE / 'payload-map.json').read_text())
    inspections = json.loads((HERE / 'qualification-inspections.json').read_text())
    by_id = {a.asset_id: a for a in candidates}
    for item in [*payloads, *inspections]:
        record = by_id[item['asset_id']]
        raw = safe_bytes(REPO / item['source_path'])
        if digest(raw) != item['sha256'] or len(raw) != item['size_bytes'] or record.sha256 != item['sha256']:
            raise ValueError('Source candidate bytes changed')
        payload = (HERE / 'prepared-artifacts' / item['receipt_path']).read_bytes()
        reference = authoring_input_reference(json.loads(payload))
        facts = require_authoring_input(reference, payload)
        if reference.reference != item['receipt_path'] or digest(payload) != item['receipt_sha256']:
            raise ValueError('Source receipt changed')
        measured = {key: getattr(record.video_metadata, key) for key in facts['measurement']}
        if measured != facts['measurement'] or record.input_fingerprint != reference.content_hash:
            raise ValueError('Typed video metadata differs from measured source facts')
        if item in inspections:
            if item['probe_receipt_path'] is not None:
                probe = VideoProbeReceipt.model_validate_json((HERE / item['probe_receipt_path']).read_bytes())
                scope = json.loads((HERE / item['measurement_scope_path']).read_text())
                if (scope['scope'] != 'development_preview_measurement_only'
                        or scope['production_contract_pass'] is not False
                        or scope['nominal_endpoint_recovery_performed'] is not False
                        or probe.nominal_endpoint_recovery is not None):
                    raise ValueError('Development measurement scope cannot claim Production fit or recovery')
                if (probe.measured.artifact_sha256 != record.sha256
                        or probe.measured.frame_count != record.video_metadata.frame_count
                        or probe.content_hash != record.video_metadata.probe_receipt_id
                        or probe.resolved_generation_hash != facts['origin']['request_hash']
                        or probe.fetch_fingerprint != facts['origin']['fetch_fingerprint']
                        or scope['probe_receipt_content_hash'] != probe.content_hash):
                    raise ValueError('Qualification probe does not bind the exact media')
            elif json.loads((HERE / item['probe_admission_path']).read_text())['status'] != 'REJECTED':
                raise ValueError('Missing canonical probe must retain its rejection')
            if record.asset_id in {a.asset_id for a in registry.assets}:
                raise ValueError('Qualification inspection was incorrectly admitted as an ordinary source')
    if any(asset != by_id.get(asset.asset_id) for asset in registry.assets):
        raise ValueError('Registry candidate differs from its measured AssetRecord')
    shots = [Shot.model_validate_json(p.read_bytes()) for p in sorted((HERE / 'shots').glob('*.json'))]
    if len(shots) != 8 or any(not verify_artifact_hash(s) or s.duration_policy.mode != 'content_driven'
                             or s.duration_policy.seconds is not None for s in shots):
        raise ValueError('Eight sealed content-driven Shots without fake edit timing are required')
    result = {'typed_asset_candidates': len(candidates), 'ordinary_graphics_registry_candidates': len(registry.assets),
        'qualification_inspection_candidates': len(inspections), 'typed_shot_candidates': len(shots),
        'source_bytes_and_receipts': 'PASS', 'source_audio_policy': 'MUTE',
        'preview_ready': False, 'final_compose_ready': False, 'state_writes': 0, 'provider_calls': 0,
        'missing': ['Actual selected Suno audio asset and source receipt',
            'B singing source and its exact lip-sync/raw-media Gate',
            'Measured song-led trim/duration choices for all eight Shots and subtitle timing',
            'Target project identity and sealed qualification preview admission for A/C',
            'Actual P4 audio tracks and required preview/narration constraints',
            'Canonical bootstrap/adoption and sole ResolvedTimeline resolution'],
        'production_blockers': ['A/C native rational FPS must not be relabeled as 30fps',
            'Strict Production output contract remains REJECTED; development measurement receipt is not a Production PASS',
            'Qualification capture does not promote Provider or Production acceptance']}
    if any(item['source_key'] == 'c' and item['gate_verdict'] != 'PASS' for item in inspections):
        result['missing'].append('C final exact raw-media Gate before selection')
    return result


def prepared_graphics_artifacts():
    """Return actual bytes for the future committer, without writing target state."""
    validate()
    result = []
    for item in json.loads((HERE / 'payload-map.json').read_text()):
        media = safe_bytes(REPO / item['source_path'])
        receipt = (HERE / 'prepared-artifacts' / item['receipt_path']).read_bytes()
        result.extend((PreparedArtifact(Path(item['destination']), media, item['sha256']),
                       PreparedArtifact(Path(item['receipt_path']), receipt, item['receipt_sha256'])))
    return tuple(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'validate'))
    parser.add_argument('--require-preview-ready', action='store_true')
    args = parser.parse_args()
    try:
        result = build() if args.action == 'build' else validate()
        if args.action == 'build':
            write('validation.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.require_preview_ready else 0
    except AiVideoError as error:
        print(json.dumps({'status': 'invalid', 'error_code': error.code.value,
                          'error': error.user_message}, ensure_ascii=False))
        return 2
    except (ValueError, OSError, StopIteration) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
