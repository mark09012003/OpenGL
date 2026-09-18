"""Regression coverage for an ambiguous HP bar at startup."""
import importlib
import logging
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from automation import AutomationManager


class StartupTests(unittest.TestCase):
    def test_key_failure_reports_why_the_loop_stopped(self):
        window = MagicMock()
        window.is_valid.return_value = True
        window.bring_to_front.return_value = False
        manager = AutomationManager(window, MagicMock())
        manager.is_running = True

        self.assertFalse(manager.send_key_press("1", "技能1"))
        self.assertIn("遊戲視窗", manager.last_error)

    def test_ambiguous_bar_shows_guidance_before_running(self):
        with patch.dict(sys.modules, {"win32gui": MagicMock()}):
            gui = importlib.import_module("gui")

        app = gui.MapleStoryAutoPrayerGUI.__new__(gui.MapleStoryAutoPrayerGUI)
        app.is_running = False
        app.worker_thread = None
        app.logger = logging.getLogger("startup-test")
        app.window_manager = MagicMock()
        app.window_manager.is_valid.return_value = True
        app.window_manager.bring_to_front.return_value = True
        app.detection_manager = MagicMock()
        app.detection_manager.tracker.status = "ambiguous"
        app.automation_manager = MagicMock()
        app.window_var = MagicMock(get=lambda: "MapleStory Worlds-Artale")
        app.self_bar_x_var = MagicMock(get=lambda: "")
        for name, value in (
            ("prayer_key_var", "1"), ("angel_blessing_var", "2"),
            ("custom_skill1_key_var", "3"), ("custom_skill2_key_var", "4"),
            ("blessing_interval_var", "0.5"), ("fm_wait_var", "230"),
            ("fm_check_time_var", "1"), ("left_move_time_var", "0.1"),
            ("right_move_time_var", "0.1"), ("move_direction_var", "left"),
            ("target_width_var", "1295"), ("target_height_var", "759"),
        ):
            setattr(app, name, SimpleNamespace(get=lambda value=value: value))
        for name, value in (
            ("skill2_enabled_var", True), ("custom_skill1_var", False),
            ("custom_skill2_var", False), ("enter_fm_var", True),
            ("fixed_move_var", False), ("anti_detect_after_fm_var", False),
        ):
            setattr(app, name, SimpleNamespace(get=lambda value=value: value))

        with patch.object(gui.messagebox, "showwarning") as warning:
            app.start_automation()

        warning.assert_called_once()
        self.assertIn("自身血條 X", warning.call_args.args[1])
        self.assertFalse(app.is_running)
        app.detection_manager.detect_hp_bar_position.assert_called_once()
        app.automation_manager.is_running = False


if __name__ == "__main__":
    unittest.main()
