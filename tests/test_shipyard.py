"""Headless tests for the hangar geometry and the ship exam."""

import math
import unittest

import shipyard


class MeshTests(unittest.TestCase):
    def test_every_ship_has_geometry(self):
        for ship in shipyard.SHIPS:
            vertices, faces = shipyard.MODELS[ship["id"]]
            self.assertGreaterEqual(len(vertices), 10, ship["id"])
            self.assertGreaterEqual(len(faces), 8, ship["id"])
            for point in vertices:
                self.assertEqual(len(point), 3)
                for value in point:
                    self.assertTrue(math.isfinite(value))
            for indices, material in faces:
                self.assertGreaterEqual(len(indices), 3)
                for index in indices:
                    self.assertLess(index, len(vertices))
                self.assertIn(material, shipyard.MATERIALS)

    def test_dossiers_are_complete(self):
        for ship in shipyard.SHIPS:
            for key in ("id", "name", "class", "role", "crew", "length",
                        "arms", "note", "zoom"):
                self.assertIn(key, ship)
                self.assertTrue(ship[key] not in (None, ""))


class FrameTests(unittest.TestCase):
    def test_frames_project_inside_the_canvas(self):
        for ship in shipyard.SHIPS:
            frame = shipyard.build_frame(shipyard.MODELS[ship["id"]],
                                         480, 360, 0.4, 0.2, ship["zoom"])
            self.assertGreater(len(frame), 8, ship["id"])
            for polygon in frame:
                self.assertGreaterEqual(len(polygon["points"]), 3)
                self.assertRegex(polygon["fill"], r"^#[0-9A-F]{6}$")
                for x, y in polygon["points"]:
                    self.assertTrue(math.isfinite(x))
                    self.assertTrue(math.isfinite(y))
                    self.assertLess(abs(x), 4000)
                    self.assertLess(abs(y), 4000)

    def test_rotation_changes_the_projection(self):
        model = shipyard.MODELS["xwing"]
        first = shipyard.build_frame(model, 400, 300, 0.0, 0.0)
        second = shipyard.build_frame(model, 400, 300, 1.2, 0.3)
        self.assertNotEqual([polygon["points"] for polygon in first],
                            [polygon["points"] for polygon in second])

    def test_tiny_canvas_returns_nothing(self):
        self.assertEqual(shipyard.build_frame(shipyard.MODELS["tie"], 10, 10),
                         [])

    def test_shading_stays_in_colour_space(self):
        self.assertRegex(shipyard._shade((200, 20, 240), 0.5),
                         r"^#[0-9A-F]{6}$")
        self.assertEqual(shipyard._shade((0, 0, 0), 1.0), "#000000")


class ExamTests(unittest.TestCase):
    def test_exam_has_twenty_questions(self):
        self.assertEqual(len(shipyard.QUESTIONS), 20)

    def test_every_question_swaps_in_its_own_model(self):
        self.assertEqual(len(shipyard.QUESTION_MODEL_IDS),
                         len(shipyard.QUESTIONS))
        self.assertEqual(len(set(shipyard.QUESTION_MODEL_IDS)),
                         len(shipyard.QUESTION_MODEL_IDS))
        self.assertEqual(set(shipyard.QUESTION_MODEL_IDS),
                         set(shipyard.EXAM_MODELS))
        for model_id in shipyard.QUESTION_MODEL_IDS:
            reference = shipyard.EXAM_MODELS[model_id]
            self.assertTrue(reference["name"])
            frame = shipyard.build_frame(reference["mesh"], 150, 110,
                                         0.5, 0.2, 1.1)
            self.assertGreater(len(frame), 3, model_id)

    def test_questions_are_unique(self):
        questions = [question["question"] for question in shipyard.QUESTIONS]
        self.assertEqual(len(set(questions)), len(questions))
        self.assertEqual({question["correct"] for question in shipyard.QUESTIONS},
                         {0, 1, 2})

    def test_questions_are_answerable(self):
        self.assertGreaterEqual(len(shipyard.QUESTIONS), 5)
        for question in shipyard.QUESTIONS:
            self.assertTrue(question["question"])
            self.assertEqual(len(question["answers"]), 3)
            self.assertEqual(len(set(question["answers"])), 3)
            self.assertIn(question["correct"], range(3))
            self.assertTrue(question["explain"])

    def test_correct_answers_are_not_all_in_the_same_slot(self):
        slots = {question["correct"] for question in shipyard.QUESTIONS}
        self.assertGreater(len(slots), 1)


if __name__ == "__main__":
    unittest.main()
