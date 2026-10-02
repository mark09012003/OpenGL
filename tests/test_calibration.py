import unittest
import sys
from unittest.mock import MagicMock

sys.modules.setdefault("win32gui", MagicMock())
from gui.calibration import parse_calibration_values


class CalibrationValidationTests(unittest.TestCase):
    def test_valid_form_is_parsed_with_expected_types(self):
        values = parse_calibration_values({
            "hp_bar_min_width": "20",
            "hp_bar_max_width": "45",
            "character_x_tolerance": "100",
            "color_r_min": "150",
            "color_r_max": "255",
            "anti_detect_min_moves": "0",
            "anti_detect_max_moves": "1",
            "key_press_wait": "0.25",
        })
        self.assertEqual(values["character_x_tolerance"], 100)
        self.assertIsInstance(values["character_x_tolerance"], int)
        self.assertEqual(values["key_press_wait"], 0.25)

    def test_rejects_partial_or_invalid_save(self):
        invalid_forms = (
            {"hp_bar_y": ""},
            {"hp_bar_min_width": "46", "hp_bar_max_width": "45"},
            {"color_r_min": "256", "color_r_max": "255"},
            {"anti_detect_min_moves": "2", "anti_detect_max_moves": "1"},
            {"dialog_check_width": "0"},
            {"key_press_wait": "-0.1"},
        )
        for form in invalid_forms:
            with self.subTest(form=form), self.assertRaises(ValueError):
                parse_calibration_values(form)


if __name__ == "__main__":
    unittest.main()
