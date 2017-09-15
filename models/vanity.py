import random
import subprocess

from tinydb import TinyDB, Query

import config
import crypto
from models import User, UserStorage


class VanityGenRequest(object):
    """Class to represent an user"""

    def __init__(self, user):
        self.user = User(user)
        self.pattern = None
        self.difficulty = None
        self.address = None
        self.private_key = None
        self.duration = 0

        self.id = random.randint(0, 99999999)

        # to check if we move funds of user
        self.use = None

    def parse_message(self, message_to_parse):
        split_message = message_to_parse.split()

        # parse message like : +vanity use Dpatern
        donate_index = split_message.index('+vanity')
        use_address = split_message[donate_index + 1]
        pattern = split_message[donate_index + 2]

        if use_address == "use":
            self.use = True
        if use_address == "not-use":
            self.use = False

        # check patern is ok
        if pattern[0] == "D" and crypto.base58_is_valid(pattern):
            self.pattern = pattern

    def save_resquest(self):
        if self.pattern is not None:
            db = TinyDB(config.vanitygen)
            db.insert({
                "id": self.id,
                "user": self.user.username,
                "use": self.use,
                "pattern": self.pattern,
                "finish": False,
                "address": self.address,
                "difficulty": self.difficulty,
                "duration": 0
            })
            return True
        else:
            return False

    def create_from_array(self, arr_vanity):
        self.user = User(arr_vanity['user'])
        del arr_vanity['user']

        for key in arr_vanity.keys():
            setattr(self, key, arr_vanity[key])

        return self

    def generate(self):
        out = subprocess.check_output(['vanitygen', '-X', '30', str(self.pattern)], stderr=subprocess.STDOUT)
        line = out.split('\n')
        self.difficulty = str((line[0]).split(':')[1]).strip()
        self.address = str((line[1]).split(':')[1]).strip()
        self.private_key = str((line[2]).split(':')[1]).strip()

    def move_funds(self, tx_queue, failover_time):
        if self.use is True:
            amount = self.user.get_balance()
            if crypto.tip_user(self.user.address, self.address, amount, tx_queue, failover_time):
                # update user storage file
                UserStorage.add_address(self.user.username, self.address)

                # Todo : update history of user

    def import_address(self):
        rpc = crypto.get_rpc()
        rpc.importprivkey(self.private_key, "reddit-vanity-" + self.user.username, False)

        # on import success clean key from memory
        self.private_key = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        self.private_key = None

    def update_data(self):
        db = TinyDB(config.vanitygen)
        vanity_db = Query()

        db.update(set("finish", True), vanity_db.id == self.id)
        db.update(set("difficulty", self.difficulty), vanity_db.id == self.id)
        db.update(set("duration", self.duration), vanity_db.id == self.id)
