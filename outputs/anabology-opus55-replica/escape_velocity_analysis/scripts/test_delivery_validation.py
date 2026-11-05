"""Failure-path tests for delivery integrity; synthetic fixtures are not media proof."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("delivery", Path(__file__).with_name("15_validate_delivery.py"))
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class DeliveryChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for folder in ("work", "shots"):
            (self.root / folder).mkdir()
        for name in delivery.REQUIRED_DOCS:
            (self.root / name).write_text("fixture")
        s = dict(shot_id="S0001", start_frame=0, end_frame=1, duration_frames=2)
        self.put("work/shots.json", [s])
        record = dict(**s, analysis_status="DETAILED_VISUAL_REVIEW",
                      start_time=0, end_time=2/24, start_tc="00:00:00:00", end_tc="00:00:00:01",
                      scene_type="graphic", confidence=.7, visual_complexity=dict(level="low"),
                      transitions=dict(**{"in": dict(type="start"), "out": dict(type="end")}),
                      elements=[dict(element_id="S0001-E01", description="original")], audio_events=[], in_shot_events=[])
        self.put("shots/shot_0001.json", record)
        self.put("manifest.json", dict(source_video=dict(video=dict(nb_frames_decoded=2, fps=24))))
        entry = {k: record[k] for k in ("shot_id", "start_frame", "end_frame", "duration_frames", "start_time", "end_time", "start_tc", "end_tc", "scene_type", "confidence")}
        entry.update(visual_complexity="low", transition_in="start", transition_out="end", n_elements=1, n_audio_events=0,
                     file="shots/shot_0001.json", md="shots/shot_0001.md", contactsheet="contactsheets/S0001.jpg")
        self.put("timeline.json", dict(shots=[entry], in_shot_events=[], audio_sections=[dict(start_s=0, end_s=2/24)]))
        self.put("elements.json", dict(elements=record["elements"]))
        self.put("visual_system.json", {})
        self.put("source_mapping.json", dict(sources=[]))
        self.put("synchronization.json", dict(events=[]))
        self.put("audio_timeline.json", dict(events=[], sections=[dict(start_s=0, end_s=2/24)],
                                            duration_s=2/24, coverage=dict(perceptual_listening="COMPLETE")))

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def test_complete_fixture_and_missing_top_level(self):
        self.assertEqual(delivery.assess(self.root)["status"], "REVIEW_COVERAGE_COMPLETE")
        (self.root / "audio_timeline.json").unlink()
        self.assertEqual(delivery.assess(self.root)["status"], "INVALID_PACKAGE")

    def test_schema_valid_partial_is_not_complete(self):
        p = self.root / "shots/shot_0001.json"
        s = json.loads(p.read_text())
        s["analysis_status"] = "PARTIAL_VISUAL_ANALYSIS"
        self.put("shots/shot_0001.json", s)
        r = delivery.assess(self.root)
        self.assertFalse(r["errors"])
        self.assertEqual(r["status"], "ANALYSIS_INCOMPLETE")

    def test_aggregate_duplicate_rejected(self):
        self.put("elements.json", dict(elements=[dict(element_id="S0001-E01")]*2))
        self.assertEqual(delivery.assess(self.root)["status"], "INVALID_PACKAGE")

    def test_same_element_id_with_changed_payload_rejected(self):
        data = json.loads((self.root / "elements.json").read_text())
        data["elements"][0]["description"] = "stale aggregate"
        self.put("elements.json", data)
        self.assertEqual(delivery.assess(self.root)["status"], "INVALID_PACKAGE")

    def test_same_timeline_ids_with_changed_metadata_rejected(self):
        original = json.loads((self.root / "timeline.json").read_text())
        for key, value in (("scene_type", "stale"), ("n_audio_events", 12), ("confidence", .1)):
            with self.subTest(key=key):
                data = json.loads(json.dumps(original))
                data["shots"][0][key] = value
                self.put("timeline.json", data)
                self.assertEqual(delivery.assess(self.root)["status"], "INVALID_PACKAGE")

    def test_timeline_events_or_audio_sections_drift_rejected(self):
        original = json.loads((self.root / "timeline.json").read_text())
        for key in ("in_shot_events", "audio_sections"):
            with self.subTest(key=key):
                data = json.loads(json.dumps(original))
                data[key] = [dict(stale=True)]
                self.put("timeline.json", data)
                self.assertEqual(delivery.assess(self.root)["status"], "INVALID_PACKAGE")

    def test_base_validator_failure_never_looks_complete(self):
        r = delivery.assess(self.root, ["validate_all.py failed: dangling animation target"])
        self.assertEqual(r["status"], "INVALID_PACKAGE")
        self.assertTrue(r["errors"])

    def test_audio_time_and_dangling_shot_rejected(self):
        a = json.loads((self.root / "audio_timeline.json").read_text())
        a["events"] = [dict(event_id="A1", start_s=2, end_s=3, start_frame=0, end_frame=1, shot_ids=["S0002"])]
        self.put("audio_timeline.json", a)
        r = delivery.assess(self.root)
        self.assertGreaterEqual(len(r["errors"]), 2)


if __name__ == "__main__":
    unittest.main()
