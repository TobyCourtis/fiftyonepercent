import unittest

from . import epoch_to_date


class TestHelpers(unittest.TestCase):
    def test_epoch(self):
        actual_date = epoch_to_date(1674650471000)  # epoch with 3 dp
        expected_date = "2023-01-25 12:41:11"
        self.assertEqual(actual_date, expected_date)
