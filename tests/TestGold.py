import unittest

import reddit_gold
from models import User


class TestGold(unittest.TestCase):
    def test_number_gold_credit(self):
        self.assertEqual(12, reddit_gold.number_gold_credit())
        reddit_gold.store_user_buy(User('just-an-dev'), 1, None)
        self.assertEqual(11, reddit_gold.number_gold_credit())
        reddit_gold.store_user_buy(User('just-an-dev'), 7, None)
        self.assertEqual(4, reddit_gold.number_gold_credit())


if __name__ == '__main__':
    unittest.main()
