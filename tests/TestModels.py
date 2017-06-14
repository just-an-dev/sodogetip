import datetime
import unittest

import config
import models
from MockRpc import MockRpc


class TestTip(unittest.TestCase):
    def test_tip_simple(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 100 doge", None)
        self.assertEqual(100, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_simple_verify(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " 100 doge verify", None)
        self.assertEqual(100, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual(True, tip.verify)

    def test_tip_random(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " random100 doge", None)
        self.assertLess(tip.amount, 100)
        self.assertGreater(tip.amount, 1)
        self.assertEqual("doge", tip.currency)
        self.assertEqual(False, tip.verify)

    def test_tip_random_verify(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " random10000 doge", None)
        self.assertLess(tip.amount, 10000)
        self.assertGreater(tip.amount, 1)
        self.assertEqual("doge", tip.currency)
        if tip.amount >= 1000:
            self.assertEqual(True, tip.verify)

    def test_tip_user_mention(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " /u/just-an-dev 1000 doge", None)
        self.assertEqual(1000, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual("just-an-dev", tip.receiver.username)

    def test_tip_user_mention_add(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " +/u/just-an-dev 1000 doge", None)
        self.assertEqual(1000, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual("just-an-dev", tip.receiver.username)

    def test_tip_user_mention_at(self):
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " @just-an-dev 1000 doge", None)
        self.assertEqual(1000, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual("just-an-dev", tip.receiver.username)

    def test_tip_address(self):
        mock_rpc = MockRpc()
        tip = models.Tip()
        tip.parse_message("+/u/" + config.bot_name + " nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR 1000 doge", mock_rpc)
        self.assertEqual(1000, tip.amount)
        self.assertEqual("doge", tip.currency)
        self.assertEqual("nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", tip.receiver.address)

    def test_tip_not_expired(self):
        tip = models.Tip()
        tip.time = datetime.datetime.now()
        self.assertEqual(False, tip.is_expired())

    def test_tip_expired(self):
        tip = models.Tip()
        tip.time = datetime.datetime.now() - datetime.timedelta(days=4)
        self.assertEqual(True, tip.is_expired())


class TestUser(unittest.TestCase):
    def test_user_exist(self):
        user = models.User("just-an-dev")
        self.assertEqual("nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", user.address)
        self.assertEqual(True, user.is_registered())

    def test_user_not_exist(self):
        user = models.User("doge")
        self.assertEqual(None, user.address)
        self.assertEqual(False, user.is_registered())

    def test_user_exist_by_addr(self):
        user = models.User("doge")
        user.address = "nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR"
        self.assertEqual("nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR", user.address)
        self.assertEqual(True, user.is_registered())

    def test_unregistered_tip_empty(self):
        user = models.User("doge")
        self.assertEqual(0, user.get_balance_unregistered_tip())

    def test_unregistered_tip(self):
        user = models.User("just-an-dev")
        self.assertEqual(1000, user.get_balance_unregistered_tip())


if __name__ == '__main__':
    unittest.main()
