"""Core tests for the simulator. No display or Tk root is required."""

import json
import tempfile
import unittest
from pathlib import Path

import simulator as sim


class CallsignTests(unittest.TestCase):
    def test_empty_falls_back_to_default(self):
        self.assertEqual(sim.validate_callsign("   "), ("CADET-X", ""))

    def test_valid_callsign_is_kept(self):
        self.assertEqual(sim.validate_callsign("  BLUE-FIVE  "), ("BLUE-FIVE", ""))

    def test_too_long_is_rejected(self):
        value, error = sim.validate_callsign("A" * 21)
        self.assertIsNone(value)
        self.assertTrue(error)

    def test_bad_character_is_rejected(self):
        for value in ("RED/ONE", "JEDI!", "A.B"):
            callsign, error = sim.validate_callsign(value)
            self.assertIsNone(callsign)
            self.assertTrue(error)


class ScoringTests(unittest.TestCase):
    def test_max_score_includes_performance_bonus(self):
        self.assertEqual(sim.MAX_SCORE, 390)
        choices = sum(max(o["points"] for o in m["options"]) for m in sim.MISSIONS)
        self.assertEqual(sim.MAX_SCORE, choices + 30 * len(sim.MISSIONS))

    def test_rank_thresholds(self):
        self.assertEqual(sim.rank_for(390), "JEDI ACE")
        self.assertEqual(sim.rank_for(350), "JEDI ACE")
        self.assertEqual(sim.rank_for(349), "SQUADRON LEADER")
        self.assertEqual(sim.rank_for(270), "SQUADRON LEADER")
        self.assertEqual(sim.rank_for(190), "SENIOR PILOT")
        self.assertEqual(sim.rank_for(100), "FLIGHT CADET")
        self.assertEqual(sim.rank_for(0), "GROUND CREW")

    def test_each_mission_has_three_difficulty_ranks(self):
        for index, mission in enumerate(sim.MISSIONS):
            ranks = sorted(sim.option_rank(mission, option)
                           for option in mission["options"])
            self.assertEqual(ranks, [0, 1, 2], "mission %d" % index)

    def test_three_missions_and_modes(self):
        self.assertEqual(len(sim.MISSIONS), 3)
        self.assertEqual(sim.FlightScreen.MODES,
                         ("LOAD SEQUENCE", "HOVERSLAM", "DEBRIS RUN"))
        for mission in sim.MISSIONS:
            self.assertEqual(len(mission["options"]), 3)
            self.assertEqual(len(mission["briefing"]), len(mission["briefing"]))


class PilotStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilot.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_file_is_a_clean_start(self):
        store = sim.PilotStore(self.path)
        self.assertEqual((store.best_score, store.flights), (0, 0))
        self.assertEqual(store.last_callsign, "")

    def test_record_persists_and_reloads(self):
        store = sim.PilotStore(self.path)
        self.assertTrue(store.record(245, "BLUE-FIVE", "SENIOR PILOT"))
        self.assertEqual(store.flights, 1)
        reloaded = sim.PilotStore(self.path)
        self.assertEqual(reloaded.best_score, 245)
        self.assertEqual(reloaded.best_rank, "SENIOR PILOT")
        self.assertEqual(reloaded.last_callsign, "BLUE-FIVE")
        self.assertEqual(reloaded.flights, 1)

    def test_lower_score_does_not_replace_record(self):
        store = sim.PilotStore(self.path)
        store.record(300, "A", "SQUADRON LEADER")
        self.assertFalse(store.record(120, "B", "FLIGHT CADET"))
        self.assertEqual(store.best_score, 300)
        self.assertEqual(store.flights, 2)
        self.assertEqual(store.last_callsign, "B")

    def test_corrupt_file_falls_back_safely(self):
        self.path.write_text("{not valid json", encoding="utf-8")
        store = sim.PilotStore(self.path)
        self.assertEqual(store.best_score, 0)
        self.assertEqual(store.flights, 0)

    def test_record_payload_is_json(self):
        store = sim.PilotStore(self.path)
        store.record(210, "GHOST", "SQUADRON LEADER")
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], sim.APP_VERSION)
        self.assertEqual(payload["best_score"], 210)
        self.assertEqual(payload["flights"], 1)


class DebriefTextTests(unittest.TestCase):
    def test_landing_crash_is_not_called_touchdown(self):
        text = sim.OutcomeScreen.stats_text(
            {"mode": "landing", "speed": 21.0, "miss": 40.0, "fuel": 2.0},
            success=False)
        self.assertIn("IMPACT", text)
        self.assertNotIn("TOUCHDOWN", text)

    def test_debris_summary(self):
        text = sim.OutcomeScreen.stats_text(
            {"mode": "debris", "hull": 2, "max_hull": 4, "close": 3})
        self.assertIn("HULL 2/4", text)
        self.assertIn("CLOSE CALLS 3", text)


if __name__ == "__main__":
    unittest.main()
