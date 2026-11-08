import unittest

import engine3d
import fleet3d
import visuals3d


class RecordingCanvas:
    """The small Canvas surface used by the scene painters."""

    def __init__(self):
        self.polygons = 0
        self.ovals = 0
        self.lines = 0
        self.texts = 0
        self.deleted = []

    def delete(self, tag=None):
        self.deleted.append(tag)

    def create_rectangle(self, *args, **kwargs):
        pass

    def create_oval(self, *args, **kwargs):
        self.ovals += 1

    def create_line(self, *args, **kwargs):
        self.lines += 1

    def create_polygon(self, *args, **kwargs):
        self.polygons += 1

    def create_text(self, *args, **kwargs):
        self.texts += 1


class Engine3DTests(unittest.TestCase):
    def test_triangle_renders_into_depth_sorted_polygons(self):
        mesh = engine3d.Mesh()
        mesh.add_triangle([(-1, -1, 0), (1, -1, 0), (0, 1, 0)], "hull")
        camera = engine3d.Camera(eye=(0, 0, 5), target=(0, 0, 0))
        polygons = engine3d.render([engine3d.Part(mesh)], 400, 300, camera,
                                   fog_start=10, fog_end=20)
        self.assertEqual(len(polygons), 1)
        self.assertEqual(len(polygons[0]["points"]), 3)
        self.assertRegex(polygons[0]["fill"], r"^#[0-9A-F]{6}$")

    def test_near_plane_clips_geometry_behind_camera(self):
        mesh = engine3d.Mesh()
        mesh.add_quad([(-1, -1, 10), (1, -1, 10), (1, 1, 10), (-1, 1, 10)])
        camera = engine3d.Camera(eye=(0, 0, 5), target=(0, 0, 0))
        self.assertEqual(engine3d.render([engine3d.Part(mesh)], 320, 240,
                                         camera), [])

    def test_fleet_has_five_ships_and_dense_models(self):
        self.assertEqual(len(fleet3d.SHIPS), 5)
        for ship in fleet3d.SHIPS:
            self.assertGreater(len(ship["mesh"].faces), 350)
            self.assertIn("target", ship)
            self.assertIn("distance", ship)
        self.assertGreater(len(fleet3d.HANGAR.faces), 1200)
        self.assertGreater(len(fleet3d.BOOSTER.faces), 150)

    def test_hangar_scene_paints_environment_and_ship(self):
        canvas = RecordingCanvas()
        visuals3d.draw_hangar_environment(canvas, fleet3d.SHIPS[0], 760, 520)
        self.assertGreater(canvas.polygons, 1200)
        canvas.polygons = 0
        count = visuals3d.draw_hangar_ship(canvas, fleet3d.SHIPS[0],
                                          0.55, 0.16, 1.05, 760, 520)
        self.assertGreater(count, 500)
        self.assertGreater(canvas.polygons, 500)
        self.assertGreater(canvas.ovals, 0)

    def test_title_and_mission_scenes_use_models(self):
        for index in range(3):
            canvas = RecordingCanvas()
            visuals3d.draw_mission(canvas, index, 520, 520)
            self.assertGreater(canvas.polygons, 300)
        canvas = RecordingCanvas()
        visuals3d.draw_title(canvas, 900, 560)
        self.assertGreater(canvas.polygons, 800)

    def test_flight_scenes_paint_without_tk(self):
        canvas = RecordingCanvas()
        visuals3d.draw_flight_load(canvas, 40, 50, 55, 12, 0.5, 900, 430)
        self.assertGreater(canvas.polygons, 400)
        canvas = RecordingCanvas()
        visuals3d.draw_flight_landing(canvas, 450, 850, -40, True, 60,
                                      900, 430)
        self.assertGreater(canvas.polygons, 400)
        canvas = RecordingCanvas()
        rocks = [{"x": 0.2 + i * 0.12, "y": 0.35 + i * 0.08,
                  "r": 0.02, "rot": i} for i in range(8)]
        visuals3d.draw_flight_debris(canvas, 0.5, rocks, 3, 4, 900, 430)
        self.assertGreater(canvas.polygons, 1000)


if __name__ == "__main__":
    unittest.main()
