import unittest

import numpy as np
from PIL import Image
from unittest.mock import patch

from hp_tracking import Bar, PlayerBarTracker, red_intervals
from config import ConfigManager
from detection import DetectionManager
from automation import AutomationManager


def bar(x, width=30, image_width=300):
    return Bar(x, x + width - 1, 445,
               x == 0 or x + width == image_width)


class HpTrackingTests(unittest.TestCase):
    def test_no_arbitrary_player_when_multiple_bars_appear(self):
        tracker = PlayerBarTracker(20, 45, 60)
        self.assertIsNone(tracker.observe([bar(40), bar(150)]))
        self.assertEqual(tracker.status, "ambiguous")

    def test_seed_selects_own_bar_and_follows_it(self):
        tracker = PlayerBarTracker(20, 45, 60, seed_x=145)
        self.assertEqual(tracker.observe([bar(40), bar(150)]).x_start, 150)
        self.assertEqual(tracker.observe([bar(45), bar(160)]).x_start, 160)

    def test_overlap_does_not_switch_to_other_player(self):
        tracker = PlayerBarTracker(20, 45, 60, seed_x=150)
        tracker.observe([bar(40), bar(150)])
        self.assertIsNone(tracker.observe([bar(40), bar(138, 55)]))
        self.assertEqual(tracker.status, "occluded")
        self.assertEqual(tracker.position, 150)
        self.assertEqual(tracker.observe([bar(41), bar(153)]).x_start, 153)

    def test_split_after_overlap_waits_when_two_identities_remain_possible(self):
        tracker = PlayerBarTracker(20, 45, 60, seed_x=150)
        tracker.observe([bar(140), bar(150)])
        self.assertIsNone(tracker.observe([bar(145, 55)]))
        self.assertIsNone(tracker.observe([bar(145), bar(175)]))
        self.assertEqual(tracker.status, "ambiguous")

    def test_edge_clipping_does_not_become_position_zero(self):
        tracker = PlayerBarTracker(20, 45, 60, seed_x=5)
        self.assertIsNone(tracker.observe([bar(0, 25)]))
        self.assertIsNone(tracker.position)
        self.assertEqual(tracker.observe([bar(7)]).x_start, 7)

    def test_missing_bar_never_reacquires_distant_player(self):
        tracker = PlayerBarTracker(20, 45, 60, seed_x=150)
        tracker.observe([bar(150)])
        for _ in range(10):
            self.assertIsNone(tracker.observe([bar(40)]))
        self.assertEqual(tracker.position, 150)

    def test_red_extraction_keeps_partial_edge_candidate_visible(self):
        row = np.zeros((100, 3), dtype=np.uint8)
        row[:25] = (230, 20, 20)
        row[50:80] = (230, 20, 20)
        bars = red_intervals(row, 445, r_min=150, r_max=255, g_max=100,
                             b_max=100, rg_ratio=1.5, rb_ratio=1.5, gap=2)
        self.assertTrue(bars[0].clipped)
        self.assertFalse(bars[1].clipped)

    def test_config_merge_restores_missing_nested_defaults(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"detection": {"hp_bar_y": 444}}))
            config = ConfigManager(str(path)).load()
            self.assertEqual(config["detection"]["hp_bar_y"], 444)
            self.assertIn("character_x_tolerance", config["detection"])

    def test_detector_crops_to_narrow_strip_and_keeps_identity(self):
        class Window:
            def get_window_handle(self):
                return 1

            def get_window_rect(self):
                return (20, 30, 300, 500)

        detector = DetectionManager(Window(), {"detection": {
            "hp_bar_y": 445, "hp_bar_min_width": 20,
            "hp_bar_max_width": 45, "self_bar_x": 150,
        }})
        frames = []
        for intervals in (((40, 30), (150, 30)),
                          ((40, 30), (140, 55)),
                          ((40, 30), (155, 30))):
            frame = np.zeros((11, 300, 3), dtype=np.uint8)
            for x, width in intervals:
                frame[5, x:x + width] = (230, 20, 20)
            frames.append(Image.fromarray(frame))
        bboxes = []

        def grab(*, bbox):
            bboxes.append(bbox)
            return frames.pop(0)

        with patch("detection.ImageGrab.grab", side_effect=grab):
            self.assertEqual(detector.detect_hp_bar_position()[0], 150)
            self.assertIsNone(detector.detect_hp_bar_position())
            self.assertEqual(detector.detect_hp_bar_position()[0], 155)
        self.assertEqual(bboxes[0], (20, 470, 320, 481))

    def test_detector_ignores_single_noisy_pixel_on_calibrated_row(self):
        class Window:
            def get_window_handle(self):
                return 1

            def get_window_rect(self):
                return (0, 0, 300, 500)

        detector = DetectionManager(Window(), {"detection": {"hp_bar_y": 445}})
        frame = np.zeros((11, 300, 3), dtype=np.uint8)
        frame[5, 100] = (230, 20, 20)
        frame[4, 150:180] = (230, 20, 20)
        with patch("detection.ImageGrab.grab", return_value=Image.fromarray(frame)):
            self.assertEqual(detector.detect_hp_bar_position()[0], 150)

    def test_movement_releases_direction_when_tracking_is_lost(self):
        class Window:
            def is_valid(self):
                return True

            def bring_to_front(self):
                return True

        class Detector:
            def __init__(self):
                self.tracker = type("Tracker", (), {"status": "occluded"})()

            def detect_hp_bar_position(self, exclude_x_range=None):
                return None

        manager = AutomationManager(Window(), Detector())
        manager.is_running = True
        with patch("automation.pyautogui.keyUp") as key_up, \
             patch.object(manager, "_sleep_with_check", return_value=False):
            self.assertFalse(manager.move_to_target_position(200))
        self.assertIn("left", [call.args[0] for call in key_up.call_args_list])
        self.assertIn("right", [call.args[0] for call in key_up.call_args_list])

    def test_occlusion_is_not_confirmed_as_market_exit(self):
        class Detector:
            all_candidates = [{"x_start": 100}]
            tracker = type("Tracker", (), {"status": "occluded"})()

            def detect_hp_bar_position(self):
                return None

        manager = AutomationManager(None, Detector())
        manager.is_running = True
        self.assertFalse(manager._confirm_bar_absent())


if __name__ == "__main__":
    unittest.main()
