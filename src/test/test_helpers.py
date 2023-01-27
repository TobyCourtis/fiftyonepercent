import unittest

from . import epoch_to_date, convert_to_hours


class TestHelpers(unittest.TestCase):
    def test_epoch(self):
        actual_date = epoch_to_date(1674650471000)  # epoch with 3 dp
        expected_date = "2023-01-25 12:41:11"
        self.assertEqual(actual_date, expected_date)

    def test_epoch_rounds_up_to_minute(self):
        actual_date = epoch_to_date(1674741839999)  # 14:03:59
        expected_date = "2023-01-26 14:04:00"
        self.assertEqual(actual_date, expected_date)

    def test_day_to_hour_conversion(self):
        window_min = 2
        window_max = 4
        units = "days"

        actual_min_conversion, actual_max_conversion = convert_to_hours(window_min, window_max, units)

        self.assertEqual(actual_min_conversion, 2 * 24)
        self.assertEqual(actual_max_conversion, 4 * 24)

    def test_hour_to_hour_conversion(self):
        window_min = 2
        window_max = 4
        units = "hours"

        actual_min_conversion, actual_max_conversion = convert_to_hours(window_min, window_max, units)

        self.assertEqual(actual_min_conversion, 2)
        self.assertEqual(actual_max_conversion, 4)
