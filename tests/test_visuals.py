"""Headless smoke tests for the Canvas vector art.

The drawing helpers intentionally only use the Canvas method subset below, so
they can be exercised without a display or a Tk root.
"""

import unittest

import visuals


class RecordingCanvas:
    def __init__(self):
        self.calls = []

    def _record(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))

    def delete(self, *args, **kwargs):
        self._record("delete", *args, **kwargs)

    def create_line(self, *args, **kwargs):
        self._record("line", *args, **kwargs)

    def create_oval(self, *args, **kwargs):
        self._record("oval", *args, **kwargs)

    def create_rectangle(self, *args, **kwargs):
        self._record("rectangle", *args, **kwargs)

    def create_polygon(self, *args, **kwargs):
        self._record("polygon", *args, **kwargs)

    def create_arc(self, *args, **kwargs):
        self._record("arc", *args, **kwargs)

    def create_text(self, *args, **kwargs):
        self._record("text", *args, **kwargs)


class BackdropTests(unittest.TestCase):
    def test_backdrop_draws_stars_grid_and_registration_marks(self):
        canvas = RecordingCanvas()
        visuals.draw_backdrop(canvas, 800, 500, stars=12)
        kinds = [call[0] for call in canvas.calls]
        self.assertIn("delete", kinds)
        self.assertGreaterEqual(kinds.count("line"), 12)
        self.assertIn("oval", kinds)
        self.assertIn("rectangle", kinds)


class ArtTests(unittest.TestCase):
    def test_every_vector_helper_runs_on_a_canvas(self):
        canvas = RecordingCanvas()
        visuals.draw_orbit(canvas, 200, 200, 130, 60)
        visuals.draw_planet(canvas, 300, 160, 80)
        visuals.draw_star_destroyer(canvas, 160, 120, 90)
        visuals.draw_xwing(canvas, 220, 260, 70)
        visuals.draw_radar(canvas, 80, 80, 26)
        visuals.draw_rank_badge(canvas, 100, 100, 70, "JEDI ACE")
        visuals.draw_auth_art(canvas, 250, 250, 0.55)
        self.assertIn("polygon", [call[0] for call in canvas.calls])
        self.assertIn("arc", [call[0] for call in canvas.calls])
        self.assertIn("text", [call[0] for call in canvas.calls])


if __name__ == "__main__":
    unittest.main()
