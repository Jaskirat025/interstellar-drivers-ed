"""Headless tests for the chart-ready debrief metrics."""

import unittest

from dataviz import Metric, score_metrics, telemetry_metrics


class MetricTests(unittest.TestCase):
    def test_fraction_is_clamped_and_safe(self):
        self.assertEqual(Metric("A", 12, 0, "12").fraction, 0.0)
        self.assertEqual(Metric("A", -4, 20, "-4").fraction, 0.0)
        self.assertEqual(Metric("A", 40, 20, "40").fraction, 1.0)
        self.assertAlmostEqual(Metric("A", 10, 20, "10").fraction, 0.5)
        self.assertEqual(Metric("A", 10, 20, "10", target=5).target_fraction, 0.25)
        self.assertIsNone(Metric("A", 10, 20, "10").target_fraction)


class TelemetryTests(unittest.TestCase):
    def test_load_metrics_are_percentages(self):
        rows = telemetry_metrics({"mode": "load", "stability": 64, "load": 92})
        self.assertEqual([row.label for row in rows], ["STABILITY", "LOAD"])
        self.assertEqual([row.display for row in rows], ["64%", "92%"])
        self.assertAlmostEqual(rows[1].fraction, 0.92)

    def test_landing_failure_uses_impact_language(self):
        rows = telemetry_metrics(
            {"mode": "landing", "speed": 21.0, "miss": 40.0, "fuel": 2.0},
            success=False,
        )
        self.assertEqual(rows[0].label, "IMPACT SPEED")
        self.assertEqual(rows[0].display, "21.0 M/S")
        self.assertEqual(rows[0].tone, "bad")
        self.assertAlmostEqual(rows[0].target_fraction, 0.475)
        self.assertEqual(rows[2].display, "2%")
        self.assertEqual(rows[2].tone, "bad")

    def test_landing_difficulty_moves_the_miss_target(self):
        rows = telemetry_metrics(
            {"mode": "landing", "speed": 8.0, "miss": 35.0, "fuel": 40.0,
             "target_half": 27.0},
            success=True,
        )
        self.assertEqual(rows[1].limit, 43.0)
        self.assertAlmostEqual(rows[1].target_fraction, 27.0 / 43.0)
        self.assertEqual(rows[1].tone, "warn")

    def test_debris_hull_and_close_calls(self):
        rows = telemetry_metrics(
            {"mode": "debris", "hull": 2, "max_hull": 4, "close": 3})
        self.assertEqual(rows[0].display, "2/4")
        self.assertEqual(rows[0].tone, "warn")
        self.assertAlmostEqual(rows[0].fraction, 0.5)
        self.assertEqual(rows[1].display, "3")
        self.assertEqual(rows[1].tone, "warn")

    def test_unknown_or_invalid_stats_are_ignored(self):
        self.assertEqual(telemetry_metrics({}), ())
        self.assertEqual(telemetry_metrics(None), ())
        self.assertEqual(telemetry_metrics("not a mapping"), ())


class ScoreTests(unittest.TestCase):
    def test_missing_and_negative_missions_stay_visible(self):
        rows = score_metrics([
            {"points": 120},
            {"points": -20},
        ])
        self.assertEqual(len(rows), 3)
        self.assertEqual([row.display for row in rows], ["+120", "-20", "SKIP"])
        self.assertEqual(rows[0].tone, "default")
        self.assertEqual(rows[1].tone, "bad")
        self.assertEqual(rows[1].fraction, 0.0)

    def test_scores_are_clamped_to_the_mission_ceiling(self):
        rows = score_metrics([{"points": 999}], missions=1)
        self.assertEqual(rows[0].fraction, 1.0)
        self.assertEqual(rows[0].display, "+999")


if __name__ == "__main__":
    unittest.main()
