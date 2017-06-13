import unittest

import utils


class TestUtils(unittest.TestCase):
    def test_check_amount_valid(self):
        self.assertEqual(True, utils.check_amount_valid(1))
        self.assertEqual(True, utils.check_amount_valid(10))
        self.assertEqual(False, utils.check_amount_valid(0.1))
        self.assertEqual(False, utils.check_amount_valid(-1))
        self.assertEqual(True, utils.check_amount_valid("1"))
        self.assertEqual(True, utils.check_amount_valid("10"))
        self.assertEqual(False, utils.check_amount_valid("0.1"))
        self.assertEqual(False, utils.check_amount_valid("-1"))


if __name__ == '__main__':
    unittest.main()
