import unittest

import commands
import models


class TestGold(unittest.TestCase):
    def test_number_gold_credit(self):
        self.assertEqual(12, commands.reddit_gold.number_gold_credit())
        commands.reddit_gold.store_user_buy(models.User('just-an-dev'), 1, None)
        self.assertEqual(11, commands.reddit_gold.number_gold_credit())
        commands.reddit_gold.store_user_buy(models.User('just-an-dev'), 7, None)
        self.assertEqual(4, commands.reddit_gold.number_gold_credit())


if __name__ == '__main__':
    unittest.main()
