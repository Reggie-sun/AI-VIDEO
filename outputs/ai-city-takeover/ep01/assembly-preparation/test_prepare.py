"""Focused preparation-boundary checks; no Provider or target state."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import prepare
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import DurationPolicy, Shot
from ai_video.production.video_artifact import VideoProbeReceipt


class PreparationBoundaryTests(unittest.TestCase):
    def clone(self, folder):
        target = Path(folder)
        for name in ('registry-candidate.json', 'asset-candidates.json', 'payload-map.json',
                     'qualification-inspections.json', 'composition-inputs.json'):
            shutil.copyfile(prepare.HERE / name, target / name)
        for name in ('prepared-artifacts', 'probe-receipts', 'probe-admission', 'development-measurements', 'shots'):
            source = prepare.HERE / name
            if source.exists():
                shutil.copytree(source, target / name)
        return target

    def test_real_inputs_stay_unready_without_audio_and_admission(self):
        result = prepare.validate()
        self.assertEqual((result['typed_asset_candidates'], result['typed_shot_candidates']), (6, 8))
        self.assertFalse(result['preview_ready'])
        self.assertFalse(result['final_compose_ready'])
        self.assertEqual(result['state_writes'], 0)
        self.assertEqual(len(prepare.prepared_graphics_artifacts()), 8)

    def test_vfr_relabelled_as_30fps_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=prepare.HERE, prefix='.test-') as folder:
            target = self.clone(folder)
            path = target / 'asset-candidates.json'
            values = json.loads(path.read_text())
            video = next(x for x in values if x['asset_id'] == 'iris-assembly-a01-v2')
            video['video_metadata']['fps_numerator'] = 30
            video['video_metadata']['fps_denominator'] = 1
            path.write_text(json.dumps(values))
            with patch.object(prepare, 'HERE', target), self.assertRaisesRegex(ValueError, 'metadata differs'):
                prepare.validate()

    def test_preview_measurement_receipts_do_not_claim_production_pass(self):
        for key in ('a01-v2', 'c'):
            receipt = VideoProbeReceipt.model_validate_json(
                (prepare.HERE / 'probe-receipts' / (key + '.json')).read_bytes())
            scope = json.loads((prepare.HERE / 'development-measurements' / (key + '.json')).read_text())
            strict = json.loads((prepare.HERE / 'probe-admission' / (key + '.json')).read_text())
            self.assertEqual(strict['status'], 'REJECTED')
            self.assertEqual(scope['scope'], 'development_preview_measurement_only')
            self.assertFalse(scope['production_contract_pass'])
            self.assertFalse(scope['nominal_endpoint_recovery_performed'])
            self.assertEqual(scope['existing_preview_probe_validator'], 'PASS')
            self.assertEqual(receipt.measured.frame_count, 145)
            self.assertEqual((receipt.measured.fps_numerator, receipt.measured.fps_denominator), (8700, 361))
            self.assertIsNone(receipt.nominal_endpoint_recovery)

    def test_source_hash_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=prepare.HERE, prefix='.test-') as folder:
            target = self.clone(folder)
            path = target / 'asset-candidates.json'
            values = json.loads(path.read_text())
            values[0]['sha256'] = '0' * 64
            path.write_text(json.dumps(values))
            with patch.object(prepare, 'HERE', target), self.assertRaisesRegex(ValueError, 'Source candidate bytes changed'):
                prepare.validate()

    def test_development_receipt_cannot_be_relabelled_production_pass(self):
        with tempfile.TemporaryDirectory(dir=prepare.HERE, prefix='.test-') as folder:
            target = self.clone(folder)
            path = target / 'development-measurements/a01-v2.json'
            value = json.loads(path.read_text())
            value['production_contract_pass'] = True
            path.write_text(json.dumps(value))
            with patch.object(prepare, 'HERE', target), self.assertRaisesRegex(ValueError, 'measurement scope'):
                prepare.validate()

    def test_fabricated_edit_duration_is_rejected_even_when_sealed(self):
        with tempfile.TemporaryDirectory(dir=prepare.HERE, prefix='.test-') as folder:
            target = self.clone(folder)
            path = target / 'shots/ep01-intro.json'
            shot = Shot.model_validate_json(path.read_bytes())
            changed = seal_artifact(shot.model_copy(update={
                'duration_policy': DurationPolicy(mode='fixed', seconds=3)}))
            path.write_text(changed.model_dump_json())
            with patch.object(prepare, 'HERE', target), self.assertRaisesRegex(ValueError, 'content-driven Shots'):
                prepare.validate()


if __name__ == '__main__':
    unittest.main()
